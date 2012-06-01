#!/usr/bin/python
# -*- coding: utf-8 -*-       

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

# TODO :
# 1. move xplmessage in a new xplhub project.
# 2. use the new lib
# 3. adapt domogik to use the new lib
# 4. adapt domogik install to also install the new hub
from domogik.xpl.common.xplmessage import XplMessage, XplMessageError

from datetime import datetime
from time import time
from twisted.python import log
from sys import stdout
from threading import Thread, Event


# TODO : 
# - handle multi hosts
# - log each invalid message in a file
# - make stats for each client on number of each schema per hour
# - bandwitch by client per minute


class Hub():
    """ Main class
        Here we will launch the hub
    """

    def __init__(self):
        """ Init hub
        """
        ### Initiate the logger
        # TODO : handle log file
        # 1. create a /etc/domogik/xplhub.cfg file
        # 2. use this file
        # log.startLogging(open(’/var/log/foo.log’, ’w’))
        log.startLogging(stdout)

        ### Read hub options
        # TODO
        do_log_bandwidth = True
        do_log_invalid_data = True

        ### Start listening to udp
        # We use listenMultiple=True so that we can run MulticastServer.py and
        # MulticastClient.py on same machine:
        self.MPP = MulticastPingPong(do_log_bandwidth = do_log_bandwidth,
                                     do_log_invalid_data = do_log_invalid_data)
        reactor.listenMulticast(3865, self.MPP,
                                listenMultiple=True)
        reactor.addSystemEventTrigger('during', 'shutdown', self.stop_hub)
        reactor.run()

    def stop_hub(self):
        log.msg("Request to stop the xPL hub")
        self.MPP.stop_threads()


class MulticastPingPong(DatagramProtocol):
    """
       _client_list : the list of all seen clients
         List of dict : 
          [{'id' : '192.168.0.1_9999',                # client id
                                                      # used to check only 1 item insteas of checking both ip and port
            'ip' : '192.168.0.1',
            'port' : '9999',
            'source' : 'vendorid-deviceid.instance',  # xpl source
            'interval' : 5,                           # hbeat interval given by the client
            'last seen' : datetime obj                # last seen date/time
            'nb_valid_messages' : 99                  # number of valid messages sent by a client
            'nb_invalid_messages' : 9                 # number of invalid messages sent by a client
           },...
          ]
       bandwidth : bandwitdh stats
          [{'id' : '192.168.0.1_9999',                # client id
            'source' : 'vendorid-deviceid.instance',  # xpl source
            'schema' : 'sensor.basic',                # xpl schema
            'type' : 'xpl-stat',                      # xpl type
            'timestamp' : 1234567890,                 # timestamp
           }, ...
          ]

    """

    def __init__(self, do_log_bandwidth = False, do_log_invalid_data = False):
        """ Init MulticastPingPong object
        """
        ### Client list
        self._client_list = []

        ### Bandwidth
        self._do_log_bandwidth = do_log_bandwidth

        ### Invalid data
        self._do_log_invalid_data = do_log_invalid_data

        ### Check for dead clients each minute
        self._stop = Event()
        self._timer = self.__InternalTimer(60, self._check_dead_clients, self._stop)
        self._timer.start()

    def stop_threads(self):
        """ Stop all threads
        """
        log.msg("Stopping timers...")
        self._stop.set()
        self._timer.join()

    def _check_dead_clients(self):
        """ Look for each client if it is still alive
        """
        msg = "Looking for dead clients..."
        now = time()
        dead_clients = False
        for client in self._client_list:
            dead_time = now - 60 - 2*60*client['interval']
            if client['alive'] and client['last_seen'] < dead_time:
                client['alive'] = False
                msg += "Client %s died" % client['id']
                dead_clients = True
        log.msg(msg)
        if dead_clients:
            self._list_clients()

    def _get_client_id(self, ip, port):
        """ Create the client id from the client ip and port
            @param ip : client ip
            @param port : client port
        """
        return "%s_%s" % (ip, port)

    def _is_new_client(self, client_id):
        """ Check if a client is a new client or not 
            @param client_id : client id
        """
        for client in self._client_list:
            if client['id'] == client_id:
                return False
                break
        log.msg("New client : %s" % client_id)
        return True

    def _decode2xpl(self, data):
        """ Check if data is a valid xpl message and create a xpl object
            @param data : data as string
            @return : boolean (true : xpl, false : no xpl)
                      xplmessage object (or None if not a valid xpl)
        """
        try:
            mess = XplMessage(data)
            log.msg("Valid xPL message")
            return True, mess
        except XplMessageError:
            log.err("Invalid xPL message : %s" % data)
            return False, None

    def _is_hbeat(self, xpl):
        """ Check if data is a hbeat xpl message
            @param xpl : xpl message
        """
        if xpl.schema in ('hbeat.app', 'hbeat.basic'):
            log.msg("Hbeat message")
            return True
        else:
            return False

    def _is_hbeat_end(self, xpl):
        """ Check if data is a hbeat.end xpl message
            @param xpl : xpl message
        """
        if xpl.schema == 'hbeat.end':
            log.msg("Hbeat.End message")
            return True
        else:
            return False

    def _add_client(self, ip, port, xpl):
        """ Add a new client in the client list
            @param ip : client ip
            @param port : client port
            @param xpl : xpl message
        """
        self._client_list.append({'id' : self._get_client_id(ip, port),
                                 'ip' : ip,   # TODO : replace with  xpl.data['remote-ip']???
                                 'port' : port,
                                 'source' : xpl.source,
                                 'interval' : int(xpl.data['interval']),
                                 'last_seen' : time(),
                                 'alive' : True,
                                 'nb_valid_messages' : 1,  
                                 'nb_invalid_messages' : 0})
 
    def _update_client(self, client_id, xpl):
        """ update the client with the new interval and the last seen date (now)
            @param client_id : client id
            @param xpl : xpl message
        """
        found = False
        for client in self._client_list:
            if client['id'] == client_id:
                if client['alive'] == False:
                    log.err("Client %s was dead. Resurrect it.")
                client['interval'] = int(xpl.data['interval'])
                client['last_seen'] = time()
                client['alive'] = True
                found = True
                break
        if found == False:
            log.err("No client to update : %s" % client_id)

    def _remove_client(self, client_id):
        """ Set the client as dead/inactive
            @param client_id : client id
        """
        found = False
        for client in self._client_list:
            if client['id'] == client_id:
                if client['alive'] == False:
                    log.err("Client %s was already dead.")
                client['last_seen'] = time()
                client['alive'] = False
                found = True
                break
        if found == False:
            log.err("No client to remove : %s" % client_id)

    def _get_delivery_addresses(self, xpl):
        """ return the port list of the local client to deliver the xpl message
            @param xpl : xpl message
        """
        addresses = []
        if xpl.target == "*":
            msg = "Target=*. Client ids for delivery : "
            for client in self._client_list:
                addresses.append((client['ip'], client['port']))
                msg += "%s, " % client['id']
        else:
            msg = "Target=%s. Client id for delivery : " % xpl.target
            for client in self._client_list:
                if client['source'] == xpl.target:
                    msg += client['id']
                    addresses.append((client['ip'], client['port']))
        log.msg(msg)
        return addresses

    def _deliver_xpl(self, delivery_addresss, xpl):
        """ Deliver the xpl message to all known xpl clients
            @param delivery_address : (ip, port)
            @param xpl : xpl message to send
        """
        for address in delivery_addresss:
            self.transport.write(str(xpl), address)
        pass

 
    def _list_clients(self):
        """ List all the clients in the log file
        """
        msg =  "\n| Client id             | Client source                      | Interval | Last seen                  | Alive | Nb OK  | Nb KO  |"
        msg += "\n|-----------------------+------------------------------------+----------+----------------------------+-------+--------+--------|"
        for client in self._client_list:
            msg += "\n| %-21s | %-34s | %8s | %25s | %-5s | %6s | %6s |" \
                           % (client['id'],
                              client['source'],
                              client['interval'],
                              datetime.fromtimestamp(client['last_seen']).isoformat(),
                              client['alive'],
                              client['nb_valid_messages'],
                              client['nb_invalid_messages'])
        log.msg(msg)

    def _inc_valid_counter(self, client_id):
        """ Increase the valid counter for a client (if it exists)
            @param client_id : client id
        """
        for client in self._client_list:
            if client['id'] == client_id:
                client['nb_valid_messages'] += 1
                log.msg("Increase number of valid messages for %s to %s" % (client_id, client['nb_valid_messages']))
                break

    def _inc_invalid_counter(self, client_id):
        """ Increase the invalid counter for a client (if it exists)
            @param client_id : client id
        """
        for client in self._client_list:
            if client['id'] == client_id:
                client['nb_invalid_messages'] += 1
                log.msg("Increase number of invalid messages for %s to %s" % (client_id, client['nb_invalid_messages']))
                break

    def _log_bandwidth(self, client_id, xpl):
        """ Log bandwith in memory
            @param client_id : client id
            @param xpl : xpl message
        """
        #TODO
        # put in memory
        # create another function to call from a timer to flush
        pass

    def _log_invalid_data(self, datagram):
        """ Log invalid datagrams in memory
            @param datagram : data
        """
        #TODO
        # put in momory
        # create another function to call from a timer to flush in a file
        pass

 



    def startProtocol(self):
        """
        Called after protocol has started listening.
        """
        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        self.transport.joinGroup("228.0.0.5")

    def datagramReceived(self, datagram, address):
        """ Process received datagrams
            @param datagram : data received
            @param address : source ip/port
        """        
        log.msg("Data received from %s : %s" % (repr(address), repr(datagram)))
        ip = address[0]
        port = address[1]
        client_id = self._get_client_id(ip, port)
 
        # check if this is a valid xpl message
        is_xpl, xpl = self._decode2xpl(datagram)
        if is_xpl:
            # Nothing to do, just continue
            self._inc_valid_counter(client_id)
        else:
            # Assuming the client already exists, increase its invalid msg counter and then finish the processing
            self._inc_invalid_counter(client_id)
            if self._do_log_invalid_data:
                self._log_invalid_data(datagram)
            return

        # TODO : 
        # When the hub receives a hbeat.app or config.app message, the hub should extract the "remote-ip" value from the message body and compare the IP address with the list of addresses the hub is currently bound to for the local computer. If the address does not match any local addresses, the packet moves on to the delivery/rebroadcast step. 

        # check if this is a local hbeat message
        # TODO : check if the hbeat comes from localhost or not
        if self._is_hbeat(xpl):
            # handle new clients
            if self._is_new_client(client_id):  
                self._add_client(ip, port, xpl)
                self._list_clients()
            else:
                self._update_client(client_id, xpl)
                self._list_clients()

        # send to the appropriate target
        # tODO
        delivery_addresses = self._get_delivery_addresses(xpl)
        self._deliver_xpl(delivery_addresses, xpl)

        # handle hbeat.end messages
        if self._is_hbeat_end(xpl):
            self._remove_client(client_id)

        # Stats features (we did them after sending the xpl messages for performance
        if self._do_log_bandwidth:
            self._log_bandwidth(client_id, xpl)

    def sigInt(self):
        print "ZZZ"

    class __InternalTimer(Thread):
        '''
        Internal timer class
        '''
        def __init__(self, time, cb, stop):
            '''
            @param time : interval between each callback call
            @param cb : callback function
            @param stop : Event to check for stop thread
            '''
            Thread.__init__(self)
            self._time = time
            self._cb = cb
            self._stop = stop
            self.name = "internal-timer"

        def run(self):
            '''
            Call the callback every X seconds
            '''
            while not self._stop.isSet():
                self._cb()
                self._stop.wait(self._time)




if __name__ == "__main__":
    Hub()


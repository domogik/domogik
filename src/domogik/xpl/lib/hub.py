#!/usr/bin/python
# -*- coding: utf-8 -*-       
""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

xpl Hub

Implements
==========

class Hub()
class MulticastPingPong(DatagramProtocol)
    class __InternalTimer(Thread)

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


# dependencies needed : twisted, netifaces
# pip install twisted
# pip install netifaces

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.python import log
from optparse import OptionParser
#from domogik.xpl.bin.hub import VERSION


from domogik.xpl.common.xplmessage import XplMessage, XplMessageError
from domogik.common import daemonize

from datetime import datetime
from time import time
from sys import stdout
from threading import Thread, Event
from netifaces import interfaces, ifaddresses, AF_INET
import ConfigParser
import traceback
import sys
#import copy
#import os
#import socket

# config file
CONFIG_FILE = "/etc/domogik/xplhub.cfg"

# client status
ALIVE = "alive"
DEAD = "dead"
STOPPED = "stopped"








class Logger:

    def __init__(self, log_level):
        self._log_level = log_level

    def info(self, msg):
        # log only in 'info' log level
        if self._log_level == 'info':
            log.msg(msg)

    def error(self, msg):
        # log in all log level
        log.err(msg)









class Hub():
    """ Main class
        Here we will launch the hub
    """


    def __init__(self, daemon = False):
        """ Init hub
            @param daemon : True : launch as a daemon
        """

        self.is_daemon = daemon

        #print("Domogik xPL Hub (python) v%s" % VERSION)
        print("Domogik xPL Hub (python) v%s" % 666)
        print("Starting...")
        print("- Reading configuration...")

        ### Read hub options
        # read config file
        config_p = ConfigParser.ConfigParser()
        try:
            with open(CONFIG_FILE) as cfg_file:
                config_p.readfp(cfg_file)
                # get config
                config = {}
                for k, v in config_p.items('hub'):
                    config[k] = v

        except:
            print("ERROR : Unable to open configuration file '%s' : %s" % (CONFIG_FILE, traceback.format_exc()))
            return
 
        ### Initiate the logger
        print("- Preparing the log files...")
        self.log = Logger(config['log_level'])

        file_stdout = "%s/xplhub.log" % config['log_dir_path']
        log.startLogging(open(file_stdout, "w"), setStdout=False)
        self.log.info("------------------------")

        file_clients = "%s/client_list.txt" % config['log_dir_path']
        do_log_bandwidth = config['log_bandwidth']
        if do_log_bandwidth == "True":
            do_log_bandwidth = True
        else:
            do_log_bandwidth = False
        file_bandwidth = "%s/bandwidth.csv" % config['log_dir_path']
        do_log_invalid_data = config['log_invalid_data']
        if do_log_invalid_data == "True":
            do_log_invalid_data = True
        else:
            do_log_invalid_data = False
        file_invalid_data = "%s/invalid_data.csv" % config['log_dir_path']

        ### Start listening to udp
        # We use listenMultiple=True so that we can run MulticastServer.py and
        # MulticastClient.py on same machine:
        print("- Initiating the multicast UDP client...")
        self.log.info("Initiating the multicast UDP client...")
        self.log.info("- creation...")
        self.MPP = MulticastPingPong(log = self.log,
                                     file_clients = file_clients,
                                     do_log_bandwidth = do_log_bandwidth,
                                     file_bandwidth = file_bandwidth,
                                     do_log_invalid_data = do_log_invalid_data,
                                     file_invalid_data = file_invalid_data)
        self.log.info("- start reactor...")
        reactor.listenMulticast(3865, self.MPP,
                                listenMultiple=True)
        self.log.info("- add triggers...")
        reactor.addSystemEventTrigger('during', 'shutdown', self.stop_hub)
        print("xPL hub started!")

        # following printed lines are in the xplhub.log file
        self.log.info("xPL hub started")
        reactor.run()

    def stop_hub(self):
        print("Request to stop the xPL hub")
        self.log.info("Request to stop the xPL hub")
        self.MPP.stop_threads()










class MulticastPingPong(DatagramProtocol):
    """
       _client_list : the list of all seen clients
       _dead_client_list : the list of all dead clients
         List of dict : 
          [{'id' : '192.168.0.1_9999',                # client id
                                                      # used to check only 1 item insteas of checking both ip and port
            'ip' : '192.168.0.1',
            'port' : '9999',
            'source' : 'vendorid-deviceid.instance',  # xpl source
            'interval' : 5,                           # hbeat interval given by the client
            'last seen' : datetime obj                # last seen date/time
            'alive' : ALIVE / DEAD / STOPPED          # status
            'nb_valid_messages' : 99                  # number of valid messages sent by a client
            'nb_invalid_messages' : 9                 # number of invalid messages sent by a client
           },...
          ]

       _bandwidth : bandwitdh stats
          [{'id' : '192.168.0.1_9999',                # client id
            'source' : 'vendorid-deviceid.instance',  # xpl source
            'schema' : 'sensor.basic',                # xpl schema
            'type' : 'xpl-stat',                      # xpl type
            'timestamp' : 1234567890,                 # timestamp
           }, ...
          ]

       _invalid_data : list of invalid xpl messages
          [{'id' : '192.168.0.1_9999',                # client id
            'data' : '.....',                         # invalid data
            'timestamp' : 1234567890,                 # timestamp
           }, ...

    """

    def __init__(self, log, file_clients, do_log_bandwidth, file_bandwidth, do_log_invalid_data, file_invalid_data):
        """ Init MulticastPingPong object
        """
        ### Main log
        self.log = log

        ### Host's IP
        self._ips = self._ip4_addresses()
        self.log.info("The hub will be bind to the following addresses : %s" % self._ips)

        ### Client list
        self._file_clients = file_clients
        self._client_list = []
        self._dead_client_list = []

        ### Bandwidth
        self._do_log_bandwidth = do_log_bandwidth
        self._file_bandwidth = file_bandwidth
        self._bandwidth = []

        ### Invalid data
        self._do_log_invalid_data = do_log_invalid_data
        self._file_invalid_data = file_invalid_data
        self._invalid_data = []

        ### Check for dead clients each minute
        self._stop = Event()

        self._timer_dead_clients = self.__InternalTimer(60, self._check_dead_clients, self._stop)
        self._timer_dead_clients.start()

        ### Log data in files
        self._timer_write_clients = self.__InternalTimer(30, self._write_clients, self._stop)
        self._timer_write_clients.start()

        # For debug only
        #self._timer_display_bandwidth = self.__InternalTimer(30, self._display_bandwidth, self._stop)
        #self._timer_display_bandwidth.start()

        self._timer_append_bandwidth = self.__InternalTimer(30, self._append_bandwidth, self._stop)
        self._timer_append_bandwidth.start()

        # For debug only
        #self._timer_display_invalid_data = self.__InternalTimer(30, self._display_invalid_data, self._stop)
        #self._timer_display_invalid_data.start()

        self._timer_append_invalid_data = self.__InternalTimer(30, self._append_invalid_data, self._stop)
        self._timer_append_invalid_data.start()

    def _ip4_addresses(self):
        """ Return the list of all ipv4 addresses of the host
        """
        ip_list = []
        for interface in interfaces():
            try:
                for link in ifaddresses(interface)[AF_INET]:
                    ip_list.append(link['addr'])
            except:
                # Probably a non configured interface (wifi for example)
                # Do nothing
                pass
        return ip_list


    def stop_threads(self):
        """ Stop all threads
        """
        self.log.info("Stopping timers...")
        self._stop.set()
        self._timer_dead_clients.join()
        self._timer_write_clients.join()
        self._timer_append_bandwidth.join()
        self._timer_append_invalid_data.join()

    def _write_file(self, filename, data):
        """ Write data to the file 'filename'
            @param filename : file name
            @param data : data to append
        """
        with open(filename, "w") as my_file:
            my_file.write(data)

    def _append_file(self, filename, data):
        """ Append data to the file 'filename'
            @param filename : file name
            @param data : data to append
        """
        with open(filename, "a") as my_file:
            my_file.write(data)

    def _check_dead_clients(self):
        """ Look for each client if it is still alive
        """
        msg = "Looking for dead clients..."
        now = time()
        dead_clients = False
        for client in self._client_list:
            dead_time = now - 60 - 2*60*client['interval']
            if client['alive'] == ALIVE and client['last_seen'] < dead_time:
                client['alive'] = DEAD
                msg += "Client %s died" % client['id']
                self._dead_client_list.append(client)
                self._client_list.remove(client)
                dead_clients = True
        self.log.info(msg)
        if dead_clients:
            self._display_clients()

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
        self.log.info("New client : %s" % client_id)
        return True

    def _decode2xpl(self, data):
        """ Check if data is a valid xpl message and create a xpl object
            @param data : data as string
            @return : boolean (true : xpl, false : no xpl)
                      xplmessage object (or None if not a valid xpl)
        """
        try:
            mess = XplMessage(data)
            self.log.info("Valid xPL message")
            return True, mess
        except XplMessageError:
            self.log.error("Invalid xPL message : %s" % data)
            return False, None

    def _is_hbeat(self, xpl):
        """ Check if data is a hbeat xpl message
            @param xpl : xpl message
        """
        if xpl.schema in ('hbeat.app', 'hbeat.basic'):
            self.log.info("Hbeat message")
            return True
        else:
            return False

    def _is_hbeat_end(self, xpl):
        """ Check if data is a hbeat.end xpl message
            @param xpl : xpl message
        """
        if xpl.schema == 'hbeat.end':
            self.log.info("Hbeat.End message")
            return True
        else:
            return False

    def _is_local_client(self, ip):
        """ Check if the client ip comes from the localhost or not
            @param ip : ip address
        """
        if ip in self._ips:
            self.log.info("Local xpl client")
            return True
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
                                 'alive' : ALIVE,
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
                if client['alive'] != ALIVE:    # should not happen
                    self.log.error("Client %s was not alive and still in alive clients list. Resurrect it.")
                client['interval'] = int(xpl.data['interval'])
                client['last_seen'] = time()
                client['alive'] = ALIVE
                found = True
                break
        if found == False:
            self.log.error("No client to update : %s" % client_id)

    def _remove_client(self, client_id):
        """ Set the client as dead/inactive
            @param client_id : client id
        """
        found = False
        for client in self._client_list:
            if client['id'] == client_id:
                if client['alive'] != ALIVE:   # should not happen
                    self.log.error("Client %s was already not alive and still in alive clients list.")
                client['last_seen'] = time()
                client['alive'] = STOPPED
                self._dead_client_list.append(client)
                self._client_list.remove(client)
                found = True
                break
        if found == False:
            self.log.error("No client to remove : %s" % client_id)

    def _get_delivery_addresses(self, xpl):
        """ return the port list of the local client to deliver the xpl message
            @param xpl : xpl message
        """
        addresses = []
        if xpl.target == "*":
            msg = "Target=*. Client ids for delivery : *"
            for client in self._client_list:
                addresses.append((client['ip'], client['port']))
                msg += "%s, " % client['id']
        else:
            msg = "Target=%s. Client id for delivery : " % xpl.target
            for client in self._client_list:
                if client['source'] == xpl.target:
                    msg += client['id']
                    addresses.append((client['ip'], client['port']))
        self.log.info(msg)
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
        """ List all the clients (alives and deads) in the log file
        """
        msg =  "\n| Client id             | Client source                      | Interval | Last seen                  | Status  | Nb OK  | Nb KO  |"
        msg += "\n|-----------------------+------------------------------------+----------+----------------------------+---------+--------+--------|"
        for client in self._client_list:
            msg += "\n| %-21s | %-34s | %8s | %25s | %-7s | %6s | %6s |" \
                           % (client['id'],
                              client['source'],
                              client['interval'],
                              datetime.fromtimestamp(client['last_seen']).isoformat(),
                              client['alive'],
                              client['nb_valid_messages'],
                              client['nb_invalid_messages'])
        msg += "\n|-----------------------+------------------------------------+----------+----------------------------+---------+--------+--------|"
        for client in self._dead_client_list:
            msg += "\n| %-21s | %-34s | %8s | %25s | %-7s | %6s | %6s |" \
                           % (client['id'],
                              client['source'],
                              client['interval'],
                              datetime.fromtimestamp(client['last_seen']).isoformat(),
                              client['alive'],
                              client['nb_valid_messages'],
                              client['nb_invalid_messages'])
        return msg

    def _display_clients(self):
        """ List all the clients (alives and deads) in the log file
        """
        self.log.info(self._list_clients())

    def _write_clients(self):
        """ Write the client list in a file
        """
        self._write_file(self._file_clients, self._list_clients() + "\n")

    def _inc_valid_counter(self, client_id):
        """ Increase the valid counter for a client (if it exists)
            @param client_id : client id
        """
        for client in self._client_list:
            if client['id'] == client_id:
                client['nb_valid_messages'] += 1
                self.log.info("Increase number of valid messages for %s to %s" % (client_id, client['nb_valid_messages']))
                break

    def _inc_invalid_counter(self, client_id):
        """ Increase the invalid counter for a client (if it exists)
            @param client_id : client id
        """
        for client in self._client_list:
            if client['id'] == client_id:
                client['nb_invalid_messages'] += 1
                self.log.info("Increase number of invalid messages for %s to %s" % (client_id, client['nb_invalid_messages']))
                break

    def _log_bandwidth(self, client_id, xpl):
        """ Log bandwith in memory
            @param client_id : client id
            @param xpl : xpl message
        """
        self._bandwidth.append({'id' : client_id,
                                'source' : xpl.source,
                                'schema' : xpl.schema,
                                'type' : xpl.type,
                                'timestamp' : time()})

    # for debug only
    def _display_bandwidth(self):
        """ Display in log the bandwidth
        """
        msg =  "Bandwith data :"
        msg += "\nbandwidth ; id                    ; timestamp       ; source                             ; schema           ; type"
        for my_item in self._bandwidth:
            msg += "\nbandwidth ; %-21s ; %15s ; %-34s ; %-17s ; %-8s" \
                           % (my_item['id'],
                              my_item['timestamp'],
                              my_item['source'],
                              my_item['schema'],
                              my_item['type'])
        self.log.info(msg)

    def _append_bandwidth(self):
        """ Append bandwidth data to a file
        """
        # TODO : to add only if the file is empty
        #msg = "bandwidth ; id                    ; timestamp       ; source                             ; schema           ; type\n"
        msg = ""
        # Generate data to write in the file
        for my_item in self._bandwidth:
            msg += "%-21s ; %15s ; %-34s ; %-17s ; %-8s\n" \
                           % (my_item['id'],
                              my_item['timestamp'],
                              my_item['source'],
                              my_item['schema'],
                              my_item['type'])
        # Clean data
        self._bandwidth = []
        self._append_file(self._file_bandwidth, msg)

    def _log_invalid_data(self, client_id, datagram):
        """ Log invalid datagrams in memory
            @param client_id : client id
            @param datagram : data
        """
        self._invalid_data.append({'id' : client_id,
                                   'data' : datagram,
                                   'timestamp' : time()})

    # for debug only
    def _display_invalid_data(self):
        """ Display in log the bandwidth
        """
        msg = "List of invalid data received :"
        msg += "\ninvalid_data ;  id                   ; timestamp       ; data"
        for my_item in self._invalid_data:
            msg += "\ninvalid_data ; %-21s ; %15s ; %s" % (my_item['id'],
                                                my_item['timestamp'],
                                                my_item['data'].replace("\n", "\\n"))
        self.log.info(msg)

    def _append_invalid_data(self):
        """ Append invalid data to a file
        """
        # TODO : add only if the file is empty
        #msg = "invalid_data ;  id                   ; timestamp       ; data\n"
        msg = ""
        for my_item in self._invalid_data:
            msg += "%-21s ; %15s ; %s\n" % (my_item['id'],
                                            my_item['timestamp'],
                                            my_item['data'].replace("\n", "\\n"))
        self._invalid_data = []
        self._append_file(self._file_invalid_data, msg)

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
        self.log.info("Data received from %s : %s" % (repr(address), repr(datagram)))
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
                self._log_invalid_data(client_id, datagram)
                print("Invalid message : %s" % datagram)
            return

        # TODO : needed ????
        # When the hub receives a hbeat.app or config.app message, the hub should extract the "remote-ip" value from the message body and compare the IP address with the list of addresses the hub is currently bound to for the local computer. If the address does not match any local addresses, the packet moves on to the delivery/rebroadcast step. 

        # check if this is a local hbeat message
        if self._is_local_client(ip) and self._is_hbeat(xpl):
            # handle new clients
            if self._is_new_client(client_id):  
                self._add_client(ip, port, xpl)
                self._display_clients()
            else:
                self._update_client(client_id, xpl)
                self._display_clients()

        # send to the appropriate target
        # tODO
        delivery_addresses = self._get_delivery_addresses(xpl)
        self._deliver_xpl(delivery_addresses, xpl)

        # handle hbeat.end messages
        if self._is_hbeat_end(xpl):
            self._remove_client(client_id)
            self._display_clients()

        # Stats features (we did them after sending the xpl messages for performance
        if self._do_log_bandwidth:
            self._log_bandwidth(client_id, xpl)

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



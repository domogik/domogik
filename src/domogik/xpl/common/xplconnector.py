# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
A
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

Manage connection to the xPL network

Implements
==========

- Manager.__init__(self, ip=gethostbyname(gethostname()), port=0)
- Manager.leave(self)
- Manager.send(self, message)
- Manager._SendHeartbeat(self)
- Manager._run_thread_monitor(self)
- Manager.add_listener(self, listener)
- Listener:.__init__(self, cb, manager, filter = {})
- Listener:.getFilter(self)
- Listener:.getCb(self)
- Listener:.new_message(self, message)
- Listener:.add_filter(self, key, value)
- Listener:.del_filter(self, key)
- Listener:.get_filter_list(self)
- XPLException.__init__(self, value)
- XPLException.__str__(self)
- Message:.__init__(self, mess=None)
- Message:.set_type(self, type)
- Message:.get_type(self)
- Message:.set_schema(self, schema)
- Message:.get_schema(self)
- Message:.set_conf_key(self, key, value)
- Message:.set_data_key(self, key, value)
- Message:.set_data_order(self, order)
- Message:.set_conf_order(self, order)
- Message:.__contains__(self, key)
- Message:.has_key(self, key)
- Message:.has_conf_key(self, key)
- Message:.data[self, key]
- Message:.get_all_keys(self)
- Message:.self, key
- Message:.__str__(self)
- XplTimer.__init__(self, time, cb, stop)
- XplTimer.start(self)
- XplTimer.getTimer(self)
- XplTimer.stop(self)
- XplTimer.__init__(self, time, cb, stop)
- XplTimer.run(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
import select
import threading
import traceback
import random
#from socket import socket, gethostbyname, gethostname, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
#from domogik.common import logger
#from domogik.xpl.common.baseplugin import BasePlugin
from domogik.xpl.common.xplmessage import XplMessage, FragmentedXplMessage
from domogik.common.dmg_exceptions import XplMessageError
import time

READ_NETWORK_TIMEOUT = 2

class Manager:
    """
    Manager is the main component of the system
    You can run many managers on different port
    Each manager will send an heartbeat message on broadcast on port 3865
    to announce itself to the xPL Hub
    """
    # _port = 0
    # _ip = ""
    # _source = ""
    # _listeners = [] # List of listeners to brodacast message
    # _network = None
    # _UDPSock = None

    def __init__(self, ip=None, port=0, broadcast="255.255.255.255", plugin = None, nohub = False):
        """
        Create a new manager instance
        @param ip : IP to listen to (default real ip address)
        @param port : port to listen to (default 0)
        @param plugin : The plugin associated with this xpl instance
        @param nohub : Don't start the hub discovery
        """
        if ip == None:
            ip = self.get_sanitized_hostname()
        self.p = plugin
        source = "domogik-%s.%s" % (self.p.get_plugin_name(), self.p.get_sanitized_hostname())
        # Define maximum xPL message size
        self._buff = 1500
        # Define xPL base port
        self._source = source
        self._listeners = []
        #Not really usefull
        #self.port = port
        # Initialise the socket
        self._UDPSock = socket(AF_INET, SOCK_DGRAM)
        #Set broadcast flag
        self._UDPSock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self._broadcast = broadcast
        #xPL plugins only needs to connect on local xPL Hub on localhost
        addr = (ip, port)
        #UID for the fragment management
        self._fragment_uid = 1
        self._sent_fragments_buffer = {}
        self._received_fragments_buffer = {}

        #Define locks
        self._lock_send = threading.Semaphore()
        self._lock_list = threading.Semaphore()

	# plugin status
        # 0 = strating (xpl hub discovery)
        # 1 = config (xpl config phase)
        # 2 = running (plugin ready for receiving xpl commands)
        self._status = 0
	# status (starting, config, started)
        self._lock_status = threading.Semaphore()

        # hbeat detected
        self._foundhub = threading.Event()
        if nohub == True:
            self._foundhub.set()
        else:
            self._foundhub.clear()

        # Try and bind to the base port
        try:
            self._UDPSock.bind(addr)
        except:
            # Smthg is already running on this port
            self.p.log.error("Can't bind to the interface %s, port %i" % (ip, port))
            exit(1)
        else:
            self.p.add_stop_cb(self.leave)
            self.port = self._UDPSock.getsockname()[1]
            #Get the port number assigned by the system
            self._ip, self._port = self._UDPSock.getsockname()
            self.p.log.debug("xPL plugin %s socket bound to %s, port %s" \
                            % (self.p.get_plugin_name(), self._ip, self._port))
            self._h_timer = None

            msg = "HUB discovery > starting"
            self.p.log.info(msg)
            print(msg)

            self._SendHeartbeat()
            #And finally we start network listener in a thread
            self._stop_thread = False
            self._network = threading.Thread(None, self._run_thread_monitor,
                    "thread-monitor", (), {})
            self.p.register_thread(self._network)
            self._network.start()
            self.p.log.debug("xPL thread started for %s " % self.p.get_plugin_name())
        # start hbeat discovery
        self.hub_discovery()
        self._foundhub.wait()

    def hub_discovery(self):
        """ Start HUB discovery
        random hbeat timeout between 3 and 10 seconds, and sends HBEAT
        """
        if not self._foundhub.is_set():
            # This log info will be written in another function because here, it is sometimes written *after* the hub is discovered
            #msg = "HUB discovery > starting"
            #self.p.log.info(msg)
            # random send hbeat (between 3 and 10 seconds)
            rnd = random.randrange(3, 10)
            self._h_timer = XplTimer(rnd, self._SendHeartbeat, self)
            self._h_timer.start()

    def foundhub(self):
        """ resets the timer to the default timeout
        """
        msg = "HUB discovery > Received HBEAT echo, HUB detected"
        self.p.log.info(msg)
        print(msg)
        self._foundhub.set()
        self.update_status(1)
        if self._h_timer != None:
            self._h_timer._timer._time = 300
        Listener(cb = self.got_hbeat, manager = self, filter = {'schema':'hbeat.request', 'xpltype':'xpl-cmnd'})

    def enable_hbeat(self, lock = False):
        """ Enable the answer to hbeat request
        @param lock : If set to True, the process will lock  on 'should_stop'
        """
        self.update_status(2)
        if lock:
            self.p.log.debug("Hbeat : Wait for stop flag")
            self.get_stop().wait() 

    def update_status(self, setto):
        """ Update internal plugin status
        Only do this if the status really changes
        """
        if setto != self._status:
            self._lock_status.acquire()
            self._status = setto
            self._lock_status.release()
            self._SendHeartbeat()

    def leave(self):
        """
        Stop threads and leave the Manager
        """
        self.p.log.debug("send hbeat.end")
        self._SendHeartbeat(schema='hbeat.end')
        self._UDPSock.close()
        self.p.log.debug("xPL thread stopped")

    def send(self, message):
        """
        This function allows you to send an xPL message on the Bus
        Be carreful, there is no check on message correctness
        This method is protected by semaphore because in some plugin (REST for example)
        many threads can call it.
        """
        self._lock_send.acquire()
        try:
            if not message.hop_count:
                message.set_hop_count("5")
            if not message.source:
                message.set_source(self._source)
            if not message.target:
                message.set_target("*")
            try:
                if len(message.to_packet()) > 1472:
                    fragments = FragmentedXplMessage.fragment_message(message, self._fragment_uid)
                    self._sent_fragments_buffer[self._fragment_uid] = fragments
                    for fragment in fragments.keys():
                        self.p.log.debug("fragment send")
                        self._UDPSock.sendto(fragments[fragment].__str__(), (self._broadcast, 3865))
                else:
                    self.p.log.debug("normal send")
                    self._UDPSock.sendto(message.__str__(), (self._broadcast, 3865))
            except:
                if self.p.get_stop().is_set():
                    pass
                else:
                    raise
            else:
                self._fragment_uid = self._fragment_uid + 1
            self.p.log.debug("xPL Message sent by thread %s : %s" % (threading.currentThread().getName(), message))
        except:
            self.p.log.warning("Error during send of message")
            self.p.log.debug(traceback.format_exc())
        self._lock_send.release()

    def _SendHeartbeat(self, target='*', test="", schema="hbeat.app"):
        """
        Send heartbeat message in broadcast on the network, on the bus port
        (3865)
        This make the application able to be discovered by the hub
        This method is not called by childs, so no need to protect it.
        """
        self._lock_status.acquire()
        self.p.log.debug("send hbeat")
        mesg = XplMessage()
        mesg.set_type( "xpl-stat" )
        mesg.set_hop_count( 1 )
        mesg.set_source( self._source )
        mesg.set_target( target )
        mesg.set_schema( schema )
        mesg.add_single_data( "interval", "5" )
        mesg.add_single_data( "port", self.port )
        mesg.add_single_data( "remote-ip", self._ip )
        if schema != 'hbeat.end':
            if self._status == 0:
                msg = "HUB discovery > looking for the hub. I hope there is one hub, Domogik won't work without the hub!"
                self.p.log.info(msg)
                print(msg)
            elif self._status == 1:
                msg = "HUB discovery > hub found, configuration in progress"
                self.p.log.info(msg)
                print(msg)
            elif self._status == 2:
                pass
            else:
                msg = "Oops! Wrong status for the hbeat message : %s. Please create a bug report for this!" % self._status
                self.p.log.warning(msg)
                print(msg)

            mesg.add_single_data( "status", self._status )
        if self is not None:
            self.send( mesg )
        self._lock_status.release()

    def got_hbeat(self, message):
        """ Callback for hbeat listener
        """
        if(message.target == self._source or message.target == "*"):
            self._SendHeartbeat(message.source)

    def _run_thread_monitor(self):
        """
        The monitor thread receive all messages on the connection and check
        them to see if the target is the application.
        If it is, call all listeners
        This method is not called by childs, so no need to protect it.
        """
        while not self.p.should_stop():
            try:
                readable, writeable, errored = select.select([self._UDPSock], [], [], READ_NETWORK_TIMEOUT)
            except:
                self.p.log.info("Error during the read of the socket : %s" % traceback.format_exc())
            else:
                if len(readable) == 1:
                    try:
                        data, addr = self._UDPSock.recvfrom(self._buff)
                    except:
                        self.p.log.debug("bad data received")
                    else:
                        try:
                            mess = XplMessage(data)
                            if (not self._foundhub.is_set()) and (mess.source == self._source)\
                                and (mess.schema == "hbeat.app"):
                                self.foundhub()
                            elif (mess.target == "*" or (mess.target == self._source)) and\
                                (self._source != mess.source):
                                update = False
                                if mess.schema == "fragment.basic":
                                    key = (mess.source, mess.data["partid"].split(':')[1])
                                    if not key in self._received_fragments_buffer:
                                        self._received_fragments_buffer[key] = {}
                                    self._received_fragments_buffer[key][mess.data["partid"].split('/')[0]] = mess
                                    if len(self._received_fragments_buffer[key]) == int(mess.data["partid"].split('/')[1].split(':')[0]):
                                        nf = FragmentedXplMessage()
                                        for f in self._received_fragments_buffer[key].keys():
                                            nf.add_fragment(self._received_fragments_buffer[key][f])
                                        mess = nf.build_message()
                                        update = True
                                        del self._received_fragments_buffer[key]
                                else:
                                    update = True
                                if update:
                                    for l in self._listeners:
                                        l.new_message(mess)
                                #Enabling this debug will really polute your logs
                                #self.p.log.debug("New message received : %s" % \
                                #        mess.type)
                        except XPLException:
                            self.p.log.warning("XPL Exception occured in : %s" % sys.exc_info()[2])
                        except XplMessageError as exc:
                            self.p.log.warning("Malformated message received, ignoring it.")
                            self.p.log.warning("Error was : %s" % exc)
                            self.p.log.warning("Message was : %s" % mess)
        self.p.log.info("self._should_stop set, leave.")

    def add_listener(self, listener):
        """
        Add a listener on the list of the manager
        @param listener : the listener instance
        """
        self._lock_list.acquire()
        self._listeners.append(listener)
        self._lock_list.release()

    def del_listener(self, listener):
        """
        del a listener on the list of the manager
        @param listener : the listener instance
        """
        self._lock_list.acquire()
        self._listeners.remove(listener)
        self._lock_list.release()

class Listener:
    """
    Listener are objects which are able to check if a message
    match some filter and to call a function if they do
    """
    # _callback = None
    # _filter = None

    def __init__(self, cb, manager, filter = {}, cb_params = {}):
        """
        The listener will get all messages from the manager and parse them.
        If a message match the filter, then the callback function will be
        called with the message as parameter
        @param cb : the callback function
        @param manager : the manager instance
        @param filter : dictionnary { key : value }. If value is a list, then the 
        listener will check if the key equals any of these values
        """
        manager.p.log.debug("New listener, filter : %s" % filter)
        self._callback = cb
        self._filter = filter
        self._manager = manager
        manager.add_listener(self)
        self._cb_params = cb_params

    def unregister(self):
        self._manager.del_listener(self)

    def __str__(self):
        return "Listener<%s>" % (self._filter)

    def get_filter(self):
        return self._filter

    def get_cb(self):
        return self._callback

    def new_message(self, message):
        """
        This is the function which is called by the manager when a message
        arrives
        The goal of this function is to check if message match filter rules,
        and to call the callback function if it does
        """
        suffixe = ""
        ok = True
        for key in self._filter:
            suffixe = "%s-%s-%s" % (suffixe, key, self._filter[key])
            if key in message.data:
                if isinstance(self._filter[key], list) and not (message.data[key].lower() in [s.lower() for s in self._filter[key]]):
                    ok = False
                elif not isinstance(self._filter[key], list) and (message.data[key].lower() != self._filter[key].lower()):
                    ok = False
            elif key == "schema":
                ok = ok and (self._filter[key] == message.schema)
            elif key == "xpltype":
                ok = ok and (self._filter[key] == message.type)
            elif key == "xplsource":
                ok = ok and (self._filter[key] == message.source)
            elif key == "xplinstance":
                ok = ok and (self._filter[key] == message.source_instance_id)
            elif not (key in message.data or key in ("xpltype", "schema")):
                ok = False
        #The message match the filter, we can call  the callback function
        if ok:
            try:
                if self._cb_params != {} and self._callback.func_code.co_argcount > 1:  
                    thread = threading.Thread(target=self._callback, args = (message, self._cb_params), name="Manager-new-message-cb-%s" % suffixe)
                else:
                    thread = threading.Thread(target=self._callback, args = (message,), name="Manager-new-message-cb-%s" % suffixe)
                self._manager.p.register_thread(thread)
                thread.start()
            except:
                self._manager.p.log.error("Listener exception : %s" % traceback.format_exc())

    def add_filter(self, key, value):
        """
        Add a filter rule. No distinction between conf and data
        If the key already exists, the new value is used
        """
        self._filter[key] = value

    def del_filter(self, key):
        """
        Remove a rule from filter list
        If the key isn't in the list, do nothing
        """
        if key in self._filter:
            del self._filter[key]

    def get_filter_list(self):
        """
        Get all the filter items
        """
        return self._filter


class XPLException(Exception):
    """
    xPL exception
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.repr(self.value)


class XplTimer():
    """
    XplTimer will call a callback function each n seconds
    """
#    _time = 0
#    _callback = None
#    _timer = None

    def __init__(self, time, cb, manager):
        """
        Constructor : create the internal timer
        @param time : time of loop in second
        @param cb : callback function which will be call eact 'time' seconds
        """
        self._stop = threading.Event()
        self._timer = self.__InternalTimer(time, cb, self._stop, manager.p.log)
        self._manager = manager
        self.log = manager.p.log
        manager.p.register_timer(self)
        manager.p.register_thread(self._timer)
        self.log.debug("New timer created : %s " % self)

#    def __repr__(self):
#        """ Representation of the Timer
#        """
#        return "<domogik.xpl.lib.xplconnector.XplTimer> name : %s" % self._timer.name

    def start(self):
        """
        Start the timer
        """
        self._timer.start()

    def get_stop(self):
        """ Returns the threading.Event instance used to stop the XplTimer
        """
        return self._stop

    def get_timer(self):
        """
        Waits for the internal thread to finish
        """
        return self._timer

    def __del__(self):
        self.log.debug("__del__ Manager")
        self.stop()

    def stop(self):
        """
        Stop the timer
        """
        self.log.debug("Timer : stop, try to join() internal thread")
        self._stop.set()
        self._timer.join()
        self.log.debug("Timer : stop, internal thread joined, unregister it")
        self._manager.p.unregister_timer(self._timer)

    class __InternalTimer(threading.Thread):
        '''
        Internal timer class
        '''
        def __init__(self, time, cb, stop, log):
            '''
            @param time : interval between each callback call
            @param cb : callback function
            @param stop : Event to check for stop thread
            '''
            threading.Thread.__init__(self)
            self._time = time
            self._cb = cb
            self._stop = stop
            self.name = "internal-timer"
            self.log = log

        def run(self):
            '''
            Call the callback every X seconds
            '''
            while not self._stop.isSet():
                self._cb()
                self._stop.wait(self._time)

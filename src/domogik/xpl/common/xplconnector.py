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
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
import string
import select
import threading
import traceback
from socket import socket, gethostbyname, gethostname, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
import time
import signal
import os
from domogik.common import logger
from domogik.xpl.common.baseplugin import BasePlugin
from domogik.xpl.common.xplmessage import XplMessage

class Manager(BasePlugin):
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

    def __init__(self, ip=gethostbyname(gethostname()), port=0, broadcast="255.255.255.255"):
        """
        Create a new manager instance
        @param ip : IP to listen to (default real ip address)
        @param port : port to listen to (default 0)
        """
        BasePlugin.__init__(self, stop_cb = self.leave)
        source = "xpl-%s.domogik" % self.get_plugin_name()
        # Define maximum xPL message size
        self._buff = 1500
        # Define xPL base port
        self._source = source
        self._listeners = []
        #Not really usefull
        #self._port = port
        # Initialise the socket
        self._UDPSock = socket(AF_INET, SOCK_DGRAM)
        #Set broadcast flag
        self._UDPSock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self._broadcast = broadcast
        #xPL plugins only needs to connect on local xPL Hub on localhost
        addr = (ip, port)

        self._log = self.get_my_logger()
        #Define locks
        self._lock_send = threading.Semaphore()
        self._lock_list = threading.Semaphore()

        # Try and bind to the base port
        try:
            self._UDPSock.bind(addr)
        except:
            # Smthg is already running on this port
            self._log.error("Can't bind to the interface %s, port %i" % (ip,port))
            exit(1)
        else:
            self.add_stop_cb(self.leave)
            self._port = self._UDPSock.getsockname()[1]
            #Get the port number assigned by the system
            self._ip, self._port = self._UDPSock.getsockname()
            self._log.debug("xPL plugin %s socket bound to %s, port %s" % (self.get_plugin_name(), self._ip, self._port))
            # All is good, we start sending Heartbeat every 5 minutes using
            # XplTimer
            self._SendHeartbeat()
            self._h_timer = XplTimer(300, self._SendHeartbeat, self.get_stop(), self)
            self._h_timer.start()
            #We add a listener in order to answer to the hbeat requests
            Listener(cb = self.got_hbeat, manager = self, filter = {'schema':'hbeat.app','xpltype':'xpl-stat'})
            #And finally we start network listener in a thread
            self._stop_thread = False
            self._network = threading.Thread(None, self._run_thread_monitor,
                    "thread-monitor", (), {})
            self.register_thread(self._network)
            self._network.start()
            self._log.debug("xPL thread started for %s " % self.get_plugin_name())

    def leave(self):
        """
        Stop threads and leave the Manager
        """
        self._UDPSock.close()
        self._log.debug("xPL thread stopped")

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
            self._UDPSock.sendto(message.__str__(), (self._broadcast, 3865))
            self._log.debug("xPL Message sent by thread %s : %s" % (threading.currentThread().getName(), message))
        except:
            self._log.warning("Error during send of message")
            self._log.debug(traceback.format_exc())
        self._lock_send.release()

    def _SendHeartbeat(self, target='*', test=""):
        """
        Send heartbeat message in broadcast on the network, on the bus port
        (3865)
        This make the application able to be discovered by the hub
        This method is not called by childs, so no need to protect it.
        """
        # Sub routine for sending a heartbeat

        mess = """\
xpl-stat
{
hop=1
source=%s
target=%s
}
hbeat.app
{
interval=5
port=%s
remote-ip=%s
}
""" % (self._source, target, self._port, self._ip)
        if self is not None:
            if not self.should_stop():
                self._UDPSock.sendto(mess, (self._broadcast, 3865))

    def got_hbeat(self, message):
        if(message.target != self._source ):
            self._SendHeartbeat(message.source)

    def _run_thread_monitor(self):
        """
        The monitor thread receive all messages on the connection and check
        them to see if the target is the application.
        If it is, call all listeners
        This method is not called by childs, so no need to protect it.
        """
        while not self.should_stop():
            try:
                readable, writeable, errored = select.select(
                    [self._UDPSock], [], [], 10)
            except:
                self._log.info("Error during the read of the socket : %s" % traceback.format_exc())
            else:
                if len(readable) == 1:
                    try:
                        data, addr = self._UDPSock.recvfrom(self._buff)
                    except:
                        self._log.debug("bad data received")
                    else:
                        try:
                            mess = XplMessage(data)
                            if mess.target == "*" or (
                                    mess.target == self._source):
                                [l.new_message(mess) for l in self._listeners]
                                #Enabling this debug will really polute your logs
                                #self._log.debug("New message received : %s" % \
                                #        mess.get_type())
                        except XPLException:
                            self._log.warning("XPL Exception occured in : %s" % sys.exc_info()[2])
        self._log.info("self._should_stop set, leave")

    def add_listener(self, listener):
        """
        Add a listener on the list of the manager
        @param listener : the listener instance
        """
        self._lock_list.acquire()
        self._listeners.append(listener)
        self._lock_list.release()


class Listener:
    """
    Listener are objects which are able to check if a message
    match some filter and to call a function if they do
    """
    # _callback = None
    # _filter = None

    def __init__(self, cb, manager, filter = {}):
        """
        The listener will get all messages from the manager and parse them.
        If a message match the filter, then the callback function will be
        called with the message as parameter
        @param cb : the callback function
        @param manager : the manager instance
        @param filter : dictionnary { key : value }
        """
        manager._log.debug("New listener, filter : %s" % filter)
        self._callback = cb
        self._filter = filter
        self._manager = manager
        manager.add_listener(self)

    def __str__(self):
        return "Listener<%s>" % (self._filter)

    def getFilter(self):
        return self._filter

    def getCb(self):
        return self._callback

    def new_message(self, message):
        """
        This is the function which is called by the manager when a message
        arrives
        The goal of this function is to check if message match filter rules,
        and to call the callback function if it does
        """
        ok = True
        for key in self._filter:
            if key in message.data:
                if (message.data[key] != self._filter[key]):
                    ok = False
            elif key == "schema":
                ok = ok and (self._filter[key] == message.schema)

            elif key == "xpltype":
                ok = ok and (self._filter[key] == message.type)

            elif not (key in message.data or key in (
                    "xpltype", "schema")):
                ok = False
        #The message match the filter, we can call  the callback function
        if ok:
            thread = threading.Thread(target=self._callback, args = (message,), name="Manager-new-message-cb")
            self._manager.register_thread(thread)
            thread.start()

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

    def __init__(self, time, cb, stop, manager):
        """
        Constructor : create the internal timer
        @param time : time of loop in second
        @param cb : callback function which will be call eact 'time' seconds
        """
        self._timer = self.__internalTimer(time, cb, stop, manager._log)
        self._manager = manager
        lg = logger.Logger(self.__class__.__name__)
        self._log = lg.get_logger()
        manager.register_timer(self)
        manager.register_thread(self._timer)

    def __repr__(self):
        """ Representation of the Timer
        """
        return "<domogik.xpl.lib.xplconnector.XplTimer> name : %s" % self._timer.name

    def start(self):
        """
        Start the timer
        """
        self._timer.start()

    def getTimer(self):
        """
        Waits for the internal thread to finish
        """
        return self._timer

    def __del__(self):
        self._log.debug("__del__ Manager")
        self.stop()

    def stop(self):
        """
        Stop the timer
        """
        self._timer.join()
        self._manager.unregister_timer(self._timer)

    class __internalTimer(threading.Thread):
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
            self._log = log


        def run(self):
            '''
            Call the callback every X seconds
            '''
            while not self._stop.isSet():
                self._cb()
                self._stop.wait(self._time)

#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-03-21 14:33:23 +0100 (sam. 21 mars 2009) $
# $LastChangedRevision: 417 $

import sys
import string
import select
import threading
from socket import *

from domogik.common import logger
from domogik.xpl.lib.module import xPLModule


class Manager(xPLModule):
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

    def __init__(self, ip="127.0.0.1", module_name="generic", port=3865):
        """
        Create a new manager instance
        @param ip : IP to listen to (default 0.0.0.0)
        @param source : source name of the application
        @param port : port to listen to (default 3865)
        """
        source = "xpl-%s.domogik" % module_name
        xPLModule.__init__(self)
        # Define maximum xPL message size
        self._buff = 1500
        # Define xPL base port
        self._source = source
        self._listeners = []
        self._port = port
        # Initialise the socket
        self._UDPSock = socket(AF_INET, SOCK_DGRAM)
        #xPL plugins only needs to connect on local xPL Hub on localhost
        #The port is dynamically selected by the system
        addr = (ip, 0)

        l = logger.Logger(module_name)
        self._log = l.get_logger()

        # Try and bind to the base port
        try:
            self._UDPSock.bind(addr)
        except:
            # Smthg is already running on this port
            self._log.error("Can't bind to the port %i" % self._port)
            exit(1)
        else:
            self._port = self._UDPSock.getsockname()[1]
            self._ip = ip
            # All is good, we start sending Heartbeat every 5 minutes using
            # xPLTimer
            self._SendHeartbeat()
            self._h_timer = xPLTimer(300, self._SendHeartbeat)
            self._h_timer.start()
            #And finally we start network listener in a thread
            self._stop_thread = False
            self._network = threading.Thread(None, self._run_thread_monitor,
                    None, (), {})
            self.register_thread(self._network)
            self._network.start()
            self._log.debug("xPL thread started for %s " % module_name)

    def leave(self):
        """
        Stop threads and leave the Manager
        """
        self._h_timer.stop()
        self.force_leave()
        self._log.debug("xPL thread stopped")
        #exit(0)

    def send(self, message):
        """
        This function allows you to send an xPL message on the Bus
        Be carreful, there is no check on message correctness
        """
        try:
            if not message.has_conf_key("hop"):
                message.set_conf_key("hop", "1")
            if not message.has_conf_key("source"):
                message.set_conf_key("source", self._source)
            if not message.has_conf_key("target"):
                message.set_conf_key("target", "*")
        except:
            pass
        finally:
            hbSock = socket(AF_INET, SOCK_DGRAM)
            hbSock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            hbSock.sendto(message.__str__(), ("255.255.255.255", 3865))
            hbSock.close()
            self._log.debug("xPL Message sent")

    def _SendHeartbeat(self):
        """
        Send heartbeat message in broadcast on the network, on the bus port
        (3865)
        This make the application able to be discovered by the hub
        """
        # Sub routine for sending a heartbeat
        self.send("""\
xpl-stat
{
hop=1
source=%s
target=*
}
hbeat.app
{
interval=5
port=%s
remote-ip=%s
}
""" % (self._source, self._port, self._ip))

    def _run_thread_monitor(self):
        """
        The monitor thread receive all messages on the connection and check
        them to see if the target is the application.
        If it is, call all listeners
        """
        while not self.should_stop():
            readable, writeable, errored = select.select(
                    [self._UDPSock], [], [], 10)
            if len(readable) == 1:
                data, addr = self._UDPSock.recvfrom(self._buff)
                try:
                    mess = Message(data)
                    if mess.get_conf_key_value("target") == "*" or (
                            mess.get_conf_key_value("target") == self._source):
                        [l.new_message(mess) for l in self._listeners]
                        #Enabling this debug will really polute your logs
                        #self._log.debug("New message received : %s" % \
                        #        mess.get_type())
                except XPLException:
                    pass
        self.unregister_thread(self._network)

    def add_listener(self, listener):
        """
        Add a listener on the list of the manager
        @param listener : the listener instance
        """
        self._listeners.append(listener)


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
        self._callback = cb
        self._filter = filter
        manager.add_listener(self)

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
            if message.has_key(key):
                if (message.get_key_value(key) != self._filter[key]):
                    ok = False
            else:
                if message.has_conf_key(key):
                    if (message.get_conf_key_value(key) != self._filter[key]):
                        ok = False
                    else:
                        pass
            if key == "schema":
                ok = ok and (self._filter[key] == message.get_schema())

            if key == "type":
                ok = ok and (self._filter[key] == message.get_type())

            if not (message.has_key(key) or message.has_conf_key(key) or key in (
                    "type", "schema")):
                ok = False
        #The message match the filter, we can call  the callback function
        if ok:
            self._callback(message)

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


class Message:
    """
    Message is the object for all data received form the network.
    The monitor create an instance of Message each time it receive smthg
    """
    _mess_types = ['xpl-stat', 'xpl-cmnd', 'xpl-trig']

#    _conf = {} #Dico ayant la configuration du paquet
#    _data = {} #Dico ayant les données du paquet
#    _schema = ''
#    _type = ''
#    _conf_order = ""
#    _data_order = ""

    def __init__(self, mess=None):
        """
        Create Message instance from a message string and check if the
        structure is correct. Raise exception if it is not
        The message can be None (to allow building a message)
        @param mess : the message as a unique string, as it is send on the
        network
        """
        self._conf = {}
        self._data = {}
        self._conf_order = ""
        self._data_order = ""
        l = logger.Logger("message")
        self._log = l.get_logger()
        if mess is None:
            return
        m = mess.split("\n")
        if not m[0] in self._mess_types:
            self._log.warning("Packet type not existing")
        else:
            self._type = m[0]
            try:
                #We get the configuration part (between first {})
                for line in m[m.index('{')+1:m.index('}')]:
                    (key, value) = line.split('=')
                    self._conf[string.lower(key)] = value
                #We get the schema
                self._schema = m[m.index('}') + 1]
                #And the last part, between second {}
                m = m[m.index('}') + 2:]
                for line in m[m.index('{')+1:m.index('}')]:
                    (key, value) = line.split('=')
                    self._data[string.lower(key)] = value
            except:
                self._log.warning("Bad message format, won't be sent")

    def set_type(self, type):
        """
        Define the message type (xpl-stat, xpl-trig or xpl-cmnd)
        """
        if type in self._mess_types:
            self._type = type
        else:
            self._log.warning("Bad message type")

    def get_type(self):
        """
        Return the message type
        """
        return self._type

    def set_schema(self, schema):
        """
        Define the message schema
        """
        self._schema = schema

    def get_schema(self):
        """
        Return the message schema
        """
        return self._schema

    def set_conf_key(self, key, value):
        """
        Define a configuration key (which appears between first {})
        """
        self._conf[key] = value

    def set_data_key(self, key, value):
        """
        Define a data key (which appears between second {})
        """
        self._data[key] = value

    def set_data_order(self, order):
        """
        As schema define parameter order, and since this class isn't specific
        enough to determine order, you have to set the order to ensure a good
        message.
        If you do not, the order of parameter in each part may not conform to
        schema
        If you set order, be sure to list all the keys !
        """
        self._data_order = order

    def set_conf_order(self, order):
        """
        As schema define parameter order, and since this class isn't specific
        enough to determine order, you have to set the order to ensure a good
        message.
        If you do not, the order of parameter in each part may not conform to
        schema
        If you set order, be sure to list all the keys !
        """
        self._conf_order = order

    def has_key(self, key):
        """
        Check if a key exists in data dictionnary
        """
        return key in self._data

    def has_conf_key(self, key):
        """
        Check if a key exists in configuration dictionnary
        """
        return key in self._conf

    def get_key_value(self, key):
        """
        get the value of a key from data
        """
        if key in self._data:
            return self._data[key]
        else:
            raise XPLException("Key not existing")

    def get_conf_key_value(self, key):
        """
        get the value of a key from configuration
        """
        if key in self._conf:
            return self._conf[key]
        else:
            self._log.warning("Key %s does not exist" % key)

    def __str__(self):
        str = "%s\n{\n" % self._type
        if (not self._conf_order):
            for k in self._conf:
                str += "%s=%s\n" % (k, self._conf[k])
        else:
            for k in self._conf_order:
                str += "%s=%s\n" % (k, self._conf[k])
        str += "}\n%s\n{\n" % (self._schema)
        if (not self._data_order):
            for k in self._data:
                str += "%s=%s\n" % (k, self._data[k])
        else:
            for k in self._data_order:
                str += "%s=%s\n" % (k, self._data[k])
        str += "}\n"
        return str


class xPLTimer(xPLModule):
    """
    xPLTimer will call a callback function each n seconds
    """
#    _time = 0
#    _callback = None
#    _timer = None

    def __init__(self, time, cb):
        """
        Constructor : create the internal timer
        @param time : time of loop in second
        @param cb : callback function which will be call eact 'time' seconds
        """
        xPLModule.__init__(self)
        self._callback = cb
        self._time = time
        self._timer = threading.Timer(self._time, self._run)
        self.register_timer(self._timer)
        self.should_stop = False

    def _run(self):
        """
        internal timer loopback function
        """
        if self.should_stop:
            self.unregister_timer(self._timer)
            #self._timer.cancel()
        else:
            self._intimer = threading.Timer(self._time, self._run)
            self._callback()
            self._intimer.start()

    def start(self):
        """
        Start the timer
        """
        self._timer.start()

    def stop(self):
        """
        Stop the timer
        """
        self.should_stop = True
        self.unregister_timer(self._timer)
        self._timer.cancel()



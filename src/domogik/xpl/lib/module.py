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

Module purpose
==============

Base class for all xPL clients

Implements
==========

- xPLModule
- xPLResult

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import time
from socket import gethostname
from domogik.xpl.lib.xplconnector import *
from domogik.xpl.lib.basemodule import BaseModule

class xPLModule():
    '''
    Global module class, manage signal handlers.
    This class shouldn't be used as-it but should be extended by xPL module
    This class is a Singleton
    '''
    __instance = None

    def __init__(self, name = None, stop_cb = None, is_manager = False, reload_cb = None, dump_cb = None):
        '''
        Create xPLModule instance, which defines signal handlers
        @param name : The n,ame of the current module
        @param stop_cb : Method to call when a stop request is received
        @param is_manager : Must be True if the child script is a Domogik Manager process 
        @param reload_cb : Callback to call when a "RELOAD" order is received, if None, 
        nothing will happen
        @param dump_cb : Callback to call when a "DUMP" order is received, if None, 
        nothing will happen

        You should never need to set it to True
        '''
        if len(name) > 8:
            raise IoError, "The name must be 8 chars max"
        if xPLModule.__instance is None and name is None:
            raise AttributeError, "'name' attribute is mandatory for the first instance"
        if xPLModule.__instance is None:
            xPLModule.__instance = xPLModule.__Singl_xPLModule(name, stop_cb, is_manager, reload_cb, dump_cb)
            self.__dict__['_xPLModule__instance'] = xPLModule.__instance
        elif stop_cb is not None:
            xPLModule.__instance.add_stop_cb(stop_cb)

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)


    class __Singl_xPLModule(BaseModule):
        def __init__(self, name, stop_cb = None, is_manager = False, reload_cb = None, dump_cb = None):
            '''
            Create xPLModule instance, which defines system handlers
            @param name : The name of the current module
            @param stop_cb : Additionnal method to call when a stop request is received
            @param is_manager : Must be True if the child script is a Domogik Manager process 
            You should never need to set it to True unless you develop your own manager
            @param reload_cb : Callback to call when a "RELOAD" order is received, if None, 
            nothing will happen
            @param dump_cb : Callback to call when a "DUMP" order is received, if None, 
            nothing will happen
            '''
            BaseModule.__init__(self, name, stop_cb)
            self._log.debug("New system manager instance for %s" % name)
            self._is_manager = is_manager
            self._myxpl = Manager()
            self._l = Listener(self._system_handler, self._myxpl, {'schema' : 'domogik.system',
                'type':'xpl-cmnd'})
            self._reload_cb = reload_cb 
            self._dump_cb = dump_cb

        def _system_handler(self, message):
            """ Handler for domogik system messages
            """
            cmd = message.data['command']
            if not self._is_manager and cmd in ["stop", "reload", "dump", "ping"]:
                self._client_handler(message)
            else:
                self._manager_handler(message)

        def _client_handler(self, message):
            """ Handle domogik system request for an xpl client 
            @param message : the Xpl message received 
            """
            cmd = message.data["command"]
            module = message.data["module"]
            if cmd == "stop" and module == self.get_module_name():
                self._log.info("Someone asked to stop %s, doing." % self.get_module_name())
                self._answer_stop()
                self.force_leave()
            elif cmd == "reload":
                if self._reload_cb is None:
                    log.info("Someone asked to reload config of %s, but the module \
                    isn't able to do it." % self.get_module_name())
                else:
                    self._reload_cb()
            elif cmd == "dump":
                if self._dump_cb is None:
                    log.info("Someone asked to dump config of %s, but the module \
                    isn't able to do it." % self.get_module_name())
                else:
                    self._dump_cb()
            else: #cmd == ping 
                if message.data["module"] in [self.get_module_name(), "*"]:
                    self._answer_ping()

        def _answer_stop(self):
            """ Ack a stop request
            """
            mess = XplMessage()
            mess.set_type("xpl-trig")
            mess.set_schema("domogik.system")
            mess.add_data({"command":"stop", "module": self.get_module_name(), 
                "host": gethostname()})
            self._myxpl.send(mess)

        def _answer_ping(self):
            """ Send a ping reply
            """
            mess = XplMessage()
            mess.set_type("xpl-trig")
            mess.set_schema("domogik.system")
            mess.add_data({"command":"ping", "module": self.get_module_name(), 
                "host": gethostname()})
            self._myxpl.send(mess)

        def _manager_handler(self, message):
            """ Handle domogik system request for the Domogik manager
            @param message : the Xpl message received 
            """


        def force_leave(self):
            '''
            Leave threads & timers
            '''
            self._stop.set()
            for t in self._threads:
                t.join()
                self._log.debug("Thread stopped %s" % t)
                #t._Thread__stop()
            for t in self._timers:
                t.stop()
                self._log.debug("Timer stopped %s" % t)
            for cb in self._stop_cb:
                self._log.debug("Calling stop additionnal method : %s " % cb.__name__)
                cb()

class xPLResult():
    '''
    This object just provides a way to get and set a value between threads
    '''

    def __init__(self):
        self.value = None
        self.event = threading.Event()

    def set_value(self, value):
        '''
        Set the new value of the objet
        '''
        self.value = value

    def get_value(self):
        '''
        Get the value of the objet
        '''
        return self.value

    def get_lock(self):
        '''
        Returns an event item
        '''
        return self.event

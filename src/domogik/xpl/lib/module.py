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

- xPLModule.__init__(self, name = None, stop_cb = None)
- xPLModule.__getattr__(self, attr)
- xPLModule.__setattr__(self, attr, value)
- xPLModule.__init__(self, name, stop_cb = None)
- xPLModule.get_my_logger(self)
- xPLModule.get_module_name(self)
- xPLModule.add_stop_cb(self, cb)
- xPLModule.register_thread(self, thread)
- xPLModule.unregister_thread(self, thread)
- xPLModule.register_timer(self, timer)
- xPLModule.unregister_timer(self, timer)
- xPLModule.should_stop(self)
- xPLModule.get_stop(self)
- xPLModule.hand_leave(self, signum, frame)
- xPLModule.force_leave(self)
- xPLResult.__init__(self)
- xPLResult.set_value(self, value)
- xPLResult.get_value(self)
- xPLResult.get_lock(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import signal
import threading
import time
from domogik.common import logger
import threading

class xPLModule():
    '''
    Global module class, manage signal handlers.
    This class shouldn't be used as-it but should be extended by xPL module
    This class is a Singleton
    '''
    __instance = None

    def __init__(self, name = None, stop_cb = None):
        '''
        Create xPLModule instance, which defines signal handlers
        @param name : The n,ame of the current module
        @param stop_cb : Method to call when a SIGTERM is received
        '''
        if xPLModule.__instance is None and name is None:
            raise AttributeError, "'name' attribute is mandatory for the first instance"
        if xPLModule.__instance is None:
            xPLModule.__instance = xPLModule.__Singl_xPLModule(name, stop_cb)
            self.__dict__['_xPLModule__instance'] = xPLModule.__instance
        elif stop_cb is not None:
            xPLModule.__instance.add_stop_cb(stop_cb)

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)


    class __Singl_xPLModule():
        def __init__(self, name, stop_cb = None):
            '''
            Create xPLModule instance, which defines signal handlers
            @param name : The n,ame of the current module
            @param stop_cb : Method to call when a SIGTERM is received
            '''
            self._threads = []
            self._timers = []
            self._module_name = name
            l = logger.Logger(name)
            self._log = l.get_logger()
            self._log.debug("New signal manager instance for %s" % name)

            self._stop = threading.Event()
            if stop_cb is not None:
                self._stop_cb = [stop_cb]
            else:
                self._stop_cb = []
            signal.signal(signal.SIGTERM, self.hand_leave)

        def get_my_logger(self):
            """
            Returns the associated logger instance
            """
            return self._log

        def get_module_name(self):
            """
            Returns the name of the current module
            """
            return self._module_name

        def add_stop_cb(self, cb):
            '''
            Add an additionnal callback to call when a SIGTERM is received
            '''
            self._stop_cb.append(cb)

        def register_thread(self, thread):
            '''
            Register a thread in the current instance
            Should be called by each thread at start
            @param thread : the thread to add
            '''
            self._log.debug('New thread registered')
            self._threads.append(thread)

        def unregister_thread(self, thread):
            '''
            Unregister a thread in the current instance
            Should be the last action of each thread
            @param thread : the thread to remove
            '''
            if thread in self._threads:
                self._log.debug('Unregister thread')
                self._threads.remove(thread)

        def register_timer(self, timer):
            '''
            Register a time in the current instance
            Should be called by each timer
            @param timer : the timer to add
            '''
            self._log.debug('New timer registered')
            self._timers.append(timer)

        def unregister_timer(self, timer):

            '''
            Unregister a timer in the current instance
            Should be the last action of each timer
            @param timer : the timer to remove
            '''
            if timer in self._timers:
                self._log.debug('Unregister timer')
                self._timers.remove(timer)

        def should_stop(self):
            '''
            Check if the module should stop
            This method should be called to check loop condition in threads
            '''
            return self._stop.isSet()

        def get_stop(self):
            '''
            Returns the Event instance
            '''
            return self._stop

        def hand_leave(self, signum, frame):
            '''
            Handler called when a SIGTERM is catched
            '''
            self._log.debug('Signal SIGTERM catched')
            self.force_leave()

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

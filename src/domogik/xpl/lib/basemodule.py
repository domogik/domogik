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

Base class for all clients

Implements
==========

- BaseModule

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import threading

from domogik.common import logger

class BaseModule():
    """ Basic module class, manage common part of all modules.
    For all xPL modules, the xPLModule class must be use as a basis, not this one.
    This class is a Singleton
    """

    __instance = None 

    def __init__(self, name = None, stop_cb = None):
        """ @param name : Name of current module 
        """
        if BaseModule.__instance is None:
            BaseModule.__instance = BaseModule.__Singl_BaseModule(name, stop_cb)

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        try:
            return getattr(self.__instance, attr)
        except:
            pass

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

    class __Singl_BaseModule:

        def __init__(self, name, stop_cb = None):
            self._threads = []
            self._timers = []
            print "create Base module instance"
            if name is not None:
                self._module_name = name
            l = logger.Logger(name)
            self._log = l.get_logger()
            self._stop = threading.Event()
            self._lock_add_thread = threading.Semaphore()
            self._lock_add_timer = threading.Semaphore()
            self._lock_add_cb = threading.Semaphore()
            if stop_cb is not None:
                self._stop_cb = [stop_cb]
            else:
                self._stop_cb = []

        def get_my_logger(self):
            """
            Returns the associated logger instance
            """
            return self._log

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

        def get_module_name(self):
            """
            Returns the name of the current module
            """
            return self._module_name

        def register_thread(self, thread):
            '''
            Register a thread in the current instance
            Should be called by each thread at start
            @param thread : the thread to add
            '''
            self._lock_add_thread.acquire()
            self._log.debug('New thread registered')
            self._threads.append(thread)
            self._lock_add_thread.release()

        def unregister_thread(self, thread):
            '''
            Unregister a thread in the current instance
            Should be the last action of each thread
            @param thread : the thread to remove
            '''
            self._lock_add_thread.acquire()
            if thread in self._threads:
                self._log.debug('Unregister thread')
                self._threads.remove(thread)
            self._lock_add_thread.release()

        def register_timer(self, timer):
            '''
            Register a time in the current instance
            Should be called by each timer
            @param timer : the timer to add
            '''
            self._lock_add_timer.acquire()
            self._log.debug('New timer registered')
            self._timers.append(timer)
            self._lock_add_timer.release()

        def unregister_timer(self, timer):

            '''
            Unregister a timer in the current instance
            Should be the last action of each timer
            @param timer : the timer to remove
            '''
            self._lock_add_timer.acquire()
            if timer in self._timers:
                self._log.debug('Unregister timer')
                self._timers.remove(timer)
            self._lock_add_timer.release()

        def add_stop_cb(self, cb):
            '''
            Add an additionnal callback to call when a stop request is received
            '''
            self._lock_add_cb.acquire()
            self._stop_cb.append(cb)
            self._lock_add_cb.release()



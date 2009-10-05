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
from domogik.xpl.lib.xplconnector import *
from domogik.xpl.lib.basemodule import BaseModule

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
        @param stop_cb : Method to call when a stop request is received
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


    class __Singl_xPLModule(BaseModule):
        def __init__(self, name, stop_cb = None):
            '''
            Create xPLModule instance, which defines system handlers
            @param name : The name of the current module
            @param stop_cb : Additionnal method to call when a stop request is received
            '''
            BaseModule.__init__(self, name, stop_cb)
            print "create xPLModule instance"
            self._log.debug("New system manager instance for %s" % name)

            self._myxpl = Manager()
            self._l = Listener(self.hand_leave, self._myxpl, {'schema' : 'domogik.system',
                'type':'xpl-cmnd'})

        def hand_leave(self, signum, frame):
            '''
            Handler called when a stop request is catched
            '''
            self._log.debug('Stop request catched, try to end gracefullly')
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

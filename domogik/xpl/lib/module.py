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
# $LastChangedDate: 2009-02-19 13:56:04 +0100 (jeu 19 fév 2009) $
# $LastChangedRevision: 378 $

import signal
import threading
import time
from domogik.common import logger

class xPLModule():
    '''
    Global module class, manage signal handlers.
    This class shouldn't be used as-it but should be extended by xPL module
    '''

    def __init__(self):
        '''
        Create xPLModule instance, which defines signal handlers
        '''
        self._threads = []
        self._timers = []

        l = logger.Logger('signal')
        self._log = l.get_logger()
        self._log.debug("new signal manager instance")

        self._stop = threading.Event()
        signal.signal(signal.SIGTERM, self.hand_leave)

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

    def hand_leave(self, signum, frame):
        '''
        Handler called when a SIGTERM is catched
        This will set event to leave the current threads of the module
        then force threads to stop after 5 seconds.
        '''
        self._log.debug('Signal SIGTERM catched')
        self.force_leave()

    def force_leave(self):
        '''
        Leave threads & timers
        '''
        self._stop.set()
        time.sleep(2)
        for t in self._threads:
            t._Thread__stop()
        for t in self._timers:
            t.cancel()


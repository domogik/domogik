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

Base class for all clients

Implements
==========

- BasePlugin

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import threading
from socket import gethostname 
import sys
import os
import pwd

from domogik.common.defaultloader import DefaultLoader
from domogik.common import logger
from optparse import OptionParser
from domogik.common.daemonize import createDaemon

class BasePlugin():
    """ Basic plugin class, manage common part of all plugins.
    For all xPL plugins, the XplPlugin class must be use as a basis, not this one.
    """
    def __init__(self, name, stop_cb = None, p = None, daemonize = True):
        ''' 
        @param p : An instance of OptionParser. If you want to add extra options to the generic option parser,
        create your own optionparser instance, use parser.addoption and then pass your parser instance as parameter.
        Your options/params will then be available on self.options and self.args
        @param daemonize : If set to False, force the instance *not* to daemonize, even if '-f' is not passed
        on the command line. If set to True (default), will check if -f was added.
        '''

        # First, check if the user is allowed to launch the plugin. The user must be the same as the one defined
        # in the file /etc/default/domogik : DOMOGIK_USER
        Default = DefaultLoader()
        dmg_user = Default.get("DOMOGIK_USER")
        logname = pwd.getpwuid(os.getuid())[0]
        if dmg_user != logname:
            print("ERROR : this Domogik part must be run with the user defined in /etc/default/domogik as DOMOGIK_USER : %s" % dmg_user)
            sys.exit(1)

        # Then, start the plugin...
        self._threads = []
        self._timers = []
        if name is not None:
            self._plugin_name = name
        self._stop = threading.Event()
        self._lock_add_thread = threading.Semaphore()
        self._lock_add_timer = threading.Semaphore()
        self._lock_add_cb = threading.Semaphore()
        if stop_cb is not None:
            self._stop_cb = [stop_cb]
        else:
            self._stop_cb = []

        # options management
        if p is not None and isinstance(p, OptionParser):
            parser = p
        else:
            parser = OptionParser()
        parser.add_option("-V", 
                          "--version", 
                          action="store_true", 
                          dest="display_version", 
                          default=False, 
                          help="Display Domogik version.")
        parser.add_option("-f", 
                          action="store_true", 
                          dest="run_in_foreground", 
                          default=False, 
                          help="Run the plugin in foreground, default to background.")
        (self.options, self.args) = parser.parse_args()
        if self.options.display_version:
            __import__("domogik")
            global_release = sys.modules["domogik"].__version__
            print global_release
            sys.exit(0)
        elif not self.options.run_in_foreground and daemonize:
            createDaemon()
            l = logger.Logger(name)
            self.log = l.get_logger()
            self.log.info("Daemonize plugin %s" % name)
            self.is_daemon = True
        else:
            l = logger.Logger(name)
            self.log = l.get_logger()
            self.is_daemon = False

    def should_stop(self):
        '''
        Check if the plugin should stop
        This method should be called to check loop condition in threads
        '''
        return self._stop.isSet()

    def get_stop(self):
        '''
        Returns the Event instance
        '''
        return self._stop

    def get_plugin_name(self):
        """
        Returns the name of the current plugin
        """
        return self._plugin_name

    def register_thread(self, thread):
        '''
        Register a thread in the current instance
        Should be called by each thread at start
        @param thread : the thread to add
        '''
        # self.log.debug('New thread registered : %s' % thread)
        #Remove all stopped thread from the list
        for t in self._threads:
            if not  t.isAlive():
                self._threads.remove(t)
        if thread in self._threads:
            self.log.info("Try to register a thread twice :" % thread)
        else:
            self._lock_add_thread.acquire()
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
            self.log.debug('Unregister thread')
            self._threads.remove(thread)
        else:
            self.log.warn('Asked to remove a thread not in the list')
        self._lock_add_thread.release()

    def register_timer(self, timer):
        '''
        Register a time in the current instance
        Should be called by each timer
        @param timer : the timer to add
        '''
        if timer in self._timers:
            self.log.info("Try to register a timer twice : %s" % timer)
        else:
            self.log.debug('New timer registered : %s' % timer)
            self._lock_add_timer.acquire()
            self._timers.append(timer)
            self._lock_add_timer.release()

    def unregister_timer(self, timer):
        '''
        Unregister a timer in the current instance
        Should be the last action of each timer
        @param timer : the timer to remove
        '''
        self.log.debug('ASk for timer unregister : %s' % timer)
        self._lock_add_timer.acquire()
        if timer in self._timers:
            self.log.debug('Unregister timer')
            self._timers.remove(timer)
        self._lock_add_timer.release()

    def add_stop_cb(self, cb):
        '''
        Add an additionnal callback to call when a stop request is received
        '''
        self._lock_add_cb.acquire()
        self._stop_cb.append(cb)
        self._lock_add_cb.release()

    def get_sanitized_hostname(self):
        """ Get the sanitized hostname of the host 
        This will lower it and keep only the part before the first dot

        """
        return gethostname().lower().split('.')[0].replace('-','')[0:16]

    def __del__(self):
        if hasattr(self, log):
            self.log.debug("__del__ baseplugin")


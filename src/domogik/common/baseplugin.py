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
from argparse import ArgumentParser
from domogik.common.utils import get_sanitized_hostname
import sys
import os
import pwd
import traceback
import locale

from domogik.common.utils import get_sanitized_hostname
from domogik.common.daemon.daemon import DaemonContext
from domogik.common.defaultloader import DefaultLoader
from domogik.common import logger
from domogik.common.utils import is_already_launched

FIFO_DIR = "/var/run/domogik/"


class BasePlugin(object):
    """ Basic plugin class, manage common part of all plugins.
    For all xPL plugins, the XplPlugin class must be use as a basis, not this one.
    """
    def __init__(self, name, stop_cb=None, p=None, daemonize=True, log_prefix="", log_on_stdout=True):
        '''
        @param p : An instance of ArgumentParser. If you want to add extra options to the generic option parser,
        create your own ArgumentParser instance, use parser.add_argument and then pass your parser instance as parameter.
        Your options/params will then be available on self.options and self.args
        @param daemonize : If set to False, force the instance *not* to daemonize, even if '-f' is not passed
        on the command line. If set to True (default), will check if -f was added.
        @param log_prefix : If set, use this prefix when creating the log file in Logger()
        @param log_on_stdout : if set to True, allow to read logs on both stdout and log file
        '''

        self.set_sanitized_hostname()

        ### First, check if the user is allowed to launch the plugin. The user must be the same as the one defined
        # in the file /etc/default/domogik : DOMOGIK_USER
        default = DefaultLoader()
        dmg_user = default.get("DOMOGIK_USER")
        logname = pwd.getpwuid(os.getuid())[0]
        if dmg_user != logname:
            print(u"ERROR : this Domogik part must be run with the user defined in /etc/default/domogik as DOMOGIK_USER : {0}".format(dmg_user))
            sys.exit(1)

        if name is not None:
            self._plugin_name = name

        logg = logger.Logger(name, use_filename="{0}{1}".format(log_prefix, name), log_on_stdout=log_on_stdout)
        self.log = logg.get_logger(name)

        ### Check if the plugin is not already launched
        # notice that when the plugin is launched from the manager, this call is not done as the manager already does this test before starting a plugin
        # TODO : improve ? currently, as it is not used, we set the type of the client to None
        # in case the 'is_already_launched function would use it a day, we should find a way to get the client type
        res, pid_list = is_already_launched(self.log, None, name)
        if res:
            sys.exit(2)

        ### Create a file to handle the return code
        # this is used by the function set_return_code and get_return_code
        # this is needed as a Domogik process is forked, there is no way to send from a class a return code from the child to the parent.
        try:
            self.return_code_filename = "{0}/{1}_return_code_{2}".format(FIFO_DIR, self._plugin_name, os.getpid())
            # just touch the file to create it
            open(self.return_code_filename, 'a').close()
        except:
            self.log.error("Error while creating return_code file '{0}' : {1}".format(self.return_code_filename, traceback.format_exc()))
            sys.exit(3)

        # set the lcoale to the system one
        locale.resetlocale()
        self.log.debug("Setting locale to system locale: {0}".format(locale.getlocale()))

        ### Start the plugin...
        self._threads = []
        self._timers = []
        self._stop = threading.Event()
        self._lock_add_thread = threading.Semaphore()
        self._lock_add_timer = threading.Semaphore()
        self._lock_add_cb = threading.Semaphore()
        if stop_cb is not None:
            self._stop_cb = [stop_cb]
        else:
            self._stop_cb = []

        ### options management
        if p is not None and isinstance(p, ArgumentParser):
            parser = p
        else:
            parser = ArgumentParser()
        parser.add_argument("-V",
                            "--version",
                            action="store_true",
                            dest="display_version",
                            default=False,
                            help="Display Domogik version.")
        parser.add_argument("-f",
                            action="store_true",
                            dest="run_in_foreground",
                            default=False,
                            help="Run the plugin in foreground, default to background.")
        parser.add_argument("-T",
                            dest="test_option",
                            default=None,
                            help="Test option.")
        self.options = parser.parse_args()
        if self.options.display_version:
            __import__("domogik")
            global_release = sys.modules["domogik"].__version__
            print(global_release)
            sys.exit(0)
        elif not self.options.run_in_foreground and daemonize:
            self.log.info(u"Starting the plugin in background...")
            ctx = DaemonContext()
            #ctx = daemon.DaemonContext()
            ctx.files_preserve = logg.get_fds([name])
            ctx.open()
            self.log.info(u"Daemonize plugin {0}".format(name))
            self.is_daemon = True
        else:
            #l = logger.Logger(name)
            #self.log = l.get_logger()
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
        # self.log.debug('New thread registered : {0}'.format(thread))
        #Remove all stopped thread from the list
        for thread in self._threads:
            if not  thread.isAlive():
                self._threads.remove(thread)
        if thread in self._threads:
            self.log.info(u"Try to register a thread twice: {0}".format(thread))
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
            self.log.info(u"Try to register a timer twice : {0}".format(timer))
        else:
            self.log.debug('New timer registered : {0}'.format(timer))
            self._lock_add_timer.acquire()
            self._timers.append(timer)
            self._lock_add_timer.release()

    def unregister_timer(self, timer):
        '''
        Unregister a timer in the current instance
        Should be the last action of each timer
        @param timer : the timer to remove
        '''
        self.log.debug('ASk for timer unregister : {0}'.format(timer))
        self._lock_add_timer.acquire()
        if timer in self._timers:
            self.log.debug('Unregister timer')
            self._timers.remove(timer)
        self._lock_add_timer.release()

    def add_stop_cb(self, callback):
        '''
        Add an additionnal callback to call when a stop request is received
        '''
        self._lock_add_cb.acquire()
        self._stop_cb.append(callback)
        self._lock_add_cb.release()

    def set_sanitized_hostname(self):
        """ Get the sanitized hostname of the host 
        This will lower it and keep only the part before the first dot

        """
        self._sanitized_hostname = get_sanitized_hostname()

    def get_sanitized_hostname(self):
        """ Get the sanitized hostname of the host
        This will lower it and keep only the part before the first dot

        """
        return self._sanitized_hostname

    def set_return_code(self, value):
        """ Helper to set the return code
            @param value : return code to set
        """
        # the fifo is created in the __init__ :
        # x = os.mkfifo(filename)
        try:
            filel = os.open(self.return_code_filename, os.O_WRONLY)
            os.write(filel, "{0}".format(value))
        except:
            self.log.error("Error while setting return code in '{0}' : {1}".format(self.return_code_filename, traceback.format_exc()))

    def get_return_code(self):
        """ Helper to get the return code set with set_return_code
            @return : return code
        """
        # the fifo is created in the __init__ :
        # x = os.mkfifo(filename)
        try:
            filel = open(self.return_code_filename, 'r')
            lines = filel.readline()
            # just in case the file is empty (no return code set)
            if lines == '':
                lines = 0
            #elif lines == 'True':
            #    lines = 0
            #elif lines == 'False':
            #    lines = 1
            return int(lines)
        except:
            self.log.error("Error while getting return code in '{0}' : {1}".format(self.return_code_filename, traceback.format_exc()))
            return 0
        # http://stackoverflow.com/questions/3806210/python-interprocess-querying-control

    def clean_return_code_file(self):
        """ To be called when we exit (Watcher class) to delete the file used to handle the retur code
        """
        try:
            # TODO :
            # delete the file
            # delete also in /etc/init.d/domogik start|stop ???
            self.log.debug("Delete the file {0}".format(self.return_code_filename))
            #self.log.debug(u"the stack is :")
            #for elt in inspect.stack():
            #    self.log.debug(u"    {0}".format(elt))
            os.unlink(self.return_code_filename)
        except:
            self.log.error("Error while deleting the file '{0}' : {1}".format(self.return_code_filename, traceback.format_exc()))

    def __del__(self):
        if hasattr(self, 'log'):
            self.log.debug(u"__del__ baseplugin")



if __name__ == "__main__":
    import time
    print("aa")
    time.sleep(50)
    print("aa")

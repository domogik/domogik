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

Manage xPL clients on each host

Implements
==========

# TODO : update

@author: Maxence Dunnewind <maxence@dunnewind.net>
@        Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import pyinotify
import os
import sys
import time
import stat
from threading import Event, Thread, Lock, Semaphore
from optparse import OptionParser
import traceback
from subprocess import Popen, PIPE

from domogik.common.configloader import Loader
from domogik.xpl.common.xplconnector import Listener 
from domogik.xpl.common.xplconnector import READ_NETWORK_TIMEOUT
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.common.packagemanager import PackageManager, PKG_PART_XPL
from domogik.common.packagejson import PackageJson, PackageException
from domogik.xpl.common.xplconnector import XplTimer 
from ConfigParser import NoSectionError
from distutils2.version import VersionPredicate, IrrationalVersionError
# the try/except it to handle http://bugs.python.org/issue14317
try:
    from distutils2.index.simple import Crawler
except ImportError:  
    from distutils2.pypi.simple import Crawler
import re
import tempfile
import domogik.xpl.bin
import math
import os


KILL_TIMEOUT = 2
PING_DURATION = 20
# time between 2 pings of a plugin
WAIT_TIME_BETWEEN_PING = 60

PATTERN_DISTUTILS_VERSION = re.compile(".*\(.*\).*")

FIFO_DIR = "/var/run/domogik/"
CONFIG_DIR = "/etc/domogik/"

DESCRIPTION_LEN_IN_DETAIL = 500

class EventHandler(pyinotify.ProcessEvent):
    """ Check a file for any event (creation, modification, etc)
    """
    
    def set_callback(self, callback):
        """ set callback to launch external stuff
        @param callback : callback function
        """
        self.my_callback = callback

    #def set_config_files(self, config_files):
    #    """ set the list of config files
    #    @param list of the monitored config files
    #    """
    #    self._cfg_files = config_files 

    def process_default(self, event):
        """ A file is modified
        """
        print("File modified : %s" % event.pathname)
        self.my_callback()

class SysManager(XplPlugin):
    """ System management from domogik
    """

    def __init__(self):
        """ Init manager and start listeners
        """
        # Semaphore init
        self.sema_installed = Semaphore(value=1)
        self.loader_plugins = Loader('plugins')

        # Check parameters 
        parser = OptionParser()
        parser.add_option("-d", 
                          action="store_true", 
                          dest="start_dbmgr", 
                          default=False, \
                          help="Start database manager if not already running.")
        parser.add_option("-r", 
                          action="store_true", 
                          dest="start_rest", 
                          default=False, \
                          help="Start scenario manager if not already running.")
        parser.add_option("-p", 
                          action="store_true", 
                          dest="allow_ping", 
                          default=False, \
                          help="Activate background ping for all plugins.")
        parser.add_option("-E", 
                          action="store_true", 
                          dest="check_external", 
                          default=False, \
                          help="This manager is the one who looks for hardware.")
        parser.add_option("-t", 
                          action="store", 
                          type="int",
                          dest="custom_ping_duration", 
                          help="Time for xpl ping duration (default : %s)" % PING_DURATION)
        parser.add_option("-w", 
                          action="store", 
                          type="int",
                          dest="wait_time_between_ping", 
                          help="Time between 2 xpl ping (default : %s)" % WAIT_TIME_BETWEEN_PING)
        XplPlugin.__init__(self, name = 'manager', parser=parser)

        # Logger init
        self.log.info("Host : %s" % self.get_sanitized_hostname())

        # Fifo to communicate with the init script
        self._state_fifo = None
        if os.path.exists("%s/dmg-manager-state" % FIFO_DIR):
            mode = os.stat("%s/dmg-manager-state" % FIFO_DIR).st_mode
            if mode & stat.S_IFIFO == stat.S_IFIFO:
                self._state_fifo = open("%s/dmg-manager-state" % FIFO_DIR,"w")    
                self._startup_count = 0
                self._startup_count_lock = Lock()
                self._write_fifo("NONE","\n")

        # Get config
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        self._pid_dir_path = conf['pid_dir_path']
        # plugin installation path
        if conf.has_key('package_path'):
            self._package_path = conf['package_path']
            self.log.info("Set package path to '%s' " % self._package_path)
            print("Set package path to '%s' " % self._package_path)
            # TODO : move the sys.path.append near the __import__ and add a test if already appended ?
            sys.path = [self._package_path] + sys.path
            self._json_plugin_directory = os.path.join(self._package_path, "domogik_packages/plugins/")
            self._json_external_directory = os.path.join(self._package_path, "domogik_packages/externals/")
            self.package_mode = True
        else:
            self.log.info("No package path defined in config file")
            self._package_path = None
            self._json_plugin_directory = os.path.join(conf['src_prefix'], "share/domogik/plugins/")
            self._json_external_directory = os.path.join(conf['src_prefix'], "share/domogik/externals/")
            self.package_mode = False

        self._pinglist = {}
        self._plugins = []
        self._externals = []
        self._external_models = []
        
        # To ensure rest is started
        self._rest_started = False

        if self.options.allow_ping:
            msg = "xpl ping activated"
        else:
            msg = "xpl ping not activated"
        print(msg)
        self.log.info(msg)

        if self.options.custom_ping_duration != None:
            self.ping_duration = self.options.custom_ping_duration
        else:
            self.ping_duration = PING_DURATION
        msg = "xpl ping duration=%s" % self.ping_duration
        print(msg)
        self.log.info(msg)

        if self.options.wait_time_between_ping != None:
            self.wait_time_between_ping = self.options.wait_time_between_ping
        else:
            self.wait_time_between_ping = WAIT_TIME_BETWEEN_PING
        msg = "Delay between 2 xpl ping=%s" % self.wait_time_between_ping
        print(msg)
        self.log.info(msg)

        try:
            #Start dbmgr
            if self.options.start_dbmgr:
                self._inc_startup_lock()
                if self._check_component_is_running("dbmgr", startup = True):
                    self.log.warning("Manager started with -d, but a database manager is already running")
                    self._write_fifo("WARN", "Manager started with -d, but a database manager is already running\n")
                    self._dec_startup_lock()
                else:
                    thr_dbmgr = Thread(None,
                                       self._start_plugin,
                                       "start_plugin_dbmgr",
                                       ("dbmgr",),
                                       {"ping" : False, "startup" : True})
                    self.register_thread(thr_dbmgr)
                    thr_dbmgr.start()
    
            #Start rest
            if self.options.start_rest:
                self._inc_startup_lock()
                if self._check_component_is_running("rest", startup = True):
                    self.log.warning("Manager started with -r, but a REST manager is already running")
                    self._write_fifo("WARN", "Manager started with -r, but a REST manager is already running\n")
                    self._dec_startup_lock()
                else:
                    thr_rest = Thread(None,
                                       self._start_plugin,
                                       "start_plugin_rest",
                                       ("rest",),
                                       {"ping" : False, "startup" : True})
                    self.register_thread(thr_rest)
                    thr_rest.start()
    
            # Get components:
            self._list_plugins()
            if self.options.check_external == True:
                self._list_external_models()
 
            # Start plugins at manager startup
            startup_plugins = Thread(None, self._startup_plugins, "th_startup_plugins", (), {})
            self.register_thread(startup_plugins)
            startup_plugins.start()
            
            # Define listeners
            Listener(self._system_action_cb, self.myxpl, {
                'schema': 'domogik.system',
                'xpltype': 'xpl-cmnd',
            })
    
            # Define listeners for packages
            Listener(self._package_cb, self.myxpl, {
                'schema': 'domogik.package',
                'xpltype': 'xpl-cmnd',
            })

            # PackageManager instance
            self.pkg_mgr = PackageManager()
    
            # hbeat management for externals
            if self.options.check_external:
                Listener(self._refresh_external_list, self.myxpl, {
                    'schema': 'hbeat.app',
                    'xpltype': 'xpl-stat',
                })
                Listener(self._refresh_external_list, self.myxpl, {
                    'schema': 'hbeat.basic',
                    'xpltype': 'xpl-stat',
                })
                # TODO : handle hbeat.end

            # hbeat management for plugins
            Listener(self._set_component_running, self.myxpl, 
                 {'schema':'hbeat.app', 
                  'xpltype':'xpl-stat'})
            Listener(self._set_component_not_running, self.myxpl, 
                 {'schema':'hbeat.end', 
                  'xpltype':'xpl-stat'})

            # define timers
            if self.options.check_external:
                external_timer = XplTimer(15, 
                                          self._check_external_status, 
                                          self.myxpl)
                external_timer.start()

            # inotify 
            wmgr = pyinotify.WatchManager() # Watch manager
            mask = pyinotify.IN_MODIFY | pyinotify.IN_MOVED_TO | pyinotify.IN_DELETE | pyinotify.IN_CREATE # watched events
            notify_handler = EventHandler()
            notify_handler.set_callback(self._reload_configuration_file)
            #notify_handler.set_config_files(self.get_config_files())
            notifier = pyinotify.ThreadedNotifier(wmgr, notify_handler)
            notifier.setName("thread_notifier")
            notifier.start()
            config_files_dir = [self._json_plugin_directory,
                                self._json_external_directory,
                                CONFIG_DIR]
            #for fic in  self.get_config_files():
            #    config_files_dir.append(os.path.dirname(fic))
            for direc in set(config_files_dir):
                #wdd = wmgr.add_watch(direc, mask, rec = True)
                wmgr.add_watch(direc, mask, rec = True)
            self.add_stop_cb(notifier.join)

            self.enable_hbeat()
            print("Ready!")
    
            if self._state_fifo != None:
                while self._startup_count > 0:
                    time.sleep(1)
            self.log.info("System manager initialized")
            self._write_fifo("OK", "System manager initialized.\n")
            if self._state_fifo != None:
                self._state_fifo.close()

            ### Send installed packages list
            if self.package_mode == True:
                self._pkg_list_installed()

            ### make an eternal loop to ping plugins
            # the goal is to detect manually launched plugins
            if self.options.allow_ping:
                while True:
                    time.sleep(self.wait_time_between_ping)
                    ping_thread = {}
                    for plugin in self._plugins:
                        name = plugin["name"]
                        ping_thread[name] = Thread(None,
                                             self._check_component_is_running,
                                             "ping_%s" % name,
                                             (name,), 
                                             {"only_one_ping" : True})
                        self.register_thread(ping_thread[name])
                        ping_thread[name].start()

            self.wait()
        except:
            self.log.error("%s" % traceback.format_exc())
            print("%s" % traceback.format_exc())

    def _startup_plugins(self):
        """ Start plugins, with auto start option, after rest full init.
            Called during manager startup.
        """
        # waiting for rest response
        if self._waitForRest() :
            self.log.debug("Check non-system plugins to start at manager startup...")
            self._write_fifo("INFO", "Check non-system plugins to start at manager startup.\n")
            comp_thread = {}
            for plugin in self._plugins:
                if plugin["check_startup_option"]:
                    name = plugin["name"]
                    self.log.debug("%s..." % name)
                    self._config = Query(self.myxpl, self.log)
                    startup = self._config.query(name, 'startup-plugin')
                    # start plugin
                    if startup == 'True':
                        self.log.debug("Starting %s" % name)
                        self._inc_startup_lock()
                        comp_thread[name] = Thread(None,
                                                       self._start_plugin,
                                                       "start_plugin_%s" % name,
                                                       (name,),
                                                       {"startup" : True})
                        self.register_thread(comp_thread[name])
                        comp_thread[name].start()
        else : 
            self.log.warning("Manager start-up can't start plugins, REST doesn't respond.")

    def _waitForRest(self):
        """ Wait until the rest http server is available, timeout = 180s output.
        """
        import urllib2

        cfg_rest = Loader('rest')
        config_rest = cfg_rest.load()
        conf_rest = dict(config_rest[1])
        if conf_rest['rest_use_ssl'] == 'False' : protocol = 'http'
        else : protocol = 'https'
        rest = "%s://%s:%s" % (protocol, conf_rest['rest_server_ip'], conf_rest['rest_server_port'])
        the_url = "%s/base/device/list" % (rest)
        rest_ok = False
        time_out = False
        t = time.time()
        cptTry = 1
        waitTime = 3
        while not self.get_stop().isSet() and not time_out and not rest_ok:
            if self._rest_started :
                self.log.debug("Try to join rest HTTP at :{0}".format(the_url))
                try :
                    req = urllib2.Request(the_url)
                    handle = urllib2.urlopen(req)
                    devices = handle.read()
                except IOError,  e:
                    if time.time() - t >= 180 : time_out = True
                    else : 
                        if cptTry >= 2 : waitTime = 2
                        cptTry +=1
                        self.log.debug("REST no response, wait {0}s for try {1}. {2}".format(waitTime, cptTry,  e.reason))
                        self.get_stop().wait(waitTime)
                else : rest_ok = True
            else :
                if time.time() - t >= 180 : time_out = True
                else:
                    self.log.debug("REST not started, wait 3s more (waiting time {0:.2f}s).".format(time.time() - t))
                    self.get_stop().wait(3)
        if rest_ok : return True
        else:
            if time_out :
                self.log.error("REST didn't respond (timeout 180s), plugins are not started with auto start option:(")
                return False
            else :
                self.log.error("Waiting for REST response stopped in starting process, plugins are not started.")
                return False

    def _reload_configuration_file(self):
        """ reload all plugins and external list
        """
        print("Reloading plugin list")
        self.log.info("Reloading plugin list")
        self._list_plugins()

    def _write_fifo(self, level, message):
        """ Write the message into _state_fifo fifo, with ansi color
        @param level : one of OK,INFO,WARN,ERROR,NONE
        @param message : the message to write
        """
        if self._state_fifo == None:
            return
        colors = {
            "OK" : '\033[92m',
            "INFO" : '\033[94m',
            "WARN" : '\033[93m',
            "ERROR" : '\033[91m',
            "ENDC" : '\033[0m'
        }
        if level not in colors.keys() and level != "NONE":
            level = "INFO"
        if not self._state_fifo.closed:
            if level == "NONE":
                self._state_fifo.write(message)
            else:
                self._state_fifo.write("%s[%s] %s %s" % (colors[level], level, message, colors["ENDC"]))
            self._state_fifo.flush()
    
    def _inc_startup_lock(self):
        """ Increment self._startup_count
        """
        if self._state_fifo == None:
            return
        self.log.info("lock++ acquire : %s" % self._startup_count)
        self._startup_count_lock.acquire()
        self._startup_count = self._startup_count + 1
        self._startup_count_lock.release()
        self.log.info("lock++ released: %s" % self._startup_count)
    
    def _dec_startup_lock(self):
        """ Decrement self._startup_count
        """
        if self._state_fifo == None:
            return
        self.log.info("lock-- acquire : %s" % self._startup_count)
        self._startup_count_lock.acquire()
        self._startup_count = self._startup_count - 1
        self._startup_count_lock.release()
        self.log.info("lock-- released: %s" % self._startup_count)

    def _system_action_cb(self, message):
        """ Internal callback for receiving system messages
        @param message : xpl message received
        """
        cmd = message.data['command']
        self.log.debug("Call _system_action_cb for cmd='%s'" % cmd)
        print("Call _system_action_cb for cmd='%s'" % cmd)

        try:
            plg = message.data['plugin']
        except KeyError:
            plg = "*"
        try:
            host = message.data["host"]
        except KeyError:
            host = "*"

        # error if no plugin in list
        error = ""
        if plg != "*":
            if self.get_sanitized_hostname() == host and \
               cmd != "enable" and \
               cmd != "disable" and \
               self._is_plugin(plg) == False:
                self._invalid_plugin(cmd, plg)
                return

        # if no error at this point, process
        if error == "":
            self.log.debug("System request %s for host %s, plugin %s. current hostname : %s" % (cmd, host, plg, self.get_sanitized_hostname()))

            # start plugin
            if cmd == "start" and host == self.get_sanitized_hostname() and plg not in ["rest", "dbmgr", "*"]:
                self._start_plugin(plg)

            # stop plugin
            if cmd == "stop" and host == self.get_sanitized_hostname() and plg not in ["rest", "dbmgr", "*"]:
                self._stop_plugin(plg)

            # enable plugin
            if cmd == "enable" and host == self.get_sanitized_hostname() and plg not in ["rest", "dbmgr", "*"]:
                self._enable_plugin(plg)

            # disable plugin
            if cmd == "disable" and host == self.get_sanitized_hostname() and plg not in ["rest", "dbmgr", "*"]:
                self._disable_plugin(plg)

            # list plugin
            elif cmd == "list" and (host == self.get_sanitized_hostname() or host == "*"):
                self._send_plugin_list()

            # detail plugin
            elif cmd == "detail": # and host == self.get_sanitized_hostname():
                                  # no check on host for external
                self._send_plugin_detail(plg, host)

        # if error
        else:
            self.log.error("Error detected : %s, request %s has been cancelled" % (error, cmd))

    def _invalid_plugin(self, cmd, plg):
        """ send an invalid plugin message
             @param cmd : command
             @param plg : plugin name
        """
        error = "Component %s doesn't exists on %s" % (plg, self.get_sanitized_hostname())
        self.log.debug(error)
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'host' : self.get_sanitized_hostname()})
        mess.add_data({'command' :  cmd})
        mess.add_data({'plugin' :  plg})
        mess.add_data({'error' :  error})
        self.myxpl.send(mess)

    def _start_plugin(self, plg, ping = True, startup = False):
        """ Start a plugin
            @param plg : plugin name
            @param startup : set it to True if you call _start_plugin during manager start
        """
        error = ""
        self.log.debug("Ask to start %s on %s" % (plg, self.get_sanitized_hostname()))
        if startup:
            self._write_fifo("INFO", "Start %s on %s\n" % (plg, self.get_sanitized_hostname()))
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'host' : self.get_sanitized_hostname()})
        mess.add_data({'command' :  'start'})
        mess.add_data({'plugin' :  plg})
        if ping == True:
            if self._check_component_is_running(plg, only_one_ping = True):
                error = "Component %s is already running on %s" % (plg, self.get_sanitized_hostname())
                self.log.warning(error)
                if startup:
                    self._write_fifo("ERROR", "Component %s is already running\n" % plg)
                mess.add_data({'error' : error})
                self.myxpl.send(mess)
                return
        pid = self._exec_plugin(plg)
        if pid:
            # let's check if component successfully started
            time.sleep(READ_NETWORK_TIMEOUT + 0.5) # time a plugin took to die.
            # component started
            if self._check_component_is_running(plg):
                if plg == "rest" : self._rest_started = True
                self.log.debug("Component %s started with pid %s" % (plg,
                        pid))
                if startup:
                    self._write_fifo("OK", "Component %s started with pid %s\n" % (plg,
                            pid))

            # component failed to start
            else:
                error = "Component %s failed to start. Please look in this component log files" % plg
                self.log.error(error)
                if startup:
                    self._write_fifo("ERROR", error + "\n")
                self._delete_pid_file(plg)
            if error != "":
                mess.add_data({'error' :  error})
        if startup:
            self._dec_startup_lock()
        self.myxpl.send(mess)

    def _stop_plugin(self, plg):
        """ stop a plugin
            @param plg : plugin name
        """
        self.log.debug("Check plugin stops : %s on %s" % (plg, self.get_sanitized_hostname()))
        if self._check_component_is_running(plg) == False:
            error = "Component %s is not running on %s" % (plg, self.get_sanitized_hostname())
            self.log.warning(error)
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('domogik.system')
            mess.add_data({'command' : 'stop'})
            mess.add_data({'host' : self.get_sanitized_hostname()})
            mess.add_data({'plugin' : plg})
            mess.add_data({'error' : error})
            self.myxpl.send(mess)
        else:
            pid = int(self._read_pid_file(plg))
            self.log.debug("Check if process (pid %s) is down" % pid)
            if pid != 0:
                try:
                    time.sleep(KILL_TIMEOUT)
                    os.kill(pid, 0)
                except OSError:
                    self.log.debug("Process %s down" % pid)
                else:
                    self.log.debug("Process %s up. Try to kill it" % pid)
                    try:
                        os.kill(pid, 15)
                        self.log.debug("...killed (%s)" % pid)
                    except OSError:
                        self.log.debug("Process %s resists to kill -15... Detail : %s" % (pid, str(sys.exc_info()[1])))
                        self.log.debug("Trying kill -9 on process %s..." % pid)
                        time.sleep(KILL_TIMEOUT)
                        try:
                            os.kill(pid, 9)
                        except OSError:
                            self.log.debug("Process %s resists again... Failed to stop process. Detail : %s" % (pid, str(sys.exc_info()[1])))
                            return
                self._delete_pid_file(plg)
                 
                self._set_status(plg, "OFF")
            else:
                self.log.warning("Pid file contains no pid!")


    def _check_component_is_running(self, name, startup = False, only_one_ping = False):
        """ This method will send a ping request to a component on localhost
        and wait for the answer (max 5 seconds).
        @param name : component name
        @param startup : set to True if the method is called during manager startup 
        @param only_one_ping : set to True if you want to ping once only
        Notice : sort of a copy of this function is used in rest.py to check 
                 if a plugin is on before using a helper
                 Helpers will change in future, so the other function should
                 disappear. There is no need for the moment to put this function
                 in a library
        """
        self.log.debug("Check if '%s' is running... (thread)" % name)
        if startup:
            self._write_fifo("INFO", "Check if %s is running.\n" % name)
        self._pinglist[name] = Event()
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        if name != "*":
            mess.set_target("domogik-%s.%s" % (name, self.get_sanitized_hostname()))
        mess.set_schema('hbeat.request')
        mess.add_data({'command' : 'request'})
        my_listener = Listener(self._set_component_running, 
                 self.myxpl, 
                 {'schema':'hbeat.app', 
                  'xpltype':'xpl-stat', 
                  'xplsource':"domogik-%s.%s" % (name, self.get_sanitized_hostname())},
                 cb_params = {'name' : name})
        if only_one_ping:
            max_ping = 1
        else:
            max_ping = self.ping_duration
        while max_ping != 0:
            self.myxpl.send(mess)
            time.sleep(1)
            max_ping -= 1
            if self._pinglist[name].isSet():
                break
        my_listener.unregister()
        if self._pinglist[name].isSet():
            self.log.debug("'%s' is running" % name)
            self._set_status(name, "ON")
            return True
        else:
            self.log.debug("'%s' is not running" % name)
            self._set_status(name, "OFF")
            return False

    def _set_component_running(self, message, args = {}):
        """ Set plugin state to true
            Called from check_component_is_running : 
                Set the Event to true if an answer was received
            Called from the main Listener :
                Set the plugin to "on" in the list
        """
        # if this function is called from check_component_is_running
        if args.has_key("name"):
            self.log.debug("Component %s is running" % args["name"])
            self._pinglist[args["name"]].set()
        # if this function is called from the main listener
        else:
            if message.source_vendor_id == "domogik":
                name = message.source_device_id
                # hardcoded values for no plugin part of domogik
                if name not in ("manager", "rest", "dbmgr"):
                    self._set_status(name, "ON")

    def _set_component_not_running(self, message):
        """ Set the component to off in the list
        """
        vendor_device = message.source.split(".")[0]
        vendor_id = vendor_device.split("-")[0].lower()
        device_id = vendor_device.split("-")[1].lower()
        instance = message.source.split(".")[1]
        if self.get_sanitized_hostname() == instance:
            self._set_status(device_id, "OFF")

    def _exec_plugin(self, name):
        """ Internal method
        Start the plugin
        @param name : the name of the component to start
        This method does *not* check if the component exists
        """
        self.log.info("Start the component %s" % name)
        print("Start %s" % name)
        if name == "dbmgr" or name == "rest":
            plg_path = "domogik.xpl.bin." + name
        else:
            plg_path = "domogik_packages.xpl.bin." + name
        __import__(plg_path)
        plugin = sys.modules[plg_path]
        self.log.debug("Component path : %s" % plugin.__file__)
        subp = Popen("export PYTHONPATH=%s && /usr/bin/python %s" % (self._package_path, plugin.__file__), \
                     shell=True)
        pid = subp.pid
        subp.communicate()
        return pid

    def _delete_pid_file(self, plg):
        """ Delete pid file
        @param plg : plugin name
        """
        self.log.debug("Delete pid file")
        pidfile = os.path.join(self._pid_dir_path,
                plg + ".pid")
        return os.remove(pidfile)

    def _read_pid_file(self, plg):
        """ Read the pid in a file
        @param plg : plugin name
        """
        pidfile = os.path.join(self._pid_dir_path,
                plg + ".pid")
        try:
            fil = open(pidfile, "r")
            return fil.read()
        except:
            return 0

    def _set_status(self, plg, state):
        """ Set status for a component
        @param plg : plugin name
        @param state : status
        """ 
        for plugin in self._plugins:
            if plugin["name"] == plg:
                # if status changed, set new status and send event
                if plugin["status"] != state:
                    plugin["status"] = state
                    self._send_plugin_list()

    def _list_external_models(self):
        """ List domogik external models
        """
        print("Start listing available external members models")
        self.log.debug("Start listing available external members models")

        self._external_models = []

        # Get external list
        try:
            # list json files
            try:
                external_list = []
                for root, dirs, files in os.walk(self._json_external_directory):
                    for fic in files:
                        if fic[-5:] == ".json":
                            external_list.append(fic)
            except:
                msg = "Error accessing external directory : %s. You should create it" % str(traceback.format_exc())
                print(msg)
                self.log.error(msg)
                return 

            for external in external_list:
                external = external[0:-5]
                print(external)
                self.log.info("==> %s" % (external))
                # try open json file
                json_file = "%s/%s.json" % (self._json_external_directory, external)
                try:
                    # get data for external
                    pkg_json = PackageJson(path = json_file).json
   
                    # register plugin
                    self._external_models.append({"type" : pkg_json["identity"]["type"],
                                      "name" : pkg_json["identity"]["id"], 
                                      "description" : pkg_json["identity"]["description"], 
                                      "technology" : pkg_json["identity"]["category"],
                                      "version" : pkg_json["identity"]["version"],
                                      "documentation" : pkg_json["identity"]["documentation"],
                                      "vendor_id" : pkg_json["external"]["vendor_id"],
                                      "device_id" : pkg_json["external"]["device_id"]})

                except:
                    msg = "Error reading json file : %s\n%s" % (json_file, str(traceback.format_exc()))
                    print(msg)
                    self.log.error(msg)
        except NoSectionError:
            pass 

        return


    def _refresh_external_list(self, message):
        """ Refresh external list
            @param message : xpl message
        """
        vendor_device = message.source.split(".")[0]
        vendor_id = vendor_device.split("-")[0].lower()
        device_id = vendor_device.split("-")[1].lower()
        instance = message.source.split(".")[1]

        # don't handle domogik elements
        if vendor_id == "domogik":
            return

        unknown = True
        for external_model in self._external_models:
            msg_vendor_device = "%s-%s" % (external_model["vendor_id"], 
                                           external_model["device_id"])
            unknown = True
            if vendor_device == msg_vendor_device:
                unknown = False
                self.log.debug("Refresh external members list with : %s" % str(message))
                found = False
                for external in self._externals:
                    if external["host"] == instance and external["vendor_id"] == vendor_id and external["device_id"] == device_id:
                        external["status"] = "ON"
                        external["last_seen"] = time.time()
                        # interval converted from minutes to seconds : *60
                        external["interval"] = int(message.data["interval"])*60
                        found = True
                        self.log.info("Set external member status ON : %s on %s" % \
                                                   (external["name"], instance))
                        # external config part
                        # - external configuration is given in hbeat.app body
                        external["configuration"] = self._get_external_configuration(message)
                     
                if found == False:
                    # external config part
                    # - external configuration is given in hbeat.app body
                    configuration = self._get_external_configuration(message)
                    self._externals.append({"type" : external_model["type"],
                              "name" : external_model["name"], 
                              "description" : external_model["description"], 
                              "technology" : external_model["technology"],
                              "status" : "ON",
                              "host" : instance,
                              "version" : external_model["version"],
                              "documentation" : external_model["documentation"],
                              "vendor_id" : external_model["vendor_id"],
                              "device_id" : external_model["device_id"],
                              "configuration" : configuration,
                              "interval" : int(message.data["interval"]) * 60,
                              "last_seen" : time.time()})
                    self.log.info("Add external : %s on %s" % \
                                             (external_model["name"], instance))
        # an unknown external member : we will add it in the list (only for information)
        if unknown:
            found = False
            for external in self._externals:
                if external["host"] == instance and external["vendor_id"] == vendor_id and external["device_id"] == device_id:
                    external["status"] = "ON"
                    external["last_seen"] = time.time()
                    # interval converted from minutes to seconds : *60
                    external["interval"] = int(message.data["interval"])*60
                    external["configuration"] = self._get_external_configuration(message)
                    found = True
                    self.log.info("Set unknown external member status ON : %s on %s" % \
                                               (vendor_device, instance))
            if found == False:
                self._externals.append({"type" : "external",
                          "name" : vendor_device,
                          "description" : " ",
                          "technology" : "unknown",
                          "status" : "ON",
                          "host" : instance,
                          "version" : "n/a",
                          "documentation" : "#",
                          "vendor_id" : vendor_id,
                          "device_id" : device_id,
                          "configuration" :  self._get_external_configuration(message),
                          "interval" : int(message.data["interval"]) * 60,
                          "last_seen" : time.time()})
                self.log.info("Add unknown external : %s on %s" % \
                                         (vendor_device, instance))

    def _get_external_configuration(self, message):
        """ Get external configuration from hbeat message
        @param message : hbeat message
        """
        config = []
        idx = 0
        for conf in message.data:
            # we take all keys, except interval
            if conf == "interval":
                pass
            else:
                config.append( {"id" : idx,
                                "key" : conf,
                                "value" : message.data[conf]})
                idx += 1
        return config

    def _clean_external_list(self, id):
        """ Clean external members
            @param id : id of the external to remove from the list
        """
        tmp_externals = []
        for external in self._externals:
            if external["name"]!= id:
                tmp_externals.append(external)
        self._externals = tmp_externals

    def _clean_unknow_from_external_list(self):
        """ Clean unknown external members
        """
        tmp_externals = []
        for external in self._externals:
            if external["technology"].lower() != "unknown":
                tmp_externals.append(external)
        self._externals = tmp_externals

    def _check_external_status(self):
        """ Check if externals are always present
        """
        # send a hbeat request
        self._send_broadcast_hbeat()

        # wait for answers
        time.sleep(1)
 
        # process
        for external in self._externals:
            # if external was not seen in the interval its tells, 
            # we consider it as OFF
            if time.time() - external["last_seen"] > external["interval"]:
                external["status"] = "OFF"
                self.log.info("Set external member status OFF : %s on %s" % \
                                       (external["name"], external["host"]))


    def _list_plugins(self):
        """ List domogik plugins
        """
        self.log.debug("Start listing available plugins")

        self._plugins = []

        # Getplugin list
        cfg_plugins = self.loader_plugins.load()[1]
        plugin_list = dict(cfg_plugins)
        for plugin in plugin_list:
            self.log.info("==> %s (%s)" % (plugin, plugin_list[plugin]))
            if plugin_list[plugin] == "enabled":
                print(plugin)
                # try open json file
                json_file = "%s/%s.json" % (self._json_plugin_directory, plugin)
                try:
                    # get data for plugin
                    pkg_json = PackageJson(path = json_file).json

                    # register plugin
                    self._plugins.append({"type" : pkg_json["identity"]["type"],
                                      "name" : pkg_json["identity"]["id"], 
                                      "description" : pkg_json["identity"]["description"], 
                                      "technology" : pkg_json["identity"]["category"],
                                      "status" : "OFF",
                                      "host" : self.get_sanitized_hostname(), 
                                      "version" : pkg_json["identity"]["version"],
                                      "documentation" : pkg_json["identity"]["documentation"],
                                      "configuration" : pkg_json["configuration"],
                                      "check_startup_option" : True})

                except:
                    print("Error reading json file : %s\n%s" % (json_file, str(traceback.format_exc())))
                    self.log.error("Error reading json file : %s. Detail : \n%s" % (json_file, str(traceback.format_exc())))

        return


    def _is_plugin(self, name):
        """ Is a component a plugin or external?
        @param name : component name to check
        """
        for plugin in self._plugins:
            if plugin["name"] == name:
                return True
        for external in self._externals:
            if external["name"] == name:
                return True
        return False

    def _send_plugin_list(self):
        """ send compoennt list
        """
        try:
            self.log.debug("Call _send_plugin_list")
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('domogik.system')
            mess.add_data({'command' :  'list'})
            # notice : this entry seems to be duplicate because of pluginX-host
            # entries. But this is need by rest in /plugin/list for multi hosts
            mess.add_data({'host' :  self.get_sanitized_hostname()})
            # plugins
            idx = 0
            for plugin in self._plugins:
                mess.add_data({'plugin'+str(idx)+'-name' : plugin["name"]})
                mess.add_data({'plugin'+str(idx)+'-type' : plugin["type"]})
                mess.add_data({'plugin'+str(idx)+'-techno' : plugin["technology"]})
                #mess.add_data({'plugin'+str(idx)+'-desc' : plugin["description"]})
                mess.add_data({'plugin'+str(idx)+'-status' : plugin["status"]})
                mess.add_data({'plugin'+str(idx)+'-host' : plugin["host"]})
                idx += 1
            # externals
            for external in self._externals:
                mess.add_data({'plugin'+str(idx)+'-name' : external["name"]})
                mess.add_data({'plugin'+str(idx)+'-type' : external["type"]})
                mess.add_data({'plugin'+str(idx)+'-techno' : external["technology"]})
                #mess.add_data({'plugin'+str(idx)+'-desc' : external["description"]})
                mess.add_data({'plugin'+str(idx)+'-status' : external["status"]})
                mess.add_data({'plugin'+str(idx)+'-host' : external["host"]})
                idx += 1
            # mess.add_data({'host' : self.get_sanitized_hostname()})
            self.log.debug("Send xPL in function send_plugin_list")
            self.myxpl.send(mess)
        except:
            self.log.error("Error while sending plugin list : %s" % traceback.format_exc())

    def _send_plugin_detail(self, plg, host):
        """ send details about a component 
            @param plg : plugin name
            @param host : hostname for external members requests
        """
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' :  'detail'})
        host_in_msg = False
        for plugin in self._plugins:
            if plugin["name"] == plg:
                for conf in plugin["configuration"]:
                    mess.add_data({'cfg'+str(conf["id"])+'-key' : conf["key"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-type' : conf["type"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-desc' : conf["description"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-default' : conf["default"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-int' : conf["interface"]})
                    if conf["type"] == "enum":
                        mess.add_data({'cfg'+str(conf["id"])+'-options' : ','.join( map( str, conf["options"] ) )})
                    if conf["optionnal"] == "yes":
                        mess.add_data({'cfg'+str(conf["id"])+'-opt' : conf["optionnal"]})
                mess.add_data({'type' :  plugin["type"]})
                mess.add_data({'plugin' :  plugin["name"]})

                # Cut description in multiple parts
                the_desc = plugin["description"].replace('\n', "\\n")
                cut_desc = [the_desc[n*DESCRIPTION_LEN_IN_DETAIL:(n+1)*DESCRIPTION_LEN_IN_DETAIL ] for n in range(int(math.ceil((len(the_desc) / float(DESCRIPTION_LEN_IN_DETAIL))))) ]
                idx = 0
                for elt_desc in cut_desc:
                    mess.add_data({'description%s' % idx :  elt_desc})
                    idx += 1
                mess.add_data({'technology' :  plugin["technology"]})
                mess.add_data({'status' :  plugin["status"]})
                mess.add_data({'version' :  plugin["version"]})
                mess.add_data({'documentation' :  plugin["documentation"]})
                mess.add_data({'host' : self.get_sanitized_hostname()})
                host_in_msg = True
        for external in self._externals:
            if external["name"] == plg and external["host"] == host:
                for conf in external["configuration"]:
                    mess.add_data({'cfg'+str(conf["id"])+'-id' : conf["id"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-key' : conf["key"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-value' : conf["value"]})
                mess.add_data({'type' :  external["type"]})
                mess.add_data({'plugin' :  external["name"]})
 
                # Cut description in multiple parts
                the_desc = external["description"].replace('\n', "\\n")
                cut_desc = [the_desc[n*DESCRIPTION_LEN_IN_DETAIL:(n+1)*DESCRIPTION_LEN_IN_DETAIL ] for n in range(int(math.ceil((len(the_desc) / float(DESCRIPTION_LEN_IN_DETAIL))))) ]
                idx = 0
                for elt_desc in cut_desc:
                    mess.add_data({'description%s' % idx :  elt_desc})
                    idx += 1
                mess.add_data({'technology' :  external["technology"]})
                mess.add_data({'status' :  external["status"]})
                mess.add_data({'version' :  external["version"]})
                mess.add_data({'documentation' :  external["documentation"]})
                mess.add_data({'host' : external["host"]})
                host_in_msg = True
        if host_in_msg == False:
            mess.add_data({'host' : self.get_sanitized_hostname()})


        self.myxpl.send(mess)


    def _enable_plugin(self, name):
        """ Enable a plugin in domogik.cfg file
            @param name : plugin to enable
        """
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'enable'})
        mess.add_data({'host' : self.get_sanitized_hostname()})
        mess.add_data({'plugin' : name})

        subp = Popen("dmgenplug %s" % name, shell=True)
        subp.communicate()
        if self.package_mode == True:
            self._pkg_list_installed()
        time.sleep(1) # make sure rest receive the updated list before the ack of enable
        self.myxpl.send(mess)          

    def _disable_plugin(self, name):
        """ Disable a plugin in domogik.cfg file
            @param name : plugin to disable
        """
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'disable'})
        mess.add_data({'host' : self.get_sanitized_hostname()})
        mess.add_data({'plugin' : name})

        # check the component is nut running
        if self._check_component_is_running(name, only_one_ping = True):
            mess.add_data({'error' : "Component '%s' is running. Please stop it before trying to disable" % name})
        else:
            subp = Popen("dmgdisplug %s" % name, shell=True)
            subp.communicate()
            if self.package_mode == True:
                self._pkg_list_installed()
            time.sleep(1) # make sure rest receive the updated list before the ack of disable
        self.myxpl.send(mess)          

    def _send_broadcast_hbeat(self):
        """ This method will send a ping request to everybody
        """
        self.log.debug("Send hbeat.request")
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_target("*")
        mess.set_schema('hbeat.request')
        mess.add_data({'command' : 'request'})
        self.myxpl.send(mess)

    def _package_cb(self, message):
        """ Internal callback for receiving packages related messages
        @param message : xpl message received
        """
        self.log.debug("Call _packagge_cb")

        command = message.data['command']
        print("Package action : %s" % command)
        try:
            host = message.data['host']
        except KeyError:
            host = "*"

        # check if message is for us
        if self.get_sanitized_hostname() != host and host != "*":
            return

        if command == "installed-packages-list":
            self._pkg_list_installed()

        if command == "get-dependencies" and host != "*":
            self._pkg_get_dependencies(message)

        if command == "check-dependencies" and host != "*":
            self._pkg_check_dependencies(message)

        if command == "get-udev-rules" and host != "*":
            self._pkg_get_udev_rules(message)

        if command == "install" and host != "*":
            self._pkg_install(message)

        if command == "uninstall" and host != "*":
            self._pkg_uninstall(message)


    def _pkg_list_installed(self):
        """ List packages installed on host
            This function use a semaphore to be used only by 1 command at a time
        """
        self.sema_installed.acquire()
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'installed-packages-list'})
        mess.add_data({'host' : self.get_sanitized_hostname()})
        cfg_plugin_list = dict(self.loader_plugins.load()[1])
        idx = 0
        for package in self.pkg_mgr.get_installed_packages_list():
            # I guess all plugins are naturally activated except for plugins
            if package['type'] == "plugin":
                if cfg_plugin_list.has_key(package['id']) and cfg_plugin_list[package['id']] == "enabled":
                    enabled = "yes"
                else:
                    enabled = "no"
            else:
                enabled = "yes"
            # Add data to xpl
            mess.add_data({'id%s' % idx : package['id'],
                           'fullname%s' % idx : package['fullname'],
                           'version%s' % idx : package['version'],
                           'type%s' % idx : package['type'],
                           #'source%s' % idx : package['archive_url'],
                           'enabled%s' % idx : enabled})
            idx += 1
        self.myxpl.send(mess)
        time.sleep(0.3) # make sure to make a pause between 2 messages
        self.sema_installed.release()

    def _pkg_get_dependencies(self, message):
        """ Return the list of dependencies for a package
            @param message : xpl message received
        """
        pkg_id = message.data["id"]
        pkg_type = message.data["type"]
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'get-dependencies'})
        mess.add_data({'id' : pkg_id})
        mess.add_data({'type' : pkg_type})
        mess.add_data({'host' : self.get_sanitized_hostname()})

        pkg_json = PackageJson(pkg_id, pkg_type = pkg_type).json
        idx = 0
        for dep in pkg_json["identity"]["dependencies"]:
            mess.add_data({"dep%s-id" % idx : dep["id"]})
            mess.add_data({"dep%s-type" % idx : dep["type"]})
            idx += 1
        self.myxpl.send(mess)

    def _pkg_get_udev_rules(self, message):
        """ Return the list of udev rules for a package
            @param message : xpl message received
        """
        pkg_id = message.data["id"]
        pkg_type = message.data["type"]
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'get-udev-rules'})
        mess.add_data({'id' : pkg_id})
        mess.add_data({'type' : pkg_type})
        mess.add_data({'host' : self.get_sanitized_hostname()})

        try:
            pkg_json = PackageJson(pkg_id, pkg_type = pkg_type).json
        except PackageException:
            # bad json or no such plugin installed
            self.myxpl.send(mess)
            return

        idx = 0
        for rule in pkg_json["udev-rules"]:
            mess.add_data({"rule%s-model" % idx : rule["model"]})
            mess.add_data({"rule%s-desc" % idx : rule["description"]})
            mess.add_data({"rule%s-filename" % idx : rule["filename"]})
            mess.add_data({"rule%s-rule" % idx : rule["rule"]})
            idx += 1
        self.myxpl.send(mess)


    def _pkg_check_dependencies(self, message):
        """ Check if python dependencies for a package are installed
            @param message : xpl message received
        """
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'check-dependencies'})
        mess.add_data({'host' : self.get_sanitized_hostname()})

        idx = 0
        while message.data.has_key("dep%s" % idx):
            dep = message.data["dep%s" % idx]
            mess.add_data({"dep%s" % idx : dep})
            if PATTERN_DISTUTILS_VERSION.findall(dep) == []:
                msg = "Wrong version format for '%s' : should be 'foo (...)'" % dep
                self.log.warning(msg)
                mess.add_data({'error' : msg})
                self.myxpl.send(mess)
                return
            try:
                ver = VersionPredicate(dep)
            except IrrationalVersionError:
                msg = "Irrational version for dependency '%s'" % dep
                self.log.warning(msg)
                mess.add_data({'error' : msg})
                self.myxpl.send(mess)
                return

            is_installed, installed_version = self._pkg_is_dep_installed(ver)
            if is_installed:
                installed = "yes"
                mess.add_data({"dep%s-version" % idx : installed_version})
            else:
                installed = "no"
                if installed_version != None:
                    mess.add_data({"dep%s-version" % idx : installed_version})
                crawler = Crawler()
                found = False
                try:
                    for rel in crawler.get_releases(dep):
                        if  ver.match(rel._version):
                            found = True
                            mess.add_data({"dep%s-candidate" % idx : rel._version})
                            mess.add_data({"dep%s-cmd-line" % idx : "sudo pip install %s==%s" % (ver.name, rel._version)})
                            break
                except:
                    self.log.error("Error while looking for candidates : %s" % traceback.format_exc())

                if found == False:
                    msg = "No candidate to dependency '%s' installation found" % ver.name
                    self.log.warning(msg)
                    mess.add_data({"dep%s-error" % idx : msg})

            mess.add_data({"dep%s-installed" % idx : installed})
            idx += 1
        self.myxpl.send(mess)

    def _pkg_is_dep_installed(self, version):
        """ Check if dependency is installed
            @param dep : dependency as VersionPredicate. Example : pyserial >= 2.4
        """
        subp = Popen("pip freeze | grep -i %s" % version.name, stdout=PIPE, shell=True)
        res = subp.stdout.read()
        subp.communicate()
        if res == "":
            return False, None
        tab = res.rstrip().split("==")
        if version.match(tab[1]):
            return True, tab[1]
        else:
            return False, tab[1]
        return True, None
        

    def _pkg_install(self, message):
        """ Install a package
            @param message : xpl message received
        """
        try:
            source = message.data['source']
            pkg_type = message.data['type']
            pkg_id = message.data['id']
            version = message.data['version']
            package_part = message.data['part']
        except KeyError:
            self.log.error("Missing part of xPL message for installing a package : %s" % traceback.format_exc())
            return

        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'install'})
        mess.add_data({'host' : self.get_sanitized_hostname()})
        mess.add_data({'source' : source})
        mess.add_data({'type' : pkg_type})
        mess.add_data({'id' : pkg_id})
        mess.add_data({'version' : version})

        if source == "cache":
            package = "cache:%s/%s/%s" % (pkg_type, pkg_id, version)
        else:
            mess.add_data({'error' : "source '%s' not allowed" % source})
            self.myxpl.send(mess)
            return

        # check if plugin (for a plugin) is running
        if pkg_type == "plugin":
            if self._check_component_is_running(pkg_id, only_one_ping = True):
                mess.add_data({'error' : "Plugin '%s' is running. Stop it before installing plugin." % pkg_id})
                self.myxpl.send(mess)
                return

        # check if it is a external if current manager handle external
        if pkg_type == "external" and self.options.check_external == False:
            mess.add_data({'error' : "This host doesn't handle external member packages. Please install it on main host"})
            self.myxpl.send(mess)
            return

        try:
            status = self.pkg_mgr.install_package(package, package_part = package_part)
            if status != True:
                mess.add_data({'error' : status})

            # for an external member, reload all json files
            if pkg_type == "external":
                self._clean_unknow_from_external_list()
                self._list_external_models()
        except:
            mess.add_data({'error' : 'Error while installing package. Check log file : packagemanager.log and manager.log'})
            self.log.error("Error while installing package '%s' : %s" % (package, traceback.format_exc()))
        if package_part == PKG_PART_XPL:
            self._pkg_list_installed()
            time.sleep(1) # make sure rest receive the updated list before the ack of install
        self.myxpl.send(mess)          


    def _pkg_uninstall(self, message):
        """ Uninstall a package
            @param message : xpl message received
        """
        try:
            pkg_type = message.data['type']
            pkg_id = message.data['id']
        except KeyError:
            self.log.error("Missing part of xPL message for installing a package : %s" % traceback.format_exc())
            return

        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'uninstall'})
        mess.add_data({'host' : self.get_sanitized_hostname()})
        mess.add_data({'type' : pkg_type})
        mess.add_data({'id' : pkg_id})

        # check if plugin (for a plugin) is enabled
        if pkg_type == "plugin":
            cfg_plugins = self.loader_plugins.load()[1]
            plugin_list = dict(cfg_plugins)
            try:
                if plugin_list[id] == "enabled":
                    mess.add_data({'error' : "Plugin '%s' is enabled. Disable it before uninstalling plugin." % pkg_id})
                    self.myxpl.send(mess)
                    return
            except KeyError:
                # plugin disabled because not in the config file
                pass


        # check if plugin (for a plugin) is running
        if pkg_type == "plugin":
            if self._check_component_is_running(pkg_id, only_one_ping = True):
                mess.add_data({'error' : "Plugin '%s' is running. Stop it before uninstalling plugin." % pkg_id})
                self.myxpl.send(mess)
                return

        # check if it is a external if current manager handle external
        if pkg_type == "external" and self.options.check_external == False:
            mess.add_data({'error' : "This host doesn't handle external member packages. Please install it on main host"})
            self.myxpl.send(mess)
            return

        try:
            status = self.pkg_mgr.uninstall_package(pkg_type, pkg_id)
            if status != True:
                mess.add_data({'error' : status})
            # if this is a plugin, disable it (this is a security as a plugin shouldn't be enabled when installing it)
            if pkg_type == "plugin":
                self._disable_plugin(pkg_id)
            # for an external member, reload all json files
            if pkg_type == "external":
                self._list_external_models()
                self._clean_external_list(pkg_id)
        except:
            mess.add_data({'error' : 'Error while uninstalling package. Check log file : packagemanager.log and manager.log'})
            self.log.error("Error while uninstalling package '%s-%s' : %s" % (pkg_type, pkg_id, traceback.format_exc()))

        # send updated list of installed packages
        self._pkg_list_installed()
        time.sleep(1) # make sure rest receive the updated list before the ack of install

        self.myxpl.send(mess)          




def main():
    ''' Called by the easyinstall mapping script
    '''
    SysManager()

if __name__ == "__main__":
    main()

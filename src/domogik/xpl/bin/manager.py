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
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import pyinotify
import os
import sys
import time
import stat
from threading import Event, currentThread, Thread, enumerate, Lock
from optparse import OptionParser
import traceback
from subprocess import Popen, PIPE

from domogik.common.configloader import Loader
from domogik.xpl.common.xplconnector import Listener 
from domogik.xpl.common.xplconnector import READ_NETWORK_TIMEOUT
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.common.packagemanager import PackageManager, PKG_PART_XPL, PKG_PART_RINOR
from domogik.common.packagexml import PackageXml, PackageException
from domogik.xpl.common.xplconnector import XplTimer 
from xml.dom import minidom
from ConfigParser import NoSectionError
from distutils2.version import VersionPredicate, _split_predicate, IrrationalVersionError
from distutils2.install import get_infos
from distutils2.index.simple import Crawler
import re


import domogik.xpl.bin
import pkgutil


KILL_TIMEOUT = 2
PING_DURATION = 3
WAIT_TIME_BETWEEN_PING = 15


PATTERN_DISTUTILS_VERSION = re.compile(".*\(.*\).*")


class EventHandler(pyinotify.ProcessEvent):
    """ Check a file for any event (creation, modification, etc)
    """
    
    def set_callback(self, callback):
        """ set callback to launch external stuff
        @param callback : callback function
        """
        self.my_callback = callback

    def set_config_files(self, config_files):
        """ set the list of config files
        @param list of the monitored config files
        """
        self._cfg_files = config_files 

    def process_default(self, event):
        """ A file is modified
        """
        if event.pathname in self._cfg_files or event.pathname[-4:] == ".xml":
            print("File modified : %s" % event.pathname)
            self.my_callback()

class SysManager(XplPlugin):
    """ System management from domogik
    """

    def __init__(self):
        """ Init manager and start listeners
        """

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
        parser.add_option("-H", 
                          action="store_true", 
                          dest="check_hardware", 
                          default=False, \
                          help="This manager is the one who looks for harware.")
        parser.add_option("-t", 
                          action="store", 
                          type="int",
                          dest="custom_ping_duration", 
                          help="Time for ping duration (default : %s)" % PING_DURATION)
        XplPlugin.__init__(self, name = 'manager', parser=parser)

        # Logger init
        self.log.info("Host : %s" % self.get_sanitized_hostname())

        # Fifo to communicate with the init script
        self._state_fifo = None
        if os.path.exists("/tmp/dmg-manager-state"):
            mode = os.stat("/tmp/dmg-manager-state").st_mode
            if mode & stat.S_IFIFO == stat.S_IFIFO:
                self._state_fifo = open("/tmp/dmg-manager-state","w")    
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
            sys.path.append(self._package_path)
            self._xml_plugin_directory = os.path.join(self._package_path, "plugins/softwares/")
            self._xml_hardware_directory = os.path.join(self._package_path, "plugins/hardwares/")
        else:
            self.log.info("No package path defined in config file")
            self._package_path = None
            self._xml_plugin_directory = os.path.join(conf['custom_prefix'], "share/domogik/plugins/")
            self._xml_hardware_directory = os.path.join(conf['custom_prefix'], "share/domogik/hardwares/")

        self._pinglist = {}
        self._plugins = []
        self._hardwares = []
        self._hardware_models = []

        if self.options.custom_ping_duration != None:
            self.ping_duration = self.options.custom_ping_duration
        else:
            self.ping_duration = PING_DURATION
        print "ping duration=%s" % self.ping_duration
        try:
            # Get components:
            self._list_plugins()
            if self.options.check_hardware == True:
                self._list_hardware_models()
 
            #Start dbmgr
            if self.options.start_dbmgr:
                self._inc_startup_lock()
                if self._check_component_is_running("dbmgr", True):
                    self.log.warning("Manager started with -d, but a database manager is already running")
                    self._write_fifo("WARN", "Manager started with -d, but a database manager is already running\n")
                    self._dec_startup_lock()
                else:
                    thr_dbmgr = Thread(None,
                                       self._start_plugin,
                                       "start_plugin_dbmgr",
                                       ("dbmgr",
                                        self.get_sanitized_hostname()),
                                       {"ping" : False, "startup" : True})
                    self.register_thread(thr_dbmgr)
                    thr_dbmgr.start()
    
            #Start rest
            if self.options.start_rest:
                self._inc_startup_lock()
                if self._check_component_is_running("rest", True):
                    self.log.warning("Manager started with -r, but a REST manager is already running")
                    self._write_fifo("WARN", "Manager started with -r, but a REST manager is already running\n")
                    self._dec_startup_lock()
                else:
                    thr_rest = Thread(None,
                                       self._start_plugin,
                                       "start_plugin_rest",
                                       ("rest",
                                        self.get_sanitized_hostname()),
                                       {"ping" : False, "startup" : True})
                    self.register_thread(thr_rest)
                    thr_rest.start()
    
            # Start plugins at manager startup
            self.log.debug("Check non-system plugins to start at manager startup...")
            self._write_fifo("INFO", "Check non-system plugins to start at manager startup.\n")
            comp_thread = {}
            for plugin in self._plugins:
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
                                                   (name,
                                                    self.get_sanitized_hostname()),
                                                   {"startup" : True})
                    self.register_thread(comp_thread[name])
                    comp_thread[name].start()
            
            # Define listeners
            Listener(self._sys_cb, self.myxpl, {
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
    
            if self.options.check_hardware:
                Listener(self._refresh_hardware_list, self.myxpl, {
                    'schema': 'hbeat.app',
                    'xpltype': 'xpl-stat',
                })
                Listener(self._refresh_hardware_list, self.myxpl, {
                    'schema': 'hbeat.basic',
                    'xpltype': 'xpl-stat',
                })

            # define timers
            if self.options.check_hardware:
                hardware_timer = XplTimer(15, 
                                          self._check_hardware_status, 
                                          self.myxpl)
                hardware_timer.start()

            # inotify 
            wm = pyinotify.WatchManager() # Watch manager
            mask = pyinotify.IN_MODIFY | pyinotify.IN_MOVED_TO # watched events
            notify_handler = EventHandler()
            notify_handler.set_callback(self._reload_configuration_file)
            notify_handler.set_config_files(self.get_config_files())
            notifier = pyinotify.ThreadedNotifier(wm, notify_handler)
            notifier.start()
            config_files_dir = [self._xml_plugin_directory,
                                self._xml_hardware_directory]
            for fic in  self.get_config_files():
                config_files_dir.append(os.path.dirname(fic))
            for direc in set(config_files_dir):
                wdd = wm.add_watch(direc, mask, rec = True)
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

            ### make an eternal loop to ping plugins
            # the goal is to detect manually launched plugins
            if self.options.allow_ping:
                while True:
                    time.sleep(WAIT_TIME_BETWEEN_PING)
                    ping_thread = {}
                    for plugin in self._plugins:
                        name = plugin["name"]
                        ping_thread[name] = Thread(None,
                                             self._check_component_is_running,
                                             "ping_%s" % name,
                                             (name, None),
                                             {})
                        self.register(ping_thread[n])
                        ping_thread[name].start()

            self.wait()
        except:
            self.log.error("%s" % sys.exc_info()[1])
            print("%s" % sys.exc_info()[1])

    def _reload_configuration_file(self):
        """ reload all plugins and hardware list
        """
        print("Reloading plugin and hardware model lists")
        self.log.info("Reloading plugin and hardware model lists")
        self._list_plugins()
        self._list_hardware_models()  # still usefull ? TODO :check
                                      # hardwares are automatically loaded by
                                      # manager now...

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

    def _sys_cb(self, message):
        """ Internal callback for receiving system messages
        @param message : xpl message received
        """
        self.log.debug("Call _sys_cb")

        cmd = message.data['command']
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
               (cmd != "enable" and cmd != "disable") and \
               self._is_plugin(plg) == False:
                self._invalid_plugin(cmd, plg, host)
                return

        # if no error at this point, process
        if error == "":
            self.log.debug("System request %s for host %s, plugin %s. current hostname : %s" % (cmd, host, plg, self.get_sanitized_hostname()))

            # start plugin
            if cmd == "start" and host == self.get_sanitized_hostname() and plg not in ["rest", "dbmgr", "*"]:
                self._start_plugin(plg, host) 

            # stop plugin
            if cmd == "stop" and host == self.get_sanitized_hostname() and plg not in ["rest", "dbmgr", "*"]:
                self._stop_plugin(plg, host)

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
                                  # no check on host for hardware
                self._send_plugin_detail(plg)

        # if error
        else:
            self.log.error("Error detected : %s, request %s has been cancelled" % (error, cmd))

    def _invalid_plugin(self, cmd, plg, host):
        """ send an invalid plugin message
             @param cmd : command
             @param plg : plugin name
             @param host : computer on which action was tried
        """
        error = "Component %s doesn't exists on %s" % (plg, host)
        self.log.debug(error)
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'host' : host})
        mess.add_data({'command' :  cmd})
        mess.add_data({'plugin' :  plg})
        mess.add_data({'error' :  error})
        self.myxpl.send(mess)

    def _start_plugin(self, plg, host, ping = True, startup = False):
        """ Start a plugin
            @param plg : plugin name
            @param host : computer on which plugin should be started
            @param startup : set it to True if you call _start_plugin during manager start
        """
        error = ""
        self.log.debug("Ask to start %s on %s" % (plg, host))
        if startup:
            self._write_fifo("INFO", "Start %s on %s\n" % (plg, host))
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'host' : host})
        mess.add_data({'command' :  'start'})
        mess.add_data({'plugin' :  plg})
        if ping == True:
            if self._check_component_is_running(plg):
                error = "Component %s is already running on %s" % (plg, host)
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

    def _stop_plugin(self, plg, host):
        """ stop a plugin
            @param plg : plugin name
            @param host : computer on which we want to stop plugin
        """
        self.log.debug("Check plugin stops : %s on %s" % (plg, host))
        if self._check_component_is_running(plg) == False:
            error = "Component %s is not running on %s" % (plg, host)
            self.log.warning(error)
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('domogik.system')
            mess.add_data({'command' : 'stop'})
            mess.add_data({'host' : host})
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


    def _check_component_is_running(self, name, startup = False):
        """ This method will send a ping request to a component on localhost
        and wait for the answer (max 5 seconds).
        @param name : component name
        @param startup : set to True if the method is called during manager startup 
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
            mess.set_target("xpl-%s.%s" % (name, self.get_sanitized_hostname()))
        mess.set_schema('hbeat.request')
        mess.add_data({'command' : 'request'})
        my_listener = Listener(self._cb_check_component_is_running, 
                 self.myxpl, 
                 {'schema':'hbeat.app', 
                  'xpltype':'xpl-stat', 
                  'xplsource':"xpl-%s.%s" % (name, self.get_sanitized_hostname())},
                 cb_params = {'name' : name})
        max = self.ping_duration
        while max != 0:
            self.myxpl.send(mess)
            time.sleep(1)
            max = max - 1
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

    def _cb_check_component_is_running(self, message, args):
        """ Set the Event to true if an answer was received
        """
        self._pinglist[args["name"]].set()


    def _exec_plugin(self, name):
        """ Internal method
        Start the plugin
        @param name : the name of the component to start
        This method does *not* check if the component exists
        """
        self.log.info("Start the component %s" % name)
        print("Start %s" % name)
        if name == "dbmgr" or name == "rest" or self._package_path == None:
            plg_path = "domogik.xpl.bin." + name
        else:
            plg_path = "plugins.xpl.bin." + name
        __import__(plg_path)
        plugin = sys.modules[plg_path]
        self.log.debug("Component path : %s" % plugin.__file__)
        subp = Popen("/usr/bin/python %s" % plugin.__file__, shell=True)
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

    def _list_hardware_models(self):
        """ List domogik hardware models
        """
        self.log.debug("Start listing available hardware models")

        self._hardware_models = []

        # Get hardware list
        try:
            #hardwares = Loader('hardwares')
            #hardware_list = dict(hardwares.load()[1])

            # list xml files
            try:
                hardware_list = os.listdir(self._xml_hardware_directory)
            except:
                msg = "Error accessing hardware directory : %s. You should create it" % str(traceback.format_exc())
                print msg
                self.log.error(msg)
                return 

            state_thread = {}
            for hardware in hardware_list:
                hardware = hardware[0:-4]
                print(hardware)
                self.log.info("==> %s" % (hardware))
                # try open xml file
                xml_file = "%s/%s.xml" % (self._xml_hardware_directory, hardware)
                try:
                    # get data for hardware
                    plg_xml = PackageXml(path = xml_file)
   
                    # register plugin
                    self._hardware_models.append({"type" : plg_xml.type,
                                      "name" : plg_xml.name, 
                                      "description" : plg_xml.desc, 
                                      "technology" : plg_xml.techno,
                                      "release" : plg_xml.release,
                                      "documentation" : plg_xml.doc,
                                      "vendor_id" : plg_xml.vendor_id,
                                      "device_id" : plg_xml.device_id})

                except:
                    msg = "Error reading xml file : %s\n%s" % (xml_file, str(traceback.format_exc()))
                    print msg
                    self.log.error(msg)
        except NoSectionError:
            pass 

        return


    def _refresh_hardware_list(self, message):
        """ Refresh hardware list
            @param message : xpl message
        """
        self.log.debug("Refresh hardware list with : %s" % str(message))
        vendor_device = message.source.split(".")[0]
        instance = message.source.split(".")[1]
        for hardware_model in self._hardware_models:
            msg_vendor_device = "%s-%s" % (hardware_model["vendor_id"], 
                                           hardware_model["device_id"])
            if vendor_device == msg_vendor_device:
                found = False
                for hardware in self._hardwares:
                    if hardware["host"] == instance:
                        hardware["status"] = "ON"
                        hardware["last_seen"] = time.time()
                        # interval converted from minutes to seconds : *60
                        hardware["interval"] = int(message.data["interval"])*60
                        found = True
                        self.log.info("Set hardware status ON : %s on %s" % \
                                                   (hardware["name"], instance))
                        # hardware config part
                        # - hardware configuration is given in hbeat.app body
                        hardware["configuration"] = self._get_hardware_configuration(message)
                     
                if found == False:
                    # hardware config part
                    # - hardware configuration is given in hbeat.app body
                    configuration = self._get_hardware_configuration(message)
                    self._hardwares.append({"type" : hardware_model["type"],
                              "name" : hardware_model["name"], 
                              "description" : hardware_model["description"], 
                              "technology" : hardware_model["technology"],
                              "status" : "ON",
                              "host" : instance,
                              "release" : hardware_model["release"],
                              "documentation" : hardware_model["documentation"],
                              "vendor_id" : hardware_model["vendor_id"],
                              "device_id" : hardware_model["device_id"],
                              "configuration" : configuration,
                              "interval" : int(message.data["interval"]) * 60,
                              "last_seen" : time.time()})
                    self.log.info("Add hardware : %s on %s" % \
                                             (hardware_model["name"], instance))

    def _get_hardware_configuration(self, message):
        """ Get hardware configuration from hbeat message
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

    def _check_hardware_status(self):
        """ Check if hardwares are always present
        """
        # send a hbeat request
        self._send_broadcast_hbeat()

        # wait for answers
        time.sleep(1)
 
        # process
        for hardware in self._hardwares:
            # if hardware was not seen in the interval its tells, 
            # we consider it as OFF
            if time.time() - hardware["last_seen"] > hardware["interval"]:
                hardware["status"] = "OFF"
                self.log.info("Set hardware status OFF : %s on %s" % \
                                       (hardware["name"], hardware["host"]))


    def _list_plugins(self):
        """ List domogik plugins
        """
        self.log.debug("Start listing available plugins")

        self._plugins = []

        # Getplugin list
        plugins = Loader('plugins')
        plugin_list = dict(plugins.load(refresh = True)[1])
        state_thread = {}
        for plugin in plugin_list:
            print(plugin)
            self.log.info("==> %s (%s)" % (plugin, plugin_list[plugin]))
            if plugin_list[plugin] == "enabled":
                # try open xml file
                xml_file = "%s/%s.xml" % (self._xml_plugin_directory, plugin)
                try:
                    # get data for plugin
                    plg_xml = PackageXml(path = xml_file)

                    # register plugin
                    self._plugins.append({"type" : plg_xml.type,
                                      "name" : plg_xml.name, 
                                      "description" : plg_xml.desc, 
                                      "technology" : plg_xml.techno,
                                      "status" : "OFF",
                                      "host" : self.get_sanitized_hostname(), 
                                      "release" : plg_xml.release,
                                      "documentation" : plg_xml.doc,
                                      "configuration" : plg_xml.configuration})

                    # check plugin state (will update component status)
                    state_thread[plg_xml.name] = Thread(None,
                                                   self._check_component_is_running,
                                                   "ping_%s" % plg_xml.name,
                                                   (plg_xml.name, None),
                                                   {})
                    self.register_thread(state_thread[plg_xml.name])
                    state_thread[plg_xml.name].start()

                except:
                    print("Error reading xml file : %s\n%s" % (xml_file, str(traceback.format_exc())))
                    self.log.error("Error reading xml file : %s. Detail : \n%s" % (xml_file, str(traceback.format_exc())))

                # get data from xml file
        return


    def _is_plugin(self, name):
        """ Is a component a plugin or hardware?
        @param name : component name to check
        """
        for plugin in self._plugins:
            if plugin["name"] == name:
                return True
        for hardware in self._hardwares:
            if hardware["name"] == name:
                return True
        return False

    def _send_plugin_list(self):
        """ send compoennt list
        """
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
            mess.add_data({'plugin'+str(idx)+'-desc' : plugin["description"]})
            mess.add_data({'plugin'+str(idx)+'-status' : plugin["status"]})
            mess.add_data({'plugin'+str(idx)+'-host' : plugin["host"]})
            idx += 1
        # hardwares
        for hardware in self._hardwares:
            mess.add_data({'plugin'+str(idx)+'-name' : hardware["name"]})
            mess.add_data({'plugin'+str(idx)+'-type' : hardware["type"]})
            mess.add_data({'plugin'+str(idx)+'-techno' : hardware["technology"]})
            mess.add_data({'plugin'+str(idx)+'-desc' : hardware["description"]})
            mess.add_data({'plugin'+str(idx)+'-status' : hardware["status"]})
            mess.add_data({'plugin'+str(idx)+'-host' : hardware["host"]})
            idx += 1
        # mess.add_data({'host' : self.get_sanitized_hostname()})
        self.myxpl.send(mess)

    def _send_plugin_detail(self, plg):
        """ send details about a component 
            @param plg : plugin name
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
                    mess.add_data({'cfg'+str(conf["id"])+'-desc' : conf["desc"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-default' : conf["default"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-int' : conf["interface"]})
                    if conf["optionnal"] == "yes":
                        mess.add_data({'cfg'+str(conf["id"])+'-opt' : conf["optionnal"]})
                mess.add_data({'type' :  plugin["type"]})
                mess.add_data({'plugin' :  plugin["name"]})
                mess.add_data({'description' :  plugin["description"]})
                mess.add_data({'technology' :  plugin["technology"]})
                mess.add_data({'status' :  plugin["status"]})
                mess.add_data({'release' :  plugin["release"]})
                mess.add_data({'documentation' :  plugin["documentation"]})
                mess.add_data({'host' : self.get_sanitized_hostname()})
                host_in_msg = True
        for hardware in self._hardwares:
            if hardware["name"] == plg:
                for conf in hardware["configuration"]:
                    mess.add_data({'cfg'+str(conf["id"])+'-id' : conf["id"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-key' : conf["key"]})
                    mess.add_data({'cfg'+str(conf["id"])+'-value' : conf["value"]})
                mess.add_data({'type' :  hardware["type"]})
                mess.add_data({'plugin' :  hardware["name"]})
                mess.add_data({'description' :  hardware["description"]})
                mess.add_data({'technology' :  hardware["technology"]})
                mess.add_data({'status' :  hardware["status"]})
                mess.add_data({'release' :  hardware["release"]})
                mess.add_data({'documentation' :  hardware["documentation"]})
                mess.add_data({'host' : hardware["host"]})
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

        subp = Popen("dmgenplug -f %s" % name, shell=True)
        pid = subp.pid
        subp.communicate()
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

        subp = Popen("dmgdisplug %s" % name, shell=True)
        pid = subp.pid
        subp.communicate()
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

        if command == "check-dependencies" and host != "*":
            self._pkg_check_dependencies(message)

        if command == "install" and host != "*":
            self._pkg_install(message)


    def _pkg_list_installed(self):
        """ List packages installed on host
        """
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'list-packages-installed'})
        mess.add_data({'host' : self.get_sanitized_hostname()})
        idx = 0
        for package in self.pkg_mgr.get_installed_packages_list():
            mess.add_data({'name%s' % idx : package['name'],
                           'fullname%s' % idx : package['fullname'],
                           'release%s' % idx : package['release'],
                           'type%s' % idx : package['type']})
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

            is_installed, installed_release = self._pkg_is_dep_installed(ver)
            if is_installed:
                installed = "yes"
                mess.add_data({"dep%s-release" % idx : installed_release})
            else:
                installed = "no"
                if installed_release != None:
                    mess.add_data({"dep%s-release" % idx : installed_release})
                crawler = Crawler()
                found = False
                for rel in crawler.get_releases(dep):
                    if  ver.match(rel._version):
                        found = True
                        mess.add_data({"dep%s-candidate" % idx : rel._version})
                        mess.add_data({"dep%s-cmd-line" % idx : "sudo easy_install %s==%s" % (ver.name, rel._version)})
                        break
                if found == False:
                    msg = "No candidate to dependency '%s' installation found" % ver.name
                    self.log.warning(msg)
                    mess.add_data({'error' : msg})

            mess.add_data({"dep%s-installed" % idx : installed})
            idx += 1
        self.myxpl.send(mess)

    def _pkg_is_dep_installed(self, version):
        """ Check if dependency is installed
            @param dep : dependency as VersionPredicate. Example : pyserial >= 2.4
        """
        subp = Popen("pip freeze | grep %s" % version.name, stdout=PIPE, shell=True)
        pid = subp.pid
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
            package = message.data['package']
            release = message.data['release']
            package_part = message.data['part']
        except KeyError:
            mess.add_data({'error' : 'incomplete xpl message'})
            self.myxpl.send(mess)
            return

        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.package')
        mess.add_data({'command' : 'install'})
        mess.add_data({'host' : self.get_sanitized_hostname()})
        mess.add_data({'package' : package})
        mess.add_data({'release' : release})

        # check if plugin (for a plugin) is running
        tab = message.data['package'].split("-")
        print "T=%s" % tab
        if tab[0] == "plugin":
            if self._check_component_is_running(tab[1]):
                mess.add_data({'error' : "Plugin '%s' is running. Stop it before installing plugin." % tab[1]})
                self.myxpl.send(mess)
                return

        # check if it is a hardware if current manager handle hardware
        if tab[0] == "hardware" and self.options.check_hardware == False:
            mess.add_data({'error' : "This host doesn't handle hardware packages. Please install it on main host"})
            self.myxpl.send(mess)
            return

        try:
            status = self.pkg_mgr.install_package("repo:%s" % package, release, package_part)
            if status != True:
                mess.add_data({'error' : status})
        except:
            mess.add_data({'error' : 'Error while installing package. Check log file : packagemanager.log and manager.log'})
            self.log.error("Error while installing package '%s (%s)' : %s" % (package, release, traceback.format_exc()))
        self.myxpl.send(mess)          




def main():
    ''' Called by the easyinstall mapping script
    '''
    SYS = SysManager()

if __name__ == "__main__":
    main()

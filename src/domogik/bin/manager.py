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

Domogik manager
- called with init.d script to start Domogik
- launch rest, dbmgr and plugins
- manage plugins (start, check for dead plugins) and maintains a list
- give informations about plugins when requested

History
=======

Before May 2013 : domogik 0.1/0.2/0.3
  - use xpl with domogik.system to handle plugins

After May 2013 : domogik 0.4
  - complete rewrite
  - use the MQ to handle plugins

Implements
==========

class Manager

@author: Fritz <fritz.smh@gmail.com>
@        Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""




# TODO : translate as from... import
import os
import sys
import time
import stat
import traceback
import math
import tempfile
import re
import signal

from threading import Event, Thread, Lock, Semaphore
from argparse import ArgumentParser
from subprocess import Popen, PIPE

from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common import logger
from domogik.common.utils import is_already_launched, STARTED_BY_MANAGER
from domogik.xpl.common.plugin import XplPlugin, STATUS_STARTING, STATUS_ALIVE, STATUS_STOPPED, STATUS_DEAD, STATUS_UNKNOWN, STATUS_INVALID, STATUS_STOP_REQUEST, STATUS_NOT_CONFIGURED, PACKAGES_DIR, DMG_VENDOR_ID
from domogik.common.queryconfig import Query

import zmq
from domogik.mq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
#from domogik.mq.reqrep.worker import MQRep   # moved in XplPlugin
from domogik.mq.message import MQMessage
from domogik.mq.pubsub.publisher import MQPub

from domogik.xpl.common.xplconnector import XplTimer
from domogik.common.packagejson import PackageJson, PackageException

##### packages management #####
# TODO : use later : package management related
#from distutils2.version import VersionPredicate, IrrationalVersionError
#from domogik.common.packagemanager import PackageManager, PKG_PART_XPL
## the try/except it to handle http://bugs.python.org/issue14317
#try:
#    from distutils2.index.simple import Crawler
#except ImportError:  
#    from distutils2.pypi.simple import Crawler

#PATTERN_DISTUTILS_VERSION = re.compile(".*\(.*\).*")



### constants
FIFO_DIR = "/var/run/domogik/"
PYTHON = sys.executable
WAIT_AFTER_STOP_REQUEST = 15
CHECK_FOR_NEW_PACKAGES_INTERVAL = 60


class Manager(XplPlugin):
    """ Domogik manager
    """

    def __init__(self):
        """ Init the manager
            - read options
            - create needed threads
            - initiate vars
        """

        ### Logger init
        # logger init is done after the parser setup because it is setup in the XplPlugin.__init__() call

        ### Option parser
        parser = ArgumentParser()
        parser.add_argument("-d", 
                          action="store_true", 
                          dest="start_dbmgr", 
                          default=False, \
                          help="Start database manager if not already running.")
        parser.add_argument("-r", 
                          action="store_true", 
                          dest="start_rest", 
                          default=False, \
                          help="Start rest if not already running.")
        parser.add_argument("-x", 
                          action="store_true", 
                          dest="start_xpl", 
                          default=False, \
                          help="Start xpl gateway if not already running.")
        parser.add_argument("-s",
                          action="store_true",
                          dest="start_scenario",
                          default=False, \
                          help="Start scenario manager if not already running.")
        # TODO : add -E option for externals ?

        ### Call the XplPlugin init  
        XplPlugin.__init__(self, name = 'manager', parser=parser)

        ### Logger
        self.log.info(u"Manager startup")
        self.log.info(u"Host : {0}".format(self.get_sanitized_hostname()))
        self.log.info(u"Start dbmgr : {0}".format(self.options.start_dbmgr))
        self.log.info(u"Start rest : {0}".format(self.options.start_rest))
        self.log.info(u"Start xpl gateway : {0}".format(self.options.start_xpl))
        self.log.info(u"Start scenario manager : {0}".format(self.options.start_scenario))

        ### create a Fifo to communicate with the init script
        self.log.info(u"Create the fifo to communicate with the init script")
        self._state_fifo = None
        self._create_fifo()

        ### Read the configuration file
        try:
            cfg = Loader('domogik')
            config = cfg.load()
            conf = dict(config[1])

            # pid dir path
            self._pid_dir_path = conf['pid_dir_path']
       
        except:
            self.log.error(u"Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
            return

        self.log.info(u"Packages path : {0}".format(self.get_packages_directory()))

        ### MQ
        # self.zmq = zmq.Context() is aleady define in XplPlugin
        # notice that Xplugin plugins already inherits of MQRep
        # notice that MQRep.__init__(self, self.zmq, self.name) is already done in XplPlugin

        ### Create the clients list
        self._clients = Clients()
        # note that a core component or plugin are also clients but for the self._clients object is managed directly from the Plugin and CoreComponent objects
        # so, self._clients here is only the reference to the Clients object refreshed by all plugins and core components

        ### Create the packages list
        self._packages = {}

        ### Create the device types list
        self._device_types = {}

        ### Create the plugins list
        self._plugins = {}

        ### Start the dbmgr
        if self.options.start_dbmgr:
            if not self._start_core_component("dbmgr"):
                self.log.error(u"Unable to start dbmgr")

        ### Start rest
        if self.options.start_rest:
            if not self._start_core_component("rest"):
                self.log.error(u"Unable to start rest")

        ### Start xpl GW
        if self.options.start_xpl:
            if not self._start_core_component("xplgw"):
                self.log.error(u"Unable to start xpl gateway")

        ### Start scenario
        if self.options.start_scenario:
            if not self._start_core_component("scenario"):
                self.log.error(u"Unable to start scenario manager")

        ### Check for the available packages
        #self._check_available_packages()
        #self.p = self
        # TODO : use a thread instead of XplTimer to be independent of xpl libraries
        # or rename XplTimer :)
        #self.packageTimer = XplTimer(\
        #        CHECK_FOR_NEW_PACKAGES, \
        #        self._check_available_packages, \
        #        self)
        #self.packageTimer.start()
        thr_check_available_packages = Thread(None,
                                              self._check_available_packages,
                                              "check_check_available_packages",
                                              (),
                                              {})
        thr_check_available_packages.start()

        ### Component is ready
        self.ready()



    def _check_available_packages(self):
        """ Check the available packages and get informations on them
        """
        while not self._stop.isSet():
            packages_updates = False
            is_ok, pkg_list = self._list_packages()
            if not is_ok:
                self.log.error(u"Error while checking available packages. Exiting!")
                sys.exit(1)
            for pkg in pkg_list:
                self.log.debug(u"Package available : {0}".format(pkg))
                try:
                    [type, name] = pkg.split("_")
                except:
                    self.log.warning(u"Invalid package : {0} (should be named like this : <type>_<name> (plugin_ipx800, ...)".format(pkg))
                    continue
              
                ### is the package already registered ?
                pkg_id = "{0}-{1}".format(type, name)
                if pkg_id not in self._packages:
                    self.log.info(u"New package detected : type = {0} / id = {1}".format(type, name))
                    packages_updates = True
                    pkg_registered = False
                else:
                    pkg_registered = True

                ### Create a package object in order to get packages details over MQ
                pkg = Package(type, name)
                if pkg.is_valid():
                    if pkg_registered:
                        json_has_changed = (self._packages[pkg_id].get_json() != pkg.get_json())
                    else:
                        json_has_changed = False
                    if json_has_changed:
                        self.log.info(u"Package {0} : the json file has been updated".format(pkg_id))

                    # if the package is already registered...
                    # ...we check if the json has been updated. If so we need to reload data
                    # else...
                    # ...we load data
                    if not pkg_registered or json_has_changed:
                        packages_updates = True
                        self._packages[pkg_id] = pkg

                        ### type = plugin
                        if type == "plugin":
                            if self._plugins.has_key(name):
                                self.log.debug(u"The plugin '{0}' is already registered. Reloading its data".format(name))
                                self._plugins[name].reload_data()
                            else:
                                self.log.info(u"New plugin available : {0}".format(name))
                                self._plugins[name] = Plugin(name, 
                                                           self.get_sanitized_hostname(), 
                                                           self._clients, 
                                                           self.get_libraries_directory(),
                                                           self.get_packages_directory(),
                                                           self.zmq,
                                                           self.get_stop(),
                                                           self.get_sanitized_hostname())
                                # The automatic startup is handled in the Plugin class in __init__

                                ### Create a DeviceType collection in order to send them over MQ
                                # this is only done when a new package is found

                            ### Register all the device types
                            for device_type in self._packages[pkg_id].get_device_types():
                                self.log.info(u"Register device type : {0}".format(device_type))
                                # TODO : delete
                                #if self._device_types.has_key(device_type):
                                #    self.log.error(u"Duplicate device type detected : {0} for package {1}. There is already such a device_type : please fix one of the 2 packages!. Here are the informations about the other device type entry : {3}".format(device_type, pkg_id, self._device_types[device_type]))
                                self._device_types[device_type] = self._packages[pkg_id].get_json()
    
            # publish packages list if there are some updates or new packages
            if packages_updates:
                msg_data = {}
                for pkg in self._packages:
                    msg_data[pkg] = self._packages[pkg].get_json()
                self._pub.send_event('package.detail', 
                                     msg_data)

            # wait before next check
            self._stop.wait(CHECK_FOR_NEW_PACKAGES_INTERVAL)


    def _create_fifo(self):
        """ Create the fifo
        """
        if os.path.exists("{0}/dmg-manager-state".format(FIFO_DIR)):
            mode = os.stat("0}/dmg-manager-state".format(FIFO_DIR)).st_mode
            if mode & stat.S_IFIFO == stat.S_IFIFO:
                self._state_fifo = open("{0}/dmg-manager-state".format(FIFO_DIR),"w")    
                self._startup_count = 0
                self._startup_count_lock = Lock()
                self._write_fifo("NONE","\n")


    def _start_core_component(self, name):
        """ Start a core component
            @param name : component name : dbmgr, rest
        """
        self._inc_startup_lock()
        component = CoreComponent(name, self.get_sanitized_hostname(), self._clients, self.zmq)
        self._write_fifo("INFO", "Start {0}...".format(name))
        pid = component.start()
        if pid != 0:
            self._write_fifo("OK", "{0} started with pid {1}\n".format(name, pid))
            self._dec_startup_lock()
        else:
            self._write_fifo("ERROR", "{0} failed to start. Please check logs".format(name))
            return False
        return True


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
                self._state_fifo.write("{0}[{1}] {2} {3}".format(colors[level], level, message, colors["ENDC"]))
            self._state_fifo.flush()
    
    def _inc_startup_lock(self):
        """ Increment self._startup_count
        """
        if self._state_fifo == None:
            return
        self.log.info(u"lock++ acquire : {0}".format(self._startup_count))
        self._startup_count_lock.acquire()
        self._startup_count = self._startup_count + 1
        self._startup_count_lock.release()
        self.log.info(u"lock++ released: {0}".format(self._startup_count))
    
    def _dec_startup_lock(self):
        """ Decrement self._startup_count
        """
        if self._state_fifo == None:
            return
        self.log.info(u"lock-- acquire : {0}".format(self._startup_count))
        self._startup_count_lock.acquire()
        self._startup_count = self._startup_count - 1
        self._startup_count_lock.release()
        self.log.info(u"lock-- released: {0}".format(self._startup_count))


    def _list_packages(self):
        """ List the packages available in the packages directory
            @return status : True/False
                    list : a list of packages directory names
        """
        try:
            list = []
            #for root, dirs, files in os.walk(self.get_packages_directory()):
            #    for dir in dirs:
            for a_file in os.listdir(self.get_packages_directory()):
                if os.path.isdir(os.path.join(self.get_packages_directory(), a_file)):
                    list.append(a_file)
        except:
            msg = "Error accessing packages directory : {0}. You should create it".format(str(traceback.format_exc()))
            self.log.error(msg)
            return False, None
        return True, list


    def on_mdp_request(self, msg):
        """ Handle Requests over MQ 
            @param msg : MQ req message
        """
        # XplPlugin handles MQ Req/rep also
        XplPlugin.on_mdp_request(self, msg)

        ### packages details
        # retrieve the packages details
        if msg.get_action() == "package.detail.get":
            self.log.info(u"Packages details request : {0}".format(msg))
            self._mdp_reply_packages_detail()

        ### device_types
        # retrieve the device_types
        elif msg.get_action() == "device_types.get":
            self.log.info(u"Device types request : {0}".format(msg))
            self._mdp_reply_device_types(msg)

        ### clients list and details
        # retrieve the clients list
        elif msg.get_action() == "client.list.get":
            self.log.info(u"Clients list request : {0}".format(msg))
            self._mdp_reply_clients_list()

        # retrieve the clients details
        elif msg.get_action() == "client.detail.get":
            self.log.info(u"Clients details request : {0}".format(msg))
            self._mdp_reply_clients_detail()

        # start clients
        elif msg.get_action() == "plugin.start.do":
            self.log.info(u"Plugin startup request : {0}".format(msg))
            self._mdp_reply_plugin_start(msg)

        # stop clients
        # nothing is done in the manager directly :
        # a stop request is sent to a plugin
        # the plugin publish  new status : STATUS_STOP_REQUEST
        # Then, when the manager catches this (done in class Plugin), it will check after a time if the client is stopped


    def _mdp_reply_packages_detail(self):
        """ Reply on the MQ
        """
        msg = MQMessage()
        msg.set_action('package.detail.result')
        for pkg in self._packages:
            msg.add_data(pkg, self._packages[pkg].get_json())
        self.reply(msg.get())


    def _mdp_reply_device_types(self, data):
        """ Reply on the MQ
            @param data : message data
        """
        msg = MQMessage()
        msg.set_action('device_types.result')
        if 'device_type' not in data.get_data():
            for dev in self._device_types:
                msg.add_data(dev, self._device_types[dev])
        else:
            device_type = data.get_data()['device_type']
            if self._device_types.has_key(device_type):
                msg.add_data(device_type, self._device_types[device_type])
            else:
                msg.add_data(device_type, None)
        self.reply(msg.get())


    def _mdp_reply_clients_list(self):
        """ Reply on the MQ
        """
        msg = MQMessage()
        msg.set_action('client.list.result')
        clients = self._clients.get_list() 
        for key in clients:
            msg.add_data(key, clients[key])
        self.reply(msg.get())


    def _mdp_reply_clients_detail(self):
        """ Reply on the MQ
        """
        msg = MQMessage()
        msg.set_action('client.detail.result')
        clients = self._clients.get_detail() 
        for key in clients:
            msg.add_data(key, clients[key])
        self.reply(msg.get())


    def _mdp_reply_plugin_start(self, data):
        """ Reply on the MQ
            @param data : msg REQ received
        """
        msg = MQMessage()
        msg.set_action('plugin.start.result')

        if 'name' not in data.get_data().keys():
            status = False
            reason = "Plugin startup request : missing 'name' field"
            self.log.error(reason)
        else:
            name = data.get_data()['name']
            msg.add_data('name', name)

            # try to start the plugin
            pid = self._plugins[name].start()
            if pid != 0:
                status = True
                reason = ""
            else:
                status = False
                reason = "Plugin '{0}' startup failed".format(name)

        msg.add_data('status', status)
        msg.add_data('reason', reason)
        self.reply(msg.get())





class Package():
    """ This class is used to create a package object which contains the packages information (parts of the json).
        This is needed for the package.detais MQ dialog
    """

    def __init__(self, type, name):
        """ Init a plugin 
            @param type : package type
            @param name : package name
        """
        self.type = type
        self.name = name
        self.json = None

        ### init logger
        log = logger.Logger('manager')
        self.log = log.get_logger('manager')

        self.valid = False
        self.log.debug(u"Package {0}-{1} : read the json file and validate it".format(self.type, self.name))
        try:
            pkg_json = PackageJson(pkg_type = self.type, name = self.name)
            pkg_json.validate()
            self.json = pkg_json.get_json()
            self.valid = True
            self.log.debug(u"Package {0}-{1} : the json file is valid".format(self.type, self.name))
        except PackageException as e:
            self.log.error(u"Package {0}-{1} : error while trying to read the json file".format(self.type, self.name))
            self.log.error(u"Package {0}-{1} : invalid json file".format(self.type, self.name))
            self.log.error(u"Package {0}-{1} : {2}".format(self.type, self.name, e.value))

    def is_valid(self):
        """ Return the json data (after some cleanup)
        """
        return self.valid

    def get_json(self):
        """ Return the json data (after some cleanup)
        """
        return self.json

    def get_device_types(self):
        """ Return all the device types available or the package
        """
        dt_list = []
        for dt in self.json['device_types']:
            dt_list.append(dt)
        return dt_list








class GenericComponent():
    """ This is a sample class to be used for plugins and core components
    """

    def __init__(self, name, host, clients):
        """ Init a component 
            @param name : plugin name (ipx800, onewire, ...)
            @param host : hostname
            @param clients : clients list 
        """
        ### init vars
        self.name = name
        self.host = host
        self.xpl_source = "{0}-{1}.{2}".format(DMG_VENDOR_ID, self.name, self.host)
        self.client_id = "{0}-{1}.{2}".format("plugin", self.name, self.host)
        self.type = "unknown - not setted yet"
        self.configured = None
        self._clients = clients
        self.data = {}

        ### init logger
        log = logger.Logger('manager')
        self.log = log.get_logger('manager')


    def register_component(self):
        """ register the component as a client
        """
        self._clients.add(self.host, self.type, self.name, self.client_id, self.xpl_source, self.data, self.configured)


    def set_status(self, new_status):
        """ set the status of the component
            @param status : new status
        """
        self._clients.set_status(self.client_id, new_status)


    def set_pid(self, pid):
        """ set the pid of the component (for those with a pid)
            @param status : new status
        """
        self._clients.set_pid(self.client_id, pid)






class CoreComponent(GenericComponent, MQAsyncSub):
    """ This helps to handle core components startup
        Notice that there is currently no need to stop a core component, we just want to be able to start them
    """

    def __init__(self, name, host, clients, zmq_context):
        """ Init a component
            @param name : component name (dbmgr, rest)
            @param host : hostname
            @param clients : clients list 
            @param zmq_context : 0MQ context
        """
        GenericComponent.__init__(self, name = name, host = host, clients = clients)
        self.log.info(u"New core component : {0}".format(self.name))

        ### set the component type
        self.type = "core"

        ### component data (empty)
        self.data = {}

        ### register the component as a client
        self.register_component()

        ### zmq context
        self.zmq = zmq_context

        ### subscribe the the MQ for category = plugin and name = self.name
        MQAsyncSub.__init__(self, self.zmq, 'manager', ['plugin.status'])


    def start(self):
        """ to call to start the component
            @return : None if ko
                      the pid if ok
        """
        ### Check if the component is not already launched
        # notice that this test is not really needed as the plugin also test this in startup...
        # but the plugin does it before the MQ is initiated, so the error message won't go overt the MQ.
        # By doing it now, the error will go to the UI through the 'error' MQ messages (sended by self.log.error)
        res, pid_list = is_already_launched(self.log, self.name)
        if res:
            return 0

        ### Start the component
        self.log.info(u"Request to start core component : {0}".format(self.name))
        pid = self.exec_component("domogik.bin")
        self.set_pid(pid)
        if pid != 0:
            # Notice : we whould not need to do this as this information should be provided by the MQ plugin.status.
            # But as the IOLoop is not started when core components are launched with -r, -d or -x options, we don't
            # have the plugin.status message.
            self.set_status(STATUS_ALIVE)
       
        # no need to add a step to check if the component is started as the status is given to the user directly by the pub/sub 'plugin.status'

        return pid


    def exec_component(self, python_component_basepackage):
        """ to call to start a component
            @param python_component_basepackage : domogik.bin, packages
        """
        ### get python package path for the component
        pkg = "{0}.{1}".format(python_component_basepackage, self.name)
        self.log.debug(u"Try to import module : {0}".format(pkg))
        __import__(pkg)
        component_path = sys.modules[pkg].__file__
        
        ### Generate command
        # we add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
        cmd = "{0} && {1} {2}".format(STARTED_BY_MANAGER, PYTHON, component_path)
 
        ### Execute command
        self.log.info(u"Execute command : {0}".format(cmd))
        subp = Popen(cmd, 
                     shell=True)
        pid = subp.pid
        subp.communicate()
        return pid


    def on_message(self, msgid, content):
        """ when a message is received from the MQ 

            WARNING : for core components : 
            notice that this function is not called when the manager starts with -r, -d, -x options as the IOLoop is not yet started. This function is only used after manager startup
        """
        #self.log.debug(u"New pub message received {0}".format(msgid))
        #self.log.debug(u"{0}".format(content))
        if msgid == "plugin.status":
            if content["name"] == self.name and content["host"] == self.host:
                self.log.info(u"New status received from {0} on {1} : {2}".format(self.name, self.host, content["event"]))
                self.set_status(content["event"])
                # if the status is STATUS_STOP_REQUEST, launch a check in N seconds to check if the plugin was able to shut alone
                if content["event"] == STATUS_STOP_REQUEST:
                    self.log.info(u"The plugin '{0}' is requested to stop. In 15 seconds, we will check if it has stopped".format(self.name))
                    thr_check_if_stopped = Thread(None,
                                                  self._check_if_stopped,
                                                  "check_if_{0}_is_stopped".format(self.name),
                                                  (),
                                                  {})
                    thr_check_if_stopped.start()



class Plugin(GenericComponent, MQAsyncSub):
    """ This helps to handle plugins discovered on the host filesystem
        The MQAsyncSub helps to set the status 

        Notice that some actions can't be done if the plugin host is not the server host! :
        * check if a plugin has stopped and kill it if needed
        * start the plugin
    """

    def __init__(self, name, host, clients, libraries_directory, packages_directory, zmq_context, stop, local_host):
        """ Init a plugin 
            @param name : plugin name (ipx800, onewire, ...)
            @param host : hostname
            @param clients : clients list 
            @param libraries_directory : path for the base python module for packages : /var/lib/domogik/
            @param packages_directory : path in which are stored the packages : /var/lib/domogik/packages/
            @param zmq_context : zmq context
            @param stop : get_stop()
            @param local_host : get_sanitized_hostname()
        """
        GenericComponent.__init__(self, name = name, host = host, clients = clients)
        self.log.info(u"New plugin : {0}".format(self.name))

        ### check if the plugin is on he local host
        if self.host == local_host:
            self.local_plugin = True
        else:
            self.local_plugin = False

        ### TODO : this will be to handle later : multi host (multihost)
        # * how to find available plugins on other hosts ?
        # * how to start/stop plugins on other hosts ?
        # * ...
        if self.local_plugin == False:
            self.log.error(u"Currently, the multi host feature for plugins is not yet developped. This plugin will not be registered")
            return

        ### set the component type
        self.type = "plugin"

        ### set package path
        self._packages_directory = packages_directory
        self._libraries_directory = libraries_directory

        ### zmq context
        self.zmq = zmq_context

        ### XplPlugin
        self._stop = stop

        ### config
        # used only in the function add_configuration_values_to_data()
        # elsewhere, this function is used : self.get_config("xxxx")
        self._config = Query(self.zmq, self.log)

        ### get the plugin data (from the json file)
        status = None
        self.data = {}
        self.fill_data()

        ### check if the plugin is configured (get key 'configured' in database over queryconfig)
        configured = self._config.query(self.name, 'configured')
        if configured == '1':
            configured = True
        if configured == True:
            self.configured = True
        else:
            self.configured = False

        ### register the plugin as a client
        self.register_component()

        ### subscribe the the MQ for category = plugin and name = self.name
        MQAsyncSub.__init__(self, self.zmq, 'manager', ['plugin.status', 'plugin.configuration'])

        ### check if the plugin must be started on manager startup
        startup = self._config.query(self.name, 'auto_startup')
        if startup == '1':
            startup = True
        if startup == True:
            self.log.info(u"Plugin {0} configured to be started on manager startup. Starting...".format(name))
            pid = self.start()
            if pid:
                self.log.info(u"Plugin {0} started".format(name))
            else:
                self.log.error(u"Plugin {0} failed to start".format(name))
        else:
            self.log.info(u"Plugin {0} not configured to be started on manager startup.".format(name))


    def on_message(self, msgid, content):
        """ when a message is received from the MQ 
        """
        #self.log.debug(u"New pub message received {0}".format(msgid))
        #self.log.debug(u"{0}".format(content))
        if msgid == "plugin.status":
            if content["name"] == self.name and content["host"] == self.host:
                self.log.info(u"New status received from {0} on {1} : {2}".format(self.name, self.host, content["event"]))
                self.set_status(content["event"])
                # if the status is STATUS_STOP_REQUEST, launch a check in N seconds to check if the plugin was able to shut alone
                if content["event"] == STATUS_STOP_REQUEST:
                    self.log.info(u"The plugin '{0}' is requested to stop. In 15 seconds, we will check if it has stopped".format(self.name))
                    thr_check_if_stopped = Thread(None,
                                                  self._check_if_stopped,
                                                  "check_if_{0}_is_stopped".format(self.name),
                                                  (),
                                                  {})
                    thr_check_if_stopped.start()
        elif msgid == "plugin.configuration":
            self.add_configuration_values_to_data()
            self._clients.publish_update()


    def reload_data(self):
        """ Just reload the client data
        """
        self.data = {}
        self.fill_data()

    def fill_data(self):
        """ Fill the client data by reading the json file
        """
        try:
            self.log.info(u"Plugin {0} : read the json file".format(self.name))
            pkg_json = PackageJson(pkg_type = "plugin", name = self.name)
            #we don't need to validate the json file as it has already be done in the check_avaiable_packages function
            self.data = pkg_json.get_json()
            self.add_configuration_values_to_data()
        except PackageException as e:
            self.log.error(u"Plugin {0} : error while trying to read the json file".format(self.name))
            self.log.error(u"Plugin {0} : invalid json file".format(self.name))
            self.log.error(u"Plugin {0} : {1}".format(self.name, e.value))
            self.set_status(STATUS_INVALID)
            pass

    def add_configuration_values_to_data(self):
        """
        """
        # grab all the config elements for the plugin
        config = self._config.query(self.name)
        if config != None:
            for key in config:
                # filter on the 'configured' key
                if key != 'configured':
                    # check if the key exists in the plugin configuration
                    key_found = False
                    # search the key in the configuration json part
                    for idx in range(len(self.data['configuration'])):
                        if self.data['configuration'][idx]['key'] == key:
                            key_found = True
                            # key found : insert value in the json
                            self.data['configuration'][idx]['value'] = config[key]
                    if key_found == False:
                        self.log.warning(u"A key '{0}' is configured for plugin {1} on host {2} but there is no such key in the json file of the plugin. You may need to clean your configuration".format(key, self.name, self.host))

    def start(self):
        """ to call to start the plugin
            @return : None if ko
                      the pid if ok
        """
        ### Check if the plugin is not already launched
        # notice that this test is not really needed as the plugin also test this in startup...
        # but the plugin does it before the MQ is initiated, so the error message won't go overt the MQ.
        # By doing it now, the error will go to the UI through the 'error' MQ messages (sended by self.log.error)
        res, pid_list = is_already_launched(self.log, self.name)
        if res:
            return 0

        ### Actions for test mode
        test_mode = self._config.query(self.name, "test_mode")
        test_option = self._config.query(self.name, "test_option")
        test_args = ""
        if test_mode == True: 
            self.log.info("The plugin {0} is requested to be launched in TEST mode. Option is {1}".format(self.name, test_option))
            test_args = "-t {0}".format(test_option)

        ### Try to start the plugin
        self.log.info(u"Request to start plugin : {0} {1}".format(self.name, test_args))
        pid = self.exec_component(py_file = "{0}/plugin_{1}/bin/{2}.py {3}".format(self._packages_directory, self.name, self.name, test_args), \
                                  env_pythonpath = self._libraries_directory)
        pid = pid

        # There is no need to check if it is successfully started as the plugin will send over the MQ its status the UI will get the information in this way

        self.set_pid(pid)
        return pid


    def exec_component(self, py_file, env_pythonpath = None):
        """ to call to start a component
            @param py_file : path to the .py file
            @param env_pythonpath (optionnal): custom PYTHONPATH if needed (for packages it is needed)
        """
        ### Generate command
        # we add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
        cmd = "{0} && ".format(STARTED_BY_MANAGER)
        if env_pythonpath:
            cmd += "export PYTHONPATH={0} && ".format(env_pythonpath)
        cmd += "{0} {1}".format(PYTHON, py_file)
 
        ### Execute command
        self.log.info(u"Execute command : {0}".format(cmd))
        subp = Popen(cmd, 
                     shell=True)
        pid = subp.pid
        subp.communicate()
        return pid


    def _check_if_stopped(self):
        """ Check if the plugin is stopped. If not, kill it
        """
        self._stop.wait(WAIT_AFTER_STOP_REQUEST)
        res, pid_list = is_already_launched(self.log, self.name)
        if res:
            for the_pid in pid_list:
                self.log.info(u"Try to kill pid {0}...".format(the_pid))
                os.kill(int(the_pid), signal.SIGKILL)
                # TODO : add one more check ?
                # do a while loop over is_already.... ?
            self.log.info(u"The plugin {0} should be killed now (kill -9)".format(self.name))
        else:
            self.log.info(u"The plugin {0} has stopped itself properly.".format(self.name))



class Clients():
    """ The clients list
          client_id : for a domogik plugin : plugin-<name>.<hostname>
                      for an external member : <vendor id>-<device id>.<instance>
        { client_id = { 
                        xpl_source : vendorid-deviceid.instance
                        host : hostname or ip
                        type : plugin, ...
                        name : package name (onewire, ipx800, ...)
                        package_id : [type]+[name]
                        status : alive, stopped, dead, unknown
                        configured : True/False (plugins) or None (other types)
                        data : { 
                                 ....
                               }
                       },
          ... = {}
        }

        The data part is related to the type

        WARNING : the 'primary key' is the client_id as you may have several clients with the same {type,name}
        So, all updates will be done on a client_id
    """

    def __init__(self):
        """ prepare an empty package list 
        """
        ### init vars
        self._clients = {}
        self._clients_with_details = {}

        ### init logger
        log = logger.Logger('manager')
        self.log = log.get_logger('manager')
        self.log.info(u"Clients initialisation")
        self._pub = MQPub(zmq.Context(), 'manager')

    def add(self, host, type, name, client_id, xpl_source, data, configured = None):
        """ Add a client to the list of clients
            @param host : client hostname or ip or dns
            @param type : client type
            @param name : client name
            @param client_id : client id
            @param data : client data : only for clients details
            @param configured : True/False : for a plugin : True if the plugin is configured, else False
                                None : for type != 'plugin'
        """
        self.log.info(u"Add new client : host={0}, type={1}, name={2}, client_id={3}, data={4}".format(host, type, name, client_id, str(data)))
        client = { "host" : host,
                   "type" : type,
                   "name" : name,
                   "xpl_source" : xpl_source,
                   "package_id" : "{0}-{1}".format(type, name),
                   "pid" : 0,
                   "status" : STATUS_UNKNOWN,
                   "configured" : configured}
        client_with_details = { "host" : host,
                   "type" : type,
                   "name" : name,
                   "xpl_source" : xpl_source,
                   "package_id" : "{0}-{1}".format(type, name),
                   "pid" : 0,
                   "status" : STATUS_UNKNOWN,
                   "configured" : configured,
                   "data" : data}
        self._clients[client_id] = client
        self._clients_with_details[client_id] = client_with_details
        self.publish_update()

    def set_status(self, client_id, new_status):
        """ Set a new status to a client
        """
        self.log.debug(u"Try to set a new status : {0} => {1}".format(client_id, new_status))
        if new_status not in (STATUS_UNKNOWN, STATUS_STARTING, STATUS_ALIVE, STATUS_STOPPED, STATUS_DEAD, STATUS_INVALID, STATUS_STOP_REQUEST, STATUS_NOT_CONFIGURED):
            self.log.error(u"Invalid status : {0}".format(new_status))
            return
        old_status = self._clients[client_id]['status']
        if old_status == new_status:
            self.log.debug(u"The status was already {0} : nothing to do".format(old_status))
            return
        self._clients[client_id]['status'] = new_status
        self._clients_with_details[client_id]['status'] = new_status
        self.log.info(u"Status set : {0} => {1}".format(client_id, new_status))
        self.publish_update()

    def set_pid(self, client_id, pid):
        """ Set a pid to a client
        """
        self.log.debug(u"Try to set the pid : {0} => {1}".format(client_id, pid))
        self._clients[client_id]['pid'] = pid
        self._clients_with_details[client_id]['pid'] = pid
        self.log.info(u"Pid set : {0} => {1}".format(client_id, pid))
        self.publish_update()

    def get_list(self):
        """ Return the clients list
        """
        return self._clients

    def get_detail(self):
        """ Return the clients details
        """
        return self._clients_with_details

    def publish_update(self):
        """ Publish the clients list update over the MQ
        """
        # MQ publisher
        self._pub.send_event('client.list', 
                             self._clients)
        self._pub.send_event('client.detail', 
                             self._clients_with_details)




def main():
    ''' Called by the easyinstall mapping script
    '''
    Manager()

if __name__ == "__main__":
    main()

# this is a test.


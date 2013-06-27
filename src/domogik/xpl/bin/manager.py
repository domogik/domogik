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
from optparse import OptionParser
from subprocess import Popen, PIPE

from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common import logger
from domogik.common.utils import is_already_launched, STARTED_BY_MANAGER
from domogik.xpl.common.xplconnector import Listener 
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin, STATUS_STARTING, STATUS_ALIVE, STATUS_STOPPED, STATUS_DEAD, STATUS_UNKNOWN, STATUS_INVALID, STATUS_STOP_REQUEST, STATUS_NOT_CONFIGURED, PACKAGES_DIR, DMG_VENDOR_ID
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.xplconnector import XplTimer 
from ConfigParser import NoSectionError

import zmq
from domogik.mq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
#from domogik.mq.reqrep.worker import MQRep   # moved in XplPlugin
from domogik.mq.message import MQMessage
from domogik.mq.pubsub.publisher import MQPub


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
                          help="Start rest if not already running.")
        parser.add_option("-x", 
                          action="store_true", 
                          dest="start_xplevent", 
                          default=False, \
                          help="Start xpl events manager if not already running.")
        # TODO : add -E option for externals ?

        ### Call the XplPlugin init  
        XplPlugin.__init__(self, name = 'manager', parser=parser)

        ### Logger
        self.log.info("Manager startup")
        self.log.info("Host : {0}".format(self.get_sanitized_hostname()))
        self.log.info("Start dbmgr : {0}".format(self.options.start_dbmgr))
        self.log.info("Start rest : {0}".format(self.options.start_rest))
        self.log.info("Start xplevent : {0}".format(self.options.start_xplevent))

        ### create a Fifo to communicate with the init script
        self.log.info("Create the figo to communicate with the init script")
        self._state_fifo = None
        self._create_fifo()

        ### Read the configuration file
        try:
            cfg = Loader('domogik')
            config = cfg.load()
            conf = dict(config[1])

            # pid dir path
            self._pid_dir_path = conf['pid_dir_path']
       
            # packages module path : /var/lib/domogik
            #self._package_module_path = conf['package_path']
            # packages installation path : /var/lib/domogik/packages
            #self._package_path = "{0}/{1}".format(self._package_module_path, PACKAGES_DIR)
            #self.log.info("Package path : {0}".format(self._package_path))
        except:
            self.log.error("Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
            return

        self.log.info("Packages path : {0}".format(self.get_packages_directory()))

        ### MQ
        # self._zmq = zmq.Context() is aleady define in XplPlugin
        # notice that Xplugin plugins already inherits of MQRep
        # notice that MQRep.__init__(self, self._zmq, self.name) is already done in XplPlugin

        ### Create the clients list
        self._clients = Clients()
        # note that a core component or plugin are also clients but for the self._clients object is managed directly from the Plugin and CoreComponent objects
        # so, self._clients here is only the reference to the Clients object refreshed by all plugins and core components

        ### Create the plugins list
        self._plugins = {}
        # { 'onewire' : Plugin('onewire'),
        #   'ipx800' : Plugin('ipx800'),
        #   ...
        # }

        ### Start the dbmgr
        if self.options.start_dbmgr:
            if not self._start_core_component("dbmgr"):
                return

        ### Start rest
        if self.options.start_rest:
            if not self._start_core_component("rest"):
                return

        ### Start xplevent
        if self.options.start_xplevent:
            if not self._start_core_component("xplevent"):
                return

        ### Check for the available packages
        # TODO : call it with a timer !
        # each <a new parameter to define> seconds
        # wait for 1 minute or more between each check
        # in 'install' mode, when a new package will be installed, a signal will be sent over MQ, so we will be able to call this function when needed
        self._check_available_packages()

        ### Start the MQ 
        # Already done in XplPlugin
        #IOLoop.instance().start() 

        ### Component is ready
        self.ready()



    def _check_available_packages(self):
        """ Check the available packages and get informations on them
        """
        is_ok, pkg_list = self._list_packages()
        if not is_ok:
            self.log.error("Error while checking available packages. Exiting!")
            sys.exit(1)
        for pkg in pkg_list:
            self.log.debug("Package available : {0}".format(pkg))
            [type, id] = pkg.split("_")
            self.log.debug("Type : {0}     / Id : {1}".format(type, id))
          
            ### type = plugin
            if type == "plugin":
                if self._plugins.has_key(id):
                    self.log.debug("The plugin '{0}' is already registered.".format(id))
                else:
                    self.log.info("New plugin available : {0}".format(id))
                    self._plugins[id] = Plugin(id, 
                                               self.get_sanitized_hostname(), 
                                               self._clients, 
                                               self.get_libraries_directory(),
                                               self.get_packages_directory(),
                                               self._zmq,
                                               self.get_stop,
                                               self.get_sanitized_hostname())
                    # The automatic startup is handled in the Plugin class in __init__
            


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


    def _start_core_component(self, id):
        """ Start a core component
            @param id : component id : dbmgr, rest
        """
        self._inc_startup_lock()
        component = CoreComponent(id, self.get_sanitized_hostname(), self._clients)
        self._write_fifo("INFO", "Start {0}...".format(id))
        pid = component.start()
        if pid != 0:
            self._write_fifo("OK", "{0} started with pid {1}\n".format(id, pid))
            self._dec_startup_lock()
        else:
            self._write_fifo("ERROR", "{0} failed to start. Please check logs".format(id))
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
        self.log.info("lock++ acquire : {0}".format(self._startup_count))
        self._startup_count_lock.acquire()
        self._startup_count = self._startup_count + 1
        self._startup_count_lock.release()
        self.log.info("lock++ released: {0}".format(self._startup_count))
    
    def _dec_startup_lock(self):
        """ Decrement self._startup_count
        """
        if self._state_fifo == None:
            return
        self.log.info("lock-- acquire : {0}".format(self._startup_count))
        self._startup_count_lock.acquire()
        self._startup_count = self._startup_count - 1
        self._startup_count_lock.release()
        self.log.info("lock-- released: {0}".format(self._startup_count))


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

        ### clients list and details
        # retrieve the clients list
        if msg.get_action() == "clients.list.get":
            self.log.info("Clients list request : {0}".format(msg))
            self._mdp_reply_clients_list()

        # retrieve the clients details
        elif msg.get_action() == "clients.detail.get":
            self.log.info("Clients details request : {0}".format(msg))
            self._mdp_reply_clients_detail()

        # start clients
        elif msg.get_action() == "plugin.start.do":
            self.log.info("Plugin startup request : {0}".format(msg))
            self._mdp_reply_plugin_start(msg)

        # stop clients
        # nothing is done in the manager directly :
        # a stop request is sent to a plugin
        # the plugin publish  new status : STATUS_STOP_REQUEST
        # Then, when the manager catches this (done in class Plugin), it will check after a time if the client is stopped


    def _mdp_reply_clients_list(self):
        """ Reply on the MQ
        """
        msg = MQMessage()
        msg.set_action('clients.list.result')
        msg.add_data('clients', self._clients.get_list())
        self.reply(msg.get())


    def _mdp_reply_clients_detail(self):
        """ Reply on the MQ
        """
        msg = MQMessage()
        msg.set_action('clients.detail.result')
        msg.add_data('clients', self._clients.get_detail())
        self.reply(msg.get())


    def _mdp_reply_plugin_start(self, data):
        """ Reply on the MQ
            @param data : msg REQ received
        """
        msg = MQMessage()
        msg.set_action('plugin.start.result')

        if 'id' not in data.get_data().keys():
            status = False
            reason = "Plugin startup request : missing 'id' field"
            self.log.error(reason)
        else:
            id = data.get_data('id')
            msg.add_data('id', id)

            # try to start the plugin
            pid = self._plugins[id].start()
            if pid != 0:
                status = True
                reason = ""
            else:
                status = False
                reason = "Plugin '{0}' startup failed".format(id)

        msg.add_data('status', status)
        msg.add_data('reason', reason)
        self.reply(msg.get())











class GenericComponent():
    """ This is a sample class to be used for plugins and core components
    """

    def __init__(self, id, host, clients):
        """ Init a component 
            @param id : plugin id (ipx800, onewire, ...)
            @param host : hostname
            @param clients : clients list 
        """
        ### init vars
        self.id = id
        self.host = host
        self.xpl_source = "{0}-{1}.{2}".format(DMG_VENDOR_ID, self.id, self.host)
        self.type = "unknown - not setted yet"
        self.configured = None
        self._clients = clients

        ### init logger
        log = logger.Logger('manager')
        self.log = log.get_logger('manager')


    def register_component(self):
        """ register the component as a client
        """
        self._clients.add(self.host, self.type, self.id, self.xpl_source, self.data, self.configured)


    def set_status(self, new_status):
        """ set the status of the component
            @param status : new status
        """
        self._clients.set_status(self.xpl_source, new_status)


    def set_pid(self, pid):
        """ set the pid of the component (for those with a pid)
            @param status : new status
        """
        self._clients.set_pid(self.xpl_source, pid)






class CoreComponent(GenericComponent):
    """ This helps to handle core components startup
        Notice that there is currently no need to stop a core component, we just want to be able to start them
    """

    def __init__(self, id, host, clients):
        """ Init a component
            @param id : component id (dbmgr, rest)
            @param host : hostname
            @param clients : clients list 
        """
        GenericComponent.__init__(self, id = id, host = host, clients = clients)
        self.log.info("New core component : {0}".format(self.id))

        ### set the component type
        self.type = "core"

        ### component data (empty)
        self.data = {}

        ### register the component as a client
        self.register_component()


    def start(self):
        """ to call to start the component
            @return : None if ko
                      the pid if ok
        """
        ### Check if the component is not already launched
        # notice that this test is not really needed as the plugin also test this in startup...
        # but the plugin does it before the MQ is initiated, so the error message won't go overt the MQ.
        # By doing it now, the error will go to the UI through the 'error' MQ messages (sended by self.log.error)
        res, pid_list = is_already_launched(self.log, self.id)
        if res:
            return 0

        ### Start the component
        self.log.info("Request to start core component : {0}".format(self.id))
        pid = self.exec_component("domogik.xpl.bin")
        self.set_pid(pid)
       
        # no need to add a step to check if the composent is started as the status is given to the user directly by the pub/sub 'plugin.status'

        return pid


    def exec_component(self, python_component_basepackage):
        """ to call to start a component
            @param python_component_basepackage : domogik.xpl.bin, packages
        """
        ### get python package path for the component
        pkg = "{0}.{1}".format(python_component_basepackage, self.id)
        self.log.debug("Try to import module : {0}".format(pkg))
        __import__(pkg)
        component_path = sys.modules[pkg].__file__
        
        ### Generate command
        # we add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
        cmd = "{0} && {1} {2}".format(STARTED_BY_MANAGER, PYTHON, component_path)
 
        ### Execute command
        self.log.info("Execute command : {0}".format(cmd))
        subp = Popen(cmd, 
                     shell=True)
        pid = subp.pid
        subp.communicate()
        return pid




class Plugin(GenericComponent, MQAsyncSub):
    """ This helps to handle plugins discovered on the host filesystem
        The MQAsyncSub helps to set the status 

        Notice that some actions can't be done if the plugin host is not the server host! :
        * check if a plugin has stopped and kill it if needed
        * start the plugin
    """

    def __init__(self, id, host, clients, libraries_directory, packages_directory, zmq_context, stop, local_host):
        """ Init a plugin 
            @param id : plugin id (ipx800, onewire, ...)
            @param host : hostname
            @param clients : clients list 
            @param libraries_directory : path for the base python module for packages : /var/lib/domogik/
            @param packages_directory : path in which are stored the packages : /var/lib/domogik/packages/
            @param zmq_context : zmq context
            @param stop : get_stop()
            @param local_host : get_sanitized_hostname()
        """
        GenericComponent.__init__(self, id = id, host = host, clients = clients)
        self.log.info("New plugin : {0}".format(self.id))

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
            self.log.error("Currently, the multi host feature for plugins is not yet developped. This plugin will not be registered")
            return

        ### set the component type
        self.type = "plugin"

        ### set package path
        self._packages_directory = packages_directory
        self._libraries_directory = libraries_directory

        ### zmq context
        self._zmq = zmq_context

        ### XplPlugin
        self._stop = stop

        ### config
        self._config = Query(self._zmq, self.log)

        ### get the plugin data (from the json file)
        status = None
        self.data = {}
        self.fill_data()

        ### check if the plugin is configured (get key 'configured' in database over queryconfig)
        configured = self._config.query(self.id, 'configured')
        if configured == '1':
            configured = True
        if configured == True:
            self.configured = True
        else:
            self.configured = False

        ### register the plugin as a client
        self.register_component()

        ### subscribe the the MQ for category = plugin and id = self.id
        MQAsyncSub.__init__(self, self._zmq, 'manager', ['plugin.status', 'plugin.configuration'])

        ### check if the plugin must be started on manager startup
        startup = self._config.query(self.id, 'startup')
        if startup == '1':
            startup = True
        if startup == True:
            self.log.info("Plugin {0} configured to be started on manager startup. Starting...".format(id))
            pid = self.start()
            if pid:
                self.log.info("Plugin {0} started".format(id))
            else:
                self.log.error("Plugin {0} failed to start".format(id))
        else:
            self.log.info("Plugin {0} not configured to be started on manager startup.".format(id))


    def on_message(self, msgid, content):
        """ when a message is received from the MQ 
        """
        self.log.debug("New pub message {0}".format(msgid))
        self.log.debug("{0}".format(content))
        if msgid == "plugin.status":
            if content["id"] == self.id and content["host"] == self.host:
                self.log.info("New status received from {0} on {1} : {2}".format(self.id, self.host, content["event"]))
                self.set_status(content["event"])
                # if the status is STATUS_STOP_REQUEST, launch a check in N seconds to check if the plugin was able to shut alone
                if content["event"] == STATUS_STOP_REQUEST:
                    self.log.info("The plugin '{0}' is requested to stop. In 15 seconds, we will check if it has stopped".format(self.id))
                    thr_check_if_stopped = Thread(None,
                                                  self._check_if_stopped,
                                                  "check_if_{0}_is_stopped".format(self.id),
                                                  (),
                                                  {})
                    thr_check_if_stopped.start()
        elif msgid == "plugin.configuration":
             self.add_configuration_values_to_data()


    def fill_data(self):
        """ Fill the client data by reading the json file
        """
        try:
            self.log.info("Plugin {0} : read the json file and validate id".format(self.id))
            pkg_json = PackageJson(pkg_type = "plugin", id = self.id)
            # check if json is valid
            if pkg_json.validate() == False:
                self.set_status(STATUS_INVALID)
                # TODO : how to get the reason ?
                self.log.error("Plugin {0} : invalid json file".format(self.id))
            else:
                self.data = pkg_json.get_json()
                # and finally, add the configuration values in the data
                self.add_configuration_values_to_data()
        except:
            self.log.error("Plugin {0} : error while trying to read the json file : {1}".format(self.id, traceback.format_exc()))
            self.set_status(STATUS_INVALID)

    def add_configuration_values_to_data(self):
        """
        """
        # grab all the config elements for the plugin
        config = self._config.query(self.id)
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
                    self.log.warning("A key '{0}' is configured for plugin {1} on host {2} but there is no such key in the json file of the plugin. You may need to clean your configuration".format(key, self.id, self.host))

    def start(self):
        """ to call to start the plugin
            @return : None if ko
                      the pid if ok
        """
        ### Check if the plugin is not already launched
        # notice that this test is not really needed as the plugin also test this in startup...
        # but the plugin does it before the MQ is initiated, so the error message won't go overt the MQ.
        # By doing it now, the error will go to the UI through the 'error' MQ messages (sended by self.log.error)
        res, pid_list = is_already_launched(self.log, self.id)
        if res:
            return 0

        ### Try to start the plugin
        self.log.info("Request to start plugin : {0}".format(self.id))
        pid = self.exec_component(py_file = "{0}/plugin_{1}/bin/{2}.py".format(self._packages_directory, self.id, self.id), \
                                  env_pythonpath = self._librairies_directory)
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
        self.log.info("Execute command : {0}".format(cmd))
        subp = Popen(cmd, 
                     shell=True)
        pid = subp.pid
        subp.communicate()
        return pid


    def _check_if_stopped(self):
        """ Check if the plugin is stopped. If not, kill it
        """
        self._stop.wait(WAIT_AFTER_STOP_REQUEST)
        res, pid_list = is_already_launched(self.log, self.id)
        if res:
            for the_pid in pid_list:
                self.log.info("Try to kill pid {0}...".format(the_pid))
                os.kill(int(the_pid), signal.SIGKILL)
                # TODO : add one more check ?
                # do a while loop over is_already.... ?
            self.log.info("The plugin {0} should be killed now (kill -9)".format(self.id))
        else:
            self.log.info("The plugin {0} has stopped itself properly.".format(self.id))



class Clients():
    """ The clients list
          xpl_source : for a domogik plugin : domogik-<id>.<hostname>
                       for an external member : <vendor id>-<device id>.<instance>
        { xplsource = { 
                        host : hostname or ip
                        type : plugin, ...
                        id : package name (onewire, ipx800, ...)
                        status : alive, stopped, dead, unknown
                        configured : True/False (plugins) or None (other types)
                        data : { 
                                 ....
                               }
                       },
          ... = {}
        }

        The data part is related to the type

        WARNING : the 'primary key' is the xpl_source as you may have several clients with the same {type,id}
        So, all updates will be done on a xpl_source
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
        self.log.info("Clients initialisation")
        self._pub = MQPub(zmq.Context(), 'manager')

    def add(self, host, type, id, xpl_source, data, configured = None):
        """ Add a client to the list of clients
            @param host : client hostname or ip or dns
            @param type : client type
            @param id : client id
            @param xpl_source : client xpl source
            @param data : client data : only for clients details
            @param configured : True/False : for a plugin : True if the plugin is configured, else False
                                None : for type != 'plugin'
        """
        self.log.info("Add new client : host={0}, type={1}, id={2}, xpl_source={3}, data={4}".format(host, type, id, xpl_source, str(data)))
        client = { "host" : host,
                   "type" : type,
                   "id" : id,
                   "pid" : 0,
                   "status" : STATUS_UNKNOWN,
                   "configured" : configured}
        client_with_details = { "host" : host,
                   "type" : type,
                   "id" : id,
                   "pid" : 0,
                   "status" : STATUS_UNKNOWN,
                   "configured" : configured,
                   "data" : data}
        self._clients[xpl_source] = client
        self._clients_with_details[xpl_source] = client_with_details
        self._publish_update()

    def set_status(self, xpl_source, new_status):
        """ Set a new status to a client
        """
        self.log.debug("Try to set a new status : {0} => {1}".format(xpl_source, new_status))
        if new_status not in (STATUS_UNKNOWN, STATUS_STARTING, STATUS_ALIVE, STATUS_STOPPED, STATUS_DEAD, STATUS_INVALID, STATUS_STOP_REQUEST, STATUS_NOT_CONFIGURED):
            self.log.error("Invalid status : {0}".format(new_status))
            return
        old_status = self._clients[xpl_source]['status']
        if old_status == new_status:
            self.log.debug("The status was already {0} : nothing to do".format(old_status))
            return
        self._clients[xpl_source]['status'] = new_status
        self._clients_with_details[xpl_source]['status'] = new_status
        self.log.info("Status set : {0} => {1}".format(xpl_source, new_status))
        self._publish_update()

    def set_pid(self, xpl_source, pid):
        """ Set a pid to a client
        """
        self.log.debug("Try to set the pid : {0} => {1}".format(xpl_source, pid))
        self._clients[xpl_source]['pid'] = pid
        self._clients_with_details[xpl_source]['pid'] = pid
        self.log.info("Pid set : {0} => {1}".format(xpl_source, pid))
        self._publish_update()

    def get_list(self):
        """ Return the clients list
        """
        return self._clients

    def get_detail(self):
        """ Return the clients details
        """
        return self._clients_with_details

    def _publish_update(self):
        """ Publish the clients list update over the MQ
        """
        # MQ publisher
        self._pub.send_event('clients.list', 
                             self._clients)
        self._pub.send_event('clients.detail', 
                             self._clients_with_details)




def main():
    ''' Called by the easyinstall mapping script
    '''
    Manager()

if __name__ == "__main__":
    main()

# this is a test.


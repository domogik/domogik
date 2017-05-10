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
- launch core component and plugins
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
import json
import requests
import platform
import pprint
from collections import OrderedDict
from threading import Event, Thread, Lock, Semaphore
from argparse import ArgumentParser
from subprocess import Popen, PIPE

from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common import logger
from domogik.common.utils import is_already_launched, STARTED_BY_MANAGER
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.plugin import STATUS_STARTING, STATUS_ALIVE, STATUS_STOPPED, STATUS_DEAD, STATUS_UNKNOWN, STATUS_INVALID, STATUS_STOP_REQUEST, STATUS_NOT_CONFIGURED, PACKAGES_DIR, DMG_VENDOR_ID, STATUS_HBEAT
from domogik.common.queryconfig import Query
from domogik.common.baseplugin import FIFO_DIR

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
#from domogikmq.reqrep.worker import MQRep   # moved in XplPlugin
from domogikmq.message import MQMessage
from domogikmq.pubsub.publisher import MQPub

from domogik.xpl.common.xplconnector import XplTimer
from domogik.common.packagejson import PackageJson, PackageException

from domogik.xpl.common.xplconnector import Listener, STATUS_HBEAT_XPL

from multiprocessing.managers import SyncManager
from domogik.bin.cachedb import WorkerCache, CACHE_NAME


### constants

PYTHON = sys.executable
WAIT_AFTER_STOP_REQUEST = 15           # seconds
CHECK_FOR_NEW_PACKAGES_INTERVAL = 30   # seconds
SEND_METRICS_INTERVAL = 600            # seconds

class CacheDB(SyncManager):
    pass

class Manager(XplPlugin, MQAsyncSub):
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
        parser.add_argument("-a",
                          action="store_true",
                          dest="start_admin",
                          default=False, \
                          help="Start admin interface if not already running.")
        parser.add_argument("-d",
                          action="store_true",
                          dest="start_admin",
                          default=False, \
                          help="Start database manager if not already running.")
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
        parser.add_argument("-b",
                          action="store_true",
                          dest="start_butler",
                          default=False, \
                          help="Start butler if not already running.")

        ### Call the XplPlugin init
        XplPlugin.__init__(self, name = 'manager', parser=parser, log_prefix = "core_", nohub=True)

        ### Logger
        self.log.info(u"Manager startup")
        self.log.info(u"Host : {0}".format(self.get_sanitized_hostname()))
        self.log.info(u"Start xpl gateway : {0}".format(self.options.start_xpl))
        self.log.info(u"Start admin interface : {0}".format(self.options.start_admin))
        self.log.info(u"Start scenario manager : {0}".format(self.options.start_scenario))
        self.log.info(u"Start butler : {0}".format(self.options.start_butler))

        ### MQ
        MQAsyncSub.__init__(self, self.zmq, 'manager', ['metrics.processinfo', 'metrics.browser'])

        ### Read the configuration file
        try:
            cfg = Loader('domogik')
            config = cfg.load()
            conf = dict(config[1])

            # pid dir path
            self._pid_dir_path = conf['pid_dir_path']

            # try to get the metrics installation id
            # this data may be deleted from the end user in the /etc/domogik.cfg file, so we assume that the values will be None
            # in case of error
            try:
                cfgm = Loader('metrics')
                configm = cfgm.load()
                confm = dict(configm[1])
                self._metrics_id = confm['id']
                self._metrics_url = confm['url']
                if self._metrics_id != '' and self._metrics_url != '':
                    self.log.info(u"The metrics informations are configured. 'id' = '{0}', 'url' = '{1}'".format(self._metrics_id, self._metrics_url))
                    self.log.info(u"The metrics informations goal is to help us to have an overview of the Domogik releases fragmentation and performances issues. To disable them, just remove the [metrics] section in the Domogik configuration file ;)")
                else:
                    self.log.warning(u"The metrics options are not configured (one or all) : [metrics] > id, [metrics] > url. This is surely an end user wish, we respect this and won't send metrics for analysis!")
                    self._metrics_id = None
                    self._metrics_url = None
            except:
                self.log.warning(u"The metrics options are not configured (one or all) : [metrics] > id, [metrics] > url. This is surely an end user wish, we respect this and won't send metrics for analysis!")
                self._metrics_id = None
                self._metrics_url = None

        except:
            self.log.error(u"Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
            return

        self.log.info(u"Packages path : {0}".format(self.get_packages_directory()))

        ### Metrics
        self.metrics_processinfo = []
        self.metrics_browser = []
        self.distribution = "{0} {1}".format(platform.linux_distribution()[0], platform.linux_distribution()[1])

        # send metrics from time to time
        if self._metrics_url != None and self._metrics_id != None:
            thr_send_metrics = Thread(None,
                                      self._send_metrics,
                                      "send_metrics",
                                      (),
                                      {})
            thr_send_metrics.start()



        ### MQ
        # self.zmq = zmq.Context() is aleady define in XplPlugin
        # notice that Xplugin plugins already inherits of MQRep
        # notice that MQRep.__init__(self, self.zmq, self.name) is already done in XplPlugin

        ### Create the clients list
        self._clients = Clients(self._stop)
        # note that a core component or plugin are also clients but for the self._clients object is managed directly from the Plugin and CoreComponent objects
        # so, self._clients here is only the reference to the Clients object refreshed by all plugins and core components

        ### Create the packages list
        self._packages = {}

        ### Create the device types list
        self._device_types = {}

        ### Create the plugins list
        self._plugins = {}

        ### Create the brain parts list
        self._brains = {}

        ### Create the interfaces list
        self._interfaces = {}

        ### Start cachedevice system
#        if self.options.start_cachedevice:
        self.log.info(u"Manager init cache")
        self._cache_pid = None
        thr__runCacheDevices = Thread(None,
                                      self._runCacheDevices,
                                      "run_cache_devices",
                                      (),
                                      {})
        thr__runCacheDevices.start()
        self.log.info(u"Manager instanciate cache")

        ### Start xpl GW
        if self.options.start_xpl:
            if not self._start_core_component("xplgw"):
                self.log.error(u"Unable to start xpl gateway")

        ### Start admin
        if self.options.start_admin:
            if not self._start_core_component("admin"):
                self.log.error(u"Unable to start admin interface")

        ### Start scenario
        if self.options.start_scenario:
            if not self._start_core_component("scenario"):
                self.log.error(u"Unable to start scenario manager")

        ### Start butler
        if self.options.start_butler:
            if not self._start_core_component("butler"):
                self.log.error(u"Unable to start butler")

        ### Check for the available packages
        thr_check_available_packages = Thread(None,
                                              self._check_available_packages,
                                              "check_check_available_packages",
                                              (),
                                              {})
        thr_check_available_packages.start()

        ### Check for xpl clients that are not part of Domogik
        # they are external clients
        # they can be related to a plugin (example : rfxcom lan model)
        # or to no plugin (example : an arduino DIY device that sends temperature and the plugin generic will catch this data)
        Listener(self._register_xpl_client, self.myxpl,
                 {'schema': 'hbeat.basic'})
        Listener(self._register_xpl_client, self.myxpl,
                 {'schema': 'hbeat.app'})


        ### Component is ready
        self.ready()

    def force_leave(self, status = False, return_code = None):
        ### Call the XplPlugin init
        XplPlugin.force_leave(self, status, return_code, exit=False)
        if self._cache_pid is not None :
            cfg = Loader('database')
            config = cfg.load()
            dbConfig = dict(config[1])
            port_c = 50001 if not 'portcache' in dbConfig else int(dbConfig['portcache'])
            CacheDB.register('force_leave')
            m = CacheDB(address=('localhost', port_c), authkey=b'{0}'.format(dbConfig['password']))
            m.connect()
            if hasattr(self, "log"):
                self.log.info(u"force_leave called. Exit to memory devices cache {0}".format(m))
            # Actually Killing all subProcess. Not really academic, but I d'ont find other way ! and raise an exception."
            try :
                m.force_leave()
            except :
                pass
        sys.exit()

    def _check_available_packages(self):
        """ Check the available packages and get informations on them
        """
        while not self._stop.isSet():
            packages_updates = False
            is_ok, pkg_list = self._list_packages()
            if not is_ok:
                self.log.error(u"Error while checking available packages. Exiting!")
                sys.exit(1)

            # first, check all the packages found and process them
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
                                self._device_types[device_type] = self._packages[pkg_id].get_json()

                        ### type = brain
                        elif type == "brain":
                            if self._brains.has_key(name):
                                self.log.debug(u"The brain '{0}' is already registered. Reloading its data".format(name))
                                self._brains[name].reload_data()
                            else:
                                self.log.info(u"New brain available : {0}".format(name))
                                self._brains[name] = Brain(name,
                                                           self.get_sanitized_hostname(),
                                                           self._clients,
                                                           self.get_libraries_directory(),
                                                           self.get_packages_directory(),
                                                           self.zmq,
                                                           self.get_stop(),
                                                           self.get_sanitized_hostname())

                        ### type = interface
                        elif type == "interface":
                            if self._interfaces.has_key(name):
                                self.log.debug(u"The interface '{0}' is already registered. Reloading its data".format(name))
                                self._interfaces[name].reload_data()
                            else:
                                self.log.info(u"New interface available : {0}".format(name))
                                self._interfaces[name] = Interface(name,
                                                           self.get_sanitized_hostname(),
                                                           self._clients,
                                                           self.get_libraries_directory(),
                                                           self.get_packages_directory(),
                                                           self.zmq,
                                                           self.get_stop(),
                                                           self.get_sanitized_hostname())
                                # The automatic startup is handled in the Interface class in __init__


            # finally, check if some packages has been uninstalled/removed
            pkg_to_unregister = []
            for pkg in self._packages:
                # we build an id in the same format as the folders in the /var/lib/domogik/domogik_packages folder
                if not self._packages[pkg].get_folder_basename() in pkg_list:
                    pkg_to_unregister.append(pkg)

            # and unregister some packages if needed
            for pkg in pkg_to_unregister:
                type = self._packages[pkg].get_type()
                name = self._packages[pkg].get_name()
                del(self._packages[pkg])
                if type == 'plugin':
                    self.log.info("Unregister plugin '{0}'".format(name))
                    self._plugins[name].unregister()
                    del(self._plugins[name])

            # publish packages list if there are some updates or new packages
            if packages_updates:
                msg_data = {}
                for pkg in self._packages:
                    msg_data[pkg] = self._packages[pkg].get_json()
                self._pub.send_event('package.detail',
                                     msg_data)

            # wait before next check
            self._stop.wait(CHECK_FOR_NEW_PACKAGES_INTERVAL)

    def _start_core_component(self, name):
        """ Start a core component
            @param name : component name : admin
        """
        component = CoreComponent(name, self.get_sanitized_hostname(), self._clients, self.zmq)
        pid = component.start()
        if pid == 0:
            return False
        else:
            return True

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
        try:
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

            # retrieve the clients conversions
            elif msg.get_action() == "client.conversion.get":
                self.log.info(u"Clients conversion request : {0}".format(msg))
                self._mdp_reply_clients_conversion()

            # retrieve the datatypes
            elif msg.get_action() == "datatype.get":
                self.log.info(u"Clients datatype request : {0}".format(msg))
                self._mdp_reply_datatype()

            # start clients
            elif msg.get_action() == "plugin.start.do":
                self.log.info(u"Plugin startup request : {0}".format(msg))
                self._mdp_reply_plugin_start(msg)

            # stop clients
            # nothing is done in the manager directly :
            # a stop request is sent to a plugin
            # the plugin publish  new status : STATUS_STOP_REQUEST
            # Then, when the manager catches this (done in class Plugin), it will check after a time if the client is stopped

        except:
            self.log.error("Error while processing MQ message : '{0}'. Error is : {1}".format(msg, traceback.format_exc()))


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


    def _mdp_reply_datatype(self):
        """ Reply on the MQ
            @param data : message data
        """
        msg = MQMessage()
        msg.set_action('datatype.result')


        json_file = "{0}/datatypes.json".format(self.get_resources_directory())
        data = OrderedDict()
        try:
            data = json.load(open(json_file), object_pairs_hook=OrderedDict)
        except:
            self.log.error("Error while reading datatypes json file '{0}'. Error is : {1}".format(json_file, traceback.format_exc()))
       
        msg.add_data("datatypes", data)
        self.reply(msg.get())


    def _mdp_reply_clients_list(self):
        """ Reply on the MQ
        """
        msg = MQMessage()
        msg.set_action('client.list.result')
        clients = self._clients.get_list()
        self.log.info("Clients for client.list.get request : {0}".format(clients))
        for key in clients:
            msg.add_data(key, clients[key])
        if clients == []:
            self.log.warning("No clients for client.list.get request. The list is empty!")
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


    def _mdp_reply_clients_conversion(self):
        """ Reply on the MQ
        """
        msg = MQMessage()
        msg.set_action('client.conversion.result')
        conv = self._clients.get_conversions()
        for key in conv:
            msg.add_data(key, conv[key])
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
            type = data.get_data()['type']
            msg.add_data('type', type)
            name = data.get_data()['name']
            msg.add_data('name', name)
            host = data.get_data()['host']
            msg.add_data('host', host)

            # try to start the client
            #
            try:
                if type == "plugin":
                    pid = self._plugins[name].start()
                elif type == "interface":
                    pid = self._interfaces[name].start()
                else:
                    pid = 0

                if pid != 0:
                    status = True
                    reason = ""
                else:
                    status = False
                    reason = "{0} '{1}' startup failed".format(type, name)
            except KeyError:
                # plugin doesn't exist
                status = False
                reason = "{0} '{1}' does not exist on this host".format(type, name)

        msg.add_data('status', status)
        msg.add_data('reason', reason)
        self.reply(msg.get())

    def _register_xpl_client(self, message):
        """ Register non Domogik xPL clients
        """
        # skip domogik components
        if message.source_vendor_id == DMG_VENDOR_ID:
            return

        # process external clients
        self._clients.add(message.source_instance_id, "xpl_client", "{0}-{1}".format(message.source_vendor_id, message.source_device_id), message.source, message.source, None, None, None)
        self._clients.set_status(message.source, STATUS_ALIVE)


    def on_message(self, msgid, content):
        """ Process publicated messages
        """
        if msgid == "metrics.processinfo":
            ### process the processinfo data
            # store them in a list so they can be send by group of data from time to time
            content['id'] = self._metrics_id
            # some additionnal informations
            # TODO : do in ProcessInfo ?
            content['tags']['distribution'] = self.distribution
            self.metrics_processinfo.append(content)

        elif msgid == "metrics.browser":
            ### process the processinfo data
            # store them in a list so they can be send by group of data from time to time
            content['id'] = self._metrics_id
            self.metrics_browser.append(content)


    def _send_metrics(self):
        """ Send the metrics to a REST service. This is related to the ProcessInfo class from common/processinfo.py
        """
        while not self._stop.isSet():
            ratio = 1
            try:

                # send metrics
                self.log.debug(u"Send the metrics to '{0}'".format(self._metrics_url))
                url = self._metrics_url   # just in case of except before first set


                # We put the metrics in buffers and clean the self.xxx metrics now.
                # if the send will fail, we will put back "after" the metrics in the self.xxx in order to resend them later on
                # these buffers allow to avoid cleaning self.xxx with some stuff added during the post actions
                metrics_processinfo = self.metrics_processinfo
                self.metrics_processinfo = []
                metrics_browser = self.metrics_browser
                self.metrics_browser = []

                headers = {'content-type': 'application/json'}

                ### Send process info metrics
                try:
                    url = "{0}/metrics/processinfo/".format(self._metrics_url.strip("/"))
                    response = requests.post(url, data=json.dumps(metrics_processinfo), headers=headers)
                    self.log.debug(u"Metrics for process info send. Server response (http code) is '{0}'".format(response.status_code))

                    ok = True
                except:
                    ok = False
                    ratio = 2    # in case the server does not respond because the load on it is too heavy, send data less often
                    self.log.warning(u"Error while trying to push metrics on '{0}'. The error is : {1}".format(url, traceback.format_exc()))
                # if ok, do nothing
                # if not ok, refill self.xxx with buffer metrics
                if not ok:
                    #for item in self.metrics_processinfo:
                    #    self.log.debug("XXXXX {0}".format(json.dumps(item)))
                    self.metrics_processinfo = metrics_processinfo


                ### Send browsers metrics
                try:
                    url = "{0}/metrics/domoweb-browser/".format(self._metrics_url.strip("/"))
                    response = requests.post(url, data=json.dumps(metrics_browser), headers=headers)
                    self.log.debug(u"Metrics for domoweb browser send. Server response (http code) is '{0}'".format(response.status_code))

                    ok = True
                except:
                    ok = False
                    ratio = 2    # in case the server does not respond because the load on it is too heavy, send data less often
                    self.log.warning(u"Error while trying to push metrics on '{0}'. The error is : {1}".format(url, traceback.format_exc()))
                # if ok, do nothing
                # if not ok, refill self.xxx with buffer metrics
                if not ok:
                    #for item in self.metrics_browser:
                    #    self.log.debug("XXXXX {0}".format(json.dumps(item)))
                    self.metrics_browser = metrics_browser


            except:
                self.log.error(u"Send metrics : error not handled! The error is : {0}".format(traceback.format_exc()))
            # wait for the next time to send
            self._stop.wait(SEND_METRICS_INTERVAL * ratio)

    def _runCacheDevices(self):
        self.log.info(u"Manager run cache")
#        self.__cacheData = WorkerCache()
#        self.log.info(u"Cache running")
        self._pid_dir_path = self.config['pid_dir_path']
        try:
            the_path = os.path.join(os.path.dirname(__file__), "{0}.py".format(('cachedb')))
            self.log.debug(u"Path for component '{0}' is : {1}".format('cache_db', the_path))
        except:
            msg = u"Error while trying to get the module path. The component will not be started !. Error is : {0}".format(traceback.format_exc())
            self.log.error(msg)
            return 0

        ### Generate command
        # we add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
#        cmd = "{0} && {1} {2}".format(STARTED_BY_MANAGER, PYTHON, the_path)
        cmd = "{0} {1}".format(PYTHON, the_path)

        ### Execute command
        self.log.info(u"Execute command : {0}".format(cmd))
        subp = Popen(cmd,
                     shell=True)
        self._cache_pid = subp.pid
        self.log.info(u"Cache running on pid {0}".format(self._cache_pid))
#        subp.communicate()
        pid_file = os.path.join(self._pid_dir_path,
                                CACHE_NAME + ".pid")
        self.log.debug(u"Write pid file for pid '{0}' in file '{1}'".format(str(self._cache_pid), pid_file))
        fil = open(pid_file, "w")
        fil.write(str(self._cache_pid))
        fil.close()



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

    def get_type(self):
        """ Return the package type only
        """
        return self.type

    def get_name(self):
        """ Return the package name only
        """
        return self.name

    def get_folder_basename(self):
        """ Return the folder installation basename of the package
        """
        return "{0}_{1}".format(self.type, self.name)

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
        self.folder = "{0}_{1}".format("plugin", self.name)
        self.type = "unknown - not setted yet"
        self.configured = None
        self._clients = clients
        self.conversions = None
        self.data = {}

        ### init logger
        log = logger.Logger('manager')
        self.log = log.get_logger('manager')

    def register_component(self):
        """ register the component as a client
        """
        self._clients.add(self.host, self.type, self.name, self.client_id, self.xpl_source, self.data, self.conversions, self.configured)

    def unregister(self):
        """ unregister the component
        """
        self._clients.remove(self.client_id)


    def set_configured(self, new_status):
        """ set the flag configured
            @param status : new flag value
        """
        self._clients.set_configured(self.client_id, new_status)


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


    def add_configuration_values_to_data(self):
        """
        """
        # grab all the config elements for the plugin
        config = self._config.query(self.type, self.name)
        if config != None:
            for key in config:
                # filter on the 'configured' key
                if key == 'configured':
                    self.configured = True
                    self.set_configured(True)
                else:
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





class CoreComponent(GenericComponent, MQAsyncSub):
    """ This helps to handle core components startup
        Notice that there is currently no need to stop a core component, we just want to be able to start them
    """

    def __init__(self, name, host, clients, zmq_context):
        """ Init a component
            @param name : component name (admin)
            @param host : hostname
            @param clients : clients list
            @param zmq_context : 0MQ context
        """
        GenericComponent.__init__(self, name = name, host = host, clients = clients)
        self.log.info(u"New core component : {0}".format(self.name))

        ### set the component type
        self.type = "core"

        ### change the client id as 'core-....'
        self.client_id = "{0}-{1}.{2}".format("core", self.name, self.host)

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
        res, pid_list = is_already_launched(self.log, self.type, self.name)
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

        try:
            the_path = os.path.join(os.path.dirname(__file__), "{0}.py".format(self.name))
            self.log.debug(u"Path for component '{0}' is : {1}".format(self.name, the_path))
        except:
            msg = u"Error while trying to get the module path. The component will not be started !. Error is : {0}".format(traceback.format_exc())
            self.log.error(msg)
            return 0

        ### Generate command
        # we add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
        #cmd = "{0} && {1} {2}".format(STARTED_BY_MANAGER, PYTHON, component_path)
        cmd = "{0} && {1} {2}".format(STARTED_BY_MANAGER, PYTHON, the_path)

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

        # TODO : the below if seems useless as this is a core component and not a plugin !
        # to delete ?
        #pass

        #self.log.debug(u"Core : New pub message received {0}".format(msgid))
        #self.log.debug(u"{0}".format(content))
        if msgid == "plugin.status":
            if content["type"] == self.type and content["name"] == self.name and content["host"] == self.host:
                self.log.debug(u"New status received from {0} {1} on {2} : {3}".format(self.type, self.name, self.host, content["event"]))
                self.set_status(content["event"])
        #        # if the status is STATUS_STOP_REQUEST, launch a check in N seconds to check if the plugin was able to shut alone
        #        if content["event"] == STATUS_STOP_REQUEST:
        #            self.log.info(u"The plugin '{0}' is requested to stop. In 15 seconds, we will check if it has stopped".format(self.name))
        #            thr_check_if_stopped = Thread(None,
        #                                          self._check_if_stopped,
        #                                          "check_if_{0}_is_stopped".format(self.name),
        #                                          (),
        #                                          {})
        #            thr_check_if_stopped.start()



class Brain(GenericComponent, MQAsyncSub):
    """ This helps to handle brains discovered on the host filesystem

        Notice that this kind of packages is only data!
        * the brain packages will never "run"
        * they have no alive/stopped/dead/... status
    """

    def __init__(self, name, host, clients, libraries_directory, packages_directory, zmq_context, stop, local_host):
        """ Init a plugin
            @param name : brain name (ipx800, onewire, ...)
            @param host : hostname
            @param clients : clients list
            @param libraries_directory : path for the base python module for packages : /var/lib/domogik/
            @param packages_directory : path in which are stored the packages : /var/lib/domogik/packages/
            @param zmq_context : zmq context
            @param stop : get_stop()
            @param local_host : get_sanitized_hostname()
        """
        GenericComponent.__init__(self, name = name, host = host, clients = clients)
        self.log.info(u"New brain : {0}".format(self.name))

        ### change the client id as 'brain-....'
        self.client_id = "{0}-{1}.{2}".format("brain", self.name, self.host)

        ### check if the plugin is on he local host
        self.local_plugin = True

        ### set the component type
        self.type = "brain"

        ### zmq context
        self.zmq = zmq_context

        ### config
        # used only in the function add_configuration_values_to_data()
        # elsewhere, this function is used : self.get_config("xxxx")
        self._config = Query(self.log, host)

        ### set package path
        self._packages_directory = packages_directory

        ### get the plugin data (from the json file)
        self.data = {}
        self.fill_data()

        #TO DEL ??#
        self.configured = False

        ### subscribe the the MQ for category = plugin and name = self.name
        MQAsyncSub.__init__(self, self.zmq, 'manager', ['plugin.configuration'])

        ### register the plugin as a client
        self.register_component()


    def on_message(self, msgid, content):
        """ when a message is received from the MQ
        """
        self.log.debug(u"{0}".format(content))
        if msgid == "plugin.configuration":
            # TODO : rename plugin.configuration to client.configuration ?
            #        as this is currently used by type=plugin, brain
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
            self.log.info(u"Brain {0} : read the json file".format(self.name))
            pkg_json = PackageJson(pkg_type = "brain", name = self.name)
            #we don't need to validate the json file as it has already be done in the check_avaiable_packages function
            self.data = pkg_json.get_json()
            self.add_configuration_values_to_data()
        except PackageException as e:
            self.log.error(u"Brain {0} : error while trying to read the json file".format(self.name))
            self.log.error(u"Brain {0} : invalid json file".format(self.name))
            self.log.error(u"Brain {0} : {1}".format(self.name, e.value))
            self.set_status(STATUS_INVALID)
            pass


class Plugin(GenericComponent, MQAsyncSub):
    """ This helps to handle plugins discovered on the host filesystem
        The MQAsyncSub helps to set the status

        Notice that some actions can't be done if the plugin host is not the server host! :
        * check if a plugin has stopped and kill it if needed
        * start the plugin

        Notice also that all brain parts are to be hosted on the master Domogik

        TODO : create a parent class PythonClient
               the classes Plugin, Interface and any other thant depends on python will inherit from it
               as there are currently a lot of common code in Plugin and Interface classes
    """

    def __init__(self, name, host, clients, libraries_directory, packages_directory, zmq_context, stop, local_host):
        """ Init a plugin
            @param name : plugin name (core, datatype, ...)
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
        self._config = Query(self.log, host)

        ### get the plugin data (from the json file)
        self.data = {}
        self.fill_data()

        ### check if the plugin is configured (get key 'configured' in database over queryconfig)
        configured = self._config.query(self.type, self.name, 'configured')
        if configured == '1':
            configured = True
        if configured == True:
            #self.set_configured(True)
            self.configured = True
        else:
            #self.set_configured(False)
            self.configured = False

        ### get udev rules informations
        udev_rules = {}
        udev_dir = "{0}/{1}/udev_rules/".format(self._packages_directory, self.folder)

        # parse all udev files
        try:
            for udev_file in os.listdir(udev_dir):
                if udev_file.endswith(".rules"):
                    self.log.info("Udev rule discovered for '{0}' : {1}".format(self.client_id, udev_file))
                    # read the content of the file
                    with open ("{0}/{1}".format(udev_dir, udev_file), "r") as myfile:
                        data = myfile.read()
                        udev_rules[os.path.splitext(udev_file)[0]] = data
        except OSError as err:
            if err.errno == 2:
                self.log.info("There is no udev rules file for '{0}'".format(self.client_id))
            else:
                self.log.error("Error while looking for udev rules for '{0}' : {1}".format(self.client_id, err))

        # add in the data
        self.data["udev_rules"] = udev_rules

        ### get conversion informations
        self.conversions = {}
        conv_dir = "{0}/{1}/conversion/".format(self._packages_directory, self.folder)

        # parse all conversion files
        try:
            for conv_file in os.listdir(conv_dir):
                if conv_file.endswith(".py") and conv_file != "__init__.py":
                    self.log.info("Conversion discovered for '{0}' : {1}".format(self.client_id, conv_file))
                    # read the content of the file
                    with open ("{0}/{1}".format(conv_dir, conv_file), "r") as myfile:
                        data = myfile.read()
                        self.conversions[os.path.splitext(conv_file)[0]] = data
        except OSError as err:
            if err.errno == 2:
                self.log.info("There is no conversion file for '{0}'".format(self.client_id))
            else:
                self.log.error("Error while looking for udev rules for '{0}' : {1}".format(self.client_id, err))

        ### register the plugin as a client
        self.register_component()

        ### subscribe the the MQ for category = plugin and name = self.name
        MQAsyncSub.__init__(self, self.zmq, 'manager', ['plugin.status', 'plugin.configuration'])

        ### check if the plugin must be started on manager startup
        startup = self._config.query(self.type, self.name, 'auto_startup')
        if startup == '1' or startup == 'Y':
            startup = True
        if startup == True:
            res, pid_list = is_already_launched(self.log, self.type, self.name)
            if res:
                self.log.error(u"Plugin {0} failed to start, Process already running (pid :{1})".format(name, pid_list))
            else :
                self.log.info(u"Plugin {0} configured to be started on manager startup. Starting...".format(name))
                pid = self.__start()
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
            if content["type"] == self.type and content["name"] == self.name and content["host"] == self.host:
                self.log.debug(u"New status received from {0} {1} on {2} : {3}".format(self.type, self.name, self.host, content["event"]))
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
            # TODO : rename plugin.configuration to client.configuration ?
            #        as this is currently used by type=plugin, brain
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

    # MOVED in the parent class because used also for brain, interface types
    #def add_configuration_values_to_data(self):
    #    """
    #    """
    #    # grab all the config elements for the plugin
    #    config = self._config.query(self.name)
    #    if config != None:
    #        for key in config:
    #            # filter on the 'configured' key
    #            if key == 'configured':
    #                self.configured = True
    #                self.set_configured(True)
    #            else:
    #                # check if the key exists in the plugin configuration
    #                key_found = False
    #                # search the key in the configuration json part
    #                for idx in range(len(self.data['configuration'])):
    #                    if self.data['configuration'][idx]['key'] == key:
    #                        key_found = True
    #                        # key found : insert value in the json
    #                        self.data['configuration'][idx]['value'] = config[key]
    #                if key_found == False:
    #                    self.log.warning(u"A key '{0}' is configured for plugin {1} on host {2} but there is no such key in the json file of the plugin. You may need to clean your configuration".format(key, self.name, self.host))

    def start(self):
        """ to call to start the plugin, Call real start in a thread
            @return : None if ko
                      0 if already started
                      1 if starting is launch
        """
        ### Check if the plugin is not already launched
        # notice that this test is not really needed as the plugin also test this in startup...
        # but the plugin does it before the MQ is initiated, so the error message won't go overt the MQ.
        # By doing it now, the error will go to the UI through the 'error' MQ messages (sended by self.log.error)
        res, pid_list = is_already_launched(self.log, self.type, self.name)
        if res:
            return 0
        Thread(None,
              self.__start,
              "th_Start_{0}".format(self.name),
              (),
              {}).start()
        return 1

    def __start(self):
        """ to call to start the plugin in a thread and don't lock MQ response.
            Don't recheck already launched
            @return : Nothing
        """
        ### Actions for test mode
        test_mode = self._config.query(self.type, self.name, "test_mode")
        test_option = self._config.query(self.type, self.name, "test_option")
        test_args = ""
        if test_mode == True:
            self.log.info("The plugin {0} is requested to be launched in TEST mode. Option is {1}".format(self.name, test_option))
            test_args = "-T {0}".format(test_option)

        ### Try to start the plugin
        self.log.info(u"Request to start plugin : {0} {1}".format(self.name, test_args))
        pid = self.exec_component(py_file = "{0}/plugin_{1}/bin/{2}.py {3}".format(self._packages_directory, self.name, self.name, test_args), \
                                  env_pythonpath = self._libraries_directory)

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
        cmd += "{0} {1}".format(PYTHON, py_file.strip())

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
        self.log.debug("Check if the plugin {0} has stopped it self. Else there will be a bloodbath".format(self.name))
        res, pid_list = is_already_launched(self.log, self.type, self.name)
        if res:
            for the_pid in pid_list:
                self.log.info(u"Try to kill pid {0}...".format(the_pid))
                os.kill(int(the_pid), signal.SIGKILL)
                # TODO : add one more check ?
                # do a while loop over is_already.... ?
                # update on 20/03/14 : it seems this is not needed currently
            self.log.info(u"The plugin {0} should be killed now (kill -9)".format(self.name))
        else:
            self.log.info(u"The plugin {0} has stopped itself properly.".format(self.name))


class Interface(GenericComponent, MQAsyncSub):
    """ This helps to handle interfaces discovered on the host filesystem
        The MQAsyncSub helps to set the status

        Notice that some actions can't be done if the plugin host is not the server host! :
        * check if a plugin has stopped and kill it if needed
        * start the plugin

    """

    def __init__(self, name, host, clients, libraries_directory, packages_directory, zmq_context, stop, local_host):
        """ Init an interface
            @param name : interface name
            @param host : hostname
            @param clients : clients list
            @param libraries_directory : path for the base python module for packages : /var/lib/domogik/
            @param packages_directory : path in which are stored the packages : /var/lib/domogik/packages/
            @param zmq_context : zmq context
            @param stop : get_stop()
            @param local_host : get_sanitized_hostname()
        """
        GenericComponent.__init__(self, name = name, host = host, clients = clients)
        self.log.info(u"New interface : {0}".format(self.name))

        ### change the client id as 'interface-....'
        self.client_id = "{0}-{1}.{2}".format("interface", self.name, self.host)

        ### check if the interface is on he local host
        if self.host == local_host:
            self.local_interface = True
        else:
            self.local_interface = False

        ### TODO : this will be to handle later : multi host (multihost)
        # * how to find available interface on other hosts ?
        # * how to start/stop interface on other hosts ?
        # * ...
        if self.local_interface == False:
            self.log.error(u"Currently, the multi host feature for interfaces is not yet developped. This interface will not be registered")
            return

        ### set the component type
        self.type = "interface"

        ### set package path
        self._packages_directory = packages_directory
        self._libraries_directory = libraries_directory

        ### zmq context
        self.zmq = zmq_context

        ### config
        # used only in the function add_configuration_values_to_data()
        # elsewhere, this function is used : self.get_config("xxxx")
        self._config = Query(self.log, host)

        ### get the interface data (from the json file)
        self.data = {}
        self.fill_data()

        ### check if the interface is configured (get key 'configured' in database over queryconfig)
        configured = self._config.query(self.type, self.name, 'configured')
        if configured == '1':
            configured = True
        if configured == True:
            self.configured = True
        else:
            self.configured = False

        ### get udev rules informations
        udev_rules = {}
        udev_dir = "{0}/{1}/udev_rules/".format(self._packages_directory, self.folder)

        # parse all udev files
        try:
            for udev_file in os.listdir(udev_dir):
                if udev_file.endswith(".rules"):
                    self.log.info("Udev rule discovered for '{0}' : {1}".format(self.client_id, udev_file))
                    # read the content of the file
                    with open ("{0}/{1}".format(udev_dir, udev_file), "r") as myfile:
                        data = myfile.read()
                        udev_rules[os.path.splitext(udev_file)[0]] = data
        except OSError as err:
            if err.errno == 2:
                self.log.info("There is no udev rules file for '{0}'".format(self.client_id))
            else:
                self.log.error("Error while looking for udev rules for '{0}' : {1}".format(self.client_id, err))


        # add in the data
        self.data["udev_rules"] = udev_rules

        # there is no conversion files

        ### register the interface as a client
        self.register_component()

        ### subscribe the the MQ for category = interface and name = self.name
        MQAsyncSub.__init__(self, self.zmq, 'manager', ['plugin.status', 'plugin.configuration'])

        ### check if the interface must be started on manager startup
        startup = self._config.query(self.type, self.name, 'auto_startup')
        if startup == '1' or startup == 'Y':
            startup = True
        if startup == True:
            self.log.info(u"Interface {0} configured to be started on manager startup. Starting...".format(name))
            pid = self.start()
            if pid:
                self.log.info(u"Interface {0} started".format(name))
            else:
                self.log.error(u"Interface {0} failed to start".format(name))
        else:
            self.log.info(u"Interface {0} not configured to be started on manager startup.".format(name))


    def on_message(self, msgid, content):
        """ when a message is received from the MQ
        """
        #self.log.debug(u"New pub message received {0}".format(msgid))
        #self.log.debug(u"{0}".format(content))
        if msgid == "plugin.status":
            if content["type"] == self.type and content["name"] == self.name and content["host"] == self.host:
                self.log.debug(u"New status received from {0} {1} on {2} : {3}".format(self.type, self.name, self.host, content["event"]))
                self.set_status(content["event"])
                # if the status is STATUS_STOP_REQUEST, launch a check in N seconds to check if the plugin was able to shut alone
                if content["event"] == STATUS_STOP_REQUEST:
                    self.log.info(u"The interface '{0}' is requested to stop. In 15 seconds, we will check if it has stopped".format(self.name))
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
            self.log.info(u"Interface {0} : read the json file".format(self.name))
            pkg_json = PackageJson(pkg_type = "interface", name = self.name)
            #we don't need to validate the json file as it has already be done in the check_avaiable_packages function
            self.data = pkg_json.get_json()
            self.add_configuration_values_to_data()
        except PackageException as e:
            self.log.error(u"Interface {0} : error while trying to read the json file".format(self.name))
            self.log.error(u"Interface {0} : invalid json file".format(self.name))
            self.log.error(u"Interface {0} : {1}".format(self.name, e.value))
            self.set_status(STATUS_INVALID)
            pass


    def start(self):
        """ to call to start the interface
            @return : None if ko
                      the pid if ok
        """
        ### Check if the interface is not already launched
        # notice that this test is not really needed as the client also test this in startup...
        # but the interface does it before the MQ is initiated, so the error message won't go overt the MQ.
        # By doing it now, the error will go to the UI through the 'error' MQ messages (sended by self.log.error)

        # TODO : add type in is_already_launched params!!!!!
        res, pid_list = is_already_launched(self.log, self.type, self.name)
        if res:
            return 0

        ### Actions for test mode
        test_mode = self._config.query(self.type, self.name, "test_mode")
        test_option = self._config.query(self.type, self.name, "test_option")
        test_args = ""
        if test_mode == True:
            self.log.info("The interface {0} is requested to be launched in TEST mode. Option is {1}".format(self.name, test_option))
            test_args = "-T {0}".format(test_option)

        ### Try to start the interface
        self.log.info(u"Request to start interface : {0} {1}".format(self.name, test_args))
        pid = self.exec_component(py_file = "{0}/{1}_{2}/bin/{3}.py {4}".format(self._packages_directory, self.type, self.name, self.name, test_args), \
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
        cmd += "{0} {1}".format(PYTHON, py_file.strip())

        ### Execute command
        self.log.info(u"Execute command : {0}".format(cmd))
        subp = Popen(cmd,
                     shell=True)
        pid = subp.pid
        subp.communicate()
        return pid


    def _check_if_stopped(self):
        """ Check if the interface is stopped. If not, kill it
        """
        self._stop.wait(WAIT_AFTER_STOP_REQUEST)
        self.log.debug("Check if the interface {0} has stopped it self. Else there will be a bloodbath".format(self.name))
        res, pid_list = is_already_launched(self.log, self.type, self.name)
        if res:
            for the_pid in pid_list:
                self.log.info(u"Try to kill pid {0}...".format(the_pid))
                os.kill(int(the_pid), signal.SIGKILL)
                # TODO : add one more check ?
                # do a while loop over is_already.... ?
                # update on 20/03/14 : it seems this is not needed currently
            self.log.info(u"The interface {0} should be killed now (kill -9)".format(self.name))
        else:
            self.log.info(u"The interface {0} has stopped itself properly.".format(self.name))




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

    def __init__(self, stop):
        """ prepare an empty package list
        """
        ### init vars
        self._stop = stop
        self._clients = {}
        self._clients_with_details = {}
        self._conversions = {}

        ### init logger
        log = logger.Logger('manager')
        self.log = log.get_logger('manager')
        self.log.info(u"Clients initialisation")
        self._pub = MQPub(zmq.Context(), 'manager')

        ### Check for dead clients
        thr_check_dead_clients = Thread(None,
                                        self._check_dead_clients,
                                        "check_dead_clients",
                                        (),
                                        {})
        thr_check_dead_clients.start()

    def _check_dead_clients(self):
        """ Check if some clients are dead
            If the last time a client n a alive state has been seen is greater than twice STATUS_HBEAT seconds, set the client as dead
        """
        while not self._stop.isSet():
            now = time.time()
            for a_client in self._clients:
                if self._clients[a_client]['type'] in ['plugin', 'core', 'interface']:
                    # check if the client is dead only when the client is alive (or partially alive)
                    if self._clients[a_client]['status'] in (STATUS_STARTING, STATUS_ALIVE, STATUS_STOP_REQUEST):
                        delta = now - self._clients[a_client]['last_seen']
                        if delta > 2*STATUS_HBEAT:
                            # client is dead!
                            self.set_status(a_client, STATUS_DEAD)

                elif self._clients[a_client]['type'] == 'xpl_client':
                    # check if the client is dead only when the client is alive (a xpl client can be only ALIVE or DEAD)
                    if self._clients[a_client]['status'] in (STATUS_ALIVE):
                        delta = now - self._clients[a_client]['last_seen']
                        # Here we do a shorcut.... we should check the delta related to the 'interval' information taken from
                        # the body of the hbeat.app or hbeat.basic message.
                        # But as usually I never see a xpl client with interval > 5, we assume that 5 is a default common value
                        # This part may of course be improved later ;)
                        if delta > 2*(STATUS_HBEAT_XPL*60):
                            # client is dead!
                            self.set_status(a_client, STATUS_DEAD)
            self._stop.wait(STATUS_HBEAT)

    def add(self, host, type, name, client_id, xpl_source, data, conversions, configured = None):
        """ Add a client to the list of clients
            @param host : client hostname or ip or dns
            @param type : client type
            @param name : client name
            @param client_id : client id
            @param data : client data : only for clients details
            @param configured : True/False : for a plugin : True if the plugin is configured, else False
                                None : for type != 'plugin'
            @param conversions : conversions info for the client
        """
        self.log.info(u"Add new client : host={0}, type={1}, name={2}, client_id={3}, data={4}".format(host, type, name, client_id, str(data)))
        try:
            if data != None:
                try:
                    compliant_xpl_clients = data["identity"]["compliant_xpl_clients"]
                except KeyError:
                    # data is empty for core components
                    compliant_xpl_clients = []

                try:
                    xpl_clients_only = data["identity"]["xpl_clients_only"]
                except KeyError:
                    # data is empty for core components
                    xpl_clients_only = []
            else:
                compliant_xpl_clients = []
                xpl_clients_only = []
            client = { "host" : host,
                       "type" : type,
                       "name" : name,
                       "xpl_source" : xpl_source,
                       "package_id" : "{0}-{1}".format(type, name),
                       "pid" : 0,
                       "last_seen" : time.time(),
                       "status" : STATUS_STOPPED,
                       "configured" : configured,
                       "compliant_xpl_clients" : compliant_xpl_clients,
                       "xpl_clients_only" : xpl_clients_only}
            client_with_details = { "host" : host,
                       "type" : type,
                       "name" : name,
                       "xpl_source" : xpl_source,
                       "package_id" : "{0}-{1}".format(type, name),
                       "pid" : 0,
                       "last_seen" : time.time(),
                       "status" : STATUS_STOPPED,
                       "configured" : configured,
                       "data" : data}
            self._clients[client_id] = client
            self._clients_with_details[client_id] = client_with_details
            self._conversions[client_id] = conversions
            self.publish_update()
        except:
            self.log.error("Error when adding the client in the clients list. Error : {0}".format(traceback.format_exc()))

    def remove(self, client_id):
        """ Remove a client from the list
        """
        del(self._clients[client_id])
        del(self._clients_with_details[client_id])
        self.publish_update()


    def set_configured(self, client_id, new_status):
        """ Set a new status to a client
        """
        # the first time this function is called, the client is not already registered (on client startup)
        # so we need to handle this case to avoid a KeyError exception
        if client_id not in self._clients:
            return
        old_status = self._clients[client_id]['configured']
        if old_status == new_status:
            return
        self._clients[client_id]['configured'] = new_status
        self.log.info("The client 'configured' flag is now set to : {0}".format(new_status))
        self.publish_update()

    def set_status(self, client_id, new_status):
        """ Set a new status to a client
        """
        self.log.debug(u"Try to set a new status : {0} => {1}".format(client_id, new_status))
        if new_status not in (STATUS_UNKNOWN, STATUS_STARTING, STATUS_ALIVE, STATUS_STOPPED, STATUS_DEAD, STATUS_INVALID, STATUS_STOP_REQUEST, STATUS_NOT_CONFIGURED):
            self.log.error(u"Invalid status : {0}".format(new_status))
            return
        if client_id not in self._clients:
            return
        old_status = self._clients[client_id]['status']
        # in all cases, set the 'last seen' time for the clients which are not dead
        if new_status != STATUS_DEAD:
            self._clients[client_id]['last_seen'] = time.time()
        if old_status == new_status:
            self.log.debug(u"The status was already {0} : nothing to do".format(old_status))
            return
        self._clients[client_id]['status'] = new_status
        self._clients_with_details[client_id]['status'] = new_status
        self.log.info(u"Status set : {0} => {1}".format(client_id, new_status))
        # in case the client is dead, it means that it could have been killed or anything else.
        # so the client was not able to send itself the plugin.status message with status 'dead'...
        # so the manager will do it for the client!
        if new_status == STATUS_DEAD:
            self.log.debug("Send plugin.status for client {0} and status = {1}....".format(client_id, STATUS_DEAD))
            try:
                package, host = client_id.split(".")
                type, name = package.split("-")
                self._pub.send_event('plugin.status',
                                     {"type" : type,
                                      "name" : name,
                                      "host" : host,
                                      "event" : STATUS_DEAD})
            except:
                # bad data...
                pass
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

    def get_conversions(self):
        """ Return the clients conversions elements
        """
        return self._conversions

    def publish_update(self):
        """ Publish the clients list update over the MQ
        """
        # MQ publisher
        self._pub.send_event('client.list',
                             self._clients)
        self._pub.send_event('client.detail',
                             self._clients_with_details)
        self._pub.send_event('client.conversion',
                             self._conversions)




def main():
    ''' Called by the easyinstall mapping script
    '''
    Manager()

if __name__ == "__main__":
    main()

# this is a test.


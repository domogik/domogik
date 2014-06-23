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

Base class for all xPL clients

Implements
==========

- XplPlugin
- XplResult

@author: Maxence Dunnewind <maxence@dunnewind.net>
         Fritz SMH <fritz.smg@gmail.com> for refactoring
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import signal
import threading
import os
import sys
from domogik.common.baseplugin import BasePlugin
from domogik.common.utils import ucode
from domogik.common.queryconfig import Query
from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common.processinfo import ProcessInfo
from domogik.mq.pubsub.publisher import MQPub
from domogik.mq.reqrep.worker import MQRep
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from zmq.eventloop.ioloop import IOLoop
from domogik.common.packagejson import PackageJson, PackageException
import zmq
import traceback
import json

# clients (plugins, etc) status
STATUS_UNKNOWN = "unknown"
STATUS_STARTING = "starting"
STATUS_NOT_CONFIGURED = "not-configured"
STATUS_ALIVE = "alive"
STATUS_STOP_REQUEST = "stop-request"
STATUS_STOPPED = "stopped"
STATUS_DEAD = "dead"
STATUS_INVALID = "invalid"

# time between each send of the status
STATUS_HBEAT = 15

# core components
CORE_COMPONENTS = ['manager', 'rest', 'dbmgr', 'xplgw', 'send', 'dump_xpl', 'scenario', 'admin']

# folder for the packages in library_path folder (/var/lib/domogik/)
PACKAGES_DIR = "domogik_packages"
RESOURCES_DIR = "resources"
PRODUCTS_DIR = "products"
PRODUCTS_PICTURES_EXTENSIONS = ['jpg', 'png']

# domogik vendor id (for xpl)
DMG_VENDOR_ID = "domogik"

# time between each read of cpu/memory usage for process
TIME_BETWEEN_EACH_PROCESS_STATUS = 60


class Plugin(BasePlugin, MQRep):
    '''
    Global plugin class, manage signal handlers.
    This class shouldn't be used as-it but should be extended by no xPL plugin or by the class xPL plugin which will be used by the xPL plugins
    This class is a Singleton
    '''


    def __init__(self, name, stop_cb = None, is_manager = False, parser = None,
                 daemonize = True, test = False):
        '''
        Create XplPlugin instance, which defines system handlers
        @param name : The name of the current plugin
        @param stop_cb : Additionnal method to call when a stop request is received
        @param is_manager : Must be True if the child script is a Domogik Manager process
        You should never need to set it to True unless you develop your own manager
        @param parser : An instance of ArgumentParser. If you want to add extra options to the generic option parser,
        create your own ArgumentParser instance, use parser.add_argument and then pass your parser instance as parameter.
        Your options/params will then be available on self.options and self.args
        @param daemonize : If set to False, force the instance *not* to daemonize, even if '-f' is not passed
        on the command line. If set to True (default), will check if -f was added.
        '''
        BasePlugin.__init__(self, name, stop_cb, parser, daemonize)
        Watcher(self)
        self.log.info(u"----------------------------------")
        self.log.info(u"Starting plugin '%s' (new manager instance)" % name)
        self.log.info(u"Python version is {0}".format(sys.version_info))
        if self.options.test_option:
            self.log.info(u"The plugin is starting in TEST mode. Test option is {0}".format(self.options.test_option))
        self._name = name
        self._test = test   # flag used to avoid loading json in test mode
        
        '''
        Calculate the MQ name
        - For a core component this is just its component name (self._name)
        - For a plugin this is plugin-<self._name>-self.hostname

        The reason is that the core components need a fixed name on the mq network,
        if a plugin starts up it needs to request the config on the network, and it needs to know the worker (core component)
        to ask the config from.

        Because of the above reason, every item in the core_component list can only run once
        '''
        if self._name in CORE_COMPONENTS:
            self._mq_name = self._name
        else:
            self._mq_name = "plugin-{0}.{1}".format(self._name, self.get_sanitized_hostname())

        # MQ publisher and REP
        self.zmq = zmq.Context()
        self._pub = MQPub(self.zmq, self._mq_name)
        self._set_status(STATUS_STARTING)

        # MQ : start the thread which sends the status each N seconds
        thr_send_status = threading.Thread(None,
                                           self._send_status_loop,
                                           "send_status_loop",
                                           (),
                                           {})
        thr_send_status.start()

        ### MQ
        # for stop requests
        MQRep.__init__(self, self.zmq, self._mq_name)

        self.helpers = {}
        self._is_manager = is_manager
        cfg = Loader('domogik')
        my_conf = cfg.load()
        self._config_files = CONFIG_FILE
        self.config = dict(my_conf[1])
 
        self.libraries_directory = self.config['libraries_path']
        self.packages_directory = "{0}/{1}".format(self.config['libraries_path'], PACKAGES_DIR)
        self.resources_directory = "{0}/{1}".format(self.config['libraries_path'], RESOURCES_DIR)
        self.products_directory = "{0}/{1}_{2}/{3}".format(self.packages_directory, "plugin", self._name, PRODUCTS_DIR)

        # Get pid and write it in a file
        self._pid_dir_path = self.config['pid_dir_path']
        self._get_pid()

        if len(self.get_sanitized_hostname()) > 16:
            self.log.error(u"You must use 16 char max hostnames ! %s is %s long" % (self.get_sanitized_hostname(), len(self.get_sanitized_hostname())))
            self.force_leave()
            return

        # Create object which get process informations (cpu, memory, etc)
        # TODO : activate
        # TODO : use something else that xPL ?????????
        #self._process_info = ProcessInfo(os.getpid(),
        #                                 TIME_BETWEEN_EACH_PROCESS_STATUS,
        #                                 self._send_process_info,
        #                                 self.log,
        #                                 self.myxpl)
        #self._process_info.start()

        self.dont_run_ready = False

        # for all no core elements, load the json
        # TODO find a way to do it nicer ??
        if self._name not in CORE_COMPONENTS and self._test == False:
            self._load_json()

        # init an empty instances list
        self.instances = []
        # init an empty 'new' instances list
        self.new_instances = []

        # check for products pictures
        if self._name not in CORE_COMPONENTS and self._test == False:
            self.check_for_pictures()

        # init finished
        self.log.info(u"End init of the global Plugin part")


    def check_configured(self):
        """ For a plugin only
            To be call in the plugin __init__()
            Check in database (over queryconfig) if the key 'configured' is set to True for the plugin
            if not, stop the plugin and log this
        """
        self._config = Query(self.zmq, self.log)
        configured = self._config.query(self._name, 'configured')
        if configured == '1':
            configured = True
        if configured != True:
            self.log.error(u"The plugin is not configured (configured = '{0}'. Stopping the plugin...".format(configured))
            self.force_leave(status = STATUS_NOT_CONFIGURED)
            return False
        self.log.info(u"The plugin is configured. Continuing (hoping that the user applied the appropriate configuration ;)")
        return True


    def _load_json(self):
        """ Load the plugin json file
        """
        try:
            self.log.info(u"Read the json file and validate id".format(self._name))
            pkg_json = PackageJson(pkg_type = "plugin", name = self._name)
            # check if json is valid
            if pkg_json.validate() == False:
                # TODO : how to get the reason ?
                self.log.error(u"Invalid json file")
                self.force_leave(status = STATUS_INVALID)
            else:
                # if valid, store the data so that it can be used later
                self.log.info(u"The json file is valid")
                self.json_data = pkg_json.get_json()
        except:
            self.log.error(u"Error while trying to read the json file : {1}".format(self._name, traceback.format_exc()))
            self.force_leave(status = STATUS_INVALID)

    def get_config(self, key):
        """ Try to get the config over the MQ. If value is None, get the default value
        """
        value = self._config.query(self._name, key)
        if value == None or value == 'None':
            self.log.info(u"Value for '{0}' is None or 'None' : trying to get the default value instead...".format(key))
            value = self.get_config_default_value(key)
        self.log.info(u"Value for '{0}' is : {1}".format(key, value))
        return self.cast_config_value(key, value)

    def get_config_default_value(self, key):
        """ Get the default value for a config key from the json file
            @param key : configuration key
        """
        for idx in range(len(self.json_data['configuration'])):
            if self.json_data['configuration'][idx]['key'] == key:
                default = self.json_data['configuration'][idx]['default']
                self.log.info(u"Default value required for key '{0}' = {1}".format(key, default))
                return default

    def cast_config_value(self, key, value):
        """ Cast the config value as the given type in the json file
            @param key : configuration key
            @param value : configuration value to cast and return
            @return : the casted value
        """
        for idx in range(len(self.json_data['configuration'])):
            if self.json_data['configuration'][idx]['key'] == key:
                type = self.json_data['configuration'][idx]['default']
                self.log.info(u"Casting value for key '{0}' in type '{1}'...".format(key, type)) 
                return self.cast(value, type)

        # no cast operation : return the value
        if value == "None":
            return None
        return value

    def cast(self, value, type):
        """ Cast a value for a type
            @param value : value to cast
            @param type : type in which you want to cast the value
        """
        try:
            if type == "boolean":
                # just in case, the "True"/"False" are not already converted in True/False
                # this is (currently) done on queryconfig side
                if value == "True":
                    return True
                elif value ==  "False":
                    return False
            # type == choice : nothing to do
            if type == "date": 
                self.log.error(u"TODO : the cast in date format is not yet developped. Please request fritz_smh to do it")
            if type == "datetime": 
                self.log.error(u"TODO : the cast in date format is not yet developped. Please request fritz_smh to do it")
            # type == email : nothing to do
            if type == "float":
                return float(value)
            if type == "integer":
                return float(value)
            # type == ipv4 : nothing to do
            # type == multiple choice : nothing to do
            # type == string : nothing to do
            if type == "time": 
                self.log.error(u"TODO : the cast in date format is not yet developped. Please request fritz_smh to do it")
            # type == url : nothing to do

        except:
            # if an error occurs : return the default value and log a warning
            self.log.warning(u"Error while casting value '{0}' to type '{1}'. The plugin may not work!! Error : {2}".format(value, type, traceback.format_exc()))
            return value
        return value

    def get_instance_list(self, quit_if_no_instance = False):
        """ Request the dbmgr component over MQ to get the instances list for this client
            @param quit_if_no_instance: if True, exit the plugin if there is no instances
        """
        self.log.info(u"Retrieve the instances list for this client...")
        mq_client = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('instance.get')
        msg.add_data('type', 'plugin')
        msg.add_data('name', self._name)
        msg.add_data('host', self.get_sanitized_hostname())
        result = mq_client.request('dbmgr', msg.get(), timeout=10)
        if not result:
            self.log.error(u"Unable to retrieve the instance list")
            self.force_leave()
            return []
        else:
            instance_list = result.get_data()['instances']
            if instance_list == []:
                self.log.warn(u"There is no instance created for this client")
                if quit_if_no_instance:
                    self.log.warn(u"The developper requested to stop the client if there is no instance created")
                    self.force_leave()
                    return []
            for a_instance in instance_list:
                self.log.info(u"- id : {0}  /  name : {1}  /  instance type id : {2}".format(a_instance['id'], \
                                                                                    a_instance['name'], \
                                                                                    a_instance['instance_type_id']))
                # log some informations about the instance
                # notice that even if we are not in the XplPlugin class we will display xpl related informations :
                # for some no xpl plugins, there will just be nothing to display.

                # first : the stats
                self.log.info(u"  xpl_stats features :")
                for a_xpl_stat in a_instance['xpl_stats']:
                    self.log.info(u"  - {0}".format(a_xpl_stat))
                    self.log.info(u"    Static Parameters :")
                    for a_feature in a_instance['xpl_stats'][a_xpl_stat]['parameters']['static']:
                        self.log.info(u"    - {0} = {1}".format(a_feature['key'], a_feature['value']))
                    self.log.info(u"    Dynamic Parameters :")
                    for a_feature in a_instance['xpl_stats'][a_xpl_stat]['parameters']['dynamic']:
                        self.log.info(u"    - {0}".format(a_feature['key']))

                # then, the commands
                self.log.info(u"  xpl_commands features :")
                for a_xpl_cmd in a_instance['xpl_commands']:
                    self.log.info(u" - {0}".format(a_xpl_cmd))
                    self.log.info(u" + Parameters :")
                    for a_feature in a_instance['xpl_commands'][a_xpl_cmd]['parameters']:
                        self.log.info(u" - {0} = {1}".format(a_feature['key'], a_feature['value']))

            self.instances = instance_list
            return instance_list


    def instance_detected(self, instance_type, type, feature, data):
        """ The plugin developpers can call this function when a instance is detected
            This function will check if a corresponding instance exists and : 
            - if so, do nothing
            - if not, add the instance in a 'new instances' list
                 - if the instance is already in the 'new instances list', does nothing
                 - if not : add it into the list and send a MQ message : an event for the UI to say a new instance is detected

            ### TODO : implement a req/rep MQ message to allow UI to get the new instances list

            @param instance_type : instance_type of the detected instance
            @param data : data about the instance (address or any other configuration element of a instance for this plugin)
            @param type : xpl_stats, xpl_commands
            @param feature : a xpl_stat or xpl_command feature
        """
        self.log.debug(u"Device detected : instance_type = {0}, data = {1}".format(instance_type, data))
        #self.log.debug(u"Already existing instances : {0}".format(self.instances))
        # browse all instances to find if the instance exists
        found = False
        for a_instance in self.instances:
            # first, search for instance type
            if a_instance['instance_type_id'] == instance_type:
                params = a_instance[type][feature]['parameters']['static']
                found = True
                for key in data:
                    for a_param in params:
                        if key == a_param['key'] and data[key] != a_param['value']:
                            found = False
                            break
                if found:
                    break
        if found:
            self.log.debug(u"The instance already exists : id={0}.".format(a_instance['id']))
        else:
            self.log.debug(u"The instance doesn't exists in database")
         
            # add the instance feature in the new instances list : self.new_instances[instance_type][type][feature] = data
            self.log.debug(u"Check if the instance has already be marked as new...")
            found = False
            for a_instance in self.new_instances:
                if a_instance['instance_type_id'] == instance_type and \
                   a_instance['type'] == type and \
                   a_instance['feature'] == feature:

                   if data == a_instance['data']:
                        found = True
                    
            if found == False:
                new_instance ={'instance_type_id' : instance_type,
                             'type' : type,
                             'feature' : feature,
                             'data' : data}
                self.log.info(u"New instance feature detected and added in the new instances list : {0}".format(new_instance))
                self.new_instances.append(new_instance)

                # publish new instances update
                self._pub.send_event('instance.new',
                                     {"type" : "plugin",
                                      "name" : self._name,
                                      "host" : self.get_sanitized_hostname(),
                                      "client_id" : "plugin-{0}.{1}".format(self._name, self.get_sanitized_hostname()),
                                      "instances" : self.new_instances})

                # TODO : later (0.4.0+), publish one "new instance" notification with only the new instance detected

            else:
                self.log.debug(u"The instance has already been detected since the plugin startup")


    def get_parameter(self, a_instance, key):
        """ For a instance feature, return the required parameter value
            @param a_instance: the instance informations
            @param key: the parameter key
        """
        try:
            self.log.debug(u"Get parameter '{0}'".format(key))
            for a_param in a_instance['parameters']:
                if a_param == key:
                    value = self.cast(a_instance['parameters'][a_param]['value'], a_instance['parameters'][a_param]['type'])
                    self.log.debug(u"Parameter value found: {0}".format(value))
                    return value
            self.log.warning(u"Parameter not found : return None")
            return None
        except:
            self.log.error(u"Error while looking for a instance parameter. Return None. Error: {0}".format(traceback.format_exc()))
            return None
         

    def get_parameter_for_feature(self, a_instance, type, feature, key):
        """ For a instance feature, return the required parameter value
            @param a_instance: the instance informations
            @param type: the parameter type (xpl_stats, ...)
            @param feature: the parameter feature
            @param key: the parameter key
        """
        try:
            self.log.debug(u"Get parameter '{0}' for '{1}', feature '{2}'".format(key, type, feature))
            for a_param in a_instance[type][feature]['parameters']['static']:
                if a_param['key'] == key:
                    value = self.cast(a_param['value'], a_param['type'])
                    self.log.debug(u"Parameter value found: {0}".format(value))
                    return value
            self.log.warning(u"Parameter not found : return None")
            return None
        except:
            self.log.error(u"Error while looking for a instance feature parameter. Return None. Error: {0}".format(traceback.format_exc()))
            return None
         

    def check_for_pictures(self):
        """ if some products are defined, check if the corresponding pictures are present in the products/ folder
        """
        self.log.info(u"Check if there are pictures for the defined products")
        ok = True
        ok_product = None
        if self.json_data.has_key('products'):
            for product in self.json_data['products']:
                ok_product = False
                pdict = self.json_data['products'][product]
                for ext in PRODUCTS_PICTURES_EXTENSIONS:
                    file = "{0}.{1}".format(product, ext)
                    if os.path.isfile("{0}/{1}".format(self.get_products_directory(), file)):
                        ok_product = True
                        break
                if ok_product:
                    self.log.debug(u"- OK : {0} ({1})".format(pdict['name'], file))
                else:
                    ok = False
                    self.log.warning(u"- Missing : {0} ({1}.{2})".format(pdict['name'], product, PRODUCTS_PICTURES_EXTENSIONS))
        if ok == False:
            self.log.warning(u"Some pictures are missing!")
        else:
            if ok_product == None:
                self.log.info(u"There is no products defined for this plugin")


    def ready(self, ioloopstart=1):
        """ to call at the end of the __init__ of classes that inherits of this one
 
            In the XplPLugin class, this function will be completed to also activate the xpl hbeat
        """
        if self.dont_run_ready == True:
            return

        ### send plugin status : STATUS_ALIVE
        # TODO : why the dbmgr has no self._name defined ???????
        # temporary set as unknown to avoir blocking bugs
        if not hasattr(self, '_name'):
            self._name = "unknown"
        self._set_status(STATUS_ALIVE)

        ### Instantiate the MQ
        # nothing can be launched after this line (blocking call!!!!)
        self.log.info(u"Start IOLoop for MQ : nothing else can be executed in the __init__ after this! Make sure that the self.ready() call is the last line of your init!!!!")
        if ioloopstart == 1:
            IOLoop.instance().start()



    def on_mdp_request(self, msg):
        """ Handle Requests over MQ
            @param msg : MQ req message
        """
        self.log.debug(u"MQ Request received : {0}" . format(str(msg)))

        ### stop the plugin
        if msg.get_action() == "plugin.stop.do":
            self.log.info(u"Plugin stop request : {0}".format(msg))
            self._mdp_reply_plugin_stop(msg)
        elif msg.get_action() == "helper.list.get":
            self.log.info(u"Plugin helper list request : {0}".format(msg))
            self._mdp_reply_helper_list(msg)
        elif msg.get_action() == "helper.help.get":
            self.log.info(u"Plugin helper help request : {0}".format(msg))
            self._mdp_reply_helper_help(msg)
        elif msg.get_action() == "helper.do":
            self.log.info(u"Plugin helper action request : {0}".format(msg))
            self._mdp_reply_helper_do(msg)
        elif msg.get_action() == "instance.new.get":
            self.log.info(u"Plugin new instances request : {0}".format(msg))
            self._mdp_reply_instance_new_get(msg)
    
    def _mdp_reply_helper_do(self, msg):
        contens = msg.get_data()
        if 'command' in contens.keys():
            if contens['command'] in self.helpers.keys():
                if 'parameters' not in contens.keys():
                    contens['parameters'] = {}
                    params = []
                else:
                    params = []
                    for key, value in contens['parameters'].items():
                        params.append( "{0}='{1}'".format(key, value) )
                command = "self.{0}(".format(self.helpers[contens['command']]['call'])
                command += ", ".join(params)
                command += ")"
                result = eval(command)
                # run the command with all params
                msg = MQMessage()
                msg.set_action('helper.do.result')
                msg.add_data('command', contens['command'])
                msg.add_data('parameters', contens['parameters'])
                msg.add_data('result', result)
                self.reply(msg.get())

    def _mdp_reply_helper_help(self, data):
        content = data.get_data()
        if 'command' in contens.keys():
            if content['command'] in self.helpers.keys():
                msg = MQMessage()
                msg.set_action('helper.help.result')
                msg.add_data('help', self.helpers[content['command']]['help'])
                self.reply(msg.get())

    def _mdp_reply_plugin_stop(self, data):
        """ Stop the plugin
            @param data : MQ req message

            First, send the MQ Rep to 'ack' the request
            Then, change the plugin status to STATUS_STOP_REQUEST
            Then, quit the plugin by calling force_leave(). This should make the plugin send a STATUS_STOPPED if all is ok

            Notice that no check is done on the MQ req content : we need nothing in it as it is directly addressed to a plugin
        """
        # check if the message is for us
        content = data.get_data()
        if content['name'] != self._name or content['host'] != self.get_sanitized_hostname():
            return

        ### Send the ack over MQ Rep
        msg = MQMessage()
        msg.set_action('plugin.stop.result')
        status = True
        reason = ""
        msg.add_data('status', status)
        msg.add_data('reason', reason)
        self.reply(msg.get())

        ### Change the plugin status
        self._set_status(STATUS_STOP_REQUEST)

        ### Try to stop the plugin
        # if it fails, the manager should try to kill the plugin
        self.force_leave()

    def _mdp_reply_helper_list(self, data):
        """ Return a list of supported helpers
            @param data : MQ req message
        """
        ### Send the ack over MQ Rep
        msg = MQMessage()
        msg.set_action('helper.list.result')
        msg.add_data('actions', self.helpers.keys())
        self.reply(msg.get())

    def _mdp_reply_instance_new_get(self, data):
        """ Return a list of new instances detected
            @param data : MQ req message
        """
        ### Send the ack over MQ Rep
        msg = MQMessage()
        msg.set_action('instance.new.result')
        msg.add_data('instances', self.new_instances)
        self.reply(msg.get())


    def _set_status(self, status):
        """ Set the plugin status and send it
        """
        # when ctrl-c is done, there is no more self._name at this point...
        # why ? because the force_leave method is called twice as show in the logs : 
        #
        # ^CKeyBoardInterrupt
        # 2013-12-20 22:48:41,040 domogik-manager INFO Keyoard Interrupt detected, leave now.
        # Traceback (most recent call last):
        #   File "./manager.py", line 1176, in <module>
        #     main()
        #   File "./manager.py", line 1173, in main
        # 2013-12-20 22:48:41,041 domogik-manager DEBUG force_leave called
        # 2013-12-20 22:48:41,044 domogik-manager DEBUG __del__ Single xpl plugin
        # 2013-12-20 22:48:41,045 domogik-manager DEBUG force_leave called

        if hasattr(self, '_name'):
            if self._name not in CORE_COMPONENTS:
                self._status = status
                self._send_status()

    def _send_status_loop(self):
        """ send the status each STATUS_HBEAT seconds
        """
        # TODO : we could optimize by resetting the timer each time the status is sent
        # but as this is used only to check for dead plugins by the manager, it is not very important ;)
        while not self._stop.isSet():
            self._send_status()
            self._stop.wait(STATUS_HBEAT)

    def _send_status(self):
        """ Send the plugin status over the MQ
        """ 
        if hasattr(self, "_pub"):
            if self._name in CORE_COMPONENTS:
                #type = "core"
                return
            else:
                type = "plugin"
            self.log.debug("Send plugin status : {0}".format(self._status))
            self._pub.send_event('plugin.status', 
                                 {"type" : type,
                                  "name" : self._name,
                                  "host" : self.get_sanitized_hostname(),
                                  "event" : self._status})

    def get_config_files(self):
       """ Return list of config files
       """
       return self._config_files

    def get_products_directory(self):
       """ getter 
       """
       return self.products_directory

    def get_libraries_directory(self):
       """ getter 
       """
       return self.libraries_directory

    def get_packages_directory(self):
       """ getter 
       """
       return self.packages_directory

    def get_resources_directory(self):
       """ getter 
       """
       return self.resources_directory

    def get_data_files_directory(self):
       """
       Return the directory where a plugin developper can store data files.
       If the directory doesn't exist, try to create it.
       After that, try to create a file inside it.
       If something goes wrong, generate an explicit exception.
       """
       path = "{0}/{1}/{2}_{3}/data/" % (self.librairies_directory, PACKAGES_DIR, "plugin", self._name)
       if os.path.exists(path):
           if not os.access(path, os.W_OK & os.X_OK):
               raise OSError("Can't write in directory %s" % path)
       else:
           try:
               os.mkdir(path, '0770')
               self.log.info(u"Create directory %s." % path)
           except:
               raise OSError("Can't create directory %s." % path)
       try:
           tmp_prefix = "write_test";
           count = 0
           filename = os.path.join(path, tmp_prefix)
           while(os.path.exists(filename)):
               filename = "{}.{}".format(os.path.join(path, tmp_prefix),count)
               count = count + 1
           f = open(filename,"w")
           f.close()
           os.remove(filename)
       except :
           raise IOError("Can't create a file in directory %s." % path)
       return path

    def register_helper(self, action, help_string, callback):
        if action not in self.helpers:
            self.helpers[action] = {'call': callback, 'help': help_string}

    def publish_helper(self, key, data):
        if hasattr(self, "_pub"):
            if self._name in CORE_COMPONENTS:
                type = "core"
            else:
                type = "plugin"
            self._pub.send_event('helper.publish',
                                 {"origin" : self._mq_name,
                                  "key": key,
                                  "data": data})

    def _get_pid(self):
        """ Get current pid and write it to a file
        """
        pid = os.getpid()
        pid_file = os.path.join(self._pid_dir_path,
                                self._name + ".pid")
        self.log.debug(u"Write pid file for pid '%s' in file '%s'" % (str(pid), pid_file))
        fil = open(pid_file, "w")
        fil.write(str(pid))
        fil.close()

    def __del__(self):
        if hasattr(self, "log"):
            self.log.debug(u"__del__ Single plugin")
            # we guess that if no "log" is defined, the plugin has not really started, so there is no need to call force leave (and _stop, .... won't be created)
            self.force_leave()

    def force_leave(self, status = False, return_code = None):
        """ Leave threads & timers

            In the XplPLugin class, this function will be completed to also activate the xpl hbeat
        """
        if return_code != None:
            self.set_return_code(return_code)
            self.log.info("Return code set to {0} when calling force_leave()".format(return_code))


        # avoid ready() to be launched
        self.dont_run_ready = True
        # stop IOLoop
        #try:
        #    IOLoop.instance().start()
        #except:
        #    pass
        if hasattr(self, "log"):
            self.log.debug(u"force_leave called")
        # send stopped status over the MQ
        if status:
            self._set_status(status)
        else:
            self._set_status(STATUS_STOPPED)

        # try to stop the thread
        try:
            self.get_stop().set()
        except AttributeError:
            pass

        if hasattr(self, "_timers"):
            for t in self._timers:
                if hasattr(self, "log"):
                    self.log.debug(u"Try to stop timer %s"  % t)
                t.stop()
                if hasattr(self, "log"):
                    self.log.debug(u"Timer stopped %s" % t)

        if hasattr(self, "_stop_cb"):
            for cb in self._stop_cb:
                if hasattr(self, "log"):
                    self.log.debug(u"Calling stop additionnal method : %s " % cb.__name__)
                cb()
    
        if hasattr(self, "_threads"):
            for t in self._threads:
                if hasattr(self, "log"):
                    self.log.debug(u"Try to stop thread %s" % t)
                try:
                    t.join()
                except RuntimeError:
                    pass
                if hasattr(self, "log"):
                    self.log.debug(u"Thread stopped %s" % t)
                #t._Thread__stop()

        #Finally, we try to delete all remaining threads
        for t in threading.enumerate():
            if t != threading.current_thread() and t.__class__ != threading._MainThread:
                if hasattr(self, "log"):
                    self.log.info(u"The thread %s was not registered, killing it" % t.name)
                t.join()
                if hasattr(self, "log"):
                    self.log.info(u"Thread %s stopped." % t.name)

        if threading.activeCount() > 1:
            if hasattr(self, "log"):
                self.log.warn(u"There are more than 1 thread remaining : %s" % threading.enumerate())


class Watcher:
    """this class solves two problems with multithreaded
    programs in Python, (1) a signal might be delivered
    to any thread (which is just a malfeature) and (2) if
    the thread that gets the signal is waiting, the signal
    is ignored (which is a bug).

    The watcher is a concurrent process (not thread) that
    waits for a signal and the process that contains the
    threads.  See Appendix A of The Little Book of Semaphores.
    http://greenteapress.com/semaphores/

    I have only tested this on Linux.  I would expect it to
    work on the Macintosh and not work on Windows.
    Tip found at http://code.activestate.com/recipes/496735/
    """

    def __init__(self, plugin):
        """ Creates a child thread, which returns.  The parent
            thread waits for a KeyboardInterrupt and then kills
            the child thread.
        """
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self._plugin = plugin
            self._plugin.log.debug("watcher fork")
            signal.signal(signal.SIGTERM, self._signal_handler)
            self.watch()

    def _signal_handler(self, signum, frame):
        """ Handler called when a SIGTERM is received
        Stop the plugin
        """
        self._plugin.log.info("SIGTERM receive, stop plugin")
        self._plugin.force_leave()
        self.kill()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            print('KeyBoardInterrupt')
            self._plugin.log.info("Keyoard Interrupt detected, leave now.")
            self._plugin.force_leave()
            self.kill()
        except OSError:
            print(u"OSError")
        return_code = self._plugin.get_return_code()
        self._plugin.clean_return_code_file()
        sys.exit(return_code)

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError: pass

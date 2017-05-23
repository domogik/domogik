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
=============

- REST support for Domogik project

Implements
==========

class Admin(Plugin)
class AdminWebSocket(WebSocketHandler, MQAsyncSub)

@author: 	Friz <fritz.smh@gmail.com>
		Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.common.jsondata import domogik_encoder
from domogik.xpl.common.plugin import DMG_VENDOR_ID
from domogik.common.database import DbHelper, DbHelperException
from domogik.common.plugin import Plugin
#from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.common.utils import get_ip_for_interfaces, build_deviceType_from_packageJson
from domogikmq.pubsub.subscriber import MQAsyncSub
from domogikmq.pubsub.publisher import MQPub
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
import locale
import traceback
import zmq
#import signal
import time
import json
import subprocess
#import datetime
#import random
#import uuid
#from threading import Thread       #, Lock
from tornado import gen
from tornado.queues import Queue
from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop                        #, PeriodicCallback 
from tornado.httpserver import HTTPServer
from tornado.web import FallbackHandler, Application
from tornado.websocket import WebSocketHandler, WebSocketClosedError
from distutils.spawn import find_executable
import re
import os

zmq.eventloop.ioloop.install()

DATABASE_CONNECTION_NUM_TRY = 50
DATABASE_CONNECTION_WAIT = 30
REST_API_VERSION = "0.9"

################################################################################


class MQManager(MQAsyncSub):
    """Handles new data to be passed on to subscribers."""
    def __init__(self):
        self.ctx = zmq.Context()
        self.ToWSmessages = Queue()
        self.ToMQmessages = Queue()
        self.sub = MQAsyncSub.__init__(self, self.ctx, 'admin', [])
        self.pub = MQPub(self.ctx, 'admin-ws')
        self.subscribers = set()

    def register(self, subscriber):
        """Register a new subscriber."""
        self.subscribers.add(subscriber)

    def deregister(self, subscriber):
        """Stop publishing to a subscriber."""
        try:
            self.subscribers.remove(subscriber)
        except:
            pass

    @gen.coroutine
    def on_message(self, did, msg):
        """Receive message from MQ sub """
        msg2 = str(msg)
        #print(u"MQManager => on_message({0}, {1})".format(did, msg2[0:50]))

        # For now, all messages from MQ should be sent to the browsers
        yield self.ToWSmessages.put({"msgid": did, "content": msg})

    @gen.coroutine
    def publishToWS(self):
        while True:
            message = yield self.ToWSmessages.get()
            if len(self.subscribers) > 0:
                #print(u"Pushing MQ message to {} WS subscribers...".format(len(self.subscribers)))
                yield [subscriber.submit(message) for subscriber in self.subscribers]

    @gen.coroutine
    def publishToMQ(self):
        while True:
            message = yield self.ToMQmessages.get()
            self.sendToMQ(message)
    
    def sendToMQ(self, message):
        try:
            ctx = zmq.Context()
            jsons = json.loads(message)
            # req/rep
            if 'mq_request' in jsons and 'data' in jsons:
                #print(u"MQ REQ !")
                cli = MQSyncReq(ctx)
                msg = MQMessage()
                msg.set_action(str(jsons['mq_request']))
                msg.set_data(jsons['data'])
                #print(u"REQ : {0}".format(msg.get()))
                if 'dst' in jsons:
                    dst = str(jsons['dst'])
                else:
                    dst = 'manager'
                res = cli.request(dst, msg.get(), timeout=10)
                if res:
                    print(res.get())
                cli.shutdown()
                del cli
            # pub
            elif 'mq_publish' in jsons and 'data' in jsons:
                #print(u"MQ pub !")
                self.pub.send_event(jsons['mq_publish'],
                                jsons['data'])
        except Exception as e:
            print(u"Error sending mq message: {0}".format(e))

class WebSocketManager(WebSocketHandler):
    """Websocket for subscribers."""
    def check_origin(self, origin):
        return True

    def initialize(self, publisher):
        self.publisher = publisher
        self.messages = Queue()
        self.finished = False

    def open(self):
        #print(u"WebSocketManager > open()")
        self.publisher.register(self)
        self.run()

    def on_close(self):
        #print(u"WebSocketManager > on_close()")
        self._close()        

    def _close(self):
        #print("Subscriber left.")
        self.publisher.deregister(self)
        self.finished = True

    @gen.coroutine
    def submit(self, message):
        yield self.messages.put(message)

    @gen.coroutine
    def run(self):
        """ Empty the queue of messages to send to the WS """
        while not self.finished:
            message = yield self.messages.get()
            self.send(message)

    def send(self, message):
        try:
            self.write_message(message)
        except WebSocketClosedError:
            self._close()
    
    def on_message(self, content):
        """ receive message from websocket """
        #print(u"WebSocketManager => on_message({0})".format(content))

        try:
            # samples :
            # request to start a plugin from admin :
            #    {"mq_request": "plugin.start.do", "data": {"type" : "plugin", "name": "diskfree", "host": "darkstar"}}
            # test from a dev page :
            #    {"message": "ping from browser (Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36))"}
            json_data = json.loads(content)
    
            ### Process the simple messages
            if "message" in json_data:
                #print(u"=> message")
    
                message = json_data["message"]
                #print(message)
                if message.startswith("ping from browser"):
                    browser_info = re.sub("ping from browser", "", message)
                    self.send(json.dumps({"message" : "pong from admin {0}".format(browser_info)}))
                    return
    
            ### Process the MQ related messages
            elif "mq_request" in json_data:
                #print(u"=> MQ req")
                self.publisher.ToMQmessages.put(content)
    
            elif "mq_publish" in json_data:
                #print(u"=> MQ pub")
                self.publisher.ToMQmessages.put(content)
    
        except:
            print(u"Error while processing input websocket message. Message is : '{0}'. Error is : {1}".format(content, traceback.format_exc()))

class Admin(Plugin):
    """ Admin Server 
        - create a HTTP server 
        - handle the admin interface urls
    """

    def __init__(self, server_interfaces, server_port):
        """ Initiate DbHelper, Logs and config
            
            Then, start HTTP server and give it initialized data
            @param server_interfaces :  interfaces of HTTP server
            @param server_port :  port of HTTP server
        """

        Plugin.__init__(self, name = 'admin', log_prefix='core_')
        self.log.debug(u"Init database_manager instance")
        # Check for database connexion
        self._db = DbHelper()

        # logging initialization
        self.log.info(u"Admin Server initialisation...")
        self.log.debug(u"locale : {0}".format(locale.getdefaultlocale()))
        try:
            try:
                # admin config
                cfg_admin = Loader('admin')
                config_admin = cfg_admin.load()
                conf_global = dict(config_admin[0])
                self.log_level = conf_global['log_level']
                self.log_folder = conf_global['log_dir_path']
                self.http_log_file = os.path.join(self.log_folder, "core_admin_http.log")
                conf_admin = dict(config_admin[1])
                self.interfaces = conf_admin['interfaces']
                self.port = conf_admin['port']
                self.http_workers = conf_admin['http_workers_number']
                self.ws_port = conf_admin['ws_port']
                # if use_ssl = True, set here path for ssl certificate/key
                self.use_ssl = conf_admin['use_ssl']
                if self.use_ssl.strip() == "True":
                    self.use_ssl = True
                self.key_file = conf_admin['ssl_key']
                self.cert_file = conf_admin['ssl_certificate']
                self.secret_key = conf_admin['secret_key']
                if 'clean_json' in conf_admin:
                    self.clean_json = conf_admin['clean_json']
                else:
                    self.clean_json = False
                if 'rest_auth' in conf_admin and conf_admin['rest_auth'] == 'True':
                    self.rest_auth = True
                else:
                    self.rest_auth = False
            except KeyError:
                # default parameters
                self.interfaces = server_interfaces
                self.port = server_port
                self.use_ssl = False
                self.key_file = ""
                self.cert_file = ""
                self.clean_json = False
                self.log.error("Error while reading configuration for section [admin] : using default values instead. The error is : {0}".format(traceback.format_exc()))
            self.log.info(u"Configuration : interfaces:port = {0}:{1}".format(self.interfaces, self.port))
            self.log.info(u"Configuration : use_ssl = {0}".format(self.use_ssl))
	    
	    # get all datatypes
            cli = MQSyncReq(self.zmq)
            msg = MQMessage()
            msg.set_action('datatype.get')
            res = cli.request('manager', msg.get(), timeout=10)
            if res is not None:
                self.datatypes = res.get_data()['datatypes']
            else:
                self.datatypes = {}

 	    # Launch server, stats
            self.log.info(u"Admin Initialisation OK")
            self.add_stop_cb(self.stop_http)
            self.server = None
            self._start_http_ws()
	    self._start_http_admin()
            # calls the tornado.ioloop.instance().start()
            
            ### Component is ready
            self.ready(0)
            IOLoop.instance().start()
        except :
            self.log.error(u"{0}".format(self.get_exception()))

    @gen.coroutine
    def _start_http_ws(self):
        """ Start HTTP Server
        """
        self.log.info(u"Start WS Server on {0}:{1}...".format(self.interfaces, self.ws_port))
        
        publisher = MQManager()
        tapp = Application([
            (r"/ws", WebSocketManager, dict(publisher=publisher))
            ])

	# create the server
        # for ssl, extra parameter to HTTPServier init
        if self.use_ssl is True:
            ssl_options = {
                 "certfile": self.cert_file,
                 "keyfile": self.key_file,
            }
            self.http_server = HTTPServer(tapp, ssl_options=ssl_options)
        else:
            self.http_server = HTTPServer(tapp)
	# listen on the interfaces
        if self.interfaces != "":
            # value can be : lo, eth0, ...
            # or also : '*' to catch all interfaces, whatever they are
            intf = self.interfaces.split(',')
            self.log.info("The admin will be available on the below addresses : ")
            num_int = 0
            for ip in get_ip_for_interfaces(intf, log = self.log):
                self.log.info(" - {0}:{1} [BIND]".format(ip, self.ws_port))
                self.http_server.listen(int(self.ws_port), address=ip)
                num_int += 1
            if num_int == 0:
                self.log.error("The admin is not configured to use any working network interface! Please check configuration!!!!!!")
        else:
            self.http_server.bind(int(self.ws_port))
            self.http_server.start(0)
        yield [publisher.publishToMQ(), publisher.publishToWS()]

    def stop_http(self):
        """ Stop HTTP Server
        """
        self.log.info('Stopping http server')
        try:
            self.http_server.stop()
        except:
            # in case of error while stopping the http server (maybe the startup was not fine so the http server does not exists), we don't raise an error to allow continuing to stop
            pass
 
        self.log.info('Will shutdown in 10 seconds ...' )
        io_loop = IOLoop.instance()
        deadline = time.time() + 10
 
        def stop_loop():
            now = time.time()
            if now < deadline and (io_loop._callbacks or io_loop._timeouts):
                io_loop.add_timeout(now + 1, stop_loop)
            else:
                io_loop.stop()
                logging.info('Shutdown')
        stop_loop()
        return

    def _start_http_admin(self):
        self.log.info(u"HTTP Server initialisation...")
        acfg = dict(Loader('admin').load()[1])
        cmd = "{0} --preload --access-logfile {1} --error-logfile {1} --log-level {2}".format(find_executable("gunicorn"), self.http_log_file, self.log_level)

        # SSL handling
        if acfg['use_ssl'] == "True":
            cmd = "{0} --certfile {1} --keyfile {2}".format(cmd, acfg['ssl_certificate'], acfg['ssl_key'])

        # Listening interfaces and port
        for dev in get_ip_for_interfaces(acfg['interfaces'].split(',')):
            cmd = "{0} -b {1}:{2}".format(cmd, dev, acfg['port'])

        # Number of workers + threads
        cmd = "{0} -w {1}".format(cmd, self.http_workers)

        # Append the application to start
        cmd = "{0} domogik.admin.application:app".format(cmd)

        # Start the subprocess
        self.log.info(u"Starting webserver as: {0}".format(cmd))
        self._http = subprocess.Popen(cmd, shell=True)
        self.log.info(u"HTTP Server initialisation: Finished")

    def get_exception(self):
        """ Get exception and display it on stdout
        """
        my_exception =  str(traceback.format_exc()).replace('"', "'")
        return my_exception

    def on_mdp_request(self, msg):
        """ Handle Requests over MQ
            @param msg : MQ req message
        """
        try:
            with self._db.session_scope():
                # Plugin handles MQ Req/rep also
                Plugin.on_mdp_request(self, msg)

                # configuration
                if msg.get_action() == "config.get":
                    self._mdp_reply_config_get(msg)
                elif msg.get_action() == "config.set":
                    self._mdp_reply_config_set(msg)
                elif msg.get_action() == "config.delete":
                    self._mdp_reply_config_delete(msg)
                # devices list
                elif msg.get_action() == "device.get":
                    self._mdp_reply_devices_result(msg)
                # device get params
                elif msg.get_action() == "device.params":
                    self._mdp_reply_devices_params_result(msg)
                # device create
                elif msg.get_action() == "device.create":
                    self._mdp_reply_devices_create_result(msg)
                # device delete
                elif msg.get_action() == "device.delete":
                    self._mdp_reply_devices_delete_result(msg)
                # device update
                elif msg.get_action() == "device.update":
                    self._mdp_reply_devices_update_result(msg)
                # deviceparam update
                elif msg.get_action() == "deviceparam.update":
                    self._mdp_reply_deviceparam_update_result(msg)
                # sensor update
                elif msg.get_action() == "sensor.update":
                    self._mdp_reply_sensor_update_result(msg)
                # sensor history
                elif msg.get_action() == "sensor_history.get":
                    self._mdp_reply_sensor_history(msg)
                # person
                elif msg.get_action() == "person.get":
                    self._mdp_reply_person_get(msg)
        except:
            msg = "Error while processing request. Message is : {0}. Error is : {1}".format(msg, traceback.format_exc())
            self.log.error(msg)

    def _mdp_reply_config_get(self, data):
        """ Reply to config.get MQ req
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('config.result')
        status = True
        msg_data = data.get_data()
        if 'type' not in msg_data:
            status = False
            reason = "Config request : missing 'type' field : {0}".format(data)

        if msg_data['type'] not in ["plugin", "brain", "interface"]:
            status = False
            reason = "Configuration request not available for type={0}".format(msg_data['type'])

        if 'name' not in msg_data:
            status = False
            reason = "Config request : missing 'name' field : {0}".format(data)

        if 'host' not in msg_data:
            status = False
            reason = "Config request : missing 'host' field : {0}".format(data)

        if 'key' not in msg_data:
            get_all_keys = True
            key = "*"
        else:
            get_all_keys = False
            key = msg_data['key']

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            name = msg_data['name']
            host = msg_data['host']
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            msg.add_data('key', key)  # we let this here to display key or * depending on the case
            try:
                if get_all_keys == True:
                    config = self._db.list_plugin_config(type, name, host)
                    self.log.info(u"Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, config))
                    json_config = {}
                    for elt in config:
                        json_config[elt.key] = self.convert(elt.value)
                    msg.add_data('data', json_config)
                else:
                    value = self._fetch_techno_config(name, type, host, key)
                    # temporary fix : should be done in a better way (on db side)
                    value = self.convert(value)
                    self.log.info(u"Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, value))
                    msg.add_data('value', value)
            except:
                status = False
                reason = "Error while getting configuration for '{0} {1} on {2}, key {3}' : {4}".format(type, name, host, key, traceback.format_exc())
                self.log.error(reason)

        msg.add_data('reason', reason)
        msg.add_data('status', status)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _mdp_reply_config_set(self, data):
        """ Reply to config.set MQ req
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('config.result')
        status = True
        msg_data = data.get_data()
        if 'type' not in msg_data:
            status = False
            reason = "Config set : missing 'type' field : {0}".format(data)

        if msg_data['type'] not in ["plugin", "brain", "interface"]:
            status = False
            reason = "You are not able to configure items for type={0}".format(msg_data['type'])

        if 'name' not in msg_data:
            status = False
            reason = "Config set : missing 'name' field : {0}".format(data)

        if 'host' not in msg_data:
            status = False
            reason = "Config set : missing 'host' field : {0}".format(data)

        if 'data' not in msg_data:
            status = False
            reason = "Config set : missing 'data' field : {0}".format(data)

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            name = msg_data['name']
            host = msg_data['host']
            data = msg_data['data']
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            try: 
                # we add a configured key set to true to tell the UIs and plugins that there are some configuration elements
                self._db.set_plugin_config(type, name, host, "configured", True)
                for key in msg_data['data']:
                    self._db.set_plugin_config(type, name, host, key, data[key])
                self.publish_config_updated(type, name, host)
            except:
                reason = "Error while setting configuration for '{0} {1} on {2}' : {3}".format(type, name, host, traceback.format_exc())
                status = False
                self.log.error(reason)

        msg.add_data('status', status)
        msg.add_data('reason', reason)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _mdp_reply_config_delete(self, data):
        """ Reply to config.delete MQ req
            Delete all the config items for the given type, name and host
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('config.result')
        status = True
        msg_data = data.get_data()
        if 'type' not in msg_data:
            status = False
            reason = "Config request : missing 'type' field : {0}".format(data)

        if msg_data['type'] not in ["plugin", "brain", "interface"]:
            status = False
            reason = "Configuration deletion not available for type={0}".format(msg_data['type'])

        if 'name' not in msg_data:
            status = False
            reason = "Config request : missing 'name' field : {0}".format(data)

        if 'host' not in msg_data:
            status = False
            reason = "Config request : missing 'host' field : {0}".format(data)

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            name = msg_data['name']
            host = msg_data['host']
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            try:
                self._db.del_plugin_config(type, name, host)
                self.log.info(u"Delete config for {0} {1}".format(type, name))
                self.publish_config_updated(type, name, host)
            except:
                status = False
                reason = "Error while deleting configuration for '{0} {1} on {2} : {3}".format(type, name, host, traceback.format_exc())
                self.log.error(reason)

        msg.add_data('reason', reason)
        msg.add_data('status', status)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _fetch_techno_config(self, name, type, host, key):
        '''
        Fetch a plugin global config value in the database
        @param name : the plugin of the element
        @param host : hostname
        @param key : the key of the config tuple to fetch
        '''
        try:
            try:
                result = self._db.get_plugin_config(type, name, host, key)
                # tricky loop as workaround for a (sqlalchemy?) bug :
                # sometimes the given result is for another plugin/key
                # so while we don't get the good data, we loop
                # This bug happens rarely
                while result.id != name or \
                   result.type != type or \
                   result.hostname != host or \
                   result.key != key:
                    self.log.debug(u"Bad result : {0}-{1}/{2} != {3}/{4}".format(result.id, result.type, result.key, plugin, key))
                    result = self._db.get_plugin_config(type, name, host, key)
                val = result.value
                if val == '':
                    val = "None"
                return val
            except AttributeError:
                # if no result is found
                #self.log.error(u"Attribute error : {0}".format(traceback.format_exc()))
                return "None"
        except:
            msg = "No config found host={0}, plugin={1}, key={2}".format(host, name, key)
            self.log.warn(msg)
            return "None"

    def _mdp_reply_devices_delete_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Deleting device : {0}".format(data))
        try:
            did = data.get_data()['did']
            if did:
                res = self._db.del_device(did)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such device"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while deleting device: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while deleting device: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('device.delete.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            self._pub.send_event('device.update',
                     {"device_id" : did,
                      "client_id" : res.client_id})

    def _mdp_reply_sensor_update_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Updating sensor : {0}".format(data))
        try:
            data = data.get_data()
            if 'sid' in data:
                sid = data['sid']
                if 'history_round' not in data:
                    hround = None
                else:
                    hround = data['history_round']
                if 'history_store' not in data:
                    hstore = None
                else:
                    hstore = data['history_store']
                if 'history_max' not in data:
                    hmax = None
                else:
                    hmax = data['history_max']
                if 'history_expire' not in data:
                    hexpire = None
                else:
                    hexpire = data['history_expire']
                if 'timeout' not in data:
                    timeout = None
                else:
                    timeout = data['timeout']
                if 'formula' not in data:
                    formula = None
                else:
                    formula = data['formula']
                if 'data_type' not in data:
                    data_type = None
                else:
                    data_type = data['data_type']
                # do the update
                res = self._db.update_sensor(sid, \
                     history_round=hround, \
                     history_store=hstore, \
                     history_max=hmax, \
                     history_expire=hexpire, \
                     timeout=timeout, \
                     formula=formula, \
                     data_type=data_type)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such sensor"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while updating sensor: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while updating sensor: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('sensor.update.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            dev = self._db.get_device(res.device_id)
            self._pub.send_event('device.update',
                     {"device_id" : res.device_id,
                      "client_id" : dev['client_id']})

    def _mdp_reply_deviceparam_update_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Updating device param : {0}".format(data))
        try:
            data = data.get_data()
            if 'dpid' in data:
                dpid = data['dpid']
                val = data['value']
                # do the update
                res = self._db.udpate_device_param(dpid, value=val)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such device param"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while updating device param: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while updating device param: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('deviceparam.update.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            dev = self._db.get_device(res.device_id)
            self._pub.send_event('device.update',
                    {"device_id" : res.device_id,
                     "client_id" : dev['client_id']})

    def _mdp_reply_devices_update_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Updating device : {0}".format(data))
        try:
            data = data.get_data()
            if 'did' in data:
                did = data['did']
                if 'name' not in data:
                    name = None
                else:
                    name = data['name']
                if 'reference' not in data:
                    ref = None
                else:
                    ref = data['reference']
                if 'description' not in data:
                    desc = None
                else:
                    desc = data['description']
                # do the update
                res = self._db.update_device(did, \
                    d_name=name, \
                    d_description=desc, \
                    d_reference=ref)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such device"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while updating device: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while updating device: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('device.update.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            self._pub.send_event('device.update',
                     {"device_id" : res.id,
                      "client_id" : res.client_id})

    def _mdp_reply_devices_create_result(self, data):
        status = True
        reason = False
        result = False
        # get the filled package json
        params = data.get_data()['data']
        # get the json
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('device_types.get')
        msg.add_data('device_type', params['device_type'])
        res = cli.request('manager', msg.get(), timeout=10)
        del cli
        if res is None:
            status = False
            reason = "Manager is not replying to the mq request" 
        pjson = res.get_data()
        if pjson is None:
            status = False
            reason = "No data for {0} found by manager".format(params['device_type']) 
        pjson = pjson[params['device_type']]
        if pjson is None:
            status = False
            reason = "The json for {0} found by manager is empty".format(params['device_type']) 

        if status:
            # call the add device function
            res = self._db.add_full_device(params, pjson)
            if not res:
                status = False
                reason = "An error occured while adding the device in database. Please check the file admin.log for more informations"
            else:
                status = True
                reason = False
                result = res

        msg = MQMessage()
        msg.set_action('device.create.result')
        if reason:
            msg.add_data('reason', reason)
        if result:
            msg.add_data('result', result)
        msg.add_data('status', status)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            self._pub.send_event('device.update',
                     {"device_id" : res['id'],
                      "client_id" : res['client_id']})

    def _mdp_reply_devices_params_result(self, data):
        """
            Reply to device.params mq req
            @param data : MQ req message
                => should contain
                    - device_type
        """
        status = True

        try:
            # check we have all the needed info
            msg_data = data.get_data()
            if 'device_type' not in msg_data:
                status = False
                reason = "Device params request : missing 'cevice_type' field : {0}".format(data)
            else:
                dev_type_id = msg_data['device_type']
    
            # check the received info
            (result, reason, status) = build_deviceType_from_packageJson(self.zmq, dev_type_id)
            msg = MQMessage()
            msg.set_action('device.params.result')
            if not status:
                # we don't have all info so exit
                msg = MQMessage()
                msg.set_action('device.params.result')
                msg.add_data('result', 'Failed')
                msg.add_data('reason', reason)
                self.log.debug(msg.get())
                self.reply(msg.get())
            else:
                # return the data
                msg.add_data('result', result)
            self.log.debug(msg.get())
            self.reply(msg.get())
        except:
            self.log.error("Error when replying to device.params for data={0}. Error: {1}".format(data, traceback.format_exc()))

    def _mdp_reply_devices_result(self, data):
        """ Reply to device.get MQ req
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('device.result')
        status = True

        msg_data = data.get_data()

        # request for all devices
        if 'type' not in msg_data and \
           'name' not in msg_data and \
           'host' not in msg_data:

            reason = ""
            status = True
            dev_list = self._db.list_devices()

            dev_json = dev_list
            msg.add_data('status', status)
            msg.add_data('reason', reason)
            msg.add_data('devices', dev_json)

        # request for all devices of one client
        else:
            if 'type' not in msg_data:
                status = False
                reason = "Devices request : missing 'type' field : {0}".format(data)

            if 'name' not in msg_data:
                status = False
                reason = "Devices request : missing 'name' field : {0}".format(data)

            if 'host' not in msg_data:
                status = False
                reason = "Devices request : missing 'host' field : {0}".format(data)

            if status == False:
                self.log.error(reason)
            else:
                reason = ""
                type = msg_data['type']
                name = msg_data['name']
                host = msg_data['host']
                dev_list = self._db.list_devices_by_plugin("{0}-{1}.{2}".format(type, name, host))

            #dev_json = json.dumps(dev_list, cls=domogik_encoder(), check_circular=False),
            dev_json = dev_list
            msg.add_data('status', status)
            msg.add_data('reason', reason)
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            msg.add_data('devices', dev_json)

        self.reply(msg.get())

    def _mdp_reply_sensor_history(self, data):
        """ Reply to sensor_history.get MQ req
            @param data : MQ req message

            If no other param than the sensor id, return the last value
        """
        msg = MQMessage()
        msg.set_action('sensor_history.result')
        status = True
        reason = ""

        ### process parameters
        msg_data = data.get_data()
        if 'sensor_id' in msg_data:
            sensor_id = msg_data['sensor_id']
        else:
            reason = "ERROR when getting sensor history. No sensor_id declared in the message"
            self.log.error(reason)
            status = False
            sensor_id = None
        if 'mode' in msg_data:
            if msg_data['mode'] == "last":
                mode = "last"
            elif msg_data['mode'] == "period":
                mode = "period"
            else:
                reason = "ERROR when getting sensor history. No valid type (last, from) declared in the message"
                self.log.error(reason)
                status = False
                mode = None
        else:
            reason = "ERROR when getting sensor history. No type (last, from) declared in the message"
            self.log.error(reason)
            status = False
            sensor_id = None

        values = None

        ### last N values
        if mode == "last":
            if 'number' in msg_data:
                number = msg_data['number']
            else:
                number = 1

            try:
                history = self._db.list_sensor_history(sensor_id, number)
                if len(history) == 0:
                    values = self._db.get_last_sensor_value(sensor_id)
                else: 
                    values = self._db.list_sensor_history(sensor_id, number)
            except:
                self.log.error("ERROR when getting sensor history for id = {0} : {1}".format(sensor_id, traceback.format_exc()))
                reason = "ERROR : {0}".format(traceback.format_exc())
                status = False

        ### period
        elif mode == "period":
            if 'from' in msg_data:
                frm = msg_data['from']
            else:
                reason = "ERROR when getting sensor history. No key 'from' defined for mode = 'period'!"
                self.log.error(reason)
                status = False
                frm = None

            if 'to' in msg_data:
                to = msg_data['to']
            else:
                to = None

            if frm != None and to == None:
                values = self._db.list_sensor_history_between(sensor_id, frm)
                print(values)

            else:
                # TODO
                values = "TODO"
        

        msg.add_data('status', status)
        msg.add_data('reason', reason)
        msg.add_data('sensor_id', sensor_id)
        msg.add_data('mode', mode)
        msg.add_data('values', values)

        self.reply(msg.get())

    def _mdp_reply_person_get(self, data):
        status = True
        reason = False
        res = None

        self.log.debug(u"Get the person list : {0}".format(data))
        try:
            res = self._db.list_persons()
            print(res)
            if not res:
                status = False
            else:
                status = True
        except DbHelperException as d:
            status = False
            reason = "Error while getting the persons list : {0}".format(traceback.format_exc())
            self.log.error(reason)
        except:
            status = False
            reason = "Error while deleting device: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('person.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        if res:
            persons = []
            for per in res:
                # print(per)
                # <Person: first_name='Stephanie', last_name='LR', location_sensor='663', birthdate='1977-09-19', id='5'> 
                birthdate_ts = None
                if per.birthdate:
                    birthdate_ts = time.mktime(per.birthdate.timetuple())
                persons.append({'first_name' : per.first_name, 
                                'last_name' : per.last_name,
                                'location_sensor' : per.location_sensor,
                                'birthdate' : birthdate_ts,
                                'id' : per.id})
            msg.add_data('persons', persons)
        self.log.debug(msg.get())
        self.reply(msg.get())


    def convert(self, data):
        """ Do some conversions on data
        """
        if data == "True":
            data = True
        if data == "False":
            data = False
        return data

    def publish_config_updated(self, type, name, host):
        """ Publish over the MQ a message to inform that a plugin configuration has been updated
            @param type : package type (plugin)
            @param name : package name
            @param host : host
        """
        self.log.debug("Publish configuration update notification for {0}-{1}.{2}".format(type, name, host))
        self._pub.send_event('plugin.configuration',
                             {"type" : type,
                              "name" : name,
                              "host" : host,
                              "event" : "updated"})

def main():
    ''' Called by the easyinstall mapping script
    '''
    # launch the admin
    Admin('lo', '40406')

if __name__ == '__main__':
    main()


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
from domogik.common.database import DbHelper      #, DbHelperException
from domogik.common.plugin import Plugin
#from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.common.utils import get_ip_for_interfaces
from domogikmq.pubsub.subscriber import MQAsyncSub
from domogikmq.pubsub.publisher import MQPub
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
from domogik.admin.application import app as admin_app
import locale
import traceback
import zmq
#import signal
import time
import json
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

zmq.eventloop.ioloop.install()

REST_API_VERSION = "0.8"

################################################################################


class Publisher(MQAsyncSub):
    """Handles new data to be passed on to subscribers."""
    def __init__(self):
        self.ctx = zmq.Context()
        self.WSmessages = Queue()
        self.MQmessages = Queue()
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
        """Receive message from MQ sub and send to WS."""
        yield self.WSmessages.put({"msgid": did, "content": msg})

    @gen.coroutine
    def publishToWS(self):
        while True:
            message = yield self.WSmessages.get()
            if len(self.subscribers) > 0:
                #print(u"Pushing MQ message to {} WS subscribers...".format(len(self.subscribers)))
                yield [subscriber.submit(message) for subscriber in self.subscribers]

    @gen.coroutine
    def publishToMQ(self):
        while True:
            message = yield self.MQmessages.get()
            self.sendToMQ(message)
    
    def sendToMQ(self, message):
        try:
            ctx = zmq.Context()
            jsons = json.loads(message)
            # req/rep
            if 'mq_request' in jsons and 'data' in jsons:
                cli = MQSyncReq(ctx)
                msg = MQMessage()
                msg.set_action(str(jsons['mq_request']))
                msg.set_data(jsons['data'])
                print(u"REQ : {0}".format(msg.get()))
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
                self.pub.send_event(jsons['mq_publish'],
                                jsons['data'])
        except Exception as e:
            print(u"Error sending mq message: {0}".format(e))

class Subscription(WebSocketHandler):
    """Websocket for subscribers."""
    def initialize(self, publisher):
        self.publisher = publisher
        self.messages = Queue()
        self.finished = False

    def open(self):
        print("New subscriber.")
        self.publisher.register(self)
        self.run()

    def on_close(self):
        self._close()        

    def _close(self):
        print("Subscriber left.")
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
        """ reciev message from websocket and send to MQ """
        #print(u"WS to MQ: {0}".format(content))
        self.publisher.MQmessages.put(content)

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
        # logging initialization
        self.log.info(u"Admin Server initialisation...")
        self.log.debug(u"locale : {0}".format(locale.getdefaultlocale()))
        try:
            try:
                # admin config
                cfg_admin = Loader('admin')
                config_admin = cfg_admin.load()
                conf_admin = dict(config_admin[1])
                self.interfaces = conf_admin['interfaces']
                self.port = conf_admin['port']
                # if use_ssl = True, set here path for ssl certificate/key
                self.use_ssl = conf_admin['use_ssl']
                if self.use_ssl.strip() == "True":
                    self.use_ssl = True
                self.key_file = conf_admin['ssl_key']
                self.cert_file = conf_admin['ssl_certificate']
                if 'clean_json' in conf_admin:
                    self.clean_json = conf_admin['clean_json']
                else:
                    self.clean_json = False
                if 'rest_auth'in conf_admin:
                    self.rest_auth = conf_admin['rest_auth']
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
                self.log.error("Error while reading configuration for section [admin] : using default values instead")
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
            self.start_http()
            # calls the tornado.ioloop.instance().start()
            
            ### Component is ready
            self.ready(0)
            IOLoop.instance().start()
        except :
            self.log.error(u"{0}".format(self.get_exception()))

    @gen.coroutine
    def start_http(self):
        """ Start HTTP Server
        """
        self.log.info(u"Start HTTP Server on {0}:{1}...".format(self.interfaces, self.port))
        # logger
        for log in self.log.handlers:
            admin_app.logger.addHandler(log)
        admin_app.zmq_context = self.zmq
        admin_app.db = DbHelper()
        admin_app.datatypes = self.datatypes
        admin_app.clean_json = self.clean_json
        admin_app.rest_auth = self.rest_auth
        admin_app.apiversion = REST_API_VERSION
        admin_app.use_ssl = self.use_ssl
        admin_app.hostname = self.get_sanitized_hostname()
        admin_app.resources_directory = self.get_resources_directory()
        admin_app.packages_directory = self.get_packages_directory()
        admin_app.publish_directory = self.get_publish_directory() # publish directory for all packages
        
        publisher = Publisher()
        tapp = Application([
            (r"/ws", Subscription, dict(publisher=publisher)),
            (r".*", FallbackHandler, dict(fallback=WSGIContainer(admin_app)))
            ])

	# create the server
        # for ssl, extra parameter to HTTPServier init
        if self.use_ssl is True:
            ssl_options = {
                 "certfile": self.cert_file,
                 "keyfile": self.key_file,
            }
            print(ssl_options)
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
                self.log.info(" - {0}:{1} [BIND]".format(ip, self.port))
                self.http_server.listen(int(self.port), address=ip)
                num_int += 1
            if num_int == 0:
                self.log.error("The admin is not configured to use any working network interface! Please check configuration!!!!!!")
        else:
            self.http_server.bind(int(self.port))
            self.http_server.start(0)
        yield [publisher.publishToMQ(), publisher.publishToWS()]

    def stop_http(self):
        """ Stop HTTP Server
        """
        self.log.info('Stopping http server')
        self.http_server.stop()
 
        self.log.info('Will shutdown in 10 seconds ...' )
        io_loop = tornado.ioloop.IOLoop.instance()
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

    def get_exception(self):
        """ Get exception and display it on stdout
        """
        my_exception =  str(traceback.format_exc()).replace('"', "'")
        return my_exception

def main():
    ''' Called by the easyinstall mapping script
    '''
    # launch the admin
    Admin('lo', '40406')

if __name__ == '__main__':
    main()

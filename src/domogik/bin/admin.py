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
from domogik.common.database import DbHelper, DbHelperException
from domogik.common.plugin import Plugin
from domogik.common import logger
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
import signal
import time
import json
import datetime
import random
import uuid
from threading import Thread, Lock
zmq.eventloop.ioloop.install()
from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop, PeriodicCallback 
from tornado.httpserver import HTTPServer
from tornado.web import FallbackHandler, Application
from tornado.websocket import WebSocketHandler, WebSocketClosedError

################################################################################

### web sockets cleanup
# this is used to list all webscokets
# example : [{'open': True, 'ws': <domogik.bin.admin.AdminWebSocket object at 0x7f9568f09bd0>}, {'open': True, 'ws': <domogik.bin.admin.AdminWebSocket object at 0x7f9568f17710>}]
# a timer will check for ws with open == False and destroy them
#
# this is needed as the MQASyncSub uses also the on_message function and a socket, so the object is not destroyed as usual :(
class WSList():
    def __init__(self):
        self.web_sockets = [{"id" : "foo", "open" : True}]
    
    def add(self, data):
        self.web_sockets.append(data)

    def list(self):
        return self.web_sockets

ws_list = WSList()

class AdminWebSocket(WebSocketHandler, MQAsyncSub):
    #clients = set()

    def __init__(self, application, request, **kwargs):
        WebSocketHandler.__init__(self, application, request, **kwargs)
        self.io_loop = IOLoop.instance()
        self.pub = MQPub(zmq.Context(), 'admin')

    def open(self):
        self.id = uuid.uuid4()
        print("Open WebSocket connection : {0}".format(self.id))
        MQAsyncSub.__init__(self, zmq.Context(), 'admin', [])
        # Ping to make sure the agent is alive.
        self.io_loop.add_timeout(datetime.timedelta(seconds=random.randint(5,30)), self.send_ping)
        #AdminWebSocket.clients.add(self)
        #web_sockets.append({"id" : self.id, "ws" : self, "open" : True})
        global ws_list
        ws_list.add({"id" : self.id, "ws" : self, "open" : True})
        print(ws_list.list())


    def on_connection_timeout(self):
        self.on_close()

    def send_ping(self):
        try:
            self.ping("a")
            self.ping_timeout = self.io_loop.add_timeout(datetime.timedelta(minutes=1), self.on_connection_timeout)
        except Exception as ex:
            pass

    def on_pong(self, data):
        if hasattr(self, "ping_timeout"):
            self.io_loop.remove_timeout(self.ping_timeout)
            # Wait 5 seconds before pinging again.
            self.io_loop.add_timeout(datetime.timedelta(seconds=5), self.send_ping)

    def on_close(self):

        print("Close WebSocket {0}".format(self.id))
        print("Stop subscribing to MQ for {0}".format(self.id))
        #self.stop_sub()
        #AdminWebSocket.clients.remove(self)
        #for a_ws in web_sockets:
        #    if a_ws['id'] == self.id:
        #        a_ws['open'] = False
        #        print("ws set to open == False : {0}".format(self.id))
                

    def on_message(self, msg, content=None):
        """ This function is quite tricky
            It is called by both WebSocketHandler and MQASyncSub...
        """
        try:
            ### websocket message (from the web)
            if not content:
                jsons = json.loads(msg)

                # req/rep
                if 'action' in jsons and 'data' in jsons:
                    cli = MQSyncReq(zmq.Context())
                    msg = MQMessage()
                    msg.set_action(str(jsons['action']))
                    msg.set_data(jsons['data'])
                    if 'dst' in jsons:
                        cli.request(str(jsons['dst']), msg.get(), timeout=10).get()
                    else:
                        cli.request('manager', msg.get(), timeout=10).get()

                # pub
                elif 'publish' in jsons and 'data' in jsons:
                    print("Publish : {0}".format(jsons['data']))
                    self.pub.send_event(jsons['publish'],
                                        jsons['data'])

            ### MQ message (from domogik)
            else:
                #for cli in AdminWebSocket.clients:
                #    cli.write_message({"msgid": msg, "content": content})
                try:
                    self.write_message({"msgid": msg, "content": content})
                except WebSocketClosedError:
                    print("websocketclosederror..")
        except:
            print("Error : {0}".format(traceback.format_exc()))

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

        Plugin.__init__(self, name = 'admin')
        # logging initialization
        self.log.info(u"Admin Server initialisation...")
        self.log.debug(u"locale : %s %s" % locale.getdefaultlocale())

	try:
            try:
                cfg_rest = Loader('admin')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.interfaces = conf_rest['interfaces']
                self.port = conf_rest['port']
                # if rest_use_ssl = True, set here path for ssl certificate/key
                self.use_ssl = conf_rest['use_ssl']
                self.key_file = conf_rest['ssl_certificate']
                self.cert_file = conf_rest['ssl_key']
            except KeyError:
                # default parameters
                self.interfaces = server_interfaces
                self.port = server_port
		self.use_ssl = False
		self.key_file = ""
		self.cert_file = ""
                self.clean_json = False
            self.log.info(u"Configuration : interfaces:port = %s:%s" % (self.interfaces, self.port))
	    
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
            self.log.error(u"%s" % self.get_exception())

    def start_http(self):
        """ Start HTTP Server
        """
        self.log.info(u"Start HTTP Server on %s:%s..." % (self.interfaces, self.port))
        # logger
        for log in self.log.handlers:
            admin_app.logger.addHandler(log)
        admin_app.zmq_context = self.zmq
        admin_app.db = DbHelper()
        admin_app.datatypes = self.datatypes
        
	tapp = Application([
		(r"/ws", AdminWebSocket),
        (r".*", FallbackHandler, dict(fallback=WSGIContainer(admin_app)))
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
	    intf = self.interfaces.split(',')
	    for ip in get_ip_for_interfaces(intf):
	        self.http_server.listen(int(self.port), address=ip)
        else:
            self.http_server.bind(int(self.port))
            self.http_server.start(1)
        return

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


def clean_websockets():
    global ws_list

    while True:
        time.sleep(5)
        print("Start cleaning websockets...")
        print(ws_list.list())
        #for a_ws in web_sockets:
        #    print(a_ws)
        #    if a_ws["open"] == False:
        #        print("Closing {0}".format(a_ws['id']))

def main():
    ''' Called by the easyinstall mapping script
    '''
    # launch the cleanup process
    thr_cleanup = Thread(None,
                         clean_websockets,
                         "clean_ws",
                         (),
                         {})
    #thr_cleanup.start()

    # launch the admin
    Admin('lo', '40406')

if __name__ == '__main__':
    main()

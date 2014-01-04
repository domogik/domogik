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

class Admin(XplPlugin)
class AdminWebSocket(WebSocketHandler, MQAsyncSub)

@author: 	Friz <fritz.smh@gmail.com>
		Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.common.database import DbHelper, DbHelperException
from domogik.xpl.common.plugin import XplPlugin
from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.common.utils import get_ip_for_interfaces
from domogik.mq.pubsub.subscriber import MQAsyncSub
from domogik.mq.message import MQMessage
from domogik.mq.reqrep.client import MQSyncReq
from domogik.admin.application import app as admin_app
import locale
import traceback
import zmq
import signal
import time
import json
zmq.eventloop.ioloop.install()
from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop, PeriodicCallback 
from tornado.httpserver import HTTPServer
from tornado.web import FallbackHandler, Application
from tornado.websocket import WebSocketHandler

################################################################################
class AdminWebSocket(WebSocketHandler, MQAsyncSub):
    clients = set()

    def open(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'admin', [])
        AdminWebSocket.clients.add(self)

    def on_close(self):
        AdminWebSocket.clients.remove(self)

    def on_message(self, msg, content=None):
        if not content:
            # this is a websocket message
            jsons = json.loads(msg)
            if 'action' in jsons and 'data' in jsons:
                cli = MQSyncReq(zmq.Context())
                msg = MQMessage()
                msg.set_action(str(jsons['action']))
                msg.set_data(jsons['data'])
                print cli.request('manager', msg.get(), timeout=10).get()
        else:
            # this is a mq message
            print(u"New pub message {0}".format(msg))
            for cli in AdminWebSocket.clients:
                cli.write_message({'msgid': msg, 'content': content})

class Admin(XplPlugin):
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

        XplPlugin.__init__(self, name = 'admin', nohub = True)
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
            # TODO : delete
            #self.db = DbHelper()

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
        # db access
        admin_app.db = DbHelper()
        admin_app.zmq_context = self.zmq
        # handler for getting the paths
        admin_app.resources_directory = self.get_resources_directory()
        
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
        selg.http_server.stop()
 
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
    Admin('lo', '40405')

if __name__ == '__main__':
    main()

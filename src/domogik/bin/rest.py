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

class Rest(Plugin):
@author: 	Friz <fritz.smh@gmail.com>
		Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.common.database import DbHelper, DbHelperException
from domogik.common.plugin import Plugin
from domogik.common import logger
from domogik.rest.url import urlHandler
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from domogik.common.configloader import Loader
from domogik.common.utils import get_ip_for_interfaces
import locale
from Queue import Queue, Empty, Full
import tempfile
import traceback
import datetime
import errno
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
import zmq
import signal
zmq.eventloop.ioloop.install()
from tornado.ioloop import IOLoop 

REST_API_VERSION = "0.7"
USE_SSL = False
SSL_CERTIFICATE = "/dev/null"
# temp dir
TMP_DIR = tempfile.gettempdir()
# Repository
DEFAULT_REPO_DIR = TMP_DIR

################################################################################
class Rest(Plugin):
    """ REST Server 
        - create a HTTP server 
        - process REST requests
    """
        

    def __init__(self, server_interfaces, server_port):
        """ Initiate DbHelper, Logs and config
            Then, start HTTP server and give it initialized data
            @param server_interfaces :  interfaces of HTTP server
            @param server_port :  port of HTTP server
        """

        Plugin.__init__(self, name = 'rest')
        # logging initialization
        self.log.info(u"Rest Server initialisation...")
        self.log.debug(u"locale : %s %s" % locale.getdefaultlocale())

        # API version
        self._rest_api_version = REST_API_VERSION

        try:
            ### Config
            # directory data 
            cfg = Loader('domogik')
            config = cfg.load()
            conf = dict(config[1])
            self.log_dir_path = conf['log_dir_path']

            # plugin installation path
            #self._package_path = conf['package_path']
            #self._src_prefix = None
            #self.log.info(u"Set package path to '%s' " % self._package_path)
            #self._design_dir = "%s/domogik_packages/design/" % self._package_path
            self.package_mode = True
    
            # HTTP server ip and port
            try:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.interfaces = conf_rest['interfaces']
                self.port = conf_rest['port']
                use_ssl = False
                # if rest_use_ssl = True, set here path for ssl certificate/key
                self.use_ssl = conf_rest['use_ssl']
                self.key_file = conf_rest['ssl_certificate']
                self.cert_file = conf_rest['ssl_key']
                if 'clean_json' in conf_rest:
                    self.clean_json = conf_rest['clean_json']
                else:
                    self.clean_json = False
            except KeyError:
                # default parameters
                self.interfaces = server_interfaces
                self.port = server_port
		self.use_ssl = False
		self.key_file = ""
		self.cert_file = ""
                self.clean_json = False
            self.log.info(u"Configuration : interfaces:port = %s:%s" % (self.interfaces, self.port))
    
            # SSL configuration
            try:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.use_ssl = conf_rest['use_ssl']
                if self.use_ssl == "True":
                    self.use_ssl = True
                else:
                    self.use_ssl = False
                self.ssl_certificate = conf_rest['ssl_certificate']
            except KeyError:
                # default parameters
                self.use_ssl = USE_SSL
                self.ssl_certificate = SSL_CERTIFICATE
            if self.use_ssl == True:
                self.log.info(u"Configuration : SSL support activated (certificate : %s)" % self.ssl_certificate)
            else:
                self.log.info(u"Configuration : SSL support not activated")
    
            # File repository
            try:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.repo_dir = conf_rest['repository']
            except KeyError:
                # default parameters
                self.repo_dir = DEFAULT_REPO_DIR

 	    # Launch server, stats
            self.log.info(u"REST Initialisation OK")
            self.add_stop_cb(self.stop_http)
            self.server = None
            # calls the tornado.ioloop.instance().start()
            self.start_http()
            
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
            urlHandler.logger.addHandler(log)
        # db access
        urlHandler.db = DbHelper()
        # needed for status
        urlHandler.apiversion = self._rest_api_version
        urlHandler.use_ssl = self.use_ssl
        urlHandler.hostname = self.get_sanitized_hostname()
        urlHandler.clean_json = self.clean_json
        # reload statsmanager helper
        urlHandler.reload_stats = self.reload_stats
        urlHandler.zmq_context = self.zmq
        # handler for getting the paths
        urlHandler.resources_directory = self.get_resources_directory()
        
	# create the server
        # for ssl, extra parameter to HTTPServier init
        if self.use_ssl:
            ssl_options = {
                 "certfile": self.cert_file,
                 "keyfile": self.key_file,
            }
	    self.http_server = HTTPServer(WSGIContainer(urlHandler), ssl_options=ssl_options)
        else:
            self.http_server = HTTPServer(WSGIContainer(urlHandler))
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
 
        self.log.info('Will shutdown in <F2>0 seconds ...' )
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

    def reload_stats(self):
        self.log.debug(u"=============== reload stats")
        req = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action( 'reload' )
        resp = req.request('xplgw', msg.get(), 100)
        self.log.debug(u"Reply from xplgw: {0}".format(resp))
        self.log.debug(u"=============== reload stats END")

    def get_exception(self):
        """ Get exception and display it on stdout
        """
        my_exception =  str(traceback.format_exc()).replace('"', "'")
        # TODO : to delete : no more need to print this as log are in stdout
        #print(u"==== Error in REST ====")
        #print(my_exception)
        #print(u"=======================")
        return my_exception

if __name__ == '__main__':
    # Create REST server with default values (overriden by ~/.domogik/domogik.cfg)
    REST = Rest('lo', '40405')


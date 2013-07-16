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

class Rest(XplPlugin):
@author: 	Friz <fritz.smh@gmail.com>
		Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.common.database import DbHelper, DbHelperException
from domogik.xpl.common.plugin import XplPlugin
from domogik.common import logger
from domogik.xpl.lib.rest.event import DmgEvents
from domogik.xpl.lib.rest.url import urlHandler
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from domogik.common.configloader import Loader
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
class Rest(XplPlugin):
    """ REST Server 
        - create a HTTP server 
        - process REST requests
    """
        

    def __init__(self, server_ip, server_port):
        """ Initiate DbHelper, Logs and config
            Then, start HTTP server and give it initialized data
            @param server_ip :  ip of HTTP server
            @param server_port :  port of HTTP server
        """

        XplPlugin.__init__(self, name = 'rest')
        # logging initialization
        self.log.info("Rest Server initialisation...")
        self.log.debug("locale : %s %s" % locale.getdefaultlocale())

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
            #self.log.info("Set package path to '%s' " % self._package_path)
            #self._design_dir = "%s/domogik_packages/design/" % self._package_path
            self.package_mode = True
    
            # HTTP server ip and port
            try:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.server_ip = conf_rest['server_ip']
                self.server_port = conf_rest['server_port']
            except KeyError:
                # default parameters
                self.server_ip = server_ip
                self.server_port = server_port
            self.log.info("Configuration : ip:port = %s:%s" % (self.server_ip, self.server_port))
    
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
                self.log.info("Configuration : SSL support activated (certificate : %s)" % self.ssl_certificate)
            else:
                self.log.info("Configuration : SSL support not activated")
    
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
            self.log.info("REST Initialisation OK")
            self.add_stop_cb(self.stop_http)
            self.server = None
            # calls the tornado.ioloop.instance().start()
            self.start_http()
            
            ### Component is ready
            self.ready(0)
            IOLoop.instance().start()
        except :
            self.log.error("%s" % self.get_exception())

    def start_http(self):
        """ Start HTTP Server
        """
        self.log.info("Start HTTP Server on %s:%s..." % (self.server_ip, self.server_port))
        # logger
        for log in self.log.handlers:
            urlHandler.logger.addHandler(log)
        # db access
        urlHandler.db = DbHelper()
        # needed for status
        urlHandler.apiversion = self._rest_api_version
        urlHandler.use_ssl = self.use_ssl
        urlHandler.hostname = self.get_sanitized_hostname()
        # xpl handler
        urlHandler.xpl = self.myxpl 
        # reload statsmanager helper
        urlHandler.reload_stats = self.reload_stats
        urlHandler.zmq_context = self._zmq
        # handler for getting the paths
        urlHandler.resources_directory = self.get_resources_directory()
        
        self.http_server = HTTPServer(WSGIContainer(urlHandler))
        # for ssl, extra parameter to HTTPServier init
        #ssl_options={
             #"certfile": os.path.join(data_dir, "mydomain.crt"),
             #"keyfile": os.path.join(data_dir, "mydomain.key"),
        #}) 
        self.http_server.listen(int(self.server_port), address=self.server_ip)
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
        self.log.debug("=============== reload stats")
        req = MQSyncReq(self._zmq)
        msg = MQMessage()
        msg.setaction( 'reload' )
        req.request('statmgr', msg.get())

    def get_exception(self):
        """ Get exception and display it on stdout
        """
        my_exception =  str(traceback.format_exc()).replace('"', "'")
        # TODO : to delete : no more need to print this as log are in stdout
        #print("==== Error in REST ====")
        #print(my_exception)
        #print("=======================")
        return my_exception

if __name__ == '__main__':
    # Create REST server with default values (overriden by ~/.domogik/domogik.cfg)
    REST = Rest("127.0.0.1", "8080")


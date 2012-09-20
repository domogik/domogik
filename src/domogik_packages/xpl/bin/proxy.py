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

- Add authentification to the rest server via a tiny proxy

Implements
==========



@author: bibi21000 <bibi21000@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
#import time
import urllib
import locale
#import datetime
from OpenSSL import SSL
import SocketServer
import threading
#import urlparse
#import os
#import errno
#import pyinotify
#import calendar
#import tempfile
import traceback
#from threading import Semaphore
from BaseHTTPServer import HTTPServer
#from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from domogik.common.configloader import Loader
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.common.database import DbHelper, DbHelperException
#from XyneHTTPServer import BaseHTTPRequestHandler, HTTPServer
from domogik_packages.xpl.lib.proxy import ProxyException, ProxyHandler

################################################################################
class Proxy(XplPlugin):
    """ REST Proxy
        - create a HTTP server
        - process REST proxy requests
    """

    def __init__(self, proxy_ip, proxy_port):
        """
        Initiate properties
        Then, start HTTP server and give it initialized data
        @param proxy_ip :  ip of the proxy server
        @param proxy_port :  port of proxy server
        """

        XplPlugin.__init__(self, name = 'proxy',
            reload_cb = self.reload_config)
        # logging initialization
        self.log.info("Proxy initialisation ...")
        self.log.debug("locale : %s %s" % locale.getdefaultlocale())
        self._config = Query(self.myxpl, self.log)
        self.server = None
        self.server_process = None
        self.proxy_ip = None
        self.proxy_port = None
        self.use_ssl = False
        self.ssl_certificate = None
        self.server_ip = None
        self.server_port = None
        self.auth_method = None
        self.username = None
        self.password = None
        self.add_stop_cb(self.stop_http)
        self.enable_hbeat()
        self.reload_config()
        #self.log.info("Proxy initialisation done")

    def reload_config(self):
        '''
        Load configuration an start proxy server
        '''
        if self.server != None:
            self.stop_http()
            self.server = None
            self.server_process = None
        try:
            cfg_rest = Loader('rest')
            config_rest = cfg_rest.load()
            conf_rest = dict(config_rest[1])
            self.server_ip = conf_rest['rest_server_ip']
            self.server_port = conf_rest['rest_server_port']
        except KeyError:
            self.log.error("Can't retrieve REST configuration from domogik.cfg. Leave plugin.")
            self.force_leave()
        try:
            self.proxy_ip = self._config.query('proxy', 'proxy-ip')
            self.proxy_port = self._config.query('proxy', 'proxy-port')
        except:
            self.log.warning("Can't get proxy address configuration from XPL. Use default value.")
        finally:
            if self.proxy_ip == None:
                self.proxy_ip = self.server_ip
            try :
                self.proxy_port = int(self.proxy_port)
            except:
                self.proxy_port = str(int(self.server_port)+1)
        try:
            self.auth_method = self._config.query('proxy', 'auth-method')
        except:
            self.log.warning("Can't get authentification method from XPL. Use basic by default.")
        finally:
            if self.auth_method == None:
                self.auth_method = "basic"
        try:
            self.username = self._config.query('proxy', 'username')
            self.password = self._config.query('proxy', 'password')
        except:
            self.log.warning("Can't get username/password from XPL. Use defaults.")
        finally:
            if self.username == None or self.username == "None" :
                self.username = "admin"
            if self.password == None or self.password == "None" :
                self.password = "123"
        try:
            boo = self._config.query('proxy', 'use-ssl')
            #print boo
            self.use_ssl = True if boo == "True" else False
            if self.use_ssl:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.ssl_certificate = conf_rest['rest_ssl_certificate']
        except KeyError:
            self.log.warning("Can't get ssl configuration from XPL. Do not use it.")
            self.use_ssl = False
            self.ssl_certificate = None
        self.log.info("Proxy configuration  : ip:port = %s:%s" % (self.proxy_ip, self.proxy_port))
        if self.use_ssl == True:
            self.log.info("Proxy configuration : SSL support activated (certificate : %s)" % self.ssl_certificate)
        else:
            self.log.info("Proxy configuration : SSL support not activated")
        self.log.info("Proxy authentification  : %s" % (self.auth_method))
        self.log.info("Rest configuration : ip:port = %s:%s" % (self.server_ip, self.server_port))
        try:
            self.start_http()
        except :
            self.log.error("Can't start proxy. Leave plugin.")
            self.log.error("%s" % str(traceback.format_exc()).replace('"', "'"))
            self.force_leave()

    def start_http(self):
        """
        Start HTTP proxy
        """
        # Start HTTP proxy
        self.log.info("Start HTTP proxy on %s:%s..." % (self.proxy_ip, self.proxy_port))
        if self.use_ssl:
            self.server = HTTPSServerWithParam((self.proxy_ip, int(self.proxy_port)), \
                                            (self.server_ip, int(self.server_port)), \
                                            self.get_stop(), self.log, self.auth_method, \
                                            self.username, self.password, \
                                            ProxyHandler, bind_and_activate=True, handler_params = [self])
        else:
            self.server = HTTPServerWithParam((self.proxy_ip, int(self.proxy_port)), \
                                            (self.server_ip, int(self.server_port)), \
                                            self.get_stop(), self.log, self.auth_method, \
                                            self.username, self.password, \
                                            ProxyHandler, bind_and_activate=True, handler_params = [self])
        self.server.serve_forever()
        #self.log.info("HTTP proxy started.")
        #self.server.server_bind()
        #self.server.server_activate()
        #self.server_process = threading.Thread(None,
        #                    self.server.serve_forever(),
        #                    "rest_proxy",
        #                    (),
        #                    {})
        #self.log.info("HTTP proxy started.")
        #self.server_process.start()

    def stop_http(self):
        """
        Stop HTTP proxy
        """
        if self.server != None:
            self.server.stop_handling()


################################################################################
# HTTP
class HTTPServerWithParam(SocketServer.ThreadingMixIn, HTTPServer):
    """ Extends HTTPServer to allow send params to the Handler.
    """

    def __init__(self, proxy_address, server_address, get_stop, log, \
                 auth_method, username, password, \
                 request_handler_class, bind_and_activate=True, handler_params = []):
        HTTPServer.__init__(self, proxy_address, request_handler_class, \
                            bind_and_activate)
        self.username = username
        self.password = password
        self.address = proxy_address
        self.server = server_address
        self.handler_params = handler_params
        self.log = log
        self.get_stop = get_stop
        self.auth_method = auth_method
        self.stop = False
        #self.daemon_threads = True
        # DB Helper
        #self.db = DbHelper()

    def serve_forever(self):
        """
        we rewrite this fucntion to make HTTP Server shutable
        """
        self.stop = False
        while not (self.stop or self.get_stop.isSet()):
            self.handle_request()

    def stop_handling(self):
        """
        Put the stop flag to True in order stopping handling requests
        """
        self.stop = True
        # we do a last request to terminate server
        #print("Make a last request to HTTP server to stop it")
        resp = urllib.urlopen("http://%s:%s" % (self.address[0], self.address[1]))

################################################################################
# HTTPS
class HTTPSServerWithParam(SocketServer.ThreadingMixIn, HTTPServer):
    """
    Extends HTTPServer to allow send params to the Handler.
    """

    def __init__(self, proxy_address, server_address, get_stop, log, \
                 auth_method, username, password, \
                 request_handler_class, bind_and_activate=True, handler_params = []):
        HTTPServer.__init__(self, proxy_address, request_handler_class, \
                            bind_and_activate)
        self.username = username
        self.password = password
        self.address = proxy_address
        self.server = server_address
        self.handler_params = handler_params
        self.log = log
        self.get_stop = get_stop
        self.auth_method = auth_method
        self.stop = False
        ### SSL specific
        ssl_certificate = self.handler_params[0].ssl_certificate
        #if 1 == 1:
        try:
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.use_privatekey_file (ssl_certificate)
            ctx.use_certificate_file(ssl_certificate)
            self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                        self.socket_type))
        except:
            error = "SSL error : %s. Did you generate certificate ?" % self.handler_params[0].get_exception()
            print(error)
            self.handler_params[0].log.error(error)
            # force exiting
            self.handler_params[0].force_leave()
            return
        # DB Helper
        #self.db = DbHelper()

    def serve_forever(self):
        """
        we rewrite this fucntion to make HTTP Server shutable
        """
        self.stop = False
        while not (self.stop or self.get_stop.isSet()):
            self.handle_request()

    def stop_handling(self):
        """
        Put the stop flag to True in order stopping handling requests
        """
        self.stop = True
        # we do a last request to terminate server
        resp = urllib.urlopen("https://%s:%s" % (self.address[0], self.address[1]))

if __name__ == '__main__':
    # Create REST server with default values (overriden by ~/.domogik/domogik.cfg)
    PROXY = Proxy("127.0.0.1", "8081")


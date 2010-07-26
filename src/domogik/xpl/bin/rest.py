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
- Log device stats by listening xpl network

Implements
==========

TODO when finished ;)



@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.common import logger
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from domogik.common.database import DbHelper
from domogik.xpl.common.helper import HelperError
from domogik.common.configloader import Loader
from xml.dom import minidom
import time
import urllib
import sys
import locale
from socket import gethostname
from Queue import *
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.plugin import XplResult
import re
import traceback
import datetime
import socket
from OpenSSL import SSL
import SocketServer
import os
import glob
import random
import calendar
import domogik.xpl.helpers
import pkgutil
import uuid
import stat
import shutil
import mimetypes



REST_API_VERSION = "0.1"
REST_DESCRIPTION = "REST plugin is part of Domogik project. See http://trac.domogik.org/domogik/wiki/modules/REST.en for REST API documentation"

### parameters that can be overidden by Domogik config file
USE_SSL = False
SSL_CERTIFICATE = "/dev/null"

# global queues config (plugins, etc)
QUEUE_TIMEOUT = 15
QUEUE_SIZE = 10
QUEUE_LIFE_EXPECTANCY = 3
QUEUE_SLEEP = 0.1 # sleep time between reading all queue content

# /command queue config
QUEUE_COMMAND_SIZE = 1000

# /event queue config
QUEUE_EVENT_TIMEOUT = 120   # If 0, no timeout is set
QUEUE_EVENT_LIFE_EXPECTANCY = 5
QUEUE_EVENT_SIZE = 50

# Repository
DEFAULT_REPO_DIR = "/tmp/"

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
        self._log.info("Rest Server initialisation...")
        self._log.debug("locale : %s %s" % locale.getdefaultlocale())

        # logging Queue activities
        log_queue = logger.Logger('rest-queues')
        self._log_queue = log_queue.get_logger()
        self._log_queue.info("Rest's queues activities...")
    
        # logging data manipulation initialization
        log_dm = logger.Logger('rest-dm')
        self._log_dm = log_dm.get_logger()
        self._log_dm.info("Rest Server Data Manipulation...")
    
        try:
    
            ### Config
    
            # directory data in ~/.domogik.cfg
            cfg = Loader('domogik')
            config = cfg.load()
            conf = dict(config[1])
            self._xml_directory = "%s/share/domogik/url2xpl/" % conf['custom_prefix']
    
            # HTTP server ip and port
            try:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.server_ip = conf_rest['rest_server_ip']
                self.server_port = conf_rest['rest_server_port']
            except KeyError:
                # default parameters
                self.server_ip = server_ip
                self.server_port = server_port
            self._log.info("Configuration : ip:port = %s:%s" % (self.server_ip, self.server_port))
    
            # SSL configuration
            try:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.use_ssl = conf_rest['rest_use_ssl']
                if self.use_ssl == "True":
                    self.use_ssl = True
                else:
                    self.use_ssl = False
                self.ssl_certificate = conf_rest['rest_ssl_certificate']
            except KeyError:
                # default parameters
                self.use_ssl = USE_SSL
                self.ssl_certificate = SSL_CERTIFICATE
            if self.use_ssl == True:
                self._log.info("Configuration : SSL support activated (certificate : %s)" % self.ssl_certificate)
            else:
                self._log.info("Configuration : SSL support not activated")
    
            # File repository
            try:
                cfg_rest = Loader('rest')
                config_rest = cfg_rest.load()
                conf_rest = dict(config_rest[1])
                self.repo_dir = conf_rest['rest_repository']
            except KeyError:
                # default parameters
                self.repo_dir = DEFAULT_REPO_DIR

            # Gloal Queues config
            self._log.debug("Get queues configuration")
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-timeout', res)
            self._queue_timeout = res.get_value()['q-timeout']
            if self._queue_timeout == "None":
                self._queue_timeout = QUEUE_TIMEOUT
            self._queue_timeout = float(self._queue_timeout)
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-size', res)
            self._queue_size = res.get_value()['q-size']
            if self._queue_size == "None":
                self._queue_size = QUEUE_SIZE
            self._queue_size = float(self._queue_size)
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-life-exp', res)
            self._queue_life_expectancy = res.get_value()['q-life-exp']
            if self._queue_life_expectancy == "None":
                self._queue_life_expectancy = QUEUE_LIFE_EXPECTANCY
            self._queue_life_expectancy = float(self._queue_life_expectancy)
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-sleep', res)
            self._queue_sleep = res.get_value()['q-sleep']
            if self._queue_sleep == "None":
                self._queue_sleep = QUEUE_SLEEP
            self._queue_sleep = float(self._queue_sleep)

            # /command Queues config
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-cmd-size', res)
            self._queue_command_size = res.get_value()['q-cmd-size']
            if self._queue_command_size == "None":
                self._queue_command_size = QUEUE_COMMAND_SIZE
            self._queue_command_size = float(self._queue_command_size)

            # /event Queues config
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-evt-size', res)
            self._queue_event_size = res.get_value()['q-evt-size']
            if self._queue_event_size == "None":
                self._queue_event_size = QUEUE_EVENT_SIZE
            self._queue_event_size = float(self._queue_event_size)
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-evt-timeout', res)
            self._queue_event_timeout = res.get_value()['q-evt-timeout']
            if self._queue_event_timeout == "None":
                self._queue_event_timeout = QUEUE_EVENT_TIMEOUT
            self._queue_event_timeout = float(self._queue_event_timeout)
            self._config = Query(self._myxpl)
            res = XplResult()
            self._config.query('rest', 'q-evt-life-exp', res)
            self._queue_event_life_expectancy = res.get_value()['q-evt-life-exp']
            if self._queue_event_life_expectancy == "None":
                self._queue_event_life_expectancy = QUEUE_EVENT_LIFE_EXPECTANCY
            self._queue_event_life_expectancy = float(self._queue_event_life_expectancy)
    
            # Queues for xPL
            self._queue_system_list = Queue(self._queue_size)
            self._queue_system_detail = Queue(self._queue_size)
            self._queue_system_start = Queue(self._queue_size)
            self._queue_system_stop = Queue(self._queue_size)

            # Queues for /command
            self._queue_command = Queue(self._queue_command_size)
    
            # Queues for /event
            # this queue will be fill by stat manager
            self._event_requests = EventRequests(self._log,
                                                 self._queue_event_size,
                                                 self._queue_event_timeout,
                                                 self._queue_event_life_expectancy)
    
            # define listeners for queues
            self._log.debug("Create listeners")
            Listener(self._add_to_queue_system_list, self._myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'list',
                      'host' : gethostname()})
            Listener(self._add_to_queue_system_detail, self._myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'detail',
                      'host' : gethostname()})
            Listener(self._add_to_queue_system_start, self._myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'start',
                      'host' : gethostname()})
            Listener(self._add_to_queue_system_stop, self._myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'stop',
                      'host' : gethostname()})
            Listener(self._add_to_queue_command, self._myxpl, \
                     {'xpltype': 'xpl-trig'})
    
            # Load xml files for /command
            self.load_xml()

            self._log.info("REST Initialisation OK")


            self.start_stats()
            self.start_http()




        except :
            self._log.error("%s" % self.get_exception())
  
  


    def _add_to_queue_system_list(self, message):
        self._put_in_queue(self._queue_system_list, message)

    def _add_to_queue_system_detail(self, message):
        self._put_in_queue(self._queue_system_detail, message)

    def _add_to_queue_system_start(self, message):
        self._put_in_queue(self._queue_system_start, message)

    def _add_to_queue_system_stop(self, message):
        self._put_in_queue(self._queue_system_stop, message)

    def _add_to_queue_command(self, message):
        self._put_in_queue(self._queue_command, message)

    def _get_from_queue(self, my_queue, filter = None, nb_rec = 0):
        """ Encapsulation for _get_from_queue_in
            If timeout not elapsed and _get_from_queue didn't find a valid data
            call again _get_from_queue until timeout
            This encapsulation is used to process case where queue is not empty but there is
            no valid data in it and we want to wait for timeout
        """
        start_time = time.time()
        ok = False
        while time.time() - start_time < self._queue_timeout:
            try:
                return self._get_from_queue_without_waiting(my_queue, filter, nb_rec)
            except Empty:
                # no data in queue for us.... let's continue until time elapsed
                # in order not rest not working so much, let it make a pause
                time.sleep(self._queue_sleep)
        # time elapsed... we can raise the Empty exception
        raise Empty



    def _get_from_queue_without_waiting(self, my_queue, filter = None, nb_rec = 0):
        """ Get an item from queue (recursive function)
            Checks are made on : 
            - life expectancy of message
            - filter given
            - size of queue
            If necessary, each item of queue is read.
            @param my_queue : queue to get data from
            @param filter : dictionnay of filters. Examples :
                - {"command" : "start", ...}
                - {"plugin" : "wol%", ...} : here "%" indicate that we search for something starting with "wol"
            @param nb_rec : internal parameter (do not use it for first call). Used to check recursivity VS queue size
        """
        self._log_queue.debug("Get from queue : %s (recursivity deepth : %s)" % (str(my_queue), nb_rec))
        # check if recursivity doesn't exceed queue size
        if nb_rec > my_queue.qsize():
            self._log_queue.warning("Get from queue %s : number of call exceed queue size (%s) : return None" % (str(my_queue), my_queue.qsize()))
            # we raise an "Empty" exception because we consider that if we don't find
            # the good data, it is as if it was "empty"
            raise Empty

        msg_time, message = my_queue.get(True, self._queue_timeout)

        # if message not too old, we process it
        if time.time() - msg_time < self._queue_life_expectancy:
            # no filter defined
            if filter == None: 
                self._log_queue.debug("Get from queue %s : return %s" % (str(my_queue), str(message)))
                return message

            # we want to filter data
            else:
                keep_data = True
                for key in filter:
                    # take care of final "%" in order to search data starting by filter[key]
                    if filter[key][-1] == "%":
                        msg_data = str(message.data[key])
                        filter_data = str(filter[key])
                        len_data = len(filter_data) - 1
                        if msg_data[0:len_data] != filter_data[0:-1]:
                            keep_data = False
                    # normal search
                    else:
                        if message.data[key] != filter[key]:
                            keep_data = False

                # if message is ok for us, return it
                if keep_data == True:
                    self._log_queue.debug("Get from queue %s : return %s" % (str(my_queue), str(message)))
                    return message

                # else, message get back in queue and get another one
                else:
                    self._log_queue.debug("Get from queue %s : bad data, check another one..." % (str(my_queue)))
                    self._put_in_queue(my_queue, message)
                    return self._get_from_queue_without_waiting(my_queue, filter, nb_rec + 1)

        # if message too old : get an other message
        else:
            self._log_queue.debug("Get from queue %s : data too old, check another one..." % (str(my_queue)))
            return self._get_from_queue_without_waiting(my_queue, filter, nb_rec + 1)

    def _put_in_queue(self, my_queue, message):
        self._log_queue.debug("Put in queue %s : %s" % (str(my_queue), str(message)))
        my_queue.put((time.time(), message), True, self._queue_timeout) 
        # todo : except Full:
        #           call a "clean" function
        #           put again in queue



    def start_http(self):
        """ Start HTTP Server
        """
        # Start HTTP server
        self._log.info("Start HTTP Server on %s:%s..." % (self.server_ip, self.server_port))

        if self.use_ssl:
            server = HTTPSServerWithParam((self.server_ip, int(self.server_port)), RestHandler, \
                                         handler_params = [self])
        else:
            server = HTTPServerWithParam((self.server_ip, int(self.server_port)), RestHandler, \
                                         handler_params = [self])

        server.serve_forever()




    def start_stats(self):
        """ Start Statistics manager
        """
        print "Start Stats"
        self._log.info("Starting statistics manager. His logs will be in a dedicated log file")
        StatsManager(handler_params = [self])




    def load_xml(self):
        """ Load XML files for /command
        """
        # list technologies folders
        self.xml = {}
        for techno in os.listdir(self._xml_directory):
            for command in os.listdir(self._xml_directory + "/" + techno):
                xml_file = self._xml_directory + "/" + techno + "/" + command
                self._log.info("Load XML file for %s>%s : %s" % (techno, command, xml_file))
                self.xml["%s-%s" % (techno, command)] = minidom.parse(xml_file)
        self.xml_date = datetime.datetime.now()




    def get_exception(self):
        # TODO : finish exception take in count
        #my_exception =  str(traceback.format_exc()).replace('"', "'").replace('\n', '      ')
        my_exception =  str(traceback.format_exc()).replace('"', "'")
        print "==== Error in REST ===="
        print my_exception
        print "======================="
        return my_exception




################################################################################
# HTTP
class HTTPServerWithParam(SocketServer.ThreadingMixIn, HTTPServer):
    """ Extends HTTPServer to allow send params to the Handler.
    """

    def __init__(self, server_address, request_handler_class, \
                 bind_and_activate=True, handler_params = []):
        HTTPServer.__init__(self, server_address, request_handler_class, \
                            bind_and_activate)
        self.handler_params = handler_params
        # dirty issue
        #self.timeout = None



################################################################################
# HTTPS
class HTTPSServerWithParam(SocketServer.ThreadingMixIn, HTTPServer):
    """ Extends HTTPServer to allow send params to the Handler.
    """

    def __init__(self, server_address, request_handler_class, \
                 bind_and_activate=True, handler_params = []):
        HTTPServer.__init__(self, server_address, request_handler_class, \
                            bind_and_activate)
        self.handler_params = handler_params
        # dirty issue
        #self.timeout = None

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
            print error
            self.handler_params[0]._log.error(error)
            # force exiting
            self.handler_params[0].force_leave()
            return
        self.server_bind()
        self.server_activate()









################################################################################
class RestHandler(BaseHTTPRequestHandler):
    """ Class/object called for each request to HTTP server
        Here we will process use GET/POST/OPTION HTTP methods 
        and then create a REST request
    """


######
# GET/POST/OPTIONS processing
######


    def setup(self):
        """ Function only for SSL
        """
        use_ssl = self.server.handler_params[0].use_ssl
        if use_ssl == True:
            self.connection = self.request
            self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
            self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
        else:
            BaseHTTPRequestHandler.setup(self)


    def do_GET(self):
        """ Process GET requests
            Call directly .do_for_all_methods()
        """
        self.do_for_all_methods()

    def do_POST(self):
        """ Process POST requests
            Call directly .do_for_all_methods()
        """
        self.do_for_all_methods()

    def do_PUT(self):
        """ Process PUT requests
            Call directly .do_for_all_methods()
        """
        self.do_for_all_methods()

    def do_OPTIONS(self):
        """ Process OPTIONS requests
            Call directly .do_for_all_methods()
        """
        self.do_for_all_methods()

    def do_for_all_methods(self):
        """ Create an object for each request. This object will process 
            the REST url
        """
        request = ProcessRequest(self.server.handler_params, self.path, \
                                 self.command, \
                                 self.headers, \
                                 self.send_response, \
                                 self.send_header, \
                                 self.end_headers, \
                                 self.wfile, \
                                 self.rfile, \
                                 self.send_http_response_ok, \
                                 self.send_http_response_error)
        request.do_for_all_methods()
        




######
# HTTP return
######

    def send_http_response_ok(self, data = ""):
        """ Send to browser a HTTP 200 responde
            200 is the code for "no problem"
            Send also json data
            @param data : json data to display
        """
        self.server.handler_params[0]._log.debug("Send HTTP header for OK")
        try:
            self.send_response(200)
        except BrokenPipe:
            # [Errno 32] Broken pipe : client closed connexion
            self.server.handler_params[0]._log.debug("It seems that socket has closed on client side (the browser may have change of the page displayed")
            return
        self.send_header('Content-type',  'application/json')
        self.send_header('Expires', '-1')
        self.send_header('Cache-control', 'no-cache')
        self.send_header('Content-Length', len(data.encode("utf-8")))
        self.end_headers()
        if data:
            # if big data, log only start of data
            if len(data) > 1000:
                self.server.handler_params[0]._log.debug("Send HTTP data : %s... [truncated because data too long for logs]" % data[0:1000].encode("utf-8"))
            # else log all data
            else:
                self.server.handler_params[0]._log.debug("Send HTTP data : %s" % data.encode("utf-8"))
            self.wfile.write(data.encode("utf-8"))


    def send_http_response_error(self, err_code, err_msg, jsonp, jsonp_cb):
        """ Send to browser a HTTP 200 responde
            200 is the code for "no problem" but we send error status in 
            json data, so we use 200 code
            Send also json data
            @param err_code : error code. 999 : generic error 
            @param err_msg : error description
            @param jsonp : True/False. True : use jsonp format
            @param jsonp_cb : if jsonp is True, name of callback to use 
                              in jsonp format
        """
        self.server.handler_params[0]._log.warning("Send HTTP header for ERROR : code=%s ; msg=%s" % (err_code, err_msg))
        json_data = JSonHelper("ERROR", err_code, err_msg)
        json_data.set_jsonp(jsonp, jsonp_cb)
        self.send_response(200)
        self.send_header('Content-type',    'text/html')
        self.send_header('Expires', '-1')
        self.send_header('Cache-control', 'no-cache')
        self.send_header('Content-Length', len(json_data.get().encode("utf-8")))
        self.end_headers()
        self.wfile.write(json_data.get())




################################################################################
class ProcessRequest():
    """ Class for processing a request
    """

######
# init namespace
######


    def __init__(self, handler_params, path, command, headers, \
                 send_response, \
                 send_header, \
                 end_headers, \
                 wfile, \
                 rfile, \
                 cb_send_http_response_ok, \
                 cb_send_http_response_error):
        """ Create shorter access : self.server.handler_params[0].* => self.*
            First processing on url given
            @param handler_params : parameters given to HTTPHandler
            @param path : path given to HTTP server : /base/area/... for example
            @param command : GET, POST, PUT, OPTIONS, etc
            @param cb_send_http_response_ok : callback for function
                                              REST.send_http_response_ok 
            @param cb_send_http_response_error : callback for function
                                              REST.send_http_response_error 
        """

        self.handler_params = handler_params
        self.path = path
        self.command = command
        self.headers = headers
        self.send_response = send_response
        self.send_header = send_header
        self.end_headers = end_headers
        self.copyfile = self.handler_params[0].copyfile
        self.wfile = wfile
        self.rfile = rfile
        self.send_http_response_ok = cb_send_http_response_ok
        self.send_http_response_error = cb_send_http_response_error

        # shorter access
        self._myxpl = self.handler_params[0]._myxpl
        self._log = self.handler_params[0]._log
        self._log_dm = self.handler_params[0]._log_dm
        self._xml_directory = self.handler_params[0]._xml_directory
        self.repo_dir = self.handler_params[0].repo_dir
        self.use_ssl = self.handler_params[0].use_ssl
        self.get_exception = self.handler_params[0].get_exception

        self._log.debug("Process request : init")

        self._queue_timeout =  self.handler_params[0]._queue_timeout
        self._queue_size =  self.handler_params[0]._queue_size
        self._queue_command_size =  self.handler_params[0]._queue_command_size
        self._queue_life_expectancy = self.handler_params[0]._queue_life_expectancy
        self._queue_event_size =  self.handler_params[0]._queue_event_size
        self._get_from_queue = self.handler_params[0]._get_from_queue
        self._put_in_queue = self.handler_params[0]._put_in_queue

        self._queue_system_list =  self.handler_params[0]._queue_system_list
        self._queue_system_detail =  self.handler_params[0]._queue_system_detail
        self._queue_system_start =  self.handler_params[0]._queue_system_start
        self._queue_system_stop =  self.handler_params[0]._queue_system_stop
        self._queue_command =  self.handler_params[0]._queue_command

        self._event_requests =  self.handler_params[0]._event_requests

        self.xml =  self.handler_params[0].xml
        self.xml_date =  self.handler_params[0].xml_date

        # global init
        self.jsonp = False
        self.jsonp_cb = ""

        # url processing
        #self.path = urllib.unquote(unicode(self.path))

        # replace password by "***". 
        path_without_passwd = re.sub("password/[^/]+/", "password/***/", self.path + "/")
        self._log.info("Request : %s" % path_without_passwd)

        # log data manipulation here
        if re.match(".*(add|update|del|set).*", path_without_passwd) is not None:
            self._log_dm.info("REQUEST=%s" % path_without_passwd)

        tab_url = self.path.split("?")
        self.path = tab_url[0]
        if len(tab_url) > 1:
            self.parameters = tab_url[1]
            self._parse_options()

        if self.path[-1:] == "/":
            self.path = self.path[0:len(self.path)-1]
        tab_path = self.path.split("/")

        # Get type of request : /command, /xpl-cmnd, /base, etc
        if len(tab_path) < 2:
            self.rest_type = None
            # Display an information json if no request done in do_for_all_methods
            return
        self.rest_type = tab_path[1].lower()
        if len(tab_path) > 2:
            self.rest_request = tab_path[2:]
        else:
            self.rest_request = []

        # DB Helper
        self._db = DbHelper()



    def do_for_all_methods(self):
        """ Process request
            This function call appropriate functions for processing path
        """
        if self.rest_type == "command":
            self.rest_command()
        elif self.rest_type == "stats":
            self.rest_stats()
        elif self.rest_type == "events":
            self.rest_events()
        elif self.rest_type == "xpl-cmnd":
            self.rest_xpl_cmnd()
        elif self.rest_type == "base":
            self.rest_base()
        elif self.rest_type == "plugin":
            self.rest_plugin()
        elif self.rest_type == "account":
            self.rest_account()
        elif self.rest_type == "queuecontent":
            self.rest_queuecontent()
        elif self.rest_type == "helper":
            self.rest_helper()
        elif self.rest_type == "testlongpoll":
            self.rest_testlongpoll()
        elif self.rest_type == "repo":
            self.rest_repo()
        elif self.rest_type == None:
            self.rest_status()
        else:
            self.send_http_response_error(999, "Type [" + str(self.rest_type) + \
                                          "] is not supported", \
                                          self.jsonp, self.jsonp_cb)


    def _parse_options(self):
        """ Process parameters : ...?param1=val1&param2=val2&....
        """
        self._log.debug("Parse request options : %s" % self.parameters)

        if self.parameters[-1:] == "/":
            self.parameters = self.parameters[0:len(self.parameters)-1]

        # for each debug option
        for opt in self.parameters.split("&"):
            self._log.debug("OPT : %s" % opt)
            tab_opt = opt.split("=")
            opt_key = tab_opt[0]
            if len(tab_opt) > 1:
                opt_value = tab_opt[1]
            else:
                opt_value = None

            # call json specific options
            if opt_key == "callback" and opt_value != None:
                self._log.debug("Option : jsonp mode")
                self.jsonp = True
                self.jsonp_cb = opt_value

            # call debug functions
            if opt_key == "debug-sleep" and opt_value != None:
                self._debug_sleep(opt_value)

            # name for PUT : /repo/put?filename=foo.txt
            if opt_key == "filename" and opt_value != None:
                self._put_filename = opt_value



    def _debug_sleep(self, duration):
        """ Sleep process for 15 seconds
        """
        self._log.debug("Start sleeping for " + str(duration))
        time.sleep(float(duration))
        self._log.debug("End sleeping")





######
# / processing
######

    def rest_status(self):
        json_data = JSonHelper("OK", 0, "REST server available")
        json_data.set_data_type("rest")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)

        # Description and parameters
        json_data.add_data({"Version" : REST_API_VERSION})
        json_data.add_data({"Description" : REST_DESCRIPTION})
        json_data.add_data({"SSL" : self.use_ssl})

        # Xml data
        xml_info = ""
        for key in self.xml:
            xml_info += key + ", "
        xml_info = xml_info[0:len(xml_info)-2]
        json_data.add_data({"/command : XML files loaded" : xml_info})
        json_data.add_data({"/command : XML files last load" : self.xml_date})

        # Queues stats

        json_data.add_data({"Queue 'system_list' usage" : "%s/%s" \
            % (self._queue_system_list.qsize(), int(self._queue_size))})
        json_data.add_data({"Queue 'system_detail' usage" : "%s/%s" \
            % (self._queue_system_detail.qsize(), int(self._queue_size))})
        json_data.add_data({"Queue 'system_start' usage" : "%s/%s" \
            % (self._queue_system_start.qsize(), int(self._queue_size))})
        json_data.add_data({"Queue 'system_stop' usage" : "%s/%s" \
            % (self._queue_system_stop.qsize(), int(self._queue_size))})
        json_data.add_data({"Queue 'command' usage" : "%s/%s" \
            % (self._queue_command.qsize(), int(self._queue_command_size))})

        # Events stats
        json_data.add_data({"Events requests count" : self._event_requests.count()})
        json_data.add_data({"Events queues max size count" : int(self._queue_event_size)})
        json_data.add_data({"Events requests" : self._event_requests.list()})

        self.send_http_response_ok(json_data.get())



######
# /command processing
######

    def rest_command(self):
        """ Process /command url
            - decode request
            - call a xml parser for the technology (self.rest_request[0])
           - send appropriate xPL message on network
        """
        self._log.debug("Process /command")

        ### Check url length
        if len(self.rest_request) < 3:
            json_data = JSonHelper("ERROR", 999, "Url too short for /command")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())
            return

        ### Get parameters
        techno = self.rest_request[0]
        address = self.rest_request[1]
        command = self.rest_request[2]
        if len(self.rest_request) > 3:
            params = self.rest_request[3:]
        else:
            params = None

        self._log.debug("Techno  : %s" % techno)
        self._log.debug("Address : %s" % address)
        self._log.debug("Command : %s" % command)
        self._log.debug("Params  : %s" % str(params))

        ### Get message 
        message = self._rest_command_get_message(techno, address, command, params)

        ### Get listener
        (schema, xpl_type, filters) = self._rest_command_get_listener(techno, address, command, params)

        ### Send xpl message
        self._myxpl.send(XplMessage(message))

        ### Wait for answer
        # get xpl message from queue
        try:
            self._log.debug("Command : wait for answer...")
            msg_cmd = self._get_from_queue(self._queue_command, filters)
        except Empty:
            self._log.debug("Command (%s, %s, %s, %s) : no answer" % (techno, address, command, params))
            json_data = JSonHelper("ERROR", 999, "No data or timeout on getting command response")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("response")
            self.send_http_response_ok(json_data.get())
            return

        self._log.debug("Command : message received : %s" % str(msg_cmd))

        ### REST processing finished and OK
        json_data = JSonHelper("OK")
        json_data.set_data_type("response")
        json_data.add_data({"xpl" : str(msg_cmd)})
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())




    def _rest_command_get_message(self, techno, address, command, params):
        ref = "%s-%s.xml" % (techno,command)
        try:
            xml_data = self.xml[ref]
        except KeyError:
            self.send_http_response_error(999, "No xml file for '%s'" % ref, \
                                          self.jsonp, self.jsonp_cb)
            return

        ### Check xml validity
        if xml_data.getElementsByTagName("technology")[0].attributes.get("id").value != techno:
            self.send_http_response_error(999, "'technology' attribute in xml file must be '%s'" % techno, \
                                          self.jsonp, self.jsonp_cb)
            return
        if xml_data.getElementsByTagName("command")[0].attributes.get("name").value != command:
            self.send_http_response_error(999, "'command' attribute in xml file must be '%s'" % command, \
                                          self.jsonp, self.jsonp_cb)
            return

        ### Get only <command...> part
        xml_command = xml_data.getElementsByTagName("command")[0]

        ### Get data from xml
        # Schema
        schema = xml_command.getElementsByTagName("schema")[0].firstChild.nodeValue
        # command key name 
        command_key = xml_command.getElementsByTagName("command-key")[0].firstChild.nodeValue
        #address key name (device)
        address_key = xml_command.getElementsByTagName("address-key")[0].firstChild.nodeValue
        # real command value in xpl message
        command_xpl_value = xml_command.getElementsByTagName("command-xpl-value")[0].firstChild.nodeValue

        # Parameters
        #get and count parameters in xml file
        parameters = xml_command.getElementsByTagName("parameters")[0]
        count_parameters = len(parameters.getElementsByTagName("parameter"))
        #do the association between url and xml
        parameters_value = {}
        for param in parameters.getElementsByTagName("parameter"):
            key = param.attributes.get("key").value
            loc = param.attributes.get("location")
            static_value = param.attributes.get("value")
            if static_value is None:
                if loc is None:
                    loc.value = 0
                value = params[int(loc.value) - 1]
            else:
                value = static_value.value
            parameters_value[key] = value

        ### Create xpl message
        msg = """xpl-cmnd
{
hop=1
source=xpl-rest.domogik
target=*
}
%s
{
%s=%s
%s=%s
""" % (schema, address_key, address, command_key, command_xpl_value)
        for m_param in parameters_value.keys():
            msg += "%s=%s\n" % (m_param, parameters_value[m_param])
        msg += "}"
        return msg




    def _rest_command_get_listener(self, techno, address, command, params):
        xml_data = self.xml["%s-%s.xml" % (techno,command)]

        ### Get only <command...> part
        # nothing to do, tests have be done in get_command

        xml_listener = xml_data.getElementsByTagName("listener")[0]

        ### Get data from xml
        # Schema
        schema = xml_listener.getElementsByTagName("schema")[0].firstChild.nodeValue
        # xpl type
        xpl_type = xml_listener.getElementsByTagName("xpltype")[0].firstChild.nodeValue

        # Filters
        filters = xml_listener.getElementsByTagName("filter")[0]
        filters_value = {}
        for filter in filters.getElementsByTagName("key"):
            name = filter.attributes.get("name").value
            value = filter.attributes.get("value").value
            if value == "@address@":
                value = address
            filters_value[name] = value

        return schema, xpl_type, filters_value




######
# /stats processing
######

    def rest_stats(self):
        """ Get stats in database
            - Decode and check URL format
            - call the good fonction to get stats from database
        """
        self._log.debug("Process stats request")
        # parameters initialisation
        self.parameters = {}

        # Check url length
        if len(self.rest_request) < 3:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        device_id = self.rest_request[0]
        key = self.rest_request[1]

        ### all ######################################
        if self.rest_request[2] == "all":
            self._rest_stats_all(device_id, key)

        ### latest ###################################
        elif self.rest_request[2] == "latest":
            self._rest_stats_last(device_id, key)

        ### last #####################################
        elif self.rest_request[2] == "last":
            if len(self.rest_request) < 4:
                self.send_http_response_error(999, "Wrong syntax for %s" % self.rest_request[2], self.jsonp, self.jsonp_cb)
                return
            self._rest_stats_last(device_id, key, int(self.rest_request[3]))

        ### from #####################################
        elif self.rest_request[2] == "from":
            if len(self.rest_request) < 4:
                self.send_http_response_error(999, "Wrong syntax for %s" % self.rest_request[2], self.jsonp, self.jsonp_cb)
                return
            offset = 2
            if self.set_parameters(offset):
                self._rest_stats_from(device_id, key)
            else:
                self.send_http_response_error(999, "Error in parameters", \
                                              self.jsonp, self.jsonp_cb)


        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return



    def _rest_stats_all(self, device_id, key):
        """ Get all values for device/key in database
             @param device_id : device id
             @param key : key for device
        """
        # TODO

        json_data = JSonHelper("OK")
        json_data.set_data_type("stats")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        for data in self._db.list_device_stats(device_id):
            # TODO : filter by key
            json_data.add_data(data)
        self.send_http_response_ok(json_data.get())



    def _rest_stats_last(self, device_id, key, num = 1):
        """ Get the last values for device/key in database
             @param device_id : device id
             @param key : key for device
             @param num : number of data to return
        """

        json_data = JSonHelper("OK")
        json_data.set_data_type("stats")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        for data in self._db.list_last_n_stats_of_device_by_key(key, device_id,  num):
            json_data.add_data(data)
        self.send_http_response_ok(json_data.get())



    def _rest_stats_from(self, device_id, key):
        """ Get the values for device/key in database for an start time to ...
             @param device_id : device id
             @param key : key for device
             @param others params : will be get with get_parameters (dynamic params)
        """

        st_from = self.get_parameters("from")
        st_to = self.get_parameters("to")

        json_data = JSonHelper("OK")
        json_data.set_data_type("stats")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        for data in self._db.list_stats_of_device_between_by_key(key, device_id, st_from, st_to):
            json_data.add_data(data)
        self.send_http_response_ok(json_data.get())
    



######
# /events processing
######

    def rest_events(self):
        """ Events processing
        """
        self._log.debug("Process events request")

        # Check url length
        if len(self.rest_request) < 2:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### request  ######################################
        if self.rest_request[0] == "request":

            #### new
            if self.rest_request[1] == "new":
                new_idx = 2
                device_id_list = []
                while new_idx < len(self.rest_request):
                    try:
                        device_id_list.append(int(self.rest_request[new_idx]))
                    except ValueError:
                        self.send_http_response_error(999, "Bad value for device id '%s'" % self.rest_request[new_idx], self.jsonp, self.jsonp_cb)
                        return
                        
                    new_idx += 1
                if new_idx == 2:
                    self.send_http_response_error(999, "No device id given", self.jsonp, self.jsonp_cb)
                    return
                self._rest_events_request_new(device_id_list)

            #### get
            elif self.rest_request[1] == "get" and len(self.rest_request) == 3:
                self._rest_events_request_get(self.rest_request[2])

            #### free
            elif self.rest_request[1] == "free" and len(self.rest_request) == 3:
                self._rest_events_request_free(self.rest_request[2])

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return

        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return



    def _rest_events_request_new(self, device_id_list):
        """ Create new event request and send data for event
            @param device_id_list : list of devices to check for events
        """
        ticket_id = self._event_requests.new(device_id_list)
        data = self._event_requests.get(ticket_id)
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("event")
        json_data.add_data(data)
        self.send_http_response_ok(json_data.get())




    def _rest_events_request_get(self, ticket_id):
        """ Get data from event associated to ticket id
            @param ticket_id : ticket id
        """
        data = self._event_requests.get(ticket_id)
        if data == False:
            json_data = JSonHelper("ERROR", 999, "Error in getting event in queue")
        else:
            json_data = JSonHelper("OK")
            json_data.set_data_type("event")
            json_data.add_data(data)
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())




    def _rest_events_request_free(self, ticket_id):
        """ Free event queue for ticket id
            @param ticket_id : ticket id
        """
        if self._event_requests.free(ticket_id):
            json_data = JSonHelper("OK")
        else:
            json_data = JSonHelper("ERROR", 999, "Error when trying to free queue for event")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())

######
# /xpl-cmnd processing
######

    def rest_xpl_cmnd(self):
        """ Send xPL message given in REST url
            - Decode and check URL
            - Send message
        """
        self._log.debug("Send xpl message")

        if len(self.rest_request) == 0:
            self.send_http_response_error(999, "Schema not given", self.jsonp, self.jsonp_cb)
            return
        self.xpl_cmnd_schema = self.rest_request[0]

        # Init xpl message
        message = XplMessage()
        message.set_type('xpl-cmnd')
        message.set_schema(self.xpl_cmnd_schema)
  
        iii = 0
        for val in self.rest_request:
            # We pass target and schema
            if iii > 0:
                # Parameter
                if iii % 2 == 1:
                    param = val
                # Value
                else:
                    value = val
                    message.add_data({param : value})
            iii = iii + 1

        # no parameters
        if iii == 1:
            self.send_http_response_error(999, "No parameters specified", self.jsonp, self.jsonp_cb)
            return
        # no value for last parameter
        if iii % 2 == 0:
            self.send_http_response_error(999, "Value missing for last parameter", self.jsonp, self.jsonp_cb)
            return

        self._log.debug("Send message : %s" % str(message))
        self._myxpl.send(message)

        # REST processing finished and OK
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())




######
# /base processing
######

    def rest_base(self):
        """ Get data in database
            - Decode and check URL format
            - call the good fonction to get data from database
        """
        self._log.debug("Process base request")
        # parameters initialisation
        self.parameters = {}

        # Check url length
        if len(self.rest_request) < 2:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### area #####################################
        if self.rest_request[0] == "area":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_area_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_base_area_list(area_id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_area_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", \
                                                  self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_area_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", \
                                                  self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_area_del(area_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return

        ### room #####################################
        elif self.rest_request[0] == "room":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_room_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_base_room_list(room_id=self.rest_request[3])
                    elif self.rest_request[2] == "by-area":
                        self._rest_base_room_list(area_id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_room_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", \
                                                  self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_room_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", \
                                                  self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_room_del(room_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return

        ### ui_config ################################
        elif self.rest_request[0] == "ui_config":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_ui_item_config_list()
                elif len(self.rest_request) >= 3 and len(self.rest_request) <=4:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 5:
                    if self.rest_request[2] == "by-key":
                        self._rest_base_ui_item_config_list(name = self.rest_request[3], key = self.rest_request[4])
                    elif self.rest_request[2] == "by-reference":
                        self._rest_base_ui_item_config_list(name = self.rest_request[3], reference = self.rest_request[4])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 6:
                    if self.rest_request[2] == "by-element":
                        self._rest_base_ui_item_config_list(name = self.rest_request[3], reference = self.rest_request[4], key = self.rest_request[5])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### set
            elif self.rest_request[1] == "set":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_ui_item_config_set()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### delete
            elif self.rest_request[1] == "del":
                #offset = 2
                #if self.set_parameters(offset):
                #    self._rest_base_ui_item_config_del()
                #else:
                #    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

                if len(self.rest_request) !=5 and len(self.rest_request) != 6:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 5:
                    if self.rest_request[2] == "by-key":
                        self._rest_base_ui_item_config_del(name = self.rest_request[3], key = self.rest_request[4])
                    elif self.rest_request[2] == "by-reference":
                        self._rest_base_ui_item_config_del(name = self.rest_request[3], reference = self.rest_request[4])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 6:
                    if self.rest_request[2] == "by-element":
                        self._rest_base_ui_item_config_del(name = self.rest_request[3], reference = self.rest_request[4], key = self.rest_request[5])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### device_usage #############################
        elif self.rest_request[0] == "device_usage":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_usage_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-name":
                        self._rest_base_device_usage_list(self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_usage_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_usage_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_device_usage_del(du_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### device_type ##############################
        elif self.rest_request[0] == "device_type":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_type_list()
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_area_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_area_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_area_del(dt_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### feature ######################
        elif self.rest_request[0] == "feature":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 4 and self.rest_request[2] == "by-id":
                    self._rest_base_feature_list(id = self.rest_request[3])
                elif len(self.rest_request) == 4 and self.rest_request[2] == "by-device_id":
                    self._rest_base_feature_list(device_id = self.rest_request[3])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return



        ### device technology ##########################
        elif self.rest_request[0] == "device_technology":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_technology_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_base_device_technology_list(id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_technology_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_technology_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_device_technology__del(dt_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return






        ### device #####################################
        elif self.rest_request[0] == "device":
            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_list()
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_device_del(id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### feature_association ######################
        elif self.rest_request[0] == "feature_association":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_feature_association_list()
                elif len(self.rest_request) == 3:
                    if self.rest_request[2] == "by-house":
                        self._rest_base_feature_association_list_by_house()
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                      self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 4:
                    if self.rest_request[2] == "by-area":
                        self._rest_base_feature_association_list_by_area(self.rest_request[3])
                    elif self.rest_request[2] == "by-room":
                        self._rest_base_feature_association_list_by_room(self.rest_request[3])
                    elif self.rest_request[2] == "by-feature":
                        self._rest_base_feature_association_list_by_feature(self.rest_request[3])
                    #elif self.rest_request[2] == "by-device":
                    #    self._rest_base_feature_association_list_by_device(self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                      self.jsonp, self.jsonp_cb)
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_feature_association_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 4 and self.rest_request[2] == "id":
                    self._rest_base_feature_association_del(id=self.rest_request[3])
                elif len(self.rest_request) == 4 and self.rest_request[2] == "feature_id":
                    self._rest_base_feature_association_del(feature_id=self.rest_request[3])
                elif len(self.rest_request) == 6 and self.rest_request[2] == "association_type" and self.rest_request[4] == "association_id":
                    self._rest_base_feature_association_del(association_type=self.rest_request[3], 
                                                            association_id=self.rest_request[5])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return



        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return



    def set_parameters(self, offset):
        """ define parameters as key => value
            @param offset : number of item to pass before getting key/values in REST request
            @return value if OK. False if no parameters or missing value
        """
        iii = 0
        while offset + iii < len(self.rest_request):
            key = self.rest_request[offset + iii]
            if offset + iii + 1 < len(self.rest_request):
                value = self.rest_request[offset + iii + 1]
            else:
                # wrong number of arguments
                return False
            # specific process for False/True
            #if value == "False" or value == "false":
            #    self.parameters[key] = False
            #elif value == "True" or value == "true":
            #    self.parameters[key] = True
            #else:
            #    self.parameters[key] = value
            self.parameters[key] = value
            iii += 2
        # no parameters
        if iii == 0:
            return False
        # ok
        else:
            return True



    def get_parameters(self, name):
        """ Getter for parameters. If parameter doesn't exist, return None
            @param name : name of parameter to get
            @return parameter value or None if parameter doesn't exist
        """
        try:
            data = self.parameters[name]
            if data == None:
                return None
            else:
                #return unicode(urllib.unquote(data), sys.stdin.encoding)
                return unicode(urllib.unquote(data), "UTF-8")
        except KeyError:
            return None



    def to_date(self, date):
        """ Transform YYYYMMDD date in datatime object
                      YYYYMMDD-HHMM ....
            @param date : date
        """
        if date == None:
            return None
        my_date = None
        if len(date) == 8:  # YYYYMDD
            year = int(date[0:4])
            month = int(date[4:6])
            day = int(date[6:8])
            try:
                my_date = datetime.date(year, month, day)
            except:
                self.send_http_response_error(999, self.get_exception(), self.jsonp, self.jsonp_cb)
        elif len(date) == 13:  # YYYYMMDD-HHMM
            year = int(date[0:4])
            month = int(date[4:6])
            day = int(date[6:8])
            hour = int(date[9:11])
            minute = int(date[11:13])
            try:
                my_date = datetime.datetime(year, month, day, hour, minute)
            except:
                self.send_http_response_error(999, self.get_exception(), self.jsonp, self.jsonp_cb)
        else:
            self.send_http_response_error(999, "Bad date format (YYYYMMDD or YYYYMMDD-HHMM required", self.jsonp, self.jsonp_cb)
        return my_date




######
# /base/area processing
######

    def _rest_base_area_list(self, area_id = None):
        """ list areas
            @param area_id : id of area
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("area")
        if area_id == None:
            for area in self._db.list_areas():
                json_data.add_data(area)
        else:
            area = self._db.get_area_by_id(area_id)
            if area is not None:
                json_data.add_data(area)
        self.send_http_response_ok(json_data.get())




    def _rest_base_area_add(self):
        """ add areas
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("area")
        try:
            area = self._db.add_area(self.get_parameters("name"), self.get_parameters("description"))
            json_data.add_data(area)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




    def _rest_base_area_update(self):
        """ update areas
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("area")
        try:
            area = self._db.update_area(self.get_parameters("id"), self.get_parameters("name"), \
                                        self.get_parameters("description"))
            json_data.add_data(area)
        except:
            # TODO make a function to get arranged trace and use it everywhere :)
            json_data.set_error(code = 999, description = str(traceback.format_exc()).replace('"', "'").replace('\n', '      '))
        self.send_http_response_ok(json_data.get())




    def _rest_base_area_del(self, area_id=None):
        """ delete areas
            @param area_id : id of area
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("area")
        try:
            area = self._db.del_area(area_id)
            json_data.add_data(area)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



######
# /base/room processing
######

    def _rest_base_room_list(self, room_id = None, area_id = None):
        """ list rooms
            @param room_id : id of room
            @param area_id : id of area
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("room")
        try:
            if room_id == None and area_id == None:
                for room in self._db.list_rooms():
                    json_data.add_data(room)
            elif room_id != None:
                room = self._db.get_room_by_id(room_id)
                if room is not None:
                    json_data.add_data(room)
            elif area_id != None:
                if area_id == "":
                    area_id = None
                for room in self._db.get_all_rooms_of_area(area_id):
                    json_data.add_data(room)
            self.send_http_response_ok(json_data.get())
        except:
            self._log.error("Exception : %s" % traceback.format_exc())


    def _rest_base_room_add(self):
        """ add rooms
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("room")
        try:
            room = self._db.add_room(self.get_parameters("name"), self.get_parameters("area_id"), \
                                     self.get_parameters("description"))
            json_data.add_data(room)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_base_room_update(self):
        """ update rooms
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("room")
        try:
            room = self._db.update_room(self.get_parameters("id"), self.get_parameters("name"), \
                                        self.get_parameters("area_id"), self.get_parameters("description"))
            json_data.add_data(room)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_base_room_del(self, room_id=None):
        """ delete rooms
            @param room_id : room id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("room")
        try:
            room = self._db.del_room(room_id)
            json_data.add_data(room)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


######
# /base/ui_config processing
######

    def _rest_base_ui_item_config_list(self, name = None, reference = None, key = None):
        """ list ui_item_config
            @param name : ui item config name
            @param reference : ui item config reference
            @param key : ui item config key
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("ui_config")
        if name == None and reference == None and key == None:
            for ui_item_config in self._db.list_all_ui_item_config():
                json_data.add_data(ui_item_config)
        elif name != None and reference != None:
            if key == None:
                # by-reference
                for ui_item_config in self._db.list_ui_item_config_by_ref(ui_item_name = name, ui_item_reference = reference):
                    json_data.add_data(ui_item_config)
            else:
                # by-key
                for ui_item_config in self._db.list_ui_item_config_by_key(ui_item_name = name, ui_item_key= key):
                    json_data.add_data(ui_item_config)
        elif name != None and key != None and reference != None:
            # by-element
            ui_item_config = self._db.get_ui_item_config(self, ui_item_name = name, \
                                                         ui_item_reference = reference, ui_key = key)
            if ui_item_config is not None:
                json_data.add_data(ui_item_config)
        self.send_http_response_ok(json_data.get())



    def _rest_base_ui_item_config_set(self):
        """ set ui_item_config (add if it doesn't exists, update else)
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("ui_config")
        try:
            ui_item_config = self._db.set_ui_item_config(self.get_parameters("name"), \
                                                         self.get_parameters("reference"), \
                                                         self.get_parameters("key"), \
                                                         self.get_parameters("value"))
            json_data.add_data(ui_item_config)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    #def _rest_base_ui_item_config_del(self):
    #    """ del ui_item_config
    #    """
    #    json_data = JSonHelper("OK")
    #    json_data.set_jsonp(self.jsonp, self.jsonp_cb)
    #    json_data.set_data_type("ui_config")
    #    try:
    #        for ui_item_config in self._db.delete_ui_item_config( \
    #                           ui_name = self.get_parameters("name"), \
    #                           ui_reference = self.get_parameters("reference"),\
    #                           ui_key = self.get_parameters("key")):
    #            json_data.add_data(ui_item_config)
    #    except:
    #        json_data.set_error(code = 999, description = self.get_exception())
    #    self.send_http_response_ok(json_data.get())

    def _rest_base_ui_item_config_del(self, name = None, reference = None, key = None):
        """ delete ui_item_config
            @param name : ui item config name
            @param reference : ui item config reference
            @param key : ui item config key
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("ui_config")
        for ui_item_config in self._db.delete_ui_item_config(ui_item_name = name,
                                                             ui_item_reference = reference,
                                                             ui_item_key = key):
            json_data.add_data(ui_item_config)
        self.send_http_response_ok(json_data.get())



######
# /base/device_usage processing
######

    def _rest_base_device_usage_list(self, name = None):
        """ list device usages
            @param name : name of device usage
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        if name == None:
            for device_usage in self._db.list_device_usages():
                json_data.add_data(device_usage)
        else:
            device_usage = self._db.get_device_usage_by_name(name)
            if device_usage is not None:
                json_data.add_data(device_usage)
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_usage_add(self):
        """ add device_usage
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        try:
            device_usage = self._db.add_device_usage(self.get_parameters("name"), \
                                                     self.get_parameters("description"), \
                                                     self.get_parameters("default_options"))
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_usage_update(self):
        """ update device usage
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        try:
            device_usage = self._db.update_device_usage(self.get_parameters("id"), \
                                                        self.get_parameters("name"), \
                                                        self.get_parameters("description"), \
                                                        self.get_parameters("default_options"))
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




    def _rest_base_device_usage_del(self, du_id=None):
        """ delete device usage
            @param du_id : device usage id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_usage")
        try:
            device_usage = self._db.del_device_usage(du_id)
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



######
# /base/device_type processing
######

    def _rest_base_device_type_list(self):
        """ list device types
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        for device_type in self._db.list_device_types():
            json_data.add_data(device_type)
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_type_add(self):
        """ add device type
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        try:
            device_type = self._db.add_device_type(self.get_parameters("name"), \
                                                   self.get_parameters("technology_id"), \
                                                   self.get_parameters("description"))
            json_data.add_data(device_type)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_type_update(self):
        """ update device_type
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        try:
            area = self._db.update_device_type(self.get_parameters("id"), \
                                               self.get_parameters("name"), \
                                               self.get_parameters("technology_id"), \
                                               self.get_parameters("description"))
            json_data.add_data(area)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




    def _rest_base_device_type_del(self, dt_id=None):
        """ delete device_type
            @param dt_id : device type id to delete
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_type")
        try:
            device_type = self._db.del_device_type(dt_id)
            json_data.add_data(device_type)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




######
# /base/feature processing
######

    def _rest_base_feature_list(self, id = None, device_id = None):
        """ list device type features
            @param id : feature id
            @param device_id : id of device 
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature")
        if id != None:
            feature = self._db.get_device_feature_by_id(id)
            json_data.add_data(feature)
        elif device_id != None:
            for feature in self._db.list_device_features_by_device_id(device_id):
                json_data.add_data(feature)
        self.send_http_response_ok(json_data.get())





######
# /base/device_technology processing
######

    def _rest_base_device_technology_list(self, id = None):
        """ list device technologies
            @param name : device technology name
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        if id == None:
            for device_technology in self._db.list_device_technologies():
                json_data.add_data(device_technology)
        else:
            device_technology = self._db.get_device_technology_by_id(id)
            if device_technology is not None:
                json_data.add_data(device_technology)
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_technology_add(self):
        """ add device technology
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        try:
            device_technology = self._db.add_device_technology(self.get_parameters("name"), \
                                                                  self.get_parameters("description"))
            json_data.add_data(device_technology)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_technology_update(self):
        """ update device technology
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        try:
            device_technology = self._db.update_device_technology(self.get_parameters("id"), \
                                                                  self.get_parameters("name"), \
                                                                  self.get_parameters("description"))
            json_data.add_data(device_technology)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_technology_del(self, dt_id=None):
        """ delete device technology
            @param dt_id : device tehcnology id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        try:
            device_technology = self._db.del_device_technology(dt_id)
            json_data.add_data(device_technology)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())






######
# /base/device processing
######

    def _rest_base_device_list(self):
        """ list devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        for device in self._db.list_devices():
            json_data.add_data(device)
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_add(self):
        """ add devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        try:
            device = self._db.add_device(self.get_parameters("name"), \
                                         self.get_parameters("address"), \
                                         self.get_parameters("type_id"), \
                                         self.get_parameters("usage_id"), \
                                         self.get_parameters("description"), \
                                         self.get_parameters("reference"))
            json_data.add_data(device)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_update(self):
        """ update devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        try:
            device = self._db.update_device(self.get_parameters("id"), \
                                         self.get_parameters("name"), \
                                         self.get_parameters("address"), \
                                         self.get_parameters("usage_id"), \
                                         self.get_parameters("description"), \
                                         self.get_parameters("reference"))
            json_data.add_data(device)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_del(self, id):
        """ delete device 
            @param id : device id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        try:
            device = self._db.del_device(id)
            json_data.add_data(device)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())





######
# /base/feature_association processing
######

    def _rest_base_feature_association_list(self):
        """ list feature association
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature_association")
        for ass in self._db.list_device_feature_associations():
            json_data.add_data(ass)
        self.send_http_response_ok(json_data.get())



    def _rest_base_feature_association_list_by_house(self):
        """ list feature association by house
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature_association")
        for ass in self._db.list_device_feature_associations_by_house():
            json_data.add_data(ass)
        self.send_http_response_ok(json_data.get())



    def _rest_base_feature_association_list_by_area(self, id):
        """ list feature association by area
            @param id : id of element
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature_association")
        for ass in self._db.list_device_feature_associations_by_area_id(id):
            json_data.add_data(ass)
        self.send_http_response_ok(json_data.get())



    def _rest_base_feature_association_list_by_room(self, id):
        """ list feature association by room
            @param id : id of element
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature_association")
        for ass in self._db.list_device_feature_associations_by_room_id(id):
            json_data.add_data(ass)
        self.send_http_response_ok(json_data.get())



    def _rest_base_feature_association_list_by_feature(self, id):
        """ list feature association by feature
            @param id : id of element
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature_association")
        for ass in self._db.list_device_feature_associations_by_feature_id(id):
            json_data.add_data(ass)
        self.send_http_response_ok(json_data.get())



    #def _rest_base_feature_association_list_by_device(self, id):
    #    """ list feature association by device
    #        @param id : id of element
    #    """
    #    json_data = JSonHelper("OK")
    #    json_data.set_jsonp(self.jsonp, self.jsonp_cb)
    #    json_data.set_data_type("feature_association")
    #    for ass in self._db.list_device_feature_associations_by_device_id(id):
    #        json_data.add_data(ass)
    #    self.send_http_response_ok(json_data.get())




    def _rest_base_feature_association_add(self):
        """ add feature_association
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature_association")
        try:
            ass = self._db.add_device_feature_association( self.get_parameters("feature_id"), \
                                                               self.get_parameters("association_type"), \
                                                               self.get_parameters("association_id"))
            json_data.add_data(ass)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())




    def _rest_base_feature_association_del(self, id = None, 
                                          feature_id = None,
                                          association_type = None,
                                          association_id = None):
        """ delete feature association
            @param id : association id
            @param feature_id : feature id
            @param association_type : house, area, room...
            @param association_id : area id, room id, etc
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("feature_association")
        if id != None:
            try:
                fa = self._db.del_device_feature_association(id)
                json_data.add_data(fa)
            except:
                json_data.set_error(code = 999, description = self.get_exception())
        elif feature_id != None:
            try:
                for fa in self._db.del_device_feature_association_by_device_feature_id(feature_id):
                    json_data.add_data(fa)
            except:
                json_data.set_error(code = 999, description = self.get_exception())
        elif association_type != None:
            try:
                for fa in self._db.del_device_feature_association_by_place(association_id, association_type):
                    json_data.add_data(fa)
            except:
                json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())





######
# /plugin processing
######

    def rest_plugin(self):
        """ /plugin processing
        """
        self._log.debug("Plugin action")

        # parameters initialisation
        self.parameters = {}

        if len(self.rest_request) < 1:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### list ######################################
        if self.rest_request[0] == "list":

            if len(self.rest_request) == 1:
                self._rest_plugin_list()
            elif len(self.rest_request) == 2:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
            else:
                if self.rest_request[1] == "by-name":
                    self._rest_plugin_list(name=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                              self.jsonp, self.jsonp_cb)
                    return

        ### detail ####################################
        elif self.rest_request[0] == "detail":
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_plugin_detail(self.rest_request[1])


        ### start #####################################
        elif self.rest_request[0] == "start":
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_plugin_start_stop(plugin =  self.rest_request[1], \
                                   command = "start")

        ### stop ######################################
        elif self.rest_request[0] == "stop":
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_plugin_start_stop(plugin =  self.rest_request[1], \
                                   command = "stop")


        ### plugin config ############################
        elif self.rest_request[0] == "config":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_plugin_config_list()
                elif len(self.rest_request) == 4 or len(self.rest_request) == 6:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 5:
                    if self.rest_request[2] == "by-name":
                        self._rest_plugin_config_list(name=self.rest_request[3], hostname=self.rest_request[4])
                elif len(self.rest_request) == 7:
                    if self.rest_request[2] == "by-name" and self.rest_request[5] == "by-key":
                        self._rest_plugin_config_list(name = self.rest_request[3], hostname=self.rest_request[4], key = self.rest_request[6])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### set
            elif self.rest_request[1] == "set":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_plugin_config_set()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)


            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 4:
                    self._rest_plugin_config_del(name=self.rest_request[2], hostname=self.rest_request[3])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)


            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return

        ### others ####################################
        else:
            self.send_http_response_error(999, "Bad operation for /plugin", self.jsonp, self.jsonp_cb)
            return



    def _rest_plugin_list(self, name = None, host = gethostname()):
        """ Send a xpl message to manager to get plugin list
            Display this list as json
            @param name : name of plugin
        """
        self._log.debug("Plugin : ask for plugin list on %s." % host)

        ### Send xpl message to get list
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.system")
        message.add_data({"command" : "list"})
        # TODO : ask for good host
        message.add_data({"host" : gethostname()})
        self._myxpl.send(message)
        self._log.debug("Plugin : send message : %s" % str(message))

        ### Wait for answer
        # get xpl message from queue
        try:
            self._log.debug("Plugin : wait for answer...")
            message = self._get_from_queue(self._queue_system_list)
        except Empty:
            self._log.debug("Plugin : no answer")
            json_data = JSonHelper("ERROR", 999, "No data or timeout on getting plugin list")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("plugin")
            self.send_http_response_ok(json_data.get())
            return

        self._log.debug("Plugin : message received : %s" % str(message))

        # process message
        cmd = message.data['command']
        host = message.data["host"]
    

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("plugin")

        idx = 0
        loop_again = True
        while loop_again:
            try:
                data = message.data["plugin"+str(idx)].split(",")
                if name == None or name == data[0]:
                    json_data.add_data({"name" : data[0], "technology" : data[1], "description" : data[3], "status" : data[2], "host" : host})
                idx += 1
            except:
                loop_again = False

        self.send_http_response_ok(json_data.get())



    def _rest_plugin_detail(self, name, host = gethostname()):
        """ Send a xpl message to manager to get plugin list
            Display this list as json
            @param name : name of plugin
        """
        self._log.debug("Plugin : ask for plugin detail : %s on %s." % (name, host))

        ### Send xpl message to get detail
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.system")
        message.add_data({"command" : "detail"})
        message.add_data({"plugin" : name})
        # TODO : ask for good host
        message.add_data({"host" : host})
        self._myxpl.send(message)
        self._log.debug("Plugin : send message : %s" % str(message))

        ### Wait for answer
        # get xpl message from queue
        try:
            self._log.debug("Plugin : wait for answer...")
            # in filter, "%" means, that we check for something starting with name
            message = self._get_from_queue(self._queue_system_detail, filter = {"command" : "detail", "plugin" : name + "%"})
        except Empty:
            json_data = JSonHelper("ERROR", 999, "No data or timeout on getting plugin detail for %s" % name)
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("plugin")
            self.send_http_response_ok(json_data.get())
            return

        self._log.debug("Plugin : message received : %s" % str(message))

        # process message
        cmd = message.data['command']
        host = message.data["host"]
        name = message.data["plugin"]
        try:
            error = message.data["error"]
            self.send_http_response_error(999, "Error on detail request : %s" % error,
                                          self.jsonp, self.jsonp_cb)
            return
        except:
            # no error, everything is alright
            pass 
        description = message.data["description"]
        technology = message.data["technology"]
        status = message.data["status"]
        version = message.data["version"]
        documentation = message.data["documentation"]
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("plugin")

        idx = 0
        loop_again = True
        config_data = []
        while loop_again:
            try:
                data_conf = message.data["config"+str(idx)].split(",")
                config_data.append({"id" : idx+1, "key" : data_conf[0], "type" : data_conf[1], "description" : data_conf[2], "default" : data_conf[3]})
                idx += 1
            except:
                loop_again = False

        json_data.add_data({"name" : name, "technology" : technology, "description" : description, "status" : status, "host" : host, "version" : version, "documentation" : documentation, "configuration" : config_data})
        self.send_http_response_ok(json_data.get())




    def _rest_plugin_start_stop(self, command, host = gethostname(), plugin = None, force = 0):
        """ Send start xpl message to manager
            Then, listen for a response
            @param host : host to which we send command
            @param plugin : name of plugin
            @param force : force (or not) action. 0/1. 1 : force
        """
        self._log.debug("Plugin : ask for %s %s on %s (force=%s)" % (command, plugin, host, force))

        ### Send xpl message
        cmd_message = XplMessage()
        cmd_message.set_type("xpl-cmnd")
        cmd_message.set_schema("domogik.system")
        cmd_message.add_data({"command" : command})
        cmd_message.add_data({"host" : host})
        cmd_message.add_data({"plugin" : plugin})
        cmd_message.add_data({"force" : force})
        self._myxpl.send(cmd_message)
        self._log.debug("Plugin : send message : %s" % str(cmd_message))

        ### Listen for response
        # get xpl message from queue
        try:
            self._log.debug("Plugin : wait for answer...")
            if command == "start":
                message = self._get_from_queue(self._queue_system_start, filter = {"command" : "start", "plugin" : plugin})
            elif command == "stop":
                message = self._get_from_queue(self._queue_system_stop, filter= {"command" : "stop", "plugin" : plugin})
        except Empty:
            json_data = JSonHelper("ERROR", 999, "No data or timeout on %s plugin %s" % (command, plugin))
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("plugin")
            self.send_http_response_ok(json_data.get())
            return

        self._log.debug("Plugin : message received : %s" % str(message))

        # an error happens
        if 'error' in message.data:
            error_msg = message.data['error']
            json_data = JSonHelper("ERROR", 999, error_msg)
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())


        # no error
        else:
            json_data = JSonHelper("OK")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())




######
# /plugin/config/ processing
######

    def _rest_plugin_config_list(self, name = None, hostname = None, key = None):
        """ list device technology config
            @param name : name of module
            @param key : key of config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("config")
        if name == None:
            for plugin in self._db.list_all_plugin_config():
                json_data.add_data(plugin)
        elif key == None:
            for plugin in self._db.list_plugin_config(name, hostname):
                json_data.add_data(plugin)
        else:
            plugin = self._db.get_plugin_config(name, hostname, key)
            if plugin is not None:
                json_data.add_data(plugin)
        self.send_http_response_ok(json_data.get())



    def _rest_plugin_config_set(self):
        """ set device technology config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("config")
        try:
            plugin = self._db.set_plugin_config(self.get_parameters("name"), \
                                                self.get_parameters("hostname"), \
                                                self.get_parameters("key"), \
                                                self.get_parameters("value"))
            json_data.add_data(plugin)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_plugin_config_del(self, name, hostname):
        """ delete device technology config
            @param name : module name
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("config")
        try:
            for plugin in self._db.del_plugin_config(name, hostname):
                json_data.add_data(plugin)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())











######
# /account processing
######

    def rest_account(self):
        self._log.debug("Account action")

        # Check url length
        if len(self.rest_request) < 2:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        # parameters initialisation
        self.parameters = {}

        ### auth #####################################
        if self.rest_request[0] == "auth":
            if len(self.rest_request) == 3:
                self._rest_account_auth(self.rest_request[1], self.rest_request[2])
            else:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return
    
        ### user #####################################
        if self.rest_request[0] == "user":

            ### list 
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_account_user_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_account_user_list(id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
    
            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_user_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_user_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### password
            elif self.rest_request[1] == "password":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_password()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_account_user_del(id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                      self.jsonp, self.jsonp_cb)

            ### others ###################################
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed", self.jsonp, self.jsonp_cb)
                return

        ### person ###################################
        elif self.rest_request[0] == "person":

            ### list #####################################
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_account_person_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_account_person_list(id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
    
            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_person_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_account_person_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)
    
            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_account_person_del(id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                      self.jsonp, self.jsonp_cb)

            ### others ###################################
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed", self.jsonp, self.jsonp_cb)
                return

        ### others ###################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)
            return



    def _rest_account_user_list(self, id = None):
        """ list accounts
            @param id : id of account
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        if id == None:
            for account in self._db.list_user_accounts():
                json_data.add_data(account)
        else:
            account = self._db.get_user_account(id)
            if account is not None:
                json_data.add_data(account)
        self.send_http_response_ok(json_data.get())

        
    def _rest_account_auth(self, login, password):
        """ check authentification
            @param login : login
            @param password : password
        """
        self._log.info("Try to authenticate as %s" % login)
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        login_ok = self._db.authenticate(login, password)
        if login_ok == True:
            self._log.info("Authentication OK")
            json_data.set_ok(description = "Authentification granted")
            json_data.set_data_type("account")
            account = self._db.get_user_account_by_login(login)
            if account is not None:
                json_data.add_data(account)
        else:
            self._log.warning("Authentication refused")
            json_data.set_error(999, "Authentification refused")
        self.send_http_response_ok(json_data.get())


    def _rest_account_user_add(self):
        """ add user account
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        try:
            # create user and person
            if self.get_parameters("person_id") == None:
                account = self._db.add_user_account_with_person(self.get_parameters("login"), \
                                                    self.get_parameters("password"), \
                                                    self.get_parameters("first_name"), \
                                                    self.get_parameters("last_name"), \
                                                    self.to_date(self.get_parameters("birthday")), \
                                                    bool(self.get_parameters("is_admin")), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
            # create an user and attach it to a person
            else:
                account = self._db.add_user_account(self.get_parameters("login"), \
                                                    self.get_parameters("password"), \
                                                    self.get_parameters("person_id"), \
                                                    bool(self.get_parameters("is_admin")), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_user_update(self):
        """ update user account
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        try:
            # update account with person data
            if self.get_parameters("person_id") == None:
                account = self._db.update_user_account_with_person(self.get_parameters("id"), \
                                                    self.get_parameters("login"), \
                                                    self.get_parameters("first_name"), \
                                                    self.get_parameters("last_name"), \
                                                    self.get_parameters("birthday"), \
                                                    self.get_parameters("is_admin"), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
            # update and attach to a person
            else:
                account = self._db.update_user_account(self.get_parameters("id"), \
                                                    self.get_parameters("login"), \
                                                    self.get_parameters("person_id"), \
                                                    self.get_parameters("is_admin"), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_password(self):
        """ update user password
        """
        self._log.info("Try to change password for account id %s" % self.get_parameters("id"))
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        change_ok = self._db.change_password(self.get_parameters("id"), \
                                          self.get_parameters("old"), \
                                          self.get_parameters("new"))
        if change_ok == True:
            self._log.info("Password updated")
            json_data.set_ok(description = "Password updated")
            json_data.set_data_type("account")
            account = self._db.get_user_account(self.get_parameters("id"))
            if account is not None:
                json_data.add_data(account)
        else:
            self._log.warning("Password not updated : error")
            json_data.set_error(999, "Error in updating password")
        self.send_http_response_ok(json_data.get())



    def _rest_account_user_del(self, id):
        """ delete user account
            @param id : account id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        try:
            account = self._db.del_user_account(id)
            json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_list(self, id = None):
        """ list persons
            @param id : id of person
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        if id == None:
            for person in self._db.list_persons():
                json_data.add_data(person)
        else:
            person = self._db.get_person(id)
            if person is not None:
                json_data.add_data(person)
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_add(self):
        """ add person
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        try:
            person = self._db.add_person(self.get_parameters("first_name"), \
                                         self.get_parameters("last_name"), \
                                         self.to_date(self.get_parameters("birthday")))
            json_data.add_data(person)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_update(self):
        """ update person
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        try:
            person = self._db.update_person(self.get_parameters("id"), \
                                            self.get_parameters("first_name"), \
                                            self.get_parameters("last_name"), \
                                            self.to_date(self.get_parameters("birthday")))
            json_data.add_data(person)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())



    def _rest_account_person_del(self, id):
        """ delete person
            @param id : person id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("person")
        try:
            person = self._db.del_person(id)
            json_data.add_data(person)
        except:
            json_data.set_error(code = 999, description = self.get_exception())
        self.send_http_response_ok(json_data.get())








######
# /queeucontent processing
######

    def rest_queuecontent(self):
        self._log.debug("Display queue content")
        
        # Check url length
        if len(self.rest_request) != 1:
            self.send_http_response_error(999, "Bad url", self.jsonp, self.jsonp_cb)
            return

        if self.rest_request[0] == "system_list":
            self.rest_queuecontent_display(self._queue_system_list)
        elif self.rest_request[0] == "system_detail":
            self.rest_queuecontent_display(self._queue_system_detail)
        elif self.rest_request[0] == "system_start":
            self.rest_queuecontent_display(self._queue_system_start)
        elif self.rest_request[0] == "system_stop":
            self.rest_queuecontent_display(self._queue_system_stop)
        elif self.rest_request[0] == "command":
            self.rest_queuecontent_display(self._queue_command)
        elif self.rest_request[0] == "event":
            self.rest_queuecontent_display(self._queue_event)


    def rest_queuecontent_display(self, my_queue):
        # Queue size
        queue_size = my_queue.qsize()

        # Queue elements
        queue_data = []
        if queue_size > 0:
            idx = 0
            while idx < queue_size:
                idx += 1
                # Queue content
                elt_time, elt_data = my_queue.get_nowait()
                my_queue.put((elt_time, elt_data))
                queue_data.append({"time" : time.ctime(elt_time), "content" : str(elt_data)})

        data = {"size" : queue_size, "data" : queue_data}

        # Send result
        json_data = JSonHelper("OK")
        json_data.set_data_type("queue %s" % self.rest_request[0])
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.add_data(queue_data)
        self.send_http_response_ok(json_data.get())



######
# /testlongpol processing
######

    def rest_testlongpoll(self):
        self._log.debug("Testing long poll action")
        num = random.randint(1, 15)
        time.sleep(num)
        data = {"number" : num}
        json_data = JSonHelper("OK")
        json_data.set_data_type("longpoll")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.add_data(data)
        self.send_http_response_ok(json_data.get())






#####
# /helper processing
#####

    def rest_helper(self):
        print "Helper action"

        json_data = JSonHelper("OK")
        json_data.set_data_type("helper")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        
        command = self.rest_request[0]
        if len(self.rest_request) <= 1 and command != "help":
            self.send_http_response_error(999, 
                                         "Bad command, no command given or missing first option", 
                                         self.jsonp, self.jsonp_cb)
            return


        package = domogik.xpl.helpers
        if command == "help":
            output = ["List of available helpers :"]
            for importer, plgname, ispkg in pkgutil.iter_modules(package.__path__):
                output.append(" - %s" % plgname)
            output.append("Type 'foo help' to get help on foo helper")


        else:
            print "command=%s" % command
            ### load helper and create object
            try:
                for importer, plgname, ispkg in pkgutil.iter_modules(package.__path__):
                    print "%s / %s" % (plgname, command)
                    if plgname == command:
                        print "Import..."
                        helper = __import__('domogik.xpl.helpers.%s' % plgname, fromlist="dummy")
                        try:
                            helper_object = helper.MY_CLASS["cb"]()
                            if len(self.rest_request) == 2:
                                output = helper_object.command(self.rest_request[1])
                            else:
                                output = helper_object.command(self.rest_request[1], \
                                                               self.rest_request[2:])
                        except HelperError as e:
                            self.send_http_response_error(999, 
                                                         "Error : %s" % e.value,
                                                         self.jsonp, self.jsonp_cb)
                            return
                    
                        

            except:
                json_data.add_data(self.get_exception())
                self.send_http_response_ok(json_data.get())
                return

        if output != None:
            for line in output:
                json_data.add_data(line)
        else:
            json_data.add_data("<No result>")
        self.send_http_response_ok(json_data.get())




#####
# /repo processing
#####

    def rest_repo(self):
        print "Repository action"

        ### put #####################################
        if self.rest_request[0] == "put":
            if self.command != "PUT":
                self.send_http_response_error(999, "HTTP %s command not allowed. Use PUT." % self.command, \
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_repo_put()

        ### get #####################################
        elif self.rest_request[0] == "get":
            if len(self.rest_request) != 2:
                self.send_http_response_error(999, "Wrong number of parameters for %s" % self.rest_request[0],
                                          self.jsonp, self.jsonp_cb)
            else:
                self._rest_repo_get(self.rest_request[1])
            
        ### others ##################################
        else:
            self.send_http_response_error(999, self.rest_request[0] + " not allowed", self.jsonp, self.jsonp_cb)


    def _rest_repo_put(self):
        """ Put a file on rest repository
        """
        self.headers.getheader('Content-type')
        print self.headers
        content_length = int(self.headers['Content-Length'])

        if hasattr(self, "_put_filename") == False:
            print "No file name given!!!"
            self.send_http_response_error(999, "You must give a file name : ?filename=foo.txt",
                                          self.jsonp, self.jsonp_cb)
            return
        self._log.info("PUT : uploading %s" % self._put_filename)

        # TODO : check filename value (extension, etc)

        # replace name (without extension) with an unique id
        basename, extension = os.path.splitext(self._put_filename)
        file_id = str(uuid.uuid4())
        file = "%s/%s%s" % (self.repo_dir, 
                             file_id,
                             extension)

        try:
            sv = open(file, "w")
            sv.write(self.rfile.read(content_length))
            sv.close()
        except IOError:
            self._log.error("PUT : failed to upload %s : %s" % (self._put_filename, traceback.format_exc()))
            print traceback.format_exc()
            self.send_http_response_error(999, "Error while writing '%s' : %s" % (file, traceback.format_exc()),
                                          self.jsonp, self.jsonp_cb)
            return

        self._log.info("PUT : %s uploaded as %s%s" % (self._put_filename,
                                                   file_id, extension))
        json_data = JSonHelper("OK")
        json_data.set_data_type("repository")
        json_data.add_data({"file" : "%s%s" % (file_id, extension)})
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())


    def _rest_repo_get(self, file):
        """ Get a file from rest repository
        """
        # Check file opening
        try:
            f = open("%s/%s" % (self.repo_dir, file), "rb")
        except IOError:
            self.send_http_response_error(999, "No file % available" % file,
                                          self.jsonp, self.jsonp_cb)
            return

        # Get informations on file
        ctype = None
        fs = os.fstat(f.fileno())
        lm = os.stat("%s%s" % (self.repo_dir, file))[stat.ST_MTIME]

        # Get mimetype information
        if not mimetypes.inited:
            mimetypes.init()
        extension_map = mimetypes.types_map.copy()
        extension_map.update({
                '' : 'application/octet-stream', # default
                '.py' : 'text/plain'})
        basename, extension = os.path.splitext(file)
        if extension in extension_map:
            ctype = extension_map[extension] 
        else:
            extension = extension.lower()
            if extension in extension_map:
                ctype = extension_map[extension] 
            else:
                ctype = extension_map[''] 

        # Send file
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", lm)
        self.end_headers()
        #self.copyfile(f, self.wfile)
        shutil.copyfileobj(f, self.wfile)
        f.close(

    )


################################################################################
class JSonHelper():
    """ Easy way to create a json or jsonp structure
    """

    def __init__(self, status = "OK", code = 0, description = ""):
        """ Init json structure
            @param status : OK/ERROR
            @param code : 0...999 : error code. If error no referenced, 999
            @param description : error description
        """
        if status == "OK":
            self.set_ok()
        else:
            self.set_error(code, description)
        self._data_type = ""
        self._data_values = ""
        self._nb_data_values = 0

    def set_jsonp(self, jsonp, jsonp_cb):
        """ define jsonp mode
            @param jsonp : True/False : True : jsonp mode
            @param jsonp_cb : name of jsonp callback
        """
        self._jsonp = jsonp
        self._jsonp_cb = jsonp_cb

    def set_ok(self, code=0, description=None):
        """ set ok status
        """
        self._status = '"status" : "OK", "code" : ' + str(code) + ', "description" : "' + str(description) + '",'

    def set_error(self, code=0, description=None):
        """ set error status
            @param code : error code
            @param description : error description
        """
        description = description.replace('\n', "\\n")
        self._status = '"status" : "ERROR", "code" : ' + str(code) + ', "description" : "' + str(description) + '",'

    def set_data_type(self, type):
        """ set data type
            @param type : data type
        """
        self._data_type = type

    def add_data(self, data):
        """ add data to json structure in 'type' table
            @param data : data to add
        """
        data_out = ""
        self._nb_data_values += 1

        # issue to force data not to be in cache
        # TODO : update when all tables will be defined!!!
        table_list = ["device_feature",  \
                     "area",  \
                     "device",  \
                     "device_usage",  \
                     "device_config",  \
                     "device_feature_association",  \
                     "device_stats",  \
                     "device_stats_value",  \
                     "device_technology",  \
                     "plugin_config",  \
                     "plugin_config_param",  \
                     "device_type",  \
                     "device_feature_model",  \
                     "uiitemconfig",  \
                     "room",  \
                     "useraccount",  \
                     "sensor_reference_data",  \
                     "person",  \
                     "system_config",  \
                     "system_stats",  \
                     "system_statsvalue", \
                     "id", \
                     "device_id", \
                     "name"]

        for table in table_list:
            if hasattr(data, table):
                pass
      
        if data == None:
            return

        data_out += self._process_data(data)
        data_out = data_out.replace('\n', "\\n")
        self._data_values += data_out
            




    def _process_data(self, data, idx = 0, key = None):
        #print "==== PROCESS DATA " + str(idx) + " ===="

        # check deepth in recursivity
        if idx > 2:
            return "#MAX_DEPTH# "

        # define data types
        db_type = ("DeviceFeature", "Area", "Device", "DeviceUsage", \
                   "DeviceConfig", "DeviceStats", "DeviceStatsValue", \
                   "DeviceTechnology", "PluginConfig", "PluginConfigParam",  \
                   "DeviceType", "UIItemConfig", "Room", "UserAccount", \
                   "SensorReferenceData", "Person", "SystemConfig", \
                   "SystemStats", "SystemStatsValue", "Trigger", \
                   "DeviceFeatureAssociation", "DeviceFeatureModel") 
        instance_type = ("instance")
        num_type = ("int", "float")
        str_type = ("str", "unicode", "bool", "datetime", "date")
        none_type = ("NoneType")
        tuple_type = ("tuple")
        list_type = ("list")
        dict_type = ("dict")

        data_json = ""

        # get data type
        data_type = type(data).__name__
        #print "TYPE=%s" % data_type
        #print data

        ### type instance (sql object)
        if data_type in instance_type:
            # get <object>._type value
            try:
                sub_data_type = data._type.lower()
            except:
                sub_data_type = "???"
            #print "SUB TYPE = %s" % sub_data_type

            if idx == 0:
                data_json += "{"
            else:
                data_json += '"%s" : {' % sub_data_type

            for key in data.__dict__:
                sub_data_key = key
                sub_data = data.__dict__[key]
                sub_data_type = type(sub_data).__name__
                #print "    DATA KEY : " + str(sub_data_key)
                #print "    DATA : " + str(sub_data)
                #print "    DATA TYPE : " + str(sub_data_type)
                data_json += self._process_sub_data(idx + 1, False, sub_data_key, sub_data, sub_data_type, db_type, instance_type, num_type, str_type, none_type, tuple_type, list_type, dict_type)
            data_json = data_json[0:len(data_json)-1] + "},"

        ### type : SQL table
        elif data_type in db_type: 
            data_json += "{" 
            for key in data.__dict__: 
                sub_data_key = key 
                sub_data = data.__dict__[key] 
                sub_data_type = type(sub_data).__name__ 
                #print "    DATA KEY : " + str(sub_data_key) 
                #print "    DATA : " + unicode(sub_data) 
                #print "    DATA TYPE : " + str(sub_data_type) 
                buffer = self._process_sub_data(idx + 1, False, sub_data_key, sub_data, sub_data_type, db_type, instance_type, num_type, str_type, none_type, tuple_type, list_type, dict_type) 
                # if max depth in recursivity, we don't display "foo : {}"
                if re.match(".*#MAX_DEPTH#.*", buffer) is None:
                    data_json += buffer
            data_json = data_json[0:len(data_json)-1] + "}," 

        ### type : tuple
        elif data_type in tuple_type:
            if idx > 0:
                data_json += "{"
            for idy in range(len(data)):
                sub_data_key = "???"
                sub_data = data[idy]
                sub_data_type = type(data[idy]).__name__
                #print "    DATA KEY : " + str(sub_data_key)
                #print "    DATA : " + str(sub_data)
                #print "    DATA TYPE : " + str(sub_data_type)
                data_json += self._process_sub_data(idx + 1, False, sub_data_key, sub_data, sub_data_type, db_type, instance_type, num_type, str_type, none_type, tuple_type, list_type, dict_type)
            if idx > 0:
                data_json = data_json[0:len(data_json)-1] + "},"


        ### type : list
        elif data_type in list_type:
            # get first data type
            if len(data) > 0:
                sub_data_elt0_type = type(data[0]).__name__
            else:
                return data_json

            # start table
            if sub_data_elt0_type == "dict":
                data_json += '"%s" : [' % key
            else:
                display_sub_data_elt0_type = re.sub(r"([^^])([A-Z][a-z])",
                             r"\1_\2",
                             sub_data_elt0_type).lower()
                data_json += '"%s" : [' % display_sub_data_elt0_type

            # process each data
            for sub_data in data:
                sub_data_key  = "???(2)"
                sub_data_type = type(sub_data).__name__
                #print "    DATA KEY : " + str(sub_data_key)
                #print "    DATA : " + str(sub_data)
                #print "    DATA TYPE : " + str(sub_data_type)
                data_json += self._process_sub_data(idx + 1, True, sub_data_key, sub_data, sub_data_type, db_type, instance_type, num_type, str_type, none_type, tuple_type, list_type, dict_type)
            # finish table
            data_json = data_json[0:len(data_json)-1] + "],"


        ### type : dict
        elif data_type in dict_type:
            data_json += "{"
            for key in data:
                sub_data_key = key
                sub_data = data[key]
                sub_data_type = type(sub_data).__name__
                #print "    DATA KEY : " + str(sub_data_key)
                #print "    DATA : " + str(sub_data)
                #print "    DATA TYPE : " + str(sub_data_type)
                data_json += self._process_sub_data(idx + 1, False, sub_data_key, sub_data, sub_data_type, db_type, instance_type, num_type, str_type, none_type, tuple_type, list_type, dict_type)
            data_json = data_json[0:len(data_json)-1] + "},"

        ### type : str
        elif data_type in str_type:
            data_json += '"%s",' % data

        return data_json



    def _process_sub_data(self, idx, is_table, sub_data_key, sub_data, sub_data_type, db_type, instance_type, num_type, str_type, none_type, tuple_type, list_type, dict_type):
        if sub_data_key[0] == "_":
            return ""
        data_tmp = ""
        if sub_data_type in db_type: 
            if is_table is False:  # and idx != 0: 
                display_sub_data_type = re.sub(r"([^^])([A-Z][a-z])",
                             r"\1_\2",
                             sub_data_type).lower()
                data_tmp = '"%s" : ' % display_sub_data_type
            data_tmp += self._process_data(sub_data, idx)
        elif sub_data_type in instance_type:
            data_tmp += self._process_data(sub_data, idx)
        elif sub_data_type in list_type:
            data_tmp += self._process_data(sub_data, idx, sub_data_key)
        elif sub_data_type in dict_type:
            data_tmp += self._process_data(sub_data, idx)
        elif sub_data_type in num_type:
            data_tmp = '"%s" : %s,' % (sub_data_key, sub_data)
        elif sub_data_type in str_type:
            data_tmp = '"%s" : "%s",' % (sub_data_key, sub_data)
        elif sub_data_type in none_type:
            data_tmp = '"%s" : "None",' % (sub_data_key)
        else: 
            data_tmp = ""
        
        return data_tmp




        

    def get(self):
        """ getter for all json data created
            @return json or jsonp data
        """
        if self._jsonp is True and self._jsonp_cb != "":
            json_buf = "%s (" % self._jsonp_cb
        else:
            json_buf = ""

        if self._data_type != "":
            json_buf += '{%s "%s" : [%s]}' % (self._status,   self._data_type, self._data_values[0:len(self._data_values)-1])
        else:
            json_buf += '{%s}' % self._status[0:len(self._status)-1]

        if self._jsonp is True and self._jsonp_cb != "":
            json_buf += ")"
        return json_buf
        
    






################################################################################
class StatsManager(XplPlugin):
    """
    Listen on the xPL network and keep stats of device and system state
    """
    def __init__(self, handler_params):
        XplPlugin.__init__(self, 'statmgr')
        cfg = Loader('domogik')
        config = cfg.load()
        cfg_db = dict(config[1])
        directory = "%s/share/domogik/stats/" % cfg_db['custom_prefix']

        # logging initialization
        log = logger.Logger('rest-stat')
        self._log_stats = log.get_logger()
        self._log_stats.info("Rest Stat Manager initialisation...")

        # logging initialization for unkwnon devices
        log_unknown = logger.Logger('rest-stat-unknown-devices')
        self._log_stats_unknown = log_unknown.get_logger()

        files = glob.glob("%s/*/*xml" % directory)
        stats = {}
        self._db = DbHelper()

        ### Rest data
        self.handler_params = handler_params

        self._event_requests = self.handler_params[0]._event_requests

        ### Read xml files
        res = {}
        for _file in files :
            self._log_stats.info("Parse file %s" % _file)
            doc = minidom.parse(_file)
            #Statistic/root node
            technology = doc.documentElement.attributes.get("technology").value
            schema_types = self.get_schemas_and_types(doc.documentElement)
            self._log_stats.debug("Parsed : %s" % schema_types)
            for schema in schema_types:
                for type in schema_types[schema]:
                    is_uniq = self.check_config_uniqueness(res, schema, type)
                    if not is_uniq:
                        self._log_stats.warning("Schema %s, type %s is already defined ! check your config." % (schema, type))
                        self.force_leave()
            if technology not in res:
                res[technology] = {}
                stats[technology] = {}
            
            for schema in schema_types:
                if schema not in res[technology]:
                    res[technology][schema] = {}
                    stats[technology][schema] = {}
                for type in schema_types[schema]:
                    device, mapping, static_device = self.parse_mapping(doc.documentElement.getElementsByTagName("mapping")[0])
                    res[technology][schema][type] = {"filter": 
                            self.parse_listener(schema_types[schema][type].getElementsByTagName("listener")[0]),
                            "mapping": mapping,
                            "device": device,
                            "static_device": static_device}
            
                    stats[technology][schema][type] = self._Stat(self._myxpl, res[technology][schema][type], technology, schema, type, self.handler_params)

    def get_schemas_and_types(self, node):
        """ Get the schema and the xpl message type
        @param node : the root (statistic) node
        @return {'schema1': ['type1','type2'], 'schema2', ['type1','type3']}
        """
        res = {}
        schemas = node.getElementsByTagName("schema")
        for schema in schemas:
            res[schema.attributes.get("name").value] = {}
            for xpltype in schema.getElementsByTagName("xpltype"):
                res[schema.attributes.get("name").value][xpltype.attributes.get("type").value] = xpltype
        return res

    def check_config_uniqueness(self, res, schema, type):
        """ Check the schema/type is not already defined in res
        @param res : the array with all already-defined mapping
        @param schema : the current schema
        @param type : the current xpl-type
        Return True if the schema/type is *not* already defined in res
        """
        # TODO : delete this fucntion and its call ?
        #for techno in res.keys():
        #    for _schema in res[techno].keys(): 
        #        if _schema == schema:
        #            for _type in res[techno][schema].keys():
        #                if _type == type:
        #                    return False
        return True

    def parse_listener(self, node):
        """ Parse the "listener" node
        """
        filters = {}
        for _filter in node.getElementsByTagName("filter")[0].getElementsByTagName("key"):
            if _filter.attributes["name"].value in filters:
                if not isinstance(filters[_filter.attributes["name"].value], list):
                        filters[_filter.attributes["name"].value] = \
                            [filters[_filter.attributes["name"].value]]
                filters[_filter.attributes["name"].value].append(_filter.attributes["value"].value)
            else:
                filters[_filter.attributes["name"].value] = _filter.attributes["value"].value
        return filters

    def parse_mapping(self, node):
        """ Parse the "mapping" node
        """
         
        values = []
        device_node = node.getElementsByTagName("device")[0]
        device = None
        static_device = None
        if device_node.attributes.has_key("field"):
            device = device_node.attributes["field"].value.lower()
        elif device_node.attributes.has_key("static_name"):
            static_device = device_node.attributes["static_name"].value.lower()
 
        #device = node.getElementsByTagName("device")[0].attributes["field"].value.lower()
        for value in node.getElementsByTagName("value"):
            name = value.attributes["field"].value
            data = {}
            data["name"] = name
            #If a "name" attribute is defined, use it as vallue, else value is empty
            if value.attributes.has_key("new_name"):
                data["new_name"] = value.attributes["new_name"].value.lower()
                if value.attributes.has_key("filter_key"):
                    data["filter_key"] = value.attributes["filter_key"].value.lower()
                    if value.attributes.has_key("filter_value"):
                        data["filter_value"] = value.attributes["filter_value"].value.lower()
                    else:
                        data["filter_value"] = None
                else:
                    data["filter_key"] = None
                    data["filter_value"] = None
            else:
                data["new_name"] = None
                data["filter_key"] = None
                data["filter_value"] = None
            values.append(data)
        return device, values, static_device


    class _Stat:
        """ This class define a statistic parser and logger instance
        Each instance create a Listener and the associated callbacks
        """

        def __init__(self, xpl, res, technology, schema, type, handler_params):
            """ Initialize a stat instance 
            @param xpl : A xpl manager instance
            @param res : The result of xml parsing for this techno/schema/type
            @params technology : The technology monitored
            @param schema : the schema to listen for
            @param type : the xpl type to listen for
            @param handler_params : handler_params from rest
            """
            ### Rest data
            self.handler_params = handler_params

            self._event_requests = self.handler_params[0]._event_requests
            self._log_stats = self.handler_params[0]._log_stats
            self._log_stats_unknown = self.handler_params[0]._log_stats_unknown
            self._db = self.handler_params[0]._db

            self._res = res
            params = {'schema':schema, 'xpltype': type}
            params.update(res["filter"])
            self._listener = Listener(self._callback, xpl, params)
            self._technology = technology

        def _callback(self, message):
            """ Callback for the xpl message
            @param message : the Xpl message received 
            """

            print "MSG=%s" % message
            ### we put data in database
            self._db = DbHelper()
            self._log_stats.debug("message catcher : %s" % message)
            try:
                if self._res["device"] != None:
                    d_id = self._db.get_device_by_technology_and_address(self._technology, \
                        message.data[self._res["device"]]).id
                elif self._res["static_device"] != None:
                    d_id = self._db.get_device_by_technology_and_address(self._technology, \
                        self._res["static_device"]).id
                else:  # oups... something wrong in xml file ?
                    self._log_stats.error("Device has no name... is there a problem in xml file ?")
                    raise AttributeError
                print "Stat for techno '%s' / adress '%s' / id '%s'" % (self._technology, message.data[self._res["device"]], d_id)
            except AttributeError:
                if self._res["device"] != None:
                    self._log_stats_unknown.warning("Received a stat for an unreferenced device : %s - %s" \
                        % (self._technology, message.data[self._res["device"]]))
                else:
                    self._log_stats_unknown.warning("Received a stat for an unreferenced device : %s - %s" \
                        % (self._technology, self._res["static_device"]))
                print "=> unknown device"
                return
            self._log_stats.debug("Stat received for %s - %s." \
                    % (self._technology, message.data[self._res["device"]]))
            #current_date = time.mktime(calendar.timegm(datetime.datetime.now().timetuple()))
            current_date = calendar.timegm(datetime.datetime.now().timetuple())
            #current_date = datetime.datetime.now()
            device_data = []

            ### mapping processing
            for map in self._res["mapping"]:
                # first : get value and default key
                key = map["name"]
                value = message.data[map["name"]]
                if map["filter_key"] == None:
                    key = map["name"]
                    device_data.append({"key" : key, "value" : value})
                    self._db.add_device_stat(current_date, key, value, d_id)
                else:
                    if map["filter_value"] != None and \
                       map["filter_value"] == message.data[map["filter_key"]]:
                        key = map["new_name"]
                        device_data.append({"key" : key, "value" : value})
                        self._db.add_device_stat(current_date, key, value, d_id)
                    else:
                        if map["filter_value"] == None:
                            self._log_stats.warning ("Stats : no filter_value defined in map : %s" % str(map))

            # Put data in events queues
            self._event_requests.add_in_queues(d_id, 
                    {"device_id" : d_id, "data" : device_data})






################################################################################
class EventRequests():
    """
    Object where all events queues and ticket id will be stored
    """
    def __init__(self, log, queue_size, queue_timeout, queue_life_expectancy):
        """ Init Event Requests
            @param queue_size : size of queues for events
        """
        self.requests = {}
        self._log = log
        self.queue_size = queue_size
        if queue_timeout == 0:
            self.queue_timeout = None
        else:
            self.queue_timeout = queue_timeout
        self.queue_life_expectancy = queue_life_expectancy
        self.ticket = 0
        self.count_request = 0

    def new(self, device_id_list):
        """ Add a new queue and ticket id for a new event
            @param device_id : id of device to get events from
            @return ticket_id : ticket id
        """
        print "---- NEW ----"
        new_queue = Queue(self.queue_size)
        ticket_id = self.generate_ticket()
        new_data = {"creation_date" :  datetime.datetime.now(),
                    "device_id_list" : device_id_list,
                    "queue" : new_queue,
                    "queue_size" : 0}
        self.requests[ticket_id] = new_data
        self.count_request += 1
        self._log.debug("New event request created (ticket_id=%s) for device(s) : %s" % (ticket_id, str(device_id_list)))
        return ticket_id

    def free(self, ticket_id):
        """ End request for a ticket id : remove queue
            @param ticket_id : ticket id of queue to remove
            @return True if succcess, False if ticket doesn't exists
        """
        try:
            del self.requests[ticket_id]
        # ticket doesn't exists
        except KeyError:
            self._log.warning("Trying to free an unknown event request (ticket_id=%s)" % ticket_id)
            return False
        self.count_request -= 1
        return True

    def generate_ticket(self):
        """ Generate a ticket id for an event request
        """
        # TODO : make something random for ticket generation
        self.ticket += 1
        return str(self.ticket)
 
    def count(self):
        """ Return number of event requests
        """
        return self.count_request

    def add_in_queues(self, device_id, data):
        """ Add data in each queue linked to device id
            @param data : data to put in queues
        """
        print "---- ADD ----"
        for req in self.requests:
            if device_id in self.requests[req]["device_id_list"]:
                ### clean queue
                idx = 0
                queue_size = self.requests[req]["queue"].qsize()
                actual_time = time.time()
                while idx < queue_size:
                    if self.requests[req]["queue"].empty() == False:
                        (elt_time, elt_data) = self.requests[req]["queue"].get_nowait()
                        # if there is already data about device_id, we clean it (we don't put it back in queue)
                        # or if data is too old
                        # Note : if we get new stats only each 2 minutes, 
                        #     cleaning about life expectancy will only happen 
                        #     every 2 minutes instead of every 'life_expectancy'
                        #     seconds. I supposed that when you got several 
                        #     technologies, you pass throug this code several 
                        #     times in a minute. More over,  events are
                        #     actually (0.1) used only by UI and when you use
                        #     UI, events are read immediatly. So, I think
                        #     that cleaning queues here instead of creating
                        #     a dedicated process which will run in background
                        #     is a good thing for the moment
                        if elt_data["device_id"] != device_id and \
                           actual_time - elt_time < self.queue_life_expectancy:

                            self.requests[req]["queue"].put((elt_time, elt_data),
                                                            True, self.queue_timeout) 
                        else:
                            # one data suppressed from queue
                            self.requests[req]["queue_size"] -= 1
                        
                    idx += 1

                ### put data in queue
                try:
                    self.requests[req]["queue"].put((time.time(), data), 
                                                    True, self.queue_timeout) 
                    self.requests[req]["queue_size"] += 1
                except Full:
                    self._log.error("Queue for ticket_id '%s' is full. Feel free to adjust Event queues size" % ticket_id)


    def get(self, ticket_id):
        """ Get data from queue linked to ticket id. 
            If no data, wait until queue timeout
            @param ticket_id : id of ticket
            @return data in queue or False if ticket doesn't exists
        """
        print "---- GET ----"
        try:
            (elt_time, elt_data) = self.requests[ticket_id]["queue"].get(True, self.queue_timeout)
            self.requests[ticket_id]["queue_size"] -= 1
            # TODO : use queue_life_expectancy in order not to get old data

            # Add ticket id to answer
            elt_data["ticket_id"] = str(ticket_id)

        # Timeout
        except Empty:
            # Add ticket id to answer
            elt_data = {}
            elt_data["ticket_id"] = str(ticket_id)

        # Ticket doesn't exists
        except KeyError:
            self._log.warning("Trying to get an unknown event request (ticket_id=%s)" % ticket_id)
            return False
        return elt_data

    def list(self):
        """ List queues (used by rest status)
        """
        return str(self.requests)





if __name__ == '__main__':
    # Create REST server with default values (overriden by ~/.domogik.cfg)
    rest_server = Rest("127.0.0.1", "8080")
    #rest_server.start_stats()
    #rest_server.start_http()


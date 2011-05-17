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

class Rest(XplPlugin):
class HTTPServerWithParam(SocketServer.ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, request_handler_class, \
        HTTPServer.__init__(self, server_address, request_handler_class, \
class HTTPSServerWithParam(SocketServer.ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, request_handler_class, \
        HTTPServer.__init__(self, server_address, request_handler_class, \
class RestHandler(BaseHTTPRequestHandler):



@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.common import logger
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from domogik.xpl.lib.rest.jsondata import JSonHelper
from domogik.xpl.lib.rest.event import EventRequests
from domogik.xpl.lib.rest.stat import StatsManager
from domogik.xpl.lib.rest.request import ProcessRequest
from domogik.common.configloader import Loader
from xml.dom import minidom
import time
import urllib
import locale
from Queue import Queue, Empty, Full
from domogik.xpl.common.queryconfig import Query
import traceback
import datetime
import socket
from OpenSSL import SSL
import SocketServer
import os
import errno





REST_API_VERSION = "0.1"
#REST_DESCRIPTION = "REST plugin is part of Domogik project. See http://trac.domogik.org/domogik/wiki/modules/REST.en for REST API documentation"

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
EVENT_TIMEOUT = 300  # must be superior than QUEUE_EVENT_TIMEOUT
                     # Value should be > 2*x QUEUE_EVENT_TIMEOUT
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
        self.log.info("Rest Server initialisation...")
        self.log.debug("locale : %s %s" % locale.getdefaultlocale())

        # logging Queue activities
        log_queue = logger.Logger('rest-queues')
        self.log_queue = log_queue.get_logger('rest-queues')
        self.log_queue.info("Rest's queues activities...")
    
        # logging data manipulation initialization
        log_dm = logger.Logger('rest-dm')
        self.log_dm = log_dm.get_logger('rest-dm')
        self.log_dm.info("Rest Server Data Manipulation...")

        # API version
        self._rest_api_version = REST_API_VERSION

        try:
    
            ### Config
    
            # directory data in ~/.domogik/domogik.cfg
            cfg = Loader('domogik')
            config = cfg.load()
            conf = dict(config[1])
            self._xml_cmd_dir = "%s/share/domogik/url2xpl/" % conf['custom_prefix']
            self._xml_stat_dir = "%s/share/domogik/stats/" % conf['custom_prefix']
    
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
            self.log.info("Configuration : ip:port = %s:%s" % (self.server_ip, self.server_port))
    
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
                self.log.info("Configuration : SSL support activated (certificate : %s)" % self.ssl_certificate)
            else:
                self.log.info("Configuration : SSL support not activated")
    
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
            self.log.debug("Get queues configuration")
            self._config = Query(self.myxpl, self.log)

            self._queue_timeout = self._config.query('rest', 'q-timeout')
            if self._queue_timeout == None:
                self._queue_timeout = QUEUE_TIMEOUT
            self._queue_timeout = float(self._queue_timeout)

            self._queue_size = self._config.query('rest', 'q-size')
            if self._queue_size == None:
                self._queue_size = QUEUE_SIZE
            self._queue_size = float(self._queue_size)

            self._queue_life_expectancy = self._config.query('rest', 'q-life-exp')
            if self._queue_life_expectancy == None:
                self._queue_life_expectancy = QUEUE_LIFE_EXPECTANCY
            self._queue_life_expectancy = float(self._queue_life_expectancy)

            self._queue_sleep = self._config.query('rest', 'q-sleep')
            if self._queue_sleep == None:
                self._queue_sleep = QUEUE_SLEEP
            self._queue_sleep = float(self._queue_sleep)

            # /command Queues config
            self._queue_command_size = self._config.query('rest', 'q-cmd-size')
            if self._queue_command_size == None:
                self._queue_command_size = QUEUE_COMMAND_SIZE
            self._queue_command_size = float(self._queue_command_size)

            # /event Queues config
            self._event_timeout = self._config.query('rest', 'evt-timeout')
            if self._event_timeout == None:
                self._event_timeout = EVENT_TIMEOUT
            self._event_timeout = float(self._event_timeout)

            self._queue_event_size = self._config.query('rest', 'q-evt-size')
            if self._queue_event_size == None:
                self._queue_event_size = QUEUE_EVENT_SIZE
            self._queue_event_size = float(self._queue_event_size)

            self._queue_event_timeout = self._config.query('rest', 'q-evt-timeout')
            if self._queue_event_timeout == None:
                self._queue_event_timeout = QUEUE_EVENT_TIMEOUT
            self._queue_event_timeout = float(self._queue_event_timeout)

            self._queue_event_life_expectancy = self._config.query('rest', 'q-evt-life-exp')
            if self._queue_event_life_expectancy == None:
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
            self._event_requests = EventRequests(self.log,
                                                 self._event_timeout,
                                                 self._queue_event_size,
                                                 self._queue_event_timeout,
                                                 self._queue_event_life_expectancy)
            self.add_stop_cb(self._event_requests.set_stop_clean)
    
            # define listeners for queues
            self.log.debug("Create listeners")
            Listener(self._add_to_queue_system_list, self.myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'list'})
            Listener(self._add_to_queue_system_detail, self.myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'detail'})
            Listener(self._add_to_queue_system_start, self.myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'start'})
            Listener(self._add_to_queue_system_stop, self.myxpl, \
                     {'schema': 'domogik.system',
                      'xpltype': 'xpl-trig',
                      'command' : 'stop'})
            Listener(self._add_to_queue_command, self.myxpl, \
                     {'xpltype': 'xpl-trig'})
    
            # Load xml files for /command
            self.xml = {}
            self.xml_date = None
            self.load_xml()

            self.log.info("REST Initialisation OK")

            self.add_stop_cb(self.stop_http)
            self.server = None
            self.start_stats()
            # Enable hbeat
            self.enable_hbeat()
            self.start_http()
        except :
            self.log.error("%s" % self.get_exception())


    def _add_to_queue_system_list(self, message):
        """ Add data in a queue
        """
        self._put_in_queue(self._queue_system_list, message)

    def _add_to_queue_system_detail(self, message):
        """ Add data in a queue
        """
        self._put_in_queue(self._queue_system_detail, message)

    def _add_to_queue_system_start(self, message):
        """ Add data in a queue
        """
        self._put_in_queue(self._queue_system_start, message)

    def _add_to_queue_system_stop(self, message):
        """ Add data in a queue
        """
        self._put_in_queue(self._queue_system_stop, message)

    def _add_to_queue_command(self, message):
        """ Add data in a queue
        """
        self._put_in_queue(self._queue_command, message)

    def _get_from_queue(self, my_queue, filter_type = None, filter_schema = None, filter_data = None, nb_rec = 0, timeout = None):
        """ Encapsulation for _get_from_queue_in
            If timeout not elapsed and _get_from_queue didn't find a valid data
            call again _get_from_queue until timeout
            This encapsulation is used to process case where queue is not empty but there is
            no valid data in it and we want to wait for timeout
        """
        if timeout == None:
            timeout = self._queue_timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return self._get_from_queue_without_waiting(my_queue, filter_type, filter_schema, filter_data, nb_rec, timeout)
            except Empty:
                # no data in queue for us.... let's continue until time elapsed
                # in order not rest not working so much, let it make a pause
                time.sleep(self._queue_sleep)
        # time elapsed... we can raise the Empty exception
        raise Empty



    def _get_from_queue_without_waiting(self, my_queue, filter_type = None, filter_schema = None, filter_data = None, nb_rec = 0, timeout = None):
        """ Get an item from queue (recursive function)
            Checks are made on : 
            - life expectancy of message
            - filter given
            - size of queue
            If necessary, each item of queue is read.
            @param my_queue : queue to get data from
            @param filter_type : filter on a schema type
            @param filter_schema : filter on a specific schema
            @param filter_data : dictionnay of filters. Examples :
                - {"command" : "start", ...}
                - {"plugin" : "wol%", ...} : here "%" indicate that we search for something starting with "wol"
            @param nb_rec : internal parameter (do not use it for first call). Used to check recursivity VS queue size
            @param timeout : to use a different timeout from default one
        """
        if timeout == None:
            timeout = self._queue_timeout
        self.log_queue.debug("Get from queue : %s (recursivity deepth : %s)" % (str(my_queue), nb_rec))
        # check if recursivity doesn't exceed queue size
        if nb_rec > my_queue.qsize():
            self.log_queue.warning("Get from queue %s : number of call exceed queue size (%s) : return None" % (str(my_queue), my_queue.qsize()))
            # we raise an "Empty" exception because we consider that if we don't find
            # the good data, it is as if it was "empty"
            raise Empty

        msg_time, message = my_queue.get(True, timeout)

        # if message not too old, we process it
        if time.time() - msg_time < self._queue_life_expectancy:
            # no filter defined
            if filter_type == None and filter_schema == None and filter_data == None: 
                self.log_queue.debug("Get from queue %s : return %s" % (str(my_queue), str(message)))
                return message

            # we want to filter data
            else:
                keep_data = True
                if filter_type != None and filter_type.lower() != message.type.lower():
                    keep_data = False
                if filter_schema != None and filter_schema.lower() != message.schema.lower():
                    keep_data = False

                if filter_data != None and keep_data == True:
                    # data
                    self.log_queue.debug("Filter on message %s WITH %s" % (message.data, filter_data))
                    for key in filter_data:
                        # take care of final "%" in order to search data starting by filter_data[key]
                        if filter_data[key][-1] == "%":
                            msg_data = str(message.data[key])
                            my_filter_data = str(filter_data[key])
                            len_data = len(my_filter_data) - 1
                            if msg_data[0:len_data] != my_filter_data[0:-1]:
                                keep_data = False
                        # normal search
                        else:
                            if message.data[key].lower() != filter_data[key].lower():
                                keep_data = False
    
                # if message is ok for us, return it
                if keep_data == True:
                    self.log_queue.debug("Get from queue %s : return %s" % (str(my_queue), str(message)))
                    return message

                # else, message get back in queue and get another one
                else:
                    self.log_queue.debug("Get from queue %s : bad data, check another one..." % (str(my_queue)))
                    self._put_in_queue(my_queue, message)
                    return self._get_from_queue_without_waiting(my_queue, filter_type, filter_schema, filter_data, nb_rec + 1, timeout)

        # if message too old : get an other message
        else:
            self.log_queue.debug("Get from queue %s : data too old, check another one..." % (str(my_queue)))
            return self._get_from_queue_without_waiting(my_queue, filter_type, filter_schema, filter_data, nb_rec + 1, timeout)

    def _put_in_queue(self, my_queue, message):
        """ put a message in a named queue
            @param my_queue : queue 
            @param message : data to put in queue
        """
        self.log_queue.debug("Put in queue %s : %s" % (str(my_queue), str(message)))
        try:
            my_queue.put((time.time(), message), True, self._queue_timeout) 

        # Clean queue to make space
        except Full:
            msg = "Queue '%s' is full : cleaning it to make some space..." % my_queue
            self.log_queue.debug(msg)
            print msg
            # queue is full : start cleaning it
            nb_ck = 0
            while nb_ck < my_queue.qsize():
                (q_time, q_data) = my_queue.get()
                # data to keep
                if time.time() - self._queue_life_expectancy < q_time:
                    my_queue.put((q_time, q_data), True, self._queue_timeout)
                nb_ck += 1
            my_queue.put((time.time(), message), True, self._queue_timeout) 
            self.log_queue.debug("Cleaning finished")
              
                



    def start_http(self):
        """ Start HTTP Server
        """
        # Start HTTP server
        self.log.info("Start HTTP Server on %s:%s..." % (self.server_ip, self.server_port))

        if self.use_ssl:
            self.server = HTTPSServerWithParam((self.server_ip, int(self.server_port)), RestHandler, \
                                         handler_params = [self])
        else:
            self.server = HTTPServerWithParam((self.server_ip, int(self.server_port)), RestHandler, \
                                         handler_params = [self])

        self.server.serve_forever()



    def stop_http(self):
        """ Stop HTTP Server
        """
        self.server.stop_handling()



    def start_stats(self):
        """ Start Statistics manager
        """
        print "Start Stats"
        self.log.info("Starting statistics manager. His logs will be in a dedicated log file")
        StatsManager(handler_params = [self], xpl = self.myxpl)
        self.log.info("Stat manager started")




    def load_xml(self):
        """ Load XML files for /command
        """
        # list technologies folders
        self.xml = {}
        for techno in os.listdir(self._xml_cmd_dir):
            for command in os.listdir(self._xml_cmd_dir + "/" + techno):
                xml_file = self._xml_cmd_dir + "/" + techno + "/" + command
                if xml_file[-4:] == ".xml":
                    self.log.info("Load XML file for %s>%s : %s" % (techno, command, xml_file))
                    self.xml["%s/%s" % (techno, command)] = minidom.parse(xml_file)
        self.xml_date = datetime.datetime.now()




    def get_exception(self):
        """ Get exception and display it on stdout
        """
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
        self.address = server_address
        self.handler_params = handler_params
        self.stop = False


    def serve_forever(self):
        """ we rewrite this fucntion to make HTTP Server shutable
        """
        self.stop = False
        while not self.stop:
            self.handle_request()


    def stop_handling(self):
        """ put the stop flag to True in order stopping handling requests
        """
        self.stop = True
        # we do a last request to terminate server
        print "Make a last request to HTTP server to stop it"
        resp = urllib.urlopen("http://%s:%s" % (self.address[0], self.address[1]))



################################################################################
# HTTPS
class HTTPSServerWithParam(SocketServer.ThreadingMixIn, HTTPServer):
    """ Extends HTTPServer to allow send params to the Handler.
    """

    def __init__(self, server_address, request_handler_class, \
                 bind_and_activate=True, handler_params = []):
        HTTPServer.__init__(self, server_address, request_handler_class, \
                            bind_and_activate)
        self.address = server_address
        self.handler_params = handler_params
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
            print error
            self.handler_params[0].log.error(error)
            # force exiting
            self.handler_params[0].force_leave()
            return
        self.server_bind()
        self.server_activate()


    def serve_forever(self):
        """ we rewrite this fucntion to make HTTP Server shutable
        """
        self.stop = False
        while not self.stop:
            self.handle_request()


    def stop_handling(self):
        """ put the stop flag to True in order stopping handling requests
        """
        self.stop = True
        # we do a last request to terminate server
        resp = urllib.urlopen("https://%s:%s" % (self.address[0], self.address[1]))








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
        # get type to see if we had to make tricky action for TinyWebDb
        # notice : this code is duplicated from request.py : ProcessRequest
        if self.path[-1:] == "/":
            self.path = self.path[0:len(self.path)-1]
        tab_path = self.path.split("/")

        # Get type of request : /command, /xpl-cmnd, /base, etc
        if len(tab_path) < 2:
            rest_type = None
            # Display an information json if no request done in do_for_all_methods
            return
        rest_type = tab_path[1].lower()

        # tricky usage for TinyWebDb in order to use Google appinventor
        if rest_type == "getvalue":
            if self.headers.has_key("content-length"):
                post_length = int(self.headers['content-length'])
                post_data = self.rfile.read(post_length)
                post_tab = post_data.split("&")
                for data in post_tab:
                    if data[0:3] == "tag":
                        tag = data[4:]
                tag = unicode(urllib.unquote(tag), "UTF-8")
            else:
                tag = None
            # replace self.path with tag value
            self.path = tag

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
        try:
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
        except:
            self.server.handler_params[0].log.error("%s" % self.server.handler_params[0].get_exception())
        




######
# HTTP return
######

    def send_http_response_ok(self, data = ""):
        """ Send to browser a HTTP 200 responde
            200 is the code for "no problem"
            Send also json data
            @param data : json data to display
        """
        self.server.handler_params[0].log.debug("Send HTTP header for OK")
        try:
            self.send_response(200)
            self.send_header('Content-type',  'application/json')
            self.send_header('Expires', '-1')
            self.send_header('Cache-control', 'no-cache')
            self.send_header('Content-Length', len(data.encode("utf-8")))
            self.end_headers()
            if data:
                # if big data, log only start of data
                if len(data) > 1000:
                    self.server.handler_params[0].log.debug("Send HTTP data : %s... [truncated because data too long for logs]" % data[0:1000].encode("utf-8"))
                # else log all data
                else:
                    self.server.handler_params[0].log.debug("Send HTTP data : %s" % data.encode("utf-8"))
                self.wfile.write(data.encode("utf-8"))
        except IOError as err: 
            if err.errno == errno.EPIPE:
                # [Errno 32] Broken pipe : client closed connexion
                self.server.handler_params[0].log.debug("It seems that socket has closed on client side (the browser may have change the page displayed")
                return
            else:
                raise err


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
        self.server.handler_params[0].log.warning("Send HTTP header for ERROR : code=%s ; msg=%s" % (err_code, err_msg))
        json_data = JSonHelper("ERROR", err_code, err_msg)
        json_data.set_jsonp(jsonp, jsonp_cb)
        try:
            self.send_response(200)
            self.send_header('Content-type',    'text/html')
            self.send_header('Expires', '-1')
            self.send_header('Cache-control', 'no-cache')
            self.send_header('Content-Length', len(json_data.get().encode("utf-8")))
            self.end_headers()
            self.wfile.write(json_data.get())
        except IOError as err:
            if err.errno == errno.EPIPE:
                # [Errno 32] Broken pipe : client closed connexion
                self.server.handler_params[0].log.debug("It seems that socket has closed on client side (the browser may have change the page displayed")
                return
            else:
                raise err





if __name__ == '__main__':
    # Create REST server with default values (overriden by ~/.domogik/domogik.cfg)
    REST = Rest("127.0.0.1", "8080")


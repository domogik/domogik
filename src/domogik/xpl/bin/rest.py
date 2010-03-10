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

Module purpose
==============

REST support for Domogik project

Implements
==========

TODO when finished ;)



@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.lib.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.module import xPLModule
from domogik.common import logger
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader
from xml.dom import minidom
import time
import urllib
import sys
import locale
from socket import gethostname
from Queue import *
from domogik.xpl.lib.queryconfig import Query
from domogik.xpl.lib.module import xPLResult
import re
import traceback
import datetime


REST_API_VERSION = "0.1"
REST_DESCRIPTION = "REST module is part of Domogik project. See http://trac.domogik.org/domogik/wiki/modules/REST.en for REST API documentation"



QUEUE_TIMEOUT = 10
QUEUE_SIZE = 10
QUEUE_LIFE_EXPECTANCY = 3



################################################################################
class Rest(xPLModule):
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
        xPLModule.__init__(self, name = 'rest')

        # logging initialization
        log = logger.Logger('REST')
        self._log = log.get_logger()
        self._log.info("Rest Server initialisation...")
        self._log.debug("locale : %s %s" % locale.getdefaultlocale())
        # logging data manipulation initialization
        log_dm = logger.Logger('REST-DM')
        self._log_dm = log_dm.get_logger()
        self._log_dm.info("Rest Server Data Manipulation...")
        self._log_dm.debug("locale : %s %s" % locale.getdefaultlocale())
        # DB Helper
        self._db = DbHelper()

        ### Config

        # directory data in ~/.domogik.cfg
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        self._xml_directory = "%s/share/domogik/rest/" % conf['custom_prefix']

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


        # Queues config
        self._log.debug("Get queues configuration")
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('rest', 'queue-timeout', res)
        self._queue_timeout = res.get_value()['queue-timeout']
        if self._queue_timeout == "None":
            self._queue_timeout = QUEUE_TIMEOUT
        self._queue_timeout = float(self._queue_timeout)
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('rest', 'queue-size', res)
        self._queue_size = res.get_value()['queue-size']
        if self._queue_size == "None":
            self._queue_size = QUEUE_SIZE
        self._queue_size = float(self._queue_size)
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('rest', 'queue-life-exp', res)
        self._queue_life_expectancy = res.get_value()['queue-life-exp']
        if self._queue_life_expectancy == "None":
            self._queue_life_expectancy = QUEUE_LIFE_EXPECTANCY
        self._queue_life_expectancy = float(self._queue_life_expectancy)

        # Queues for xPL
        self._queue_system_list = Queue(self._queue_size)
        self._queue_system_detail = Queue(self._queue_size)
        self._queue_system_start = Queue(self._queue_size)
        self._queue_system_stop = Queue(self._queue_size)

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

        self._log.info("Initialisation OK")


    def _add_to_queue_system_list(self, message):
        self._put_in_queue(self._queue_system_list, message)

    def _add_to_queue_system_detail(self, message):
        self._put_in_queue(self._queue_system_detail, message)

    def _add_to_queue_system_start(self, message):
        self._put_in_queue(self._queue_system_start, message)

    def _add_to_queue_system_stop(self, message):
        self._put_in_queue(self._queue_system_stop, message)

    def _get_from_queue(self, my_queue, filter = None, nb_rec = 0):
        """ Get an item from queue (recursive function)
            Checks are made on : 
            - life expectancy of message
            - filter given
            - size of queue
            If necessary, each item of queue is read.
            @param my_queue : queue to get data from
            @param filter : dictionnay of filters. Examples :
                - {"command" : "start", ...}
                - {"module" : "wol%", ...} : here "%" indicate that we search for something starting with "wol"
            @param nb_rec : internal parameter (do not use it for first call). Used to check recursivity VS queue size
        """
        self._log.debug("Get from queue : %s (recursivity deepth : %s)" % (str(my_queue), nb_rec))
        # check if recursivity doesn't exceed queue size
        if nb_rec > self._queue_size:
            self._log.warning("Get from queue %s : number of call exceed queue size (%s) : return None" % (str(my_queue), self._queue_size))
            # we raise an "Empty" exception because we consider that if we don't find
            # the good data, it is as if it was "empty"
            raise Empty

        msg_time, message = my_queue.get(True, self._queue_timeout)

        # if message not too old, we process it
        if time.time() - msg_time < self._queue_life_expectancy:
            # no filter defined
            if filter == None: 
                self._log.debug("Get from queue %s : return %s" % (str(my_queue), str(message)))
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
                    self._log.debug("Get from queue %s : return %s" % (str(my_queue), str(message)))
                    return message

                # else, message get back in queue and get another one
                else:
                    self._log.debug("Get from queue %s : bad data, check another one..." % (str(my_queue)))
                    self._put_in_queue(my_queue, message)
                    return self._get_from_queue(my_queue, filter, nb_rec + 1)

        # if message too old : get an other message
        else:
            self._log.debug("Get from queue %s : data too old, check another one..." % (str(my_queue)))
            return self._get_from_queue(my_queue, filter, nb_rec + 1)

    def _put_in_queue(self, my_queue, message):
        self._log.debug("Put in queue %s : %s" % (str(my_queue), str(message)))
        my_queue.put((time.time(), message), True, self._queue_timeout) 



    def start(self):
        """ Start HTTP Server
        """
        # Start HTTP server
        self._log.info("Start HTTP Server on %s:%s..." % (self.server_ip, self.server_port))
        server = HTTPServerWithParam((self.server_ip, int(self.server_port)), RestHandler, \
                                     handler_params = [self])
        server.serve_forever()




################################################################################
class HTTPServerWithParam(HTTPServer):
    """ Extends HTTPServer to allow send params to the Handler.
    """

    def __init__(self, server_address, request_handler_class, \
                 bind_and_activate=True, handler_params = []):
        HTTPServer.__init__(self, server_address, request_handler_class, \
                            bind_and_activate)
        self.handler_params = handler_params
        # dirty issue
        self.timeout = None






################################################################################
class RestHandler(BaseHTTPRequestHandler):
    """ Class/object called for each request to HTTP server
        Here we will process use GET/POST/OPTION HTTP methods 
        and then create a REST request
    """


######
# GET/POST/OPTIONS processing
######

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

    def do_OPTIONS(self):
        """ Process OPTIONS requests
            Call directly .do_for_all_methods()
        """
        self.do_for_all_methods()

    def do_for_all_methods(self):
        """ Create an object for each request. This object will process 
            the REST url
        """
        # dirty issue to force HTTP/1.1 
        self.protocol_version = 'HTTP/1.1'
        self.request_version = 'HTTP/1.1'

        # TODO : create a thread here
        request = ProcessRequest(self.server.handler_params, self.path, \
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
        self.send_response(200)
        self.send_header('Content-type',  'application/json')
        self.send_header('Expires', '-1')
        self.send_header('Cache-control', 'no-cache')
        self.send_header('Content-Length', len(data.encode("utf-8")))
        self.end_headers()
        if data:
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
        # TODO : log!!
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


    def __init__(self, handler_params, path, cb_send_http_response_ok, \
                 cb_send_http_response_error):
        """ Create shorter access : self.server.handler_params[0].* => self.*
            First processing on url given
            @param handler_params : parameters given to HTTPHandler
            @param path : path given to HTTP server : /base/area/... for example
            @param cb_send_http_response_ok : callback for function
                                              REST.send_http_response_ok 
            @param cb_send_http_response_error : callback for function
                                              REST.send_http_response_error 
        """

        self.handler_params = handler_params
        self.path = path
        self.send_http_response_ok = cb_send_http_response_ok
        self.send_http_response_error = cb_send_http_response_error

        # shorter access
        self._db = self.handler_params[0]._db
        self._myxpl = self.handler_params[0]._myxpl
        self._log = self.handler_params[0]._log
        self._log_dm = self.handler_params[0]._log_dm
        self._xml_directory = self.handler_params[0]._xml_directory

        self._log.debug("Process request : init")

        self._queue_timeout =  self.handler_params[0]._queue_timeout
        self._queue_size =  self.handler_params[0]._queue_size
        self._queue_life_expectancy = self.handler_params[0]._queue_life_expectancy
      
        self._get_from_queue = self.handler_params[0]._get_from_queue
        self._put_in_queue = self.handler_params[0]._put_in_queue

        self._queue_system_list =  self.handler_params[0]._queue_system_list
        self._queue_system_detail =  self.handler_params[0]._queue_system_detail
        self._queue_system_start =  self.handler_params[0]._queue_system_start
        self._queue_system_stop =  self.handler_params[0]._queue_system_stop

        # global init
        self.jsonp = False
        self.jsonp_cb = ""

        # url processing
        self.path = urllib.unquote(unicode(self.path))
        # replace password by "***". 
        path_without_passwd = re.sub("password/.*/", "password/***/", self.path + "/")
        self._log.info("Request : %s" % path_without_passwd)

        # TODO log data manipulation here
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




    def do_for_all_methods(self):
        """ Process request
            This function call appropriate functions for processing path
        """
        if self.rest_type == "command":
            self.rest_command()
        elif self.rest_type == "xpl-cmnd":
            self.rest_xpl_cmnd()
        elif self.rest_type == "base":
            self.rest_base()
        elif self.rest_type == "module":
            self.rest_module()
        elif self.rest_type == "account":
            self.rest_account()
        elif self.rest_type == None:
            self.rest_status()
        else:
            self.send_http_response_error(999, "Type [" + str(self.rest_type) + \
                                          "] is not supported", \
                                          self.jsonp, self.jsonp_cb)


    def _parse_options(self):
        """ Process parameters : ...?param1=val1&param2=val2&....
        """
        self._log.debug("Parse request options")

        # for each debug option
        for opt in self.parameters.split("&"):
            print "OPT :" + opt
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
            elif opt_key == "debug-sleep" and opt_value != None:
                self._debug_sleep(opt_value)



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
        json_data.add_data({"Version" : REST_API_VERSION})
        json_data.add_data({"Description" : REST_DESCRIPTION})
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
        self._log.debug("Process command")

        # parse data in URL
        if len(self.rest_request) >= 3:
            techno = self.rest_request[0]
            address = self.rest_request[1]
            order = self.rest_request[2]
            if len(self.rest_request) > 3:
                others = self.rest_request[3:]
            else:
                others = None
        else:
            json_data = JSonHelper("ERROR", 999, "Url too short for /command")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())
            return
        self._log.debug("Techno    : %s" % techno)
        self._log.debug("Address   : %s" % address)
        self._log.debug("Order     : %s" % order)
        self._log.debug("Others    : %s" % str(others))

        # open xml file
        xml_file = "%s/%s.xml" % (self._xml_directory, techno)
        #xml_file = "%s/%s.xml" % ("../xml/", techno)
        # process xml
        message = self._parse_xml(xml_file, techno, address, order, others)
        if message == None:
            return

        self._log.debug("Process command > send message : %s" % str(message))
        self._myxpl.send(message)

        # REST processing finished and OK
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        self.send_http_response_ok(json_data.get())

        


    def _parse_xml(self, xml_file, techno, address, order, others):
        """ xml parser for a technology file
            Generation of a xPL message by processing REST request and XML file
            @param xml_file : xml file defining how to construct message
            @param techno : technology (x10, etc)
            @param address : address of device
            @param order : order to send
            @param others : other parameters
            @return None if a problem occurs or a xPL message if ok
        """
        try:
            xml_doc = minidom.parse(xml_file)
        except:
            json_data = JSonHelper("ERROR", 999, \
                                   "Error while reading xml file : " + xml_file)
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            self.send_http_response_ok(json_data.get())
            return None

        mapping = xml_doc.documentElement
        if mapping.getElementsByTagName("technology")[0].attributes.get("name").value != techno:
            self.send_http_response_error(999, "'technology' attribute must be the same as file name !", \
                                          self.jsonp, self.jsonp_cb)
            return
        
        #Schema
        schema = mapping.getElementsByTagName("schema")[0].firstChild.nodeValue

        #Device key name
        device = mapping.getElementsByTagName("device")[0]
        if device.getElementsByTagName("key") != []:
            device_address_key = device.getElementsByTagName("key")[0].firstChild.nodeValue
        else:
            device_address_key = None

        #Orders
        orders = mapping.getElementsByTagName("orders")[0]
        order_key = orders.getElementsByTagName("key")[0].firstChild.nodeValue

        #Get the good order bloc :
        the_order = None
        for an_order in orders.getElementsByTagName("order"):
            if an_order.getElementsByTagName("name")[0].firstChild.nodeValue == order:
                the_order = an_order
        if the_order == None:
            self.send_http_response_error(999, "Order can't be found", self.jsonp, self.jsonp_cb)
            return

        #Parse the order bloc
        order_value = the_order.getElementsByTagName("value")[0].firstChild.nodeValue
        #mandatory parameters
        mandatory_parameters_value = {}
        optional_parameters_value = {}
        if the_order.getElementsByTagName("parameters")[0].hasChildNodes():
            mandatory_parameters = the_order.getElementsByTagName("parameters")[0].getElementsByTagName("mandatory")[0]
            count_mandatory_parameters = len(mandatory_parameters.getElementsByTagName("parameter"))
            mandatory_parameters_from_url = others[3:3+count_mandatory_parameters]
            for mandatory_param in mandatory_parameters.getElementsByTagName("parameter"):
                key = mandatory_param.attributes.get("key").value
                value = mandatory_parameters_from_url[int(mandatory_param.attributes.get("location").value) - 1]
                mandatory_parameters_value[key] = value
            #optional parameters
            if the_order.getElementsByTagName("parameters")[0].getElementsByTagName("optional") != []:
                optional_parameters =  the_order.getElementsByTagName( \
                                                   "parameters")[0].getElementsByTagName("optional")[0]
                for opt_param in optional_parameters.getElementsByTagName("parameter"):
                    ind = others.index(opt_param.getElementsByTagName("name")[0])
                    optional_parameters_value[url[ind]] = url[ind + 1]

        return self._forge_msg(schema, device_address_key, address, order_key, order_value, \
                               mandatory_parameters_value, optional_parameters_value)





    def _forge_msg(self, schema, device_address_key, address, order_key, order_value, \
                   mandatory_parameters_value, optional_parameters_value):
        """ forge xpl message
            @param schema : xpl schema
            @param device_address_key : key for address in xpl message
            @param address : value for address in xpl message
            @param order_key : key for order in xpl message
            @param order_value : value for order in xpl message
            @param mandatory_parameters_value : mandatory params
            @param optional_parameters_value : optionnal params
            @return xPL message
        """
        msg = """xpl-cmnd
{
hop=1
source=rest
target=*
}
%s
{
%s=%s
%s=%s
""" % (schema, device_address_key, address, order_key, order_value)
        for m_param in mandatory_parameters_value.keys():
            msg += "%s=%s\n" % (m_param, mandatory_parameters_value[m_param])
        for o_param in optional_parameters_value.keys():
            msg += "%s=%s\n" % (o_param, optional_parameters_value[o_param])
        msg += "}"
        return msg





        



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
        if self.xpl_target.lower() != "all":
            message.set_header(target=self.xpl_target)
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
            elif self.rest_request[1] == "list-with-rooms":
                if len(self.rest_request) == 2:
                    self._rest_base_area_list_with_rooms()
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
            elif self.rest_request[1] == "list-with-devices":
                if len(self.rest_request) == 2:
                    self._rest_base_room_list_with_devices()
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
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_ui_item_config_del()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

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

        ### sensor reference #########################
        elif self.rest_request[0] == "sensor_reference":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_sensor_reference_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-type_id":
                        self._rest_base_sensor_reference_list(type_id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add_OFF":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_sensor_reference_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update_OFF":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_sensor_reference_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del_OFF":
                if len(self.rest_request) == 3:
                    self._rest_base_sensor_reference_del(sr_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### actuator feature #########################
        elif self.rest_request[0] == "actuator_feature":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_actuator_feature_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-type_id":
                        self._rest_base_actuator_feature_list(type_id=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add_OFF":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_actuator_feature_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update_OFF":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_actuator_feature_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del_OFF":
                if len(self.rest_request) == 3:
                    self._rest_base_actuator_feature__del(af_id=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### others
            else:
                self.send_http_response_error(999, self.rest_request[1] + " not allowed for " + self.rest_request[0], \
                                                  self.jsonp, self.jsonp_cb)
                return


        ### device technology ########################
        elif self.rest_request[0] == "device_technology":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_technology_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-name":
                        self._rest_base_device_technology_list(name=self.rest_request[3])
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


        ### device technology config #################
        elif self.rest_request[0] == "device_technology_config":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_device_technology_config_list()
                elif len(self.rest_request) == 3 or len(self.rest_request) == 5:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                elif len(self.rest_request) == 4:
                    if self.rest_request[2] == "by-technology-id":
                        self._rest_base_device_technology_config_list(technology_id=self.rest_request[3])
                elif len(self.rest_request) == 6:
                    if self.rest_request[2] == "by-technology-id" and self.rest_request[4] == "by-key":
                        self._rest_base_device_technology_config_list(technology_id = self.rest_request[3], key = self.rest_request[5])
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
                    self._rest_base_device_technology_config_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_device_technology_config_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_device_technology_config_del(tc_id=self.rest_request[2])
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
                elif len(self.rest_request) == 3:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)
                else:
                    if self.rest_request[2] == "by-room":
                        self._rest_base_device_list(room_id=self.rest_request[3])
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
            # specific process for False
            if value == "False":
                self.parameters[key] = False
            else:
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
            return self.parameters[name]
        except KeyError:
            return None



    def to_date(self, date):
        """ Transform YYYYMMDD date in datatime object
            @param date : date
        """
        if date == None:
            return None
        year = int(date[0:4])
        month = int(date[4:6])
        day = int(date[6:8])
        try:
            my_date = datetime.date(year, month, day)
        except:
            self.send_http_response_error(999, str(sys.exc_info()[1].replace('"', "'")), self.jsonp, self.jsonp_cb)
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



    def _rest_base_area_list_with_rooms(self):
        """ list areas and associated rooms
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("area")
        for area in self._db.list_areas_with_rooms():
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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



    def _rest_base_room_list_with_devices(self):
        """ list rooms and associated devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("room")
        for room in self._db.list_rooms_with_devices():
            json_data.add_data(room)
        self.send_http_response_ok(json_data.get())



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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



    def _rest_base_ui_item_config_del(self):
        """ del ui_item_config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("ui_config")
        try:
            for ui_item_config in self._db.delete_ui_item_config(ui_name = name, \
                                                         ui_reference = reference, ui_key = key):
                json_data.add_data(ui_item_config)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
                                                     self.get_parameters("description"))
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
                                                        self.get_parameters("description"))
            json_data.add_data(device_usage)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



######
# /base/sensor_reference processing
######

    def _rest_base_sensor_reference_list(self, type_id = None):
        """ list sensor references
            @param name : sensor reference name
        """ 
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("sensor_reference")
        if type_id == None:
            for sensor_reference in self._db.list_sensor_reference_data():
                json_data.add_data(sensor_reference)
        else:
            for sensor_reference in self._db.get_sensor_reference_data_by_typeid(type_id):
                json_data.add_data(sensor_reference)
        self.send_http_response_ok(json_data.get())



    def _rest_base_sensor_reference_add(self):
        """ add sensor reference
        """ 
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("sensor_reference")
        try:
            sensor_reference = self._db.add_sensor_reference_data(self.get_parameters("name"), \
                                                                  self.get_parameters("value"), \
                                                                  self.get_parameters("type_id"), \
                                                                  self.get_parameters("unit"), \
                                                                  self.get_parameters("stat_key"))
            json_data.add_data(sensor_reference)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



    def _rest_base_sensor_reference_update(self):
        """ update sensor_reference
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("sensor_reference")
        try:
            sensor_reference = self._db.update_sensor_reference_data(self.get_parameters("id"), \
                                                                  self.get_parameters("name"), \
                                                                  self.get_parameters("value"), \
                                                                  self.get_parameters("type_id"), \
                                                                  self.get_parameters("unit"), \
                                                                  self.get_parameters("stat_key"))
            json_data.add_data(sensor_reference)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())




    def _rest_base_sensor_reference_del(self, sr_id=None):
        """ delete sensor reference
            @param sr_id : sensor reference id to delete
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("sensor_reference")
        try:
            sensor_reference = self._db.del_sensor_reference_data(sr_id)
            json_data.add_data(sensor_reference)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



######
# /base/actuator_feature processing
######

    def _rest_base_actuator_feature_list(self, type_id = None):
        """ list actuator features
            @param name : actuator feature name
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("actuator_feature")
        if type_id == None:
            for actuator_feature in self._db.list_actuator_features():
                json_data.add_data(actuator_feature)
        else:
            for actuator_feature in self._db.get_actuator_feature_by_typeid(type_id):
                json_data.add_data(actuator_feature)
        self.send_http_response_ok(json_data.get())



    def _rest_base_actuator_feature_add(self):
        """ add actuator feature
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("actuator_feature")
        try:
            actuator_feature = self._db.add_actuator_feature(self.get_parameters("name"), \
                                                                  self.get_parameters("value"), \
                                                                  self.get_parameters("type_id"), \
                                                                  self.get_parameters("unit"), \
                                                                  self.get_parameters("configurable_states"), \
                                                                  self.get_parameters("return_confirmation"))
            json_data.add_data(actuator_feature)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())


    def _rest_base_actuator_feature_update(self):
        """ update actuator feature
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("actuator_feature")
        try:
            actuator_feature = self._db.update_actuator_feature(self.get_parameters("id"), \
                                                                  self.get_parameters("name"), \
                                                                  self.get_parameters("value"), \
                                                                  self.get_parameters("type_id"), \
                                                                  self.get_parameters("unit"), \
                                                                  self.get_parameters("configurable_states"), \
                                                                  self.get_parameters("return_confirmation"))
            json_data.add_data(actuator_feature)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())


    def _rest_base_actuator_feature_del(self, af_id=None):
        """ delete actuator feature
            @param af_id : actuator feature id to delete
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("actuator_feature")
        try:
            actuator_feature = self._db.del_actuator_feature(af_id)
            json_data.add_data(actuator_feature)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



######
# /base/device_technology processing
######

    def _rest_base_device_technology_list(self, name = None):
        """ list device technologies
            @param name : device technology name
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology")
        if name == None:
            for device_technology in self._db.list_device_technologies():
                json_data.add_data(device_technology)
        else:
            device_technology = self._db.get_device_technology_by_name(name)
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



######
# /base/device_technology_config processing
######

    def _rest_base_device_technology_config_list(self, technology_id = None, key = None):
        """ list device technology config
            @param technology_id : device technology config id
            @param key : key of config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology_config")
        if technology_id == None:
            for device_technology_config in self._db.list_all_device_technology_config():
                json_data.add_data(device_technology_config)
        elif key == None:
            for device_technology_config in self._db.list_device_technology_config(technology_id):
                json_data.add_data(device_technology_config)
        else:
            device_technology_config = self._db.get_device_technology_config(technology_id, key)
            if device_technology_config is not None:
                json_data.add_data(device_technology_config)
        self.send_http_response_ok(json_data.get())



    def _rest_base_device_technology_config_add(self):
        """ add device technology config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology_config")
        try:
            device_technology_config = self._db.add_device_technology_config(self.get_parameters("technology_id"), \
                                                                             self.get_parameters("key"), \
                                                                             self.get_parameters("value"), \
                                                                             self.get_parameters("description"))
            json_data.add_data(device_technology_config)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_technology_config_update(self):
        """ update device technology config
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology_config")
        try:
            device_technology_config = self._db.update_device_technology_config(self.get_parameters("id"), \
                                                                             self.get_parameters("technology_id"), \
                                                                             self.get_parameters("key"), \
                                                                             self.get_parameters("value"), \
                                                                             self.get_parameters("description"))
            json_data.add_data(device_technology_config)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())


    def _rest_base_device_technology_config_del(self, tc_id=None):
        """ delete device technology config
            @param tc_id : device technology config id
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device_technology_config")
        try:
            device_technology_config = self._db.del_device_technology_config(tc_id)
            json_data.add_data(device_technology_config)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



######
# /base/device processing
######

    def _rest_base_device_list(self, room_id = None, device_id = None):
        """ list devices
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("device")
        if room_id == None and device_id == None:
            for device in self._db.list_devices():
                json_data.add_data(device)
        elif device_id == None:
            # by-room
            if room_id == "":
                room_id = None
            for device in self._db.get_all_devices_of_room(room_id):
                json_data.add_data(device)
        elif room_id == None:
            # by-device
            for device in self._db.get_all_devices_of_room(room_id):
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
                                         self.get_parameters("room_id"), \
                                         self.get_parameters("description"), \
                                         self.get_parameters("reference"))
            json_data.add_data(device)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
                                         self.get_parameters("type_id"), \
                                         self.get_parameters("usage_id"), \
                                         self.get_parameters("room_id"), \
                                         self.get_parameters("description"), \
                                         self.get_parameters("reference"))
            json_data.add_data(device)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())










######
# /module processing
######

    def rest_module(self):
        """ /module processing
        """
        self._log.debug("Module action")
        if len(self.rest_request) < 1:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        ### list ######################################
        if self.rest_request[0] == "list":

            if len(self.rest_request) == 1:
                self._rest_module_list()
            elif len(self.rest_request) == 2:
                self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[0], \
                                              self.jsonp, self.jsonp_cb)
            else:
                if self.rest_request[1] == "by-name":
                    self._rest_module_list(name=self.rest_request[2])
                else:
                    self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                              self.jsonp, self.jsonp_cb)
                    return

        ### detail ####################################
        elif self.rest_request[0] == "detail":
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_module_detail(self.rest_request[1])


        ### start #####################################
        elif self.rest_request[0] == "start":
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_module_start_stop(module =  self.rest_request[1], \
                                   command = "start")

        ### stop ######################################
        elif self.rest_request[0] == "stop":
            if len(self.rest_request) < 2:
                self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
                return
            self._rest_module_start_stop(module =  self.rest_request[1], \
                                   command = "stop")
 
        ### others ####################################
        else:
            self.send_http_response_error(999, "Bad operation for /module", self.jsonp, self.jsonp_cb)
            return



    def _rest_module_list(self, name = None, host = gethostname()):
        """ Send a xpl message to manager to get module list
            Display this list as json
            @param name : name of module
        """
        self._log.debug("Module : ask for module list on %s." % host)

        ### Send xpl message to get list
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.system")
        message.add_data({"command" : "list"})
        # TODO : ask for good host
        message.add_data({"host" : gethostname()})
        self._myxpl.send(message)
        self._log.debug("Module : send message : %s" % str(message))

        ### Wait for answer
        # get xpl message from queue
        try:
            self._log.debug("Module : wait for answer...")
            message = self._get_from_queue(self._queue_system_list)
        except Empty:
            self._log.debug("Module : no answer")
            json_data = JSonHelper("ERROR", 999, "No data or timeout on getting module list")
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("module")
            self.send_http_response_ok(json_data.get())
            return

        self._log.debug("Module : message received : %s" % str(message))

        # process message
        cmd = message.data['command']
        host = message.data["host"]
    

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("module")

        idx = 0
        loop_again = True
        while loop_again:
            try:
                data = message.data["module"+str(idx)].split(",")
                if name == None or name == data[0]:
                    json_data.add_data({"name" : data[0], "description" : data[2], "status" : data[1], "host" : host})
                idx += 1
            except:
                loop_again = False

        self.send_http_response_ok(json_data.get())



    def _rest_module_detail(self, name, host = gethostname()):
        """ Send a xpl message to manager to get module list
            Display this list as json
            @param name : name of module
        """
        self._log.debug("Module : ask for module detail : %s on %s." % (name, host))

        ### Send xpl message to get detail
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.system")
        message.add_data({"command" : "detail"})
        message.add_data({"module" : name})
        # TODO : ask for good host
        message.add_data({"host" : host})
        self._myxpl.send(message)
        self._log.debug("Module : send message : %s" % str(message))

        ### Wait for answer
        # get xpl message from queue
        try:
            self._log.debug("Module : wait for answer...")
            # in filter, "%" means, that we check for something starting with name
            message = self._get_from_queue(self._queue_system_detail, filter = {"command" : "detail", "module" : name + "%"})
        except Empty:
            json_data = JSonHelper("ERROR", 999, "No data or timeout on getting module detail for %s" % name)
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("module")
            self.send_http_response_ok(json_data.get())
            return

        self._log.debug("Module : message received : %s" % str(message))

        # process message
        cmd = message.data['command']
        host = message.data["host"]
        modinfo = message.data["module"]
        data = message.data["module"].split(",")
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("module")

        idx = 0
        loop_again = True
        config_data = []
        while loop_again:
            try:
                data_conf = message.data["config"+str(idx)].split(",")
                config_data.append({"id" : idx+1, "key" : data_conf[0], "description" : data_conf[1], "default" : data_conf[2]})
                idx += 1
            except:
                loop_again = False

        json_data.add_data({"name" : data[0], "description" : data[2], "status" : data[1], "host" : host, "configuration" : config_data})
        self.send_http_response_ok(json_data.get())




    def _rest_module_start_stop(self, command, host = gethostname(), module = None, force = 0):
        """ Send start xpl message to manager
            Then, listen for a response
            @param host : host to which we send command
            @param module : name of module
            @param force : force (or not) action. 0/1. 1 : force
        """
        self._log.debug("Module : ask for %s %s on %s (force=%s)" % (command, module, host, force))

        ### Send xpl message
        cmd_message = XplMessage()
        cmd_message.set_type("xpl-cmnd")
        cmd_message.set_schema("domogik.system")
        cmd_message.add_data({"command" : command})
        cmd_message.add_data({"host" : host})
        cmd_message.add_data({"module" : module})
        cmd_message.add_data({"force" : force})
        self._myxpl.send(cmd_message)
        self._log.debug("Module : send message : " % str(cmd_message))

        ### Listen for response
        # get xpl message from queue
        try:
            self._log.debug("Module : wait for answer...")
            if command == "start":
                message = self._get_from_queue(self._queue_system_start, filter = {"command" : "start", "module" : module})
            elif command == "stop":
                message = self._get_from_queue(self._queue_system_stop, filter= {"command" : "stop", "module" : module})
        except Empty:
            json_data = JSonHelper("ERROR", 999, "No data or timeout on %s module %s" % (command, module))
            json_data.set_jsonp(self.jsonp, self.jsonp_cb)
            json_data.set_data_type("module")
            self.send_http_response_ok(json_data.get())
            return

        self._log.debug("Module : message received : " % str(message))

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
                                                    self.get_parameters("is_admin"), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
            # create an user and attach it to a person
            else:
                account = self._db.add_user_account_with_person(self.get_parameters("login"), \
                                                    self.get_parameters("password"), \
                                                    self.get_parameters("person_id"), \
                                                    self.get_parameters("is_admin"), \
                                                    self.get_parameters("skin_used"))
                json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())



    def _rest_account_user_update(self):
        """ update user account
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("account")
        try:
            account = self._db.update_user_account(self.get_parameters("id"), \
                                                self.get_parameters("login"), \
                                                self.get_parameters("is_admin"), \
                                                self.get_parameters("skin_used"))
            json_data.add_data(account)
        except:
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
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
            json_data.set_error(code = 999, description = str(sys.exc_info()[1]).replace('"', "'"))
        self.send_http_response_ok(json_data.get())








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

        # dirty issue to force data not to be in cache
        if hasattr(data, 'id') or hasattr(data, 'item_reference'):    # for all
            pass
        if hasattr(data, 'area'):  # for room
            pass

        if data == None:
            return

        data_out += self._process_data(data)
        self._data_values += data_out
            




    def _process_data(self, data, idx = 0, key = None):
        #print "==== PROCESS DATA " + str(idx) + " ===="

        # check deepth in recursivity
        if idx > 2:
            return "#MAX_DEPTH#"

        # define data types
        db_type = ("ActuatorFeature", "Area", "Device", "DeviceUsage", \
                   "DeviceConfig", "DeviceStats", "DeviceStatsValue", \
                   "DeviceTechnology", "DeviceTechnologyConfig", \
                   "DeviceType", "UIItemConfig", "Room", "UserAccount", \
                   "SensorReferenceData", "Person", "SystemConfig", \
                   "SystemStats", "SystemStatsValue", "Trigger") 
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

        # dirty issue to force cache of __dict__  
        print "DATA : " + unicode(data).encode('utf-8')
        #print "DATA TYPE : " + data_type

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
                data_json += '"%s" : [' % sub_data_elt0_type.lower()

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

        return data_json



    def _process_sub_data(self, idx, is_table, sub_data_key, sub_data, sub_data_type, db_type, instance_type, num_type, str_type, none_type, tuple_type, list_type, dict_type):
        data_tmp = ""
        if sub_data_type in db_type: 
            if is_table is False:  # and idx != 0: 
                data_tmp = '"%s" : ' % sub_data_type.lower() 
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
        #print json_buf.encode("utf-8")
        return json_buf
        
    



if __name__ == '__main__':
    # Create REST server with default values (overriden by ~/.domogik.cfg)
    http_server = Rest("127.0.0.1", "8080")
    http_server.start()




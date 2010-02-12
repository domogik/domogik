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
#from domogik.xpl.lib.xplconnector import *
from domogik.xpl.common.xplmessage import XplMessage
#from domogik.xpl.lib.module import *
from domogik.xpl.lib.module import xPLModule
from domogik.common import logger
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader
from xml.dom import minidom
import time
import urllib




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

        # parameters
        self.server_ip = server_ip
        self.server_port = server_port

        # logging initialization
        log = logger.Logger('REST')
        self._log = log.get_logger()
        self._log.info("Rest Server initialisation...")

        # DB Helper
        self._db = DbHelper()

        # Congig
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        self._xml_directory = "%s/xml/rest/" % conf['cfg_path']


    def start(self):
        """ Start HTTP Server
        """
        # Start HTTP server
        server = HTTPServerWithParam((self.server_ip, int(self.server_port)), RestHandler, \
                                     handler_params = [self])
        print 'Start REST server on %s:%s...' % (self.server_ip, self.server_port)
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
        print "==== GET ============================================"
        self.do_for_all_methods()

    def do_POST(self):
        """ Process POST requests
            Call directly .do_for_all_methods()
        """
        print "==== POST ==========================================="
        self.do_for_all_methods()

    def do_OPTIONS(self):
        """ Process OPTIONS requests
            Call directly .do_for_all_methods()
        """
        print "==== OPTIONS ==========================================="
        self.do_for_all_methods()

    def do_for_all_methods(self):
        """ Create an object for each request. This object will process 
            the REST url
        """
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
        self.send_response(200)
        self.send_header('Content-type',  'application/json')
        self.send_header('Expires', '-1')
        self.send_header('Cache-control', 'no-cache')
        self.end_headers()
        if data:
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
        self.send_response(200)
        self.send_header('Content-type',    'text/html')
        self.end_headers()
        json_data = JSonHelper("ERROR", err_code, err_msg)
        json_data.set_jsonp(jsonp, jsonp_cb)
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
        self._xml_directory = self.handler_params[0]._xml_directory

        # global init
        self.jsonp = False
        self.jsonp_cb = ""

        # url processing
        self.path = str(urllib.unquote(self.path))
        self.path = unicode(self.path, "utf-8")

        tab_url = self.path.split("?")
        self.path = tab_url[0]
        if len(tab_url) > 1:
            self.parameters = tab_url[1]
            self._parse_options()

        if self.path[-1:] == "/":
            self.path = self.path[0:len(self.path)-1]
        print "PATH : " + self.path
        tab_path = self.path.split("/")

        # Get type of request : /command, /xpl-cmnd, /base, etc
        if len(tab_path) < 2:
            self.rest_type = None
            self.send_http_response_error(999, "No type given", \
                                          self.jsonp, self.jsonp_cb)
            return
        self.rest_type = tab_path[1].lower()
        if len(tab_path) > 2:
            self.rest_request = tab_path[2:]
        else:
            self.rest_request = []
        print "TYPE    : " + self.rest_type
        print "Request : " + str(self.rest_request)





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
        else:
            self.send_http_response_error(999, "Type [" + str(self.rest_type) + \
                                          "] is not supported", \
                                          self.jsonp, self.jsonp_cb)
            return



    def _parse_options(self):
        """ Process parameters : ...?param1=val1&param2=val2&....
        """

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
                self.jsonp = True
                self.jsonp_cb = opt_value

            # call debug functions
            elif opt_key == "debug-sleep" and opt_value != None:
                self._debug_sleep(opt_value)



    def _debug_sleep(self, duration):
        """ Sleep process for 15 seconds
        """
        print "DEBUG : start sleeping for " + str(duration)
        time.sleep(float(duration))
        print "DEBUG : end sleeping"




######
# /command processing
######

    def rest_command(self):
        """ Process /command url
            - decode request
            - call a xml parser for the technology (self.rest_request[0])
           - send appropriate xPL message on network
        """
        print "Call rest_command"

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
        print "Techno    : %s" % techno
        print "Address   : %s" % address
        print "Order     : %s" % order
        print "Others    : %s" % str(others)

        # open xml file
        #xml_file = "%s/%s.xml" % (self._xml_directory, techno)
        xml_file = "%s/%s.xml" % ("../xml/", techno)
        # process xml
        message = self._parse_xml(xml_file, techno, address, order, others)
        if message == None:
            return

        print "Send message : %s" % message
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

        print "Call rest_xpl_cmnd"
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

        print "Send message : %s" % message
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
        print "Call rest_base_get"
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
                        self._rest_base_area_list(arza_id=self.rest_request[3])
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
                    if self.rest_request[2] == "by-name":
                        self._rest_base_sensor_reference_list(name=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_sensor_reference_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_sensor_reference_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
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
                    if self.rest_request[2] == "by-name":
                        self._rest_base_actuator_feature_list(name=self.rest_request[3])
                    else:
                        self.send_http_response_error(999, "Wrong syntax for " + self.rest_request[1], \
                                                  self.jsonp, self.jsonp_cb)

            ### add
            elif self.rest_request[1] == "add":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_actuator_feature_add()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### update
            elif self.rest_request[1] == "update":
                offset = 2
                if self.set_parameters(offset):
                    self._rest_base_actuator_feature_update()
                else:
                    self.send_http_response_error(999, "Error in parameters", self.jsonp, self.jsonp_cb)

            ### del
            elif self.rest_request[1] == "del":
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
                    self._rest_base_device_technology_config__del(tc_id=self.rest_request[2])
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
        if room_id == None and area_id == None:
            for room in self._db.list_rooms():
                json_data.add_data(room)
        elif room_id != None:
            room = self._db.get_room_by_id(room_id)
            if room is not None:
                json_data.add_data(room)
        elif area_id != None:
            if area_id == "null":
                area_id = None
            for room in self._db.get_all_rooms_of_area(area_id):
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
                for ui_item_config in self._db.list_ui_item_config(name, reference):
                    json_data.add_data(ui_item_config)
            else:
                # by-key
                for ui_item_config in self._db.get_ui_item_config(ui_item_name = name, ui_key= key):
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
            for ui_item_config in self._db.delete_ui_item_config(ui_item_name = name, \
                                                         ui_item_reference = reference, ui_key = key):
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

    def _rest_base_sensor_reference_list(self, name = None):
        """ list sensor references
            @param name : sensor reference name
        """ 
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("sensor_reference")
        if name == None:
            for sensor_reference in self._db.list_sensor_reference_data():
                json_data.add_data(sensor_reference)
        else:
            sensor_reference = self._db.get_sensor_reference_data_by_name(name)
            if sensor_reference is not None:
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

    def _rest_base_actuator_feature_list(self, name = None):
        """ list actuator features
            @param name : actuator feature name
        """
        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("actuator_feature")
        if name == None:
            for actuator_feature in self._db.list_actuator_features():
                json_data.add_data(actuator_feature)
        else:
            actuator_feature = self._db.get_actuator_feature_by_name(name)
            if actuator_feature is not None:
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
        json_data.set_json(self.jsonp, self.jsonp_cb)
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
                                         self.get_parameters("room_id"), \
                                         self.get_parameters("description"), \
                                         self.get_parameters("reference"), \
                                         self.get_parameters("is_resetable"), \
                                         self.get_parameters("initial_value"), \
                                         self.get_parameters("is_value_changeable_by_user"), \
                                         self.get_parameters("unit_of_stored_values"))
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
        print "Call rest_module"
        if len(self.rest_request) < 2:
            self.send_http_response_error(999, "Url too short", self.jsonp, self.jsonp_cb)
            return

        json_data = JSonHelper("OK")
        json_data.set_jsonp(self.jsonp, self.jsonp_cb)
        json_data.set_data_type("module")

        ### start #####################################
        if self.rest_request[0] == "start":
            print "start!!"
        elif self.rest_request[0] == "stop":
            print "stop!!"

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

    def set_ok(self):
        """ set ok status
        """
        self._status = '"status" : "OK", "code" : 0, "description" : "",'

    def set_error(self, code=0, description=None):
        """ set error status
            @param code : error code
            @param description : error description
        """
        self._status = '"status" : "ERROR", "code" : ' + str(code) + ', "description" : "' + description + '",'

    def set_data_type(self, type):
        """ set data type
            @param type : data type
        """
        self._data_type = type

    def add_data(self, data):
        """ add data to json structure in 'type' table
            @param data : data to add
        """
        data_out = "{"
        self._nb_data_values += 1

        # dirty issue to force data not to be in cache
        print data
        #if hasattr(data, 'id') or hasattr(data, 'reference'):    # for all
        #    pass
        if hasattr(data, 'area'):  # for room
            pass

        if data == None:
            return
        for key in data.__dict__:
            #print "#> "+ str(key) + " (" + str( type(data.__dict__[key]).__name__) + ")  : " + str(data.__dict__[key])
            type_data = type(data.__dict__[key]).__name__
            if type_data == "int" or type_data == "float" or type_data == "bool":
                data_out += '"' + key + '" : ' + str(data.__dict__[key]) + ','
            elif type_data == "unicode":
                data_out += '"' + key + '" : "' + data.__dict__[key] + '",'
            elif type_data == "NoneType":
                data_out += '"' + key + '" : "None",'
            elif type_data == "Area" or type_data == "Room":
                data_out += '"' + key + '" : {'
                for key_dmg in data.__dict__[key].__dict__:
                    type_data_dmg = type(data.__dict__[key].__dict__[key_dmg]).__name__
                    if type_data_dmg == "int" or type_data_dmg == "float":
                        data_out += '"' + key_dmg + '" : ' + str(data.__dict__[key].__dict__[key_dmg]) + ','
                    elif type_data_dmg == "unicode":
                        data_out += '"' + key_dmg + '" : "' + data.__dict__[key].__dict__[key_dmg] + '",'
                data_out = data_out[0:len(data_out)-1] + '},'
        self._data_values += data_out[0:len(data_out)-1] + '},'
            

        

    def get(self):
        """ getter for all json data created
            @return json or jsonp data
        """
        if self._jsonp is True and self._jsonp_cb != "":
            json_buf = "%s (" % self._jsonp_cb
        else:
            json_buf = ""

        if self._data_type != "":
            json_buf += '{' + self._status + '"' + self._data_type + '" : [' + \
                   self._data_values[0:len(self._data_values)-1] + ']' + '}'
        else:
            json_buf += '{' + self._status[0:len(self._status)-1] + '}'

        if self._jsonp is True and self._jsonp_cb != "":
            json_buf += ")"
        print json_buf
        return json_buf
        
    



if __name__ == '__main__':
    #main()
    http_server = Rest("127.0.0.1", "8080")
    http_server.start()
    #serv = Rest("192.168.0.10", "80")




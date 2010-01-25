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

- RestHandler.do_GET
- RestHandler.do_POST
- RestHandler.rest_command
- RestHandler.rest_xpl_cmnd
- RestHandler.send_http_response_ok
- RestHandler.send_http_response_error

- XmlRpcDbHelper


@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.lib.xplconnector import *
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.module import *
from domogik.common import logger
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from domogik.common.database import DbHelper
import json




################################################################################
class Rest(xPLModule):

    def __init__(self, ip, port):
        xPLModule.__init__(self, name = 'rest')
        # logging initialization
        l = logger.Logger('REST')
        self._log = l.get_logger()
        self._log.info("Rest Server initialisation...")
        # DB Helper
        self._db = DbHelper()

        server = HTTPServerWithParam((ip, int(port)), RestHandler, handler_params = [self])
        print 'Start REST server on port %s...' % port
        server.serve_forever()


    def get_helper(self):
        return self._db


################################################################################
class HTTPServerWithParam(HTTPServer):
    """ Extends HTTPServer to allow send params to the Handler.
    """

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, handler_params = []):
        HTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.handler_params = handler_params

################################################################################
class RestHandler(BaseHTTPRequestHandler):


######
# GET/POST processing
######

    def do_GET(self):
        """ Process GET requests
        """

        print "==== GET ============================================"
        # Create shorter access : self.server.handler_params[0].* => self.*
        self._move_namespace()

        if self.path[-1:] == "/":
            self.path = self.path[0:len(self.path)-1]
        print "PATH : " + self.path
        tab_path = self.path.split("/")

        # Get type of request : /command, /xpl-cmnd, /base, etc
        if len(tab_path) <= 1:
            self.send_http_response_error("No type given")
            return
        self.rest_type = tab_path[1].lower()
        self.rest_request = tab_path[2:]
        print "TYPE    : " + self.rest_type
        print "Request : " + str(self.rest_request)

        if self.rest_type == "command":
            # TODO will be to move in do_POST
            self.rest_command()
        elif self.rest_type == "xpl-cmnd":
            self.rest_xpl_cmnd()
        elif self.rest_type == "base":
            # specific for GET
            self.rest_base_get()
        else:
            self.send_http_response_error("Type [" + self.rest_type + "] is not supported")
            return



    def do_POST(self):
        """ Process POST requests
        """

        print "==== POST ==========================================="
        # Create shorter access : self.server.handler_params[0].* => self.*
        self._move_namespace()

        if self.path[-1:] == "/":
            self.path = self.path[0:len(self.path)-1]
        print "PATH : " + self.path
        tab_path = self.path.split("/")

        # Get type of request : /command, /xpl-cmnd, /base, etc
        self.rest_type = tab_path[1].lower()
        self.rest_request = tab_path[2:]
        print "TYPE    : " + self.rest_type
        print "Request : " + str(self.rest_request)

        if self.rest_type == "xpl-cmnd":
            self.rest_xpl_cmnd()
        elif self.rest_type == "base":
            # specific for POST
            self.rest_base_post() 
        else:
            self.send_http_response_error("Type [" + self.rest_type + "] is not supported")



    def _move_namespace(self):
        """ Create shorter access : self.server.handler_params[0].* => self.*
        """
        self._db = self.server.handler_params[0]._db
        self._myxpl = self.server.handler_params[0]._myxpl
        self._log = self.server.handler_params[0]._log



######
# /command processing
######

    def rest_command(self):
        print "Call rest_command"
        self.command_techno = self.rest_request[0]
        self.command_element = self.rest_request[1]
        self.command_command = self.rest_request[2]
        self.command_optionnal = self.rest_request[3:]
        print "Techno    : %s" % self.command_techno
        print "Element   : %s" % self.command_element
        print "Command   : %s" % self.command_command
        print "Optionnal : %s" % str(self.command_optionnal)



######
# /xpl-cmnd processing
######

    def rest_xpl_cmnd(self):
        """ Send xPL message given in REST url
            1/ Decode and check URL
            2/ Send message
        """

        print "Call rest_xpl_cmnd"
        if len(self.rest_request) == 0:
            self.send_http_response_error("Target not given")
            return
        self.xpl_target = self.rest_request[0]
        if len(self.rest_request) == 1:
            self.send_http_response_error("Schema not given")
            return
        self.xpl_cmnd_schema = self.rest_request[1]

        # Init xpl message
        message = XplMessage()
        message.set_type('xpl-cmnd')
        if self.xpl_target.lower() != "all":
            message.set_header(target=self.xpl_target)
        message.set_schema(self.xpl_cmnd_schema)
  
        ii = 0
        for val in self.rest_request:
            # We pass target and schema
            if ii > 1:
                # Parameter
                if ii % 2 == 0:
                    param = val
                # Value
                else:
                    value = val
                    message.add_data({param : value})
            ii = ii + 1

        # no parameters
        if ii == 2:
            self.send_http_response_error("No parameters specified")
            return
        # no value for last parameter
        if ii % 2 == 1:
            self.send_http_response_error("Value missing for last parameter")
            return

        print "Send message : %s" % message
        self._myxpl.send(message)

        # REST processing finished and OK
        self.send_http_response_ok()

        # TODO : send result : "{status : 'ok', code : '0', description : ''}"



######
# /base processing
######

    def rest_base_get(self):
        """ get data in database
            1/ Decode and check URL
            2/ call the good fonction to get data
        """
        print "Call rest_base_get"
        if len(self.rest_request) < 2:
            self.send_http_response_error("Url too short")
            return

        ### area #####################################
        if self.rest_request[0] == "area":

            ### list
            if self.rest_request[1] == "list":
                if len(self.rest_request) == 2:
                    self._rest_base_area_list()
                elif len(self.rest_request) == 3:
                    self.send_http_response_error("Wrong syntax for " + self.rest_request[1])
                else:
                    if self.rest_request[2] == "by-id":
                        self._rest_base_area_list(id=self.rest_request[3])

            ### add
            elif self.rest_request[1] == "add":
                if len(self.rest_request) == 4:
                    self._rest_base_area_add(name=self.rest_request[2], description=self.rest_request[3])
                else:
                    self.send_http_response_error("Wrong syntax for " + self.rest_request[1])

            ### del
            elif self.rest_request[1] == "del":
                if len(self.rest_request) == 3:
                    self._rest_base_area_del(id=self.rest_request[2])
                else:
                    self.send_http_response_error("Wrong syntax for " + self.rest_request[1])

            ### others
            else:
                self.send_http_response_error(self.rest_request[1] + " not allowed for " + self.rest_request[0])
                return

        ### room #####################################
        elif self.rest_request[0] == "room":
            print "TODO !!"

        ### device #####################################
        elif self.rest_request[0] == "device":
            print "TODO !!"

        ### others ###################################
        else:
            self.send_http_response_error(self.rest_request[0] + " not allowed")
            return




    def rest_base_post(self):
        """ create or update data in database
            1/ Decode and check URL
            2/ call the good fonction to create or update data
        """
        print "TODO !!!!!!"









    def _rest_base_area_list(self, id = None):
        result = "{status : 'OK', description: '', area : ["
        if id == None:
            for area in self._db.list_areas():
                result += "{id : '%s', name : '%s', description : '%s'}," % (area.id, area.name, area.description)
            result = result[0:len(result)-1]
        else:
            area = self._db.get_area_by_id(id)
            if area is not None:
                result += "{id : '%s', name : '%s', description : '%s'}" % (area.id, area.name, area.description)
        result += "]}"
        print result
        self.send_http_response_ok(result)
        # TODO : send result properly


    def _rest_base_area_add(self, name = None, description = None):
        area = self._db.add_area(name, description)
        result = "{status : 'OK', description: '', area : ["
        result += "{id : '%s', name : '%s', description : '%s'}" % (area.id, area.name, area.description)
        result += "]}"
        print result
        self.send_http_response_ok(result)
        # TODO : send result properly


    def _rest_base_area_del(self, id=None):
        # Check existence
        area = self._db.get_area_by_id(id)
        if area is not None:
            self._db.del_area(id)
            result = "{status : 'OK', description: '', area : ["
            result += "{id : '%s', name : '%s', description : '%s'}" % (area.id, area.name, area.description)
            result += "]}"
        else:
            result = "{status : 'KO', description : 'No data'}"
        print result
        self.send_http_response_ok(result)




######
# HTTP return
######

    def send_http_response_ok(self, data = ""):
        self.send_response(200)
        self.send_header('Content-type',    'text/html')
        self.end_headers()
        if data:
            self.wfile.write(data);
        ### TODO : log this


    def send_http_response_error(self, errMsg):
        msg = 'Error : ' + errMsg
        self.send_error(500,msg)
        ### TODO : log this





################################################################################
#class XmlRpcDbHelper():
#    ''' This class provides a mapping of DbHelper methods to use them throw REST
#    '''
#
#    def __init__(self):
#        self._db = DbHelper()
#
#    def get_helper(self):
#        return self._db
#####
## Areas
#####
#
#    def list_areas(self):
#        ''' Get the list of areas and return it as a list of tuples
#        @return a list of tuple (id, name, description)
#        '''
#        areas = self._db.list_areas()
#        res = []
#        for area in areas:
#            res.append((area.id, area.name, area.description))
#        return res






def main():
    try:
        port = 8080
        server = HTTPServer(('', port), RestHandler)
        print 'Start REST server on port %s...' % port
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    #main()
    serv = Rest("127.0.0.1", "8080")
    #serv = Rest("192.168.0.10", "80")




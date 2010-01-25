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




################################################################################
class Rest(xPLModule):

    def __init__(self, ip, port):
        xPLModule.__init__(self, name = 'REST')
        # logging initialization
        l = logger.Logger('REST')
        self._log = l.get_logger()
        self._log.info("Rest Server initialisation...")

        server = HTTPServerWithParam((ip, int(port)), RestHandler, handler_params = [1,2,3])
        print 'Start REST server on port %s...' % port
        server.serve_forever()

        # DB Helper
        self._db = DbHelper()

    def get_helper(self):
        return self._db


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
        print "==== GET ============================================"
        print self.server.handler_params
        print "====================================================="
        if self.path[-1:] == "/":
            self.path = self.path[0:len(self.path)-1]
        print "PATH : " + self.path
        tab_path = self.path.split("/")

        # Get type of request : /command, /xpl-cmnd, /base, etc
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



    def do_POST(self):
        print "==== POST ==========================================="
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
        #self._myxpl.send(message)

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

        if self.rest_request[0] == "area":
            if self.rest_request[1] == "list":
                for area in self._db.list_areas():
                    print "-- AREA --"
                    print area

            else:
                self.send_http_response_error("GET : " +  self.rest_request[1] + " not allowed for " + self.rest_request[0])
                return
        elif self.rest_request[0] == "room":
            print "TODO !!"
        elif self.rest_request[0] == "device":
            print "TODO !!"
        else:
            self.send_http_response_error("GET : " +  self.rest_request[0] + " not allowed")
            return




    def rest_base_post(self):
        """ create or update data in database
            1/ Decode and check URL
            2/ call the good fonction to create or update data
        """
        print "TODO !!!!!!"



######
# HTTP return
######

    def send_http_response_ok(self):
        self.send_response(200)
        self.send_header('Content-type',    'text/html')
        self.end_headers()


    def send_http_response_error(self, errMsg):
        msg = 'Error : ' + errMsg
        self.send_error(500,msg)





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




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


class Rest(xPLModule):

    def __init__(self, ip, port):
        xPLModule.__init__(self, name = 'REST')
        # logging initialization
        l = logger.Logger('REST')
        self._log = l.get_logger()
        self._log.info("Rest Server initialisation...")

        server = HTTPServer((ip, int(port)), RestHandler)
        print 'Start REST server on port %s...' % port
        server.serve_forever()


class RestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print "==== GET ============================================"
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
        else:
            self.send_http_response_error("Type [" + self.rest_type + "] is not supported")



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



    def send_http_response_ok(self):
        self.send_response(200)
        self.send_header('Content-type',    'text/html')
        self.end_headers()


    def send_http_response_error(self, errMsg):
        msg = 'Error : ' + errMsg
        self.send_error(500,msg)



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
    serv = Rest("192.168.0.10", "80")




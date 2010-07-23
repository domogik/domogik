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
==============

IPX 800 relay board support. www.gce-electronics.com

Implements
==========

- IPX

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import socket
import traceback
import time


# For searching IPX with UDP request
IPX_UDP_HOST = ''
IPX_UDP_PORT = 30303
IPX_SEARCH_REQ = "Discovery: Who is out there?"
IPX_SEARCH_RESP = "RELAYBOARD"
IPX_SEARCH_TIMEOUT = 5


class IPXException:                                                         
    """                                                                         
    Ipx exception                                                           
    """                                                                         
                                                                                
    def __init__(self, value):                                                  
        self.value = value                                                      
                                                                                
    def __str__(self):                                                          
        return self.repr(self.value)           
        
        
class IPX:

    def __init__(self, log, cb):
        """ Init IPX object
            @param log : log instance
            @param cb : callback
        """
        self._log = log
        self._cb = cb

    def open(self, host, port):
        """ Try to access to IPX board and return error if not possible
            @param ip : ip or dns of host
            @param port: port
        """
        print "TODO"
            
    def find(self):
        """ Try to find availables IPX boards on network
        """
        # open socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(IPX_SEARCH_TIMEOUT)

        # send Discover Message
        s.sendto(IPX_SEARCH_REQ, ('<broadcast>', IPX_UDP_PORT))

        # wait for answer until IPX_SEARCH_TIMEOUT expires
        ipx_list = []
        while 1:
            try:
                message, address = s.recvfrom(8192)
                if message.split("\n")[0].strip() == IPX_SEARCH_RESP:
                    print address[0]
                    ipx_list.append(address[0])
            except socket.timeout:
                break
    
        return ipx_list

if __name__ == "__main__":
    ipx = IPX(None, None)
    print ipx.find()

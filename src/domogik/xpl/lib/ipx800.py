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
import urllib
from xml.dom import minidom


# For searching IPX with UDP request
IPX_UDP_HOST = ''
IPX_UDP_PORT = 30303
IPX_SEARCH_REQ = "Discovery: Who is out there?"
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
        self.led = {}  # relays
        self.btn = {}  # digital input
        self.an = {}   # analogic input

    def open(self, host, port):
        """ Try to access to IPX board and return error if not possible
            @param ip : ip or dns of host
            @param port: port
        """
        # try to get status.xml on given board.
        # if it fails,raise an Exception
        print("Opening board : %s:%s" % (host, port))
        self.url = "http://%s:%s" % (host, port)
        self.url_status = "%s/status.xml" % self.url

        # setting status will raise an error if no access to status.xml
        self.get_status(first = True)


    def listen(self, interval):
        """ Listen for relay board in background
            @param interval : interval between each read of status
        """
        while True:
            self.get_status()
            time.sleep(interval)


    def set_relay(self, num, state):
        """" Set relay <num> to state <state>
             @param num : relay number (0, 1, 2,....)
             @param state : HIGH, LOW
        """
        print "TODO"


    def pule_relay(self, num):
        """" Send a pulse on relay <num>
             @param num : relay number (0, 1, 2,....)
        """
        print "TODO"



    def get_status(self, first = False):
        """ Get status.xml content on board
            @param first : optionnal : if True, first call so we will check
                           number of relay, input (ana and digi)
        """
        try:
            resp = urllib.urlopen(self.url_status)
        except IOError as e:
            raise IPXException("Error while accessing to '%s' : %s" % (self.url_status, traceback.format_exc())) 

        xml = resp.read()
        dom = minidom.parseString(xml)
        response = dom.getElementsByTagName("response")[0]
        
        # First call : count items
        if first == True:
            self.get_count(response)

        # List each relay status
        self.get_status_of(dom, "led")
        print "LED=%s" % self.led
        self.get_status_of(dom, "btn")
        print "BTN=%s" % self.btn
        self.get_status_of(dom, "an")
        print "AN=%s" % self.an


    def get_status_of(self, dom, elt):
        """ get value for <eltX> in <dom> and store then in self.<elt>[X]
            @param dom : xml data
            @param elt : led, btn, an
        """
        start = eval("self.start_" + elt)
        end = eval("self.nb_" + elt) + start 
        for idx in range(start, end):
            resp = dom.getElementsByTagName("%s%s" % (elt, idx))[0].firstChild.nodeValue
            setattr("self.%s[%s]" % (elt, idx), resp)


    def get_count(self, dom):
        """ count number of relay, input
            @param dom : xml data
        """
        print dom.toxml()
        self.start_led, self.nb_led = self.get_count_of(dom, "led")
        print("Number of relay : %s (start at %s)" % (self.nb_led, self.start_led))
        self.start_btn, self.nb_btn = self.get_count_of(dom, "btn")
        print("Number of digital input : %s (start at %s)" % (self.nb_btn, self.start_btn))
        self.start_an, self.nb_an = self.get_count_of(dom, "an")
        print("Number of anal input : %s (start at %s)" % (self.nb_an, self.start_an))


    def get_count_of(self, dom, elt):
        """ count number of <eltX> in <dom>
            @param dom : xml data
            @param elt : start of tag name
        """
        # start at 0 or 1 ?
        try:
            foo = dom.getElementsByTagName("%s0" % elt)[0]
            start = 0
        except IndexError:
            try:
                foo = dom.getElementsByTagName("%s1" % elt)[0]
                start = 1
            except IndexError:
                return 0, 0
        
        # count
        idx = start
        while True:
            try:
                foo = dom.getElementsByTagName("%s%s" % (elt, str(idx)))[0]
            except IndexError:
                break
            idx += 1
        return start, idx - start
        

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
                name = message.split("\n")[0].strip()
                print address[0]
                ipx_list.append((address[0], name))
            except socket.timeout:
                break
    
        return ipx_list

if __name__ == "__main__":
    try:
        ipx = IPX(None, None)
        #print ipx.find()
        ipx.open("192.168.0.102", 80)
        ipx.listen(10)
    except IPXException as e:
        print e.value

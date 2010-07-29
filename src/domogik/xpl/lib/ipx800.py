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
import urllib2
from xml.dom import minidom
import copy


# For searching IPX with UDP request
IPX_UDP_HOST = ''
IPX_UDP_PORT = 30303
IPX_SEARCH_REQ = "Discovery: Who is out there?"
IPX_SEARCH_TIMEOUT = 5

# status
IPX_LED_HIGH = "1"
IPX_LED_LOW = "0"
IPX_BTN_HIGH = "up"
IPX_BTN_LOW = "down"

# response
IPX_SUCCESS = "Success!"


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
        self.count = {}# counters

    def open(self, name, host):
        """ Try to access to IPX board and return error if not possible
            @param ip : ip or dns of host
        """
        self.name= name
        # define all urls
        self.url = "http://%s" % (host)
        self.url_status = "%s/status.xml" % self.url
        self.url_cgi_change = "%s/leds.cgi?led=" % self.url
        self.url_cgi_pulse = "%s/rlyfs.cgi?rlyf=" % self.url
        self.url_cgi_reset_counter = "%s/counter.cgi?count=" % self.url

        # setting status will raise an error if no access to status.xml
        self._log.info("Opening board : %s" % (host))
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
        # we get instant status of board
        self.get_status()
        actual = self.led[num]
        # do we need to change status ?
        if actual == IPX_LED_HIGH and state == "HIGH" or \
           actual == IPX_LED_LOW and state == "LOW":
            # no need to change status
            self._log.debug("No need to change 'led%s' status to '%s'" % (num, state))
            # no change but you should send a xpl-trig to tell that the order was received
            self.send_change({'elt' : 'led',
                              'num' : num,
                              'value' : actual})
            return

        # change status
        url = self.url_cgi_change + str(num)
        try:
            tricky = urllib2.urlopen("http://192.168.0.10/")
            resp = urllib2.urlopen(url)
        except IOError as e:
            error = "Error while accessing to '%s' : %s" % (self.url_status, traceback.format_exc())
            print error
            self._log.error(error)
            raise IPXException(error)
            return
        res  = resp.read()
        if res[0:8] != IPX_SUCCESS:
            self._log.error("Error while changing 'led%s' to '%s'" % (num, state))
        else:
            self._log.debug("Changing 'led%s' to '%s' successfully" % (num, state))
            # refresh status (for sending a xpl-trig)
            self.get_status()


    def pulse_relay(self, num):
        """" Send a pulse on relay <num>
             @param num : relay number (0, 1, 2,....)
        """
        # we get instant status of board
        self.get_status()

        # send pulse
        url = self.url_cgi_pulse + str(num)
        try:
            tricky = urllib2.urlopen("http://192.168.0.10/")
            resp = urllib2.urlopen(url)
        except IOError as e:
            error = "Error while accessing to '%s' : %s" % (self.url_status, traceback.format_exc())
            print error
            self._log.error(error)
            raise IPXException(error)
            return
        res  = resp.read()
        if res[0:8] != IPX_SUCCESS:
            self._log.error("Error while changing 'led%s' to 'PULSE'" % num)
        else:
            print("Changing 'led%s' to 'PULSE' successfully" % num)
            # refresh status (for sending a xpl-trig)
            self.send_change({'elt' : 'led',
                              'num' : num,
                              'value' : IPX_LED_HIGH})


    def reset_counter(self, num):
        """" Reset counter <num>
             @param num : counter number (0, 1, 2,....)
        """
        # we get instant status of board
        self.get_status()

        # send reset order
        url = self.url_cgi_reset_counter + str(num)
        try:
            tricky = urllib2.urlopen("http://192.168.0.10/")
            resp = urllib2.urlopen(url)
        except IOError as e:
            error = "Error while accessing to '%s' : %s" % (self.url_status, traceback.format_exc())
            print(error)
            send._log.error(error)
            raise IPXException(error)
            return
        res  = resp.read()
        if res[0:8] != IPX_SUCCESS:
            send._log.error("Error while reseting 'count%s'" % num)
        else:
            self._log.debug("Reseting 'count%s' successfully" % num)
            # refresh status (for sending a xpl-trig)
            self.get_status()


    def send_change(self, data):
        """ Send changes on xpl
            @param data : dictionnay with data
            Notice that 'pulse' status is never sent as it has no sense for UI :
            we send HIGH or LOW (or value for anal/counter)
        """
        self._log.debug("Status changed : %s" % data)
        device = "%s-%s%s" % (self.name, data['elt'], data['num'])

        # translate values
        if data['elt'] == "led" and data['value'] == IPX_LED_HIGH:
            current = "HIGH"
        elif data['elt'] == "led" and data['value'] == IPX_LED_LOW:
            current = "LOW"
        elif data['elt'] == "btn" and data['value'] == IPX_BTN_HIGH:
            current = "HIGH"
        elif data['elt'] == "btn" and data['value'] == IPX_BTN_LOW:
            current = "LOW"

        # translate type
        if data['elt'] == "led":
            type = 'output'
        if data['elt'] == "btn":
            type = 'input'
        if data['elt'] == "an":
            type = 'voltage'
        if data['elt'] == "count":
            type = 'count'
         
        self._cb(device, current, type)


    def get_status(self, first = False):
        """ Get status.xml content on board
            @param first : optionnal : if True, first call so we will check
                           number of relay, input (ana and digi)
        """
        try:
            tricky = urllib2.urlopen("http://192.168.0.10/")
            resp = urllib2.urlopen(self.url_status)
        except IOError as e:
            error = "Error while accessing to '%s' : %s" % (self.url_status, traceback.format_exc())
            print(error)
            self._log.error(error)
            raise IPXException(error)
            return

        xml = resp.read()
        dom = minidom.parseString(xml)
        response = dom.getElementsByTagName("response")[0]
        
        # First call : count items
        if first == True:
            self.get_count(response)

        # Save old status
        else:
           self.old_led = copy.copy(self.led)
           self.old_btn = copy.copy(self.btn)
           self.old_an = copy.copy(self.an)
           self.old_count = copy.copy(self.count)

        # List each status
        self.get_status_of(dom, "led", first)
        #print "LED=%s" % self.led
        self.get_status_of(dom, "btn", first)
        #print "BTN=%s" % self.btn
        self.get_status_of(dom, "an", first)
        #print "AN=%s" % self.an
        self.get_status_of(dom, "count", first)
        #print "COUNT=%s" % self.count


    def get_status_of(self, dom, elt, first = False):
        """ get value for <eltX> in <dom> and store then in self.<elt>[X]
            @param dom : xml data
            @param elt : led, btn, an
            @param first : first launch ?
        """
        if first == False:
            old_foo = getattr(self, "old_" + elt)
        start = getattr(self, "start_" + elt)
        end = getattr(self, "nb_" + elt) + start 
        for idx in range(start, end):
            resp = dom.getElementsByTagName("%s%s" % (elt, idx))[0].firstChild.nodeValue
            foo = getattr(self, elt)
            foo[idx] = resp
            # status of element changed : we will have to send a xPl message
            if first == False and old_foo[idx] != foo[idx]:
                self.send_change({'elt' : elt,
                                  'num' : idx,
                                  'value' : resp})


    def get_count(self, dom):
        """ count number of relay, input
            @param dom : xml data
        """
        print dom.toxml()
        self.start_led, self.nb_led = self.get_count_of(dom, "led")
        self._log.info("Number of relay : %s (start at %s)" % (self.nb_led, self.start_led))
        self.start_btn, self.nb_btn = self.get_count_of(dom, "btn")
        self._log.info("Number of digital input : %s (start at %s)" % (self.nb_btn, self.start_btn))
        self.start_an, self.nb_an = self.get_count_of(dom, "an")
        self._log.info("Number of anal input : %s (start at %s)" % (self.nb_an, self.start_an))
        self.start_count, self.nb_count = self.get_count_of(dom, "count")
        self._log.info("Number of counters : %s (start at %s)" % (self.nb_count, self.start_count))


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
                self._log.info("Find IPX board : %s" % address[0])
                ipx_list.append((address[0], name))
            except socket.timeout:
                break
    
        return ipx_list

if __name__ == "__main__":
    try:
        ipx = IPX(None, None)
        #print ipx.find()
        ipx.open("ipxboard", "192.168.0.102")
        #print "----"
        ipx.set_relay(0, "HIGH")
        time.sleep(5)
        ipx.set_relay(0, "LOW")
        #ipx.set_relay(0, "HIGH")
        #ipx.set_relay(0, "LOW")
        #ipx.pulse_relay(0)
    except IPXException as e:
        print e.value

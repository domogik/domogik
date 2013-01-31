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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import socket
import traceback
import time
from xml.dom import minidom
import copy
import urllib2


# IPX800 models
IPX800_MODELS = ['ipx800v1', 'ipx800pro', 'ipx800v2', 'ipx800v3']
IPX800_MODELS_LIKE_V2 = ['ipx800v1', 'ipx800pro', 'ipx800v2']
IPX800_MODELS_LIKE_V3 = ['ipx800v3']

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


class IPXException(Exception):
    """
    Ipx exception
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class IPX:
    """ Library to use IXP800 board
    """

    def __init__(self, log, callback, stop):
        """ Init IPX object
            @param log : log instance
            @param callback : callback
            @param stop : stop event
        """
        self._log = log
        self._callback = callback
        self._stop = stop
        self.login = None
        self.password = None
        self.model = ""
        self.name = ""
        self.url = ""
        self.url_status = ""
        self.url_cgi_change = ""
        self.url_cgi_pulse = ""
        self.url_cgi_reset_counter = ""

        self.ipx_led = {}        # relays
        self.ipx_btn = {}        # digital input
        self.ipx_an = {}         # analogic input for ipx800 v1, pro, v2
        self.ipx_analog = {}     # analogic input for ipx800 v3
        self.ipx_anselect = {}   # analogic type for ipx800 v3
        self.ipx_count = {}      # counters

        self.start_led = 0       # relays
        self.start_btn = 0       # digital input
        self.start_an = 0        # analogic input for ipx800 v1, pro, v2
        self.start_analog = 0    # analogic input for ipx800 v3
        self.start_anselect = 0  # analogic type for ipx800 v3
        self.start_count = 0     # counters

        self.nb_led = 0          # relays
        self.nb_btn = 0          # digital input
        self.nb_an = 0           # analogic input for ipx800 v1, pro, v2
        self.nb_analog = 0       # analogic input for ipx800 v3
        self.nb_anselect = 0     # analogic type for ipx800 v3
        self.nb_count = 0        # counters

        self.ipx_old_led = {}    # relays
        self.ipx_old_btn = {}    # digital input
        self.ipx_old_an = {}     # analogic input for ipx800 v1, pro, v2
        self.ipx_old_analog = {} # analogic input for ipx800 v3
        self.ipx_old_anselect ={}# analogic type for ipx800 v3
        self.ipx_old_count = {}  # counters

    def open(self, name, host, model, login = None, password = None):
        """ Try to access to IPX board and return error if not possible
        """
        if model not in IPX800_MODELS:
            error = "Bad ipx800 model : %s. Available list : %s" % (model, IPX800_MODELS)
            print(error)
            self._log.error(error)
            raise IPXException(error)
        self.model = model
            
        self.name = name
        # define all urls
        self.url = "http://%s" % (host)
        self.login = login
        self.password = password
        self.url_status = "%s/status.xml" % self.url
        self.url_cgi_change = "%s/leds.cgi?led=" % self.url
        self.url_cgi_pulse = "%s/rlyfs.cgi?rlyf=" % self.url
        self.url_cgi_reset_counter = "%s/counter.cgi?count=" % self.url

        # setting status will raise an error if no access to status.xml
        msg = "Opening board : %s. Model : %s" % (host, model)
        self._log.info(msg)
        print(msg)
        self.get_status(is_first = True)

    def urlopen(self, url):
        # Login/password management
        # description about all this can be found here : 
        # http://www.voidspace.org.uk/python/articles/authentication.shtml
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.login, self.password)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
        return urllib2.urlopen(url)

    def get_status_for_helper(self):
        """ Return status for helper
        """
        status = []
        status.append("List of relay :")
        for idx in self.ipx_led:
            status.append(" - led%s : %s" % (idx, self.ipx_led[idx]))
        status.append("List of digital input :")
        for idx in self.ipx_btn:
            status.append(" - btn%s : %s" % (idx, self.ipx_btn[idx]))
        status.append("List of analog input :")
        if self.model in IPX800_MODELS_LIKE_V2:
            for idx in self.ipx_an:
                status.append(" - an%s : %s" % (idx, self.ipx_an[idx]))
        if self.model in IPX800_MODELS_LIKE_V3:
            for idx in self.ipx_analog:
                status.append(" - anselect%s : %s" % (idx, self.ipx_anselect[idx]))
                status.append(" - analog%s : %s" % (idx, self.ipx_analog[idx]))
        status.append("List of counters :")
        for idx in self.ipx_count:
            status.append(" - count%s : %s" % (idx, self.ipx_count[idx]))
        return status



    def listen(self, interval):
        """ Listen for relay board in background
            @param interval : interval between each read of status
        """
        while not self._stop.isSet():
            self.get_status()
            self._stop.wait(interval)


    def set_relay(self, num, state):
        """" Set relay <num> to state <state>
             @param num : relay number (0, 1, 2,....)
             @param state : HIGH, LOW
        """
        # we get instant status of board
        self.get_status()
        actual = self.ipx_led[num]
        # do we need to change status ?
        if actual == IPX_LED_HIGH and state == "high" or \
           actual == IPX_LED_LOW and state == "low":
            # no need to change status
            self._log.debug("No need to change 'led%s' status to '%s'" % 
                            (num, state))
            # no change but you should send a xpl-trig to tell that 
            # the order was received
            self.send_change({'elt' : 'led',
                              'num' : num,
                              'value' : actual})
            return

        # change status
        url = self.url_cgi_change + str(num)
        try:
            resp = self.urlopen(url)
        except IOError:
            error = "Error while accessing to '%s' : %s" %  \
                     (self.url_status, traceback.format_exc())
            print(error)
            self._log.error(error)
            raise IPXException(error)
        except HTTPError:
            error = "Error while accessing to '%s' : %s" %  \
                     (self.url_status, traceback.format_exc())
            print(error)
            self._log.error(error)
            raise IPXException(error)
        res  = resp.read()
        if res[0:8] != IPX_SUCCESS:
            self._log.error("Error while changing 'led%s' to '%s'" % 
                            (num, state))
        else:
            self._log.debug("Changing 'led%s' to '%s' successfully" % 
                            (num, state))
            # refresh status (for sending a xpl-trig)
            self.get_status()


    def pulse_relay(self, num):
        """" Send a pulse on relay <num>
             @param num : relay number (0, 1, 2,....)
        """
        # we get instant status of board
        # finally no need to get status here (because we don't test old values)
        #self.get_status()

        # send pulse
        url = self.url_cgi_pulse + str(num)
        try:
            resp = self.urlopen(url)
        except IOError:
            error = "Error while accessing to '%s' : %s" % \
                     (self.url_status, traceback.format_exc())
            print(error)
            self._log.error(error)
            raise IPXException(error)
        res  = resp.read()
        if res[0:8] != IPX_SUCCESS:
            self._log.error("Error while changing 'led%s' to 'pulse'" % num)
        else:
            print("Changing 'led%s' to 'pulse' successfully" % num)
            # send change of status
            self.get_status()


    def reset_counter(self, num):
        """" Reset counter <num>
             @param num : counter number (0, 1, 2,....)
        """
        # we get instant status of board
        self.get_status()

        # send reset order
        url = self.url_cgi_reset_counter + str(num)
        try:
            resp = self.urlopen(url)
        except IOError:
            error = "Error while accessing to '%s' : %s" % \
                     (self.url_status, traceback.format_exc())
            print(error)
            self._log.error(error)
            raise IPXException(error)
        res  = resp.read()
        if res[0:8] != IPX_SUCCESS:
            self._log.error("Error while reseting 'count%s'" % num)
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
        # if no callback defined (used by helper for example), don't send changes
        if self._callback == None:
            return

        self._log.debug("Status changed : %s" % data)
        device = "%s-%s%s" % (self.name, data['elt'], data['num'])

        # translate values
        if data['elt'] == "led" and data['value'] == IPX_LED_HIGH:
            current = "high"
        elif data['elt'] == "led" and data['value'] == IPX_LED_LOW:
            current = "low"
        elif data['elt'] == "btn" and data['value'] == IPX_BTN_HIGH:
            current = "high"
        elif data['elt'] == "btn" and data['value'] == IPX_BTN_LOW:
            current = "low"
        else:
            current = float(data['value'])

        # translate type
        if data['elt'] == "led":
            elt_type = 'output'
        if data['elt'] == "btn":
            elt_type = 'input'
        if self.model in IPX800_MODELS_LIKE_V2:
            if data['elt'] == "an":       # ipx800 v1, pro, v2
                elt_type = 'voltage'
        if self.model in IPX800_MODELS_LIKE_V3:
            if data['elt'] == "analog":   # ipx800 v3
                # TODO : type to change in f(anselect)
                sel = self.ipx_anselect[data['num']]
                if sel == '0':
                    elt_type = 'generic'
                elif sel == '1':
                    elt_type = 'voltage'
                    current = current * 0.00323
                elif sel == '2':
                    elt_type = 'temp'
                    current = current * 0.323 - 50
                elif sel == '3':
                    elt_type = 'percent'
                    current = current * 0.09775
                elif sel == '4':
                    elt_type = 'temp'
                    current = ((current * 0.00323) - 1.63) / 0.0326
                elif sel == '5':
                    elt_type = 'percent'
                    current = (((current * 0.00323) / 3.3) - 0.1515) / 0.00636
                else:
                    elt_type = None
                
            # type of analogic data : used as a type : don't process as value
            if data['elt'] == "anselect":   # ipx800 v3
                return
        if data['elt'] == "count":
            elt_type = 'count'

        print("%s-%s(%s)-%s"  % (device, current, data['value'], elt_type))
        self._callback(device, current, elt_type)


    def get_status(self, is_first = False):
        """ Get status.xml content on board
            @param is_first : optionnal : if True, first call so we will check
                           number of relay, input (ana and digi)
        """
        try:
            resp = self.urlopen(self.url_status)
            xml = resp.read()

        except IOError:
            error = "IO Error while accessing to '%s' : %s" % \
                     (self.url_status, traceback.format_exc())
            print(error)
            self._log.error(error)
            raise IPXException(error)

        except:
            error = "Error while accessing to '%s' : %s" % \
                     (self.url_status, traceback.format_exc())
            print(error)
            self._log.error(error)
            raise IPXException(error)

        dom = minidom.parseString(xml)
        response = dom.getElementsByTagName("response")[0]

        # First call : count items
        if is_first == True:
            self.get_count(response)

        # Save old status
        else:
            self.ipx_old_led = copy.copy(self.ipx_led)
            self.ipx_old_btn = copy.copy(self.ipx_btn)
            if self.model in IPX800_MODELS_LIKE_V2:
                self.ipx_old_an = copy.copy(self.ipx_an)
            if self.model in IPX800_MODELS_LIKE_V3:
                self.ipx_old_anselect = copy.copy(self.ipx_anselect)
                self.ipx_old_analog = copy.copy(self.ipx_analog)
            self.ipx_old_count = copy.copy(self.ipx_count)

        # List each status
        self.get_status_of(dom, "led", is_first)
        self.get_status_of(dom, "btn", is_first)
        if self.model in IPX800_MODELS_LIKE_V2:
            self.get_status_of(dom, "an", is_first)
        if self.model in IPX800_MODELS_LIKE_V3:
            self.get_status_of(dom, "anselect", is_first)
            self.get_status_of(dom, "analog", is_first)
        self.get_status_of(dom, "count", is_first)


    def get_status_of(self, dom, elt, is_first = False):
        """ get value for <eltX> in <dom> and store then in self.<elt>[X]
            @param dom : xml data
            @param elt : led, btn, an
            @param is_first : first launch ?
        """
        if is_first == False:
            old_data = getattr(self, "ipx_old_%s" % elt)
        start = getattr(self, "start_" + elt)
        end = getattr(self, "nb_" + elt) + start
        for idx in range(start, end):
            resp = dom.getElementsByTagName("%s%s" % 
                                           (elt, idx))[0].firstChild.nodeValue
            data = getattr(self, "ipx_%s" % elt)
            data[idx] = resp
            # status of element changed : we will have to send a xPl message
            if is_first == True or (is_first == False and old_data[idx] != data[idx]):
                self.send_change({'elt' : elt,
                                  'num' : idx,
                                  'value' : resp})


    def get_count(self, dom):
        """ count number of relay, input
            @param dom : xml data
        """
        print(dom.toxml())
        self.start_led, self.nb_led = self.get_count_of(dom, "led")
        self._log.info("Number of relay : %s (start at %s)" % 
                       (self.nb_led, self.start_led))
        self.start_btn, self.nb_btn = self.get_count_of(dom, "btn")
        self._log.info("Number of digital input : %s (start at %s)" % 
                       (self.nb_btn, self.start_btn))
        if self.model in IPX800_MODELS_LIKE_V2:
            self.start_an, self.nb_an = self.get_count_of(dom, "an")
            self._log.info("Number of analogic input : %s (start at %s)" % 
                           (self.nb_an, self.start_an))
        if self.model in IPX800_MODELS_LIKE_V3:
            self.start_anselect, self.nb_anselect = self.get_count_of(dom, "anselect")
            self.start_analog, self.nb_analog = self.get_count_of(dom, "analog")
            self._log.info("Number of analogic input : %s (start at %s)" % 
                           (self.nb_analog, self.start_analog))
        self.start_count, self.nb_count = self.get_count_of(dom, "count")
        self._log.info("Number of counters : %s (start at %s)" % 
                       (self.nb_count, self.start_count))


    def get_count_of(self, dom, elt):
        """ count number of <eltX> in <dom>
            @param dom : xml data
            @param elt : start of tag name
        """
        # start at 0 or 1 ?
        try:
            data = dom.getElementsByTagName("%s0" % elt)[0]
            start = 0
        except IndexError:
            try:
                data = dom.getElementsByTagName("%s1" % elt)[0]
                start = 1
            except IndexError:
                return 0, 0

        # count
        idx = start
        while True:
            try:
                data = dom.getElementsByTagName("%s%s" % (elt, str(idx)))[0]
            except IndexError:
                break
            idx += 1
        return start, idx - start


    def find(self):
        """ Try to find availables IPX boards on network
        """
        # open socket
        my_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        my_sock.settimeout(IPX_SEARCH_TIMEOUT)

        # send Discover Message
        my_sock.sendto(IPX_SEARCH_REQ, ('<broadcast>', IPX_UDP_PORT))

        # wait for answer until IPX_SEARCH_TIMEOUT expires
        ipx_list = []
        while 1:
            try:
                message, address = my_sock.recvfrom(8192)
                name = message.split("\n")[0].strip()
                self._log.info("Find IPX board : %s" % address[0])
                ipx_list.append((address[0], name))
            except socket.timeout:
                break

        return ipx_list


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

Send demo data over xPL

Implements
==========

- DemoDataManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import XplTimer
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
#from domogik_packages.xpl.lib.demodata import DemoData, DemoUI, UIHandler
from domogik_packages.xpl.lib.demodata import DemoData, UIHandler
import threading
import datetime
from domogik.xpl.common.xplconnector import Listener

# for demo UI
import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

DEFAULT_PORT=40440


class DemoDataManager(XplPlugin):
    """ Sends demo data over xPL
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='demodata')

        ### Get config
        self._config = Query(self.myxpl, self.log)
        port = self._config.query('demodata', 'port')
        if port == None:
            port = DEFAULT_PORT 
        else:
            port = int(port)
        self.log.info("Listen port is %s" % port)

        self.log.info("Start creating the listeners")

        ### Create listeners for the fake actuator devices
        # RGB controller
        Listener(self.cmd_arduino_rgb, self.myxpl, {
            'schema': 'arduino.rgb',
            'xpltype': 'xpl-cmnd',
        })

        # Switch
        # Dimmer
        Listener(self.cmd_lighting_basic, self.myxpl, {
            'schema': 'lighting.basic',
            'xpltype': 'xpl-cmnd',
        })

        self.log.info("All listeners are created")

        ### Call the data creators
        self.log.info("Start all the data creator threads")
        demo = DemoData(self.log, self.send_sensor_basic, \
                                  self.send_teleinfo_basic)

        # weather data each minute
        self._weather_thr = XplTimer(60, \
                                     demo.weather_data, \
                                     self.myxpl)
        self._weather_thr.start()

        # teleinfo data each 10min
        self._teleinfo_thr = XplTimer(600, \
                                     demo.teleinfo_data, \
                                     self.myxpl)
        self._teleinfo_thr.start()

        # tank data each 1min
        self._tank_thr = XplTimer(60, \
                                  demo.tank_data, \
                                  self.myxpl)
        self._tank_thr.start()

        self.log.info("All the data creator threads created")

        self.enable_hbeat()

        # Launch the web UI
        #demo_ui = DemoUI()
        msg = "Launch the Web UI on port %s" % port
        print(msg)
        self.log.info(msg)
        self.add_stop_cb(self.stop_http)
        self.server = None
        self.server_ip = ''
        self.server_port = port
        self.start_http()

    def start_http(self):
        """ Start HTTP Server
        """
        self.server = HTTPServerWithParam((self.server_ip, int(self.server_port)), UIHandler, \
                                         handler_params = [self])
        self.server.serve_forever()

    def stop_http(self):
        """ Stop HTTP Server
        """
        self.server.stop_handling()

    def send_sensor_basic(self, device, type, current, units = None):
        """ Send sensor.basic xPL schema
            @param device : device
            @param type : type
            @param current : current
        """
        mess = "sensor.basic { device=%s, type=%s, current=%s}" % (device, type, current)
        print(mess)
        self.log.debug(msg)
        if current == "":
            return
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("sensor.basic")
        msg.add_data({"device" : device})
        msg.add_data({"type" : type})
        msg.add_data({"current" : current})
        if units != None:
            msg.add_data({"units" : units})
        self.myxpl.send(msg)

    def send_teleinfo_basic(self, frame):
        ''' Send a frame from teleinfo device to xpl
        @param frame : a dictionnary mapping teleinfo informations
        '''
        mess = "teleinfo.basic : %s" % frame
        print(mess)
        self.log.debug(mess)
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("teleinfo.basic")
        for key in frame:
            msg.add_data({ key : frame[key] })
        self.myxpl.send(msg)

    # RGB controller
    def cmd_arduino_rgb(self, message):
        device = message.data['device']
        command = message.data['command']
        color = message.data['color']
        # send symetric answer to simulate the device
        self.send_arduino_rgb(device, command, color)

    def send_arduino_rgb(self, device, command, color):
        mess = "arduino.rgb : device=%s, command=%s, color=%s" % (device, command, color)
        print(mess)
        self.log.debug(mess)
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema("arduino.rgb")
        msg.add_data({ 'device' : device })
        msg.add_data({ 'command' : command })
        msg.add_data({ 'color' : color })
        self.myxpl.send(msg)

    # Switch
    # Dimmer
    def cmd_lighting_basic(self, message):
        device = message.data['device']
        command = message.data['command']
        if message.data.has_key('fade-rate'):
            fade_rate = message.data['fade-rate']
        else: 
            fade_rate = None
        if message.data.has_key('level'):
            level = message.data['level']
        else: 
            level = None
        # send symetric answer to simulate the device
        self.send_lighting_device(device, command, level, fade_rate)

    def send_lighting_device(self, device, command, level = None, fade_rate = None):
        mess = "lighting.device : device=%s, command=%s, level=%s, fade_rate=%s" % (device, command, level, fade_rate)
        print(mess)
        self.log.debug(mess)
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema("lighting.device")
        msg.add_data({ 'device' : device })
        if level != None:
            msg.add_data({ 'level' : level })
        if fade_rate != None:
            msg.add_data({ 'fade-rate' : fade_rate })
        self.myxpl.send(msg)

    # Caller id
    def send_cid_basic(self, device, calltype, phone_number):
        # Notice that device is not used in this xpl schema
        mess = "cid.basic : calltype=%s, phone=%s" % (calltype, phone_number)
        print(mess)
        self.log.debug(mess)
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema("cid.basic")
        msg.add_data({ 'calltype' : calltype })
        msg.add_data({ 'phone' : phone_number })
        self.myxpl.send(msg)

    
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
        print("Make a last request to HTTP server to stop it")
        resp = urllib.urlopen("http://%s:%s" % (self.address[0], self.address[1]))


if __name__ == "__main__":
    DemoDataManager()

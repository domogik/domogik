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

Velbus usb support
=> based on rfxcom plugin

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-20012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.velbus import VelbusException
from domogik_packages.xpl.lib.velbus import VelbusDev
import threading
import re

class VelbusManager(XplPlugin):
    """
	Managages the velbus domogik plugin
    """
    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='velbus')
        self._config = Query(self.myxpl, self.log)
        # get the config values
        device_type = self._config.query('velbus', 'connection-type')
        if device_type == None:
            self.log.error('Devicetype is not configured, exitting') 
            print('Devicetype is not configured, exitting')
            self.force_leave()
            return
        device = self._config.query('velbus', 'device')
        #device = '192.168.1.101:3788'
        if device == None:
            self.log.error('Device is not configured, exitting') 
            print('Device is not configured, exitting')
            self.force_leave()
            return
        # validate the config vars
        if (device_type != 'serial') and (device_type != 'socket'):
            self.log.error('Devicetype must be socket or serial, exitting') 
            print('Devicetype must be socket or serial, exitting')
            self.force_leave()
            return
        if device_type == 'socket' and not re.match('[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}:[0-9]+', device):
            self.log.error('A socket device is in the form of <ip>:<port>, exitting') 
            print('A socket device is in the form of <ip>:<port>, exitting')
            self.force_leave()
            return

        # Init RFXCOM
        self.manager  = VelbusDev(self.log, self.send_xpl,
			self.send_trig, self.get_stop())
        self.add_stop_cb(self.manager.close)
        
        # Create a listener for all messages used by RFXCOM
        Listener(self.process_lighting_basic, self.myxpl,
                 {'xpltype': 'xpl-cmnd', 'schema': 'lighting.basic'})
        Listener(self.process_shutter_basic, self.myxpl,
                 {'xpltype': 'xpl-cmnd', 'schema': 'shutter.basic'})
        # Create listeners
        try:
            self.manager.open(device, device_type)
        except VelbusException as ex:
            self.log.error(ex.value)
            self.force_leave()
            return
        self.manager.scan()
            
        # Start reading RFXCOM
        listenthread = threading.Thread(None,
                                   self.manager.listen,
                                   "velbus-process-reader",
                                   (self.get_stop(),),
                                   {})
        self.register_thread(listenthread)
        listenthread.start()
        self.enable_hbeat()

    def send_xpl(self, schema, data):
        """ Send xPL message on network
        """
        self.log.info("schema:%s, data:%s" % (schema, data))
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema(schema)
        for key in data:
            msg.add_data({key : data[key]})
        self.myxpl.send(msg)

    def send_trig(self, message):
        """ Send xpl-trig given message
            @param message : xpl-trig message
        """
        self.myxpl.send(message)

    def process_lighting_basic(self, message):
        """ Process xpl chema lightning.basic
        """
        print message
        #self.send_xpl("lighting.device", message.data)
        device = message.data['device']
        chan = message.data['channel']
        if message.data["level"] == 'None':
            message.data["level"] = 0
        self.manager.send_level( device, chan, message.data["level"])

    def process_shutter_basic(self, message):
        """ Process xpl chema shutter.basic
        """
        self.send_xpl("shutter.device", message.data)
        add = message.data['device'].split('-')
        chan = int(add[1])
        address = add[0]
        if message.data["command"] == "up":
            self.log.debug("set shutter up")
            self.manager.send_shutterup( address, chan )
        elif message.data["command"] == "down":
            self.log.debug("set shutter down")
            self.manager.send_shutterdown( address, chan )
        else:
            self.log.debug("Unknown command in shutter.basic message")
       
if __name__ == "__main__":
    VelbusManager()

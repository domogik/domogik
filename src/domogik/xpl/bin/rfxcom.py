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

RFXCOM usb support

Implements
==========

- RfxcomUsbManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.rfxcom import RfxcomUsb
from domogik.xpl.lib.rfxcom import RfxcomException
import threading


class RfxcomUsbManager(XplPlugin):
    """ Manage the Rfxcom Usb device and connect it to xPL
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='rfxcom')
        # Get config
        #   - device
        #self._config = Query(self.myxpl, self.log)
        #device = self._config.query('rfxcom', 'device')
        device = "/dev/rfxcom"

        # Init RFXCOM
        self.rfxcom  = RfxcomUsb(self.log, self.send_xpl)
        
        # Create a listener for all messages used by RFXCOM
        # TODO !!!!!
        # Create listeners
        Listener(self.process_x10_basic, self.myxpl, 
                 {'schema': 'x10.basic',
                  'xpltype': 'xpl-cmnd'})        
        Listener(self.process_x10_security, self.myxpl, 
                 {'schema': 'x10.securiy',
                  'xpltype': 'xpl-cmnd'})        
        Listener(self.process_ac_basic, self.myxpl, 
                 {'schema': 'ac.basic',
                  'xpltype': 'xpl-cmnd'})        
        Listener(self.process_remote_basic, self.myxpl, 
                 {'schema': 'remote.basic',
                  'xpltype': 'xpl-cmnd'})        
        Listener(self.process_control_basic, self.myxpl, 
                 {'schema': 'control.basic',
                  'xpltype': 'xpl-cmnd'})        
        
        # Open RFXCOM
        try:
            self.rfxcom.open(device)
        except RfxcomException as e:
            self.log.error(e.value)
            print e.value
            self.force_leave()
            return
            
        # Start reading RFXCOM
        rfxcom_process = threading.Thread(None,
                                   self.rfxcom.listen,
                                   "rfxcom-process-reader",
                                   (self.get_stop(),),
                                   {})
        self.register_thread(rfxcom_process)
        rfxcom_process.start()
        self.enable_hbeat()

    def process_x10_basic(self, message):
        """ Process command xpl message and call the librairy for processing command
            @param message : xpl message
        """
        # TODO
        pass

    def process_x10_security(self, message):
        """ Process command xpl message and call the librairy for processing command
            @param message : xpl message
        """
        # TODO
        pass
        
    def process_ac_basic(self, message):
        """ Process command xpl message and call the librairy for processing command
            @param message : xpl message
        """
        # TODO
        pass
        
    def process_remote_basic(self, message):
        """ Process command xpl message and call the librairy for processing command
            @param message : xpl message
        """
        # TODO
        pass
        
    def process_control_basic(self, message):
        """ Process command xpl message and call the librairy for processing command
            @param message : xpl message
        """
        msg_type = message.data["type"]
        msg_current = message.data["current"]
        msg_device = message.data["current"]
        self.log.debug("CONTROL.BASIC received : device = %s, type = %s, current = %s" % (msg_device, msg_type, msg_current))
        self.rfxcom.xplcmd_control_basic(device = msg_device,
                                         type = msg_type,
                                         current = msg_current)

    def send_xpl(self, schema, data = {}):
        """ Send xPL message on network
        """
        print("schema:%s, data:%s" % (schema, data))
        msg = XplMessage()
        msg.set_type("xpl-trig")
        msg.set_schema(schema)
        for key in data:
            msg.add_data({key : data[key]})
        self.myxpl.send(msg)


if __name__ == "__main__":
    RfxcomUsbManager()

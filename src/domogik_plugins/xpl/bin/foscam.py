#!/usr/bin/python
# -*- coding: utf-8 -*-
""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
======= 

B{Domogik} is free software: you can redistribute it and/or modify it under the terms of 
the GNU General Public License as published by the Free Software Foundation, either 
version 3 of the License, or (at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even 
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
General Public License for more details. 

You should have received a copy of the GNU General Public License along with Domogik. If not, see U{http://www.gnu.org/licenses}. 

Plugin purpose
============== 
Command Foscam camera relay Implements 
========== 
-FoscamListener 
@author: capof <capof1000 at gmail.com> 
@copyright: (C) 2011 Domogik project @license: GPL(v3) 
@organization: Domogik 

"""

from domogik.xpl.common.xplconnector import Listener 
from domogik.xpl.common.plugin import XplPlugin 
from domogik.xpl.common.xplmessage import XplMessage 
from domogik.xpl.common.queryconfig import Query 
from domogik_plugins.xpl.lib.foscam import RELAY 

class foscam(XplPlugin):
    """ Implements a listener for Foscam relay messages on xPL network
    """
    def __init__(self):
        """ Create listener for Foscam Relay
        """
        XplPlugin.__init__(self, name = 'foscam')
        
        self._config = Query(self.myxpl, self.log)
        # Configuration : list of cameras
        self.cameras = {}
        num = 1
        loop = True
        while loop == True:
            #Get each camera settings
            name = self._config.query('foscam', 'name-%s' % str(num))
            ip = self._config.query('foscam', 'ip-%s' % str(num))
            port = self._config.query('foscam', 'port-%s' % str(num))
            user = self._config.query('foscam', 'user-%s' % str(num))
            password = self._config.query('foscam', 'password-%s' % str(num))
            delay = self._config.query('foscam', 'delay-%s' % str(num))
            if port == None:
                port = 80
            if user == None:
                user = ""
            if password == None:
                password = ""
            if delay == None:
                delay = 0
            if name != None:
                self.log.info("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (name, ip, port, user, delay))
                self.cameras[name] = {"ip" : ip, "port" : port, "user" : user,"password" : password, "delay" : delay}
            else:
                loop = False
            num += 1
        
        ### Create FOSCAM object
        self._foscammanager = RELAY(self.log)
        # Create listeners
        Listener(self.foscam_command, self.myxpl, {'schema': 'control.basic', 'xpltype': 'xpl-cmnd', 'type': 'output'})
        self.log.info("Listener for Foscam relay created")
        self.enable_hbeat()
    def foscam_command(self, message):
        """ Call Foscamn lib
            @param message : xPL message detected by listener
        """
        if 'device' in message.data:
            device = message.data['device']
        if 'current' in message.data:
             msg_current = message.data['current'].upper()
        
        if 'type' in message.data:
             msg_type = message.data['type'].lower()
        try:
            ip = self.cameras[device]["ip"]
            port = int(self.cameras[device]["port"])
            user = self.cameras[device]["user"]
            password = self.cameras[device]["password"]
            delay = int(self.cameras[device]["delay"])
        except KeyError:
            self.log.warning("Camera named '%s' is not defined" % device)
            return
        if msg_type == 'output' and msg_current in ['HIGH']:
             #print "HIGH recu"
             self.log.debug("HIGH command receive on relay '%s'" % device)
             # Our listener catch a Message with LOW output command
             status = self._foscammanager.close_relay(ip, port, user, password, device)
             # Send xpl-trig to say plugin whell receive HIGH command
             if status == True:
                  #print "HIGH ACKed"
                  self.log.debug("HIGH command Ack on relay '%s'" % device)
                  mess = XplMessage()
                  mess.set_type('xpl-trig')
                  mess.set_schema('sensor.basic')
                  mess.add_data({'device' : device})
                  mess.add_data({'type' : 'output'})
                  mess.add_data({'current' : 'HIGH'})
                  self.myxpl.send(mess)
        if msg_type == 'output' and msg_current in ['LOW']:
             #print "LOW recu"
             self.log.debug("LOW command receive on relay '%s'" % device)
             # Our listener catch a Message with LOW output command
             status = self._foscammanager.open_relay(ip, port, user, password, device)
             # Send xpl-trig to say plugin whell receive LOW command
             if status == True:
                  #print "LOW ACKed"
                  self.log.debug("LOW command Ack on relay '%s'" % device)
                  mess = XplMessage()
                  mess.set_type('xpl-trig')
                  mess.set_schema('sensor.basic')
                  mess.add_data({'device' : device})
                  mess.add_data({'type' : 'output'})
                  mess.add_data({'current' : 'LOW'})
                  self.myxpl.send(mess)

        if msg_type == 'output' and msg_current in ['PULSE']:
             #print "PULSE recu"
             self.log.debug("PULSE command receive on relay '%s'" % device)
             # Our listener catch a Message with output PULSE output command
             status = self._foscammanager.pulse_relay(ip, port, user, password, delay, device)
             # Send xpl-trig to say plugin whell receive PULSE command
             if status == True:
                  #print "PULSE ACKed"
                  self.log.debug("PULSE command Ack on relay '%s'" % device)
                  mess = XplMessage()
                  mess.set_type('xpl-trig')
                  mess.set_schema('sensor.basic')
                  mess.add_data({'device' : device})
                  mess.add_data({'type' : 'output'})
                  mess.add_data({'current' : 'PULSE'})
                  self.myxpl.send(mess)
		                   
if __name__ == "__main__":
    inst = foscam()

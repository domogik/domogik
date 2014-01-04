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
Command roomba vaccum  
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
from domogik_packages.xpl.lib.roowifi import command 

class roowifi(XplPlugin):
## Implements a listener for RooWifi messages on xPL network

	def __init__(self):
		##Create listener for rowifi
		##
		print("On rentre dans __init__")
		XplPlugin.__init__(self, name = 'roowifi')
		self._config = Query(self.myxpl, self.log)
		# Configuration : list of cameras
		self.roombas = {}
		num = 1
		loop = True
		while loop == True:
			#Get each roomba settings
			name = self._config.query('roowifi', 'name-%s' % str(num))
			ip = self._config.query('roowifi', 'ip-%s' % str(num))
			port = self._config.query('roowifi', 'port-%s' % str(num))
			user = self._config.query('roowifi', 'user-%s' % str(num))
			password = self._config.query('roowifi', 'password-%s' % str(num))
			delay = self._config.query('roowifi', 'delay-%s' % str(num))
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
				self.roombas[name] = {"ip" : ip, "port" : port, "user" : user,"password" : password, "delay" : delay}
			else:
				loop = False
			num += 1
        
        ### Create Roomba object
		self._roombamanager = command(self.log)
		# Create listeners
		Listener(self.roowifi_command, self.myxpl, {'schema': 'control.basic', 'xpltype': 'xpl-cmnd', 'type': 'output'})
		self.log.info("Listener for rowifi created")
		#print ("Listener for roowifi created")
		self.enable_hbeat()
		print(" FIN  __init__")
		
	def roowifi_command(self, message):
		##Call roowifi lib
		##@param message : xPL message detected by listener
		ip = self.roombas[device]["ip"]
		port = int(self.roombas[device]["port"])
		user = self.roombas[device]["user"]
		password = self.roombas[device]["password"]
		delay = int(self.roombas[device]["delay"])
		#except KeyError:
		#	self.log.warning("Roomba named '%s' is not defined" % device)
		#	return false
		if 'device' in message.data:
			device = message.data['device']
		if 'current' in message.data:
			msg_current = message.data['current'].upper() 
		if 'type' in message.data:
			msg_type = message.data['type'].lower()
		if msg_type == 'command' and msg_current.lower() in ['clean']:
			print ("Command clean recu")
			self.log.debug("Clean command receive for '%s'" % device)
			# Our listener catch a Message with low output command
			status = self._roombamanager.clean(ip, port, user, password, device)
			# Send xpl-trig to say plugin whell receive high command
			if status == True:
				#print ("high ACKed")
				self.log.debug("high command Ack on relay '%s'" % device)
				mess = XplMessage()
				mess.set_type('xpl-trig')
				mess.set_schema('sensor.basic')
				mess.add_data({'device' : device})
				mess.add_data({'type' : 'command'})
				mess.add_data({'current' : 'clean'})
				self.myxpl.send(mess)

if __name__ == "__main__":
    inst = roowifi()


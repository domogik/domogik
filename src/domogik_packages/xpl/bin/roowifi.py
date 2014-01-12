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
@author: capof <capof1000 at gmail.com> 
@copyright: (C) 2011 Domogik project @license: GPL(v3) 
@organization: Domogik 

"""
from domogik.xpl.common.plugin import XplPlugin 
from domogik.xpl.common.xplmessage import XplMessage 
from domogik.xpl.common.queryconfig import Query 
from domogik_packages.xpl.lib.roowifi import Command 
from domogik.xpl.common.xplconnector import Listener, XplTimer

class roowifi(XplPlugin):
## Implements a listener for RooWifi messages on xPL network

	def __init__(self):
		
		print("On rentre dans __init__")
		XplPlugin.__init__(self, name = 'roowifi')
		self._config = Query(self.myxpl, self.log)
		# creation d'un tableau pour recuperer les eventuels roombas
		self.roombas = {}
		num = 1
		loop = True
		while loop == True:
			#Get each roomba settings
			print ("On rentre dans while")
			self._name = self._config.query('roowifi', 'name-%s' % str(num))
			self._ip = self._config.query('roowifi', 'ip-%s' % str(num))
			self._port = self._config.query('roowifi', 'port-%s' % str(num))
			self._user = self._config.query('roowifi', 'user-%s' % str(num))
			self._password = self._config.query('roowifi', 'password-%s' % str(num))
			self._delay = self._config.query('roowifi', 'delay-%s' % str(num))
			
		## retirer les valeurs default, une fois le pb de recuperation de config du plugin regle
			if self._name == None:
				self._name = "roomba"
			if self._ip == None:
				self._ip = "192.168.1.64"
			if self._port == None:
				self._port = 9001
			if self._user == None:
				self._user = "admin"
			if self._password == None:
				self._password = "roombawifi"
			if self._delay == None:
				self._delay = 3
			print ("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))
			loop = False			
			
			if self._name != None:
				self.log.info("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))
				print ("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))
				self.roombas[self._name] = {"ip" : self._ip, "port" : self._port, "user" : self._user,"password" : self._password, "delay" : self._delay}
			else:
				loop = False
			num += 1
        
        ### Create Roomba object
		self._roombamanager = Command(self.log)
		# Create listeners
		Listener(self.roowifi_command, self.myxpl, {'schema': 'roowifi.basic', 'xpltype': 'xpl-cmnd'})
		self.log.info("Listener for roowifi created")
		#print ("Listener for roowifi created")
		self.enable_hbeat()
		
		## call send probe from time to time :
		self._probe_thr = XplTimer(self._delay, self._send_probe, self.myxpl)
		self._probe_thr.start()

	def _send_probe(self):
		##
		#Uncomment line to get according XPL-Stat message !
		##
		#print("On est dans send_probe")
		self._sensors = self._roombamanager.sensor(self._ip, self._port, self._name, self._user,self._password)
		
		if self._sensors <> "N/A" :
			#self._send_XPL_STAT("xpl-stat", self._name, "bumps-wheeldrops", self._sensors["Bumps Wheeldrops"])
			#self._send_XPL_STAT("xpl-stat", self._name, "wall", self._sensors["Wall"])
			#self._send_XPL_STAT("xpl-stat", self._name, "cliff-left", self._sensors["Cliff Left"])
			#self._send_XPL_STAT("xpl-stat", self._name, "cliff-front-left", self._sensors["Cliff Front Left"])
			#self._send_XPL_STAT("xpl-stat", self._name, "cliff-front-right", self._sensors["Cliff Front Right"])
			#self._send_XPL_STAT("xpl-stat", self._name, "cliff-right", self._sensors["Cliff Right"])
			#self._send_XPL_STAT("xpl-stat", self._name, "virtual-wall", self._sensors["Virtual Wall"])
			self._send_XPL_STAT("xpl-stat", self._name, "motor-overcurrents", self._sensors["Motor Overcurrents"])
			self._send_XPL_STAT("xpl-stat", self._name, "remote-opcode", self._sensors["Remote Opcode"])
			self._send_XPL_STAT("xpl-stat", self._name, "buttons", self._sensors["Buttons"])
			#self._send_XPL_STAT("xpl-stat", self._name, "distance", self._sensors["Distance"])
			#self._send_XPL_STAT("xpl-stat", self._name, "angle", self._sensors["Angle"])
			self._send_XPL_STAT("xpl-stat", self._name, "charging-state", str(self._sensors["Charging State"]))
			#self._send_XPL_STAT("xpl-stat", self._name, "voltage", self._sensors["Voltage"])
			self._send_XPL_STAT("xpl-stat", self._name, "current", self._sensors["Current"])
			self._send_XPL_STAT("xpl-stat", self._name, "temperature", self._sensors["Temperature"])
			#self._send_XPL_STAT("xpl-stat", self._name, "charge", self._sensors["Charge"])
			#self._send_XPL_STAT("xpl-stat", self._name, "capacity", self._sensors["Capacity"])
			self._send_XPL_STAT("xpl-stat", self._name,"battery-level", self._sensors["battery-level"])
			
		#print("Fin send_probe")
		
	def _send_XPL_STAT(self, xpl_xxx, xpl_device, xpl_type, xpl_current):	
		#genere le xpl stat
		print ("On va envoyer le xpl-stat %s . %s : %s" %(xpl_device, xpl_type, xpl_current))
		self.log.debug("Valeur de %s de %s : %s" % (xpl_type,xpl_device, xpl_current))
		mess = XplMessage()
		mess.set_type(xpl_xxx)
		mess.set_schema('sensor.basic')
		mess.add_data({'device' : xpl_device})
		mess.add_data({'type' : xpl_type})
		mess.add_data({'current' : xpl_current})
		self.myxpl.send(mess)
		
	def roowifi_command(self, message):
		
		if 'device' in message.data:
			device = message.data['device']
		
		if 'command' in message.data:
			print (" Une commande est recue !")
			lacommand = message.data['command']
			self.log.debug("Clean command receive for '%s'" % device)
			status = self._roombamanager.command(self._ip, self._port, device, lacommand)
			#status = self._roombamanager.commandweb( device, lacommand, self._ip, self._port, self._user, self._password,)
			
			if status == True:
				print ("On va envoyer le xpl-trig pour acker la commande %s" % lacommand)
				self.log.debug("Ack de la command %s on %s" % (lacommand, device))
				mess = XplMessage()
				mess.set_type('xpl-trig')
				mess.set_schema('roowifi.basic')
				mess.add_data({'device' : device})
				#mess.add_data({'type' : 'command'})
				mess.add_data({'command' : lacommand})
				self.myxpl.send(mess)
			
if __name__ == "__main__":
    inst = roowifi()


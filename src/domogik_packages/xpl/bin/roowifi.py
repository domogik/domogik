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
from domogik.xpl.common.plugin import XplPlugin 
from domogik.xpl.common.xplmessage import XplMessage 
from domogik.xpl.common.queryconfig import Query 
from domogik_packages.xpl.lib.roowifi import command 
from domogik.xpl.common.xplconnector import Listener, XplTimer



class roowifi(XplPlugin):
## Implements a listener for RooWifi messages on xPL network

	def __init__(self):
		#####
        ## Create listeners
        ##  Listener(self._plcbus_cmnd_cb, self.myxpl, {'schema': 'plcbus.basic','xpltype': 'xpl-cmnd',})
		##
		##  device = self._config.query('plcbus', 'device')
		#####
		##Create listener for roowifi
		##
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
			 
			
		## retirer les valeurs default, une fois le pb de reuperation de config du plugin regler
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
				self._delay = 15
			print ("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))
			loop = False
		##				
			
			if self._name != None:
				self.log.info("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))
				print ("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))
				self.roombas[self._name] = {"ip" : self._ip, "port" : self._port, "user" : self._user,"password" : self._password, "delay" : self._delay}
			else:
				loop = False
			num += 1
        
        ### Create Roomba object
		self._roombamanager = command(self.log)
		# Create listeners
		##Listener(self.roowifi_command, self.myxpl, {'schema': 'control.basic', 'xpltype': 'xpl-cmnd', 'type': 'command'})
		Listener(self.roowifi_command, self.myxpl, {'schema': 'roowifi.basic', 'xpltype': 'xpl-cmnd'})
		self.log.info("Listener for roowifi created")
		#print ("Listener for roowifi created")
		self.enable_hbeat()
		#print(" FIN  __init__")
#########################################
		## call send probe from time to time :
		self._probe_thr = XplTimer(self._delay, self._send_probe, self.myxpl)
		self._probe_thr.start()

#############################

		


		

	def _send_probe(self):
		#print("On est dans send_probe")
		batterylevel = ()
		batterylevel = self._roombamanager.sensor(self._ip, self._port, self._name,self._user,self._password)
		
		
		
		
		
		
		batterylevel = 50
		print ("On va envoyer le xpl-stat la batterie")
		self.log.debug("Valeur de la batterie pour %s : %s" % (self._name,batterylevel))
		mess = XplMessage()
		mess.set_type('xpl-stat')
		mess.set_schema('sensor.basic')
		mess.add_data({'device' : self._name})
		mess.add_data({'type' : 'battery-level'})
		mess.add_data({'current' : batterylevel})
		self.myxpl.send(mess)
		
		print ("Batterie from bin : %s" % (batterylevel))
		
	def roowifi_command(self, message):
		##Call roowifi lib
		##@param message : xPL message detected by listener
		#print(" On rentre dans roowifi_comand")
		

		#except KeyError:
		#	self.log.warning("Roomba named '%s' is not defined" % device)
		#	return false
		if 'device' in message.data:
			device = message.data['device']

		ip = self.roombas[device]["ip"]
		port = int(self.roombas[device]["port"])
		#user = self.roombas[device]["user"]
		#password = self.roombas[device]["password"]
		#delay = int(self.roombas[device]["delay"])

		##if 'current' in message.data:
		##	msg_current = message.data['current'].upper() 
		##if 'type' in message.data:
		##	msg_type = message.data['type'].lower()
		##if msg_type == 'command' and msg_current.lower() in ['clean']:
		#if msg_type == 'command' and msg_current.lower() in ['clean']:
		if 'command' in message.data:
			print (" Une commande est recue !")
			lacommand = message.data['command']
			self.log.debug("Clean command receive for '%s'" % device)
			# Our listener catch a Message with low output command
			status = self._roombamanager.command(ip, port, device, lacommand)
			# Send xpl-trig to say plugin whell receive high command
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


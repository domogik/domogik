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

Command Relay on Foscam camera

Implements
==========


@author: capof <capof1000 at gmail.com>
@copyright: (C) 2011 Domogik project
@license: GPL(v3)
@organization: Domogik

Library
"""

from domogik.xpl.common.xplconnector import XplTimer
from threading import Thread, Event
import subprocess
import time
import traceback
import urllib
import socket
import urllib2
import json

table = {
		"clean" : 135, 
		"dock" : 143, 
		"full": 132, 
		"max" :136, 
		"play":141, ## not implemented
		"spot" : 143, 
		"start" : 128, ## not implemented
		"spot" : 134, ## not implemented
		"LED_COMMAND" : 139,
		"SENSOR_COMMAND" : 142,
		"SENSOR_PACKET_0" : 0,
		"SENSOR_PACKET_1" : 1,
		"SENSOR_PACKET_2" : 2,
		"SENSOR_PACKET_3" : 3,
		"NUM_BYTES_PACKET_0" : 26
		} 

class command:

	def __init__(self, log):
		self._log = log

	def command(self, ip, port, device, command):
		#print("on est dans lib-command")
		self._log.info("Start processing clean Command on %s  " % (device))
		#print("Start processing Command on %s  " % (device))
		#print("LA commande est %s  " % (command))
		try:			
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			time.sleep(1)
			self.s.connect((ip , port))
			time.sleep(1)
			self.s.send(chr(132))
			time.sleep(1)
			#print("Le code de la fonction est %s  " % table[command])
			self.s.send(chr(table[command]))
			time.sleep(1)
			self.s.close()
			print ("%s command Success on %s" % (command,device))
			self._log.info("%s command Success on %s" % (command,device))
			return True
		except:
			print (" %s Command Failed on %s" % (command,device))
			self._log.error(" %s Command Failed on %s" % (command,device))
			return False
		
	def sensor(self, ip, port, device, user, password):
		print("on est dans lib.sensor")
				
		try:
			password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
			username = user
			password = password
			top_level_url = "http://" + ip 
			password_mgr.add_password(None, top_level_url, username, password)
			handler = urllib2.HTTPBasicAuthHandler(password_mgr)
			opener = urllib2.build_opener(handler)
			urllib2.install_opener(opener)
			response = urllib2.urlopen('http://192.168.1.64/roomba.json')
			page = response.read()
			j = json.loads(page)
			
			sensor_name = j['response']['r17']['name']
			sensor_value = j['response']['r17']['value']
			
			print sensor_name
			print sensor_value
			#print ("%s : %S"% (sensor_name ,sensor_value))
			
			return j			
		except:
            #self._log.error("Sensor read Failed ")
			return "N/A"
			
		
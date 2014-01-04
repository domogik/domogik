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

tablecmd = ["clean","dock"]
tablecode = [135,143]
 
clean = 135
SPOT_COMMAND = 134
DOCK_COMMAND = 143

class command:

	def __init__(self, log):
		"""
		Init object
		@param log : logger instance
		"""
		#print("on est dans lib__init__")
		self._log = log

	def command(self, ip, port, user, password, device, command):
		"""
		close the relay 
		"""
		print("on est dans lib-command")
		self._log.info("Start processing clean Command on %s  " % (device))
		print("Start processing clean Command on %s  " % (device))
		print("LA commande est %s  " % (command))
		
		try:
#####################################################			
			
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			time.sleep(1)
			self.s.connect((ip , port))
			time.sleep(1)
			print("Le code de la fonction est %s  " % tablecode[(tablecmd.index(command))])
			self.s.send(chr(tablecode[(tablecmd.index(command))]))
			time.sleep(1)
			self.s.close()
			self._log.error("clean Command success on : %s" % device)
			
#######################################################			
		except:
			self._log.error("Fail to close Foscam relay : %s" % traceback.format_exc())
			return False
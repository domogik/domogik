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

sensors = {
                "Bumps Wheeldrops" : 0 ,
                "Wall" : 0 ,
                "Cliff Left" : 0 ,
                "Cliff Front Left" : 0 ,
                "Cliff Front Right" : 0 ,
                "Cliff Right" : 0 ,
                "Virtual Wall" : 0 ,
                "Motor Overcurrents" : 0 ,
                "Dirt Detector - Left" : 0 ,
                "Dirt Detector - Right" : 0 ,
                "Remote Opcode" : 0,
                "Buttons" : 0 ,
                "Distance" : 0 ,
                "Angle" : 0 ,
                "State" : 0 ,
                "Voltage" : 0 ,
                "Current" : 0 ,
                "Temperature" : 0 ,
                "Charge" : 0 ,
                "Capacity" : 0,
                "Battery-level" : 0
                }

State = {
                0 : "Not charging" ,
                1 : "Charging Recovery" ,
                2 : "Charging" ,
                3 : "Trickle charging" ,
                4 : "Waiting" ,
                5 : "Charging Error" ,
                6 : "Cleaning",
                7 : "Docking",
                8 : "Maximun",
                }

class Command:

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

                        if str(command) == "clean":
                                sensors['State'] = State[int(6)]
                        if str(command) == "dock" :
                                sensors['State'] =  State[int(7)]
                        if str(command) == "max" :
                                sensors['State'] =  State[int(8)]

                        return True
                except:
                        print (" %s Command Failed on %s" % (command,device))
                        self._log.error(" %s Command Failed on %s" % (command,device))
                        return False

        def commandweb(self, device, command, ip, port, user, password):
                # NON-UTILISEE, TO DELETE ?
                try:
                        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                        top_level_url = "http://" + ip
                        password_mgr.add_password(None, top_level_url, user, password)
                        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
                        opener = urllib2.build_opener(handler)
                        urllib2.install_opener(opener)
                        response = urllib2.urlopen(top_level_url + '/rwr.cgi?exec=1')
                        response = urllib2.urlopen(top_level_url + '/roomba.cgi?button=' + (command).upper())
                        page = response.read()
                        print page
                        if page == "1" :
                                print ("%s command Success on %s" % (command,device))
                                self._log.info("%s command Success on %s" % (command,device))
                                return True
                except:
                        print (" %s Command Failed on %s" % (command,device))
                        self._log.error(" %s Command Failed on %s" % (command,device))
                        return False

        def sensor(self, ip, port, device, user, password):
                #print("on est dans lib.sensor")
                try:
                        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
                        top_level_url = "http://" + ip
                        password_mgr.add_password(None, top_level_url, user, password)
                        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
                        opener = urllib2.build_opener(handler)
                        urllib2.install_opener(opener)
                        response = urllib2.urlopen(top_level_url + '/roomba.json')
                        page = response.read()
                        self.j = json.loads(page)

                        sensors['Bumps Wheeldrops'] = self.j['response']['r0']['value']
                        sensors['Wall'] = self.j['response']['r1']['value']
                        sensors['Cliff Left'] = self.j['response']['r2']['value']
                        sensors['Cliff Front Left'] = self.j['response']['r3']['value']
                        sensors['Cliff Front Right'] = self.j['response']['r4']['value']
                        sensors['Cliff Right'] = self.j['response']['r5']['value']
                        sensors['Virtual Wall'] = self.j['response']['r6']['value']
                        sensors['Motor Overcurrents'] = self.j['response']['r7']['value']
                        sensors['Dirt Detector - Left'] = self.j['response']['r8']['value']
                        sensors['Dirt Detector - Right'] = self.j['response']['r9']['value']
                        sensors['Remote Opcode'] = self.j['response']['r10']['value']
                        sensors['Buttons'] = self.j['response']['r11']['value']
                        sensors['Distance'] = self.j['response']['r12']['value']
                        sensors['Angle'] = self.j['response']['r13']['value']
                        sensors['State'] = State[int(self.j['response']['r14']['value'])]

                        sensors['Voltage'] = self.j['response']['r15']['value']
                        sensors['Current'] = self.j['response']['r16']['value']
                        sensors['Temperature'] = self.j['response']['r17']['value']
                        sensors['Charge'] = self.j['response']['r18']['value']
                        sensors['Capacity'] = self.j['response']['r19']['value']
                        sensors['battery-level'] =  int(self.j['response']['r18']['value'])*100 / int (self.j['response']['r19']['value'])

                        if int(self.j['response']['r16']['value']) > (0):
                                sensors['State'] = State[int(self.j['response']['r14']['value'])]
                        if (-200) < int(self.j['response']['r16']['value']) < (0):
                                sensors['State'] = State[int(4)]

                        return sensors
                except:
            #self._log.error("Sensor read Failed ")
                        return "N/A"
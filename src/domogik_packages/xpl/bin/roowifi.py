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
from domogik_packages.xpl.lib.roowifi import Command
from domogik.xpl.common.xplconnector import Listener, XplTimer

class roowifi(XplPlugin):
## Implements a listener for RooWifi messages on xPL network

        def __init__(self):

                XplPlugin.__init__(self, name = 'roowifi')

                                ### Create Roomba object
                self._roombamanager = Command(self.log)
                # Create listeners
                Listener(self.roowifi_command, self.myxpl, {'schema': 'roowifi.basic', 'xpltype': 'xpl-cmnd'})
                self.log.info("Listener for roowifi created")
                self.enable_hbeat()

                # creation d'un tableau pour recuperer les eventuels roombas
                self._config = Query(self.myxpl, self.log)
                self.roombas = {}
                num = 1
                loop = True
                while loop == True:
                        #Get each roomba settings
                        print ("Boucle dans While %s" %(num))
                        if self._config.query('roowifi', 'name-%s' % str(num)) != None:
                                self._name = str(self._config.query('roowifi', 'name-%s' % str(num)))
                                self._ip = str(self._config.query('roowifi', 'ip-%s' % str(num)))
                                self._port = int(self._config.query('roowifi', 'port-%s' % str(num)))
                                self._user = str(self._config.query('roowifi', 'user-%s' % str(num)))
                                self._password = str(self._config.query('roowifi', 'password-%s' % str(num)))
                                self._delay = int(self._config.query('roowifi', 'delay-%s' % str(num)))

                                self.log.info("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))
                                #print ("Configuration : name=%s, ip=%s, port=%s, user=%s, password=No_Log, delay=%s" % (self._name, self._ip, self._port, self._user, self._delay))

                                self.roombas[self._name] = {"ip" : self._ip, "port" : self._port, "user" : self._user,"password" : self._password, "delay" : self._delay}

                                self._probe_thr = XplTimer(int(self._delay), self._send_probe, self.myxpl)
                                self._probe_thr.start()
                        else:
                                loop = False
                                print ("fin while")
                        num += 1


        def _send_probe(self):
                ##
                #Uncomment line to get according XPL-Stat message !
                ##

                self._sensors = self._roombamanager.sensor(self._ip, self._port, self._name, self._user,self._password)
                print self._sensors
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
                        self._send_XPL_STAT("xpl-stat", self._name, "state", str(self._sensors["State"]))
                        #self._send_XPL_STAT("xpl-stat", self._name, "voltage", self._sensors["Voltage"])
                        self._send_XPL_STAT("xpl-stat", self._name, "current", self._sensors["Current"])
                        self._send_XPL_STAT("xpl-stat", self._name, "temperature", self._sensors["Temperature"])
                        #self._send_XPL_STAT("xpl-stat", self._name, "charge", self._sensors["Charge"])
                        #self._send_XPL_STAT("xpl-stat", self._name, "capacity", self._sensors["Capacity"])
                        self._send_XPL_STAT("xpl-stat", self._name,"battery-level", self._sensors["battery-level"])


        def _send_XPL_STAT(self, xpl_xxx, xpl_device, xpl_type, xpl_current):
                #genere le xpl stat
                #print ("On va envoyer le xpl-stat %s . %s : %s" %(xpl_device, xpl_type, xpl_current))
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

                        lacommand = message.data['command']
                        self.log.debug("%s command receive for %s" % (lacommand,device))
                        print ("%s command receive for %s" % (lacommand,device))

                        status = self._roombamanager.command( self.roombas[device]["ip"], self.roombas[device]["port"],device, lacommand)

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

chris@EeeBox:/var/lib/domogik/domogik_packages/xpl/b
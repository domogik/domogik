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

xPL Chacon client through the TellStick

Implements
==========

- tsChacon.__init__(self)
- tsChacon.chacon_cmnd_cb(self, message)
- tsChacon.chacon_monitor_cb(self, house, unit, order)

@author: Julien Garet <julien@garet.info>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.TellStick import *
import os.path

class tsChacon(XplPlugin):
    '''Manage chacon devices through the TellStick device
    '''

    def __init__(self):
        """
        Create the tsChacon class
        This class is used to connect chacon devices (through TellSitck) to the xPL Network
        """
        XplPlugin.__init__(self, name = 'tschacon')
        self.log.debug("tschacon correctly started")
        self._device = "/dev/tellstick"
	#Check if the device exists
        if not os.path.exists(self._device):
            self.log.error(self._device + " is not present")
        else:
            self.log.debug("device present as "+self._device)
        self._config = Query(self.myxpl, self.log)
        try:
            self.__mytellstick = TellStick()
        except Exception:
            self.log.error("Something went wrong during TellStick init, check logs")
            self.log.error("Exception : %s" % traceback.format_exc())
            exit(1)
        #Create listeners
        Listener(self.tsChacon_cmnd_cb, self.myxpl, 
                 {'schema': 'ts.arctech', 'xpltype': 'xpl-cmnd'})
        self.enable_hbeat()
        self.log.debug("tschacon plugin correctly started")

    def tsChacon_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        commands = {
            'on': lambda h, u: self.__mytellstick.sendOn("arctech","codeswitch",h,u),
            'off': lambda h, u: self.__mytellstick.sendOff("arctech","codeswitch",h,u),
        }
        cmd = None
        dev = None
        if 'command' in message.data:
            cmd = message.data['command']
        if 'device' in message.data:	    
            house = message.data['device'][0]
            unit = message.data['device'][1]
        self.log.debug("%s received : house = %s unit= %s" %
                       (cmd, house, unit))
        commands[cmd](house, unit)
        self.tsChacon_monitor_cb(house, unit, cmd)

    def tsChacon_monitor_cb(self, house, unit, order, args = None):
        """
        Callback for TellStick Chacon monitoring
        @param house : the house of the element controled
        @param unit : the unit of the element controled
        @param order : the order sent to the unit
        """
        self.log.debug("tschacon Callback YEDfor %s" % unit)
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("ts.arctech")
        mess.add_data({"device" :  house+unit})
        mess.add_data({"command" :  order})
        self.myxpl.send(mess)

if __name__ == "__main__":
    tsChacon()

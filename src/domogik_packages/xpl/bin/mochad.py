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

xPL X10 client through Mochad with cm15 or cm19 (a mochad host must be running)
The mochad initialization makes the plugin listen to events on the cm15 and
send xpl callbacks to the network

Implements
==========

- mochad.__init__(self)
- mochad.x10_cmnd_cb(self, message)
- mochad.x10_monitor_cb(self, house, unit, order)

@author: Julien Garet <julien@garet.info>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik_packages.xpl.lib.mochad import *
import os.path

class mochad(Mochad):
    '''Manage x10 devices through mochad
    '''

    def __init__(self):
        """
        Create a Mochad instance
        This class is used to connect x10 devices (through mochad) to the xPL Network
        """
        Mochad.__init__(self)

        self.log.debug("mochad correctly started")

        #Create listeners
        Listener(self.x10_cmnd_cb, self.myxpl, 
                 {'schema': 'x10.basic', 'xpltype': 'xpl-cmnd'})
        self.enable_hbeat()
        self.log.debug("mochad plugin correctly started")

    def x10_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        commands = {
            'on': lambda d, h, l: self.send(d,"on"),
            'off': lambda d, h, l: self.send(d,"off"),
            'all_units_on': lambda d, h, l: self.send(h,"all_units_on"),
            'all_units_off': lambda d, h, l: self.send(h,"all_units_off"),
            'all_lights_on': lambda d, h, l: self.send(h,"all_lights_on"),
            'all_lights_off': lambda d, h, l: self.send(h,"all_lights_off"),
            'bright': lambda d, h, l: self.send(d,"bright",l),
            'dim': lambda d, h, l: self.send(d,"dim",l),
        }
        cmd = None
        dev = None
        house = None
        level = None
        if 'command' in message.data:
            cmd = message.data['command']
        if 'device' in message.data:
            dev = message.data['device']
        if 'house' in message.data:
            house = message.data['house']
        if 'level' in message.data:
            level = message.data['level']
        self.log.debug("%s received : device = %s, house = %s, level = %s" %
                       (cmd, dev, house, level))
        commands[cmd](dev, house, level)
        self.x10_monitor_cb(dev, cmd)

    def x10_monitor_cb(self, unit, order, args = None):
        """
        Callback for TellStick Chacon monitoring
        @param unit : the address of the element controled
        @param order : the order sent to the unit
        """
        self.log.debug("X10 Callback YEDfor %s" % unit)
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("x10.basic")
        mess.add_data({"device" :  unit})
        mess.add_data({"command" :  order})
        if args:
            mess.add_data({"level" : args})
        self.myxpl.send(mess)


if __name__ == "__main__":
    mochad()

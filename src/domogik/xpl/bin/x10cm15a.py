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

xPL X10 client

Implements
==========

- x10Main.__init__(self)
- x10Main.x10_cmnd_cb(self, message)
- x10Main.x10_monitor_cb(self, unit, order, args = None)

@author: Matthieu Bollot <mattboll@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.lib.cm15a import X10API


class X10Main(XplPlugin):
    '''Manage x10 technology using cm15a
    '''

    def __init__(self):
        """
        Create the X10Main class
        This class is used to connect x10 (through cm15a) to the xPL Network
        """
        XplPlugin.__init__(self, name = 'cm15a')
        self.log.error("Cm15a correctly started")
        self._device = ""
        self._config = Query(self.myxpl, self.log)
        self._device = self._config.query('cm15a', 'cm15a-path')
        try:
            self.__myx10 = X10API(self._device, self.log)
        except Exception:
            self.log.error("Something went wrong during cm15a init, check logs")
            self.log.error("Exception : %s" % traceback.format_exc())
            exit(1)
        #Create listeners
        Listener(self.x10_cmnd_cb, self.myxpl, 
                 {'schema': 'x10.basic', 'xpltype': 'xpl-cmnd'})
        self.enable_hbeat()
        self.log.debug("Cm15a correctly started")

    def x10_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        commands = {
            'on': lambda d, h, l: self.__myx10.on(d),
            'off': lambda d, h, l: self.__myx10.off(d),
            'all_units_on': lambda d, h, l: self.__myx10.house_on(h),
            'all_units_off': lambda d, h, l: self.__myx10.house_off(h),
            'all_lights_on': lambda d, h, l: self.__myx10.lights_on(h),
            'all_lights_off': lambda d, h, l: self.__myx10.lights_off(h),
            'bright': lambda d, h, l: self.__myx10.bright(d, l),
            'dim': lambda d, h, l: self.__myx10.dim(d, l),
            'brightb': lambda d, h, l: self.__myx10.brightb(d, l),
            'dimb': lambda d, h, l: self.__myx10.dimb(d, l),
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
        Callback for x10 monitoring
        @param unit : the unit of the element controled
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
    X10Main()

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

Module purpose
==============

xPL Téléinfo client

Implements
==========

- Teleinfo

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.module import xPLModule, xPLResult
from domogik.xpl.lib.teleinfo import TeleInfo
from domogik.xpl.common.queryconfig import Query

IS_DOMOGIK_MODULE = True
DOMOGIK_MODULE_DESCRIPTION = "Get power consumption with teleinfo"
DOMOGIK_MODULE_CONFIGURATION=[
      {"id" : 0,
       "key" : "startup-module",
       "description" : "Automatically start module at Domogik startup",
       "default" : "False"},
      {"id" : 1,
       "key" : "device",
       "description" : "Teleinfo device (ex : /dev/ttyUSB0 for an usb model)",
       "default" : "/dev/ttyUSB0"},
      {"id" : 2,
       "key" : "interval",
       "description" : "Interval between each request (seconds)",
       "default" : 60}]



class TeleinfoManager(xPLModule):
    '''
    Manage the Téléinfo stuff and connect it to xPL
    '''

    def __init__(self):
        '''
        Start teleinfo device handler
        '''
        xPLModule.__init__(self, name='teleinfo')
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('teleinfo', 'device', res)
        device = res.get_value()['device']
        res = xPLResult()
        self._config.query('teleinfo', 'interval', res)
        interval = res.get_value()['interval']
        self._myteleinfo  = TeleInfo(device, self._broadcastframe, interval)
        self.add_stop_cb(self._myteleinfo.stop)
        self._myteleinfo.start()

    def _broadcastframe(self, frame):
        ''' Send a frame from teleinfo device to xpl
        @param frame : a dictionnary mapping teleinfo informations
        '''
        my_temp_message = XplMessage()
        my_temp_message.set_type("xpl-stat")
        my_temp_message.set_schema("teleinfo.basic")
        for entry in frame:
            my_temp_message.add_data({entry["name"].lower() : entry["value"]})
        self._myxpl.send(my_temp_message)


if __name__ == "__main__":
    TeleinfoManager()

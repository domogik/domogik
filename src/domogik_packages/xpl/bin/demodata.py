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

Send demo data over xPL

Implements
==========

- DemoDataManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import XplTimer
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.demodata import DemoData, DemoUI
import threading
import datetime

class DemoDataManager(XplPlugin):
    """ Sends demo data over xPL
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='demodata')

        demo = DemoData(self.log, self.send_sensor_basic, \
                                  self.send_teleinfo_basic)

        # weather data each minute
        self._weather_thr = XplTimer(60, \
                                     demo.weather_data, \
                                     self.myxpl)
        self._weather_thr.start()

        # teleinfo data each 10min
        self._teleinfo_thr = XplTimer(600, \
                                     demo.teleinfo_data, \
                                     self.myxpl)
        self._teleinfo_thr.start()

        self.enable_hbeat()

        # Launch the web UI
        demo_ui = DemoUI()

    def send_sensor_basic(self, device, type, current, units = None):
        """ Send sensor.basic xPL schema
            @param device : device
            @param type : type
            @param current : current
        """
        print("sensor.basic { device=%s, type=%s, current=%s}" % (device, type, current))
        if current == "":
            return
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("sensor.basic")
        msg.add_data({"device" : device})
        msg.add_data({"type" : type})
        msg.add_data({"current" : current})
        if units != None:
            msg.add_data({"units" : units})
        self.myxpl.send(msg)

    def send_teleinfo_basic(self, frame):
        ''' Send a frame from teleinfo device to xpl
        @param frame : a dictionnary mapping teleinfo informations
        '''
        print("teleinfo.basic : %s" % frame)
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("teleinfo.basic")
        for key in frame:
            msg.add_data({ key : frame[key] })
        self.myxpl.send(msg)


if __name__ == "__main__":
    DemoDataManager()

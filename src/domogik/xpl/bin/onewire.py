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

xPL OneWire client

Implements
==========

- OneWireTemp.__init__(self)
- OneWireTemp._gettemp()

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin, XplResult, XplTimer
from domogik.xpl.lib.onewire import OneWire
from domogik.xpl.common.queryconfig import Query
import threading


TEMP_DELAY = 60

IS_DOMOGIK_PLUGIN = True
DOMOGIK_PLUGIN_TECHNOLOGY = "onewire"
DOMOGIK_PLUGIN_DESCRIPTION = "Manage 1 wire devices"
DOMOGIK_PLUGIN_VERSION = "0.1"
DOMOGIK_PLUGIN_DOCUMENTATION_LINK = "TODO"
DOMOGIK_PLUGIN_CONFIGURATION = [
      {"id" : 0,
       "key" : "startup-plugin",
       "type" : "boolean",
       "description" : "Automatically start plugin at Domogik startup",
       "default" : "False"},
      {"id" : 1,
       "key" : "temp-refresh",
       "type" : "number",
       "description" : "Temperature refresh delay (seconds)",
       "default" : TEMP_DELAY}]


class OneWireTemp(XplPlugin):
    '''
    Manage the One-Wire stuff and connect it to xPL
    '''

    def __init__(self):
        '''
        Starts some timers to check temperature
        '''
        XplPlugin.__init__(self, name='onewire')
        self._config = Query(self._myxpl)
        res = XplResult()
        self._config.query('onewire', 'temp-refresh', res)
        temp_delay = res.get_value()['temp-refresh']
        if temp_delay == "None":
            temp_delay = TEMP_DELAY
        self._myow = OneWire()
        self._myow.set_cache_use(False)
        stop = threading.Event()
        t_temp = XplTimer(float(temp_delay), self._gettemp, stop, self._myxpl)
        t_temp.start()

    def _gettemp(self):
        ''' Get the value of all 1wire components
        '''
        for (_id, _type, _val) in self._myow.get_temperatures():
            print "=> %s : %s : %s" % (_id, _type, _val)
            my_temp_message = XplMessage()
            my_temp_message.set_type("xpl-stat")
            my_temp_message.set_schema("sensor.basic")
            my_temp_message.add_data({"device" :  _id})
            #type should be the model of the o1wire component.
            #Anyway, because we need a way to determine which is the
            #technology of the device, we use it with value 'onewire'
            my_temp_message.add_data({"type" :  "onewire"})
            my_temp_message.add_data({"current" :  _val})
            print "msg = %s" % my_temp_message
            self._myxpl.send(my_temp_message)


if __name__ == "__main__":
    OneWireTemp()

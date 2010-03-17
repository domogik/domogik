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

Caller ID with modem support 

Implements
==========

- CallerIdModemManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import xPLPlugin
from domogik.xpl.common.plugin import xPLResult
from domogik.xpl.lib.cidmodem import CallerIdModem
from domogik.xpl.common.queryconfig import Query

IS_DOMOGIK_PLUGIN = True
DOMOGIK_PLUGIN_DESCRIPTION = "Get caller id with a modem"
DOMOGIK_PLUGIN_CONFIGURATION=[
      {"id" : 0,
       "key" : "startup-module",
       "description" : "Automatically start module at Domogik startup",
       "default" : "False"},
      {"id" : 1,
       "key" : "device", 
       "description" : "Modem device (ex : /dev/ttyUSB0 for an usb modem)", 
       "default" : "/dev/ttyUSB0"},
      {"id" : 2,
       "key" : "nbmaxtry", 
       "description" : "Max number of tries to open modem device",
       "default" : 5},
      {"id" : 3,
       "key" : "interval", 
       "description" : "Delay between each try to open modem device",
       "default" : 10}]
     


class CallerIdModemManager(xPLPlugin):
    '''
    Manage the Caller ID with Modem stuff and connect it to xPL
    '''

    def __init__(self):
        """ Init module
        """
        xPLPlugin.__init__(self, name='cidmodem')
        # Get config
        #   - serial port
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('cidmodem', 'device', res)
        device = res.get_value()['device']
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('cidmodem', 'interval', res)
        interval = res.get_value()['interval']
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('cidmodem', 'nbmaxtry', res)
        nbmaxtry = res.get_value()['nbmaxtry']
        # Call Library
        self._mycalleridmodem  = CallerIdModem(device, nbmaxtry, \
                                               interval, \
                                               self._broadcastframe)
        self._mycalleridmodem.start()

    def _broadcastframe(self, data):
        """ Send data on xPL network
            @param data : data to send : phone number
        """
        my_temp_message = XplMessage()
        my_temp_message.set_type("xpl-trig")
        my_temp_message.set_schema("cid.basic")
        my_temp_message.add_data({"calltype" : "INBOUND"})
        my_temp_message.add_data({"phone" : data})
        self._myxpl.send(my_temp_message)


if __name__ == "__main__":
    CallerIdModemManager()

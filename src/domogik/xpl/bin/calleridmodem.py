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

from domogik.xpl.lib.xplconnector import *
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.module import *
from domogik.xpl.lib.calleridmodem import *
from domogik.common import configloader
from domogik.xpl.lib.queryconfig import *


class CallerIdModemManager(xPLModule):
    '''
    Manage the Caller ID with Modem stuff and connect it to xPL
    '''

    def __init__(self):
        """ Init module
        """
        xPLModule.__init__(self, name='cidmodem')
        # Get config
        #   - serial port
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('calleridmodem', 'device', res)
        device = res.get_value()['device']
        # Call Library
        self._mycalleridmodem  = CallerIdModem(device, self._broadcastframe)
        self._mycalleridmodem.start()

    def _broadcastframe(self, data):
        my_temp_message = XplMessage()
        my_temp_message.set_type("xpl-trig")
        my_temp_message.set_schema("cid.basic")
        my_temp_message.add_data({"calltype" : "INBOUND"})
        my_temp_message.add_data({"phone" : data})
        self._myxpl.send(my_temp_message)


if __name__ == "__main__":
    CallerIdModemManager()

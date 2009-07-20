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

from domogik.xpl.lib.xplconnector import *
from domogik.xpl.lib.module import *
from domogik.xpl.lib.onewire import *
from domogik.common import configloader
from domogik.xpl.lib.queryconfig import *


class OneWireTemp(xPLModule):
    '''
    Manage the One-Wire stuff and connect it to xPL
    '''

    def __init__(self):
        '''
        Starts some timers to check temperature
        '''
        xPLModule.__init__(self, name='onewire')
        config = {"source":"dmg-onewire"}
        self._myxpl = Manager()
        self._config = Query(self.__myxpl)
        res = xPLResult()
        self._config.query('onewire', 'temperature_refresh_delay', res)
        temp_delay = res.get_value()['temperature_refresh_delay']
        self._myow = OneWire()
        self._myow.set_cache_use(False)
        t_temp = xPLTimer(temp_delay, self._gettemp)
        t_temp.start()

    def _gettemp():
        for (i, t, v) in self._myow.get_temperature():
            my_temp_message = Message()
            my_temp_message.set_type("xpl-trig")
            my_temp_message.set_schema("sensor.basic")
            my_temp_message.set_data_key("device", i)
            my_temp_message.set_data_key("type", t)
            my_temp_message.set_data_key("current", v)
            self._myxpl.send(my_temp_message)


if __name__ == "__main__":
    OneWireTemp()

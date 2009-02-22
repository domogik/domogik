#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-02-22 16:05:05 +0100 (dim. 22 févr. 2009) $
# $LastChangedRevision: 397 $

from domogik.xpl.lib.xplconnector import *
from onewire import *
from domogik.common import configloader



class OneWireTemp():
    '''
    Manage the One-Wire stuff and connect it to xPL
    '''
    def __init__(self):
        '''
        Starts some timers to check temperature
        '''
        cfgloader = Loader('onewire')
        config = cfgloader.load()
        self._myxpl = Manager(config["address"],port = config["port"], source = config["source"], module_name='onewire')
        self._myow = OneWire()
        self._myow.set_cache_use(False)
        timers = []
        t_temp = xPLTimer(config['temperature_delay'], self._gettemp)
        t_temp.start()
        timers.append(t)

    def _gettemp():
        for  (i, t, v) in self._myow.get_temperature():
            my_temp_message = Message()
            my_temp_message.set_type("xpl-trig")
            my_temp_message.set_schema("sensor.basic")
            my_temp_message.set_data_key("device", i)
            my_temp_message.set_data_key("type", t)
            my_temp_message.set_data_key("current", v) 
            self._myxpl.send(my_temp_message)

if __name__ == "__main__":
    OneWireTemp()

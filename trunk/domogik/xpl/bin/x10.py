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
# $LastChangedDate: 2009-03-20 12:03:31 +0100 (ven. 20 mars 2009) $
# $LastChangedRevision: 414 $

from domogik.xpl.lib.x10 import *
from domogik.xpl.lib.xplconnector import *
from domogik.common.configloader import Loader
from domogik.common import logger
from domogik.xpl.lib.queryconfig import *

class x10Main():

    def __init__(self):
        '''
        Create the X10Main class
        This class is used to connect x10 (through heyu) to the xPL Network
        '''
        cfgloader = Loader('x10')
        self._config = Query(self.__myxpl)
        res = xPLResult()
        self._config.query('x10', 'heyu_cfg_path', res)
        try:
            self.__myx10 = X10API(res.get_value())
        except:
            print "Something went wrong during heyu init, check logs"
            exit(1)
        self.__myxpl = Manager(module_name='x10')
        #Create listeners
        Listener(self.x10_cmnd_cb, self.__myxpl, {'schema': 'x10.basic',
                'type': 'xpl-cmnd'})
        l = logger.Logger('x10')
        self._log = l.get_logger()

    def x10_cmnd_cb(self, message):
        '''
        General callback for all command messages
        '''
        commands = {
            'on': lambda d, h, l: self.__myx10.on(d),
            'off': lambda d, h, l: self.__myx10.off(d),
            'all_units_on': lambda d, h, l: self.__myx10.house_on(h),
            'all_units_off': lambda d, h, l: self.__myx10.house_off(h),
            'all_lights_on': lambda d, h, l: self.__myx10.lights_on(h),
            'all_lights_off': lambda d, h, l: self.__myx10.lights_off(h),
            'bright': lambda d, h, l: self.__myx10.bright(d, l),
            'dim': lambda d, h, l: self.__myx10.dim(d, l),
            'brightb': lambda d, h, l: self.__myx10.bright(d, l),
            'dimb': lambda d, h, l: self.__myx10.dim(d, l),
        }
        cmd = None
        dev = None
        house = None
        level = None
        if 'command' in message:
            cmd = message.get_key_value('command')
        if 'device' in message:
            dev = message.get_key_value('device')
        if 'house' in message:
            house = message.get_key_value('house')
        if 'level' in message:
            level = message.get_key_value('level')
        self._log.debug("%s received : device = %s, house = %s, level = %s" % (
                cmd, dev, house, level))
        commands[cmd](dev, house, level)

if __name__ == "__main__":
    x = x10Main()

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
# $LastChangedDate: 2009-02-18 14:06:46 +0100 (mer. 18 févr. 2009) $
# $LastChangedRevision: 368 $

from x10API import *
from xPLAPI import *
from configloader import Loader

class x10Main():

    def __init__(self):
        '''
        Create the X10Main class
        This class is used to connect x10 (through heyu) to the xPL Network
        '''
        cfgloader = Loader('x10')
        config = cfgloader.load()[1]
        self.__myx10 = X10API(config["heyu_cfg_file"])
        self.__myxpl = Manager(config["address"],port = config["port"], source = config["source"], 'x10')
        #Create listeners
        Listener(self.x10_cmnd_cb, self.__myxpl, {'schema':'x10.basic','type':'xpl-cmnd'})

    def x10_cmnd_cb(self, message):
        '''
        General callback for all command messages
        '''
        commands = {
            'on': lambda d,h,l:self.__myx10.on(d),
            'off': lambda d,h,l:self.__myx10.off(d),
            'all_units_on': lambda d,h,l:self.__myx10.house_on(h),
            'all_units_off': lambda d,h,l:self.__myx10.house_off(h),
            'all_lights_on': lambda d,h,l:self.__myx10.lights_on(h),
            'all_lights_off': lambda d,h,l:self.__myx10.lights_off(h),
            'bright': lambda d,h,l:self.__myx10.bright(d,l),
            'dim': lambda d,h,l:self.__myx10.dim(d,l)
        }
        cmd = None
        dev = None
        house = None
        level = None
        if message.has_key('command'):
            cmd = message.get_key_value('command')
        if message.has_key('device'):
            dev = message.get_key_value('device')
        if message.has_key('house'):
            house = message.get_key_value('house')
        if message.has_key('level'):
            level = message.get_key_value('level')
        commands[cmd](dev, house, level)

if __name__ == "__main__":
    x = x10Main()

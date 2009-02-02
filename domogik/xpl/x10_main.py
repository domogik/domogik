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
# $LastChangedDate: 2009-02-01 11:32:09 +0100 (dim 01 fév 2009) $
# $LastChangedRevision: 304 $

from x10API import *
from xPLAPI import *
import configloader

class x10Main():

    def __init__(self):
        '''
        Create the X10Main class
        This class is used to connect x10 (throw heyu) to the xPL Network
        '''
        self.__myx10 = X10API()
        cfgloader = Loader('x10')
        config = cfgloader.load()
        self.__myxpl = Manager(config["address"],port = config["port"], source = config["source"])
        #Create listeners
        Listener(self.x10_cmnd_cb, self.__myxpl, {'schema':'x10.basic','type':'xpl-cmnd'})

    def x10_cmnd_cb(self, message):
        '''
        General callback for all command messages
        '''
        cmd = message.get_key_value('command')
        dev = message.get_key_value('device')
        print "CMD : %s - DEV : %s" % (cmd, dev)
        if cmd.lower() == 'on':
            print self.__myx10.on(dev)
        if cmd.lower() == 'off':
            print self.__myx10.off(dev)

if __name__ == "__main__":
    x = x10Main()

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

# $LastChangedBy: domopyx $
# $LastChangedDate: 2009-03-21 00:59:18 +0100 (sam. 21 mars 2009) $

from domogik.xpl.lib.xplconnector import *
from domogik.common.configloader import *
import re

class xPLSendHelper(xPLModule):
    """
    Helper to send basic xPL messages
    """

    def __init__(self):
        xPLModule.__init__(self, name = 'xplsendhelper')
        self.__myxpl = Manager()
        self._log = self.get_my_logger()

    def __del__(self):
        self.__myxpl.force_leave()

    def x10_on_unit(unit):
        """
        Send a message with command 'on' for unit
        @param unit : the unit to light up
        """
        if not re.match(r'^[a-pA-P][0-9]$', unit):
            raise ValueError, "Incorrect unit name"
        m = Message()
        mess.set_type("xpl-cmnd")
        mess.set_schema("x10.basic")
        mess.set_data_key("device", unit)
        mess.set_data_key("command", "on")
        self.__myxpl.send(m)



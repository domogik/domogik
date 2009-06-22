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

Helper to send xPL messages

Implements
==========

- xPLSendHelper.__init__(self)
- xPLSendHelper.__del__(self)
- xPLSendHelper.x10_on_unit(unit)
- xPLSendHelper.x10_off_unit(unit)
- xPLSendHelper.x10_on_house(house)
- xPLSendHelper.x10_off_house(house)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

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
        self.x10 = self.X10(self.__myxpl)

    def __del__(self):
        self.__myxpl.force_leave()

###
# Format check functions
###
	def _check_x10_unit_name(self, unit):
		"""
		Checks x10 unit_name_format
		@param unit : then unit's name
		"""
        return re.match(r'^[a-pA-P][0-9]$', unit)

	def _check_x10_house_name(self, unit):
		"""
		Checks x10 unit_name_format
		@param unit : then unit's name
		"""
        return re.match(r'^[a-pA-P]$', unit)

	def _check_plcbus_unit_name(self, unit):
		"""
		Checks plcbus unit_name_format
		@param unit : then unit's name
		"""
        return re.match(r'^[a-pA-P][0-9]$', unit)

	def _check_plcbus_house_name(self, unit):
		"""
		Checks plcbusunit_name_format
		@param unit : then unit's name
		"""
        return re.match(r'^[a-pA-P]$', unit)

###
# Public methods
###
    def x10_on_unit(unit):
        """
        Send a message with command 'on' for unit
        @param unit : the unit to light up
        """
        if not self._check_x10_unit_name(unit)
            raise ValueError, "Incorrect unit name"
        m = Message()
        mess.set_type("xpl-cmnd")
        mess.set_schema("x10.basic")
        mess.set_data_key("device", unit)
        mess.set_data_key("command", "on")
        self.__myxpl.send(m)

    def x10_off_unit(unit):
        """
        Send a message with command 'off' for unit
        @param unit : the unit to light down
        """
        if not self._check_x10_unit_name(unit)
            raise ValueError, "Incorrect unit name"
        m = Message()
        mess.set_type("xpl-cmnd")
        mess.set_schema("x10.basic")
        mess.set_data_key("device", unit)
        mess.set_data_key("command", "off")
        self.__myxpl.send(m)

    def x10_on_house(house):
        """
        Send a message with command 'on' for house
        @param house : the house house to light up
        """
        if not self._check_x10_house_name(house)
            raise ValueError, "Incorrect house name"
        m = Message()
        mess.set_type("xpl-cmnd")
        mess.set_schema("x10.basic")
        mess.set_data_key("device", house)
        mess.set_data_key("command", "all_units_on")
        self.__myxpl.send(m)

    def x10_off_house(house):
        """
        Send a message with command 'off' for house
        @param house : the house code to light down
        """
        if not self._check_x10_house_name(house)
            raise ValueError, "Incorrect house name"
        m = Message()
        mess.set_type("xpl-cmnd")
        mess.set_schema("x10.basic")
        mess.set_data_key("device", house)
        mess.set_data_key("command", "all_units_off")
        self.__myxpl.send(m)






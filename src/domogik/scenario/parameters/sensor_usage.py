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

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.parameters.abstract import AbstractParameter


class SensorUsageParameter(AbstractParameter):
    """ This parameter is used by the sensor test to choose if the test will be done : 
        - return the sensor value
        - return True if the value changes
        - return True if the value changes even if the value is the same as the previous value
    """

    def __init__(self, log=None, trigger=None):
        AbstractParameter.__init__(self, log, trigger)
        self.set_type("list")
        self.add_expected_entry("usage", "list", "Sensor usage")
        the_list = [["value", "value"],
                    ["trigger if the value change", "trigger_on_change"],
                    ["trigger if the value change or last update time change", "trigger_on_all"]]
        self.set_list_of_values("usage", the_list)

    def evaluate(self):
        """ Return chosen operator, or none if no operator choosed yet
        """
        p = self.get_parameters()
        if "usage" in p:
            return p["usage"]
        else:
            return "value"



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

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from threading import Thread, Event
from domogik.scenario.parameters.abstract import AbstractParameter
#from domogik.common.cron import CronExpression
import time
from domogik.common.utils import get_midnight_timestamp


class TimeHHMMParameter(AbstractParameter):
    """ This parameter  simply provides a time entry : hh:mm
    """

    def __init__(self, log = None, trigger = None):
        AbstractParameter.__init__(self, log, trigger)
        self.set_type("integer")
        self.add_expected_entry("time", "string", "Time (hh:mm)")

    def evaluate(self):
        """ Return string, or none if no string entered yet
        """
        params = self.get_parameters()
        print params
        tmp = params["time"].split(":")
        if len(tmp) != 2:
            self._log.warning("Bad time format for '{0}'. Expected : 'hh:mm'".format(params["time"]))
            self.expr = None
        try:
            given_time_in_minutes = int(tmp[0])*60 + int(tmp[1])
        except:  # bad format!
            self._log.warning("Bad time format for '{0}'. Expected : 'hh:mm'".format(params["time"]))
            self.expr = None
        print("{0}".format(given_time_in_minutes))
        return int(given_time_in_minutes)

    def destroy(self):
        """ Destroy fetch thread
        """
        AbstractParameter.destroy(self)

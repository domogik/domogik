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

# TODO
# overload fill method
# in fill method create a cronExpressionObject
# in evaluate check cronExpression.check_trigger_now()
# in destroy clean up the cron expression
from __future__ import absolute_import, division, print_function, unicode_literals
from threading import Thread, Event
from domogik.scenario.parameters.abstract import AbstractParameter
from domogik.common.cron import CronExpression

class CronParameter(AbstractParameter):
    """ This parameter  simply provides a text entry
    This is the simplest exemple for to see how you can extend Parameter
    """

    def __init__(self, log = None, trigger = None):
        AbstractParameter.__init__(self, log, trigger)
        self.set_type("string")
        self.add_expected_entry("cron", "string", "Cron expression")
        self.expr = None
        self._event = Event()
        self._fetch_thread = Thread(target=self._check,name="CronParameter.check")
        self._fetch_thread.start()

    def _check(self):
        """ This method will fetch the url peridodically and put the result in self._result
        It whould be called in some thread
        """
        while not self._event.is_set():
            self._result = False
            if self.expr:
                self._result = self.expr.check_trigger_now()
                if self._result:
                    self.call_trigger()
            # we only need to check every 60 seconds as cron works on minuts basis
            self._event.wait(60)

    def fill(self, params):
        AbstractParameter.fill(self, params)
        params = self.get_parameters()
        if "cron" in params:
            self.expr = CronExpression(params["cron"])
        else:
            self.expr = None

    def evaluate(self):
        """ Return string, or none if no string entered yet
        """
        return self._result

    def destroy(self):
        """ Destroy fetch thread
        """
        self._event.set()
        self._fetch_thread.join()
        AbstractParameter.destroy(self)

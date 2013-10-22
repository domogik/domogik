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

from domogik.common.scenario.parameters.abstract import AbstractParameter
from domogik.common.cron import CronExpression

class CronParameter(AbstractParameter):
    """ This parameter  simply provides a text entry
    This is the simplest exemple for to see how you can extend Parameter
    """

    def __init__(self, log = None, xpl = None, trigger = None):
        AbstractParameter.__init__(self, log, xpl, trigger)
        self.set_type("string")
        self.add_expected_entry("cron", "string", "Cron timed trigger")
        self.expr = None

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
        if self.expr:
            return self.expr.check_trigger_now()
        else:
            return None

#Some basic tests
if __name__ == "__main__":
    import logging
    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)
    t = CronParameter(logging, None)
    print "Expected entries : %s" % t.get_expected_entries()
    print "Evaluate should be None : %s" % t.evaluate()
    print "==> Setting some value for entry 'text'"
    data = { "cron" : "*/2 * * * *" }
    t.fill(data)
    print "Evaluate should return true on even minuts : %s" % t.evaluate()

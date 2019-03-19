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

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.tests.abstract import AbstractTest
import time

class TimestampNow(AbstractTest):
    """ Return current timestamp in seconds
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self.set_outputCheck(["Number"])
        self.set_description("Current timestamp (seconds)")


    def evaluate(self):
        """ Evaluate the current timestamp
        """
        res = int(time.time())
        self.log.debug(u"Evaluate current timestamp to '{0}' seconds. Type is '{1}'".format(res, type(res)))
        return res

if __name__ == "__main__":
    import logging
    TEST = None

    def mytrigger(test):
        print("Trigger called by test {0}, refreshing state".format(test))
        st = TEST.evaluate()
        print("state is {0}".format(st))

    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)
    TEST = TimestampNow(logging, trigger = mytrigger)
    print(TEST)
    print("getting parameters")
    p = TEST.get_parameters()
    print(p)
    print("====")
    print("set data for parameters time")
    print("Trying to evaluate : {0}".format(TEST.evaluate()))
    TEST.destroy()

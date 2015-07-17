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
from time import sleep

class CronTest(AbstractTest):
    """ Simple test to check if a word is contained in an url
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self.set_description("Trigger on a certain timed event")
        self.add_parameter("cron", "cron.CronParameter")

    def evaluate(self):
        print("CROOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOON eval")
        """ Evaluate if the text appears in the content of the page referenced by url
        """
        params = self.get_raw_parameters()
        crn = params["cron"]
        if crn.evaluate() == None:
            return None
        else:
            res = crn.evaluate()
            self.log.debug("Evaluate {0} : {1}".format(crn, res))
            return res


if __name__ == "__main__":
    import logging
    TEST = None

    def mytrigger(test):
        print("Trigger called by test {0}, refreshing state".format(test))
        st = TEST.evaluate()
        print "state is %s" % st

    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)
    TEST = CronTest(logging, trigger = mytrigger)
    print(TEST)
    print("getting parameters")
    p = TEST.get_parameters()
    print(p)
    print("====")
    print("Trying to evaluate : {0}".format(TEST.evaluate()))
    print("====")
    print("set data for parameters cron")
    data = { "cron": { "cron" : "*/2 * * * *"} }
    TEST.fill_parameters(data)
    sleep(5)
    print("Trying to evaluate : {0}".format(TEST.evaluate()))
    TEST.destroy()

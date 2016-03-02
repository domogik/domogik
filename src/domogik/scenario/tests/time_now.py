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
from domogik.common.utils import get_midnight_timestamp
import time
from threading import Thread, Event

class TimeNow(AbstractTest):
    """ Return current time in minutes
    """

    def __init__(self, log = None, trigger = None, cond = None, params = None):
        AbstractTest.__init__(self, log, trigger, cond, params)
        self.set_description("Current time (hh:mm)")
        self._res = None
        # start the thread
        self._event = Event()
        self._fetch_thread = Thread(target=self._fetch,name="pollthread")
        self._fetch_thread.start()

    def _fetch(self):
        while not self._event.is_set():
            now = time.time()
            self._res = int((now - get_midnight_timestamp())/60)
            # no parameters, so no trigger to raise
            #self._trigger(self)
            self._event.wait(60)

    def evaluate(self):
        """ Evaluate if the time is the current one
        """
        self.log.debug("Evaluate current time to '{0}' minutes. Type is '{1}'".format(self._res, type(self._res)))
        return self._res

    def destroy(self):
        """ Destroy fetch thread
        """
        self._event.set()
        self._fetch_thread.join()
        AbstractTest.destroy(self)

if __name__ == "__main__":
    import logging
    TEST = None

    def mytrigger(test):
        print("Trigger called by test {0}, refreshing state".format(test))
        st = TEST.evaluate()
        print "state is %s" % st

    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)
    TEST = TimeNow(logging, trigger = mytrigger)
    print(TEST)
    print("getting parameters")
    p = TEST.get_parameters()
    print(p)
    print("====")
    print("set data for parameters time")
    print("Trying to evaluate : {0}".format(TEST.evaluate()))
    TEST.destroy()

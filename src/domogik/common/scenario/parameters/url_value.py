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

from domogik.common.scenario.parameters.abstract import AbstractParameter
from threading import Thread, Event
from urllib import urlopen
import sys

class UrlParameter(AbstractParameter):
    """ This parameter looks periodically at some URL and return the content of the page
    """

    def __init__(self, log = None, trigger = None):
        AbstractParameter.__init__(self, log, trigger)
        self.set_type("url")
        self.add_expected_entry("urlpath", "string", "Url the script will fetch")
        self.add_expected_entry("interval", "string", "Interval between 2 fetch in second")
        self.set_default_value("interval", "10")
        self._result = None
        self._event = Event()
        self._fetch_thread = Thread(target=self._fetch,name="UrlParameter.fetch")
        self._fetch_thread.start()

    def _fetch(self):
        """ This method will fetch the url peridodically and put the result in self._result
        It whould be called in some thread
        """
        while not self._event.is_set():
            p =  self.get_parameters()
            if "urlpath" in p:
                try:
                    u = urlopen(p["urlpath"])
                except:
                    self._log.warn("urlopen : Exception occured : {0}".format(sys.exc_info()[0]))
                    self._result = None
                else:
                    self._result = "\n".join(u.readlines())
                    self.call_trigger()
            if "interval" in p:
                self._event.wait(int(p["interval"]))
            else:
                self._event.wait(10)

    def evaluate(self):
        """ return contents of url or none"
        """
        return self._result

    def destroy(self):
        """ Destroy fetch thread
        """
        self._event.set()
        self._fetch_thread.join()
        AbstractParameter.destroy(self)


#Some basic tests
if __name__ == "__main__":
    import logging
    from time import sleep
    FORMAT = "%(asctime)-15s %(message)s"
    logging.basicConfig(format=FORMAT)
    t = UrlParameter(logging, None)
    print("Expected entries : {0}".format(t.get_expected_entries()))
    print("Evaluate should be None : {0}".format(t.evaluate()))
    print("==> Setting some url value for entries")
    data = { "urlpath" : "http://people.dunnewind.net/maxence/domogik/test.txt",
    "interval": "5"}
    t.fill(data)
    print("I wait 12 seconds")
    sleep(12)
    print("And I check the result now that the page has (normally) been fetched : {0}".format(t.evaluate()))
    print("And I destroy the parameter")
    t.destroy()


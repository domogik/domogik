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

Plugin purpose
==============

Send events at dawn/dusk

Implements
==========
Class dawnduskAPI
- dawndusk:.__init__(self)
- dawndusk:.get_dawn_dusk(self, long, lat, fh)

Class dawnduskScheduler

Class dawnduskException

@author: Sébastien Gallet <sgallet@gmail.com>
@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import datetime
import math
from apscheduler.scheduler import Scheduler
import ephem
from ephem import CircumpolarError
from ephem import NeverUpError
from ephem import AlwaysUpError

class dawnduskScheduler:
    """
    dawndusk scheduler
    """
    def __init__(self):
        # Start the scheduler
        self._sched = Scheduler()
        self._sched.start()

    def __del__(self):
        self._sched.shutdown()

    def add(self,sdate,cb_function,label):
        # Start the scheduler
        self.job = self._sched.add_date_job(cb_function, sdate, [label])

class dawnduskException(Exception):
    """
    dawndusk exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

class dawnduskAPI:
    """
    dawndusk API
    """

    def __init__(self):
        """
        Init the dawndusk API
        """
        self._scheduler = dawnduskScheduler()

    def schedAdd(self,sdate,cb_function,label):
        """
        Add an event in the schedulered tasks
        @param sdate : the date of the event
        @param cb_function : the callback function to call
        @param : the label of the event
        """
        self.job = self._scheduler._sched.add_date_job(cb_function, sdate, [label])

    def schedList(self):
        """
        Return the list of schedulered events
        @return : the list of the schedulered events
        """
        data = []
        jobs = self._scheduler._sched.get_jobs()
        for i in jobs:
            data.append(str(i))
        return data

    def getNextDawn(self, lgt, lat):
        """
        Return the date and time of the next dawn
        @param lgt : longitude of the observer
        @param lat : latitude of the observer
        @return : the next dawn daytime
        """
        mycity = ephem.Observer()
        mycity.lat, mycity.lon = str(lat), str(lgt)
        mycity.date = datetime.datetime.today()
        mycity.horizon = '-6'
        dawn = ephem.localtime(mycity.next_rising(ephem.Sun(), use_center=True))
        return dawn

    def getNextDusk(self, lgt, lat):
        """
        Return the date and time of the dawn
        @param lgt : longitude of the observer
        @param lat : latitude of the observer
        @return : the next dusk daytime
        """
        mycity = ephem.Observer()
        mycity.lat, mycity.lon = str(lat), str(lgt)
        mycity.date = datetime.datetime.today()
        mycity.horizon = '-6'
        dusk = ephem.localtime(mycity.next_setting(ephem.Sun(), use_center=True))
        return dusk

if __name__ == "__main__":
    dd = dawnduskAPI()
    l = dd.getNextDawn(-01.7075, 48.1173)
    print(l)
    c = dd.getNextDusk(-01.7075, 48.1173)
    print(c)

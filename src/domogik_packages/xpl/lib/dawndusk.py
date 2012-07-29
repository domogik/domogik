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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ephem
import datetime
from apscheduler.scheduler import Scheduler
from domogik.xpl.common.xplmessage import XplMessage
try:
    from domogik_packages.xpl.lib.cron_query import CronQuery
except ImportError:
    pass

class DawnduskException(Exception):
    """
    dawndusk exception
    """

    def __init__(self, value):
        """
        dawndusk exception
        """
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        """
        dawndusk exception
        """
        return repr(self.value)

class DawnduskAPI:
    """
    dawndusk API
    """

    def __init__(self, lgt, lat, use_cron, myxpl, log):
        """
        Init the dawndusk API
        @param lgt : longitude of the observer
        @param lat : latitude of the observer
        """
        self.use_cron = use_cron
        self.log = log
        self.myxpl = myxpl
        if self.use_cron == False:
            self._scheduler = Scheduler()
            self._scheduler.start()
        else:
            self._cronquery = CronQuery(self.myxpl, self.log)
        self.mycity = ephem.Observer()
        self.mycity.lat, self.mycity.lon = lat, lgt
        self.mycity.horizon = '-6'
        self.job = None
        self.job_test_dawn = None
        self.job_test_dusk = None

    def __del__(self):
        """
        Kill the dawndusk API
        @param lgt : longitude of the observer
        @param lat : latitude of the observer
        """
        if self.use_cron == True:
            self._cronquery.halt_job("dawndusk")
            self._cronquery.halt_job("dawn-test")
            self._cronquery.halt_job("dusk-test")
        else :
            self._scheduler.shutdown()

    def sched_add(self, sdate, cb_function, label):
        """
        Add an event in the schedulered tasks
        @param sdate : the date of the event
        @param cb_function : the callback function to call
        @param : the label of the event
        """
        self.log.debug("dawndusk.schedAdd : Start ... %s" % label)
        if self.use_cron == False:
            if label == "dawn" or label == "dusk":
                self.job = self._scheduler.add_date_job(cb_function, \
                    sdate, args = [label])
                self.log.debug("dawndusk.schedAdd : Use internal cron \
                    for %s" % label)
            elif label == "dawn-test":
                self.job_test_dawn = self._scheduler.add_date_job\
                    (cb_function, sdate, args = ["dawn"])
                self.log.debug("dawndusk.schedAdd : Use internal cron \
                    for %s" % "dawn")
            elif label == "dusk-test":
                self.job_test_dusk = self._scheduler.add_date_job\
                    (cb_function, sdate, args = ["dusk"])
                self.log.debug("dawndusk.schedAdd : Use internal cron \
                    for %s" % "dusk")
            for i in self._scheduler.get_jobs():
                self.log.debug("APScheduler : %-10s | %8s" % \
                    (str(i.trigger), i.runs))
        else :
            self.log.debug("dawndusk.schedAdd : Use external cron ...")
            if label == "dawn" or label == "dusk":
                device = "dawndusk"
            elif label == "dawn-test":
                device = "dawn-test"
            elif label == "dusk-test":
                device = "dusk-test"
            if self._cronquery.status_job(device, extkey = "current") \
                != "halted":
                self._cronquery.halt_job(device)
                self.log.debug("dawndusk.schedAdd : Halt old device")
            nstmess = XplMessage()
            nstmess.set_type("xpl-trig")
            nstmess.set_schema("dawndusk.basic")
            nstmess.add_data({"type" : "dawndusk"})
            if label == "dawn":
                nstmess.add_data({"status" :  "dawn"})
            elif label == "dusk":
                nstmess.add_data({"status" :  "dusk"})
            elif label == "dawn-test":
                nstmess.add_data({"status" :  "dawn"})
            elif label == "dusk-test":
                nstmess.add_data({"status" :  "dusk"})
            if self._cronquery.start_date_job(device, nstmess, sdate):
                self.log.debug("dawndusk.schedAdd : External cron activated")
                self.log.debug("dawndusk.schedAdd : Done :)")
            else:
                self.log.error("dawndusk.schedAdd : Can't activate \
                    external cron")
                self.log.debug("dawndusk.schedAdd : Done :(")
                return False
        self.log.info("Add a new event of type %s at %s" % (label, sdate))
        return True

    def get_next_dawn(self):
        """
        Return the date and time of the next dawn
        @return : the next dawn daytime
        """
        self.mycity.date = datetime.datetime.today()
        dawn = ephem.localtime(self.mycity.next_rising(ephem.Sun(), \
            use_center = True))
        return dawn

    def get_next_dusk(self):
        """
        Return the date and time of the dusk
        @return : the next dusk daytime
        """
        self.mycity.date = datetime.datetime.today()
        dusk = ephem.localtime(self.mycity.next_setting(ephem.Sun(), \
            use_center = True))
        return dusk

    def get_next_fullmoon_dawn(self):
        """
        Return the date and time of the next dawn and dusk of the next fullmoon
        @return : the next dawn daytime
        """
        self.mycity.date = self._get_next_fullmoon()
        dawn = ephem.localtime(self.mycity.next_rising(ephem.Moon(), \
            use_center = True))
        dusk = ephem.localtime(self.mycity.next_setting(ephem.Moon(), \
            use_center = True))
        if dawn > dusk:
            dawn = ephem.localtime(self.mycity.previous_rising(ephem.Moon(), \
            use_center = True))
        return dawn

    def get_next_fullmoon_dusk(self):
        """
        Return the date and time of the dusk of the next fullmoon
        @return : the next dusk daytime
        """
        self.mycity.date = self._get_next_fullmoon()
        dusk = ephem.localtime(self.mycity.next_setting(ephem.Moon(), \
            use_center = True))
        return dusk

    def get_next_fullmoon(self):
        """
        Return the date and time of the next fullmoon
        @return : the next full moon daytime
        """
        dusk = ephem.localtime(self._get_next_fullmoon())
        return dusk

    def _get_next_fullmoon(self):
        """
        Return the date and time of the next full moon
        @return : the next full moon daytime
        """
        now = datetime.datetime.today()
        nextfullmoon = ephem.next_full_moon(now)
        return nextfullmoon

if __name__ == "__main__":
    D = DawnduskAPI()

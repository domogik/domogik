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

from domogik.xpl.common.xplmessage import XplMessage
import datetime
import math
from apscheduler.scheduler import Scheduler
import ephem
from ephem import CircumpolarError
from ephem import NeverUpError
from ephem import AlwaysUpError
from domogik.xpl.lib.cron_query import cronQuery

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

    def __init__(self,lgt,lat,use_cron,myxpl,log):
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
            self._cronQuery = cronQuery(self.myxpl,self.log)
        self.mycity = ephem.Observer()
        self.mycity.lat, self.mycity.lon = lat, lgt
        self.mycity.horizon = '-6'

    def __del__(self):
        """
        Kill the dawndusk API
        @param lgt : longitude of the observer
        @param lat : latitude of the observer
        """
        if self.use_cron == True:
            self._cronQuery.haltJob("dawndusk")
            self._cronQuery.haltJob("dawn-test")
            self._cronQuery.haltJob("dusk-test")
        else :
            self._scheduler.shutdown()

    def schedAdd(self,sdate,cb_function,label):
        """
        Add an event in the schedulered tasks
        @param sdate : the date of the event
        @param cb_function : the callback function to call
        @param : the label of the event
        """
        self.log.debug("dawndusk.schedAdd : Start ... %s"%label)
        if self.use_cron == False:
            if label=="dawn" or label=="dusk":
                self.job = self._scheduler.add_date_job(cb_function, sdate, args=[label])
                self.log.debug("dawndusk.schedAdd : Use internal cron for %s"%label)
            elif label=="dawn-test":
                self.job_test_dawn = self._scheduler.add_date_job(cb_function, sdate, args=["dawn"])
                self.log.debug("dawndusk.schedAdd : Use internal cron for %s"%"dawn")
            elif label=="dusk-test":
                self.job_test_dawn = self._scheduler.add_date_job(cb_function, sdate, args=["dusk"])
                self.log.debug("dawndusk.schedAdd : Use internal cron for %s"%"dusk")
            for i in self._scheduler.get_jobs():
                self.log.debug("APScheduler : %-10s | %8s"%(str(i.trigger), i.runs))
        else :
            self.log.debug("dawndusk.schedAdd : Use external cron ...")
            if label=="dawn" or label=="dusk":
                device="dawndusk"
            elif label=="dawn-test":
                device="dawn-test"
            elif label=="dusk-test":
                device="dusk-test"
            #print "status=%s"%self._cronQuery.statusJob(device,extkey="current")
            if self._cronQuery.statusJob(device,extkey="current")!="halted":
                self._cronQuery.haltJob(device)
                self.log.debug("dawndusk.schedAdd : Halt old device")
            nstMess = XplMessage()
            nstMess.set_type("xpl-trig")
            nstMess.set_schema("dawndusk.basic")
            nstMess.add_data({"type" : "dawndusk"})
            if label=="dawn":
                nstMess.add_data({"status" :  "dawn"})
            elif label=="dusk":
                nstMess.add_data({"status" :  "dusk"})
            elif label=="dawn-test":
                nstMess.add_data({"status" :  "dawn"})
            elif label=="dusk-test":
                nstMess.add_data({"status" :  "dusk"})
            if self._cronQuery.startDateJob(device,nstMess,sdate):
                self.log.debug("dawndusk.schedAdd : External cron activated")
                self.log.debug("dawndusk.schedAdd : Done :)")
            else:
                self.log.error("dawndusk.schedAdd : Can't activate external cron")
                self.log.debug("dawndusk.schedAdd : Done :(")
                return False
        self.log.info("Add a new event of type %s at %s"%(label,sdate))
        return True

    def getNextDawn(self):
        """
        Return the date and time of the next dawn
        @return : the next dawn daytime
        """
        self.mycity.date = datetime.datetime.today()
        dawn = ephem.localtime(self.mycity.next_rising(ephem.Sun(), use_center=True))
        return dawn

    def getNextDusk(self):
        """
        Return the date and time of the dusk
        @return : the next dusk daytime
        """
        self.mycity.date = datetime.datetime.today()
        dusk = ephem.localtime(self.mycity.next_setting(ephem.Sun(), use_center=True))
        return dusk

    def getNextFullMoonDawn(self):
        """
        Return the date and time of the next dawn and dusk of the next fullmoon
        @return : the next dawn daytime
        """
        self.mycity.date = self._getNextFullMoon()
        dawn = ephem.localtime(self.mycity.next_rising(ephem.Moon(), use_center=True))
        dusk = ephem.localtime(self.mycity.next_setting(ephem.Moon(), use_center=True))
        if dawn>dusk:
            dawn=ephem.localtime(self.mycity.previous_rising(ephem.Moon(), use_center=True))
        return dawn

    def getNextFullMoonDusk(self):
        """
        Return the date and time of the dusk of the next fullmoon
        @return : the next dusk daytime
        """
        self.mycity.date = self._getNextFullMoon()
        dusk = ephem.localtime(self.mycity.next_setting(ephem.Moon(), use_center=True))
        return dusk

    def getNextFullMoon(self):
        """
        Return the date and time of the next fullmoon
        @return : the next full moon daytime
        """
        dusk = ephem.localtime(self._getNextFullMoon())
        return dusk

    def _getNextFullMoon(self):
        """
        Return the date and time of the next full moon
        @return : the next full moon daytime
        """
        now=datetime.datetime.today()
        nextfullmoon=ephem.next_full_moon(now)
        return nextfullmoon

if __name__ == "__main__":
    dd = dawnduskAPI()
    l = dd.getNextDawn(-01.7075, 48.1173)
    print(l)
    c = dd.getNextDusk(-01.7075, 48.1173)
    print(c)

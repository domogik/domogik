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

xPL Cron like

Implements
==========
Class cron

Helps
=====
devicetipes:
------------
timer
Parameters : frequence, duration
Create an infinite timer which beat every 30 seconds:
./send.py xpl-cmnd timer.basic "action=start,device=timer1,devicetype=timer,frequence=30"
Create a timer which beats 3 times every 60 seconds:
./send.py xpl-cmnd timer.basic "action=start,device=timer1,devicetype=timer,frequence=60,duration=3"

date
Parameters : date
Create a unique date schedulered job :
./send.py xpl-cmnd timer.basic "action=start,device=timer1,devicetype=date,date=YYYYMMDDHHMMSS"


interval
Parameters : weeks, days, hours, minutes, seconds, startdate
Create an interval schedulered job which beats every 2 weeks :
./send.py xpl-cmnd timer.basic "action=start,device=timer1,devicetype=interval,weeks=2"
Create an interval schedulered job which beat every 2 days, after startdate :
./send.py xpl-cmnd timer.basic "action=start,device=timer1,devicetype=interval,days=2,startdate=YYYYMMDDHHMMSS"

cron
Parameters : year, month, day, week, day_of_week, hour, minute, second, startdate
Use a cron like syntax.
Schedules job_function to be run on the third Friday of June, July, August, November and December at 00:00, 01:00, 02:00 and 03:00
./send.py xpl-cmnd timer.basic "action=start,device=timer1,devicetype=cron,month='6-8,11-12', day='3rd fri', hour='0-3'"
Schedule a backup to run once from Monday to Friday at 5:30 (am)
./send.py xpl-cmnd timer.basic "action=start,device=timer1,devicetype=cron, day_of_week='mon-fri', hour=5, minute=30"

actions :
---------
start : create and start a job
stop : stop the job.
./send.py xpl-cmnd timer.basic "action=stop,device=timer1"
resume : restart a stopped job
./send.py xpl-cmnd timer.basic "action=resume,device=timer1"
halt : stop and remove a job
./send.py xpl-cmnd timer.basic "action=halt,device=timer1"
list : list jobs
./send.py xpl-cmnd timer.basic "action=list"

request :
---------
./send.py xpl-cmnd timer.request "device=timer1"

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.plugin import XplPlugin
import datetime
from datetime import timedelta
from domogik.xpl.lib.cron import cronAPI
from domogik.xpl.lib.cron import cronJobs
from domogik.xpl.lib.cron import cronException
from domogik.xpl.lib.helperplugin import XplHlpPlugin
import traceback
import logging

class cron(XplHlpPlugin):
    '''
    Manage
    '''
    def __init__(self):
        """
        Create the cron class
        """
        XplHlpPlugin.__init__(self, name = 'cron')
        self.log.info("cron.__init__ : Start ...")
        self.config = Query(self.myxpl, self.log)

        self.log.debug("cron.__init__ : Try to start the cron API")
        try:
            self._cron = cronAPI(self.log,self.config,self.myxpl)
        except:
            error = "Something went wrong during cronAPI init : %s" %  \
                     (traceback.format_exc())
            self.log.exception("cron.__init__ : "+error)
            raise cronException(error)

        self.log.debug("cron.__init__ : Try to create listeners")
        Listener(self.request_cmnd_cb, self.myxpl,
                 {'schema': 'timer.request', 'xpltype': 'xpl-cmnd'})
        Listener(self.basic_cmnd_cb, self.myxpl,
                 {'schema': 'timer.basic', 'xpltype': 'xpl-cmnd'})

        self.helpers =   \
           { "list" :
              {
                "cb" : self._cron.jobs.helperList,
                "desc" : "List devices (cron jobs)",
                "usage" : "list all (all the devices)|aps(jobs in APScheduler)",
                "param-list" : "which",
                "which" : "all|aps",
              },
             "ls" :
              {
                "cb" : self._cron.jobs.helperList,
                "desc" : "List devices (cron jobs)",
                "usage" : "list all the devices",
                "return-list" : "array1",
                "array1" : "multi",
              },
             "test" :
              {
                "cb" : self._cron.jobs.helperList,
                "desc" : "Test return transfert",
                "usage" : "test",
                "param-list" : "device",
                "device" : "<device>",
                "return-list" : "array1,single",
                "array1" : "multi",
              },
             "info" :
              {
                "cb" : self._cron.jobs.helperInfo,
                "desc" : "Display device information",
                "usage" : "info <device>",
                "param-list" : "device",
                "device" : "<device>",
              },
             "stop" :
              {
                "cb" : self._cron.jobs.helperStop,
                "desc" : "Stop a device",
                "usage" : "stop <device>",
                "param-list" : "device",
                "device" : "<device>",
              },
             "halt" :
              {
                "cb" : self._cron.jobs.helperHalt,
                "desc" : "Halt a device",
                "usage" : "halt <device>",
                "param-list" : "device",
                "device" : "<device>",
              },
             "resume" :
              {
                "cb" : self._cron.jobs.helperResume,
                "desc" : "Resume a device",
                "usage" : "resume <device>",
                "param-list" : "device",
                "device" : "<device>",
              },
            }

        self.enable_helper()
        self.enable_hbeat()
        self.log.info("cron plugin correctly started")

    def request_cmnd_cb(self, message):
        """
        General callback for timer.request messages
        @param message : an XplMessage object
        """
        self.log.debug("cron.request_cmnd_cb() : Start ...")
        self._cron.requestListener(message)
        self.log.debug("cron.request_cmnd_cb() : Done :)")

    def basic_cmnd_cb(self, message):
        """
        General callback for timer.basic messages
        @param message : an XplMessage object
        """
        self.log.debug("cron.basic_cmnd_cb() : Start ...")
        self._cron.basicListener(message)
        self.log.debug("cron.basic_cmnd_cb() : Done :)")

if __name__ == "__main__":
    cron()

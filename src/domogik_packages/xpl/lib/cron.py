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
XPL Cron server.

Implements
==========
class cronJobs
class cronException
class cronAPI

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import datetime
import time
import urllib2
import threading
from domogik.xpl.common.xplconnector import XplTimer
from domogik.xpl.common.xplmessage import XplMessage
from apscheduler.scheduler import Scheduler
from domogik_packages.xpl.lib.cron_tools import *
from domogik_packages.xpl.lib.cron_helpers import CronHelpers
from domogik.common.configloader import Loader
from pympler.asizeof import asizeof
import ast
import logging
from threading import Timer

logging.basicConfig()

#MEMORY USAGE
MEMORY_PLUGIN = 1
MEMORY_API = 2
MEMORY_SCHEDULER = 3
MEMORY_DATA = 4
MEMORY_STORE = 5

class CronJobs():
    """
    Encapsulate the cronjobs.
    """
    def __init__(self, api):
        """
        Init the cronjobs container

        @param api:

        """
        self.data = dict()
        self._api = api
        self._scheduler = Scheduler()
        self.store = CronStore(self._api.log, self._api.data_files_dir)
        self._scheduler.start()
        self.store.load_all(self.add_job)
        self._api.log.info("Load %s jobs from store." % len(self.data))

    def memory_usage(self, which):
        '''
        Return the memory used by an object

        @param which: the counter to get. 0 to get all counters.

        '''
        if which == 0 :
            data = []
            data.append("api : %s items, %s bytes" % (1, asizeof(self)))
            data.append("apscheduler : %s items, %s bytes" % (1, asizeof(self._scheduler)))
            data.append("jobs dict : %s items, %s bytes" % (len(self.data), asizeof(self.data)))
            data.append("store : %s items, %s bytes" % (1, asizeof(self.store)))
            return data
        else:
            if which == MEMORY_PLUGIN:
                return 0, 0
            elif which == MEMORY_API:
                return 1, asizeof(self)
            elif which == MEMORY_SCHEDULER:
                return 1, asizeof(self._scheduler)
            elif which == MEMORY_DATA:
                return len(self.data), asizeof(self.data)
            elif which == MEMORY_STORE:
                return 1, asizeof(self.store)
        return None

    def stop_scheduler(self):
        """
        Stop the aps scheduler. Must be called before killing the plugin.
        """
        self._scheduler.shutdown()

    def stop_ap_jobs(self, device):
        """
        stop the APScheduler jobs of a device

        @param device : the name of the job (=device in xpl)

        """
        if device in self.data:
            if 'apjob' in self.data[device]:
                try:
                    self._scheduler.unschedule_job(\
                        self.data[device]['apjob'])
                except:
                    self._api.log.warning("Can't unschedule AP job %s" % \
                        self.data[device]['apjob'])
                del(self.data[device]['apjob'])
            if 'apjobs' in self.data[device]:
                while len(self.data[device]['apjobs']) > 0:
                    i = self.data[device]['apjobs'].pop()
                    try:
                        self._scheduler.unschedule_job(i)
                    except:
                        self._api.log.warning("Can't unschedule AP job %s" % i)
                del (self.data[device]['apjobs'])
            return ERROR_NO
        else:
            return ERROR_DEVICE_NOT_EXIST

    def close_all(self):
        """
        Close all jobs

        """
        for device in self.data:
            self.store.on_close(device, self.get_up_time(device), \
                self.get_full_run_time(device), \
                self.get_runs(device))
        return ERROR_NO

    def stop_job(self, device):
        """
        stop a job

        @param device : the name of the job (=device in xpl)

        """
        if device in self.data:
            newruntime = self.get_full_run_time(device)
            self.store.on_stop(device, self.get_up_time(device), \
                newruntime, \
                self.get_runs(device))
            self.stop_ap_jobs(device)
            self.data[device]['state'] = "stopped"
            self.data[device]['runtime'] = newruntime
            return ERROR_NO
        else:
            return ERROR_DEVICE_NOT_EXIST

    def halt_job(self, device):
        """
        Stop and remove a job

        @param device : the name of the job (=device in xpl)

        """
        if device in self.data:
            try :
                self.stop_job(device)
            except :
                self._api.log.warning("Can't stop job %s." % device)
            finally :
                self._api.log.warning("Delete job %s.and it's file." % device)
                self.store.on_halt(device)
                del(self.data[device])
            return ERROR_NO
        else:
            return ERROR_DEVICE_NOT_EXIST

    def resume_job(self, device):
        """
        Resume a job

        @param device : the name of the job (=device in xpl)

        """
        if device in self.data:
            if self.get_state(device) == "stopped":
                self.store.on_resume(device)
                return self.start_job(device)
            else:
                return ERROR_DEVICE_NOT_STOPPED
        else:
            return ERROR_DEVICE_NOT_EXIST

    def start_job(self, device):
        """
        start a job

        @param device : the name of the job (=device in xpl)

        """
        devicetypes = {
            'date': lambda d: self._start_job_date(d),
            'timer': lambda d: self._start_job_timer(d),
            'interval': lambda d: self._start_job_interval(d),
            'cron': lambda d: self._start_job_cron(d),
            'hvac': lambda d: self._start_job_hvac(d),
            'alarm': lambda d: self._start_job_alarm(d),
            'dawnalarm': lambda d: self._start_job_dawn_alarm(d),
        }
        if device in self.data:
            self.store.on_start(device, self.data[device])
            devicetype = self.data[device]['devicetype']
            return devicetypes[devicetype](device)
        else:
            return ERROR_DEVICE_NOT_EXIST

    def _job_started(self, device):
        """
        Update stats when a job is started

        @param device : the name of the job (=device in xpl)

        """
        self.data[device]['state'] = "started"
        self.data[device]['starttime'] = \
            datetime.datetime.today().strftime("%x %X")

    def _start_job_date(self, device):
        """
        Start a job of type date

        timer.basic
           {
            action=start
            device=<name of the timer>
            devicetype=date
            date= the datetime of the job (YYYYMMDDHHMMSS)
           }

        @param device : the name of the job (=device in xpl)

        """
        okk = True
        try:
            #print "data : %s" % self.data[device]
            if 'date' not in self.data[device] and 'date0' not in self.data[device] :
                okk = False
            parameters = self._extract_parameters(device)
            #print "parameters : %s" % parameters
            if okk == False:
                self._api.log.warning("_start_job_date : Don't add alarm job : missing parameters")
                #del(self.data[device])
                return ERROR_PARAMETER
            events = {}
            cur_value = "valueon"
            for key in self.data[device]:
                if key.startswith("date"):
                    dates = set()
                    if type(self.data[device][key]) == type(""):
                        dates.add(self.data[device][key])
                    else :
                        dates = self.data[device][key]
                    #Alarm is a list of alarm
                    for date in dates:
                        xpldate = date
                        #xpldate = self.data[device][key]
                        print "xpl date = " + xpldate
                        sdate = self._api.tools.date_from_xpl(xpldate)
                        if sdate != None :
                            events[xpldate] = cur_value
                            if cur_value == "valueon" :
                                cur_value = "valueoff"
                            else:
                                cur_value = "valueon"
                            okk = True
            if okk:
                #print("events=%s"%events)
                jobs = []
                for d in events:
                    if len(events) == 1:
                        sdate = self._api.tools.date_from_xpl(d)
                        jobs.append(self._scheduler.add_date_job(self._api.fire_job, \
                        sdate, args=[device]))
                    else:
                        #print("parameters=%s"%parameters)
                        #print("value=%s"%events[d][h])
                        sdate = self._api.tools.date_from_xpl(d)
                        jobs.append(self._scheduler.add_date_job(self._api.fire_job, \
                        sdate, args=[device, parameters, events[d]]))
                self.data[device]['apjobs'] = jobs
                self._job_started(device)
                self._api.log.info("Add a date job %s." % device)
        except:
            self._api.log.warning("_start_job_date : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_SCHEDULER
        if okk:
            return ERROR_NO
        else:
            return ERROR_SCHEDULER

    def _start_job_timer(self, device):
        """
        Start a job of type timer

        timer.basic
           {
            action=start
            device=<name of the timer>
            [devicetype=timer]
            [duration=0 or empty|integer]
            [frequence=integer. 45 by default]
           }

        @param device : the name of the job (=device in xpl)

       """
        try:
            frequence = 45
            if 'frequence' in self.data[device]:
                frequence = int(self.data[device]['frequence'])
            duration = 0
            if 'duration' in self.data[device]:
                duration = int(self.data[device]['duration'])
        except:
            self._api.log.warning("_start_jobTimer : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_PARAMETER
        if duration == 0:
            #we create an infinite timer
            try:
                job = self._scheduler.add_interval_job(self._api.fire_job, \
                    seconds=frequence, args=[device])
                self.data[device]['apjob'] = job
                self._job_started(device)
                self._api.log.info("Add an infinite timer every %s seconds." % frequence)
            except:
                self._api.log.warning("_start_jobTimer : " + \
                    traceback.format_exc())
                #del(self.data[device])
                return ERROR_SCHEDULER
        else:
            try :
                now = datetime.datetime.today()
                delta = datetime.timedelta(seconds=frequence)
                jobs = []
                i = duration
                while i > 0:
                    jobs.append(self._scheduler.add_date_job(\
                        self._api.fire_job, now+i*delta, args=[device]))
                    i = i-1
                self.data[device]['apjobs'] = jobs
                self._job_started(device)
                self._api.log.info("Add a %s beat timer every %s seconds." % (duration, frequence))
            except:
                self._api.log.warning("_start_jobTimer : " + \
                    traceback.format_exc())
                #del(self.data[device])
                return ERROR_SCHEDULER
        return ERROR_NO

    def _start_job_interval(self, device):
        """
        Start a job of type interval

        timer.basic
           {
            action=start
            device=<name of the timer>
            devicetype=interval
            [weeks=0]
            [days=0]
            [hours=0]
            [minutes=0]
            [seconds=0]
            [interval=0]
            [startdate=YYYYMMDDHHMMSS]
           }

        @param device : the name of the job (=device in xpl)

        """
        try:
            okk = False
            weeks = 0
            parameters = self._extract_parameters(device)
            if 'weeks' in self.data[device]:
                weeks = int(self.data[device]['weeks'])
                okk = True
            days = 0
            if 'days' in self.data[device]:
                days = int(self.data[device]['days'])
                okk = True
            hours = 0
            if 'hours' in self.data[device]:
                hours = int(self.data[device]['hours'])
                okk = True
            minutes = 0
            if 'minutes' in self.data[device]:
                minutes = int(self.data[device]['minutes'])
                okk = True
            seconds = 0
            if 'seconds' in self.data[device]:
                seconds = int(self.data[device]['seconds'])
                okk = True
            duration = 0
            if 'duration' in self.data[device]:
                duration = int(self.data[device]['duration'])
            if okk == False:
                self._api.log.warning("_start_jobInterval : \
                    Don't add cron job : no parameters given")
                #del(self.data[device])
                return ERROR_PARAMETER
            startdate = None
            if 'startdate' in self.data[device]:
                startdate = self._api.tools.date_from_xpl(\
                    self.data[device]['startdate'])
        except:
            self._api.log.warning("_start_jobInterval : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_PARAMETER
        try:
            jobs = []
            jobs.append(self._scheduler.add_interval_job(self._api.fire_job, \
                weeks=weeks, days=days, hours=hours, minutes=minutes, \
                seconds=seconds, start_date=startdate, args=[device, parameters, "valueon"]))
            if duration > 0 :
                jobs.append(self._scheduler.add_interval_job(self._api.fire_job, \
                    weeks=weeks, days=days, hours=hours, minutes=minutes, \
                    seconds=seconds+duration, start_date=startdate, args=[device, parameters, "valueoff"]))
            self.data[device]['apjobs'] = jobs
            self._job_started(device)
            self._api.log.info("Add an interval job %s." % device)
        except:
            self._api.log.warning("_start_jobInterval : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_SCHEDULER
        return ERROR_NO

    def _start_job_cron(self, device):
        """
        Start a job of type cron

        timer.basic
           {
            action=start
            device=<name of the timer>
            devicetype=cron
            [year= ... ]
            [month= ... ]
            [day= ... ]
            [week= ... ]
            [dayofweek= ... ]
            [hour= ... ]
            [minute= ... ]
            [second= ... ]
            [startdate=YYYYMMDDHHMMSS]
           }

        @param device : the name of the job (=device in xpl)

        """
        okk = False
        try:
            year = None
            if 'year' in self.data[device]:
                year = self.data[device]['year']
                okk = True
            month = None
            if 'month' in self.data[device]:
                month = self.data[device]['month']
                okk = True
            day = None
            if 'day' in self.data[device]:
                day = self.data[device]['day']
                okk = True
            week = None
            if 'week' in self.data[device]:
                week = self.data[device]['week']
                okk = True
            dayofweek = None
            if 'dayofweek' in self.data[device]:
                dayofweek = self.data[device]['dayofweek']
                okk = True
            hour = None
            if 'hour' in self.data[device]:
                hour = self.data[device]['hour']
                okk = True
            minute = None
            if 'minute' in self.data[device]:
                minute = self.data[device]['minute']
                okk = True
            second = None
            if 'second' in self.data[device]:
                second = self.data[device]['second']
                okk = True
            if okk == False:
                self._api.log.warning("_start_jobCron : Don't add cron job : no parameters given")
                #del(self.data[device])
                return ERROR_PARAMETER
            startdate = None
            if 'startdate' in self.data[device]:
                startdate = self._api.tools.date_from_xpl(\
                    self.data[device]['startdate'])
            #parameters = self._extract_parameters(device)
        except:
            self._api.log.warning("_start_jobCron : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_PARAMETER
        try:
            job = self._scheduler.add_cron_job(self._api.fire_job, \
                year=year, month=month, day=day, week=week, \
                day_of_week=dayofweek, hour=hour, minute=minute, \
                second=second, start_date=startdate, args=[device])
            self.data[device]['apjob'] = job
            self._job_started(device)
            self._api.log.info("Add a cron job %s." % device)
        except:
            self._api.log.warning("_start_jobCron : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_SCHEDULER
        return ERROR_NO

    def _extract_parameters(self, device):
        """
        Extract the parameters from an xpl message

        @param device : the name of the job (=device in xpl)

        """
        res = {}
        okk = True
        if 'nst-command' in self.data[device]:
            okk = False
            if 'nst-value0' in self.data[device] and \
                'nst-value1' in self.data[device]:
                valueon0 = self.data[device]['nst-value0']
                valueoff0 = self.data[device]['nst-value1']
                res[self.data[device]['nst-command']] = {'valueon':valueon0, 'valueoff':valueoff0}
                okk = True
            else:
                okk = False
        if 'parameter0' in self.data[device]:
            parameter0 = self.data[device]['parameter0']
            okk = False
            if 'valueon0' in self.data[device] and \
                'valueoff0' in self.data[device]:
                valueon0 = self.data[device]['valueon0']
                valueoff0 = self.data[device]['valueoff0']
                res[parameter0] = {'valueon':valueon0, 'valueoff':valueoff0}
                okk = True
            else:
                okk = False
        if okk and 'parameter1' in self.data[device]:
            parameter1 = self.data[device]['parameter1']
            okk = False
            if 'valueon1' in self.data[device] and \
                'valueoff1' in self.data[device]:
                valueon1 = self.data[device]['valueon1']
                valueoff1 = self.data[device]['valueoff1']
                res[parameter1] = {'valueon':valueon1, 'valueoff':valueoff1}
                okk = True
            else:
                okk = False
        if okk and 'parameter2' in self.data[device]:
            parameter2 = self.data[device]['parameter2']
            okk = False
            if 'valueon2' in self.data[device] and \
                'valueoff2' in self.data[device]:
                valueon2 = self.data[device]['valueon2']
                valueoff2 = self.data[device]['valueoff2']
                res[parameter2] = {'valueon':valueon2, 'valueoff':valueoff2}
                okk = True
            else:
                okk = False
        #print res
        return res

    def _start_job_hvac(self, device):
        """
        Start a job of type hvac
        This schema reports the state timer settings. It is sent as
        an xPL status message if requested by an hvac.request
        with request=timer, or as a trigger message when a timer
        value is changed.

        The timer elements define the days and times on which the
        hvac system will be active. There can be more than one
        timer= element in the message. This allows different time
        periods to be set for different days of the week (for example,
        additional heating at weekends, when the house may be occupied
        for a greater portion of the day).The timer values provided in
        this message replace any previous timer settings, so the message
        contains all the timer information for the zone.

        The format of the timer value consists of a list of
        two-character codes for the days of the week (each code is
        simply the first two letters of the day) on which the timer
        will be active (with no delimiters), followed by a comma
        separated list of time periods. Each time period is formed
        from a start time and end time separated by a hyphen,
        with each time in the form hh:mm using the 24 hour clock.

        For example, for timers defining a morning and evening period
        during the week, and a daytime period at weekends,
        the message could look something like this:

        hvac.timer
         {
            zone=lounge
            timer=MoTuWeThFr,06:30-09:00,17:00-22:30
            timer=SaSu,08:00-23:00
         }

        If no timers have been set, then the message will contain
        the zone and a single timer= entry with nothing to the right
        of the equals sign.
        @param device : the name of the job (=device in xpl)
        timer.basic
           {
            action=start
            device=<name of the timer>, normally the zone id
            devicetype=hvac
            timer=MoTuWeThFr,06:30-09:00,17:00-22:30
            [timer=SaSu,08:00-23:00]
            [timer=...]
            [valueon1=comfort]
            [valueoff1=economy]
           }
        hvac.timer
           {
            zone=id
            timer=[SuMoTuWeThFrSa,hh:mm-hh:mm,hh:mm-hh:mm,...etc]
            [timer=]
           }

        @param device : the name of the job (=device in xpl)

        """
        okk = True
        try:
            timer = None
            if not 'timer' in self.data[device]:
                okk = False
            parameters = self._extract_parameters(device)
            if okk == False:
                self._api.log.warning("_start_jobHvac : Don't add  hvac job : missing parameters")
                #del(self.data[device])
                return ERROR_PARAMETER
        except:
            self._api.log.warning("_start_jobHvac : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_PARAMETER
        try :
            events = {}
            days = {"Mo":0, "Tu":1, "We":2, "Th":3, "Fr":4, "Sa":5, "Su":6}
            for key in self.data[device]:
                if key.startswith("timer"):
                    timersss = set()
                    if type(self.data[device][key]) == type(""):
                        timersss.add(self.data[device][key])
                    else :
                        timersss = self.data[device][key]
                    for timer in timersss:
                        timer = self.data[device][key]
                        idx = timer.find(",")
                        if idx <= 0:
                            okk = False
                        ds = timer[0:idx]
                        hrs = timer[idx+1:]
                        #print ("ds=%s")%ds
                        #print ("hrs=%s")%hrs
                        cont = True
                        while cont:
                            d = ds[0:2]
                            #print("d=%s"%d)
                            if len(ds) < 2:
                                cont = False
                            elif d not in days:
                                cont = False
                                okk = False
                            else:
                                okk = True
                                if d not in events :
                                    events[d] = {}
                                for hs in hrs.split(","):
                                    #print("hs=%s"%hs)
                                    i = hs.find("-")
                                    deb = hs[0:i]
                                    end = hs[i+1:]
                                    #print("deb=%s"%deb)
                                    #print("end=%s"%end)
                                    if self._api.tools.is_valid_hour(deb):
                                        events[d][deb] = "valueon"
                                    else:
                                        cont = False
                                        okk = False
                                    if self._api.tools.is_valid_hour(end):
                                        events[d][end] = "valueoff"
                                    else:
                                        cont = False
                                        okk = False
                            ds = ds[2:]
                            if len(ds) < 2:
                                cont = False
                            #print("okk=%s"%okk)
            if okk:
                #print("events=%s"%events)
                jobs = []
                for d in events:
                    for h in events[d]:
                        dayofweek = days[d]
                        hour,minute = h.split(":")
                        jobs.append(self._scheduler.add_cron_job(\
                            self._api.fire_job, day_of_week=dayofweek, \
                            hour=hour, minute=minute, \
                            args=[device, parameters, events[d][h]]))
                self.data[device]['apjobs'] = jobs
                self._job_started(device)
                self._api.log.info("Add an hvac job %s." % device)
        except:
            self._api.log.warning("_start_jobHvac : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_SCHEDULER
        if okk:
            return ERROR_NO
        else:
            return ERROR_SCHEDULER

    def _start_job_alarm(self, device):
        """
        Start a job of type alarm

        The format of the timer value consists of a list of
        two-character codes for the days of the week (each code is
        simply the first two letters of the day) on which the timer
        will be active (with no delimiters)
        The second parameter is a simple time or an interval time.
        If the period is an interval, a valueOn message is sent first and
        a valueOff is send at the end of te period
        The time in the form hh:mm using the 24 hour clock.

        For example, for defining one alarm during the week at 6:30 and another
        for the weekend at 8:00 :
        You can also create an alarm to turn on your christmas tree twice a day.
        timer.basic
           {
            action=start
            device=<name of the timer>
            devicetype=alarm
            alarm=MoTuWeThFr,09:30
            alarm=SaSu,08:00
            alarm=SaSu,08:00,18:00
            alarm=MoTuWeThFrSaSu,07:00-08:00,17:00-21:00
         }

        @param device : the name of the job (=device in xpl)

        """
        okk = True
        try:
            #print "data : %s" % self.data[device]
            if 'alarm' not in self.data[device] and 'alarm0' not in self.data[device] :
                okk = False
            parameters = self._extract_parameters(device)
            #print "parameters : %s" % parameters
            if okk == False:
                self._api.log.warning("_start_jobAlarm : Don't add alarm job : missing parameters")
                #del(self.data[device])
                return ERROR_PARAMETER
            events = {}
            days = {"Mo":0, "Tu":1, "We":2, "Th":3, "Fr":4, "Sa":5, "Su":6}
            for key in self.data[device]:
                if key.startswith("alarm"):
                    timersss = set()
                    if type(self.data[device][key]) == type(""):
                        timersss.add(self.data[device][key])
                    else :
                        timersss = self.data[device][key]
                    #Alarm is a list of alarm
                    for timer in timersss:
                        idx = timer.find(",")
                        if idx <= 0:
                            okk = False
                        ds = timer[0:idx]
                        hrs = timer[idx+1:]
                        #print ("ds=%s")%ds
                        #print ("hrs=%s")%hrs
                        cont = True
                        while cont:
                            d = ds[0:2]
                            #print("d=%s"%d)
                            if len(ds)<2:
                                cont = False
                            elif d not in days:
                                cont = False
                                okk = False
                            else:
                                okk = True
                                if d not in events :
                                    events[d] = {}
                                for hs in hrs.split(","):
                                    #print("hs=%s"%hs)
                                    i = hs.find("-")
                                    if i < 0:
                                        #This is a single date
                                        deb = hs
                                        if self._api.tools.is_valid_hour(deb):
                                            events[d][deb] = "single"
                                    else:
                                        #this is an interval period
                                        deb = hs[0:i]
                                        end = hs[i+1:]
                                        #print("deb=%s"%deb)
                                        #print("end=%s"%end)
                                        if self._api.tools.is_valid_hour(deb):
                                            events[d][deb] = "valueon"
                                        else:
                                            cont = False
                                            okk = False
                                        if self._api.tools.is_valid_hour(end):
                                            events[d][end] = "valueoff"
                                        else:
                                            cont = False
                                            okk = False
                            ds = ds[2:]
                            if len(ds) < 2:
                                cont = False
                                #print("okk=%s"%okk)
            if okk:
                #print("events=%s"%events)
                jobs = []
                for d in events:
                    for h in events[d]:
                        dayofweek = days[d]
                        hour,minute = h.split(":")
                        if "single" == events[d][h]:
                            jobs.append(self._scheduler.add_cron_job(\
                            self._api.fire_job, day_of_week=dayofweek, \
                            hour=hour, minute=minute, args=[device]))
                        else:
                            #print("parameters=%s"%parameters)
                            #print("value=%s"%events[d][h])
                            jobs.append(self._scheduler.add_cron_job(\
                                self._api.fire_job, day_of_week=dayofweek, \
                                hour=hour, minute=minute, \
                                args=[device, parameters, events[d][h]]))
                self.data[device]['apjobs'] = jobs
                self._job_started(device)
                self._api.log.info("Add an alarm job %s." % device)
        except:
            self._api.log.warning("_start_jobAlarm : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_SCHEDULER
        if okk:
            return ERROR_NO
        else:
            return ERROR_SCHEDULER

    def _start_job_dawn_alarm(self, device):
        """
        Start a job of type dawnalarm
        A dawnalarm emulates the dawn using a dimmer device.

        The format of the timer value consists of a list of
        two-character codes for the days of the week (each code is
        simply the first two letters of the day) on which the timer
        will be active (with no delimiters)
        The second parameter is an interval time : the begin and the end
        of the dawn process.
        The times are in the form hh:mm using the 24 hour clock.
        The next parameters are the dim level of the device
        (from 00 to 99). If none are specified, we use 10,20,...,90

        For example, for defining one alarm starting at 6:00 and
        finishing at 6:30 with 4 status (10,40,70,90)
        and another for the weekend starting at 7:00 ans finishing at 8:00
        with the standard dim levels :
        timer.basic
           {
            action=start
            device=<name of the timer>
            devicetype=dawnalarm
            alarm=MoTuWeThFr,06:00-06:30,10,40,70,90
            alarm=SaSu,07:00-08:00
         }


        @param device : the name of the job (=device in xpl)

        """
        okk = True
        try:
            if 'alarm' not in self.data[device] and 'alarm0' not in self.data[device] :
                okk = False
            if 'nst-device' not in self.data[device]:
                okk = False
            parameters = self._extract_parameters(device)
            if okk == False:
                self._api.log.warning("_start_jobDawnAlarm : Don't add alarm job : missing parameters")
                #del(self.data[device])
                return ERROR_PARAMETER
            events = {}
            days = {"Mo":0, "Tu":1, "We":2, "Th":3, "Fr":4, "Sa":5, "Su":6}
            for key in self.data[device]:
                if key.startswith("alarm"):
                    timersss = set()
                    if type(self.data[device][key]) == type(""):
                        timersss.add(self.data[device][key])
                    else :
                        timersss = self.data[device][key]
                    #Alarm is a list of alarm
                    for timer in timersss:
                        idx = timer.find(",")
                        if idx <= 0:
                            okk = False
                        ds = timer[0:idx]
                        hrs = timer[idx+1:]
                        #print ("ds=%s")%ds
                        #print ("hrs=%s")%hrs
                        cont = True
                        while cont:
                            d = ds[0:2]
                            #print("d=%s"%d)
                            if len(ds)<2:
                                cont = False
                            elif d not in days:
                                cont = False
                                okk = False
                            else:
                                okk = True
                                if d not in events :
                                    events[d] = {}
                                idx2 = hrs.find(",")
                                if idx2 < 0:
                                    hs = hrs
                                else:
                                    hs = hrs[0:idx2]
                                i = hs.find("-")
                                if i < 0:
                                    cont = False
                                    okk = False
                                else:
                                    #we are in the time part
                                    deb = hs[0:i]
                                    tmp = hs[i+1:]
                                    i2 = tmp.find("-")
                                    if i2 < 0:
                                        end = tmp
                                    else :
                                        end = tmp[0:i2]
                                        off = tmp[i2+1:]
                                    #print("deb=%s"%deb)
                                    #print("end=%s"%end)
                                    #print("off=%s"%off)
                                    if self._api.tools.is_valid_hour(deb):
                                        events[d]["deb"] = deb
                                    else:
                                        cont = False
                                        okk = False
                                    if self._api.tools.is_valid_hour(end):
                                        events[d]["end"] = end
                                    else:
                                        cont = False
                                        okk = False
                                    if i2 >= 0 and self._api.tools.is_valid_hour(off):
                                        events[d]["off"] = off
                                sdims = set()
                                if idx2 < 0:
                                    dims = ""
                                else :
                                    dims = hrs[idx2+1:]
                                    for dim in dims.split(","):
                                        #print("dim=%s"%dim)
                                        #we are in the dim parts
                                        if self._api.tools.is_valid_int(dim):
                                            sdims.add(int(dim))
                                        else:
                                            cont = False
                                            okk = False
                                #print("dims=%s"%dims)
                                if len(sdims) == 0:
                                    sdims = [10, 20, 30, 40, 50, 60, 70, \
                                        80, 90]
                                if okk:
                                    events[d]["dims"] = sdims
                            ds = ds[2:]
                            if len(ds)<2:
                                cont = False
                                #print("okk=%s"%okk)
            #print("okk=%s"%okk)
            if okk:
                #print("events=%s"%events)
                jobs = []
                #print("events=%s"%events)
                for d in events:
                    dayofweek = days[d]
                    delta = self._api.tools.delta_hour(events[d]["end"], \
                        events[d]["deb"])
                    count = len(events[d]["dims"])
                    if count > 1:
                        deltas = delta/(count-1)
                    else:
                        deltas = delta/count
                    i = 0
                    for dim in events[d]["dims"]:
                        param_dim = {"command" : {"valueon":"dim", \
                            "valueoff":"dim"}, \
                            "level" : {"valueon":dim, "valueoff":dim}}
                        #print("dim=%s"%dim)
                        hour, minute = self._api.tools.add_hour(\
                            events[d]["deb"], i*deltas)
                        #param_dim['level']["valueon"] = dim
                        #param_dim['level']["valueoff"] = dim
                        jobs.append(self._scheduler.add_cron_job(\
                            self._api.fire_job, day_of_week=dayofweek, \
                            hour=hour, minute=minute, \
                            args=[device, param_dim, "valueon"]))
                        i = i+1
                    #This is the last message
                    hour, minute = self._api.tools.add_hour(\
                        events[d]["end"], 0)
                    param_dim = {"command" : {"valueon":"dim", \
                        "valueoff":"dim"}, \
                        "level" : {"valueon":100, "valueoff":100}}
                    jobs.append(self._scheduler.add_cron_job(\
                        self._api.fire_job, day_of_week=dayofweek, \
                        hour=hour, minute=minute, \
                        args = [device, param_dim, "valueon"]))
                    if "off" in events[d] :
                    #This is the last message
                        hour, minute = self._api.tools.add_hour(\
                            events[d]["off"], 0)
                        param_dim = {"command" : {"valueon":"dim", \
                            "valueoff":"dim"}, \
                            "level" : {"valueon":0, "valueoff":0}}
                        jobs.append(self._scheduler.add_cron_job(\
                            self._api.fire_job, day_of_week=dayofweek, \
                            hour=hour, minute=minute, \
                            args = [device, param_dim, "valueoff"]))
                self.data[device]['apjobs'] = jobs
                self._job_started(device)
                self._api.log.info("Add a dawn alarm job %s." % device)
        except:
            self._api.log.warning("_start_jobDawnAlarm : " + \
                traceback.format_exc())
            #del(self.data[device])
            return ERROR_SCHEDULER

        if okk:
            return ERROR_NO
        else:
            return ERROR_SCHEDULER

    def add_job(self, device, devicetype, data):
        """
        add a job and start it if needed

        @param device : the name of the job (=device in xpl)
        @param devicetype : the type of job. (date,interval or cron)
        @param message : the incoming xpl message. Contains parameters to configure the job.

        """
        if device in self.data:
            return ERROR_DEVICE_EXIST
        self.data[device] = {'devicetype' : devicetype,
                            }
        if 'runs' not in data:
            data['runs'] = 0
        if 'runtime' not in data:
            data['runtime'] = 0
        if 'createtime' not in data:
            data['createtime'] = datetime.datetime.today().strftime("%x %X")
        if 'sensor_status' not in data:
            data['sensor_status'] = 'low'
        for key in data:
            if not key in self.data[device]:
                self.data[device][key] = data[key]
        self._api.log.debug("add_job : %s" % self.data[device] )
        if ('action' in data and data['action'] == "start") \
          or ('state' in data and data['state'] == "started") \
          or ('current' in data and data['current'] == "started"):
            err = self.start_job(device)
            if (err != ERROR_NO) \
              or (err == ERROR_NO and self.get_ap_count(device) == 0):
                #the job is created but don't want to start
                #we remove it
                self.halt_job(device)
                return ERROR_SCHEDULER
            else:
                return err
        else:
            return ERROR_NO

    def get_state(self, device):
        """
        Get the state of a job

        @param device : the name of the job (=device in xpl)
        @return : The state of the job. None if the job does not exist

        """
        if device in self.data.iterkeys():
            return self.data[device]['state']
        else:
            return ERROR_DEVICE_NOT_EXIST

    def get_run_time(self, device):
        """
        Get the runtime of a job. This is the difference between the datetime
        the device has entered in started state and now

        @param device : the name of the job (=device in xpl)
        @return : The state of the job. None if the job does not exist

        """
        if device in self.data:
            if self.data[device]['state'] == "started":
                if 'starttime' in self.data[device]:
                    start = datetime.datetime.strptime(\
                        self.data[device]['starttime'], "%x %X")
                    elapsed = datetime.datetime.today()-start
                    res = elapsed.days*86400 + elapsed.seconds
                    return res
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def get_full_run_time(self, device):
        """
        Get the runtime of a job. This is the difference between the datetime
        the device has entered in started state and now

        @param device : the name of the job (=device in xpl)
        @return : The state of the job. None if the job does not exist

        """
        oldruntime = int(self.data[device]['runtime'])
        res = self.get_run_time(device) + oldruntime
        return res

    def get_runs(self, device):
        """
        Get the state of a job

        @param device : the name of the job (=device in xpl)
        @return : The state of the job. None if the job does not exist

        """
        if device in self.data:
            return self.data[device]['runs']
        else:
            return 0

    def get_label(self, device, maxlen=0):
        """
        Get the label of a device.

        @param device : the name of the device (=device in xpl)
        @param maxlen : The maxlen of the label. 0 to return full label.
        @return : the uptime in seconds

        """
        ret = ""
        if device in self.data.iterkeys():
            if self.data[device]['devicetype'] == "date":
                alarmsss = set()
                for key in self.data[device] :
                    if key.startswith("date") :
                        if type(self.data[device][key]) == type(""):
                            alarmsss.add(self.data[device][key])
                        else :
                            alarmsss = self.data[device][key]
                        for alarm in alarmsss :
                            if ret == "" :
                                ret = "%s" % (alarm)
                            else:
                                ret = "%s#%s" % (ret,alarm)
            elif self.data[device]['devicetype'] == "timer":
                ret = "f:%s" % (self.data[device]['frequence'])
                if "duration" in self.data[device]:
                    ret = "%s#d:%s" % (ret,self.data[device]['duration'])
            elif self.data[device]['devicetype'] == "interval":
                if 'weeks' in self.data[device]:
                    ret = "w:%s" % (self.data[device]['weeks'])
                if 'days' in self.data[device]:
                    if ret == "" :
                        ret = "d:%s" % (self.data[device]['days'])
                    else:
                        ret = "%s#d:%s" % (ret,self.data[device]['days'])
                if 'hours' in self.data[device]:
                    if ret == "" :
                        ret = "h:%s" % (self.data[device]['hours'])
                    else:
                        ret = "%s#h:%s" % (ret,self.data[device]['hours'])
                if 'minutes' in self.data[device]:
                    if ret == "" :
                        ret = "m:%s" % (self.data[device]['minutes'])
                    else:
                        ret = "%s#m:%s" % (ret,self.data[device]['minutes'])
                if 'seconds' in self.data[device]:
                    if ret == "" :
                        ret = "s:%s" % (self.data[device]['seconds'])
                    else:
                        ret = "%s#s:%s" % (ret,self.data[device]['seconds'])
                if 'duration' in self.data[device]:
                    if ret == "" :
                        ret = "du:%s" % (self.data[device]['duration'])
                    else:
                        ret = "%s#du:%s" % (ret,self.data[device]['duration'])
            elif self.data[device]['devicetype'] == "cron":
                if 'year' in self.data[device]:
                    ret = "y:%s" % (self.data[device]['year'])
                if 'month' in self.data[device]:
                    if ret == "" :
                        ret = "mo:%s" % (self.data[device]['month'])
                    else:
                        ret = "%s#mo:%s" % (ret,self.data[device]['month'])
                if 'day' in self.data[device]:
                    if ret == "" :
                        ret = "d:%s" % (self.data[device]['day'])
                    else:
                        ret = "%s#d:%s" % (ret,self.data[device]['day'])
                if 'week' in self.data[device]:
                    if ret == "" :
                        ret = "w:%s" % (self.data[device]['week'])
                    else:
                        ret = "%s#w:%s" % (ret,self.data[device]['week'])
                if 'dayofweek' in self.data[device]:
                    if ret == "" :
                        ret = "dow:%s" % (self.data[device]['dayofweek'])
                    else:
                        ret = "%s#dow:%s" % (ret,self.data[device]['dayofweek'])
                if 'hour' in self.data[device]:
                    if ret == "" :
                        ret = "h:%s" % (self.data[device]['hour'])
                    else:
                        ret = "%s#h:%s" % (ret,self.data[device]['hour'])
                if 'minute' in self.data[device]:
                    if ret == "" :
                        ret = "m:%s" % (self.data[device]['minute'])
                    else:
                        ret = "%s#m:%s" % (ret,self.data[device]['minute'])
                if 'second' in self.data[device]:
                    if ret == "" :
                        ret = "s:%s" % (self.data[device]['second'])
                    else:
                        ret = "%s#s:%s" % (ret,self.data[device]['second'])
            elif self.data[device]['devicetype'] == "hvac":
                timersss = set()
                for key in self.data[device] :
                    if key.startswith("timer") :
                        if type(self.data[device][key]) == type(""):
                            alarmsss.add(self.data[device][key])
                        else :
                            alarmsss = self.data[device][key]
                        for alarm in alarmsss :
                            if ret == "" :
                                ret = "%s" % (alarm)
                            else:
                                ret = "%s#%s" % (ret,alarm)
            elif self.data[device]['devicetype'] == "alarm":
                alarmsss = set()
                for key in self.data[device] :
                    if key.startswith("alarm") :
                        if type(self.data[device][key]) == type(""):
                            alarmsss.add(self.data[device][key])
                        else :
                            alarmsss = self.data[device][key]
                        for alarm in alarmsss :
                            if ret == "" :
                                ret = "%s" % (alarm)
                            else:
                                ret = "%s#%s" % (ret,alarm)
            elif self.data[device]['devicetype'] == "dawnalarm":
                alarmsss = set()
                for key in self.data[device] :
                    if key.startswith("alarm") :
                        if type(self.data[device][key]) == type(""):
                            alarmsss.add(self.data[device][key])
                        else :
                            alarmsss = self.data[device][key]
                        for alarm in alarmsss :
                            if ret == "" :
                                ret = "%s" % (alarm)
                            else:
                                ret = "%s#%s" % (ret,alarm)
            else:
                ret = "Unknown"
            if maxlen == 0:
                return ret
            else :
                return ret[:maxlen]
        else:
            return None

    def get_up_time(self, device):
        """
        Get the uptime of a device. This is the difference between the datetime
        the device has been created and now

        @param device : the name of the device (=device in xpl)
        @return : the uptime in seconds

        """
        if device in self.data.iterkeys():
            start = datetime.datetime.strptime(self.data[device]['createtime'], "%x %X")
            elapsed = datetime.datetime.today()-start
            res = elapsed.days*86400 + elapsed.seconds
            return res
        else:
            return 0

    def get_device_type(self, device):
        """
        Get the type of a device.

        @param device : the name of the device (=device in xpl)
        @return : the uptime in seconds

        """
        if device in self.data.iterkeys():
            return self.data[device]['devicetype']
        else:
            return 'Unknown'

    def get_list(self, head):
        """
        Get the list of jobs

        @return : The list of jobs

        """
        fmtret = "%-10s | %-8s | %30s | %8s | %8s | %8s | %12s | %13s | %13s"
        fmtretn = "%s|%s|%s|%s|%s|%s|%s|%s|%s"
        lines = []
        if head == True:
            lines.append(fmtret % ("device", "type", "label", "state", "#runs", \
                "#aps", "uptime(in s)", "runtime(in s)", "fullruntime(in s)"))
            lines.append(fmtret % ("----------", "--------", "-------------------------------", "--------", \
                "--------", "--------", "------------", "-------------", "-------------"))
            for i in self.data.iterkeys():
                #print i
                lines.append(fmtret % (i, self.data[i]['state'], self.data[i]['devicetype'], \
                    self.get_label(i, 30), \
                    self.get_runs(i), self.get_ap_count(i), \
                    self.get_up_time(i), self.get_run_time(i), self.get_full_run_time(i)))
        else :
            for i in self.data.iterkeys():
                #print i
                lines.append(fmtretn % (i, self.data[i]['state'], self.data[i]['devicetype'], \
                    self.get_label(i, 30), \
                    self.get_runs(i), self.get_ap_count(i), \
                    self.get_up_time(i), self.get_run_time(i), self.get_full_run_time(i)))

        return lines

    def get_ap_list(self, head):
        """
        Get the list of jobs in APScheduler. For debug purpose

        @param head : Must we show the headers of the columns
        @return : The list of jobs in APScheduler

        """
        fmtret = "%-10s | %8s"
        fmtretn = "%s|%s"
        lines = []
        if head == True:
            lines.append(fmtret % ("name", "runs"))
            lines.append(fmtret % ("----------", "--------"))
            for i in self._scheduler.get_jobs():
                lines.append(fmtret % (str(i.trigger), i.runs))
        else:
            for i in self._scheduler.get_jobs():
                lines.append(fmtretn % (str(i.trigger), i.runs))
        return lines

    def get_ap_count(self, device):
        """
        Get the numbers of jobs
        @return : The numbers of jobs in APScheduler
        """
        if device in self.data.iterkeys():
            if "apjobs" in self.data[device]:
                return len(self.data[device]['apjobs'])
            elif "apjob" in self.data[device]:
                return 1
            else :
                return 0
        else:
            return 0


    def get_xpl_trig(self, device, parameters, value):
        """
        Return the xpl message to send and increase the counter

        @param device : The device to use in the message
        @param parameters : The parameters as a dict
        @param value : the value of parameters to use
        @return : the xpl message

        """
        if device not in self.data.iterkeys():
            return None
        self.data[device]['runs'] = int(self.data[device]['runs'])+1
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        empty = True
        try:
            #print("value=%s"%value)
            if parameters != None:
                #print("parameters=%s"%parameters)
                for key in parameters:
                    #print("key=%s"%key)
                    if value in parameters[key]:
                        #print("key=%s"%parameters[key][value])
                        mess.add_data({key:parameters[key][value]})
                        empty = False
                    else :
                        mess.add_data({"error":key})
            #print "mess = %s" % mess
            for key in self.data[device]:
                if key[0:4].startswith("nst-"):
                    k = key[4:]
                    #print("k=%s"%k)
                    if k.startswith("schema") and self.data[device][key] != "None":
                        mess.set_schema(self.data[device][key])
                        empty = False
                    elif k.startswith("xpltype") and self.data[device][key] != "None":
                        mess.set_type(self.data[device][key])
                        empty = False
                    elif not k.startswith("parameter") and \
                      not k.startswith("valueon") and \
                      not k.startswith("valueoff") and \
                      self.data[device][key] != "None":
                        mess.add_data({k : self.data[device][key]})
                        empty = False
            #print "mess = %s" % mess
            if empty:
#            if "device" not in mess :
                mess.add_data({'device' : device})
            return mess
        except:
            self._api.log.error("get_xpl_trig : " + traceback.format_exc())
            return mess
            #send an xpl error message ...

class CronException(Exception):
    """
    cron exception
    """
    def __init__(self, value):
        """
        cron exception
        """
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        """
        cron exception
        """
        return repr(self.value)

class CronAPI:
    """
    cron API
    """

    def __init__(self, log, config, myxpl, data_dir, stop):
        """
        Constructor

        @param log : the logger
        @param config : the config object to use
        @param myxpl : the xpl sender to use
        @param data_dir : the data_dir where store the files
        @param stop : the stop method

        """
        self.log = log
        self.myxpl = myxpl
        self.config = config
        self.data_files_dir = data_dir
        self._stop = stop
        self.tools = CronTools()
        try:
            self.delay_sensor = int(self.config.query('cron', 'delay-sensor'))
            self.delay_stat = int(self.config.query('cron', 'delay-stat'))
        except:
            self.delay_stat = 300
            self.delay_sensor = 2
            error = "Can't get configuration from XPL : %s" %  \
                     (traceback.format_exc())
            self.log.error("__init__ : " + error)
            self.log.error("Continue with default values.")
        self._jobs_lock = threading.Semaphore()
        try :
            self._jobs_lock.acquire()
            self.jobs = CronJobs(self)
        finally :
            self._jobs_lock.release()
        self.rest_server_ip = "127.0.0.1"
        self.rest_server_port = "40405"
        cfg_rest = Loader('rest')
        config_rest = cfg_rest.load()
        conf_rest = dict(config_rest[1])
        self.rest_server_ip = conf_rest['rest_server_ip']
        self.rest_server_port = conf_rest['rest_server_port']
        self.rest = CronRest(self.rest_server_ip,self.rest_server_port,log)
        self.helpers = CronHelpers(self.log, self.jobs)
        if (self.delay_sensor >0):
            self.timer_stat = Timer(self.delay_sensor, self.send_sensors)
            self.timer_stat.start()

    def fire_job(self, device, parameters=None, value=None):
        """
        Send the XPL Trigger or call rinor to activate device.
        Alarms set by the UI set nst-schema to rinor to do that

        @param myxpl : The XPL sender
        @param device : The timer
        @param parameters : the parameters to use
        @param value : the value

        """
        self.log.debug("cronAPI.fire_job : Start ... %s" % parameters)
        self.log.debug("cronAPI.fire_job : Start ... %s" % value)
        if (self.jobs.data[device]["nst-schema"] == "rinor" ):
            #we should call rinor directly
            #we use the rinor ip and port from ui
            #valueon, valueoff
            #By default, level is in nst-value0
            #but we can overwrite in parameters
            level = self.jobs.data[device]["nst-value0"]
            if parameters != None and \
                "level" in parameters and parameters["level"] != None and \
                "valueon" in parameters["level"] and parameters["level"]["valueon"] != None :
                level = parameters["level"]["valueon"]
            the_url = None
            if (value == None or value == "valueon") :
                 if self.jobs.data[device]["nst-command"]=='':
                    the_url = 'http://%s/command/%s/%s/%s' % (
                        self.jobs.data[device]["rinorip"]+":"+self.jobs.data[device]["rinorport"],
                        self.jobs.data[device]["nst-techno"],
                        self.jobs.data[device]["nst-device"],
                        level)
                 else:
                    the_url = 'http://%s/command/%s/%s/%s/%s' % (
                        self.jobs.data[device]["rinorip"]+":"+self.jobs.data[device]["rinorport"],
                        self.jobs.data[device]["nst-techno"],
                        self.jobs.data[device]["nst-device"],
                        self.jobs.data[device]["nst-command"],
                        level)
            elif (value == "valueoff"):
                 if self.jobs.data[device]["nst-command"]=='':
                    the_url = 'http://%s/command/%s/%s/%s' % (
                        self.jobs.data[device]["rinorip"]+":"+self.jobs.data[device]["rinorport"],
                        self.jobs.data[device]["nst-techno"],
                        self.jobs.data[device]["nst-device"],
                        self.jobs.data[device]["nst-value1"])
                 else:
                    the_url = 'http://%s/command/%s/%s/%s/%s' % (
                        self.jobs.data[device]["rinorip"]+":"+self.jobs.data[device]["rinorport"],
                        self.jobs.data[device]["nst-techno"],
                        self.jobs.data[device]["nst-device"],
                        self.jobs.data[device]["nst-command"],
                        self.jobs.data[device]["nst-value1"])
            if (the_url != None):
                #We change the status of the sensors
                req = urllib2.Request(the_url)
                handle = urllib2.urlopen(req)
                resp1 = handle.read()
                self.jobs.data[device]['runs'] = int(self.jobs.data[device]['runs'])+1
                self._send_sensor_trig(self.myxpl, device, parameters, value)
                self.log.debug("cronAPI.fire_job : rinor called with = %s" % the_url)
            else :
                self.log.debug("cronAPI.fire_job : can't call rinor = %s" % the_url)
        else:
            mess = self.jobs.get_xpl_trig(device, parameters, value)
            if mess != None:
                self.myxpl.send(mess)
                self._send_sensor_trig(self.myxpl, device, parameters, value)
                self.log.debug("cronAPI.fire_job : xplmessage = %s" % mess)
        self.log.debug("cronAPI.fire_job : Done :)")

    def request_listener(self, message):
        """
        Listen to timer.request messages

        timer.request
            {
             device=<name of the timer>
            }
        timer.basic
            {
             device=<name of the timer>
             type=timer|date|interval|cron
             state=halted|resumed|stopped|started
             elapsed=<number of seconds since device created>
             runtime=<number of seconds since device in started state>
             runs=<number of messages sent>
            }

        @param message : The XPL message

        """
        try:
            self.log.debug("cronAPI.requestListener : Start ...")
            device = None
            if 'device' in message.data:
                device = message.data['device']
            mess = XplMessage()
            mess.set_type("xpl-stat")
            mess.set_schema("timer.basic")
            mess.add_data({"device" : device})
            if device in self.jobs.data.iterkeys():
                mess.add_data({"type" : \
                    self.jobs.data[device]['devicetype']})
                mess.add_data({"state" : \
                    self.jobs.data[device]['state']})
                mess.add_data({"elapsed" : self.jobs.get_up_time(device)})
                mess.add_data({"runtime" : self.jobs.get_full_run_time(device)})
                mess.add_data({"runs" : self.jobs.get_runs(device)})
            else:
                mess.add_data({"elasped" :  0})
                mess.add_data({"state" : "halted"})
            self.myxpl.send(mess)
            self.log.debug("cronAPI.requestListener : Done :)")
        except:
            self.log.error("action _ %s _ unknown." % (device))
            error = "Exception : %s" % \
                (traceback.format_exc())
            self.log.debug("cronAPI.requestListener : " + error)

    def basic_listener(self, message):
        """
        Listen to timer.request messages

        timer.basic
           {
            action=halt|resume|stop|start|status
            device=<name of the timer>
            ...
           }

        @param message : The XPL message

        """
        self.log.debug("cronAPI.basicListener : Start ...")
        actions = {
            'halt': lambda x,d,m: self._action_halt(x, d),
            'resume': lambda x,d,m: self._action_resume(x, d),
            'stop': lambda x,d,m: self._action_stop(x, d),
            'start': lambda x,d,m: self._action_start(x, d, m),
            'status': lambda x,d,m: self._action_status(x, d),
            'list': lambda x,d,m: self._action_list(x, d),
        }

        commands = {
            'list': lambda x,d,m: self._command_list(x, d, m),
            'create-alarm': lambda x,d,m: self._command_start_alarm(x, d, m),
            'create-dawnalarm': lambda x,d,m: self._command_start_dawn_alarm(x, d, m),
            'create-date': lambda x,d,m: self._command_start_date(x, d, m),
            'create-interval': lambda x,d,m: self._command_start_interval(x, d, m),
#            'stop': lambda x,d,m: self._action_stop(x, d),
        }

        try:
            action = None
            if 'action' in message.data:
                action = message.data['action']
            command = None
            if 'command' in message.data:
                command = message.data['command']
            device = None
            if 'device' in message.data:
                device = message.data['device']
            caller = None
            if 'caller' in message.data:
                caller = message.data['caller']
            self.log.debug("cronAPI.basicListener : action %s received with device %s" % (action, device))
            self.log.debug("cronAPI.basicListener : command %s received with caller %s" % (command, caller))
            try :
                self.log.debug("cronAPI.basicListener : Try to acquire lock")
                self._jobs_lock.acquire()
                self.log.debug("cronAPI.basicListener : Lock acquired")
                if action != None :
                    self.log.debug("cronAPI.basicListener : Action is not None")
                    actions[action](self.myxpl, device, message)
                elif command != None :
                    self.log.debug("cronAPI.basicListener : Command is not None")
                    commands[command](self.myxpl, device, message)
            except:
                self.log.error("action/command error.")
                error = "Exception : %s" %  \
                         (traceback.format_exc())
                self.log.debug("cronAPI.basicCmndListener : "+error)
            finally :
                self._jobs_lock.release()
        except:
            self.log.error("action _ %s _ unknown." % (action))
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self.log.debug("cronAPI.basicCmndListener : "+error)

    def _action_list(self, myxpl, device):
        """
        Lists the timers
        timer.basic
           {
            action=status
            ...
           }

        @param myxpl : The XPL sender
        @param device : The device to use

        """
        self.log.debug("cronAPI._action_list : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        mess.add_data({"device" : device})
        mess.add_data({"action" : "list"})
        mess.add_data({"devices" : self.jobs.get_list(False)})
        mess.add_data({"apjobs" : self.jobs.get_ap_list(False)})
        myxpl.send(mess)
        self.log.debug("cronAPI._action_list : Done :)")

    def _command_list(self, myxpl, device, message):
        """
        Lists the timers
        timer.basic
           {
            action=status
            ...
           }

        @param myxpl : The XPL sender
        @param device : The device to use
        @param message : The message send by the caller

        """
        self.log.debug("cronAPI._command_list : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        caller = None
        if "caller" in message.data:
            caller = message.data['caller']
        mess.add_data({"caller" : caller})
        mess.add_data({"command" : "list"})
        mess.add_data({"devices" : self.jobs.get_list(False)})
        #mess.add_data({"apjobs" : self.jobs.get_ap_list(False)})
        myxpl.send(mess)
        self.log.debug("cronAPI._command_list : Done :)")

    def _command_start_interval(self, myxpl, device, message):
        """
        Start a job of type interval

        timer.basic
           {
            action=start
            device=<name of the timer>
            devicetype=interval
            [weeks=0]
            [days=0]
            [hours=0]
            [minutes=0]
            [seconds=0]
            [duration=0]
            [startdate=YYYYMMDDHHMMSS]
           }

        @param myxpl : The XPL sender
        @param device : The device to use
        @param message : The message send by the caller

        """
        self.log.debug("cronAPI._command_start_interval: Start ...")
        caller = None
        if 'caller' in message.data:
            caller = message.data['caller']
        data = message.data['data']
        data = data.replace('|','')
        data = "{" + data + "}"
        data = ast.literal_eval(data)
        self.log.debug("cronAPI._command_start_interval : data %s" % data)
        device = None
        if 'device' in data:
            device = data['device']
        devicetype = "interval"
        data['devicetype'] = devicetype
        data['action'] = "start"
        self.log.debug("cronAPI._command_start_interval : data %s" % data)
        ret_cron = self.jobs.add_job(device, devicetype, data)
        if ret_cron == ERROR_NO :
            ret_rest = self.rest.add(self.jobs.data[device], \
              self.jobs.get_label(device))
            if not ret_rest :
                ret_cron = ERROR_REST
        self._send_xpl_trig(myxpl, device, "start", ret_cron, caller)
        self.log.debug("cronAPI._command_start_interval : Done :)")

    def _command_start_date(self, myxpl, device, message):
        """
        Add and start a date alarm. This function is called by the UI

        timer.basic
            {
             device=<name of the timer>
             state=halted|resumed|stopped|started|went off
             elapsed=<number of seconds between start and stop>
            }

        @param myxpl : The XPL sender
        @param device : The device to use
        @param message : The message send by the caller

        """
        self.log.debug("cronAPI._command_start_date: Start ...")
        caller = None
        if 'caller' in message.data:
            caller = message.data['caller']
        data = message.data['data']
        data = data.replace('|','')
        data = "{" + data + "}"
        data = ast.literal_eval(data)
        self.log.debug("cronAPI._command_start_date : data %s" % data)
        device = None
        if 'device' in data:
            device = data['device']
        devicetype = "date"
        data['devicetype'] = devicetype
        data['action'] = "start"
        self.log.debug("cronAPI._command_start_date : data %s" % data)
        ret_cron = self.jobs.add_job(device, devicetype, data)
        if ret_cron == ERROR_NO :
            ret_rest = self.rest.add(self.jobs.data[device], \
              self.jobs.get_label(device))
            if not ret_rest :
                ret_cron = ERROR_REST
        self._send_xpl_trig(myxpl, device, "start", ret_cron, caller)
        self.log.debug("cronAPI._command_start_date : Done :)")

    def _command_start_alarm(self, myxpl, device, message):
        """
        Add and start an alarm. This function is called by the UI

        timer.basic
            {
             device=<name of the timer>
             state=halted|resumed|stopped|started|went off
             elapsed=<number of seconds between start and stop>
            }

        @param myxpl : The XPL sender
        @param device : The device to use
        @param message : The message send by the caller

        """
        self.log.debug("cronAPI._command_start_alarm : Start ...")
        caller = None
        if 'caller' in message.data:
            caller = message.data['caller']
        data = message.data['data']
        data = data.replace('|','')
        self.log.debug("cronAPI._command_start_alarm : data %s" % data)
        data = "{" + data + "}"
        data = ast.literal_eval(data)
        self.log.debug("cronAPI._command_start_alarm : data %s" % data)
        device = None
        if 'device' in data:
            device = data['device']
        devicetype = "alarm"
        data['devicetype'] = devicetype
        data['action'] = "start"
        self.log.debug("cronAPI._command_start_alarm : data %s" % data)
        ret_cron = self.jobs.add_job(device, devicetype, data)
        if ret_cron == ERROR_NO :
            ret_rest = self.rest.add(self.jobs.data[device], \
              self.jobs.get_label(device))
            if not ret_rest :
                ret_cron = ERROR_REST
        self._send_xpl_trig(myxpl, device, "start", ret_cron, caller)
        self.log.debug("cronAPI._command_start_alarm : Done :)")

    def _command_start_dawn_alarm(self, myxpl, device, message):
        """
        Add and start a dawn alarm. This function is called by the UI

        timer.basic
            {
             device=<name of the timer>
             state=halted|resumed|stopped|started|went off
             elapsed=<number of seconds between start and stop>
            }

        @param myxpl : The XPL sender
        @param device : The device to use
        @param message : The message send by the caller

        """
        self.log.debug("cronAPI._command_start_dawnalarm : Start ...")
        caller = None
        if 'caller' in message.data:
            caller = message.data['caller']
        data = message.data['data']
        self.log.debug("cronAPI._command_start_dawnalarm : data %s" % data)
        data = data.replace('|','')
        data = "{" + data + "}"
        data = ast.literal_eval(data)
        self.log.debug("cronAPI._command_start_dawnalarm : data %s" % data)
        device = None
        if 'device' in data:
            device = data['device']
        devicetype = "dawnalarm"
        data['devicetype'] = devicetype
        data['action'] = "start"
        self.log.debug("cronAPI._command_start_dawnalarm : data %s" % data)
        ret_cron = self.jobs.add_job(device, devicetype, data)
        if ret_cron == ERROR_NO :
            ret_rest = self.rest.add(self.jobs.data[device], \
              self.jobs.get_label(device))
            if not ret_rest :
                ret_cron = ERROR_REST
        self._send_xpl_trig(myxpl, device, "start", ret_cron, caller)
        self.log.debug("cronAPI._command_start_dawnalarm : Done :)")

    def _action_status(self, myxpl, device):
        """
        Status of the timers
        timer.basic
           {
            action=status
            ...
           }

        @param myxpl : The XPL sender
        @param device : The device to use

        """
        self.log.debug("cronAPI._actionStatus : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        if device in self.jobs.data.iterkeys():
            mess.add_data({"device" : device})
            mess.add_data({"devicetype" : self.jobs.data[device]['devicetype']})
            mess.add_data({"label" :  self.jobs.get_label(device,30)})
            mess.add_data({"state" :  self.jobs.get_state(device)})
            mess.add_data({"uptime" : self.jobs.get_up_time(device)})
            mess.add_data({"runtime" : self.jobs.get_full_run_time(device)})
            mess.add_data({"runs" : self.jobs.get_runs(device)})
            mess.add_data({"apjobs" : self.jobs.get_ap_count(device)})
        else:
            mess.add_data({"device" : device})
            mess.add_data({"state" : "halted"})
        myxpl.send(mess)
        self.log.debug("cronAPI._actionStatus : Done :)")

    def _action_stop(self, myxpl, device):
        """
        Stop the timer

        @param myxpl : The XPL sender
        @param device : The device to use

        """
        self.log.debug("cronAPI._actionStop : Start ...")
        self._send_xpl_trig(myxpl, device, "stop", \
            self.jobs.stop_job(device))
        self.log.debug("cronAPI._actionStop : Done :)")

    def _action_resume(self, myxpl, device):
        """
        Resume the timer

        @param myxpl : The XPL sender
        @param device : The device to use

        """
        self.log.debug("cronAPI._actionResume : Start ...")
        self._send_xpl_trig(myxpl, device, "resume", \
            self.jobs.resume_job(device))
        self.log.debug("cronAPI._actionResume : Done :)")

    def _action_halt(self, myxpl, device):
        """
        Halt the timer

        @param myxpl : The XPL sender
        @param device : The device to use

        """
        self.log.debug("cronAPI._actionHalt : Start ...")
        if device in self.jobs.data:
            ret_rest = self.rest.delete(self.jobs.data[device])
            ret_cron = self.jobs.halt_job(device)
            #We don't send rest return anymore as some cron jobs don't have a device.
            #if ret_cron == ERROR_NO :
            #    if not ret_rest :
            #        ret_cron = ERROR_REST
        else:
            ret_cron = ERROR_NO
        self._send_xpl_trig(myxpl, device, "halt", ret_cron)
        self.log.debug("Halt job :)")
        self.log.debug("cronAPI._actionHalt : Done :)")

    def _action_start(self, myxpl, device, message):
        """
        Add and start a timer

        timer.basic
            {
             device=<name of the timer>
             state=halted|resumed|stopped|started|went off
             elapsed=<number of seconds between start and stop>
            }

        @param myxpl : The XPL sender
        @param device : The device to use

        """
        self.log.debug("cronAPI._actionAdd : Start ...")

        devicetype = "timer"
        if 'devicetype' in message.data:
            devicetype = message.data['devicetype']
        self._send_xpl_trig(myxpl, device, "start", \
            self.jobs.add_job(device, devicetype, message.data))
        self.log.debug("cronAPI._actionAdd : Done :)")


    def _send_sensor_trig(self, myxpl, device, parameters, value):
        """
        Send the XPL Trigger

        @param myxpl : The XPL sender
        @param device : the device/job
        @param parameters : the parameters
        @param value : the value of the sensor

        """
        #print "_send_sensor_trig value : %s " % value
        if value == None:
            #No value set. We toggle the status of the sensor
            if self.jobs.data[device]["sensor_status"] == "low" :
                self.jobs.data[device]["sensor_status"] = "high"
            else :
                self.jobs.data[device]["sensor_status"] = "low"
#        else :
#            self.jobs.data[device]["sensor_status"] == value
        elif value == "valueon":
            #print "_send_sensor_trig valueon : %s " % value
            self.jobs.data[device]["sensor_status"] = "high"
        elif value == "valueoff":
            #print "_send_sensor_trig valueoff : %s " % value
            self.jobs.data[device]["sensor_status"] = "low"
        self.jobs.store.on_fire(device, \
                self.jobs.data[device]["sensor_status"],
                self.jobs.get_up_time(device), \
                self.jobs.get_full_run_time(device), \
                self.jobs.get_runs(device))
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("sensor.basic")
        mess.add_data({"device" : device})
        mess.add_data({"current" :  self.jobs.data[device]["sensor_status"]})
        myxpl.send(mess)

    def send_sensors(self):
        """
        Send the sensors stat messages

        """
        try :
            self._jobs_lock.acquire()
            for dev in self.jobs.data :
                if self.jobs.data[dev]["state"] == "started":
                    self._send_sensor_stat(self.myxpl,dev)
                    self._stop.wait(self.delay_stat)
        finally :
            self._jobs_lock.release()
            self.timer_stat = Timer(self.delay_sensor, self.send_sensors)
            self.timer_stat.start()

    def _send_sensor_stat(self, myxpl, device):
        """
        Send the XPL stat message

        @param myxpl : The XPL sender
        @param device : the device/job
        @param value : the value of the sensor
        @param type : the type of message (xpl-trig or xpl-stat)

        """
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("sensor.basic")
        mess.add_data({"device" : device})
        mess.add_data({"current" :  self.jobs.data[device]["sensor_status"]})
        myxpl.send(mess)

    def _send_xpl_trig(self, myxpl, device, action, error, caller=None):
        """
        Send the XPL trig message

        timer.basic
            {
             device=<name of the timer>
             state=halted|resumed|stopped|started|went off
             elapsed=<number of seconds since device created>
             runtime=<number of seconds since device in started state>
             runs=<number of messages sent>
             [error=<The message of error>]
             [errorcode=<The code of error>]
            }

        @param myxpl : The XPL sender
        @param device : the device/job
        @param action : the action sent
        @param error : the error code
        @param caller : the caller of the message. Use when sending message from UI

        """
        self.log.debug("cronAPI._send_xpl_trig : Start ...")
        if action == "halt" or (device not in self.jobs.data) :
            state = "halted"
        else :
            state = self.jobs.data[device]['state']
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        if caller != None :
            mess.add_data({"caller" : caller})
        mess.add_data({"device" : device})
        if error == ERROR_NO and state != "halted":
            mess.add_data({"state" :  state})
            mess.add_data({"action" :  action})
            mess.add_data({"elapsed" : self.jobs.get_up_time(device)})
            mess.add_data({"devicetype" : self.jobs.get_device_type(device)})
            mess.add_data({"label" :  self.jobs.get_label(device,30)})
            mess.add_data({"runtime" : self.jobs.get_run_time(device)})
            mess.add_data({"fullruntime" : self.jobs.get_full_run_time(device)})
            mess.add_data({"runs" : self.jobs.get_runs(device)})
            mess.add_data({"apjobs" : self.jobs.get_ap_count(device)})
        else:
            if device in self.jobs.data:
                mess.add_data({"state" : state})
                mess.add_data({"elapsed" : self.jobs.get_up_time(device)})
                mess.add_data({"label" :  self.jobs.get_label(device,30)})
                mess.add_data({"devicetype" : self.jobs.get_device_type(device)})
                mess.add_data({"runtime" : self.jobs.get_run_time(device)})
                mess.add_data({"fullruntime" : self.jobs.get_full_run_time(device)})
                mess.add_data({"runs" : self.jobs.get_runs(device)})
                mess.add_data({"apjobs" : self.jobs.get_ap_count(device)})
            else:
                mess.add_data({"state" : "halted"})
                mess.add_data({"elapsed" : "0"})
                mess.add_data({"runtime" : "0"})
                mess.add_data({"fullruntime" : "0"})
                mess.add_data({"runs" : "0"})
                mess.add_data({"apjobs" : "0"})
            mess.add_data(self.tools.error(error))
            self.log.debug("cronAPI._send_xpl_trig : Send error xpl-trig :(")
        myxpl.send(mess)
        self.log.debug("cronAPI._send_xpl_trig : Done :)")

    def stop_all(self):
        """
        Stop the timer and the running jobs.
        """
        self.log.info("cronAPI.stop_all : close all jobs.")
        self.jobs.close_all()
        self.jobs.stop_scheduler()
        if (self.delay_sensor >0):
            self.timer_stat.cancel()

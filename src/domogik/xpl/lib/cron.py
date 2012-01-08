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
XPL Cron server.

Implements
==========
class cronJobs
class cronException
class cronAPI

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import datetime
import math
from domogik.xpl.common.xplmessage import XplMessage
from apscheduler.scheduler import Scheduler
from apscheduler.job import Job
from apscheduler.jobstores.shelve_store import ShelveJobStore
import traceback
import logging
logging.basicConfig()

ERROR_NO=0
ERROR_PARAMETER=1
ERROR_DEVICE_EXIST=10
ERROR_DEVICE_NOT_EXIST=11
ERROR_DEVICE_NOT_STARTED=12
ERROR_DEVICE_NOT_STOPPED=13
ERROR_SCHEDULER=20
ERROR_NOT_IMPLEMENTED=30

cronErrors = { ERROR_NO: 'No error',
               ERROR_PARAMETER: 'Missing or wrong parameter',
               ERROR_DEVICE_EXIST: 'Device already exist',
               ERROR_DEVICE_NOT_EXIST: 'Device does not exist',
               ERROR_DEVICE_NOT_STARTED: "Device is not started",
               ERROR_DEVICE_NOT_STOPPED: "Device is not stopped",
               ERROR_SCHEDULER: 'Error with the scheduler',
               }

class cronJobs():

    def __init__(self,api):
        self.data = dict()
        # Start the scheduler
        self._api = api
        self._scheduler = Scheduler()
#        self._storage=None
#        self._storage = self._api.config.query('cron', 'storage')
#        if self._storage!=None:
#            self._scheduler.add_jobstore(ShelveJobStore(self._storage), 'file')
#        else:
#            raise cronException(error)
        self._scheduler.start()

    def __del__(self):
        self._scheduler.shutdown()

    def stopAPJob(self, device):
        """
        stop the APScheduler jobs of a device
        @param device : the name of the job (=device in xpl)
        """
        if device in self.data:
            if 'apjob' in self.data[device]:
                try:
                    self._scheduler.unschedule_job(self.data[device]['apjob'])
                except:
                    print "Can't unschedule AP job %s"%self.data[device]['apjob']
                del(self.data[device]['apjob'])
            if 'apjobs' in self.data[device]:
                while len(self.data[device]['apjobs'])>0:
                    i=self.data[device]['apjobs'].pop()
                    try:
                        self._scheduler.unschedule_job(i)
                    except:
                        print "Can't unschedule AP job %s"%i
                del (self.data[device]['apjobs'])
            return ERROR_NO
        else:
            return ERROR_DEVICE_NOT_EXIST

    def stopJob(self, device):
        """
        stop a job
        @param device : the name of the job (=device in xpl)
        """
        if device in self.data:
            self.stopAPJob(device)
            self.data[device]['current']="stopped"
            return ERROR_NO
        else:
            return ERROR_DEVICE_NOT_EXIST

    def haltJob(self, device):
        """
        Stop and remove a job
        @param device : the name of the job (=device in xpl)
        """
        if device in self.data:
            self.stopJob(device)
            del(self.data[device])
            return ERROR_NO
        else:
            return ERROR_DEVICE_NOT_EXIST

    def resumeJob(self, device):
        """
        Resume a job
        @param device : the name of the job (=device in xpl)
        """
        if device in self.data:
            if self.getState(device)=="stopped":
                return self.startJob(device)
            else:
                return ERROR_DEVICE_NOT_STOPPED
        else:
            return ERROR_DEVICE_NOT_EXIST

    def startJob(self, device):
        """
        start a job
        @param device : the name of the job (=device in xpl)
        """
        devicetypes = {
            'date': lambda d: self._startJobDate(d),
            'timer': lambda d: self._startJobTimer(d),
            'interval': lambda d: self._startJobInterval(d),
            'cron': lambda d: self._startJobCron(d),
            'hvac': lambda d: self._startJobHvac(d),
            'alarm': lambda d: self._startJobAlarm(d),
            'dawnalarm': lambda d: self._startJobDawnAlarm(d),
        }
        if device in self.data:
            devicetype=self.data[device]['devicetype']
            return devicetypes[devicetype](device)
        else:
            return ERROR_DEVICE_NOT_EXIST

    def _startJobDate(self, device):
        """
        Start a job of type date
        @param device : the name of the job (=device in xpl)
        timer.basic
           {
            action=start
            device=<name of the timer>
            devicetype=date
            date= the datetime of the job (YYYYMMDDHHMMSS)
           }
        """
        try:
            xpldate = None
            if 'date' in self.data[device]:
                xpldate = self.data[device]['date']
            sdate = self.dateFromXPL(xpldate)
        except:
            self._api.log.error("cronJobs._startJobDate : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_PARAMETER
        if xpldate != None:
            try:
                job = self._scheduler.add_date_job(self._api.sendXplJob, sdate, args=[device])
                self.data[device]['current']="started"
                self.data[device]['apjob']=job
                self.data[device]['starttime']=datetime.datetime.today()
                self._api.log.info("cronJobs._startJobDate : add job at date %s"%xpldate)
            except:
                self._api.log.error("cronJobs._startJobDate : "+traceback.format_exc())
                del(self.data[device])
                return ERROR_SCHEDULER
            return ERROR_NO
        else:
            self._api.log.error("cronJobs._startJobDate : Don't add cron job : no parameters given")
            del(self.data[device])
            return ERROR_PARAMETER

    def _startJobTimer(self, device):
        """
        Start a job of type timer
        @param device : the name of the job (=device in xpl)
        timer.basic
           {
            action=start
            device=<name of the timer>
            [devicetype=timer]
            [duration=0 or empty|integer]
            [frequence=integer. 45 by default]
           }
       """
        try:
            frequence = 45
            if 'frequence' in self.data[device]:
                frequence = int(self.data[device]['frequence'])
            duration = 0
            if 'duration' in self.data[device]:
                duration = int(self.data[device]['duration'])
        except:
            self._api.log.error("cronJobs._startJobTimer : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_PARAMETER
        if duration==0:
            #we create an infinite timer
            try:
                job = self._scheduler.add_interval_job(self._api.sendXplJob,seconds=frequence, args=[device])
                self.data[device]['current']="started"
                self.data[device]['apjob']=job
                self.data[device]['starttime']=datetime.datetime.today()
                self._api.log.info("cronJobs._startJobTimer : add an infinite timer every %s seconds"%frequence)
            except:
                self._api.log.error("cronJobs._startJobTimer : "+traceback.format_exc())
                del(self.data[device])
                return ERROR_SCHEDULER
        else:
            try :
                now=datetime.datetime.today()
                delta=datetime.timedelta(seconds=frequence)
                jobs=[]
                i=duration
                while i>0:
                    jobs.append(self._scheduler.add_date_job(self._api.sendXplJob, now+i*delta, args=[device]))
                    i=i-1
                self.data[device]['current']="started"
                self.data[device]['apjobs']=jobs
                self.data[device]['starttime']=datetime.datetime.today()
                self._api.log.info("cronJobs._startJobTimer : add a %s beats timer every %s seconds"%(duration,frequence))
            except:
                self._api.log.error("cronJobs._startJobTimer : "+traceback.format_exc())
                del(self.data[device])
                return ERROR_SCHEDULER
        return ERROR_NO

    def _startJobInterval(self, device):
        """
        Start a job of type interval
        @param device : the name of the job (=device in xpl)
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
            [startdate=YYYYMMDDHHMMSS]
           }
        """
        try:
            ok=False
            weeks = 0
            if 'weeks' in self.data[device]:
                weeks = int(self.data[device]['weeks'])
                ok=True
            days = 0
            if 'days' in self.data[device]:
                days = int(self.data[device]['days'])
                ok=True
            hours = 0
            if 'hours' in self.data[device]:
                hours = int(self.data[device]['hours'])
                ok=True
            minutes = 0
            if 'minutes' in self.data[device]:
                minutes = int(self.data[device]['minutes'])
                ok=True
            seconds = 0
            if 'seconds' in self.data[device]:
                seconds = int(self.data[device]['seconds'])
                ok=True
            if ok==False:
                self._api.log.error("cronJobs._startJobInterval : Don't add cron job : no parameters given")
                del(self.data[device])
                return ERROR_PARAMETER
            startdate = None
            if 'startdate' in self.data[device]:
                startdate = self.dateFromXPL(self.data[device]['startdate'])
            #parameters = self._extractParameters(device)
        except:
            self._api.log.error("cronJobs._startJobInterval : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_PARAMETER
        try:
            job = self._scheduler.add_interval_job(self._api.sendXplJob,weeks=weeks,
                  days=days,hours=hours,minutes=minutes,seconds=seconds,
                  start_date=startdate, args=[device])
            self.data[device]['current']="started"
            self.data[device]['starttime']=datetime.datetime.today()
            self.data[device]['apjob']=job
            self._api.log.info("cronJobs._startJobInterval : add an interval job %s" % str(job))
        except:
            self._api.log.error("cronJobs._startJobInterval : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_SCHEDULER
        return ERROR_NO

    def _startJobCron(self, device):
        """
        Start a job of type cron
        @param device : the name of the job (=device in xpl)
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
        """
        ok=False
        try:
            year = None
            if 'year' in self.data[device]:
                year = self.data[device]['year']
                ok=True
            month = None
            if 'month' in self.data[device]:
                month = self.data[device]['month']
                ok=True
            day = None
            if 'day' in self.data[device]:
                day = self.data[device]['day']
                ok=True
            week = None
            if 'week' in self.data[device]:
                week = self.data[device]['week']
                ok=True
            dayofweek = None
            if 'dayofweek' in self.data[device]:
                dayofweek = self.data[device]['dayofweek']
                ok=True
            hour = None
            if 'hour' in self.data[device]:
                hour = self.data[device]['hour']
                ok=True
            minute = None
            if 'minute' in self.data[device]:
                minute = self.data[device]['minute']
                ok=True
            second = None
            if 'second' in self.data[device]:
                second = self.data[device]['second']
                ok=True
            if ok==False:
                self._api.log.error("cronJobs._startJobCron : Don't add cron job : no parameters given")
                del(self.data[device])
                return ERROR_PARAMETER
            startdate = None
            if 'startdate' in self.data[device]:
                startdate = self.dateFromXPL(self.data[device]['startdate'])
            #parameters = self._extractParameters(device)
        except:
            self._api.log.error("cronJobs._startJobCron : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_PARAMETER
        try:
            job = self._scheduler.add_cron_job(self._api.sendXplJob,year=year,
                  month=month,day=day,week=week,day_of_week=dayofweek,hour=hour,
                  minute=minute,second=second,start_date=startdate, args=[device])
            self.data[device]['current']="started"
            self.data[device]['starttime']=datetime.datetime.today()
            self.data[device]['apjob']=job
            self._api.log.info("cronJobs._startJobCron : add a cron job %s" % str(job))
        except:
            self._api.log.error("cronJobs._startJobCron : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_SCHEDULER
        return ERROR_NO

    def isValidHour(self,hour):
        #print hour[0:2]
        #print hour[3:5]
        try:
            t=datetime.time(int(hour[0:2]),int(hour[3:5]))
        except :
            #print "error in %s"%hour
            return False
        return True

    def isValidInt(self,number):
        #print hour[0:2]
        #print hour[3:5]
        try:
            t=int(number)
        except :
            #print "error in %s"%hour
            return False
        return True


    def _extractParameters(self,device):
        res={}
        ok=True
        if 'parameter0' in self.data[device]:
            parameter0 = self.data[device]['parameter0']
            ok=False
            if 'valueon0' in self.data[device] and 'valueoff0' in self.data[device]:
                valueon0 = self.data[device]['valueon0']
                valueoff0 = self.data[device]['valueoff0']
                res[parameter0]={'valueon':valueon0,'valueoff':valueoff0}
                ok=True
            else:
                ok=False
        if ok and 'parameter1' in self.data[device]:
            parameter1 = self.data[device]['parameter1']
            ok=False
            if 'valueon1' in self.data[device] and 'valueoff1' in self.data[device]:
                valueon1 = self.data[device]['valueon1']
                valueoff1 = self.data[device]['valueoff1']
                res[parameter1]={'valueon':valueon1,'valueoff':valueoff1}
                ok=True
            else:
                ok=False
        #print res
        return res

    def _startJobHvac(self, device):
        """
        Start a job of type hvac
        This schema reports the current timer settings. It is sent as
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
        """
        ok=True
        try:
            timer = None
            if not 'timer' in self.data[device]:
                ok=False
            parameters = self._extractParameters(device)
            if ok==False:
                self._api.log.error("cronJobs._startJobHvac : Don't add hvac job : missing parameters")
                del(self.data[device])
                return ERROR_PARAMETER
        except:
            self._api.log.error("cronJobs._startJobHvac : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_PARAMETER
        try :
            ok=True
            events={}
            days={"Mo":0,"Tu":1,"We":2,"Th":3,"Fr":4,"Sa":5,"Su":6}
            for key in self.data[device]:
                if key.startswith("timer"):
                    timersss=set()
                    if type(self.data[device][key])==type(""):
                        timersss.add(self.data[device][key])
                    else :
                        timersss=self.data[device][key]
                    for timer in timersss:
                        timer=self.data[device][key]
                        idx=timer.find(",")
                        if idx<=0:
                            ok=False
                        ds=timer[0:idx]
                        hrs=timer[idx+1:]
                        #print ("ds=%s")%ds
                        #print ("hrs=%s")%hrs
                        cont=True
                        while cont:
                            d=ds[0:2]
                            #print "d=%s"%d
                            if len(ds)<2:
                                cont=False
                            elif d not in days:
                                cont=False
                                ok=False
                            else:
                                events[d]={}
                                for hs in hrs.split(","):
                                    #print "hs=%s"%hs
                                    i=hs.find("-")
                                    deb=hs[0:i]
                                    end=hs[i+1:]
                                    #print "deb=%s"%deb
                                    #print "end=%s"%end
                                    if self.isValidHour(deb):
                                        events[d][deb]="valueon"
                                    else:
                                        cont=False
                                        ok=False
                                    if self.isValidHour(end):
                                        events[d][end]="valueoff"
                                    else:
                                        cont=False
                                        ok=False
                            ds=ds[2:]
                            if len(ds)<2:
                                cont=False
                            #print "ok=%s"%ok
            if ok:
                #print "events=%s"%events
                jobs=[]
                for d in events:
                    for h in events[d]:
                        dayofweek=days[d]
                        hour=int(h[0:2])
                        minute=int(h[3:5])
                        jobs.append(self._scheduler.add_cron_job(self._api.sendXplJob,day_of_week=dayofweek,hour=hour,minute=minute,args=[device,parameters,events[d][h]]))
                self.data[device]['current']="started"
                self.data[device]['apjobs']=jobs
                self.data[device]['starttime']=datetime.datetime.today()
                self._api.log.info("cronJobs._startJobHvac : add a hvac job %s" % str(jobs))
        except:
            self._api.log.error("cronJobs._startJobHvac : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_SCHEDULER
        if ok:
            return ERROR_NO
        else:
            return ERROR_SCHEDULER

    def _startJobAlarm(self, device):
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

        """
        ok=True
        try:
            alarm = None
            if 'alarm' in self.data[device]:
                alarm = self.data[device]['alarm']
                #print "timer=%s"%timer
            else:
                ok=False
            parameters = self._extractParameters(device)
            if ok==False:
                self._api.log.error("cronJobs._startJobAlarm : Don't add alarm job : missing parameters")
                del(self.data[device])
                return ERROR_PARAMETER
            ok=True
            events={}
            days={"Mo":0,"Tu":1,"We":2,"Th":3,"Fr":4,"Sa":5,"Su":6}
            for key in self.data[device]:
                if key.startswith("alarm"):
                    timersss=set()
                    if type(self.data[device][key])==type(""):
                        timersss.add(self.data[device][key])
                    else :
                        timersss=self.data[device][key]
                    #Alarm is a list of alarm
                    for timer in timersss:
                        idx=timer.find(",")
                        if idx<=0:
                            ok=False
                        ds=timer[0:idx]
                        hrs=timer[idx+1:]
                        #print ("ds=%s")%ds
                        #print ("hrs=%s")%hrs
                        cont=True
                        while cont:
                            d=ds[0:2]
                            #print "d=%s"%d
                            if len(ds)<2:
                                cont=False
                            elif d not in days:
                                cont=False
                                ok=False
                            else:
                                events[d]={}
                                for hs in hrs.split(","):
                                    #print "hs=%s"%hs
                                    i=hs.find("-")
                                    if i<0:
                                        #This is a single date
                                        deb=hs
                                        if self.isValidHour(deb):
                                            events[d][deb]="single"
                                    else:
                                        #this is an interval period
                                        deb=hs[0:i]
                                        end=hs[i+1:]
                                        #print "deb=%s"%deb
                                        #print "end=%s"%end
                                        if self.isValidHour(deb):
                                            events[d][deb]="valueon"
                                        else:
                                            cont=False
                                            ok=False
                                        if self.isValidHour(end):
                                            events[d][end]="valueoff"
                                        else:
                                            cont=False
                                            ok=False
                            ds=ds[2:]
                            if len(ds)<2:
                                cont=False
                                #print "ok=%s"%ok
            if ok:
                #print "events=%s"%events
                jobs=[]
                for d in events:
                    for h in events[d]:
                        dayofweek=days[d]
                        hour=int(h[0:2])
                        minute=int(h[3:5])
                        if "single"==events[d][h]:
                            jobs.append(self._scheduler.add_cron_job(self._api.sendXplJob,day_of_week=dayofweek,hour=hour,minute=minute,args=[device]))
                        else:
                            #print "parameters=%s"%parameters
                            #print "value=%s"%events[d][h]
                            jobs.append(self._scheduler.add_cron_job(self._api.sendXplJob,day_of_week=dayofweek,hour=hour,minute=minute,args=[device,parameters,events[d][h]]))
                self.data[device]['current']="started"
                self.data[device]['apjobs']=jobs
                self.data[device]['starttime']=datetime.datetime.today()
                self._api.log.info("cronJobs._startJobAlarm : add a alarm job %s" % str(jobs))
        except:
            self._api.log.error("cronJobs._startJobAlarm : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_SCHEDULER

        if ok:
            return ERROR_NO
        else:
            return ERROR_SCHEDULER

    def _deltaHour(self,h1,h2):
        dummy_date = datetime.date(1, 1, 1)
        full_h1 = datetime.datetime.combine(dummy_date, datetime.time(int(h1[0:2]),int(h1[3:5])))
        full_h2 = datetime.datetime.combine(dummy_date, datetime.time(int(h2[0:2]),int(h2[3:5])))
        elapsed=full_h1-full_h2
        res=elapsed.days*86400+elapsed.seconds+elapsed.microseconds / 1000000.0
        return res

    def _addHour(self,h,s):
        dummy_date = datetime.date(1, 1, 1)
        full_h = datetime.datetime.combine(dummy_date, datetime.time(int(h[0:2]),int(h[3:5])))
        res=full_h+datetime.timedelta(seconds=s)
        return res.hour,res.minute

    def _startJobDawnAlarm(self, device):
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

        """
        ok=True
        try:
            alarm = None
            if 'alarm' in self.data[device]:
                alarm = self.data[device]['alarm']
            else:
                ok=False
            nstdevice = None
            if 'nst-device' in self.data[device]:
                nstdevice = self.data[device]['nst-device']
            else:
                ok=False
            parameters = self._extractParameters(device)
            if ok==False:
                self._api.log.error("cronJobs._startJobDawnAlarm : Don't add alarm job : missing parameters")
                del(self.data[device])
                return ERROR_PARAMETER
            ok=True
            events={}
            days={"Mo":0,"Tu":1,"We":2,"Th":3,"Fr":4,"Sa":5,"Su":6}
            for key in self.data[device]:
                if key.startswith("alarm"):
                    timersss=set()
                    if type(self.data[device][key])==type(""):
                        timersss.add(self.data[device][key])
                    else :
                        timersss=self.data[device][key]
                    #Alarm is a list of alarm
                    for timer in timersss:
                        idx=timer.find(",")
                        if idx<=0:
                            ok=False
                        ds=timer[0:idx]
                        hrs=timer[idx+1:]
                        #print ("ds=%s")%ds
                        #print ("hrs=%s")%hrs
                        cont=True
                        while cont:
                            d=ds[0:2]
                            #print "d=%s"%d
                            if len(ds)<2:
                                cont=False
                            elif d not in days:
                                cont=False
                                ok=False
                            else:
                                events[d]={}
                                idx2=hrs.find(",")
                                if idx2<0:
                                    hs=hrs
                                else:
                                    hs=hrs[0:idx2]
                                i=hs.find("-")
                                if i<0:
                                    cont=False
                                    ok=False
                                else:
                                    #we are in the time part
                                    deb=hs[0:i]
                                    end=hs[i+1:]
                                    #print "deb=%s"%deb
                                    #print "end=%s"%end
                                    if self.isValidHour(deb):
                                        events[d]["deb"]=deb
                                    else:
                                        cont=False
                                        ok=False
                                    if self.isValidHour(end):
                                        events[d]["end"]=end
                                    else:
                                        cont=False
                                        ok=False
                                sdims=set()
                                if idx2<0:
                                    dims=""
                                else :
                                    dims = hrs[idx2+1:]
                                    for dim in dims.split(","):
                                        #print "dim=%s"%dim
                                        #we are in the dim parts
                                        if self.isValidInt(dim):
                                            sdims.add(int(dim))
                                        else:
                                            cont=False
                                            ok=False
                                #print "dims=%s"%dims
                                if len(sdims)==0:
                                    sdims=[10,20,30,40,50,60,70,80,90]
                                if ok:
                                    events[d]["dims"]=sdims
                            ds=ds[2:]
                            if len(ds)<2:
                                cont=False
                                #print "ok=%s"%ok
            #print "ok=%s"%ok
            if ok:
                #print "events=%s"%events
                jobs=[]
                #print "events=%s"%events
                for d in events:
                    dayofweek=days[d]
                    delta=self._deltaHour(events[d]["end"],events[d]["deb"])
                    count=len(events[d]["dims"])
                    if count>1:
                        deltas=delta/(count-1)
                    else:
                        deltas=delta/count
                    i=0
                    for dim in events[d]["dims"]:
                        param_dim={"command" : {"valueon":"dim","valueoff":"dim"},
                           "level" : {"valueon":d,"valueoff":dim}}
                        #print "dim=%s"%dim
                        hour,minute=self._addHour(events[d]["deb"],i*deltas)
                        param_dim['level']["valueon"]=dim
                        param_dim['level']["valueoff"]=dim
                        if i==count-1:
                            #This is the last message
                            hour,minute=self._addHour(events[d]["end"],0)
                            jobs.append(self._scheduler.add_cron_job(self._api.sendXplJob,day_of_week=dayofweek,hour=hour,minute=minute,args=[device,param_dim,"valueon"]))
                        else:
                            jobs.append(self._scheduler.add_cron_job(self._api.sendXplJob,day_of_week=dayofweek,hour=hour,minute=minute,args=[device,param_dim,"valueon"]))
                        i=i+1
                    #hour,minute=self._addHour(events[d]["end"],0)
                    #param_on={"command" : {"valueon":"on","valueoff":"on"}}
                    #jobs.append(self._scheduler.add_cron_job(self._api.sendXplJob,day_of_week=dayofweek,hour=hour,minute=minute,args=[device,param_on,"valueon"]))
                self.data[device]['current']="started"
                self.data[device]['apjobs']=jobs
                self.data[device]['starttime']=datetime.datetime.today()
                self._api.log.info("cronJobs._startJobDawnAlarm : add a dawnalarm job %s" % str(jobs))
        except:
            self._api.log.error("cronJobs._startJobDawnAlarm : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_SCHEDULER

        if ok:
            return ERROR_NO
        else:
            return ERROR_SCHEDULER

    def addJob(self, device, devicetype, message):
        """
        add a job
        @param device : the name of the job (=device in xpl)
        @param devicetype : the type of job. (date,interval or cron)
        @param message : the inxoming xpl message
        """
        if device in self.data.iterkeys():
            return ERROR_DEVICE_EXIST
        self.data[device] = {'devicetype' : devicetype,
                            'createtime' : datetime.datetime.today(),
                            'runs' : 0,
                            }
        for key in message.data:
            if not key in self.data[device]:
                self.data[device][key]=message.data[key]
        return self.startJob(device)

    def getState(self, device):
        """
        Get the state of a job
        @param device : the name of the job (=device in xpl)
        @return : The state of the job. None if the job does not exist
        """
        if device in self.data.iterkeys():
            return self.data[device]['current']
        else:
            return ERROR_DEVICE_NOT_EXIST

    def getRunTime(self, device):
        """
        Get the runtime of a job. This is the difference between the datetime
        the device has entered in started state and now
        @param device : the name of the job (=device in xpl)
        @return : The state of the job. None if the job does not exist
        """
        if device in self.data.iterkeys():
            if self.data[device]['current']=="started":
                start=self.data[device]['starttime']
                elapsed=datetime.datetime.today()-start
                res=elapsed.days*86400+elapsed.seconds+elapsed.microseconds / 1000000.0
                return res
            else:
                return 0
        else:
            return 0

    def getRunTimes(self, device):
        """
        Get the state of a job
        @param device : the name of the job (=device in xpl)
        @return : The state of the job. None if the job does not exist
        """
        if device in self.data.iterkeys():
            return self.data[device]['runs']
        else:
            return 0

    def getUpTime(self, device):
        """
        Get the uptime of a device. This is the difference between the datetime
        the device has been created and now
        @param device : the name of the device (=device in xpl)
        @return : the uptime in seconds
        """
        if device in self.data.iterkeys():
            start=self.data[device]['createtime']
            elapsed=datetime.datetime.today()-start
            res=elapsed.days*86400+elapsed.seconds+elapsed.microseconds / 1000000.0
            return res
        else:
            return 0

    def getList(self,head):
        """
        Get the list of jobs
        @return : The list of jobs
        """
        fmtret="%-10s | %-8s | %8s | %8s | %12s"
        lines = []
        if head==True:
            lines.append(fmtret % ("device","status","#runs", "#aps","uptime(in s)"))
            lines.append(fmtret % ("----------","--------","--------", "--------","------------"))
        for i in self.data.iterkeys():
            #print i
            lines.append(fmtret % (i,self.data[i]['current'],self.getRunTimes(i),self.getAPCount(i),self.getUpTime(i)))
        return lines

    def getAPList(self,head):
        """
        Get the list of jobs
        @return : The list of jobs in APScheduler
        """
        fmtret="%-10s | %8s"
        lines = []
        if head==True:
            lines.append(fmtret % ("name","runs"))
            lines.append(fmtret % ("----------","--------"))
        for i in self._scheduler.get_jobs():
            lines.append(fmtret % (str(i.trigger), i.runs))
        return lines

    def getAPCount(self,device):
        """
        Get the numbers of jobs
        @return : The numbers of jobs in APScheduler
        """
        if "apjobs" in self.data[device]:
            return len(self.data[device]['apjobs'])
        elif "apjob" in self.data[device]:
            return 1
        else :
            return 0

    def dateFromXPL(self,xpldate):
        """
        Tranform an XPL date "yyyymmddhhmmss" to datetime
        form
        """
        y = int(xpldate[0:4])
        mo = int(xpldate[4:6])
        d = int(xpldate[6:8])
        h = int(xpldate[8:10])
        m = int(xpldate[10:12])
        s = int(xpldate[12:14])
        return datetime.datetime(y,mo,d,h,m,s)

    def dateToXPL(self,sdate):
        """
        Tranform an datetime date to an xpl one "yyyymmddhhmmss"
        form
        """
        h = "%.2i" % sdate.hour
        m = "%.2i" % sdate.minute
        s = "%.2i" % sdate.second
        y = sdate.year
        mo = "%.2i" % sdate.month
        d = "%.2i" % sdate.day
        xpldate = "%s%s%s%s%s%s" % (y, mo, d, h, m, s)
        return xpldate

    def getXplTrig(self,device,parameters,value):
        """
        Return the xpl message to send and increase the counter
        """
        if device not in self.data.iterkeys():
            return None
        self.data[device]['runs']=self.data[device]['runs']+1
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        empty=True
        try:
            #print "value=%s"%value
            if parameters!=None:
                #print "parameters=%s"%parameters
                for key in parameters:
                    #print "key=%s"%key
                    if value in parameters[key]:
                        #print "key=%s"%parameters[key][value]
                        mess.add_data({key:parameters[key][value]})
                        empty=False
                    else :
                        mess.add_data({"error":key})
            for key in self.data[device]:
                if key[0:4].startswith("nst-"):
                    k=key[4:]
                    #print "k=%s"%k
                    if k.startswith("schema"):
                       mess.set_schema(self.data[device][key])
                       empty=False
                    elif k.startswith("xpltype"):
                       mess.set_type(self.data[device][key])
                       empty=False
                    elif not k.startswith("parameter") and not k.startswith("valueon") and not k.startswith("valueoff"):
                       mess.add_data({k : self.data[device][key]})
                       empty=False
            if empty:
                mess.add_data({'device' : device})
            return mess
        except:
            return mess
            #send an xpl error message ...

    def helperList(self, params={}):
        """
        List all devices
        """
        self._api.log.error("cronJobs.helperList : Start ...")
        data = []
        if "which" in params:
            if params["which"]=="all":
                data.append("List all devices :")
                data.extend(self.getList(True))
            elif params["which"]=="aps":
                data.extend(self.getAPList(True))
            else:
                data.append("Bad parameter")
        else:
            data.append("No ""which"" parameter found")
        self._api.log.error("cronJobs.helperList : Done")
        return data

    def helperInfo(self, params={}):
        """
        Return informations on a device
        """
        self._api.log.error("cronJobs.helperList : Start ...")
        data = []
        if "device" in params:
            device=params["device"]
            data.append("Informations on device %s :"%device)
            if device in self.data:
                data.append(" Current state : %s"%(self.data[device]['current']))
                data.append(" Device type : %s"%(self.data[device]['devicetype']))
                data.append(" Uptime : %s"%(self.getUpTime(device)))
                data.append(" Runtime : %s"%(self.getRunTime(device)))
                data.append(" #Runtimes : %s"%(self.getRunTimes(device)))
                data.append(" #APScheduler jobs : %s"%(self.getAPCount(device)))
            else:
                data.append(" Device not found")
        else:
            data.append("No ""device"" parameter found")
        self._api.log.error("cronJobs.helperList : Done")
        return data

    def helperStop(self, params={}):
        """
        Stop a device
        """
        self._api.log.error("cronJobs.helperStop : Start ...")
        data = []
        if "device" in params:
            device=params["device"]
            data.append("Stop device %s :"%device)
            if device in self.data:
                data.append(" Current state : %s"%(self.data[device]['current']))
                ret=self.stopJob(device)
                data.append(" Return of the command : %s"%(cronErrors[ret]))
                data.append(" Current state : %s"%(self.data[device]['current']))
                data.append(" #APScheduler jobs : %s"%(self.getAPCount(device)))
            else:
                data.append(" Device not found")
        else:
            data.append("No ""device"" parameter found")
        self._api.log.error("cronJobs.helperStop : Done")
        return data

    def helperResume(self, params={}):
        """
        Resume a device
        """
        self._api.log.error("cronJobs.helperResume : Start ...")
        data = []
        if "device" in params:
            device=params["device"]
            data.append("Resume device %s :"%device)
            if device in self.data:
                data.append(" Current state : %s"%(self.data[device]['current']))
                ret=self.resumeJob(device)
                data.append(" Return of the command : %s"%(cronErrors[ret]))
                data.append(" Current state : %s"%(self.data[device]['current']))
                data.append(" #APScheduler jobs : %s"%(self.getAPCount(device)))
            else:
                data.append(" Device not found")
        else:
            data.append("No ""device"" parameter found")
        self._api.log.error("cronJobs.helperResume : Done")
        return data

    def helperHalt(self, params={}):
        """
        Halt a device
        """
        self._api.log.error("cronJobs.helperHalt : Start ...")
        data = []
        if "device" in params:
            device=params["device"]
            data.append("Halt device %s :"%device)
            if params["device"] in self.data:
                data.append(" Current state : %s"%(self.data[device]['current']))
                ret=self.haltJob(device)
                data.append(" Return of the command : %s"%(cronErrors[ret]))
                data.append(" Current state : %s"%("halted"))
            else:
                data.append(" Device not found")
                data.append(" Current state : %s"%("halted"))
        else:
            data.append("No ""device"" parameter found")
        self._api.log.error("cronJobs.helperHalt : Done")
        return data

class cronException(Exception):
    """
    cron exception
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

class cronAPI:
    """
    cron API
    """

    def __init__(self,log,config,myxpl):
        """
        Constructor
        @param plugin : the parent plugin (used to retrieve)
        """
        self.log=log
        self.myxpl=myxpl
        self.config=config
        self.jobs = cronJobs(self)

    def sendXplJob(self,device,parameters=None,value=None):
        """
        Send the XPL Trigger
        @param myxpl : The XPL sender
        @param device : The timer
        @param current : current state
        @param elapsed : elapsed time
        """
        self.log.debug("cronAPI._sendXPLJob : Start ...")
        mess = self.jobs.getXplTrig(device,parameters,value)
        if mess!=None:
            self.myxpl.send(mess)
            self.log.debug("cronAPI._sendXPLJob : xplmessage = %s"%mess)
        self.log.debug("cronAPI._sendXPLJob : Done :)")

    def requestListener(self,message):
        """
        Listen to timer.request messages
        @param message : The XPL message
        @param myxpl : The XPL sender

        timer.request
            {
             device=<name of the timer>
            }
        timer.basic
            {
             device=<name of the timer>
             type=timer|date|interval|cron
             current=halted|resumed|stopped|started
             elapsed=<number of seconds since device created>
             runtime=<number of seconds since device in started state>
             runtimes=<number of messages sent>
            }
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
                mess.add_data({"type" : self.jobs.data[device]['devicetype']})
                mess.add_data({"current" : self.jobs.data[device]['current']})
                mess.add_data({"elapsed" : self.jobs.getUpTime(device)})
                mess.add_data({"runtime" : self.jobs.getRunTime(device)})
#                mess.add_data({"uptime" : self.jobs.getUpTime(device)})
                mess.add_data({"runtimes" : self.jobs.getRunTimes(device)})
            else:
                mess.add_data({"elasped" :  0})
                mess.add_data({"current" : "halted"})
            self.myxpl.send(mess)
            self.log.debug("cronAPI.requestListener : Done :)")
        except:
            self.log.error("action _ %s _ unknown."%(request))
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self.log.debug("cronAPI.requestListener : "+error)

    def basicListener(self,message):
        """
        Listen to timer.request messages
        @param message : The XPL message
        @param myxpl : The XPL sender

        timer.basic
           {
            action=halt|resume|stop|start|status
            device=<name of the timer>
            ...
           }
        """
        self.log.debug("cronAPI.basicListener : Start ...")
        actions = {
            'halt': lambda x,d,m: self._actionHalt(x,d),
            'resume': lambda x,d,m: self._actionResume(x,d),
            'stop': lambda x,d,m: self._actionStop(x,d),
            'start': lambda x,d,m: self._actionStart(x,d,m),
            'status': lambda x,d,m: self._actionStatus(x,d),
            'list': lambda x,d,m: self._actionList(x,d),
        }
        try:
            action = None
            if 'action' in message.data:
                action = message.data['action']
            device = None
            if 'device' in message.data:
                device = message.data['device']
            self.log.debug("cronAPI.basicListener : action %s received with device %s" % (action,device))

            actions[action](self.myxpl,device,message)
        except:
            self.log.error("action _ %s _ unknown."%(action))
            error = "Exception : %s" %  \
                     (traceback.format_exc())
            self.log.debug("cronAPI.basicCmndListener : "+error)

    def _actionList(self,myxpl,device):
        """
        Lists the timers
        timer.basic
           {
            action=status
            ...
           }
        """
        self.log.debug("cronAPI._listStatus : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        mess.add_data({"devices" : self.jobs.getList(False)})
        mess.add_data({"apjobs" : self.jobs.getAPList(False)})
        myxpl.send(mess)
        self.log.debug("cronAPI._listStatus : Done :)")


    def _actionStatus(self,myxpl,device):
        """
        Status of the timers
        timer.basic
           {
            action=status
            ...
           }
        """
        self.log.debug("cronAPI._actionStatus : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        if device in self.jobs.data.iterkeys():
            mess.add_data({"device" : device})
            mess.add_data({"devicetype" : self.jobs.data[device]['devicetype']})
            mess.add_data({"current" :  self.jobs.getState(device)})
            mess.add_data({"uptime" : self.jobs.getUpTime(device)})
            mess.add_data({"runtime" : self.jobs.getRunTime(device)})
            mess.add_data({"runtimes" : self.jobs.getRunTimes(device)})
            mess.add_data({"apjobs" : self.jobs.getAPCount(device)})
        else:
            mess.add_data({"device" : device})
            mess.add_data({"current" : "halted"})
        myxpl.send(mess)
        self.log.debug("cronAPI._actionStatus : Done :)")

    def _actionStop(self,myxpl,device):
        """
        Stop the timer
        @param device : The timer to stop
        """
        self.log.debug("cronAPI._actionStop : Start ...")
        self._sendXplTrig(myxpl,device,"stopped",self.jobs.stopJob(device))
        self.log.debug("cronAPI._actionStop : Done :)")

    def _actionResume(self,myxpl,device):
        """
        Resume the timer
        @param device : The timer to resume
        """
        self.log.debug("cronAPI._actionResume : Start ...")
        self._sendXplTrig(myxpl,device,"started",self.jobs.resumeJob(device))
        self.log.debug("cronAPI._actionResume : Done :)")

    def _actionHalt(self,myxpl,device):
        """
        Halt the timer
        @param device : The timer to halt
        """
        self.log.debug("cronAPI._actionHalt : Start ...")
        self._sendXplTrig(myxpl,device,"halted",self.jobs.haltJob(device))
        self.log.debug("cronAPI._actionHalt : Done :)")

    def _actionStart(self,myxpl,device,message):
        """
        Add and start a timer
        @param device : The timer to start

        timer.basic
            {
             device=<name of the timer>
             current=halted|resumed|stopped|started|went off
             elapsed=<number of seconds between start and stop>
            }
        """
        self.log.debug("cronAPI._actionAdd : Start ...")

        devicetype = "timer"
        if 'devicetype' in message.data:
            devicetype = message.data['devicetype']
        self._sendXplTrig(myxpl,device,"started",self.jobs.addJob(device, devicetype, message))
        self.log.debug("cronAPI._actionAdd : Done :)")

    def _sendXplTrig(self,myxpl,device,current,error):
        """
        Send the XPL Trigger
        @param myxpl : The XPL sender
        @param device : The timer
        @param current : current state
        @param elapsed : time in seconds since timer is created

        timer.basic
            {
             device=<name of the timer>
             current=halted|resumed|stopped|started|went off
             elapsed=<number of seconds since device created>
             runtime=<number of seconds since device in started state>
             runtimes=<number of messages sent>
             [error=<The message of error>]
             [errorcode=<The code of error>]
            }
        """
        self.log.debug("cronAPI._sendXPLTrig : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        mess.add_data({"device" : device})
        if error==ERROR_NO:
            mess.add_data({"current" :  current})
            mess.add_data({"elapsed" : self.jobs.getUpTime(device)})
            mess.add_data({"runtime" : self.jobs.getRunTime(device)})
#            mess.add_data({"uptime" : self.jobs.getUpTime(device)})
            mess.add_data({"runtimes" : self.jobs.getRunTimes(device)})
            self.log.info("cronAPI._sendXPLTrig : Send ok xpl-trig :)")
        else:
            if device in self.jobs.data:
                mess.add_data({"current" : self.jobs.data[device]['current']})
                mess.add_data({"elapsed" : self.jobs.getUpTime(device)})
                mess.add_data({"runtime" : self.jobs.getRunTime(device)})
#                mess.add_data({"uptime" : self.jobs.getUpTime(device)})
                mess.add_data({"runtimes" : self.jobs.getRunTimes(device)})
            else:
                mess.add_data({"elasped" :  0})
                mess.add_data({"current" : "halted"})
            mess.add_data(self.error(error))
            self.log.info("cronAPI._sendXPLTrig : Send error xpl-trig :(")
        myxpl.send(mess)
        self.log.debug("cronAPI._sendXPLTrig : Done :)")

    def error(self,code):
        errorcode=code
        error=cronErrors[code]
        res= {'errorcode':errorcode,  'error':error}
        return res

if __name__ == "__main__":
    dd = cronAPI()
    #l, c = dd.get_dawn_dusk(-01.7075, 48.1173, 1)
    #print(l)
    #print(c)

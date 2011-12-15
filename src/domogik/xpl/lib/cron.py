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

XPL Cron

Implements
==========

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
ERROR_SCHEDULER=20

cronErrors = { ERROR_NO: 'No error',
               ERROR_PARAMETER: 'Missing or wrong parameter',
               ERROR_DEVICE_EXIST: 'Device already exist',
               ERROR_DEVICE_NOT_EXIST: 'Device does not exist',
               ERROR_SCHEDULER: 'Error with the scheduler',
               }

class cronJobs:

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

    def stopJob(self, device):
        """
        stop a job
        @param device : the name of the job (=device in xpl)
        """
        if device in self.data.iterkeys():
            if self.data[device]['apjob']!=None:
                self._scheduler.unschedule_job(self.data[device]['apjob'])
            if 'apjobs' in self.data[device]:
                while len(self.data[device]['apjobs'])>0:
                    i=self.data[device]['apjobs'].pop()
                    self._scheduler.unschedule_job(i)
                del (self.data[device]['apjobs'])
            self.data[device]['current']="stopped"
            self.data[device]['apjob']=None
            return ERROR_NO
        else:
            return ERROR_DEVICE_NOT_EXIST

    def removeJob(self, device):
        """
        Stop and remove a job
        @param device : the name of the job (=device in xpl)
        """
        if device in self.data.iterkeys():
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
        if device in self.data.iterkeys():
            if self.data[device]['apjob']!=None:
                self._scheduler.unschedule_job(self.data[device]['apjob'])
            self.data[device]['apjob']=None
            return self.startJob(device)
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
        }
        if device in self.data.iterkeys():
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
            self._api.log.exception("cronJobs._startJobDate : "+traceback.format_exc())
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
                self._api.log.exception("cronJobs._startJobDate : "+traceback.format_exc())
                del(self.data[device])
                return ERROR_SCHEDULER
            return ERROR_NO
        else:
            self._api.log.exception("cronJobs._startJobDate : Don't add cron job : no parameters given")
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
            self._api.log.exception("cronJobs._startJobTimer : "+traceback.format_exc())
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
                self._api.log.exception("cronJobs._startJobTimer : "+traceback.format_exc())
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
                self._api.log.exception("cronJobs._startJobTimer : "+traceback.format_exc())
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
                self._api.log.exception("cronJobs._startJobInterval : Don't add cron job : no parameters given")
                del(self.data[device])
                return ERROR_PARAMETER
            startdate = None
            if 'startdate' in self.data[device]:
                startdate = self.dateFromXPL(self.data[device]['startdate'])
        except:
            self._api.log.exception("cronJobs._startJobInterval : "+traceback.format_exc())
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

            self._api.log.exception("cronJobs._startJobInterval : "+traceback.format_exc())
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
                self._api.log.exception("cronJobs._startJobCron : Don't add cron job : no parameters given")
                del(self.data[device])
                return ERROR_PARAMETER
            startdate = None
            if 'startdate' in self.data[device]:
                startdate = self.dateFromXPL(self.data[device]['startdate'])
        except:
            self._api.log.exception("cronJobs._startJobCron : "+traceback.format_exc())
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
            self._api.log.exception("cronJobs._startJobCron : "+traceback.format_exc())
            del(self.data[device])
            return ERROR_SCHEDULER
        return ERROR_NO

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
                            'apjob' : None,
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

    def getList(self):
        """
        Get the list of jobs
        @return : The list of jobs
        """
        lines = []
        lines.append("%s | %s | %s" % ("device","type","state"))
        for i in self.data.iterkeys():
            #print i
            lines.append("%s | %s | %s" % (i,self.data[i]['devicetype'],self.data[i]['current']))
        return lines

    def getAPList(self):
        """
        Get the list of jobs
        @return : The list of jobs in APScheduler
        """
        lines = []
        lines.append("%s | %s" % ("name","runs"))
        for i in self._scheduler.get_jobs():
            lines.append("%s | %s" % (str(i.name), i.runs))
        return lines

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

    def getXplTrig(self,device):
        """
        Return the xpl message to send and increase the counter
        """
        if device not in self.data.iterkeys():
            return None
        self.data[device]['runs']=self.data[device]['runs']+1
        mess = XplMessage()
        mess.add_data({'device' : device})
        mess.set_type("xpl-trig")
        mess.set_schema("timer.basic")
        for key in self.data[device]:
            if key[0:4].startswith("nst-"):
                k=key[4:]
                if k.startswith("schema"):
                   mess.set_schema(self.data[device][key])
                elif k.startswith("xpltype"):
                   mess.set_type(self.data[device][key])
                else:
                   mess.add_data({k : self.data[device][key]})
        return mess

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

    def sendXplJob(self,device):
        """
        Send the XPL Trigger
        @param myxpl : The XPL sender
        @param device : The timer
        @param current : current state
        @param elapsed : elapsed time
        """
        self.log.debug("cronAPI._sendXPLJob : Start ...")
        mess = self.jobs.getXplTrig(device)
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
#            mess.add_data({"uptime" : self.jobs.getUpTime(device)})
            mess.add_data({"runtimes" : self.jobs.getRunTimes(device)})
        else:
            mess.add_data({"elasped" :  0})
            mess.add_data({"current" : "halted"})
        self.myxpl.send(mess)
        self.log.debug("cronAPI.requestListener : Done :)")

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
        }
        action = None
        if 'action' in message.data:
            action = message.data['action']

        device = None
        if 'device' in message.data:
            device = message.data['device']

        self.log.debug("cronAPI.basicListener : action %s received with device %s" % (action,device))

        actions[action](self.myxpl,device,message)

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
        else:
            mess.add_data({"devices" : self.jobs.getList()})
            mess.add_data({"apjobs" : self.jobs.getAPList()})
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
        self._sendXplTrig(myxpl,device,"resumed",self.jobs.resumeJob(device))
        self.log.debug("cronAPI._actionResume : Done :)")

    def _actionHalt(self,myxpl,device):
        """
        Halt the timer
        @param device : The timer to halt
        """
        self.log.debug("cronAPI._actionHalt : Start ...")
        self._sendXplTrig(myxpl,device,"halted",self.jobs.removeJob(device))
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
            if device in self.jobs.data.iterkeys():
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

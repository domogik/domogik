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
class CronStore
class cronTools

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import datetime
import traceback
import ConfigParser
import os
import glob

ERROR_NO = 0
ERROR_PARAMETER = 1
ERROR_DEVICE_EXIST = 10
ERROR_DEVICE_NOT_EXIST = 11
ERROR_DEVICE_NOT_STARTED = 12
ERROR_DEVICE_NOT_STOPPED = 13
ERROR_SCHEDULER = 20
ERROR_STORE = 30
ERROR_NOT_IMPLEMENTED = 40

CRONERRORS = { ERROR_NO: 'No error',
               ERROR_PARAMETER: 'Missing or wrong parameter',
               ERROR_DEVICE_EXIST: 'Device already exist',
               ERROR_DEVICE_NOT_EXIST: 'Device does not exist',
               ERROR_DEVICE_NOT_STARTED: "Device is not started",
               ERROR_DEVICE_NOT_STOPPED: "Device is not stopped",
               ERROR_SCHEDULER: 'Error with the scheduler',
               ERROR_STORE: 'Error with the store',
               }

class CronStore():
    """
    Store the jobs in the filesystem. We use a ConfigParser file per job.
    Sections [Job] [Stats] [Alarms] [Timers]
    """
    def __init__(self, log, data_dir):
        """
        Initialise the store engine. Create the directory if necessary.
        """
        self._log = log
        self._data_files_dir = data_dir
        self._log.debug("cronJobs.store_init : Use directory %s" % \
                self._data_files_dir)
        if not os.path.isdir(self._data_files_dir):
            os.mkdir(self._data_files_dir, 0770)
        self._badfields = ["action", "starttime", "uptime", "runtime"]
        self._statfields = ["current", "runs", "createtime"]

    def load_all(self, add_job_cb):
        """
        Load all jobs from the filesystem. Parse all the *.job files
        in directory and call the callback ùethod to add it to the cron
        jobs.
        """
        for jobfile in glob.iglob(self._data_files_dir+"/*.job") :
            config = ConfigParser.ConfigParser()
            config.read(jobfile)
            self._log.debug("cronJobs.store_init : Load job from %s" % \
                    jobfile)
            data = dict()
            for option in config.options('Job'):
                data[option] = config.get('Job', option)
            for option in config.options('Stats'):
                data[option] = config.get('Stats', option)
            if config.has_section('Timers'):
                timers = set()
                for option in config.options('Timers'):
                    timers.add(config.get('Timers', option))
                data['timer'] = timers
            if config.has_section('Alarms'):
                alarms = set()
                for option in config.options('Alarms'):
                    alarms.add(config.get('Alarms', option))
                data['alarm'] = alarms
            add_job_cb(data['device'], data['devicetype'], data)

    def _get_jobfile(self, job):
        """
        Return the filename associated to a job.
        """
        return os.path.join(self._data_files_dir, job + ".job")

    def on_start(self, job, data):
        """
        Must be called when a job is started. Is also ( indirectly)
        called when a job is resumed.
        """
        try:
            self._log.debug("cronJobs.store_on_start : job %s" % \
                job)
            config = ConfigParser.ConfigParser()
            if os.path.isfile(self._get_jobfile(job)):
                #The file already exists. We are in resume case.
                config.read(self._get_jobfile(job))
            timer_idx = 1
            alarm_idx = 1
            if not config.has_section('Job'):
                config.add_section('Job')
            if not config.has_section('Stats'):
                config.add_section('Stats')
            for key in data:
                if key.startswith("timer") :
                    if not config.has_section('Timers'):
                        config.add_section('Timers')
                    if type(data[key])==type(""):
                        config.set('Timers', str(timer_idx), data[key])
                    else:
                        for tim in data[key] :
                            config.set('Timers', str(timer_idx), tim)
                            timer_idx = timer_idx + 1
                elif key.startswith("alarm") :
                    if not config.has_section('Alarms'):
                        config.add_section('Alarms')
                    if type(data[key])==type(""):
                        config.set('Alarms', str(alarm_idx), data[key])
                    else:
                        for al in data[key] :
                            config.set('Alarms', str(alarm_idx), al)
                            alarm_idx = alarm_idx + 1
                elif key in self._statfields:
                    if key == "createtime":
                        config.set('Stats', key, data[key])
                    else:
                        config.set('Stats', key, data[key])
                elif key in self._badfields:
                    continue
                else :
                    config.set('Job', key, data[key])
            if not config.has_section('Stats'):
                config.add_section('Stats')
            config.set('Stats', "current", "started")
            with open(self._get_jobfile(job), 'w') \
                    as configfile:
                config.write(configfile)
            configfile.close
            return ERROR_NO
        except:
            self._log.error("cronJobs.store_on_start : " + \
                traceback.format_exc())
            return ERROR_STORE

    def on_halt(self, job):
        """
        Must be called when a job is halted. It deletes the file
        associated to the job.
        """
        try:
            self._log.debug("cronJobs.store_on_halt : job %s" % \
                job)
            if os.path.isfile(self._get_jobfile(job)):
                os.remove(self._get_jobfile(job))
            return ERROR_NO
        except:
            self._log.error("cronJobs.store_on_halt : " + \
                traceback.format_exc())
            return ERROR_STORE

    def on_stop(self, job, uptime, runtime, runs):
        """
        Must be called when a job is stopped.
        """
        try:
            self._log.debug("cronJobs.store_on_stop : job %s" % \
                job)
            config = ConfigParser.ConfigParser()
            config.read(self._get_jobfile(job))
            config.set('Stats', "current", "stopped")
            config.set('Stats', "runs", runs)
            #oldruntime = 0
            #if config.has_option('Stats','runtime'):
            #    oldruntime = config.getfloat('Stats','runtime')
            #config.set('Stats', "runtime", oldruntime+runtime)
            config.set('Stats', "runtime", runtime)
            with open(self._get_jobfile(job), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._log.error("cronJobs.store_on_stop : " + \
                traceback.format_exc())
            return ERROR_STORE

    def on_resume(self, job):
        """
        Must be called when a job is resumed.
        """

class CronTools():
    """
    Usefull tools to cron jobs
    """
    def is_valid_hour(self, hour):
        """
        Test the format of an hour. Valid format is HH:MM
        @parameter hour The hour to test
        @return True if hour is valid
        """
        try:
            t = datetime.time(int(hour[0:2]), int(hour[3:5]))
        except :
            return False
        return True

    def is_valid_int(self, number):
        """
        Test if number is an integer
        @parameter number The number to test
        @return True if number is an integer
        """
        try:
            t = int(number)
        except :
            return False
        return True

    def date_from_xpl(self, xpldate):
        """
        Tranform an XPL date "yyyymmddhhmmss" to datetime
        form
        @parameter xpldate The xpldate to transform
        @return A datetime object if everything went fine. None otherwise.
        """
        try:
            y = int(xpldate[0:4])
            mo = int(xpldate[4:6])
            d = int(xpldate[6:8])
            h = int(xpldate[8:10])
            m = int(xpldate[10:12])
            s = int(xpldate[12:14])
            return datetime.datetime(y, mo, d, h, m, s)
        except:
            return None

    def date_to_xpl(self, sdate):
        """
        Tranform an datetime date to an xpl one "yyyymmddhhmmss"
        form
        @parameter sdate The datetime to transform
        @return A string representing the xpl date if everything \
            went fine. None otherwise.
        """
        try:
            h = "%.2i" % sdate.hour
            m = "%.2i" % sdate.minute
            s = "%.2i" % sdate.second
            y = sdate.year
            mo = "%.2i" % sdate.month
            d = "%.2i" % sdate.day
            xpldate = "%s%s%s%s%s%s" % (y, mo, d, h, m, s)
            return xpldate
        except:
            return None

    def delta_hour(self, h1, h2):
        """
        Return the delta between 2 hours
        """
        dummy_date = datetime.date(1, 1, 1)
        full_h1 = datetime.datetime.combine(dummy_date, \
            datetime.time(int(h1[0:2]), int(h1[3:5])))
        full_h2 = datetime.datetime.combine(dummy_date, \
            datetime.time(int(h2[0:2]), int(h2[3:5])))
        elapsed = full_h1-full_h2
        res = elapsed.days*86400 + elapsed.seconds + \
            elapsed.microseconds / 1000000.0
        return res

    def add_hour(self, h, s):
        """
        Add an seconds to an hour
        """
        dummy_date = datetime.date(1, 1, 1)
        full_h = datetime.datetime.combine(dummy_date, \
            datetime.time(int(h[0:2]), int(h[3:5])))
        res = full_h + datetime.timedelta(seconds=s)
        return res.hour, res.minute

    def error(self, code):
        """
        Return the error text of an error code
        """
        errorcode = code
        error = CRONERRORS[code]
        res = {'errorcode':errorcode, 'error':error}
        return res

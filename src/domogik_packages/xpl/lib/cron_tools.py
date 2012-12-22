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
import json
import urllib2
import urllib

ERROR_NO = 0
ERROR_PARAMETER = 1
ERROR_DEVICE_EXIST = 10
ERROR_DEVICE_NOT_EXIST = 11
ERROR_DEVICE_NOT_STARTED = 12
ERROR_DEVICE_NOT_STOPPED = 13
ERROR_SCHEDULER = 20
ERROR_STORE = 30
ERROR_REST = 40
ERROR_NOT_IMPLEMENTED = 50

CRONERRORS = { ERROR_NO: 'No error',
               ERROR_PARAMETER: 'Missing or wrong parameter.',
               ERROR_DEVICE_EXIST: 'Device/alarm already exist.',
               ERROR_DEVICE_NOT_EXIST: 'Device/alarm does not exist.',
               ERROR_DEVICE_NOT_STARTED: "Device/alarm is not started.",
               ERROR_DEVICE_NOT_STOPPED: "Device/alarm is not stopped.",
               ERROR_SCHEDULER: 'Error with the scheduler (APS).',
               ERROR_STORE: 'Error with the store.',
               ERROR_REST: 'Error with REST.',
               }

class CronRest():
    """
    Manipulate Domogik's devices associated to the cron jobs through the rest interface
    """
    def __init__(self, rest_ip, rest_port, log):
        #self._rest_ip = rest_ip
        #self._rest_port = rest_port
        self._log = log
        self._rest = "http://%s:%s" % (rest_ip, rest_port)

    def list(self):
        """
        List all Domogik's devices associated to cron jobs

        The associated rest url is :
        http://192.168.14.167:40405/base/device/list

        @return None or a dict

        """
        the_url = "%s/base/device/list" % (self._rest)
        req = urllib2.Request(the_url)
        handle = urllib2.urlopen(req)
        devices = handle.read()
        ret = json.loads(devices)
        self._log.debug("CronRest.list : %s" % ret)
        if ret["status"] == "OK" :
            #self._log.debug("CronRest.list : type ret['device'] = %s" % type(ret["device"]))
            return ret["device"]
        else :
            return None

    def _get_id(self, job):
        """
        Return the id of a Domogik's device associated to a cron job

        @param job : the cron job
        @return None or the Domogik's device id

        """
        devices = self.list()
        if devices != None :
            for device in devices :
                if device["name"] == job["device"] \
                  and device["address"] == job["device"] \
                  and device["device_type"]["device_technology_id"] == "cron" :
                    return device["id"]
            return None
        else :
            return None

    def add(self, job, label):
        """
        Add the Domogik's device associated to a cron job

        The associated rest url is :
        http://192.168.14.167:40405/base/device/add/name/dname/address/daddress/type_id/cron.job/usage_id/light/description/desc/reference/ref

        @param job : the cron job
        @return True if delete successfull, False otherwise

        """
        try:
            name = job["device"]
            address = job["device"]
            device_type = "cron.job"
            usage = "light"
            ref = urllib.quote("Cron job %s" % job["devicetype"])
            desc = urllib.quote("%s" % label)
            the_url = "%s/base/device/add/name/%s/address/%s/type_id/%s/usage_id/%s/description/%s/reference/%s//" % \
                (self._rest, name, address, device_type, usage, desc, ref)
            req = urllib2.Request(the_url)
            handle = urllib2.urlopen(req)
            rest_ret = handle.read()
            #self._log.debug("CronRest.add : rest_ret=%s" % rest_ret)
            ret = json.loads(rest_ret)
            self._log.debug("CronRest.add : ret=%s" % ret)
            if ret["status"] == "OK" :
                return True
            else :
                return False
        except:
            self._log.error("rest.add : " + \
                traceback.format_exc())
            return False

    def delete(self, job):
        """
        Delete a Domogik's device associated to cron job

        The associated rest url is :
        http://192.168.14.167:40405/base/device/del/device_id

        @param job : the cron job
        @return True if delete successfull, False otherwise

        """
        the_id = self._get_id(job)
        if the_id != None :
            the_url = "%s/base/device/del/%s" % (self._rest, the_id)
            req = urllib2.Request(the_url)
            handle = urllib2.urlopen(req)
            rest_ret = handle.read()
            ret = json.loads(rest_ret)
            self._log.debug("CronRest.delete : %s" % ret)
            if ret["status"] == "OK" :
                return True
            else :
                return False
        else :
            return False

class PluginStoreInf():
    """
    A class to store plugin data in the file system.
    We use the ConfigParser to store informations in a config file (also known as Inf files).

    We store multiple keys (set(), dict(), ...) in a section. We will use an integer as key.
    ie : [alarm,alarm1,alarm2,...] <--> section:[alarm] 0= 1= 2=

    We also manage statistics : "current", "state", "runs", "createtime", "runtime"
    ie : [stats_createtime,stats_starttime,stats_runs,...] <--> section:[stats] createtime= startime= runs=

    All needed data is stored in the parent container (which is supposed to be a dict).
    The key will start with the prefix "stats_"

    """
    def __init__(self, plugin, filext=".dat"):
        """
        Initialise the store engine. Create the directory if necessary.

        @param plugin : the plugin
        @param filext : the file extension used to store data. Must start with a "."

        """
        self._plugin = plugin
        data_dir = plugin.get_data_files_directory()
        self._plugin.log.debug("Try to use %s to store data." % data_dir)
        if os.path.exists(data_dir):
            if not os.access(data_dir, os.W_OK & os.X_OK):
                raise OSError("Can't write in directory %s" % data_dir)
        else:
            try:
                self._plugin.log.info("cronJobs.store_init : create directory %s." % data_dir)
                os.mkdir(data_dir, 0770)
            except:
                raise IOError("Can't create directory %s." % data_dir)
        try:
            tmp_prefix = "write_test"
            count = 0
            filename = os.path.join(data_dir, tmp_prefix)
            while(os.path.exists(filename)):
                filename = "{}.{}".format(os.path.join(data_dir, tmp_prefix), count)
                count = count + 1
            fff = open(filename,"w")
            fff.close()
            os.remove(filename)
        except :
            raise IOError("Can't create a file in directory %s." % data_dir)
        self._data_files_dir = data_dir
        self._plugin.log.info("Use directory %s to store data." % self._data_files_dir)

        self._filext = filext

        self.badfields = ["action", "starttime", "uptime", ]

        self.statfields = ["current", "state", "runs", "createtime", "runtime"]

    def load_all(self, add_job_cb):
        """
        Load all jobs from the filesystem. Parse all the *.job files
        in directory and call the callback method to add it to the cron
        jobs.

        @param add_job_cb : callback to the function who add the job to CronJobs

        """
        for jobfile in glob.iglob(self._data_files_dir+"/*"+self._filext) :
            config = ConfigParser.ConfigParser()
            config.read(jobfile)
            self._plugin.log.debug("store_init : Load job from %s" % jobfile)
            data = dict()
            for option in config.options('Job'):
                data[option] = config.get('Job', option)
            for option in config.options('Stats'):
                data[option] = config.get('Stats', option)
            if config.has_section('Sensor'):
                for option in config.options('Sensor'):
                    data['sensor_'+option] = config.get('Sensor', option)
            if config.has_section('Timers'):
                timers = set()
                for option in config.options('Timers'):
                    timers.add(config.get('Timers', option))
                data['timer'] = timers
            #Will be implement in the future
            if config.has_section('Dates'):
                timers = set()
                for option in config.options('Dates'):
                    timers.add(config.get('Dates', option))
                data['date'] = timers
            if config.has_section('Alarms'):
                alarms = set()
                for option in config.options('Alarms'):
                    alarms.add(config.get('Alarms', option))
                data['alarm'] = alarms
            err = add_job_cb(data['device'], data['devicetype'], data)
            if err != ERROR_NO :
                self._plugin.log.warning("Can't load job from %s : error=%s" % (jobfile, CRONERRORS[err]))

    def _get_filename(self, job):
        """
        Return the filename associated to a job.

        @param job : the job name

        """
        return os.path.join(self._data_files_dir, job + self._filext)

    def on_start(self, job, data):
        """
        Must be called when a job is started. Is also (indirectly)
        called when a job is resumed.

        @param job : the job name
        @param data : a dict() containing the parameters of the job

        """
        try:
            self._plugin.log.debug("on_start : job %s" % job)
            config = ConfigParser.ConfigParser()
            if os.path.isfile(self._get_filename(job)):
                #The file already exists. We are in resume case.
                config.read(self._get_filename(job))
            timer_idx = 1
            alarm_idx = 1
            date_idx = 1
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
                        timer_idx = timer_idx + 1
                    else:
                        for tim in data[key] :
                            config.set('Timers', str(timer_idx), tim)
                            timer_idx = timer_idx + 1
                elif key.startswith("alarm") :
                    if not config.has_section('Alarms'):
                        config.add_section('Alarms')
                    if type(data[key])==type(""):
                        config.set('Alarms', str(alarm_idx), data[key])
                        alarm_idx = alarm_idx + 1
                    else:
                        for aal in data[key] :
                            config.set('Alarms', str(alarm_idx), aal)
                            alarm_idx = alarm_idx + 1
                #Will be implement in the future
                elif key.startswith("date") :
                    if not config.has_section('Dates'):
                        config.add_section('Dates')
                    if type(data[key])==type(""):
                        config.set('Dates', str(date_idx), data[key])
                        date_idx = date_idx + 1
                    else:
                        for aal in data[key] :
                            config.set('Dates', str(date_idx), aal)
                            date_idx = date_idx + 1
                elif key.startswith("sensor_") :
                    if not config.has_section('Sensor'):
                        config.add_section('Sensor')
                    config.set('Sensor', key[7:], data[key])
                elif key in self.statfields:
                    if key == "createtime":
                        config.set('Stats', key, data[key])
                        #We do nothing, this jobs may not be updated as the jobs where stopped
                    else:
                        config.set('Stats', key, data[key])
                elif key in self.badfields:
                    continue
                else :
                    config.set('Job', key, data[key])
            if not config.has_section('Stats'):
                config.add_section('Stats')
            config.set('Stats', "state", "started")
            with open(self._get_filename(job), 'w') \
                    as configfile:
                config.write(configfile)
            configfile.close
            return ERROR_NO
        except:
            self._plugin.log.error("store_on_start : " + traceback.format_exc())
            return ERROR_STORE

    def on_halt(self, job):
        """
        Must be called when a job is halted. It deletes the file
        associated to the job.

        @param job : the job name

        """
        try:
            self._plugin.log.debug("store_on_halt : job %s" % job)
            if os.path.isfile(self._get_filename(job)):
                os.remove(self._get_filename(job))
            return ERROR_NO
        except:
            self._plugin.log.error("store_on_halt : " + traceback.format_exc())
            return ERROR_STORE

    def on_stop(self, job, uptime, runtime, runs):
        """
        Must be called when a job is stopped.

        @param job : the job name
        @param uptime : the uptime of the job
        @param runtime : the cumulative runtime of the job
        @param runs : the number of job's run

        """
        try:
            self._plugin.log.debug("store_on_stop : job %s" % job)
            config = ConfigParser.ConfigParser()
            config.read(self._get_filename(job))
            config.set('Stats', "state", "stopped")
            config.set('Stats', "runs", runs)
            config.set('Stats', "runtime", runtime)
            with open(self._get_filename(job), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._plugin.log.error("store_on_stop : " + traceback.format_exc())
            return ERROR_STORE

    def on_close(self, job, uptime, runtime, runs):
        """
        Must be called when a job is closed : the plugin is stopped.

        @param job : the job name
        @param uptime : the uptime of the job
        @param runtime : the runtime of the job
        @param runs : the number of job's run

        """
        try:
            self._plugin.log.debug("store_on_close : job %s" % job)
            config = ConfigParser.ConfigParser()
            config.read(self._get_filename(job))
            config.set('Stats', "runs", runs)
            config.set('Stats', "runtime", runtime)
            with open(self._get_filename(job), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._plugin.log.error("store_on_close : " + traceback.format_exc())
            return ERROR_STORE

    def on_resume(self, job):
        """
        Must be called when a job is resumed.

        @param job : the job name

        """

    def on_fire(self, job, status, uptime, runtime, runs):
        """
        Must be called when a job is fired.

        @param job : the job name
        @param status : the status of the sensor associated to the job
        @param uptime : the uptime of the job
        @param runtime : the cumulative runtime of the job
        @param runs : the number of job's run

        """
        try:
            self._plugin.log.debug("store_on_fire : job %s" % job)
            config = ConfigParser.ConfigParser()
            config.read(self._get_filename(job))
            config.set('Sensor', "status", status)
            config.set('Stats', "runs", runs)
            with open(self._get_filename(job), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._plugin.log.error("store_on_fire : " + traceback.format_exc())
            return ERROR_STORE

class CronStore():
    """
    Store the jobs in the filesystem. We use a ConfigParser file per job.
    Sections [Job] [Stats] [Alarms] [Timers]
    """
    def __init__(self, log, data_dir):
        """
        Initialise the store engine. Create the directory if necessary.

        @param log : the logger
        @param data_dir : the data directory where store the cron files

        """
        self._log = log
        self._data_files_dir = data_dir
        self._log.info("cronJobs.store_init : Use directory %s to store jobs." % \
                self._data_files_dir)
        self._badfields = ["action", "starttime", "uptime", ]
        self._statfields = ["current", "state", "runs", "createtime", "runtime"]

    def load_all(self, add_job_cb):
        """
        Load all jobs from the filesystem. Parse all the *.job files
        in directory and call the callback method to add it to the cron
        jobs.

        @param add_job_cb : callback to the function who add the job to CronJobs

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
            if config.has_section('Sensor'):
                for option in config.options('Sensor'):
                    data['sensor_'+option] = config.get('Sensor', option)
            if config.has_section('Timers'):
                timers = set()
                for option in config.options('Timers'):
                    timers.add(config.get('Timers', option))
                data['timer'] = timers
            #Will be implement in the future
            if config.has_section('Dates'):
                timers = set()
                for option in config.options('Dates'):
                    timers.add(config.get('Dates', option))
                data['date'] = timers
            if config.has_section('Alarms'):
                alarms = set()
                for option in config.options('Alarms'):
                    alarms.add(config.get('Alarms', option))
                data['alarm'] = alarms
            err = add_job_cb(data['device'], data['devicetype'], data)
            if err != ERROR_NO :
                self._log.warning("Can't load job from %s : error=%s" % \
                    (jobfile,CRONERRORS[err]))

    def _get_jobfile(self, job):
        """
        Return the filename associated to a job.

        @param job : the job name

        """
        return os.path.join(self._data_files_dir, job + ".job")

    def on_start(self, job, data):
        """
        Must be called when a job is started. Is also ( indirectly)
        called when a job is resumed.

        @param job : the job name
        @param data : a dict() containing the parameters of the job

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
            date_idx = 1
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
                        timer_idx = timer_idx + 1
                    else:
                        for tim in data[key] :
                            config.set('Timers', str(timer_idx), tim)
                            timer_idx = timer_idx + 1
                elif key.startswith("alarm") :
                    if not config.has_section('Alarms'):
                        config.add_section('Alarms')
                    if type(data[key])==type(""):
                        config.set('Alarms', str(alarm_idx), data[key])
                        alarm_idx = alarm_idx + 1
                    else:
                        for aal in data[key] :
                            config.set('Alarms', str(alarm_idx), aal)
                            alarm_idx = alarm_idx + 1
                #Will be implement in the future
                elif key.startswith("date") :
                    if not config.has_section('Dates'):
                        config.add_section('Dates')
                    if type(data[key])==type(""):
                        config.set('Dates', str(date_idx), data[key])
                        date_idx = date_idx + 1
                    else:
                        for aal in data[key] :
                            config.set('Dates', str(date_idx), aal)
                            date_idx = date_idx + 1
                elif key.startswith("sensor_") :
                    if not config.has_section('Sensor'):
                        config.add_section('Sensor')
                    config.set('Sensor', key[7:], data[key])
                elif key in self._statfields:
                    if key == "createtime":
                        config.set('Stats', key, data[key])
                        #We do nothing, this jobs may not be updated as the jobs where stopped
                    else:
                        config.set('Stats', key, data[key])
                elif key in self._badfields:
                    continue
                else :
                    config.set('Job', key, data[key])
            if not config.has_section('Stats'):
                config.add_section('Stats')
            config.set('Stats', "state", "started")
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

        @param job : the job name

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

        @param job : the job name
        @param uptime : the uptime of the job
        @param runtime : the cumulative runtime of the job
        @param runs : the number of job's run

        """
        try:
            self._log.debug("cronJobs.store_on_stop : job %s" % \
                job)
            config = ConfigParser.ConfigParser()
            config.read(self._get_jobfile(job))
            config.set('Stats', "state", "stopped")
            config.set('Stats', "runs", runs)
            config.set('Stats', "runtime", runtime)
            with open(self._get_jobfile(job), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._log.error("cronJobs.store_on_stop : " + \
                traceback.format_exc())
            return ERROR_STORE

    def on_close(self, job, uptime, runtime, runs):
        """
        Must be called when a job is closed : the plugin is stopped.

        @param job : the job name
        @param uptime : the uptime of the job
        @param runtime : the runtime of the job
        @param runs : the number of job's run

        """
        try:
            self._log.debug("cronJobs.store_on_close : job %s" % \
                job)
            config = ConfigParser.ConfigParser()
            config.read(self._get_jobfile(job))
            config.set('Stats', "runs", runs)
            config.set('Stats', "runtime", runtime)
            with open(self._get_jobfile(job), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._log.error("cronJobs.store_on_close : " + \
                traceback.format_exc())
            return ERROR_STORE

    def on_resume(self, job):
        """
        Must be called when a job is resumed.

        @param job : the job name

        """

    def on_fire(self, job, status, uptime, runtime, runs):
        """
        Must be called when a job is fired.

        @param job : the job name
        @param status : the status of the sensor associated to the job
        @param uptime : the uptime of the job
        @param runtime : the cumulative runtime of the job
        @param runs : the number of job's run

        """
        try:
            self._log.debug("cronJobs.store_on_fire : job %s" % \
                job)
            config = ConfigParser.ConfigParser()
            config.read(self._get_jobfile(job))
            config.set('Sensor', "status", status)
            config.set('Stats', "runs", runs)
            with open(self._get_jobfile(job), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._log.error("cronJobs.store_on_fire : " + \
                traceback.format_exc())
            return ERROR_STORE

class CronTools():
    """
    Usefull tools to cron jobs
    """
    def is_valid_hour(self, hour):
        """
        Test the format of an hour. Valid format is HH:MM

        @parameter hour: The hour to test
        @return: True if hour is valid

        """
        try:
            #t = datetime.time(int(hour[0:2]), int(hour[3:5]))
            hhhh, mmmm = hour.split(":")
            tttt = datetime.time(int(hhhh), int(mmmm))
        except :
            return False
        return True

    def is_valid_int(self, number):
        """
        Test if number is an integer

        @parameter number: The number to test
        @return: True if number is an integer

        """
        try:
            ttt = int(number)
        except :
            return False
        return True

    def date_from_xpl(self, xpldate):
        """
        Tranform an XPL date "yyyymmddhhmmss" to datetime
        form

        @parameter xpldate: The xpldate to transform
        @return: A datetime object if everything went fine. None otherwise.

        """
        try:
            yyy = int(xpldate[0:4])
            mon = int(xpldate[4:6])
            ddd = int(xpldate[6:8])
            hhh = int(xpldate[8:10])
            mmm = int(xpldate[10:12])
            sss = int(xpldate[12:14])
            return datetime.datetime(yyy, mon, ddd, hhh, mmm, sss)
        except:
            return None
        return None

    def date_to_xpl(self, sdate):
        """
        Tranform an datetime date to an xpl one "yyyymmddhhmmss"
        form.

        @parameter sdate: The datetime to transform
        @return: A string representing the xpl date if everything \
            went fine. None otherwise.

        """
        try:
            hhh = "%.2i" % sdate.hour
            mmm = "%.2i" % sdate.minute
            sss = "%.2i" % sdate.second
            yyy = sdate.year
            mon = "%.2i" % sdate.month
            ddd = "%.2i" % sdate.day
            xpldate = "%s%s%s%s%s%s" % (yyy, mon, ddd, hhh, mmm, sss)
            return xpldate
        except:
            return None
        return None

    def delta_hour(self, hh1, hh2):
        """
        Calculate the delta between 2 hours.

        @param h1: the first hour
        @param h2: the second hour
        @return: the delta between 2 hours

        """
        dummy_date = datetime.date(1, 1, 1)
        hour, minute = hh1.split(":")
        full_h1 = datetime.datetime.combine(dummy_date, \
            datetime.time(int(hour), int(minute)))
        hour, minute = hh2.split(":")
        full_h2 = datetime.datetime.combine(dummy_date, \
            datetime.time(int(hour), int(minute)))
        elapsed = full_h1-full_h2
        res = elapsed.days*86400 + elapsed.seconds + \
            elapsed.microseconds / 1000000.0
        return res

    def add_hour(self, hhh, sss):
        """
        Add seconds to an hour.

        @param h: the hour
        @param h2: the seconds to add
        @return: the new hour

        """
        dummy_date = datetime.date(1, 1, 1)
        hour, minute = hhh.split(":")
        full_h = datetime.datetime.combine(dummy_date, \
            datetime.time(int(hour), int(minute)))
        res = full_h + datetime.timedelta(seconds=sss)
        return res.hour, res.minute

    def error(self, code):
        """
        Return the error text of an error code

        @param code: the error code
        @return: the message corresponding to error code

        """
        if code != ERROR_NO :
            errorcode = code
            error = CRONERRORS[code]
            res = {'errorcode':errorcode, 'error':error}
            return res
        return {}

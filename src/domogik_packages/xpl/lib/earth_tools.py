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
ERROR_EVENT_EXIST = 10
ERROR_EVENT_NOT_EXIST = 11
ERROR_EVENT_NOT_STARTED = 12
ERROR_EVENT_NOT_STOPPED = 13
ERROR_SCHEDULER = 20
ERROR_STORE = 30
ERROR_REST = 40
ERROR_TYPE_NOT_EXIST = 50
ERROR_PARAMETER_NOT_EXIST = 51
ERROR_STATUS_NOT_EXIST = 52
ERROR_NOT_IMPLEMENTED = 60

EARTHERRORS = { ERROR_NO: 'No error',
               ERROR_PARAMETER: 'Missing or wrong parameter.',
               ERROR_EVENT_EXIST: 'Event already exist.',
               ERROR_EVENT_NOT_EXIST: 'Event does not exist.',
               ERROR_EVENT_NOT_STARTED: "Event is not started.",
               ERROR_EVENT_NOT_STOPPED: "Event is not stopped.",
               ERROR_SCHEDULER: 'Error with the scheduler.',
               ERROR_STORE: 'Error with the store.',
               ERROR_TYPE_NOT_EXIST: "Event's type does not exist.",
               ERROR_PARAMETER_NOT_EXIST: "Event's parameter does not exist.",
               ERROR_STATUS_NOT_EXIST: "Event's status does not exist.",
               ERROR_REST: 'Error with REST. But Event is created.',
               }

class EarthStore():
    """
    Store the events in the filesystem. We use a ConfigParser file per eventype/delays.
    Sections [Event] [Stats] [Delays]
    """
    def __init__(self, log, data_dir):
        """
        Initialise the store engine. Create the directory if necessary.

        :param log: a logger
        :type log: Logger
        :param data_dir: the data directory where store the cron files
        :type data_dir: str

        """
        self._log = log
        self._data_files_dir = data_dir
        self._log.info("EarthStore.__init__ : Use directory %s to store events." % self._data_files_dir)
        self._badfields = ["action", "starttime", "uptime", ]
        self._statfields = ["current", "runs", "createtime", "runtime"]

    def load_all(self, add_job_cb):
        """
        Load all events from the filesystem. Parse all the *.ext files
        in directory and call the callback method to add it to the earth's events.

        :param add_job_cb: callback to the function who add the job to CronJobs
        :type add_job_cb: function

        """
        for jobfile in glob.iglob(self._data_files_dir+"/*" + self._get_fileext()) :
            config = ConfigParser.ConfigParser()
            config.read(jobfile)
            self._log.debug("EarthStore.load_all : Load event from %s" % jobfile)
            data = dict()
            for option in config.options('Event'):
                data[option] = config.get('Event', option)
            for option in config.options('Stats'):
                data[option] = config.get('Stats', option)
# Implement it in the future
            err = add_job_cb(data['type'], data['delay'], data)
            if err != ERROR_NO :
                self._log.warning("Can't load job from %s : error=%s" % \
                    (jobfile,CRONERRORS[err]))

    def count_files(self):
        """
        Count the number of events in the data directory.

        :returns: the number of files in the directory
        :rtype: int

        """
        cnt = 0
        for jobfile in glob.iglob(self._data_files_dir+"/*" + self._get_fileext()) :
            cnt += 1
        return cnt

    def _get_fileext(self):
        """
        Return the file extension associated to an event.

        :param event: : the event name
        :type event: : string
        :returns: the filename of the event
        :rtype: str

        """
        return ".evt"

    def _get_filename(self, event, delay):
        """
        Return the filename associated to an event.

        :param event: : the event name
        :type event: : string
        :returns: the filename of the event
        :rtype: str

        """
        filename = "%s%s%s" % (event, delay, self._get_fileext())
        #filename = filename.replace("+","p")
        #filename = filename.replace("-","m")
        return os.path.join(self._data_files_dir, filename )

    def on_start(self, event, delay, data):
        """
        Must be called when a job is started. Is also (indirectly)
        called when a job is resumed.

        :param event: : the event name
        :type event: : string
        :param delay: : the delay
        :type delay: : string
        :param data : the parameters of the event
        :type data : dict()

        """
        try:
            self._log.debug("EarthStore.on_start : %s%s" % (event, delay))
            config = ConfigParser.ConfigParser()
            if os.path.isfile(self._get_filename(event, delay)):
                #The file already exists. We are in resume case.
                config.read(self._get_filename(event, delay))
            delay_idx = 1
            #data['state'] = "started"
            #data['starttime'] = datetime.datetime.today().strftime("%x %X")
            if not config.has_section('Event'):
                config.add_section('Event')
            if not config.has_section('Stats'):
                config.add_section('Stats')
            for key in data:
                if key in self._statfields:
                    config.set('Stats', key, data[key])
                elif key in self._badfields:
                    pass
                else :
                    config.set('Event', key, data[key])
            with open(self._get_filename(event, delay), 'w') \
                    as configfile:
                config.write(configfile)
            configfile.close
            return ERROR_NO
        except:
            self._log.error("EarthStore.on_start : Exception " + traceback.format_exc())
            return ERROR_STORE

    def on_halt(self, event, delay):
        """
        Must be called when a job is halted. It deletes the file
        associated to the job.

        :param event: : the event name
        :type event: : string
        :param delay: : the delay
        :type delay: : string
        :param data : the parameters of the event
        :type data : dict()

        """
        try:
            self._log.debug("EarthStore.on_halt : %s%s" % (event, delay))
            filename = self._get_filename(event, delay)
            if os.path.isfile(filename):
                os.remove(filename)
            return ERROR_NO
        except:
            self._log.error("EarthStore.on_halt : " + traceback.format_exc())
            return ERROR_STORE

    def on_stop(self, event, delay, state, runs, runtime):
        """
        Must be called when a job is stopped.

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : string
        :param runs: : the number of runs
        :type runs: : int
        :param runtime : the runtime of the event
        :type runtime : int

        """
        try:
            self._log.debug("EarthStore.on_stop : %s%s" % (event, delay))
            config = ConfigParser.ConfigParser()
            config.read(self._get_filename(event, delay))
            config.set('Stats', "current", state)
            config.set('Stats', "runs", runs)
            config.set('Stats', "runtime", runtime)
            with open(self._get_filename(event, delay), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._log.error("EarthStore.on_stop : " + traceback.format_exc())
            return ERROR_STORE

    def on_close(self, event, delay, runs, runtime):
        """
        Must be called when a job is closed : the plugin is stopped.

        :param event: : the event name
        :type event: : string
        :param delay: : the delay
        :type delay: : string
        :param runs: : the number of runs
        :type runs: : int
        :param runtime : the runtime of the event
        :type runtime : int

        """
        try:
            self._log.debug("EarthStore.on_close : event %s%s" % (event, delay))
            config = ConfigParser.ConfigParser()
            config.read(self._get_filename(event, delay))
            config.set('Stats', "runs", runs)
            config.set('Stats', "runtime", runtime)
            with open(self._get_filename(event, delay), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._log.error("EarthStore.on_close : " + traceback.format_exc())
            return ERROR_STORE

    def on_resume(self, event, delay):
        """
        Must be called when a job is resumed.

        :param event: : the event name
        :type event: : string
        :param delay: : the delay
        :type delay: : string

        """

    def on_fire(self, event, delay, runs):
        """
        Must be called when a job is fired.

        :param event: : the event name
        :type event: : string
        :param delay: : the delay
        :type delay: : string
        :param runs: : the number of runs
        :type runs: : int

        """
        try:
            self._log.debug("EarthStore.on_fire : job %s" % (event, delay))
            config = ConfigParser.ConfigParser()
            config.read(self._get_filename(event, delay))
            config.set('Stats', "runs", runs)
            with open(self._get_filename(event, delay), 'w') as configfile:
                config.write(configfile)
                configfile.close
            return ERROR_NO
        except:
            self._log.error("EarthStore.on_fire : " + traceback.format_exc())
            return ERROR_STORE


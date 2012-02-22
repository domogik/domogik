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

A client librairy to speak with the cron plugin, via xpl language


@author: Sebastien GALLET <sgallet@gmail.com>
@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from threading import Event
#from domogik.common import logger
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
#from domogik.common.configloader import Loader
import traceback
import datetime

ERROR_NO = 0
ERROR_PARAMETER = 1
ERROR_DEVICE_EXIST = 10
ERROR_DEVICE_NOT_EXIST = 11
ERROR_DEVICE_NOT_STARTED = 12
ERROR_DEVICE_NOT_STOPPED = 13
ERROR_SCHEDULER = 20
ERROR_NOT_IMPLEMENTED = 30

CRONERRORS = { ERROR_NO: 'No error',
               ERROR_PARAMETER: 'Missing or wrong parameter',
               ERROR_DEVICE_EXIST: 'Device already exist',
               ERROR_DEVICE_NOT_EXIST: 'Device does not exist',
               ERROR_DEVICE_NOT_STARTED: "Device is not started",
               ERROR_DEVICE_NOT_STOPPED: "Device is not stopped",
               ERROR_SCHEDULER: 'Error with the scheduler',
               }

class CronQuery():
    '''
    Query throw xPL network to get a config item
    '''
    def __init__(self, xpl, log):
        '''
        Init the query system and connect it to xPL network
        @param xpl : the XplManager instance (usually self.myxpl)
        @param log : a Logger instance (usually took from self.log))
        '''
        self.log = log
        self.__myxpl = xpl
        self.log.debug("Init config query instance")
        self._keys = {}
        self._listens = {}
        self._result = None
        self.parameters = ["parameter0", "parameter1"]
        self.values = ["valueon", "valueoff"]

    def query(self, device, configmess, extkey=None):
        '''
        Ask the config system for the value. Calling this function will make
        your program wait until it got an answer

        @param technology : the technology of the item requesting the value,
        must exists in the config database
        @param element : the name of the element which requests config, None if
        it's a technolgy global parameter
        @param key : the key to fetch corresponding value, if it's an empty string,
        all the config items for this technology will be fetched
        '''
        liste = Listener(self._query_cb, self.__myxpl, {'schema': 'timer.basic',
                                                    'xpltype': 'xpl-trig',
                                                    'device': device
                                                    })
        self._keys['device'] = Event()
        self._listens['device'] = liste
        self.__myxpl.send(configmess)
        if 'device' in self._keys:
            try:
                self._keys['device'].wait(10)
                if not self._keys['device'].is_set():
                    self.log.error("No answer received for device=%s" \
                       % (device))
                    raise RuntimeError("No answer received for device=%s,  \
                        check your cron xpl setup" % (device))
            except KeyError:
                pass
        if 'error' not in self._result:
            if extkey != None:
                #print "extkey=%s"%extkey
                #print "result=%s"%self._result
                if extkey in self._result:
                    #print "extkey=%s"%self._result[extkey]
                    return self._result[extkey]
                else:
                    return False
            return True
        else:
            self.log.error("Error %s when communicating device=%s" % \
                (self._result['errorcode'], device))
            self.log.error("%s : %s" % \
                (self._result['errorcode'], self._result['error']))
            return False

    def _query_cb(self, message):
        '''
        Callback to receive message after a query() call
        @param message : the message received
        '''
        result = message.data
        device = None
        if 'device' in message.data:
            device = message.data['device']
        #print "result=%s"%result
        for resp in self._keys:
            if resp in result:
                self.log.debug("Timer value received : device=%s" % (device))
                res = self._keys.pop(resp)
                self._listens[resp].unregister()
                del self._listens[resp]
                self._result = result
                res.set()
                break

    def nested_key(self, key):
        '''
        Callback to receive message after a query() call
        @param message : the message received
        '''
        return "nst-%s" % key

    def start_job(self, device, configmess, nstmess):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param configmess : the XPL configuration message to send to the plugin
        @param nstMess : the XPL message which will be sent by the cron job
        '''
        if configmess == None or nstmess == None or device == None:
            return False
        configmess.add_data({self.nested_key("schema"):nstmess.schema})
        configmess.add_data({self.nested_key("xpltype"):nstmess.type})
        for key in nstmess.data:
            configmess.add_data({self.nested_key(key):nstmess.data[key]})
        try:
            res = self.query(device, configmess)
            return res
        except:
            self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def start_timer_job(self, device, nstmess, frequence, duration=0):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param frequence : the frequence of the signal (in seconds).
        '''
        if frequence == 0:
            return False
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"action" : "start"})
        configmess.add_data({"device" : device})
        configmess.add_data({"devicetype" : "timer"})
        configmess.add_data({"frequence" : frequence})
        if duration != 0:
            configmess.add_data({"duration" : duration})
        return self.start_job(device, configmess, nstmess)

    def start_date_job(self, device, nstmess, sdate):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param sdate : the date/time to run the job at
        '''
        if sdate == None:
            return False
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"devicetype" : "date"})
        configmess.add_data({"device" : device})
        configmess.add_data({"action" : "start"})
        configmess.add_data({"date" : self.date_to_xpl(sdate)})
        return self.start_job(device, configmess, nstmess)

    def start_interval_job( self, device, nstmess, weeks=0, days=0, hours=0,
                          minutes=0, seconds=0, startdate=None):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param weeks: number of weeks to wait
        @param days: number of days to wait
        @param hours: number of hours to wait
        @param minutes: number of minutes to wait
        @param seconds: number of seconds to wait
        @param startdate: when to first execute the job and start the
               counter (default is after the given interval)
        '''
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"devicetype" : "interval"})
        configmess.add_data({"device" : device})
        configmess.add_data({"action" : "start"})
        cont = False
        if weeks != 0:
            configmess.add_data({"weeks" : weeks})
            cont = True
        if days != 0:
            configmess.add_data({"days" : days})
            cont = True
        if hours != 0:
            configmess.add_data({"hours" : hours})
            cont = True
        if minutes != 0:
            configmess.add_data({"minutes" : minutes})
            cont = True
        if seconds != 0:
            configmess.add_data({"seconds" : seconds})
            cont = True
        if startdate != None:
            configmess.add_data({"startdate" : self.date_to_xpl(startdate)})
        if cont == False:
            return ERROR_PARAMETER
        return self.start_job(device, configmess, nstmess)

    def start_cron_job( self, device, nstmess, year=None, month=None,
                      day=None, week=None, dayofweek=None, hour=None,
                      minute=None, second=None, startdate=None):

        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param year: year to run on
        @param month: month to run on
        @param day: day of month to run on
        @param week: week of the year to run on
        @param dayofweek: weekday to run on (0 = Monday)
        @param hour: hour to run on
        @param second: second to run on
        @param startdate: when to first execute the job and start the
               counter (default is after the given interval)
       '''
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"devicetype" : "cron"})
        configmess.add_data({"device" : device})
        configmess.add_data({"action" : "start"})
        cont = False
        if year != None:
            configmess.add_data({"year" : year})
            cont = True
        if month != None:
            configmess.add_data({"month" : month})
            cont = True
        if day != None:
            configmess.add_data({"day" : day})
            cont = True
        if week != None:
            configmess.add_data({"week" : week})
            cont = True
        if dayofweek != None:
            configmess.add_data({"dayofweek" : dayofweek})
            cont = True
        if hour != None:
            configmess.add_data({"hour" : hour})
            cont = True
        if minute != None:
            configmess.add_data({"minute" : minute})
            cont = True
        if second != None:
            configmess.add_data({"second" : second})
            cont = True
        if startdate != None:
            configmess.add_data({"startdate" : self.date_to_xpl(startdate)})
        if cont == False:
            return ERROR_PARAMETER
        return self.start_job(device, configmess, nstmess)

    def start_hvac_job( self, device, nstmess, params={}, timers={}):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param params : parameters in a dict with valueon and valueoff fields
        @param timers: the list of timers to use
       '''
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"devicetype" : "hvac"})
        configmess.add_data({"device" : device})
        configmess.add_data({"action" : "start"})
        cont = True
        i = 0
        if params != None:
            for param in params:
                #try:
                configmess.add_data({"parameter"+str(i) : param})
                for value in params[param]:
                    configmess.add_data({value+str(i) : \
                        params[param][value]})
                i = i+1
                #except:
                #    cont=False
        if cont and len(timers)>0 :
            for key in timers:
                configmess.add_data({key : timers[key]})
        else:
            cont = False
        if cont == False:
            return ERROR_PARAMETER
        return self.start_job(device, configmess, nstmess)

    def start_alarm_job( self, device, nstmess, params={}, alarms=list()):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param params : parameters in a dict with valueon and valueoff fields
        @param alarms : the list of alarms to use
       '''
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"devicetype" : "alarm"})
        configmess.add_data({"device" : device})
        configmess.add_data({"action" : "start"})
        cont = True
        i = 0
        if params != None:
            for param in params:
                #try:
                configmess.add_data({"parameter"+str(i) : param})
                for value in params[param]:
                    configmess.add_data({value+str(i) : \
                        params[param][value]})
                i = i+1
                #except:
                #    cont=False
        if alarms != None:
            for key in alarms:
                configmess.add_data({"alarm" : key})
        else:
            cont = False
        if cont == False:
            return ERROR_PARAMETER
        return self.start_job(device, configmess, nstmess)

    def start_dawn_alarm_job( self, device, nstmess, params={}, alarms=list()):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param params : parameters in a dict with valueon and valueoff fields
        @param alarms : the list of alarms to use
       '''
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"devicetype" : "dawnalarm"})
        configmess.add_data({"device" : device})
        configmess.add_data({"action" : "start"})
        cont = True
        i = 0
        if params != None:
            for param in params:
                #try:
                configmess.add_data({"parameter"+str(i) : param})
                for value in params[param]:
                    configmess.add_data({value+str(i) : \
                        params[param][value]})
                i = i+1
                #except:
                #    cont=False
        if alarms != None:
            for key in alarms:
                configmess.add_data({"alarm" : key})
        else:
            cont = False
        if cont == False:
            return ERROR_PARAMETER
        return self.start_job(device, configmess, nstmess)

    def stop_job(self, device, extkey=None):
        """
        Stop a job to the cron plugin. The cron job could be restarted via a
        resume command.
        @param device : the name of the timer
        """
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"action" : "stop"})
        configmess.add_data({"device" : device})
        try :
            res = self.query(device, configmess, extkey=extkey)
            return res
        except:
            self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def resume_job(self, device, extkey=None):
        """
        Resume a previous stopped job to the cron plugin.*
        @param device : the name of the timer
        """
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"action" : "resume"})
        configmess.add_data({"device" : device})
        try:
            res = self.query(device, configmess, extkey=extkey)
            return res
        except:
            self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def halt_job(self, device, extkey=None):
        """
        Stop a job and delete the device.
        @param device : the name of the timer
        """
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"action" : "halt"})
        configmess.add_data({"device" : device})
        try:
            res = self.query(device, configmess, extkey=extkey)
            #print res
            return res
        except:
            self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def status_job(self, device, extkey=None):
        """
        Get the status of a job to the cron plugin.
        @param device : the name of the timer
        """
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"action" : "status"})
        configmess.add_data({"device" : device})
        try:
            res = self.query(device, configmess, extkey=extkey)
            return res
        except:
            self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def date_from_xpl(self, xpldate):
        """
        Tranform an XPL date "yyyymmddhhmmss" to datetime
        form
        """
        yy = int(xpldate[0:4])
        mo = int(xpldate[4:6])
        dd = int(xpldate[6:8])
        hh = int(xpldate[8:10])
        mm = int(xpldate[10:12])
        ss = int(xpldate[12:14])
        return datetime.datetime(yy, mo, dd, hh, mm, ss)

    def date_to_xpl(self, sdate):
        """
        Tranform an datetime date to an xpl one "yyyymmddhhmmss"
        form
        """
        hh = "%.2i" % sdate.hour
        mm = "%.2i" % sdate.minute
        ss = "%.2i" % sdate.second
        yy = sdate.year
        mo = "%.2i" % sdate.month
        dd = "%.2i" % sdate.day
        xpldate = "%s%s%s%s%s%s" % (yy, mo, dd, hh, mm, ss)
        return xpldate


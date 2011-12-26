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

from domogik.common import logger
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import Loader


class cronQuery():
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
        self._l = {}
        self._result = None

    def __del__(self):
        print("End query")

    def query(self, device, configMess,extkey=None):
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
        l = Listener(self._query_cb, self.__myxpl, {'schema': 'timer.basic',
                                                    'xpltype': 'xpl-trig',
                                                    'device': device
                                                    })
        self._keys['device'] = Event()
        self._l['device'] = l
        self.__myxpl.send(configMess)
        if 'device' in self._keys:
            try:
                self._keys['device'].wait(10)
                if not self._keys['device'].is_set():
                    self.log.error("No answer received for device=%s" % (device))
                    raise RuntimeError("No answer received for device=%s, check your cron xpl setup" % (device))
                    return False
            except KeyError:
                pass
        if 'error' not in self._result:
            if extkey!=None:
                #print "extkey=%s"%extkey
                #print "result=%s"%self._result
                if extkey in self._result:
                    #print "extkey=%s"%self._result[extkey]
                    return self._result[extkey]
                else:
                    return False
            return True
        else:
            self.log.error("Error %s when communicating device=%s" % (self._result['errorcode'],device))
            self.log.error("%s : %s" % (self._result['errorcode'],self._result['error']))
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
        for r in self._keys:
            if r in result:
                self.log.debug("Timer value received : device=%s" % (device))
                res = self._keys.pop(r)
                self._l[r].unregister()
                del self._l[r]
                self._result = result
                res.set()
                break

    def nestedKey(self, key):
        return "nst-%s"%key

    def startJob(self, device, configMess, nstMess):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param configMess : the XPL configuration message to send to the plugin
        @param nstMess : the XPL message which will be sent by the cron job
        '''
        if configMess==None or nstMess==None or device==None:
            return False
        configMess.add_data({self.nestedKey("schema"):nstMess.schema})
        configMess.add_data({self.nestedKey("xpltype"):nstMess.type})
        for key in nstMess.data:
                configMess.add_data({self.nestedKey(key):nstMess.data[key]})
        res=self.query(device, configMess)
        return res

    def startTimerJob(self, device, nstMess, frequence, duration=0):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param frequence : the frequence of the signal (in seconds).
        '''
        if frequence==0:
            return false
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"action" : "start"})
        configMess.add_data({"device" : device})
        configMess.add_data({"devicetype" : "timer"})
        configMess.add_data({"frequence" : frequence})
        if duration!=0:
            configMess.add_data({"duration" : duration})
        return self.startJob(device, configMess, nstMess)

    def startDateJob(self, device, nstMess, sdate):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param sdate : the date/time to run the job at
        '''
        if sdate==None:
            return false
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"devicetype" : "date"})
        configMess.add_data({"device" : device})
        configMess.add_data({"action" : "start"})
        configMess.add_data({"date" : self.dateToXPL(sdate)})
        return self.startJob(device, configMess, nstMess)

    def startIntervalJob( self, device, nstMess, weeks=0,days=0,hours=0,
                          minutes=0,seconds=0,startdate=None):
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
        if sdate==None:
            return false
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"devicetype" : "interval"})
        configMess.add_data({"device" : device})
        configMess.add_data({"action" : "start"})
        ok=False
        if weeks != 0:
            configMess.add_data({"weeks" : weeks})
            ok=True
        if days != 0:
            configMess.add_data({"days" : days})
            ok=True
        if hours != 0:
            configMess.add_data({"hours" : hours})
            ok=True
        if minutes != 0:
            configMess.add_data({"minutes" : minutes})
            ok=True
        if seconds != 0:
            configMess.add_data({"seconds" : seconds})
            ok=True
        if startdate != None:
            startdate = self.dateToXPL(startdate)
        if ok==False:
            return ERROR_PARAMETER
        return self.startJob(device, configMess, nstMess)

    def startCronJob( self, device, nstMess, year=None,month=None,day=None,
                      week=None,dayofweek=None,hour=None,
                      minute=None,second=None,startdate=None):

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
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"devicetype" : "cron"})
        configMess.add_data({"device" : device})
        configMess.add_data({"action" : "start"})
        ok=False
        if year != None:
            configMess.add_data({"year" : year})
            ok=True
        if month != None:
            configMess.add_data({"month" : month})
            ok=True
        if day != None:
            configMess.add_data({"day" : day})
            ok=True
        if week != None:
            configMess.add_data({"week" : week})
            ok=True
        if dayofweek != None:
            configMess.add_data({"dayofweek" : dayofweek})
            ok=True
        if hour != None:
            configMess.add_data({"hour" : hour})
            ok=True
        if minute != None:
            configMess.add_data({"minute" : minute})
            ok=True
        if second != None:
            configMess.add_data({"second" : second})
            ok=True
        if startdate != None:
            startdate = self.dateToXPL(startdate)
        if ok==False:
            return ERROR_PARAMETER
        return self.startJob(device, configMess, nstMess)

    def startHvacJob( self, device, nstMess,
                      parameter0=None, valueon0=None,valueoff0=None,
                      parameter1=None, valueon1=None,valueoff1=None,
                      timers={}):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param parameter0 : the first parameter to include as key in return message
        @param valueon0 : the value of parameter0 in case of on
        @param valueoff0 : the value of parameter0 in case of on
        @param parameter1 : the second parameter to include as key in return message
        @param valueon1 : the value of parameter0 in case of on
        @param valueoff1 : the value of parameter0 in case of on
        @param timers: the list of timers to use
       '''
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"devicetype" : "hvac"})
        configMess.add_data({"device" : device})
        configMess.add_data({"action" : "start"})
        ok=True
        if parameter0 != None:
            configMess.add_data({"parameter0" : parameter0})
            ok=False
            if valueon0 != None and valueoff0 != None:
                configMess.add_data({"valueon0" : valueon0})
                configMess.add_data({"valueoff0" : valueoff0})
                ok=True
        if ok and parameter1 != None:
            configMess.add_data({"parameter1" : parameter1})
            ok=False
            if valueon1 != None and valueoff1 != None:
                configMess.add_data({"valueon1" : valueon1})
                configMess.add_data({"valueoff1" : valueoff1})
                ok=True
        if ok and len(timers)>0 :
            for key in timers:
                configMess.add_data({key : timers[key]})
        else:
            ok=False
        if ok==False:
            return ERROR_PARAMETER
        return self.startJob(device, configMess, nstMess)

    def startAlarmJob( self, device, nstMess,
                      parameter0=None, valueon0=None,valueoff0=None,
                      parameter1=None, valueon1=None,valueoff1=None,
                      alarms={}):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param parameter0 : the first parameter to include as key in return message
        @param valueon0 : the value of parameter0 in case of on
        @param valueoff0 : the value of parameter0 in case of on
        @param parameter1 : the second parameter to include as key in return message
        @param valueon1 : the value of parameter0 in case of on
        @param valueoff1 : the value of parameter0 in case of on
        @param alarms : the list of alarms to use
       '''
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"devicetype" : "alarm"})
        configMess.add_data({"device" : device})
        configMess.add_data({"action" : "start"})
        ok=True
        if parameter0 != None:
            configMess.add_data({"parameter0" : parameter0})
            ok=False
            if valueon0 != None and valueoff0 != None:
                configMess.add_data({"valueon0" : valueon0})
                configMess.add_data({"valueoff0" : valueoff0})
                ok=True
        if ok and parameter1 != None:
            configMess.add_data({"parameter1" : parameter1})
            ok=False
            if valueon1 != None and valueoff1 != None:
                configMess.add_data({"valueon1" : valueon1})
                configMess.add_data({"valueoff1" : valueoff1})
                ok=True
        if alarms!=None:
            for key in alarms:
                configMess.add_data({"alarm" : key})
        else:
            ok=False
        if ok==False:
            return ERROR_PARAMETER
        return self.startJob(device, configMess, nstMess)

    def startDawnAlarmJob( self, device, nstMess,
                          alarms={}):
        '''
        Add and start a job to the cron plugin
        @param device : the name of the timer
        @param nstMess : the XPL message which will be sent by the cron job
        @param parameter0 : the first parameter to include as key in return message
        @param valueon0 : the value of parameter0 in case of on
        @param valueoff0 : the value of parameter0 in case of on
        @param parameter1 : the second parameter to include as key in return message
        @param valueon1 : the value of parameter0 in case of on
        @param valueoff1 : the value of parameter0 in case of on
        @param alarms : the list of alarms to use
       '''
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"devicetype" : "dawnalarm"})
        configMess.add_data({"device" : device})
        configMess.add_data({"action" : "start"})
        ok=True
        if alarms!=None:
            for key in alarms:
                configMess.add_data({"alarm" : key})
        else:
            ok=False
        if ok==False:
            return ERROR_PARAMETER
        return self.startJob(device, configMess, nstMess)

    def stopJob(self, device,extkey=None):
        """
        Stop a job to the cron plugin. The cron job could be restarted via a
        resume command.
        @param device : the name of the timer
        """
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"action" : "stop"})
        configMess.add_data({"device" : device})
        res=self.query(device, configMess,extkey=extkey)
        return res

    def resumeJob(self, device,extkey=None):
        """
        Resume a previous stopped job to the cron plugin.*
        @param device : the name of the timer
        """
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"action" : "resume"})
        configMess.add_data({"device" : device})
        res=self.query(device, configMess,extkey=extkey)
        return res

    def haltJob(self, device,extkey=None):
        """
        Stop a job and delete the device.
        @param device : the name of the timer
        """
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"action" : "halt"})
        configMess.add_data({"device" : device})
        res=self.query(device, configMess,extkey=extkey)
        #print res
        return res

    def statusJob(self, device,extkey=None):
        """
        Get the status of a job to the cron plugin.
        @param device : the name of the timer
        """
        configMess = XplMessage()
        configMess.set_type("xpl-cmnd")
        configMess.set_schema("timer.basic")
        configMess.add_data({"action" : "status"})
        configMess.add_data({"device" : device})
        res=self.query(device, configMess,extkey=extkey)
        return res

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


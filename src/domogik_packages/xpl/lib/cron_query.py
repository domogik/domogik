# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

.. module:: cron_query

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

A client library to speak with the cron plugin, via xpl language

.. moduleauthor:: bibi21000 <bibi21000@gmail.com>
.. copyright:: (C) 2007-2012 Domogik project
.. license:: GPL(v3)
.. organization:: Domogik

Implements
==========
class CronQuery


"""
import datetime
from threading import Event
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import Loader
import traceback
import logging

def date_to_xpl(sdate):
    """
    Tranform an datetime date to an xpl one "yyyymmddhhmmss"
    form.

    @parameter sdate: The datetime to transform
    @return: A string representing the xpl date if everything \
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

class CronQuery():
    '''
    Query throw xPL network to get a config item
    '''
    def __init__(self, xpl, log = None):
        '''
        Init the query system and connect it to xPL network
        :param xpl: the XplManager instance (usually self.myxpl)
        :param log: a Logger instance (usually took from self.log))
        '''
        self.log = log
        self.__myxpl = xpl
        if self.log != None : self.log.debug("Init config query instance")
        self._keys = {}
        self._listens = {}
        self._result = None
        self.parameters = ["parameter0", "parameter1"]
        self.values = ["valueon", "valueoff"]
        # Check in config file is target is forced
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        if conf.has_key('query_xpl_timeout'):
            try:
                self.query_timeout = int(conf["query_xpl_timeout"])
                msg = "Set query timeout to '%s' from domogik.cfg" % self.query_timeout
                if self.log != None : self.log.debug(msg)
            except ValueError:
                #There is an error in domogik.cfg. Set it to default.
                self.query_timeout = 10
                msg = "Error in domogik.cfg. query_xpl_timeout ('%s') is not an integer." % conf["query_xpl_timeout"]
                if self.log != None : self.log.error(msg)
        else:
            #There is not option in domogik.cfg. Set it to default.
            self.query_timeout = 10

    def query(self, device, configmess, extkey=None):
        '''
        Ask the cron system for a device(job). Calling this function will make
        your program wait until it got an answer

        :param device: the device to query
        :param configmess: the name of the job which requests config, None if it's a technolgy global parameter
        :param extkey: the key to fetch corresponding value, if it's an empty string, all the config items for this technology will be fetched

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
                self._keys['device'].wait(self.query_timeout)
                if not self._keys['device'].is_set():
                    if self.log != None : self.log.error("No answer received for device=%s" % (device))
                    raise RuntimeError("No answer received for device=%s," % (device) +
                        "check your cron xpl setup")
            except KeyError:
                pass
        if 'error' not in self._result:
            if extkey != None:
                #print("extkey=%s"%extkey)
                #print("result=%s"%self._result)
                if extkey in self._result:
                    #print("extkey=%s"%self._result[extkey])
                    return self._result[extkey]
                else:
                    return False
            return True
        else:
            if self.log != None : self.log.debug("Error %s when communicating device=%s" % \
                (self._result['errorcode'], device))
            if self.log != None : self.log.debug("%s : %s" % \
                (self._result['errorcode'], self._result['error']))
            return False

    def _query_cb(self, message):
        '''
        Callback to receive message after a query() call
        :param  message: the message received
        :type  message: XplMessage
        '''
        result = message.data
        device = None
        if 'device' in message.data:
            device = message.data['device']
        #print("result=%s"%result)
        for resp in self._keys:
            if resp in result:
                if self.log != None : self.log.debug("Timer value received : device=%s" % (device))
                res = self._keys.pop(resp)
                self._listens[resp].unregister()
                del self._listens[resp]
                self._result = result
                res.set()
                break

    def nested_key(self, key):
        '''
        Callback to receive message after a query() call

        :param key: the key to change
        :type key: the key to change
        :return: the corresponding nested key
        :rtype: str

        '''
        return "nst-%s" % key

    def start_job(self, device, configmess, nstmess):
        '''
        Add and start a job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            if self.log != None : self.log.debug("cron_query : %s" % (traceback.format_exc()))
            return False

    def start_timer_job(self, device, nstmess, frequence, duration=0):
        '''
        Add and start a job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :param frequence: int
        :type frequence: the frequence of the signal (in seconds).
        :param duration: the number of pulse to live.
        :type duration: int
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
        Add and start a date job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :param  sdate: the date/time to run the job
        :type  sdate: datetime
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

        '''
        if sdate == None:
            return False
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"devicetype" : "date"})
        configmess.add_data({"device" : device})
        configmess.add_data({"action" : "start"})
        configmess.add_data({"date" : date_to_xpl(sdate)})
        return self.start_job(device, configmess, nstmess)

    def start_interval_job( self, device, nstmess, weeks=0, days=0, hours=0,
                          minutes=0, seconds=0, duration=0, startdate=None):
        '''
        Add and start an interval job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :param  weeks: number of weeks to wait
        :type  weeks: int
        :param  days: number of days to wait
        :type  days: int
        :param  hours: number of hours to wait
        :type  hours: int
        :param  minutes: number of minutes to wait
        :type  minutes: int
        :param  seconds: number of seconds to wait
        :type  seconds: int
        :param  startdate: the job will be start at this date/time
        :type startdate: datetime
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            configmess.add_data({"startdate" : date_to_xpl(startdate)})
        if cont == False:
            return "Halted"
        return self.start_job(device, configmess, nstmess)

    def start_cron_job( self, device, nstmess, year=None, month=None,
                      day=None, week=None, dayofweek=None, hour=None,
                      minute=None, second=None, startdate=None):

        '''
        Add and start a job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :param  year: year to run on
        :type  year: int
        :param  month: month to run on
        :type  month: int
        :param  day: day of month to run on
        :type  day: int
        :param  week: week of the year to run on
        :type  week: int
        :param  dayofweek: weekday to run on (0 = Monday)
        :type  dayofweek: int
        :param  hour: hour to run on
        :type  hour: int
        :param  second: second to run on
        :type  second: int
        :param  startdate: the job will be start at this date/time
        :type startdate: datetime
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            configmess.add_data({"startdate" : date_to_xpl(startdate)})
        if cont == False:
            return "Halted"
        return self.start_job(device, configmess, nstmess)

    def start_hvac_job( self, device, nstmess, params={}, timers={}):
        '''
        Add and start a job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :param params: parameters in a dict with valueon and valueoff fields
        :type params: dict()
        :param timers: the list of timers to use
        :param timers: list()
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            return "halted"
        return self.start_job(device, configmess, nstmess)

    def start_alarm_job( self, device, nstmess, params={}, alarms=list()):
        '''
        Add and start a job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :param params: parameters in a dict with valueon and valueoff fields
        :type params: dict()
        :param alarms: the list of alarms to use
        :param alarms: list()
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            return "Halted"
        return self.start_job(device, configmess, nstmess)

    def start_dawn_alarm_job( self, device, nstmess, params={}, alarms=list()):
        '''
        Add and start a job to the cron plugin

        :param device: the device/job to start
        :type device: str
        :param configmess: the XPL configuration message to send to the plugin
        :type configmess: XplMessage
        :param nstMess: the XPL message which will be sent by the cron job
        :type nstMess: XplMessage
        :param params: parameters in a dict with valueon and valueoff fields
        :type params: dict()
        :param alarms: the list of alarms to use
        :param alarms: list()
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            return "Halted"
        return self.start_job(device, configmess, nstmess)

    def stop_job(self, device, extkey="state"):
        """
        Stop a job to the cron plugin. The cron job could be restarted via a
        resume command.

        :param device: the device/job to stop
        :type device: str
        :param extkey: the message key to look for ("state" by default)
        :type extkey: str
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            if self.log != None : self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def resume_job(self, device, extkey="state"):
        """
        Resume a previous stopped job to the cron plugin.*

        :param device: the device/job to resume
        :type device: str
        :param  extkey: the message key to look for ("state" by default)
        :type  extkey: str
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            if self.log != None : self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def halt_job(self, device, extkey="state"):
        """
        Stop a job and delete the device. Job is permanently deleted.

        :param device: the device/job to halt
        :type device: str
        :param  extkey: the message key to look for ("state" by default)
        :type  extkey: str
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            if self.log != None : self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def status_job(self, device, extkey="state"):
        """
        Get the status of a job to the cron plugin.

        :param device: the device/job to get status
        :type device: str
        :param  extkey: the message key to look for ("state" by default)
        :type  extkey: str
        :return: the state sent by cron plugin : "started"|"stopped"|"halted"
        :rtype: str

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
            if self.log != None : self.log.error("cron_query : %s" % (traceback.format_exc()))
            return False

    def is_running_server(self):
        """
        Check that the cron plugin is running. We simply get status of an arbitray job. Cron will reposnd that this job is halted.

        :return: the state of the cron plugin
        :rtype: bool

        """
        configmess = XplMessage()
        configmess.set_type("xpl-cmnd")
        configmess.set_schema("timer.basic")
        configmess.add_data({"action" : "status"})
        configmess.add_data({"device" : "cron"})
        try:
            res = self.query("cron", configmess, "state")
            return True
        except:
            return False

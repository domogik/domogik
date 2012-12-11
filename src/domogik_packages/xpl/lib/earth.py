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
XPL earth events (dawn, dusk, zenith, ...) server.

Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import logging
import traceback
import ephem
import datetime
import threading
from threading import Timer
from pympler.asizeof import asizeof
from domogik.xpl.common.xplmessage import XplMessage
from domogik_packages.xpl.lib.earth_tools import *
from domogik_packages.xpl.lib.cron_query import CronQuery

logging.basicConfig()

#MEMORY USAGE
MEMORY_PLUGIN = 1
MEMORY_API = 2
MEMORY_SCHEDULER = 3
MEMORY_DATA = 4
MEMORY_STORE = 5

class EarthEvents():
    """
    Encapsulate the EarthEvents.
    """
    def __init__(self, api):
        """
        Init the EarthEvents container

        @param api:

        """
        self._api = api
        self.store = EarthStore(self._api.log, self._api.data_files_dir)

        self.data = dict()
        self.device_types = dict()
        self.device_status = dict()
        self.params = dict()

        self._dawndusk = DawnDusk(self)
        self.register_type ("dawn", self._dawndusk.get_next_dawn)
        self.register_type ("dusk", self._dawndusk.get_next_dusk)
        self.register_status (["dawn", "dusk"], "daynight", self._dawndusk.check_daynight)
        self.register_status (["dawn", "dusk"], "dawndusk", self._dawndusk.check_dawndusk)
        self.register_parameter ("dawndusk", True, self._dawndusk.check_param)

        self._moonphases = MoonPhases(self)
        self.register_type ("fullmoon", self._moonphases.get_next_full_moon)
        self.register_type ("newmoon", self._moonphases.get_next_new_moon)
        self.register_type ("firstquarter", self._moonphases.get_next_first_quarter_moon)
        self.register_type ("lastquarter", self._moonphases.get_next_last_quarter_moon)
        self.register_status (["fullmoon", "newmoon", "firstquarter", "lastquarter"], "moonphase", self._moonphases.check_moonphase)

    def count_events(self):
        '''
        Count he number of events in memory.

        '''
        nb_events = 0
        for event in self.data :
            for delay in self.data[event] :
                nb_events += 1
        return nb_events

    def load_store(self):
        '''
        Load events from store.

        '''
        self.store.load_all(self.add_event)
        self._api.log.info("Load %s events from store." % self.count_events())

    def register_type(self, etype, callback):
        '''
        Register a new type of event. You must call it before registering a status.

        :param type: The type to register
        :type type: str
        :param callback: The callback funtion to use with the type
        :type callback: function

        '''
        if etype in self.device_types:
            raise KeyError("Type %s already registered in EarthEvents." % etype)
        self.device_types[etype] = { "callback" : callback,
                                     "status" : set() }
        return True

    def register_status(self, types, status, callback):
        '''
        Register a new status.

        :param types: The types to register the status with
        :type types: set
        :param status: The status to register
        :type status: str
        :param callback: The callback funtion to use with the type
        :type callback: function

        '''
        for etype in types:
            if etype not in self.device_types:
                raise KeyError("Type %s not registered in EarthEvents." % etype)
            self.device_types[etype]["status"].add(status)
        if status in self.device_status:
            raise KeyError("Status %s already registered in EarthEvents." % status)
        self.device_status[status] = { "callback" : callback, "value" : None }
        return True

    def set_status(self, status, value):
        '''
        Update a status.

        :param status: The status to register
        :type status: str
        :param value: The new value
        :type value: str
        :returns: True if the status was updated, False otherwise
        :rtype: bool

        '''
        if status not in self.device_status:
            raise KeyError("Status %s not registered in EarthEvents." % status)
        self.device_status[status]["value"] = value
        return True

    def set_param(self, param, value):
        '''
        Update a param.

        :param param: The param to register
        :type param: str
        :param value: The new value
        :type value: str
        :param callback: The callback to check the value
        :type callback: function
        :returns: True if the param was updated, False otherwise
        :rtype: bool

        '''
        if param in self.params:
            if self.params[param]["callback"](value) :
                self.params[param]["value"] = value
                return True
        return False

    def register_parameter(self, param, value, callback):
        '''
        Register a new parameter. A parameter is used by extensions
        to modifiy their comportement.
        Parameters can be updated by xpl.

        :param param: The parameter to register
        :type param: : set
        :param value: : The default value of the parameter
        :type value: : str

        '''
        if param in self.params:
            raise KeyError("Param %s already registered in EarthEvents." % param)
        self.params[param] = {"callback" : callback, "value" : value}
        return True

    def memory_usage(self, which):
        '''
        Return the memory used by an object

        :param which: : the param to get
        :type which: : int

        '''
        if which == 0 :
            data = []
            data.append("api : %s items, %s bytes" % (1, asizeof(self)))
            data.append("events : %s items, %s bytes" % (len(self.data), asizeof(self.data)))
            data.append("store : %s items, %s bytes" % (1, asizeof(self.store)))
            return data
        else:
            if which == MEMORY_PLUGIN:
                return 0, 0
            elif which == MEMORY_API:
                return 1, asizeof(self)
            elif which == MEMORY_DATA:
                return len(self.data), asizeof(self.data)
            elif which == MEMORY_STORE:
                return 1, asizeof(self.store)
        return None

    def close_all(self):
        """
        Close all jobs

        """
        for event in self.data:
            for delay in self.data[event]:
                retstore = self.store.on_close(event, delay, \
                  self.data[event][delay]["runs"], \
                  self.get_run_time(event, delay))
                retcron = self._api.cronquery.status_job(self.get_name(event, delay))
                if retcron != True :
                    self._api.cronquery.stop_job(self.get_name(event, delay))
                if retstore != ERROR_NO :
                    return ERROR_STORE
                if retcron != True :
                    return ERROR_SCHEDULER
        return ERROR_NO

    def stop_event(self, event, delay):
        """
        Stop an avent

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str

        """
        evt = self.get_event(event, delay)
        if evt != None:
            retcron = self._api.cronquery.stop_job(self.get_name(event, delay))
            newruntime = self.get_full_run_time(event, delay)
            evt['current'] = "stopped"
            evt['runtime'] = newruntime
            #evt2 = self.get_event(event, delay)
            #print "evt : %s" % evt2
            retstore = self.store.on_stop(event, delay, evt['current'], evt['runs'], newruntime)
            if retstore != ERROR_NO :
                return ERROR_STORE
            if retcron != True :
                return ERROR_SCHEDULER
            return ERROR_NO
        else:
            return ERROR_EVENT_NOT_EXIST

    def halt_event(self, event, delay):
        """
        Stop and remove an event

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str

        """
        evt = self.get_event(event, delay)
        if evt != None:
            try :
                if evt['current'] == "started":
                    self.stop_event(event, delay)
            except :
                self._api.log.warning("Can't stop %s%s." % (event, delay))
            finally :
                self._api.log.warning("Delete %s%s and it's file." % (event, delay))
                retcron = True
                if self._api.cronquery.status_job(self.get_name(event, delay)) != "halted":
                    retcron = self._api.cronquery.halt_job(self.get_name(event, delay))
                retstore = self.store.on_halt(event, delay)
                del(self.data[event][delay])
                if len(self.data[event]) == 0:
                    del(self.data[event])
                if retstore != ERROR_NO :
                    return ERROR_STORE
                if retcron != True :
                    return ERROR_SCHEDULER
            return ERROR_NO
        else:
            return ERROR_EVENT_NOT_EXIST

    def resume_event(self, event, delay):
        """
        Resume an event

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str

        """
        evt = self.get_event(event, delay)
        if evt != None:
            if evt['current'] == "stopped":
                retcron = self._api.cronquery.resume_job(self.get_name(event, delay))
                if retcron == "halted" :
                    retcron = self.add_event_to_cron(event, delay)
                retstore = self.store.on_resume(event, delay)
                retstart = self.start_event(event, delay)
                if retstore != ERROR_NO :
                    return ERROR_STORE
                if retcron != True :
                    return ERROR_SCHEDULER
                return restart
            else:
                return ERROR_EVENT_NOT_STOPPED
        else:
            return ERROR_EVENT_NOT_EXIST

    def add_event_to_cron(self, event, delay):
        """
        Start an event.

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str

        """
        #Calculate the new event
        evt = self.get_event(event, delay)
        args = None
        if "args" in evt:
            args = evt["args"]
        #newdate = self.data[event][delay]["callback"](self._api.mycity, int(delay), args)
        newdate = self.device_types[event]["callback"](self._api.mycity, int(delay), args)
        if newdate != None :
            nstmess = XplMessage()
            nstmess.set_type("xpl-trig")
            nstmess.set_schema("earth.basic")
            nstmess.add_data({"type" : event})
            if delay != "0":
                nstmess.add_data({"delay" : delay})
            nstmess.add_data({"current" :  "fired"})
            evt["next"] = newdate.strftime("%x %X")
            #Add a cron job
            ret = self._api.cronquery.status_job(self.get_name(event, delay))
            if ret != "halted" :
                self._api.cronquery.halt_job(self.get_name(event, delay))
            ret = self._api.cronquery.start_date_job(self.get_name(event, delay), nstmess, newdate)
            return ret
        else :
            evt["current"] = "halted"
            return False

    def start_event(self, event, delay):
        """
        Start an event.

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str

        """
        evt = self.get_event(event, delay)
        if evt != None:
            if 'runs' not in evt:
                evt['runs'] = 0
            if 'next' not in evt:
                evt['next'] = "None"
            if 'delay' not in evt:
                evt['delay'] = "0"
            if 'runtime' not in evt:
                evt['runtime'] = 0
            if 'createtime' not in evt:
                evt['createtime'] = datetime.datetime.today().strftime("%x %X")
            evt['current'] = "started"
            cronret = self.add_event_to_cron(event, delay)
            #print "ret add_event_to_cron : %s" % ret
            if cronret == True:
                storeret = self.store.on_start(event, delay, evt)
            else :
                self.halt_event(event, delay)
                return ERROR_SCHEDULER
            if storeret != ERROR_NO :
                self.halt_event(event, delay)
                return ERROR_STORE
            return ERROR_NO
        else:
            return ERROR_EVENT_NOT_EXIST

    def add_event(self, event, delay, data):
        """
        Add an event and start it if needed

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str

        """
        if self.get_event(event, delay) != None:
            return ERROR_EVENT_EXIST
        if event not in self.data:
            self.data[event] = {}
        if delay == None:
            delay = "0"
        if delay not in self.data[event]:
            self.data[event][delay] = {}
        for key in data:
            if not key in self.data[event][delay]:
                self.data[event][delay][key] = data[key]
        self._api.log.debug("add_event : %s" % self.data[event][delay] )
        if ('action' in data and data['action'] == "start") \
          or ('current' in data and data['current'] == "started"):
            err = self.start_event(event, delay)
            return err
        else:
            return ERROR_NO

    def get_run_time(self, event, delay):
        """
        Get the runtime of a earth's event. This is the difference between the datetime
        the device has entered in started state and now

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str
        :returns: The number of seconds since the job starts. 0 if the job is stopped
        :rtype: int

        """
        event = self.get_event(event, delay)
        if event != None and event['current'] == "started":
            if 'starttime' in event:
                start = datetime.datetime.strptime(event['starttime'], "%x %X")
                elapsed = datetime.datetime.today()-start
                res = elapsed.days*86400 + elapsed.seconds
                return res
            else:
                return 0
        else:
            return 0

    def get_full_run_time(self, event, delay):
        """
        Get the total runtime of a earth's event.

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str
        :returns: The fullruntime
        :rtype: int

        """
        evt = self.get_event(event, delay)
        if evt != None :
            oldruntime = int(evt['runtime'])
            res = self.get_run_time(event, delay) + oldruntime
        return res

    def get_up_time(self, event, delay):
        """
        Get the uptime of an event. This is the difference between the datetime
        the event has been created and now

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str
        :returns: The uptime
        :rtype: int

        """
        evt = self.get_event(event, delay)
        if evt != None :
            start = datetime.datetime.strptime(evt['createtime'], "%x %X")
            elapsed = datetime.datetime.today()-start
            res = elapsed.days*86400 + elapsed.seconds
            return res
        else:
            return 0

    def get_label(self, event, delay, maxlen=0):
        """
        Get the label of an event.

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str
        :returns: The label
        :rtype: str

        """
        ret = ""
        evt = self.get_event(event, delay)
        if evt != None :
            ret = "%s%s" % (event, delay)
            return ret[:maxlen]
        else:
            return None

    def get_name(self, event, delay):
        """
        Get the name of an event.

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str
        :returns: The name
        :rtype: str

        """
        ret = None
        evt = self.get_event(event, delay)
        if evt != None :
            ret = "%s%s" % (event, delay)
        return ret

    def get_event(self, event, delay):
        """
        Return an event.

        :param event: : the event name
        :type event: : str
        :param delay: : the delay
        :type delay: : str
        :returns: the event
        :rtype: dict()

        """
        if event in self.data:
            if delay in self.data[event]:
                return self.data[event][delay]
        else:
            return None

    def get_list_events(self):
        """
        Return the list of event's names.

        :returns: The list of events
        :rtype: set()

        """
        res = set()
        for event in self.data:
            for delay in self.data[event]:
                res.add("%s%s" % (event, delay))
        return res

    def get_list_types(self):
        """
        Return the list of event's types available.

        :returns: The list of types
        :rtype: set()

        """
        res = set()
        for i in self.device_types:
            res.add(i)
        return res

    def get_list_params(self):
        """
        Return the list of event's params available.

        :returns: The list of params
        :rtype: set()

        """
        res = set()
        for i in self.params:
            res.add(i)
        return res

    def get_list_status(self):
        """
        Return the list of event's status available.

        :returns: The list of status
        :rtype: set()

        """
        res = set()
        for i in self.device_status:
            res.add(i)
        return res

class EarthException(Exception):
    """
    Earth exception
    """
    def __init__(self, value):
        """
        Earth exception
        """
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        """
        Earth exception
        """
        return repr(self.value)

class EarthAPI:
    """
    Earth API
    """

    def __init__(self, log, config, myxpl, data_dir, stop, hostname):
        """
        Constructor

        :param log: the logger
        :type log: Logger
        :param config: the config object to use
        :type config: Config
        :param myxpl: the xpl sender to use
        :type myxpl: xpl Manager
        :param data_dir: the data_dir where store the files
        :type data_dir: str
        :param stop: the stop method
        :type stop: threading.Event()
        :param hostname: the host name
        :type hostname: str

        """
        self.log = log
        self.myxpl = myxpl
        self.config = config
        self.data_files_dir = data_dir
        self._stop = stop
        self._hostname = hostname
        self.cronquery = CronQuery(self.myxpl, self.log)
        try:
            self.delay_sensor = int(self.config.query('earth', 'delay-sensor'))
            self.delay_stat = int(self.config.query('earth', 'delay-stat'))
            longitude = str(self.config.query('earth', 'longitude'))
            latitude = str(self.config.query('earth', 'latitude'))
            horizon = str(self.config.query('earth', 'horizon'))
            pressure = float(self.config.query('earth', 'pressure'))
            if latitude == None:
                latitude = "47.352"
            if longitude == None:
                longitude = "5.043"
            if horizon == None:
                horizon = "-6"
            if pressure == None:
                pressure = "0"
        except:
            latitude = "47.352"
            longitude = "5.043"
            horizon = "-6"
            pressure = 1010.0
            self.delay_stat = 300
            self.delay_sensor = 2
            error = "Can't get configuration from XPL : %s" %  (traceback.format_exc())
            self.log.error("__init__ : " + error)
            self.log.error("Continue with default values.")
        self._events_lock = threading.Semaphore()
        self.mycity = ephem.Observer()
        self.mycity.lat, self.mycity.lon = latitude, longitude
        self.mycity.horizon = horizon
        self.mycity.pressure = pressure
        try :
            self._events_lock.acquire()
            self.events = EarthEvents(self)
            self.events.load_store()
        finally :
            self._events_lock.release()
#        self.rest_server_ip = "127.0.0.1"
#        self.rest_server_port = "40405"
#        cfg_rest = Loader('rest')
#        config_rest = cfg_rest.load()
#        conf_rest = dict(config_rest[1])
#        self.rest_server_ip = conf_rest['rest_server_ip']
#        self.rest_server_port = conf_rest['rest_server_port']
#        self.rest = CronRest(self.rest_server_ip,self.rest_server_port,log)
        if (self.delay_sensor >0):
            self.timer_stat = Timer(self.delay_sensor, self.send_sensors)
            self.timer_stat.start()

    def get_list_acts(self):
        """
        Return the list of actions managed by the gateway.

        :returns: The list of actions
        :rtype: set()

        """
        return ['start', 'stop', 'resume', 'halt']

    def get_list_cmds(self):
        """
        Return the list of commands managed by the gateway.

        :returns: The list of commands
        :rtype: set()

        """
        return ['gateway', 'memory', 'set', 'get', 'list', 'info', 'status']

    def command_listener(self, myxpl, message):
        """
        Listen to earth.request messages.
        This messsge are for the gateway.

            earth.request
            {
            command=gateway
            }

            earth.request
            {
            command=memory
            }

            earth.request
            {
            command=set
            param=dawndusk
            value=true
            }

            earth.request
            {
            command=get
            param=dawndusk
            value=true
            }

            earth.request
            {
            command=list
            }

            earth.request
            {
            command=info
            type=dawn|dusk|sunrise|fullmoon|...
            [delay=+|-XXXXXX]
            }

            earth.request
            {
            command=status
            query=daynight
            }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager
        :param message: The XPL message
        :type message: XplMessage

        """
        self.log.debug("command_listener : Start ...")
        try:
            self._events_lock.acquire()
            command = None
            if 'command' in message.data:
                command = message.data['command']
            if command == None:
                self.log.debug("command_listener : No command found in message.")
                return
            else :
                self.log.debug("command_listener : Command '%s' found in message." % command)
            if command == "gateway" :
                self._send_event_gateway(myxpl)
            elif command == "memory" :
                self._send_memory(myxpl)
            elif command == "list" :
                self._send_event_list(myxpl)
            elif command == "info" :
                event = None
                if 'type' in message.data:
                    event = message.data['type']
                delay = "0"
                if 'delay' in message.data:
                    delay = message.data['delay']
                if event != None:
                    self._send_event_info(myxpl, event, delay)
                else:
                    self.log.debug("command_listener : No event found in message.")
                    return
            elif command == "status" :
                status = None
                if 'query' in message.data:
                    status = message.data['query']
                if status != None:
                    self._send_event_status(myxpl, status)
                else:
                    self.log.debug("command_listener : No status found in message.")
                    return
            elif command == "set" or command == "get":
                param = None
                if 'param' in message.data:
                    param = message.data['param']
                if param != None:
                    if command == "set" :
                        value = None
                        if 'value' in message.data:
                            value = message.data['value']
                        self.events.set_param(param, value)
                    self._send_event_parameter(myxpl, param)
                else:
                    self.log.debug("command_listener : No param found in message.")
                    return
            else :
                self.log.debug("command_listener : command %s not found." % command)
            self.log.debug("command_listener : Done :)")
        except:
            error = "Exception %s" % (traceback.format_exc())
            self.log.error("command_listener : " + error)
        finally :
            self._events_lock.release()

    def fired_listener(self, myxpl, message):
        """
        Listen to earth.basic fired messages.

        Listener( self.fired_listener, self.myxpl,
              {'schema': 'earth.basic', 'xpltype': 'xpl-trig', 'current': 'fired'})

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager
        :param message: The XPL message
        :type message: XplMessage

        """
        self.log.debug("fire_listener : Start ...")
        try :
            self._events_lock.acquire()
            event = None
            if 'type' in message.data:
                event = message.data['type']
            if event == None:
                self.log.error("fire_listener : Event type not found in message %s" % message)
            delay = "0"
            if 'delay' in message.data:
                delay = message.data['delay']
            evt = self.events.get_event(event, delay)
            if evt != None :
                ret = self.events.add_event_to_cron(event, delay)
                self._send_event_info(myxpl, event, delay)
                if ret == False:
                    self.log.error("fire_listener : Can't start cron job %s (%s)" % (self.events.get_name(event, delay), ret))
                #Call check_status callbacks
                for status in self.events.device_types[event]["status"]:
                    if self.events.device_status[status]["callback"](event, message):
                        #The status was updated. We send a message.
                        self._send_event_status(myxpl, status)
            else:
                self.log.debug("fire_listener : Can't find event in the event list.")
        finally :
            self._events_lock.release()
        self.log.debug("fire_listener : Done :)")

    def action_listener(self, myxpl, message):
        """
        Listen to earth.basic messages.
        This messages are for the events.

        earth.basic
           {
            action=halt|resume|stop|start
            ...
           }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager
        :param message: The XPL message
        :type message: XplMessage

        """
        self.log.debug("action_listener : Start ...")
        try:
            self._events_lock.acquire()
            action = None
            if 'action' in message.data:
                action = message.data['action']
            self.log.debug("action_listener : action %s found in message." % action)
            eventtype = None
            if 'type' in message.data:
                eventtype = message.data['type']
            if eventtype == None :
                self.log.debug("action_listener : no type found in message." % eventtype)
                return
            delay = "0"
            if 'delay' in message.data:
                delay = message.data['delay']
            if action == "start" :
                self.events.add_event(eventtype, delay, message.data)
                self._send_event_info(myxpl, eventtype, delay)
            elif action == "stop" :
                self.events.stop_event(eventtype, delay)
                self._send_event_info(myxpl, eventtype, delay)
            elif action == "resume" :
                self.events.resume_event(eventtype, delay)
                self._send_event_info(myxpl, eventtype, delay)
            elif action == "halt" :
                self.events.halt_event(eventtype, delay)
                self._send_event_info(myxpl, eventtype, delay)
            else :
                self.log.debug("action_listener : action %s not found." % action)
                return
            self.log.debug("action_listener : Done :)")
        except:
            error = "Exception %s" % (traceback.format_exc())
            self.log.debug("action_listener : "+error)
        finally :
            self._events_lock.release()

    def _send_event_list(self, myxpl):
        """
        Send a lists of active events.

        earth.basic
        {
        evnt-list=type1:delay1,type2:delay2,...
        evnt-list=type3:delay3,type4:delay4,...
        count=5
        }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager

        """
        self.log.debug("_send_event_list : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("earth.basic")
        count = 0
        evlist = ""
        for evt in self.events.get_list_events() :
            if evlist == "" :
                evlist = evt
                count += 1
            else :
                evlist = evlist + "," + evt
                count += 1
            if len(evlist) > 110:
                mess.add_data({"evnt-list" : evlist})
                evlist = ""
        if len(evlist) > 0:
            mess.add_data({"evnt-list" : evlist})
        #if "evnt-list" not in mess.data:
        #    mess.add_data({"evnt-list" : ""})
        mess.add_data({"count" : count})
        myxpl.send(mess)
        self.log.debug("_send_event_list : Done :)")

    def _send_event_info(self, myxpl, etype, delay):
        """
        Send information on an event.

        earth.basic
        {
        type=dawn|dusk|sunrise|fullmoon|...
        label=<a human readable name>
        [delay=+|-XXXXXX]
        [args=str]
        current=halted|resumed|stopped|started
        uptime=<number of seconds since created>
        fullruntime=<number of seconds in the "started" state>
        runtime=<number of seconds since the last start>
        runs=<number of fires>
        next=<the date of the next event>
        }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager
        :param event: The type of the event
        :type event: str
        :param delay: The delay to apply to the event
        :type delay: str

        """
        self.log.debug("_send_event_info : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("earth.basic")
        mess.add_data({"type" : etype})
        mess.add_data({"delay" : delay})
        event = self.events.get_event(etype, delay)
        if event != None:
            if "args" in event :
                mess.add_data({"args" : event['args']})
            mess.add_data({"current" : event['current']})
            mess.add_data({"uptime" : self.events.get_up_time(etype, delay)})
            mess.add_data({"fullruntime" : self.events.get_full_run_time(etype, delay)})
            mess.add_data({"runtime" : self.events.get_run_time(etype, delay)})
            mess.add_data({"runs" : event['runs']})
            mess.add_data({"next" : event['next']})
        else :
            mess.add_data({"current" : "halted"})
            mess.add_data({"uptime" : 0})
            mess.add_data({"fullruntime" : 0})
            mess.add_data({"runtime" : 0})
            mess.add_data({"runs" : 0})
            mess.add_data({"next" : "None"})
        myxpl.send(mess)
        self.log.debug("_send_event_info : Done :)")

    def _send_event_status(self, myxpl, status):
        """
        Send the value of a status

        earth.basic
        {
        type=daynight
        status=day|night
        }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager
        :param status: The status
        :type status: str

        """
        self.log.debug("_send_event_status : Start ...")
        if status in self.events.get_list_status():
            mess = XplMessage()
            mess.set_type("xpl-trig")
            mess.set_schema("earth.basic")
            mess.add_data({"type" : status})
            mess.add_data({"status" :  self.events.device_status[status]["value"]})
            myxpl.send(mess)
        else :
            self.log.debug("_send_event_status : Nothing to do.")

    def _send_event_parameter(self, myxpl, param):
        """
        Send value of a parameter.

        earth.basic
        {
        param=dawndusk
        value=true
        }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager
        :param param: The parameter to return the value
        :type param: str

        """
        self.log.debug("_send_event_parameter : Start ...")
        if param in self.events.get_list_params():
            mess = XplMessage()
            mess.set_type("xpl-trig")
            mess.set_schema("earth.basic")
            mess.add_data({"param" : param})
            mess.add_data({"value" : self.events.params[param]["value"]})
            myxpl.send(mess)
            self.log.debug("_send_event_parameter : Done :)")
        else :
            self.log.debug("_send_event_parameter : Nothing to do.")

    def _send_memory(self, myxpl):
        """
        Returns memory information

        earth.basic
        {
        memory=120000
        events=n,11000
        rest=n,11000
        }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager

        """
        self.log.debug("_send_memory : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("earth.basic")
        mess.add_data({"memory" : asizeof(self)})
        mess.add_data({"events" : "%s (%s)" % (asizeof(self.events.data),self.events.count_events())})
        mess.add_data({"store" : "%s" % (asizeof(self.events.store))})
        mess.add_data({"datafiles" : "%s" % (self.events.store.count_files())})
        myxpl.send(mess)
        self.log.debug("_send_memory : Done :)")

    def _send_event_gateway(self, myxpl):
        """
        Return gateway capabilities.

        earth.basic
        {
        gateway="Domogik Earth"
        host="host.tld"
        stat-list=dawndusk,daynight
        type-list=dawn,dusk
        cmd-list=list,info,status,gateway,memory
        act-list=start,stop,resume,halt
        param-list=latitude,longitude,dawndusk
        }

        :param myxpl: The XPL sender
        :type myxpl: XPL Manager

        """
        self.log.debug("_send_event_gateway : Start ...")
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("earth.basic")
        mess.add_data({"host" : self._hostname})
        mylist = ""
        for myval in self.events.get_list_types() :
            if mylist == "" :
                mylist = myval
            else :
                mylist = mylist + "," + myval
            if len(mylist) > 110:
                mess.add_data({"type-list" : mylist})
        if len(mylist) > 0:
            mess.add_data({"type-list" : mylist})
        mylist = ""
        for myval in self.events.get_list_status() :
            if mylist == "" :
                mylist = myval
            else :
                mylist = mylist + "," + myval
            if len(mylist) > 110:
                mess.add_data({"stat-list" : mylist})
        if len(mylist) > 0:
            mess.add_data({"stat-list" : mylist})
        mylist = ""
        for myval in self.get_list_cmds() :
            if mylist == "" :
                mylist = myval
            else :
                mylist = mylist + "," + myval
            if len(mylist) > 110:
                mess.add_data({"cmd-list" : mylist})
        if len(mylist) > 0:
            mess.add_data({"cmd-list" : mylist})
        mylist = ""
        for myval in self.get_list_acts() :
            if mylist == "" :
                mylist = myval
            else :
                mylist = mylist + "," + myval
            if len(mylist) > 110:
                mess.add_data({"act-list" : mylist})
        if len(mylist) > 0:
            mess.add_data({"act-list" : mylist})
        mylist = ""
        for myval in self.events.get_list_params() :
            if mylist == "" :
                mylist = myval
            else :
                mylist = mylist + "," + myval
            if len(mylist) > 110:
                mess.add_data({"param-list" : mylist})
        if len(mylist) > 0:
            mess.add_data({"param-list" : mylist})
        myxpl.send(mess)
        self.log.debug("_send_event_gateway : Done :)")

    def send_sensors(self):
        """
        Send the sensors stat messages

        """
        try :
            self._events_lock.acquire()
            #for dev in self.jobs.data :
            #    if self.jobs.data[dev]["current"] == "started":
            #        self._send_sensor_stat(self.myxpl,dev)
            #        self._stop.wait(self.delay_stat)
        finally :
            self._events_lock.release()
            #self.timer_stat = Timer(self.delay_sensor, self.send_sensors)
            #self.timer_stat.start()

    def _send_sensor_stat(self, myxpl, status):
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
        mess.add_data({"device" : status})
        mess.add_data({"current" :  self.events.device_status[status]})
        myxpl.send(mess)

    def stop_all(self):
        """
        Stop the timer and the running jobs.
        """
        self.log.info("EventAPI.stop_all : close all jobs.")
        self.events.close_all()
        if (self.delay_sensor >0):
            self.timer_stat.cancel()

class DawnDusk():
    """
    Implements the dawndusk extension.
    """

    def __init__(self, events):
        """
        Init the DawnDusk extension.

        :param events: the event manager
        :type events: EartEvents

        """
        self._events = events

    def get_next_dawn(self, mycity, delay, args = None) :
        """
        Return the date and time of the next dawn

        @param city: the city wher calculate the event.
        @param delay: the delay (in seconds) to the event.
        @param args: an optional argument.
        @returns: the next dawn daytime or None

        """
        if abs(delay) >= 86400:
            return None
        today = datetime.datetime.today() - datetime.timedelta(seconds=delay+30)
        mycity.date = today
        dawn = ephem.localtime(mycity.next_rising(ephem.Sun(), use_center = True))
        return dawn + datetime.timedelta(seconds=delay)

    def get_next_dusk(self, mycity, delay, args = None) :
        """
        Return the date and time of the dusk

        @param city: the city wher calculate the event.
        @param delay: the delay (in seconds) to the event.
        @param args: an optional argument.
        @returns: the next dusk daytime or None

        """
        if abs(delay) >= 86400:
            return None
        today = datetime.datetime.today() - datetime.timedelta(seconds=delay+30)
        mycity.date = today
        dusk = ephem.localtime(mycity.next_setting(ephem.Sun(), use_center = True))
        return dusk + datetime.timedelta(seconds=delay)

    def check_daynight(self, etype, message) :
        """
        Check that we should or not change the daynight status

        @param etype: the type of the device : dawn or dusk.
        @param message: the message as a dict().
        @returns: True if daynight has changed. False otherwise.

        """
        if "delay" not in message.data or "delay"=="0" :
            #This is the real event so we can change the status
            if etype == "dawn":
                self._events.set_status("daynight", "day")
            else:
                self._events.set_status("daynight", "night")
            return True
        return False

    def check_dawndusk(self, etype, message) :
        """
        Check that we should or not change the dawndusk status

        @param etype: the type of the device : dawn or dusk.
        @param message: the message as a dict().
        @returns: True if dawndusk has changed. False otherwise.

        """
        if "delay" not in message.data or "delay"=="0" :
            #This is the real event so we can change the status
            self._events.set_status("dawndusk", etype)
            return True
        return False

    def check_param(self, value) :
        """
        Check that the new value of the parameter is valid

        @param value: the new value.
        @returns: True if value is valid. False otherwise.

        """
        if value == "True" or value == "False" :
            return True
        return False

class MoonPhases():
    """
    Implements the MoonPhases extension.
    """

    def __init__(self, events):
        """
        Init the MoonPhases extension.

        :param events: the event manager
        :type events: EartEvents

        """
        self._events = events

    def get_next_new_moon(self, mycity, delay, args = None) :
        """
        Return the date and time of the next new moon

        @param city: the city wher calculate the event.
        @param delay: the delay (in seconds) to the event.
        @param args: an optional argument.
        @returns: the next new moon daytime or None

        """
        if abs(delay) >= 86400*28:
            return None
        m = ephem.Moon()
        today = datetime.datetime.today() - datetime.timedelta(seconds=delay+30)
        mycity.date = today
        m.compute(mycity)
        moon_date = ephem.localtime(ephem.next_new_moon(mycity.date))
        return moon_date + datetime.timedelta(seconds=delay)


    def get_next_first_quarter_moon(self, mycity, delay, args = None) :
        """
        Return the date and time of the next first quarter moon

        @param city: the city wher calculate the event.
        @param delay: the delay (in seconds) to the event.
        @param args: an optional argument.
        @returns: the next first quarter moon daytime or None

        """
        if abs(delay) >= 86400*28:
            return None
        m = ephem.Moon()
        today = datetime.datetime.today() - datetime.timedelta(seconds=delay+30)
        mycity.date = today
        m.compute(mycity)
        moon_date = ephem.localtime(ephem.next_first_quarter_moon(mycity.date))
        return moon_date + datetime.timedelta(seconds=delay)


    def get_next_full_moon(self, mycity, delay, args = None) :
        """
        Return the date and time of the next full moon

        @param city: the city wher calculate the event.
        @param delay: the delay (in seconds) to the event.
        @param args: an optional argument.
        @returns: the next full moon daytime or None

        """
        if abs(delay) >= 86400*28:
            return None
        m = ephem.Moon()
        today = datetime.datetime.today() - datetime.timedelta(seconds=delay+30)
        mycity.date = today
        m.compute(mycity)
        moon_date = ephem.localtime(ephem.next_full_moon(mycity.date))
        return moon_date + datetime.timedelta(seconds=delay)


    def get_next_last_quarter_moon(self, mycity, delay, args = None) :
        """
        Return the date and time of the next last quarter moon

        @param city: the city wher calculate the event.
        @param delay: the delay (in seconds) to the event.
        @param args: an optional argument.
        @returns: the next last quarter moon daytime or None

        """
        if abs(delay) >= 86400*28:
            return None
        m = ephem.Moon()
        today = datetime.datetime.today() - datetime.timedelta(seconds=delay+30)
        mycity.date = today
        m.compute(mycity)
        moon_date = ephem.localtime(ephem.next_last_quarter_moon(mycity.date))
        return moon_date + datetime.timedelta(seconds=delay)

    def check_moonphase(self, etype, message) :
        """
        Check that we should or not change the moon phase

        @param etype: the type of the device : dawn or dusk.
        @param message: the message as a dict().
        @returns: True if dawndusk has changed. False otherwise.

        """
        if "delay" not in message.data or "delay"=="0" :
            #This is the real event so we can change the status
            self._events.set_status("moonphase", etype)
            return True
        return False




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
XPL Earth server.

Implements
==========
class EarthStore
class EarthZmq

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
import ConfigParser
import os
import glob
from domogik.common.messaging.reqrep.messaging_reqrep import MessagingRep
from domogik.common.messaging.pubsub.messaging_event_utils import MessagingEventPub
import json
from random import choice
from time import sleep
from json import dumps, loads, JSONEncoder, JSONDecoder
import pickle

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

class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return JSONEncoder.default(self, obj)
        return {'_python_object': pickle.dumps(obj)}

def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(str(dct['_python_object']))
    return dct

class EarthZmq():
    """
    Interface to the ZMQ
    """
    plugin_name = "earth"
    category = "plugin.earth"

    def __init__(self, earth, stop):
        """
        Initialise the ZMQ interface.
        """
        self._earth = earth
        self.stop = stop
        self._zmq_reply = MessagingRep()
        self._zmq_publish = MessagingEventPub('plugin_earth')

    def __del__(self, earth, stop):
        """
        Delete zmq objects
        """
        del(self._zmq_reply)
        del(self._zmq_publish)

    def close(self):
        """
        Close the mq

        """
        self._zmq_reply.s_rep.close()
        self._zmq_publish.s_send.close()

    def get_reply_action(self, reqid):
        """
        Retrieve action from the id of request.

        """
        idxx = reqid.find(self.category)
        if idxx == -1:
            idxx = reqid.find("plugin.ping")
            if idxx == -1:
                return None
            else:
                return "ping"
        else :
            offset = len(self.category)
            temp = reqid[idxx+offset+1:]
            path = temp.split(".")
            res = path[0]
            if (path[0] == "admin") :
                res = path[0] + "." + path[1]
            return res

    def get_list_replies(self):
        """
        Retrieve list of replies

        """
        return ['gateway', 'memory', 'admin.set', 'admin.get', 'admin.list', 'admin.info',
            'admin.status', 'admin.start', 'admin.stop', 'admin.resume', 'admin.halt',
            'check', 'ping']

    def get_list_pubs(self):
        """
        Retrieve list of pubs

        """
        return ['admin.list', 'admin.event', 'admin.status', 'enabled']

    def _publish_list(self, action, rdict):
        """
        Publish the list using channel list

        """
        path = "%s.%s" % (self.category, "admin.list")
        r_content = dict()
        r_content["action"] = action
        r_content["data"] = rdict
        j_content = json.dumps(r_content, cls=PythonObjectEncoder)
        self._zmq_publish.send_event(path, j_content)
        self._earth.log.debug("EarthZmq.publish_list : send list %s" % j_content)
        print("Message sent : %s - %s"  % (path, j_content))

    def _get_id(self, event, delay):
        """
        Return the id to use

        """
        return "%s.%s" % (event, delay)

    def publish_plugin_enabled(self,status):
        """
        Publish that the plugin is enabled

        """
        r_content = dict()
        r_content["status"] = status
        r_content["plugin"] = self.plugin_name
        j_content = json.dumps(r_content, cls=PythonObjectEncoder)
        path = "%s.%s" % (self.category, "enabled")
        self._zmq_publish.send_event(path, j_content)
        path = "%s.%s" % ("plugin", "enabled")
        self._zmq_publish.send_event(path, j_content)
        self._earth.log.debug("EarthZmq.publish_plugin_enabled : data %s" % j_content)
        print("Message sent : %s - %s"  % (path, j_content))

    def publish_start(self, event, delay, eventdict, listdict):
        """
        An event wav created

        """
        path = "%s.%s" % (self.category, "admin.event")
        r_content = dict()
        r_content["action"] = "added"
        r_content["id"] = self._get_id(event, delay)
        r_content["data"] = eventdict
        j_content = json.dumps(r_content, cls=PythonObjectEncoder)
        self._zmq_publish.send_event(path, j_content)
        self._earth.log.debug("EarthZmq.publish_start : send list %s" % j_content)
        print("Message sent : %s - %s"  % (path, j_content))
        self._publish_list("event-added",eventdict)

    def publish_halt(self, event, delay, eventdict, listdict):
        """
        An event wav halted

        """
        path = "%s.%s" % (self.category, "admin.event")
        r_content = dict()
        r_content["action"] = "removed"
        r_content["id"] = self._get_id(event, delay)
        r_content["data"] = eventdict
        j_content = json.dumps(r_content, cls=PythonObjectEncoder)
        self._zmq_publish.send_event(path, j_content)
        self._earth.log.debug("EarthZmq.publish_halt : data %s" % j_content)
        print("Message sent : %s - %s"  % (path, j_content))
        self._publish_list("event-removed",eventdict)

    def publish_stop(self, event, delay, eventdict):
        """
        An event was stopped

        """
        path = "%s.%s" % (self.category, "admin.event")
        r_content = dict()
        r_content["action"] = "stopped"
        r_content["id"] = self._get_id(event, delay)
        r_content["data"] = eventdict
        j_content = json.dumps(r_content, cls=PythonObjectEncoder)
        self._zmq_publish.send_event(path, j_content)
        self._earth.log.debug("EarthZmq.publish_stop : data %s" % j_content)
        print("Message sent : %s - %s"  % (path, j_content))

    def publish_resume(self, event, delay, eventdict):
        """
       An event wav resumed

        """
        path = "%s.%s" % (self.category, "admin.event")
        r_content = dict()
        r_content["action"] = "resumed"
        r_content["id"] = self._get_id(event, delay)
        r_content["data"] = eventdict
        j_content = json.dumps(r_content, cls=PythonObjectEncoder)
        self._zmq_publish.send_event(path, j_content)
        self._earth.log.debug("EarthZmq.publish_resume : data %s" % j_content)
        print("Message sent : %s - %s"  % (path, j_content))

    def publish_status(self, status, rdict):
        """
        A status is updated
        """
        path = "%s.%s" % (self.category, "event.status")
        r_content = dict()
        r_content["action"] = "status"
        r_content["id"] = status
        r_content["data"] = rdict
        j_content = json.dumps(r_content, cls=PythonObjectEncoder)
        self._zmq_publish.send_event(path, j_content)
        self._earth.log.debug("EarthZmq.publish_status : data %s" % j_content)
        print("Message sent : %s - %s"  % (path, j_content))

    def reply(self):
        """
        Wait for ZMQ request and send reply.

        """
        self._earth.log.debug("EarthZmq.reply : Listen for messages ...")
        while not self.stop.isSet():
            self._earth.log.debug("EarthZmq.reply : Waiting for request...")
            try:
                j_request = self._zmq_reply.wait_for_request()
                self._earth.log.debug("EarthZmq.reply : Received request %s" % j_request)
                request = json.loads(j_request)
                action = self.get_reply_action(request['id'])
                repl = dict()
                print("YYYYYYYYYYYYYYMQ : Incoming request")
                if action == "check":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request check")
                    repl["check"] = "ok"
                elif action == "ping":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request ping")
                    repl["plugin"] = self.plugin_name
                elif action == "gateway":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request gateway")
                    repl = self._earth.gateway()
                elif action == "memory":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request memory")
                    repl = self._earth.memory()
                elif action == "admin.start":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request start")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None :
                        repl["error"] = "no event type found in message."
                    else :
                        data = {}
                        if "args" in  request['content'] :
                            data["args"] = request['content']['args']
                        data["current"] = "started"
                        self._earth.events.add_event(etype, edelay, data)
                        repl = self._earth.event_info(etype, edelay)
                elif action == "admin.stop":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request stop")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None :
                        repl["error"] = "no event type found in message."
                    else :
                        self._earth.events.stop_event(etype, edelay)
                        repl = self._earth.event_info(etype, edelay)
                elif action == "admin.resume":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request resume")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None :
                        repl["error"] = "no event type found in message."
                    else :
                        self._earth.events.resume_event(etype, edelay)
                        repl = self._earth.event_info(etype, edelay)
                elif action == "admin.halt":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request halt")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None :
                        repl["error"] = "no event type found in message."
                    else :
                        self._earth.events.halt_event(etype, edelay)
                        repl = self._earth.event_info(etype, edelay)
                elif action == "admin.info":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request info")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None :
                        repl["error"] = "no event type found in message."
                    else :
                        repl = self._earth.event_info(etype, edelay)
                elif action == "admin.simulate":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request simulate")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None :
                        repl["error"] = "no event type found in message."
                    else :
                        repl["error"] = "Not implemented"
                elif action == "admin.set":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request set")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None:
                        repl["error"] = "no event type found in message."
                    else :
                        repl["error"] = "Not implemented"
                elif action == "admin.get":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request get")
                    etype = None
                    edelay = "0"
                    if 'type' in request['content']:
                        etype = request['content']['type']
                    if 'delay' in request['content']:
                        edelay = request['content']['delay']
                    if etype == None :
                        repl["error"] = "no event type found in message."
                    else :
                        repl["error"] = "Not implemented"
                elif action == "admin.status":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request status")
                    equery = None
                    if 'query' in request['content']:
                        equery = request['content']['query']
                    repl = self._earth.event_status(equery)
                elif action == "admin.list":
                    print("ZZZZZZZZZZZZZZZZMQ : Processing request list")
                    repl = self._earth.event_list()
                else:
                    repl["error"] = "action %s not found" % action
            except :
                repl["error"] = "exception %s" % traceback.format_exc()
            finally:
                self._zmq_reply.send_reply(repl)


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
                    (jobfile, EARTHERRORS[err]))

    def count_files(self):
        """
        Count the number of events in the data directory.

        :returns: the number of files in the directory
        :rtype: int

        """
        cnt = 0
        for jobfile in glob.iglob(self._data_files_dir + "/*" + self._get_fileext()) :
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
            #delay_idx = 1
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


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

Purpose
=======

Regression tests for the earth plugin.

Usage
=====

Start plugin and run the tests

@author: bibi21000 <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import datetime
from threading import Event
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.messaging.reqrep.messaging_reqrep import MessagingReq
from domogik.common.messaging.pubsub.messaging_event_utils import MessagingEventSub
import unittest
import time
import json

class PluginTestCase(unittest.TestCase):

    def send_request(self, category, action, request, dictkeys=[], dictkeyvals={}):
        '''
        Send a request to the ZMQ and wait for reply

        :param request: the message received
        :type request: dict()
        :param dictkeys: The keys that must exist in the returning message
        :type dictkeys: set()
        :param dictkeyvals: The key:val pairs that must exist ine the returning message
        :param dictkeyvals: disct()

        '''
        j_reply = self.messaging_req.send_request(category, action, request)
        reply = json.loads(j_reply)
        #print("receive reply : %s" % reply)
        res = True
        if "error" in reply['content']:
            res = False
        if dictkeys != None:
            for mykey in dictkeys :
                #print("check key %s" % mykey)
                if mykey not in reply['content'] :
                    #print("missing key %s" % mykey)
                    res = False
        if dictkeyvals != None:
            for mykey in dictkeyvals :
                #print("check keyval %s" % mykey)
                if mykey not in reply['content'] :
                    #print("missing keyval %s" % mykey)
                    res = False
                elif reply['content'][mykey] != dictkeyvals[mykey]:
                    #print("bad value %s for keyval %s" % (dictkeyvals[mykey],mykey))
                    res = False
        return res

    def _query_cb(self, message):
        '''
        Callback to receive message after a query() call

        :param  message: the message received
        :type  message: XplMessage

        '''
        result = message.data
        #print("result=%s"%result)
        for resp in self._keys:
            if resp in result:
                res = self._keys.pop(resp)
                self._listens[resp].unregister()
                del self._listens[resp]
                self._result = result
                res.set()
                break

    def query(self, key, testmsg, dictkeys=[], dictkeyvals={}):
        '''
        Send a command and wait for response from the plugin.

        :param key: a key to look for
        :type key: str
        :param testmsg: The message to send
        :param testmsg: XPLMessage
        :param dictkeys: The keys that must exist in the returning message
        :type dictkeys: set()
        :param dictkeyvals: The key:val pairs that must exist ine the returning message
        :param dictkeyvals: disct()

        '''
        liste = Listener(self._query_cb, self.__myxpl, {'schema': self.schema,
                                                    'xpltype': self.xpltype})
        self._keys[key] = Event()
        self._listens[key] = liste
        self.__myxpl.send(testmsg)
        if key in self._keys:
            try:
                self._keys[key].wait(10)
                if not self._keys[key].is_set():
                    print("No answer received for key %s" % (key))
                    raise RuntimeError("No answer received for key %s, check your cron xpl setup" % (key))
            except KeyError:
                pass
        res = True
        if 'error' not in self._result:
            if dictkeys != None:
                for mykey in dictkeys :
                    if mykey not in self._result :
                        res = False
            if dictkeyvals != None:
                for mykey in dictkeyvals :
                    if mykey not in self._result :
                        res = False
                    elif self._result[mykey] != dictkeyvals[mykey]:
                        res = False
            return res
        else:
            print("Error %s when communicating key %s" % (self._result['errorcode'], key))
            print("%s : %s" % (self._result['errorcode'], self._result['error']))
            return False

    def setUp(self):
        global sendplugin
        self.__myxpl = sendplugin.myxpl
        self._keys = {}
        self._listens = {}
        self._result = None
        self.schema = "earth.basic"
        self.xpltype = "xpl-trig"
        #global messagingreq
        #self.messaging_req = messagingreq
        self.messaging_req = MessagingReq()
        self.category = "plugin.earth"
        #self.category_filters = ["admin.list","admin.event","admin.status","enabled"]
        #self.messaging_sub = MessagingEventSub('plugin_earth', *self.category_filters)

    def tearDown(self):
        self.messaging_req.s_req.close()
        #self.messaging_sub.s_send.close()

class GeneralTestCase(PluginTestCase):

    def test_010_check(self):
        action = "check"
        request = {}
        keys = None
        keyvalss = {'check' : 'ok'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_020_badaction(self):
        action = "badaction"
        request = {}
        keys = None
        keyvalss = None
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_030_ping_all(self):
        action = "ping"
        request = {}
        keys = ['plugin']
        keyvalss = None
        self.assertTrue(self.send_request("plugin", action, request, keys, keyvalss))

    def test_040_ping(self):
        action = "ping"
        request = {}
        keys = ['plugin']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_050_gateway(self):
        action = "gateway"
        request = {}
        keys = ['host', 'type-list', 'stat-list', 'cmd-list', 'act-list', 'param-list', 'rep-list', 'pub-list']
        keyvalss = {"gateway" : "Domogik Earth"}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_080_memory(self):
        action = "memory"
        request = {}
        keys = ['memory', 'events', 'store', 'datafiles', 'zmq']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_100_list(self):
        action = "admin.list"
        request = {}
        keys = ['count']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_210_bad_status(self):
        action = "admin.status"
        request = {"query" :  "badstatus"}
        keys = ['status']
        keyvalss = {'type' : 'badstatus'}
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

class DawnDuskTestCase(PluginTestCase):

    def test_110_add_dawn(self):
        action = "admin.start"
        request = {}
        request["type"] =  "dawn"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_130_info(self):
        action = "admin.info"
        request = {}
        request["type"] =  "dawn"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_150_add_dusk(self):
        action = "admin.start"
        request = {}
        request["type"] =  "dusk"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dusk", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_180_info(self):
        action = "admin.info"
        request = {}
        request["type"] =  "dusk"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dusk", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_200_list(self):
        action = "admin.list"
        request = {}
        keys = ['count','evnt-list']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_230_simulate_dawn(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "dawn"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", "delay":"0", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_240_status_dawndusk(self):
        action = "admin.status"
        request = {"query" :  "dawndusk"}
        keys = None
        keyvalss = {'type' : 'dawndusk', 'status' : 'dawn'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_250_status_daynight(self):
        action = "admin.status"
        request = {"query" :  "daynight"}
        keys = None
        keyvalss = {'type' : 'daynight', 'status' : 'day'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_260_simulate_dusk(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "dusk"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dusk", "delay":"0", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_270_status_dawndusk(self):
        action = "admin.status"
        request = {"query" :  "dawndusk"}
        keys = None
        keyvalss = {'type' : 'dawndusk', 'status' : 'dusk'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_280_status_daynight(self):
        action = "admin.status"
        request = {"query" :  "daynight"}
        keys = None
        keyvalss = {'type' : 'daynight', 'status' : 'night'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    """

    def test_310_parameter_get(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "get"})
        message.add_data({"param" :  "dawndusk"})
        keys = ['value']
        keyvalss = {"param" :  "dawndusk"}
        self.assertTrue(self.query("param",message,keys,keyvalss))

    def test_320_parameter_set(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "set"})
        message.add_data({"param" :  "dawndusk"})
        message.add_data({"value" :  "True"})
        keys = []
        keyvalss = {"param" :  "dawndusk", "value" :  "True"}
        self.assertTrue(self.query("param",message,keys,keyvalss))
    """

    def test_420_stop_dawn(self):
        action = "admin.stop"
        request = {}
        request["type"] =  "dawn"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'stopped','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_450_resume_dawn(self):
        action = "admin.resume"
        request = {}
        request["type"] =  "dawn"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_550_add_dawn_delay_plus(self):
        action = "admin.start"
        request = {}
        request["type"] =  "dawn"
        request["delay"] =  "+120"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '+120'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_560_add_dawn_delay_moins(self):
        action = "admin.start"
        request = {}
        request["type"] =  "dawn"
        request["delay"] =  "-120"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '-120'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_640_status_dusk(self):
        action = "admin.status"
        request = {"query" :  "dawndusk"}
        keys = None
        keyvalss = {'type' : 'dawndusk', 'status' : 'dusk'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_650_simulate_dawn_plus_delay(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "dawn"})
        message.add_data({"delay" :  "+120"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", "delay":"+120", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_660_status_dusk_not_changed(self):
        action = "admin.status"
        request = {"query" :  "dawndusk"}
        keys = None
        keyvalss = {'type' : 'dawndusk', 'status' : 'dusk'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_670_simulate_dawn_moins_delay(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "dawn"})
        message.add_data({"delay" :  "-120"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", "delay":"-120", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_680_status_dusk_not_changed(self):
        action = "admin.status"
        request = {"query" :  "dawndusk"}
        keys = None
        keyvalss = {'type' : 'dawndusk', 'status' : 'dusk'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_830_memory(self):
        action = "memory"
        request = {}
        keys = ['memory', 'events', 'store', 'datafiles', 'zmq']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_840_stop_dawn(self):
        action = "admin.stop"
        request = {}
        request["type"] =  "dawn"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'stopped','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_841_resume_dawn(self):
        action = "admin.resume"
        request = {}
        request["type"] =  "dawn"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_850_halt_dawn(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "dawn"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'halted','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_870_halt_dawn_delay_moins(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "dawn"
        request["delay"] =  "-120"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'halted','delay' : '-120'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_880_halt_dawn_delay_plus(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "dawn"
        request["delay"] =  "+120"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'halted','delay' : '+120'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_900_halt_dusk(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "dusk"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dusk", 'current' : 'halted','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_920_add_bad_dawn_delay_moins(self):
        action = "admin.start"
        request = {}
        request["type"] =  "dawn"
        bad_delay = 24*60*60 + 10 #More than a day. Will create an error.
        request["delay"] =  "-%s" % bad_delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started'}
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_930_add_bad_dawn_delay_plus(self):
        action = "admin.start"
        request = {}
        request["type"] =  "dawn"
        bad_delay = 24*60*60 + 10 #More than a day. Will create an error.
        request["delay"] =  "+%s" % bad_delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started'}
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_980_list(self):
        action = "memory"
        request = {}
        keys = ['memory', 'events', 'store', 'datafiles', 'zmq']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_990_memory(self):
        action = "admin.list"
        request = {}
        keys = ['count']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

class MoonPhasesTestCase(PluginTestCase):

    def test_110_add_full_moon(self):
        action = "admin.start"
        request = {}
        request["type"] =  "fullmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_120_stop_fullmoon(self):
        action = "admin.stop"
        request = {}
        request["type"] =  "fullmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'stopped','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_121_resume_fullmoon(self):
        action = "admin.resume"
        request = {}
        request["type"] =  "fullmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_130_info(self):
        action = "admin.info"
        request = {}
        request["type"] =  "fullmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_150_add_new_moon(self):
        action = "admin.start"
        request = {}
        request["type"] =  "newmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_157_stop_newmoon(self):
        action = "admin.stop"
        request = {}
        request["type"] =  "newmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'stopped','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_158_resume_newmoon(self):
        action = "admin.resume"
        request = {}
        request["type"] =  "newmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_160_add_first_quarter(self):
        action = "admin.start"
        request = {}
        request["type"] =  "firstquarter"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"firstquarter", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_170_add_last_quarter(self):
        action = "admin.start"
        request = {}
        request["type"] =  "lastquarter"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"lastquarter", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_180_list(self):
        action = "memory"
        request = {}
        keys = ['memory', 'events', 'store', 'datafiles', 'zmq']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_190_memory(self):
        action = "admin.list"
        request = {}
        keys = ['count']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_210_add_full_moon_delay_plus(self):
        action = "admin.start"
        request = {}
        request["type"] =  "fullmoon"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_220_add_full_moon_delay_moins(self):
        action = "admin.start"
        request = {}
        request["type"] =  "fullmoon"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_240_add_new_moon_plus(self):
        action = "admin.start"
        request = {}
        request["type"] =  "newmoon"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_250_add_new_moon_moins(self):
        action = "admin.start"
        request = {}
        request["type"] =  "newmoon"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_260_add_first_quarter_plus(self):
        action = "admin.start"
        request = {}
        request["type"] =  "firstquarter"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"firstquarter", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_270_add_first_quarter_moins(self):
        action = "admin.start"
        request = {}
        request["type"] =  "firstquarter"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"firstquarter", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_280_add_last_quarter_plus(self):
        action = "admin.start"
        request = {}
        request["type"] =  "lastquarter"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"lastquarter", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_290_add_last_quarter_moins(self):
        action = "admin.start"
        request = {}
        request["type"] =  "lastquarter"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"lastquarter", 'current' : 'started','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_300_memory(self):
        action = "memory"
        request = {}
        keys = ['memory', 'events', 'store', 'datafiles', 'zmq']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_310_list(self):
        action = "admin.list"
        request = {}
        keys = ['count']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_400_simulate_fullmoon(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "fullmoon"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_410_status_moonphase_fullmoon(self):
        action = "admin.status"
        request = {"query" :  "moonphase"}
        keys = None
        keyvalss = {'type' : 'moonphase', 'status' : 'fullmoon'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_420_simulate_firstquarter(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "firstquarter"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"firstquarter", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_430_status_moonphase_firstquarter(self):
        action = "admin.status"
        request = {"query" :  "moonphase"}
        keys = None
        keyvalss = {'type' : 'moonphase', 'status' : 'firstquarter'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_440_simulate_newmoon(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "newmoon"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_450_status_moonphase_newmoon(self):
        action = "admin.status"
        request = {"query" :  "moonphase"}
        keys = None
        keyvalss = {'type' : 'moonphase', 'status' : 'newmoon'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_460_simulate_lastquarter(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "lastquarter"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"lastquarter", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_470_status_moonphase_lastquarter(self):
        action = "admin.status"
        request = {"query" :  "moonphase"}
        keys = None
        keyvalss = {'type' : 'moonphase', 'status' : 'lastquarter'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_500_list(self):
        action = "admin.list"
        request = {}
        keys = ['count']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_600_simulate_firstquarter_moins(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "firstquarter"})
        delay = "-%s" % (60*60*24*7)
        message.add_data({"delay" : delay })
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type" : "firstquarter", 'current' : 'started','delay' : delay}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_610_status_moonphase_not_changed_firstquarter(self):
        action = "admin.status"
        request = {"query" :  "moonphase"}
        keys = None
        keyvalss = {'type' : 'moonphase', 'status' : 'firstquarter'}
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_620_simulate_firstquarter_moins(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "firstquarter"})
        delay = "+%s" % (60*60*24*7)
        message.add_data({"delay" : delay })
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type" : "firstquarter", 'current' : 'started','delay' : delay}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_630_status_moonphase_not_changed_firstquarter(self):
        action = "admin.status"
        request = {"query" :  "moonphase"}
        keys = None
        keyvalss = {'type' : 'moonphase', 'status' : 'firstquarter'}
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_850_add_new_moon_plus_bad(self):
        action = "admin.start"
        request = {}
        request["type"] =  "newmoon"
        bad_delay = "+%s" % (60*60*24*28+3600)
        request["delay"] =  "%s" % bad_delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started'}
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_860_add_new_moon_moins_bad(self):
        action = "admin.start"
        request = {}
        request["type"] =  "newmoon"
        bad_delay = "-%s" % (60*60*24*28+3600)
        request["delay"] =  "%s" % bad_delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started'}
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_900_halt_fullmoon(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "fullmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'halted','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_901_list(self):
        action = "admin.list"
        request = {}
        keys = ['count']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_903_halt_full_moon_delay_plus(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "fullmoon"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_906_halt_full_moon_delay_moins(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "fullmoon"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"fullmoon", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_907_stop_newmoon(self):
        action = "admin.stop"
        request = {}
        request["type"] =  "newmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'stopped','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_908_resume_newmoon(self):
        action = "admin.resume"
        request = {}
        request["type"] =  "newmoon"
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_910_halt_newmoon(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "newmoon"
        delay = "%s" % (0)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_913_halt_new_moon_plus(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "newmoon"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_916_halt_new_moon_moins(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "newmoon"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"newmoon", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_920_halt_firstquarter(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "firstquarter"
        delay = "%s" % 0
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"firstquarter", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_923_halt_first_quarter_plus(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "firstquarter"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"firstquarter", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_926_halt_first_quarter_mons(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "firstquarter"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"firstquarter", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_930_halt_lastquarter(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "lastquarter"
        delay = "%s" % 0
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"lastquarter", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_933_halt_last_quarter_plus(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "lastquarter"
        delay = "+%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"lastquarter", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_936_halt_last_quarter_moins(self):
        action = "admin.halt"
        request = {}
        request["type"] =  "lastquarter"
        delay = "-%s" % (60*60*24*7)
        request["delay"] =  delay
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"lastquarter", 'current' : 'halted','delay' : delay}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_980_list(self):
        action = "memory"
        request = {}
        keys = ['memory', 'events', 'store', 'datafiles', 'zmq']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_990_memory(self):
        action = "admin.list"
        request = {}
        keys = ['count']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))


if __name__ == '__main__':

    #messagingreq = MessagingReq()

    sendplugin = XplPlugin(name = 'eartht', daemonize = False, \
            parser = None, nohub = True)


    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(GeneralTestCase)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(DawnDuskTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MoonPhasesTestCase))

    unittest.TextTestRunner(verbosity=3).run(suite)


    sendplugin.force_leave()
    #messagingreq.s_req.close()


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

Send xPL message from the shell

Implements
==========

- Sender.__init__(self, schema=None, message=None)
- Sender.parse_parameters(self)
- Sender.forge_message(self)
- Sender.usage(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import datetime
from threading import Event
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
import unittest
import time

class PluginTestCase(unittest.TestCase):

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
        :param dictkeyvals: The key:val pairs that mus exist ine the returning message
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
        if 'error' not in self._result:
            if dictkeys != None:
                res = True
                for mykey in dictkeys :
                    if mykey not in self._result :
                        res = False
                for mykey in dictkeyvals :
                    if mykey not in self._result :
                        res = False
                    elif self._result[mykey] != dictkeyvals[mykey]:
                        res = False
                return res
            return False
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

#    def tearDown(self):
#        self.plugin.force_leave()

class CommandTestCase(PluginTestCase):

    def test_020_bad_gateway(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "gateway"})
        keys = ['bad-list']
        self.assertFalse(self.query("host",message,keys))

    def test_050_gateway(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "gateway"})
        keys = ['type-list','act-list','cmd-list','stat-list']
        self.assertTrue(self.query("host",message,keys))

    def test_150_memory(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "memory"})
        keys = ['memory']
        self.assertTrue(self.query("memory",message,keys))

    def test_250_list(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "list"})
        keys = ['count']
        keyvalss = {}
        self.assertTrue(self.query("count",message,keys,keyvalss))

class DawnduskTestCase(PluginTestCase):

    def test_110_add_dawn(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"type" :  "dawn"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_130_info(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "info"})
        message.add_data({"type" :  "dawn"})
        keys = ['delay', 'current', 'uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", "delay":"0"}
        self.assertTrue(self.query("type",message,keys,keyvalss))

    def test_150_add_dusk(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"type" :  "dusk"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dusk", 'current' : 'started','delay' : '0'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_200_list(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "list"})
        keys = ['count','evnt-list']
        keyvalss = {}
        self.assertTrue(self.query("count",message,keys,keyvalss))

    def test_250_simulate_dawn(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "dawn"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", "delay":"0", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_260_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "status"})
        message.add_data({"query" :  "dawndusk"})
        keys = []
        keyvalss = {'type' : 'dawndusk','status':'dawn'}
        self.assertTrue(self.query("type",message,keys,keyvalss))

    def test_270_daynight_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "status"})
        message.add_data({"query" :  "daynight"})
        keys = []
        keyvalss = {'type' : 'daynight','status':'day'}
        self.assertTrue(self.query("type",message,keys,keyvalss))

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

    def test_350_simulate_dusk(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("earth.basic")
        message.add_data({"type" :  "dusk"})
        message.add_data({"current" :  "fired"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dusk", "delay":"0", 'current' : "started"}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_360_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "status"})
        message.add_data({"query" :  "dawndusk"})
        keys = []
        keyvalss = {'type' : 'dawndusk','status':'dusk'}
        self.assertTrue(self.query("type",message,keys,keyvalss))

    def test_370_daynight_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "status"})
        message.add_data({"query" :  "daynight"})
        keys = []
        keyvalss = {'type' : 'daynight','status':'night'}
        self.assertTrue(self.query("type",message,keys,keyvalss))

    def test_450_stop_dawn(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"type" :  "dawn"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'stopped','delay' : '0'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_460_resume_dawn(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "resume"})
        message.add_data({"type" :  "dawn"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started', 'delay' : '0'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_550_add_dawn_delay_plus(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"type" :  "dawn"})
        message.add_data({"delay" :  "+120"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '+120'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_560_add_dawn_delay_moins(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"type" :  "dawn"})
        message.add_data({"delay" :  "-120"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'started','delay' : '-120'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_640_status_dusk(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "status"})
        message.add_data({"query" :  "dawndusk"})
        keys = []
        keyvalss = {'type' : 'dawndusk','status':'dusk'}
        self.assertTrue(self.query("type",message,keys,keyvalss))

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
        #We check that the previous simulation doesn't change the dawndusk status
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "status"})
        message.add_data({"query" :  "dawndusk"})
        keys = []
        keyvalss = {'type' : 'dawndusk','status':'dusk'}
        self.assertTrue(self.query("type",message,keys,keyvalss))

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
        #We check that the previous simulation doesn't change the dawndusk status
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "status"})
        message.add_data({"query" :  "dawndusk"})
        keys = []
        keyvalss = {'type' : 'dawndusk','status':'dusk'}
        self.assertTrue(self.query("type",message,keys,keyvalss))

    def test_830_memory(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "memory"})
        keys = ['memory']
        self.assertTrue(self.query("memory",message,keys))

    def test_850_halt_dawn(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"type" :  "dawn"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'halted', 'delay' : '0'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_870_halt_dawn_delay_moins(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"type" :  "dawn"})
        message.add_data({"delay" :  "-120"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'halted', 'delay' : '-120'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_880_halt_dawn_delay_plus(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"type" :  "dawn"})
        message.add_data({"delay" :  "+120"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dawn", 'current' : 'halted', 'delay' : '+120'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_900_halt_dusk(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"type" :  "dusk"})
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {"type":"dusk", 'current' : 'halted', 'delay' : '0'}
        self.assertTrue(self.query("type", message, keys, keyvalss))

    def test_950_list(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "list"})
        keys = ['count']
        keyvalss = {}
        self.assertTrue(self.query("count",message,keys,keyvalss))

    def test_990_memory(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("earth.request")
        message.add_data({"command" :  "memory"})
        keys = ['memory']
        self.assertTrue(self.query("memory",message,keys))

#    def test_999_add_bad_dawn_delay_moins(self):
#        message = XplMessage()
#        message.set_type("xpl-cmnd")
#        message.set_schema("earth.basic")
#        message.add_data({"action" :  "start"})
#        message.add_data({"type" :  "dawn"})
#        bad_delay = 24*60*60 + 10 #More than a day. Will create an error.
#        message.add_data({"delay" :  "-%s" % bad_delay})
#        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
#        keyvalss = {"type":"dawn", 'current' : 'started'}
#        self.assertFalse(self.query("type", message, keys, keyvalss))

if __name__ == '__main__':

    count_files = 0

    sendplugin = XplPlugin(name = 'testsend', daemonize = False, \
            parser = None, nohub = True)

    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(CommandTestCase)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(DawnduskTestCase))
    unittest.TextTestRunner(verbosity=3).run(suite)

    sendplugin.force_leave()

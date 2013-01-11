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

Regression tests for the bluez plugin.

Usage
=====

Configure plugin :

delay-sensor : 60

delay-stat : 3
device-name : bluez
scan-delay : 30
error-delay : 120
hysteresis : 0
listen-method : lookup

Also add the address of your phone with a name of "myphone"
... and turn off bluetooth on it.
During the test process, you will ne asked to turn it on.

Start the plugin

Start the test

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
import unittest
import time

class PluginTestCase(unittest.TestCase):

    def now_to_xpl(self):
        """
        Tranform an datetime date to an xpl one "yyyymmddhhmmss"
        form.

        @parameter sdate: The datetime to transform
        @return: A string representing the xpl date if everything \
            went fine. None otherwise.

        """
        try:
            sdate = datetime.datetime.today() + datetime.timedelta(seconds=120)
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

    def query(self, key, testmsg, dictkeys=[], dictkeyvals={}, timeout=10):
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
                self._keys[key].wait(timeout)
                if not self._keys[key].is_set():
                    #print("No answer received for key %s" % (key))
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
            #print("Error %s when communicating key %s" % (self._result['errorcode'], key))
            #print("%s : %s" % (self._result['errorcode'], self._result['error']))
            return False

    def query_many(self, key, testmsg, dictkeys=[], dictkeyvals={}, retry=20):
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
        self._keys = {}
        self._listens = {}
        self._result = None
        left = retry
        res = False
        while ((left >= 0) and (res != True)):
            res = self.query(key, testmsg, dictkeys, dictkeyvals, timeout=60)
            left = left -1
        return res

    def setUp(self):
        global sendplugin
        self.__myxpl = sendplugin.myxpl
        self._keys = {}
        self._listens = {}
        self._result = None
        self.schema = "bluez.basic"
        self.xpltype = "xpl-trig"
        self.time_start = datetime.datetime.now()

#    def tearDown(self):
#        self.plugin.force_leave()

class BluezTestCase(PluginTestCase):

    def test_110_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"bluez"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_210_stop(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("bluez.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"bluez", "status":"stopped"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_250_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"bluez", "status":"stopped"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_310_start(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("bluez.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"bluez", "status":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_350_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"bluez", "status":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_410_wait_for_low_stat(self):
        self.schema = "sensor.basic"
        self.xpltype = "xpl-stat"
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"myphone", "bluez":"bluez", "type":"ping", "current":"low"}
        self.assertTrue(self.query_many("device", message, keys, keyvalss))

    def test_510_wait_for_phone_on(self):
        #time.sleep(30)
        self.schema = "sensor.basic"
        self.xpltype = "xpl-trig"
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"myphone", "bluez":"bluez", "type":"ping", "current":"high"}
        print("")
        print("You must now turn ON bluetooth on your phone")
        self.assertTrue(self.query_many("device", message, keys, keyvalss))

    def test_550_wait_for_high_stat(self):
        #time.sleep(30)
        self.schema = "sensor.basic"
        self.xpltype = "xpl-stat"
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"myphone", "bluez":"bluez", "type":"ping", "current":"high"}
        self.assertTrue(self.query_many("device", message, keys, keyvalss))
        duration = datetime.datetime.now() - self.time_start
        print("")
        print("Delay between 2 stats is %s seconds" % duration.seconds)

    def test_570_wait_for_high_stat_delay(self):
        #time.sleep(30)
        self.schema = "sensor.basic"
        self.xpltype = "xpl-stat"
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"myphone", "bluez":"bluez", "type":"ping", "current":"high"}
        self.assertTrue(self.query_many("device", message, keys, keyvalss))
        duration = datetime.datetime.now() - self.time_start
        print("")
        print("Delay between 2 stats is %s seconds" % duration.seconds)

    def test_610_wait_for_phone_off(self):
        #time.sleep(30)
        self.schema = "sensor.basic"
        self.xpltype = "xpl-trig"
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"myphone", "bluez":"bluez", "type":"ping", "current":"low"}
        print("")
        print("You must now turn OFF bluetooth on your phone")
        self.assertTrue(self.query_many("device", message, keys, keyvalss))

    def test_650_wait_for_low_stat(self):
        #time.sleep(30)
        self.schema = "sensor.basic"
        self.xpltype = "xpl-stat"
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"myphone", "bluez":"bluez", "type":"ping", "current":"low"}
        self.assertTrue(self.query_many("device", message, keys, keyvalss))

    def test_710_status(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema(self.schema)
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "bluez"})
        keys = None
        keyvalss = {"device":"bluez", "status":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

if __name__ == '__main__':

    count_files = 0

    sendplugin = XplPlugin(name = 'bluezt', daemonize = False, \
            parser = None, nohub = True)

    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(BluezTestCase)
    #suite.addTests(unittest.TestLoader().loadTestsFromTestCase(IntervalTestCase))
    unittest.TextTestRunner(verbosity=3).run(suite)

    sendplugin.force_leave()

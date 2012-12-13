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

Regression tests for the cron plugin.

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
        self.schema = "timer.basic"
        self.xpltype = "xpl-trig"

#    def tearDown(self):
#        self.plugin.force_leave()

class TimerTestCase(PluginTestCase):

    def test_110_halt_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "testtimer1"})
        keys = ['device']
        keyvalss = {"device":"testtimer1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_210_add_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "timer"})
        message.add_data({"frequence" :  "30"})
        message.add_data({"device" :  "testtimer1"})
        keys = ['devicetype']
        keyvalss = {"device":"testtimer1", "devicetype":"timer", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_260_add_duplicate_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "timer"})
        message.add_data({"frequence" :  "30"})
        message.add_data({"device" :  "testtimer1"})
        keys = ['devicetype']
        keyvalss = {"device":"testtimer1", "devicetype":"timer", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_310_info_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "testtimer1"})
        keys = ['devicetype']
        keyvalss = {"device":"testtimer1", "devicetype":"timer", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_410_stop_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"device" :  "testtimer1"})
        keys = ['devicetype']
        keyvalss = {"device":"testtimer1", "devicetype":"timer", "state":"stopped"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_510_resume_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "resume"})
        message.add_data({"device" :  "testtimer1"})
        keys = ['devicetype']
        keyvalss = {"device":"testtimer1", "devicetype":"timer", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_610_list_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "list"})
        keys = ['devices']
        self.assertTrue(self.query("device",message,keys))

    def test_710_add_testtimer2_duration(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "timer"})
        message.add_data({"frequence" :  "30"})
        message.add_data({"duration" :  "3"})
        message.add_data({"device" :  "testtimer2"})
        keys = ['devicetype']
        keyvalss = {"device":"testtimer2", "devicetype":"timer", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_910_halt_testtimer1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "testtimer1"})
        keys = ['device']
        keyvalss = {"device":"testtimer1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_920_halt_testtimer2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "testtimer2"})
        keys = ['device']
        keyvalss = {"device":"testtimer2", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

class IntervalTestCase(PluginTestCase):

    def test_110_halt_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "interval1"})
        keys = ['device']
        keyvalss = {"device":"interval1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_210_add_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "interval"})
        message.add_data({"seconds" :  "30"})
        message.add_data({"device" :  "interval1"})
        keys = ['devicetype']
        keyvalss = {"device":"interval1", "devicetype":"interval", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_230_add_duplicate_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "interval"})
        message.add_data({"seconds" :  "30"})
        message.add_data({"device" :  "interval1"})
        keys = ['devicetype']
        keyvalss = {"device":"interval1", "devicetype":"interval", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_260_add_bad_interval2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "interval"})
        message.add_data({"device" :  "interval2"})
        keys = ['devicetype']
        keyvalss = {"device":"interval1", "devicetype":"interval", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_310_info_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "interval1"})
        keys = ['devicetype']
        keyvalss = {"device":"interval1", "devicetype":"interval", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_410_stop_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"device" :  "interval1"})
        keys = ['devicetype']
        keyvalss = {"device":"interval1", "devicetype":"interval", "state":"stopped"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_510_resume_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "resume"})
        message.add_data({"device" :  "interval1"})
        keys = ['devicetype']
        keyvalss = {"device":"interval1", "devicetype":"interval", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_610_list_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "list"})
        keys = ['devices']
        self.assertTrue(self.query("device",message,keys))

    def test_710_add_interval2_days(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "interval"})
        message.add_data({"days" :  "1"})
        message.add_data({"device" :  "interval2"})
        keys = ['devicetype']
        keyvalss = {"device":"interval2", "devicetype":"interval", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_910_halt_interval1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "interval1"})
        keys = ['device']
        keyvalss = {"device":"interval1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_920_halt_interval2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "interval2"})
        keys = ['device']
        keyvalss = {"device":"interval2", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

class DateTestCase(PluginTestCase):

    def test_110_halt_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "date1"})
        keys = ['device']
        keyvalss = {"device":"date1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_210_add_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "date"})
        message.add_data({"date" :  self.now_to_xpl()})
        message.add_data({"device" :  "date1"})
        keys = ['devicetype']
        keyvalss = {"device":"date1", "devicetype":"date", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_230_add_duplicate_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "date"})
        message.add_data({"date" :  self.now_to_xpl()})
        message.add_data({"device" :  "date1"})
        keys = ['devicetype']
        keyvalss = {"device":"date1", "devicetype":"date", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_260_add_bad_date2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "date"})
        message.add_data({"device" :  "date2"})
        keys = ['devicetype']
        keyvalss = {"device":"date1", "devicetype":"date", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_280_add_bad_date2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "date"})
        message.add_data({"device" :  "date2"})
        message.add_data({"date" :  "2012"})
        keys = ['devicetype']
        keyvalss = {"device":"date1", "devicetype":"date", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_310_info_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "date1"})
        keys = ['devicetype']
        keyvalss = {"device":"date1", "devicetype":"date", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_410_stop_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"device" :  "date1"})
        keys = ['devicetype']
        keyvalss = {"device":"date1", "devicetype":"date", "state":"stopped"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_510_resume_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "resume"})
        message.add_data({"device" :  "date1"})
        keys = ['devicetype']
        keyvalss = {"device":"date1", "devicetype":"date", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_610_list_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "list"})
        keys = ['devices']
        self.assertTrue(self.query("device",message,keys))

    def test_910_halt_date1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "date1"})
        keys = ['device']
        keyvalss = {"device":"date1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

class CronTestCase(PluginTestCase):

    def test_110_halt_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "cron1"})
        keys = ['device']
        keyvalss = {"device":"cron1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_210_add_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "cron"})
        message.add_data({"day" :  "1"})
        message.add_data({"hour" :  "2"})
        message.add_data({"device" :  "cron1"})
        keys = ['devicetype']
        keyvalss = {"device":"cron1", "devicetype":"cron", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_230_add_duplicate_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "cron"})
        message.add_data({"day" :  "1"})
        message.add_data({"hour" :  "2"})
        message.add_data({"device" :  "cron1"})
        keys = ['devicetype']
        keyvalss = {"device":"cron1", "devicetype":"cron", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_260_add_bad_cron2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "cron"})
        message.add_data({"device" :  "cron2"})
        keys = ['devicetype']
        keyvalss = {"device":"cron1", "devicetype":"cron", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

#    def test_290_add_bad_cron2(self):
#        message = XplMessage()
#        message.set_type("xpl-cmnd")
#        message.set_schema("timer.basic")
#        message.add_data({"action" :  "start"})
#        message.add_data({"devicetype" :  "cron"})
#        message.add_data({"device" :  "cron2"})
#        message.add_data({"hour" :  "26"})
#        keys = ['devicetype']
#        keyvalss = {"device":"cron1", "devicetype":"cron", "state":"started"}
#        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_310_info_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "cron1"})
        keys = ['devicetype']
        keyvalss = {"device":"cron1", "devicetype":"cron", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_410_stop_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"device" :  "cron1"})
        keys = ['devicetype']
        keyvalss = {"device":"cron1", "devicetype":"cron", "state":"stopped"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_510_resume_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "resume"})
        message.add_data({"device" :  "cron1"})
        keys = ['devicetype']
        keyvalss = {"device":"cron1", "devicetype":"cron", "state":"started"}
        self.assertTrue(self.query("device",message,keys,keyvalss))

    def test_610_list_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "list"})
        keys = ['devices']
        self.assertTrue(self.query("device",message,keys))

    def test_710_add_cron2_more(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "cron"})
        message.add_data({"day" :  "1"})
        message.add_data({"hour" :  "2"})
        message.add_data({"minute" :  "2"})
        message.add_data({"device" :  "cron2"})
        keys = ['devicetype']
        keyvalss = {"device":"cron2", "devicetype":"cron", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_910_halt_cron1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "cron1"})
        keys = ['device']
        keyvalss = {"device":"cron1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_920_halt_cron2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "cron2"})
        keys = ['device']
        keyvalss = {"device":"cron2", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

class AlarmTestCase(PluginTestCase):

    def test_110_halt_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm1"})
        keys = ['device']
        keyvalss = {"device":"alarm1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_210_add_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "alarm"})
        message.add_data({"alarm" :  "MoTuWeThFrSaSu,8:00-10:00"})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"alarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_220_add_alarm2_no_end(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "alarm"})
        message.add_data({"alarm" :  "MoTuWeThFrSaSu,8:00"})
        message.add_data({"device" :  "alarm2"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm2", "devicetype":"alarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_230_add_alarm3_multiple(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "alarm"})
        message.add_data({"alarm" :  "MoTu,8:00-10:00"})
        message.add_data({"alarm" :  "WeTh,11:00-12:00"})
        message.add_data({"alarm" :  "Fr,8:00"})
        message.add_data({"alarm" :  "SaSu,10:00-11:00"})
        message.add_data({"device" :  "alarm3"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm3", "devicetype":"alarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_250_add_duplicate_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "alarm"})
        message.add_data({"alarm" :  self.now_to_xpl()})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"alarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_260_add_bad_alarm4(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "alarm"})
        message.add_data({"device" :  "alarm4"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm4", "devicetype":"alarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_280_add_bad_alarm4(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "alarm"})
        message.add_data({"device" :  "alarm4"})
        message.add_data({"alarm" :  "MO,9:00"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm4", "devicetype":"alarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_310_info_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"alarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_410_stop_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"alarm", "state":"stopped"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_510_resume_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "resume"})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"alarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_610_list_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "list"})
        keys = ['devices']
        self.assertTrue(self.query("device", message, keys))

    def test_910_halt_alarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm1"})
        keys = ['device']
        keyvalss = {"device":"alarm1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_920_halt_alarm2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm2"})
        keys = ['device']
        keyvalss = {"device":"alarm2", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_930_halt_alarm3(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm3"})
        keys = ['device']
        keyvalss = {"device":"alarm3", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

class DawnAlarmTestCase(PluginTestCase):

    def test_110_halt_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm1"})
        keys = ['device']
        keyvalss = {"device":"alarm1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_210_add_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"alarm" :  "MoTuWeThFrSaSu,8:00-10:00-12:00"})
        message.add_data({"device" :  "alarm1"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"dawnalarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_220_add_dawnalarm2_no_stop(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"alarm" :  "MoTuWeThFrSaSu,8:00-10:00"})
        message.add_data({"device" :  "alarm2"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm2", "devicetype":"dawnalarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_230_add_dawnalarm3_multiple(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"alarm" :  "MoTu,8:00-10:00"})
        message.add_data({"alarm" :  "WeTh,11:00-12:00"})
        message.add_data({"alarm" :  "Fr,8:00-8:30"})
        message.add_data({"alarm" :  "SaSu,10:00-11:00"})
        message.add_data({"device" :  "alarm3"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm3", "devicetype":"dawnalarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_230_add_dawnalarm4_multiple_0123(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"alarm0" :  "MoTu,8:00-10:00"})
        message.add_data({"alarm1" :  "WeTh,11:00-12:00"})
        message.add_data({"alarm2" :  "Fr,8:00-8:30"})
        message.add_data({"alarm3" :  "SaSu,10:00-11:00"})
        message.add_data({"device" :  "alarm4"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm4", "devicetype":"dawnalarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_250_add_duplicate_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"alarm" :  self.now_to_xpl()})
        message.add_data({"device" :  "alarm1"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"dawnalarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_260_add_bad_dawnalarmX_missing_alarm(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"device" :  "alarmX"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarmX", "devicetype":"dawnalarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_260_add_bad_dawnalarmX_missing_nst(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"device" :  "alarmX"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarmX", "devicetype":"dawnalarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_280_add_bad_dawnalarmX_missing_end(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"device" :  "alarmX"})
        message.add_data({"alarm" :  "Mo,9:00"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarmX", "devicetype":"dawnalarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_290_add_bad_dawnalarmX_bad_syntax(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "start"})
        message.add_data({"devicetype" :  "dawnalarm"})
        message.add_data({"device" :  "alarmX"})
        message.add_data({"alarm" :  "MO,9:00-12:00"})
        message.add_data({"nst-device" :  "DIM14"})
        keys = ['devicetype']
        keyvalss = {"device":"alarmX", "devicetype":"dawnalarm", "state":"started"}
        self.assertFalse(self.query("device", message, keys, keyvalss))

    def test_310_info_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "status"})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"dawnalarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_410_stop_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "stop"})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"dawnalarm", "state":"stopped"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_510_resume_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "resume"})
        message.add_data({"device" :  "alarm1"})
        keys = ['devicetype']
        keyvalss = {"device":"alarm1", "devicetype":"dawnalarm", "state":"started"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_610_list_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "list"})
        keys = ['devices']
        self.assertTrue(self.query("device", message, keys))

    def test_910_halt_dawnalarm1(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm1"})
        keys = ['device']
        keyvalss = {"device":"alarm1", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_920_halt_dawnalarm2(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm2"})
        keys = ['device']
        keyvalss = {"device":"alarm2", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_930_halt_dawnalarm3(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm3"})
        keys = ['device']
        keyvalss = {"device":"alarm3", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

    def test_940_halt_dawnalarm4(self):
        message = XplMessage()
        message.set_type("xpl-cmnd")
        message.set_schema("timer.basic")
        message.add_data({"action" :  "halt"})
        message.add_data({"device" :  "alarm4"})
        keys = ['device']
        keyvalss = {"device":"alarm4", "state":"halted"}
        self.assertTrue(self.query("device", message, keys, keyvalss))

if __name__ == '__main__':

    count_files = 0

    sendplugin = XplPlugin(name = 'testsend', daemonize = False, \
            parser = None, nohub = True)

    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TimerTestCase)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(IntervalTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(DateTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(CronTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(AlarmTestCase))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(DawnAlarmTestCase))
    unittest.TextTestRunner(verbosity=3).run(suite)

    sendplugin.force_leave()

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

Regression tests for the cron_query library.

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
from domogik_packages.xpl.lib.cron_query import CronQuery
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

    def setUp(self):
        global sendplugin
        self.__myxpl = sendplugin.myxpl
        self.cronquery = CronQuery(self.__myxpl)

class QueryTestCase(PluginTestCase):

    def test_110_halt_testjob1(self):
        self.assertTrue(self.cronquery.halt_job("testjob1"))

    def test_210_add_testjob1(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("sensor.basic")
        message.add_data({"current" :  "high"})
        message.add_data({"device" :  "tsjob1"})
        self.assertTrue(self.cronquery.start_timer_job("testjob1",message,45))

    def test_260_add_duplicate_testjob1(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("sensor.basic")
        message.add_data({"current" :  "high"})
        message.add_data({"device" :  "tsjob1"})
        self.assertFalse(self.cronquery.start_timer_job("testjob1",message,45))

    def test_310_info_testjob1(self):
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("sensor.basic")
        message.add_data({"current" :  "high"})
        message.add_data({"device" :  "tsjob1"})

    def test_350_stop_testjob1(self):
        self.assertTrue(self.cronquery.stop_job("testjob1"))

    def test_360_resume_testjob11(self):
        self.assertTrue(self.cronquery.resume_job("testjob1"))

    def test_410_add_interval(self):
        self.cronquery.halt_job("testjob1")
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("sensor.basic")
        message.add_data({"current" :  "high"})
        message.add_data({"device" :  "tsjob1"})
        self.assertTrue(self.cronquery.start_interval_job("testjob1",message,weeks=2))

    def test_420_add_bad_interval(self):
        self.cronquery.halt_job("testjob1")
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("sensor.basic")
        message.add_data({"current" :  "high"})
        message.add_data({"device" :  "tsjob1"})
        self.assertTrue(self.cronquery.start_interval_job("testjob1",message) != True)

    def test_510_add_date(self):
        self.cronquery.halt_job("testjob1")
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("sensor.basic")
        message.add_data({"current" :  "high"})
        message.add_data({"device" :  "tsjob1"})
        self.assertTrue(self.cronquery.start_date_job("testjob1",message, \
            datetime.datetime.today() + datetime.timedelta(seconds=120)))

    def test_520_add_bad_date(self):
        self.cronquery.halt_job("testjob1")
        message = XplMessage()
        message.set_type("xpl-trig")
        message.set_schema("sensor.basic")
        message.add_data({"current" :  "high"})
        message.add_data({"device" :  "tsjob1"})
        self.assertTrue(self.cronquery.start_date_job("testjob1",message,\
            datetime.datetime.today() - datetime.timedelta(seconds=120)) != True)

    def test_610_add_alarm(self):
        self.skipTest("Not implemented")

    def test_670_add_bad_alarm(self):
        self.skipTest("Not implemented")

    def test_710_add_alarm(self):
        self.skipTest("Not implemented")

    def test_770_add_bad_alarm(self):
        self.skipTest("Not implemented")

    def test_910_halt_testjob1(self):
        self.assertTrue(self.cronquery.halt_job("testjob1"))

    def test_920_halt_testjob2(self):
        self.assertTrue(self.cronquery.halt_job("testjob2"))

if __name__ == '__main__':

    count_files = 0

    sendplugin = XplPlugin(name = 'cronqt', daemonize = False, \
            parser = None, nohub = True)

    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(QueryTestCase)
    #suite.addTests(unittest.TestLoader().loadTestsFromTestCase(IntervalTestCase))
    unittest.TextTestRunner(verbosity=3).run(suite)

    sendplugin.force_leave()

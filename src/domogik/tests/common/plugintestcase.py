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

Tools for regression tests

Usage
=====

@author: bibi21000 <sgallet@gmail.com>     # original functions
         Fritz SMH <fritz.smh@gmail.com>   # adaptation as a generic library
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.utils import get_sanitized_hostname
from domogik.tests.common.templatetestcase import TemplateTestCase
from domogik.tests.common.helpers import check_domogik_is_running
from domogik.tests.common.helpers import delete_configuration
from domogik.tests.common.helpers import configure, check_config
from domogik.tests.common.testplugin import TestPlugin
from domogik.common.plugin import STATUS_ALIVE, STATUS_STOPPED
import time


class PluginTestCase(TemplateTestCase):
    """ This is the class containing all the tests for the plugin
    """

    # this function is the same for all plugins
    def __init__(self, testname, xpl_plugin, name, configuration):
        """ Constructor
            @param testname : used by unittest to choose the test to launch
            @param xpl_plugin : an instance of XplPlugin to allow to use xPL features 
            @param name : name of the plugin we are testing
            @param configuration : dict containing the plugin configuration
        """
        #super(PluginTestCase, self).__init__(testname)
        super(PluginTestCase, self).__init__(testname)
        #TemplateTestCase.__init__(self)
        self.myxpl = xpl_plugin.myxpl
        self.name = name
        self.configuration = configuration

    # this function is the same for all plugins
    def test_0001_domogik_is_running(self):
        self.assertTrue(check_domogik_is_running())

    # this function is the same for all plugins
    def test_0010_configure_the_plugin(self):
        # first, clean the plugin configuration
        print(u"Delete the current plugin configuration")
        self.assertTrue(delete_configuration("plugin", self.name, get_sanitized_hostname()))
        for key in self.configuration:
            print(u"Set up configuration : {0} = {1}".format(key, self.configuration[key]))
            self.assertTrue(configure("plugin", self.name, get_sanitized_hostname(), key, self.configuration[key]))
        for key in self.configuration:
            print(u"Validate the configuration : {0} = {1}".format(key, self.configuration[key]))
            self.assertTrue(check_config("plugin", self.name, get_sanitized_hostname(), key, self.configuration[key]))

    # this function is the same for all plugins
    def test_0020_create_the_devices(self):
        pass

    # this function is the same for all plugins
    def test_0050_start_the_plugin(self):
        tp = TestPlugin(self.name, get_sanitized_hostname())
        self.assertTrue(tp.request_startup())
        self.assertTrue(tp.wait_for_event(STATUS_ALIVE))
        # just wait 1 second to get clearer logs
        time.sleep(5)

    # this function is the same for all plugins
    def test_9900_hbeat(self):
        print(u"Check that a heartbeat is sent. This could take up to 5 minutes.")
        self.assertTrue(self.wait_for_xpl(xpltype = "xpl-stat", 
                                          xplschema = "hbeat.app", 
                                          xplsource = "domogik-{0}.{1}".format(self.name, get_sanitized_hostname()),
                                          timeout = 600))
    
    # this function is the same for all plugins
    def test_9990_stop_the_plugin(self):
        tp = TestPlugin(self.name, get_sanitized_hostname())
        tp.request_stop()
        self.assertTrue(tp.wait_for_event(STATUS_STOPPED))
    
    def configure(self):
        raise NotImplementedError

    def create_device(self):
        raise NotImplementedError

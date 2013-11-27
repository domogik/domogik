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

Tool to automaticly run a testdirectory

Implements
==========

- TestRunner

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.plugin import XplPlugin
from domogik import __version__ as DMG_VERSION
from domogik.common import logger
from argparse import ArgumentParser
import os
import json
import traceback
import imp
import unittest

class TestRunner():
    """ Package installer class
    """
    def __init__(self):
        """ Init
        """
        l = logger.Logger("testrunner")
        l.set_format_mode("messageOnly")
        self.log = l.get_logger()

        parser = ArgumentParser()
	parser.add_argument("directory",
                          help="What directory to run")
        parser.add_argument("-a", 
                          "--no-automatic", 
                          dest="automatic",
                          action="store_false",
                          help="Install a package from a path, a zip file or an url to a zip file or to a github repository and branch")
        parser.add_argument("-n", 
                          "--need-hardware", 
                          dest="hardware", 
                          action="store_true",
                          help="Run test that need hardware")
        parser.add_argument("-m", 
                          "--use-mock", 
                          dest="mock", 
                          action="store_true",
                          help="Run test that use virtual devices")
        self.options = parser.parse_args()
	self.testcases = {}
        self.results = {}

        self.log.info("Domogik release : {0}".format(DMG_VERSION))
        self.log.info("Running test with the folowing parameters:")
	if self.options.automatic:
	    self.log.info("   - automatic testcases")
	if self.options.hardware:
	    self.log.info("   - testcases that need hardware")
	if self.options.mock:
	    self.log.info("   - testcases that use virtualdevices")

        if not self.check_dir():
            return
	self.log.info("   - path {0}".format(self.options.directory))

	if not self.load_json():
	    return
        self.log.info("   - json file {0}".format(self.json_file))

	self.log.info("")
        self.log.info("Will run the folowing testcases:")
        for test in self.testcases.keys():
            self.log.info("   - {0}".format(test))
        
        self._run_testcases()
        print self.results

    def check_dir(self):
        self.path = None
	
	if self.options.directory == ".":
            self.path = os.path.dirname(os.path.realpath(__file__))
        elif self.options.directory.startswith('/'):
            self.path = self.options.directory
        else:
            self.path = "{0}/{1}".format(os.path.dirname(os.path.realpath(__file__)), self.options.directory)
	
        # check if self.path is a directory
	if not os.path.isdir(self.path):
	    self.log.error("Path {0} is not a directory".format(self.path))
	    return False

	# cehck if we have a json file
	self.json_file = "{0}tests.json".format(self.path)
        if not os.path.isfile(self.json_file):
	    self.log.error("Path {0} has no tests.json file".format(self.path))
	    return False

	return True

    def load_json(self):
        try:
            self.json = json.loads(open(self.json_file).read())
	except:
            self.log.error("Error during json file reading: {0}".format(traceback.format_exc()))
            return False

	for (test, config) in self.json.iteritems():
	#{u'mock_available': False, u'need_hardware': False, u'alter_configuration_or_setup': u'true', u'automatic': True}
            to_add = True
	    if config['mock_available'] != self.options.mock:
                to_add = False
	    if config['need_hardware'] != self.options.hardware:
                to_add = False
	    if config['automatic'] != self.options.automatic:
                to_add = False
            if to_add:
               self.testcases[test] = config
        return True

    def _run_testcases(self):
        for (test, config) in self.testcases.items():
            self._run_testfile(self.path, test, config)

    def _run_testfile(self, path, test, config):
        # load the module
        mod = imp.load_source(test, "{0}/{1}".format(path, config['file']))
        cls = getattr(mod, config['class'])
        # start a unittest suite
        suite = unittest.TestSuite()
        # start an xplplugin
        xpl_plugin = XplPlugin(name = 'testrunner', 
                           daemonize = False, 
                           parser = None,
                           nohub = True,
                           test  = True)
        # run the config module
        cfg = cls.configure()
        cls.create_device()

        # add the suites
        for totest in dir(cls):
            if totest.startswith('test_'):
                suite.addTest(cls(totest, xpl_plugin, 'name', cfg))
        # run
        res = unittest.TextTestRunner().run(suite)
        self.results['test'] = res
        # store the result

def main():
    testr = TestRunner()

if __name__ == "__main__":
    main()

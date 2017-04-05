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
#from domogik.xpl.common.plugin import XplPlugin
from domogik import __version__ as DMG_VERSION
from domogik.common import logger
from domogik.common.utils import is_already_launched, STARTED_BY_MANAGER
from domogik.common.configloader import Loader, CONFIG_FILE
from argparse import ArgumentParser
import os
import json
import traceback
import imp
import unittest
import sys
from subprocess import Popen, PIPE
import time

LOW = "low"
MEDIUM = "medium"
HIGH = "high"

criticity_level = { LOW : 0, MEDIUM : 1, HIGH : 2 }

class TestRunner():
    """ Package installer class
    """
    def __init__(self):
        """ Init
        """
        # set logger
        l = logger.Logger("testrunner")
        l.set_format_mode("messageOnly")
        self.log = l.get_logger()

        # read the config file
        try:
            cfg = Loader('domogik')
            config = cfg.load()
            conf = dict(config[1])

            # pid dir path
            self._libraries_path = conf['libraries_path']
            self.log.debug("Libraries path is : {0}".format(self._libraries_path))

        except:
            self.log.error(u"Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
            return


        parser = ArgumentParser(description="Launch all the tests that don't need hardware.")
	parser.add_argument("directory",
                          help="What directory to run")
        parser.add_argument("-a", 
                          "--allow-alter", 
                          dest="allow_alter",
                          action="store_true",
                          help="Launch the tests that can alter the configuration of the plugin or the setup (devices, ...)")
        parser.add_argument("-c", 
                          "--criticity", 
                          dest="criticity", 
                          help="Set the minimum level of criticity to use to filter the tests to execute. low/medium/high. Default is low.")
        self.options = parser.parse_args()
	self.testcases = {}
        self.results = {}

        # options
        self.log.info("Domogik release : {0}".format(DMG_VERSION))
        self.log.info("Running test with the folowing parameters:")
	if self.options.allow_alter:
	    self.log.info("- allow to alter the configuration or setup.")
	if self.options.criticity not in (LOW, MEDIUM, HIGH):
            self.options.criticity = LOW
	self.log.info("- criticity : {0}".format(self.options.criticity))

        # check tests folder
	self.log.info("- path {0}".format(self.options.directory))
        if not self.check_dir():
            return

        # check and load the json file
        self.log.info("- json file {0}".format(self.json_file))
	if not self.load_json():
	    return

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
	self.json_file = "{0}/tests.json".format(self.path)
        if not os.path.isfile(self.json_file):
	    self.log.error("{0} is not a valid 'tests.json' file".format(self.json_file))
	    return False

	return True

    def load_json(self):
        try:
            self.json = json.loads(open(self.json_file).read())
	except:
            self.log.error("Error during json file reading: {0}".format(traceback.format_exc()))
            return False

        self.log.info("List of the tests (keep in mind that tests which need hardware will be skipped) :")
        for test in sorted(self.json):
            config = self.json[test]
            to_run = True
            if config['automatic'] == False:
                to_run = False
            if config['need_hardware']:
                to_run = False
            if (not self.options.allow_alter) and config['alter_configuration_or_setup']:
                to_run = False
            if criticity_level[self.options.criticity] > criticity_level[config['criticity']]:
                to_run = False
            if to_run:
                indicator = "[ TO RUN  ]"
                self.testcases[test] = config
            else:
                indicator = "[ SKIPPED ]"
            self.log.info("{0} {1} : need hardware={2}, alter config or setup={3}, criticity={4}".format(indicator, test, config['need_hardware'], config['alter_configuration_or_setup'], config['criticity']))
        return True

    def run_testcases(self):
        for test in sorted(self.testcases):
            config = self.testcases[test]
            # we add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
            self.log.info("")
            self.log.info("---------------------------------------------------------------------------------------")
            self.log.info("Launching {0}".format(test))
            self.log.info("---------------------------------------------------------------------------------------")
            cmd = "export PYTHONPATH={0} && {1} && cd {2} && python ./{3}.py".format(self._libraries_path, STARTED_BY_MANAGER, self.path, test)
            subp = Popen(cmd,
                         shell=True)
            pid = subp.pid
            subp.communicate()
            self.results[test] = { 'return_code' : subp.returncode }
            # do a pause to be sure the previous test (and so plugin instance) has been killed
            self.log.debug("Do a 30s pause... (yeah, this is a lot but Travis CI is not so quick!!!)")
            time.sleep(30)
        # Display a summary and manager return code
        rc = 0
        self.log.info("")
        self.log.info("Tests summary :")
        self.log.info("---------------")
       
        for res in self.results:
            if self.results[res]['return_code'] == 0:
                self.log.info("Test {0} : OK".format(res))
            else:
                self.log.info("Test {0} : ERROR".format(res))
                rc = 1

    def get_result(self):
        """ Return 0 if all is ok
            Return 1 if there are some tests failed
        """
        # Display a summary and manager return code
        for res in self.results:
            # when errors, return 1
            if self.results[res]['return_code'] != 0:
                return 1
        return 0


def main():
    try:
        testr = TestRunner()
        testr.run_testcases()
        cr = testr.get_result()
    except Exception as exp:
        print exp
        cr = 1
    sys.exit(cr)

if __name__ == "__main__":
    main()

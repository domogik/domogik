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

Module purpose
==============

Test domogik configuration

Implements
==========


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import pwd
import sys
import ConfigParser
from multiprocessing import Process, Pipe
from socket import gethostbyname, gethostname
from domogik.install.test_config import test_config

BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

user = ''

def info(msg):
    print("%s [ %s ] %s" % (BLUE,msg,ENDC))
def ok(msg):
    print("%s ==> %s  %s" % (OK,msg,ENDC))
def warning(msg):
    print("%s ==> %s  %s" % (WARNING,msg,ENDC))
def fail(msg):
    print("%s ==> %s  %s" % (FAIL,msg,ENDC))
def getInput(sect, item, value):
    newvalue = input ("Key {0} [{1}]: ".format(item, value))

def am_i_root():
    info("Check this script is started as root")
    assert os.getuid() == 0, "This script must be started as root"
    ok("Correctly started with root privileges.")

def write_configfile():
    # read the config file
    newvalues = False
    config = ConfigParser.RawConfigParser()
    config.read( ['/etc/domogik/domogik.cfg'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            print("Key {0} [{1}]: ".format(item[0], item[1])),
            newValue = sys.stdin.readline().rstrip('\n')
            if newValue != item[1] and newValue != '':
                # need to write it to config file
                config.set(sect, item[0], newValue)
                newvalues = True
    if newvalues:
        # write the config file
        with open('/etc/domogik/domogik.cfg', 'wb') as configfile:
            ok("Writing the config file")
            config.write(configfile)     
    
def config():
    try:
        am_i_root()
        write_configfile()
        test_config()
    except:
        fail(sys.exc_info()[1])


if __name__ == "__main__":
    config()

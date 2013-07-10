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
from argparse import ArgumentParser
from multiprocessing import Process, Pipe
from socket import gethostbyname, gethostname
from domogik.install.test_config import test_config

BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def is_advanced(advanced_mode, sect, key):
    advanced_keys = {
        'domogik': ['libraries_path', 'src_prefix', 'log_dir_path', 'pid_dir_path', 'broadcast'],
        'database': ['db_prefix', 'pool_recycle'],
        'rest': ['rest_server_port', 'rest_use_ssl', 'rest_ssl_certificate'],
        'mq': ['req_rep_port', 'pub_port', 'sub_port'],
    }
    if advanced_mode:
        return True
    else:
        if sect not in advanced_keys:
            return True
        else:
            if key not in advanced_keys[sect]:
                return True
            else:
                return False

def info(msg):
    print("%s [ %s ] %s" % (BLUE,msg,ENDC))
def ok(msg):
    print("%s ==> %s  %s" % (OK,msg,ENDC))
def warning(msg):
    print("%s ==> %s  %s" % (WARNING,msg,ENDC))
def fail(msg):
    print("%s ==> %s  %s" % (FAIL,msg,ENDC))

def am_i_root():
    info("Check this script is started as root")
    assert os.getuid() == 0, "This script must be started as root"
    ok("Correctly started with root privileges.")

def write_configfile(advanced_mode):
    # read the config file
    newvalues = False
    config = ConfigParser.RawConfigParser()
    config.read( ['/etc/domogik/domogik.cfg'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            if is_advanced(advanced_mode, sect, item[0]):
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

def needupdate():
    print("Do you want to keep your current config file? [Y/n]: "),
    newValue = sys.stdin.readline().rstrip('\n')
    if newValue == "y" or newValue == "Y" or newValue == '':
        return False
    else:
        return True
    
def config():
    parser = ArgumentParser()
    parser.add_argument("-a",
                          action="store_true",
                          dest="adv",
                          default=False, \
                          help="Run in advanced mode")
    parser.add_argument("-notest",
                          action="store_true",
                          dest="notest",
                          default=False, \
                          help="Don't test the config")
 
    options = parser.parse_args()
    try:
        am_i_root()
        if needupdate():
            write_configfile(options.adv)
        if not options.notest:
            test_config()
    except:
        fail(sys.exc_info())


if __name__ == "__main__":
    config()

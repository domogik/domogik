#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-02-22 13:34:47 +0100 (dim 22 fév 2009) $
# $LastChangedRevision: 395 $

from domogik.common.configloader import Loader
from domogik.common import logger
import os
import sys
import optparse

global lastpid
global components
global arguments
global config
global log

lastpid = 0
components = {'x10' : 'x10Main()',
                'datetime' : 'xPLDateTime()',
                'onewire' : 'OneWireTemp()',
                'trigger' : 'main()',
                'dawndusk' : 'main()'}

def parse_command_line():
    '''
    Parse the command line arguments
    '''
    global arguments
    parser = optparse.OptionParser()
    (options, arguments) = parser.parse_args()

def start_from_config():
    '''
    Start all components enabled in config
    '''
    global config
    global log
    lst = config['components_list'].split(',')
    log.debug('Start components from config : %s' % config['components_list'])
    for c in lst:
        start_one_component(c)

def start_one_component(name):
    '''
    Start one component
    @param name : The name of the component to start
    '''
    global components
    global lastpid
    global log
    log.debug('Try to start component %s' % name)
    if name not in components:
        log.warning("%s is not an existing component !" % name)
        raise ValueError
    elif is_component_running(name):
        log.info("%s pid file exists" % name)
        print "The component %s seems to already be started. If you think it's not, remove its pid file in %s." % (name, config['pid_dir_path'])
        exit(1)
    else:
        _start_comp(name)
        if lastpid:
            log.info("Component %s started with pid %i" % (name, lastpid))
            write_pid_file(name, str(lastpid))

def _start_comp(name):
    '''
    Internal method
    Fork the process then start the component
    @param name : the name of the component to start
    This method does *not* check if the component exists
    '''
    global lastpid
    global components
    global log
    log.info("Start the component %s" % name)
    mod_path = "domogik.xpl.bin." + name
    __import__(mod_path)
    module = sys.modules[mod_path]
    lastpid = os.fork()
    if not lastpid:
        eval("module.%s" % components[name])
        log.debug("%s process stopped" % name)

def write_pid_file(component, pid):
    '''
    Write the a pid in a file
    '''
    global config
    global log
    f = open("%s/%s.pid" % (config['pid_dir_path'], component), "w")
    f.write(pid)
    f.close()

def is_component_running(component):
    '''
    Check if one component is still running == the pid file exists
    '''
    global config
    return False
    #return os.path.isfile('%s/%s.pid' % (config['pid_dir_path'], component))

def init_config():
    '''
    Load the config
    '''
    global config
    cfgloader = Loader()
    config = cfgloader.load()[0]

def init_log():
    '''
    Initialize the logger
    '''
    global log
    l = logger.Logger('dmgstart')
    log = l.get_logger()

def usage():
    '''
    Display usage informations
    '''
    print "dmgstart.py <comp_name>\n"
    print "\t - comp_name : The name of the component you would start. Can be 'auto' to use the config file."

if __name__ == "__main__":
    init_log()
    init_config()
    parse_command_line()
    if len(arguments) != 1:
        usage()
        exit(1)
    else:
        if arguments[0] == 'auto':
            start_from_config()
        else:
            start_one_component(arguments[0])


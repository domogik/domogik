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

Start an xPL client

Implements
==========

- parse_command_line()
- start_from_config()
- start_one_component(name)
- wait_ack(message)
- write_pid_file(component, pid)
- is_component_running(component)
- init_config()
- init_log()
- usage()
- main()

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.configloader import Loader
from domogik.common import logger
from domogik.xpl.lib.xplconnector import *
import os
import sys
import optparse
import time

global lastpid
global components
global arguments
global config
global log
global myxpl

lastpid = 0
components = {'x10': 'x10Main()',
                'datetime': 'xPLDateTime()',
                'onewire': 'OneWireTemp()',
                'trigger': 'main()',
                'dawndusk': 'main()'}


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
    Send xPL request to start one component
    @param name : The name of the component to start
    '''
    global components
    global lastpid
    global log
    global config
    global myxpl

    log.debug('Try to start component %s' % name)
    if name not in components:
        log.warning("%s is not an existing component !" % name)
        raise ValueError
    else:
        myxpl = Manager(module_name = 'dmgstart')
        log.debug("*Asking to start %s by sending xPL request" % name)
        message = Message()
        message.set_type("xpl-cmnd")
        message.set_schema("domogik.system")
        message.set_data_key("module", name)
        message.set_data_key("command", "start")
        message.set_data_key("force", "1") #TODO
        #Create a listener to check the result
        l = Listener(wait_ack, myxpl, {'schema': 'domogik.system',
                'type': 'xpl-trig', 'command': 'start', 'module': name})
        myxpl.send(message)
        time.sleep(5) #Wait 5 seconds for a message
        print "No ack has been received during the last 5 seconds. It means " \
                "that :\n"
        print "\t - No manager have been found on the network"
        print "\t - The manager has some issues"
        myxpl.leave()
        exit(1)


def wait_ack(message):
    """
    Callback method to check the contents of an ack message (domogik.system)
    """
    global myxpl
    ack = ""
    error = ''
    myxpl.leave()
    if 'error' in message:
        error = message.get_key_value('error')
        print error
        exit(1)


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
    print "\t - comp_name : The name of the component you would start. Can be"\
            " 'auto' to use the config file."

def main():
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


if __name__ == "__main__":
    main()


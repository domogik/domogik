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

from domogik.xpl.lib.xplconnector import *
from domogik.common import configloader
import os
import sys

components = {'x10' : 'x10Main()',
                'datetime' : 'xPLDateTime()',
                'onewire' : 'OneWireTemp()',
                'trigger' : 'main()',
                'dawndusk' : 'main()'}

class SysManager(xPLModule):
    '''
    System management from domogik
    At the moment, can only start a module by receiving an xPL message
    '''

    def __init__(self):
        '''
        '''
        cfgloader = Loader()
        self._config = cfgloader.load()[0]
        l = logger.Logger('sysmanager')
        self._log = l.get_logger()

    def _start_comp(self,name):
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

    def write_pid_file(self,component, pid):
        '''
        Write the pid in a file
        '''
        global config
        global log
        f = open("%s/%s.pid" % (config['pid_dir_path'], component), "w")
        f.write(pid)
        f.close()

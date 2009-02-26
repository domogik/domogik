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


class SysManager(xPLModule):
    '''
    System management from domogik
    At the moment, can only start a module by receiving an xPL message
    '''

    def __init__(self):
        '''
        Init manager and start listeners
        '''
        self._components = {'x10' : 'x10Main()',
                        'datetime' : 'xPLDateTime()',
                        'onewire' : 'OneWireTemp()',
                        'trigger' : 'main()',
                        'dawndusk' : 'main()'}
        cfgloader = Loader()
        config = cfgloader.load()
        self._config = config[0]
        l = logger.Logger('sysmanager')
        self._log = l.get_logger()
        self.__myxpl = Manager(config[1]["address"],port = int(config[1]["port"]), source = config[1]["source"], module_name = 'send')


    def _sys_cb(self, message):
        '''
        Internal callback for receiving system messages
        '''
        cmd = message.get_key_value('command')
        mod = message.get_key_value('module')
        force = 0
        if message.has_key('force'):
            force = mesage.get_key_value('force')
        error = ""
        if mod not in self._components:
            error = "Invalide component.\n"
        elif force and self._is_component_running(mod):
            error += "The component seems already running and force is disabled"
        if error == "":
            pid = self._start_comp(mod)
            if pid:
                self._write_pid_file(mod, pid)
                self._log.debug("Component %s started with pid %i" %(mod, pid))
                mess = Message()
                mess.set_type('xpl-trig')
                mess.set_schema('domogik.system')
                mess.set_data_key('command',cmd)
                mess.set_data_key('module',mod)
                mess.set_data_key('force',force)
                mess.set_data_key('error',error)
                self.__myxpl.send(mess)

    def _start_comp(self,name):
        '''
        Internal method
        Fork the process then start the component
        @param name : the name of the component to start
        This method does *not* check if the component exists
        '''
        log.info("Start the component %s" % name)
        mod_path = "domogik.xpl.bin." + name
        __import__(mod_path)
        module = sys.modules[mod_path]
        lastpid = os.fork()
        if not lastpid:
            eval("module.%s" % components[name])
            self._log.debug("%s process stopped" % name)
            exit(0)
        return lastpid

    def _is_component_running(component):
        '''
        Check if one component is still running == the pid file exists
        '''
        return os.path.isfile('%s/%s.pid' % (self._config['pid_dir_path'], component))

    def _write_pid_file(self,component, pid):
        '''
        Write the pid in a file
        '''
        f = open("%s/%s.pid" % (self._config['pid_dir_path'], component), "w")
        f.write(pid)
        f.close()

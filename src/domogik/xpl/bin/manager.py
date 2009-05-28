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
from domogik.xpl.lib.module import *
from domogik.xpl.lib.queryconfig import *
from domogik.common.configloader import *
import os
import sys
import signal
import time


class SysManager(xPLModule):
    '''
    System management from domogik
    At the moment, can only start a module by receiving an xPL message
    '''

    def __init__(self):
        '''
        Init manager and start listeners
        '''
        xPLModule.__init__(self, name = 'sysmanager')
        self._components = {
            'x10': 'x10Main()',
            'datetime': 'xPLDateTime()',
            'onewire': 'OneWireTemp()',
            'trigger': 'main()',
            'dawndusk': 'main()'}
        self._log = self.get_my_logger()
        self._log.debug("Init system manager")
        self.__myxpl = Manager()
        Listener(self._sys_cb, self.__myxpl, {
            'schema': 'domogik.system',
            'type': 'xpl-cmnd',
        })
        self._config = Query(self.__myxpl)
        res = xPLResult()
        self._config.query('global', 'pid_dir_path', res)
#        res.get_lock().wait()
        self._pid_dir_path = res.get_value()

        self._log.debug("pid_dir_path got value %s" % self._pid_dir_path)
        self._log.info("System manager initialized")

    def _sys_cb(self, message):
        '''
        Internal callback for receiving system messages
        '''
        self._log.debug("Incoming message")
        cmd = message.get_key_value('command')
        mod = message.get_key_value('module')
        force = 0
        if message.has_key('force'):
            force = int(message.get_key_value('force'))
        error = ""
        if mod not in self._components:
            error = "Invalid component.\n"
        elif not force and self._is_component_running(mod):
            error = "ALREADY_RUNNING"
            self._log.info(error)
        if error == "":
            if cmd == "start":
                pid = self._start_comp(mod)
                if pid:
                    self._write_pid_file(mod, pid)
                    self._log.debug("Component %s started with pid %i" % (mod,
                            pid))
                    mess = Message()
                    mess.set_type('xpl-trig')
                    mess.set_schema('domogik.system')
                    mess.set_data_key('command', cmd)
                    mess.set_data_key('module', mod)
                    mess.set_data_key('force', force)
                    mess.set_data_key('error', error)
                    self.__myxpl.send(mess)
            elif cmd == "stop":
                ret = self._stop_comp(mod)
                if ret == 0:
                    error = ''
                elif ret == 1:
                    error = 'The component was not started (no pid file)'
                elif ret == 2:
                    error = 'An error occurs during sending signal'
                if not error:
                    self._log.debug("Component %s stopped" % (mod))
                else:
                    self._log.warning("Error during stop of component %s : %s" %\
                            (mod, error))
        mess = Message()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.set_data_key('command', cmd)
        mess.set_data_key('module', mod)
        mess.set_data_key('force', force)
        mess.set_data_key('error', error)
        self.__myxpl.send(mess)

    def _stop_comp(self, name):
        '''
        Internal method
        Try to stop a component by getting its pid and sending signal
        @param name : the name of the component to stop
        @return 0 if stop is OK, 1 if the pid file doesn't exist,
        2 in case of other problem
        '''
        pidfile = os.path.join(self._pid_dir_path, name + ".pid")
        if os.path.isfile(pidfile):
#            try:
            f = open(pidfile, "r")
            data = f.readlines()[0].replace('\n', '')
            f.close()
            os.kill(int(data), 15)
            print "%s" % data
            #We now check if the process is still existing
            #NASTY ! Wait 2s to let the process terminate
            time.sleep(2)
            try:
                os.kill(int(data), 0)
            except OSError:
                return 0
            else:
                return 2
 #           except:
  #              return 2
        else:
            return 1

    def _start_comp(self, name):
        '''
        Internal method
        Fork the process then start the component
        @param name : the name of the component to start
        This method does *not* check if the component exists
        '''
        self._log.info("Start the component %s" % name)
        mod_path = "domogik.xpl.bin." + name
        __import__(mod_path)
        module = sys.modules[mod_path]
        lastpid = os.fork()
        if not lastpid:
            os.execlp(sys.executable, sys.executable, module.__file__)
        return lastpid

    def _is_component_running(self, component):
        '''
        Check if one component is still running == the pid file exists
        '''
        self._log.debug("Test if %s is running on %s" %
                (component, self._pid_dir_path))
        pidfile = os.path.join(self._pid_dir_path,
                component + ".pid")
        return os.path.isfile(pidfile)

    def _write_pid_file(self, component, pid):
        '''
        Write the pid in a file
        '''
        pidfile = os.path.join(self._pid_dir_path,
                component + ".pid")
        f = open(pidfile, "w")
        f.write(str(pid))

if __name__ == "__main__":
    s = SysManager()

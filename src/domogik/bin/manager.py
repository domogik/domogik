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

Manage xPL clients on each host

Implements
==========

- SysManager.__init__(self)
- SysManager._sys_cb(self, message)
- SysManager._stop_comp(self, name)
- SysManager._start_comp(self, name)
- SysManager._is_component_running(self, component)
- SysManager._write_pid_file(self, component, pid)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import sys
import signal
import time
from socket import gethostname

from domogik.xpl.lib.xplconnector import *
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.lib.module import *
from domogik.xpl.lib.queryconfig import *
from domogik.common.configloader import *


class SysManager(xPLModule):
    '''
    System management from domogik
    '''

    def __init__(self):
        '''
        Init manager and start listeners
        '''
        xPLModule.__init__(self, name = 'sysmgr')
        self._components = {
            'x10': 'x10Main()',
            'dtmgr': 'xPLDateTime()',
            'onewire': 'OneWireTemp()',
            'trigger': 'main()',
            'dawndusk': 'main()'}
        self._log = self.get_my_logger()
        self._log.debug("Init system manager")
        
        Listener(self._sys_cb, self._myxpl, {
            'schema': 'domogik.system',
            'type': 'xpl-cmnd',
        })
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('global', 'pid-dir-path', res)
        self._pid_dir_path = res.get_value()['pid-dir-path']

        self._log.info("System manager initialized")

    def _sys_cb(self, message):
        '''
        Internal callback for receiving system messages
        '''
        cmd = message.data['command']
        mod = message.data['module']
        host = message.data["host"]
        force = 0
        if "force" in message.data:
            force = int(message.data['force'])
        error = ""
        if mod not in self._components and mod != "*":
            error = "Invalid component.\n"
        if error == "":
            self._log.debug("System request %s for host %s, module %s" % (cmd, host, mod))
            if cmd == "start" and host == gethostname():
                if not force and self._is_component_running(mod):
                    error = "Component is already running"
                    self._log.info(error)
                else:
                    pid = self._start_comp(mod)
                    if pid:
                        self._write_pid_file(mod, pid)
                        self._log.debug("Component %s started with pid %i" % (mod,
                                pid))
                        mess = XplMessage()
                        mess.set_type('xpl-trig')
                        mess.set_schema('domogik.system')
                        message.add_data({'host' : gethostname()})
                        mess.add_data({'command' :  cmd})
                        mess.add_data({'module' :  mod})
                        mess.add_data({'force' :  force})
                        if error:
                            mess.add_data({'error' :  error})
                        self._myxpl.send(mess)
            elif cmd == "host-ping":
                mess = XplMessage()
                mess.set_type('xpl-trig')
                mess.set_schema('domogik.system')
                mess.add_data({'command' :  cmd})
                mess.add_data({'host' : gethostname()})
                self._myxpl.send(mess)
        else:
            self._log.info("Error detected : %s, request %s has been cancelled" % (error, cmd))

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

def main():
    s = SysManager()

if __name__ == "__main__":
    main()

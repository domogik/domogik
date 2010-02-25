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
from socket import gethostname
from threading import Event
from optparse import OptionParser

from domogik.xpl.lib.xplconnector import Listener 
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.daemonize import createDaemon
from domogik.xpl.lib.module import xPLModule, xPLResult
from domogik.xpl.lib.queryconfig import Query

import domogik.xpl.bin
import pkgutil


class SysManager(xPLModule):
    '''
    System management from domogik
    '''

    def __init__(self):
        '''
        Init manager and start listeners
        '''
        xPLModule.__init__(self, name = 'sysmgr')

        # Logger init
        self._log = self.get_my_logger()
        self._log.debug("Init system manager")
        self._log.debug("Host : %s" % gethostname())

        # Get config
        self._config = Query(self._myxpl)
        res = xPLResult()
        self._config.query('global', 'pid-dir-path', res)
        self._pid_dir_path = res.get_value()['pid-dir-path']

        # Get components
        self._list_components(gethostname())

        # Check parameters 
        parser = OptionParser()
        parser.add_option("-d", action="store_true", dest="start_dbmgr", default=False, \
                help="Start database manager if not already running.")
        parser.add_option("-r", action="store_true", dest="start_rest", default=False, \
                help="Start REST interface manager if not already running.")

        # Start modules at manager startup
        self._log.debug("Check modules to start at manager startup...")
        for component in self._components:
            self._log.debug("%s..." % component["name"])
            self._config = Query(self._myxpl)
            res = xPLResult()
            self._config.query(component["name"], 'startup-module', res)
            startup = res.get_value()['startup-module']
            # start module
            if startup == 'True':
                self._log.debug("            starting")
                self._log.debug("Starting %s" % component["name"])
                self._start_module(component["name"], gethostname(), 0)
        
        # Define listener
        Listener(self._sys_cb, self._myxpl, {
            'schema': 'domogik.system',
            'xpltype': 'xpl-cmnd',
        })

        self._log.info("System manager initialized")

    def _sys_cb(self, message):
        '''
        Internal callback for receiving system messages
        @param message : xpl message received
        '''
        self._log.debug("Call _sys_cb")

        cmd = message.data['command']
        try:
           mod = message.data['module']
        except KeyError:
           mod = "*"
        host = message.data["host"]

        # force command indicator
        force = 0
        if "force" in message.data:
            force = int(message.data['force'])

        # error if no module in list
        error = ""
        if self._is_component(mod) == False and mod != "*":
            error = "Invalid component : %s.\n" % mod

        # if no error at this point, process
        if error == "":
            self._log.debug("System request %s for host %s, module %s" % (cmd, host, mod))

            # start module
            if cmd == "start" and host == gethostname():
                self._start_module(mod, host, force)

            # stop module
            elif cmd == "stop" and host == gethostname():
                self._start_module(mod, host, force)

            # list module
            elif cmd == "list" and host == gethostname():
                # first : we refresh list
                self._list_components(gethostname())
                self._send_component_list()

            # detail module
            elif cmd == "detail" and host == gethostname():
                # first : we refresh list
                self._list_components(gethostname())
                self._send_component_detail(mod, host)

            # host ping
            elif cmd == "host-ping":
                self._ping(host)

        # if error
        else:
            self._log.info("Error detected : %s, request %s has been cancelled" % (error, cmd))



    def _start_module(self, mod, host, force):
        self._log.debug("Ask to start %s on %s" % (mod, host))
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
                message.add_data({'host' : host})
                mess.add_data({'command' :  'start'})
                mess.add_data({'module' :  mod})
                mess.add_data({'force' :  force})
                if error:
                    mess.add_data({'error' :  error})
                self._myxpl.send(mess)



    def _stop_module(self, mod, host, force):
        self._log.debug("Ask to stop %s on %s" % (mod, host))
        if not force and self._is_component_running(mod) == False:
            error = "Component is not running"
            self._log.info(error)
        else:
            stopped = self._stop_comp(mod)
            if stopped:
                self._write_pid_file(mod, pid)
                self._log.debug("Component %s stopped" % mod)
                mess = XplMessage()
                mess.set_type('xpl-trig')
                mess.set_schema('domogik.system')
                message.add_data({'host' : host})
                mess.add_data({'command' :  'stop'})
                mess.add_data({'module' :  mod})
                mess.add_data({'force' :  force})
                if error:
                    mess.add_data({'error' :  error})
                self._myxpl.send(mess)


    def _ping(self, host):
        self._log.debug("Ask to ping on %s" % (host))
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'host-ping'})
        mess.add_data({'host' : gethostname()})
        self._myxpl.send(mess)

    def _check_dbmgr_is_running(self):
        ''' This method will send a ping request to dbmgr component
        and wait 5 seconds for the answer.
        '''
        self._dbmgr = Event()
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'ping'})
        mess.add_data({'host' : gethostname()})
        mess.add_data({'module' : 'dbmgr'})
        Listener(self._cb_check_dbmgr_is_running, self._myxpl, {'schema':'domogik.system', \
                'xpltype':'xpl-trig','command':'ping','module':'dbmgr','host':gethostname()})
        self._myxpl.send(mess)
        self._dbmgr.wait(5) #Wait 5 seconds 
        return self._dbmgr.isSet() #Will be set only if an answer was received

    def _cb_check_dbmgr_is_running(self, message):
        ''' Set the Event to true if an answer was received
        The use of the Event instead of time.sleep(5) ensure not to wait 5 seconds
        if the database manager answers before
        '''
        self._dbmgr.set()

    def _check_rest_is_running(self):
        ''' This method will send a ping request to rest component
        and wait 5 seconds for the answer.
        '''
        self._rest= Event()
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'ping'})
        mess.add_data({'host' : gethostname()})
        mess.add_data({'module' : 'rest'})
        Listener(self._cb_check_dbmgr_is_running, self._myxpl, {'schema':'domogik.system',\
                'xpltype':'xpl-trig','command':'ping','module':'rest','host':gethostname()})
        self._myxpl.send(mess)
        self._dbmgr.wait(5) #Wait 5 seconds 
        return self._rest.isSet() #Will be set only if an answer was received

    def _cb_check_rest_is_running(self, message):
        ''' Set the Event to true if an answer was received
        The use of the Event instead of time.sleep(5) ensure not to wait 5 seconds
        if the rest answers before
        '''
        self._rest.set()

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
            createDaemon()
            os.execlp(sys.executable, sys.executable, module.__file__)
            self._set_component_status(name, "ON")
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
        fil = open(pidfile, "w")
        fil.write(str(pid))

    def _list_components(self, host):
        '''
        List domogik modules
        '''
        self._log.debug("Ask to list on %s" % (host))
        self._components = []
        package = domogik.xpl.bin
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
            try:
                module = __import__(modname, fromlist="dummy")
                self._log.debug("Module : %s" % modname)
                if module.IS_DOMOGIK_MODULE is True:
                    if module.DOMOGIK_MODULE_DESCRIPTION == None:
                        moddesc = modname
                    else:
                        moddesc = module.DOMOGIK_MODULE_DESCRIPTION
                    try:
                        modconf = module.DOMOGIK_MODULE_CONFIGURATION
                    except:
                        modconf = []
                    self._log.debug("  => Domogik module (%s) :)" % moddesc)
                    self._components.append({"name" : modname, 
                                             "description" : moddesc, 
                                             "status" : "OFF", 
                                             "host" : gethostname(), 
                                             "configuration" : modconf})
            except:
                pass

    def _is_component(self, name):
        '''
        Is a component a module ?
        @param name : component name to check
        '''
        for component in self._components:
            if component["name"] == name:
                return True
        return False

    def _set_component_status(self, name, status):
        '''
        Set a component status in component list
        '''
        for component in self._components:
            if component["name"] == name:
                component["status"] = status

    def _send_component_list(self):
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' :  'list'})
        idx = 0
        for component in self._components:
            mod_content = "%s,%s,%s" % (component["name"],
                                        component["status"],
                                        component["description"])
            mess.add_data({'module'+str(idx) : mod_content})
            idx += 1
        mess.add_data({'host' : gethostname()})
        self._myxpl.send(mess)

    def _send_component_detail(self, mod, host):
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' :  'detail'})
        print "mod=%s" % mod
        for component in self._components:
            if component["name"] == mod:
                mod_content = "%s,%s,%s" % (component["name"],
                                            component["status"],
                                            component["description"])
                for conf in component["configuration"]:
                    conf_content = "%s,%s,%s" % (conf["key"],
                                                conf["description"],
                                                conf["default"])
                    mess.add_data({'config'+str(conf["id"]) : conf_content})
        mess.add_data({'module' :  mod_content})
        mess.add_data({'host' : gethostname()})

        print mess
        self._myxpl.send(mess)



if __name__ == "__main__":
    SYS = SysManager()

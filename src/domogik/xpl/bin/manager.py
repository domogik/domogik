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

# TODO : update

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import sys
import time
from socket import gethostname
from threading import Event, currentThread
from optparse import OptionParser
import traceback
from subprocess import Popen

from domogik.common.configloader import Loader
from domogik.xpl.common.xplconnector import Listener 
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import xPLPlugin, xPLResult
from domogik.xpl.common.queryconfig import Query

import domogik.xpl.bin
import pkgutil


KILL_TIMEOUT = 2


class SysManager(xPLPlugin):
    '''
    System management from domogik
    '''

    def __init__(self):
        '''
        Init manager and start listeners
        '''
        # Check parameters 
        parser = OptionParser()
        parser.add_option("-d", action="store_true", dest="start_dbmgr", default=False, \
                help="Start database manager if not already running.")
        parser.add_option("-r", action="store_true", dest="start_rest", default=False, \
                help="Start REST interface manager if not already running.")
        xPLPlugin.__init__(self, name = 'sysmgr', parser=parser)

        # Logger init
        self._log = self.get_my_logger()
        self._log.debug("Init system manager")
        self._log.debug("Host : %s" % gethostname())

        # Get config
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        self._pid_dir_path = conf['pid_dir_path']

        # Get components
        self._list_components(gethostname())

        if self.options.start_dbmgr:
            if self._check_dbmgr_is_running():
                self._log.warning("Manager started with -d, but a database manager is already running")
            else:
                self._start_plugin("dbmgr", gethostname(), 1)
                if not self._check_dbmgr_is_running():
                    self._log.error("Manager started with -d, but database manager not available after a startup.\
                            Please check dbmgr.log file")

        if self.options.start_rest:
            if self._check_rest_is_running():
                self._log.warning("Manager started with -r, but a REST manager is already running")
            else:
                self._start_plugin("rest", gethostname(), 1)
                if not self._check_rest_is_running():
                    self._log.error("Manager started with -r, but REST manager not available after a startup.\
                            Please check rest.log file")

        # Start plugins at manager startup
        self._log.debug("Check non-system plugins to start at manager startup...")
        for component in self._components:
            self._log.debug("%s..." % component["name"])
            self._config = Query(self._myxpl)
            res = xPLResult()
            self._config.query(component["name"], 'startup-plugin', res)
            startup = res.get_value()['startup-plugin']
            # start plugin
            if startup == 'True':
                self._log.debug("            starting")
                self._log.debug("Starting %s" % component["name"])
                self._start_plugin(component["name"], gethostname(), 0)
        
        # Define listener
        Listener(self._sys_cb, self._myxpl, {
            'schema': 'domogik.system',
            'xpltype': 'xpl-cmnd',
        })

#        Listener(self._sys_cb_stop, self._myxpl, {
#            'schema': 'domogik.system',
#            'xpltype': 'xpl-trig',
#            'command': 'stop',
#        })
        self._log.info("System manager initialized")
        self.get_stop().wait()


    def _sys_cb(self, message):
        '''
        Internal callback for receiving system messages
        @param message : xpl message received
        '''
        self._log.debug("Call _sys_cb")

        cmd = message.data['command']
        try:
           plg = message.data['plugin']
        except KeyError:
           plg = "*"
        host = message.data["host"]

        # force command indicator
        force = 0
        if "force" in message.data:
            force = int(message.data['force'])

        # error if no plugin in list
        error = ""
        if self._is_component(plg) == False and plg != "*":
            self._invalid_component(cmd, plg, host)

        # if no error at this point, process
        if error == "":
            self._log.debug("System request %s for host %s, plugin %s. current hostname : %s" % (cmd, host, plg, gethostname()))

            # start plugin
            if cmd == "start" and host == gethostname():
                self._start_plugin(plg, host, force)

            # stop plugin
            if cmd == "stop" and host == gethostname():
                try:
                    error_msg = message.data["error"]
                except KeyError:
                    error_msg = ""
                self._stop_plugin(plg, host, force, error_msg)

            # list plugin
            elif cmd == "list" and host == gethostname():
                # first : we refresh list
                self._list_components(gethostname())
                self._send_component_list()

            # detail plugin
            elif cmd == "detail" and host == gethostname():
                # first : we refresh list
                self._list_components(gethostname())
                self._send_component_detail(plg, host)

            # host ping
            elif cmd == "host-ping":
                self._ping(host)

        # if error
        else:
            self._log.info("Error detected : %s, request %s has been cancelled" % (error, cmd))

    def _sys_cb_stop(self, message):
        '''
        Internal callback for receiving 'stop' system messages
        @param message : xpl message received
        '''
        self._log.debug("Call _sys_cb_stop")

        cmd = message.data['command']
        try:
           plg = message.data['plugin']
        except KeyError:
           plg = "*"
        host = message.data["host"]

        # force command indicator
        force = 0
        if "force" in message.data:
            force = int(message.data['force'])

        # error if no plugin in list
        error = ""
        if self._is_component(plg) == False and plg != "*":
            self._invalid_component(cmd, plg, host)

        # if no error at this point, process
        if error == "":
            self._log.debug("System request %s for host %s, plugin %s. current hostname : %s" % (cmd, host, plg, gethostname()))

            # stop plugin
            if cmd == "stop" and host == gethostname():
                try:
                    error_msg = message.data["error"]
                except KeyError:
                    error_msg = ""
                    self._stop_plugin(plg, host, force, error_msg)

        # if error
        else:
            self._log.info("Error detected : %s, request %s has been cancelled" % (error, cmd))

    def _invalid_component(self, cmd, plg, host):
        error = "Component %s doesn't exists on %s" % (plg, host)
        self._log.debug(error)
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'host' : host})
        mess.add_data({'command' :  cmd})
        mess.add_data({'plugin' :  plg})
        mess.add_data({'error' :  error})
        self._myxpl.send(mess)

    def _start_plugin(self, plg, host, force):
        error = ""
        self._log.debug("Ask to start %s on %s" % (plg, host))
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'host' : host})
        mess.add_data({'command' :  'start'})
        mess.add_data({'plugin' :  plg})
        if not force and self._is_component_running(plg):
            error = "Component %s is already running on %s" % (plg, host)
            self._log.info(error)
            mess.add_data({'error' : error})
        else:
            pid = self._start_comp(plg)
            if pid:
                self._write_pid_file(plg, pid)
                self._log.debug("Component %s started with pid %i" % (plg,
                        pid))
                mess.add_data({'force' :  force})
                if error != "":
                    mess.add_data({'error' :  error})
        self._myxpl.send(mess)

    def _stop_plugin(self, plg, host, force, error):
        self._log.debug("Check plugin stops : %s on %s" % (plg, host))
        if not force and self._is_component_running(plg) == False:
            error = "Component %s is not running on %s" % (plg, host)
            self._log.info(error)
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('domogik.system')
            mess.add_data({'command' : 'stop'})
            mess.add_data({'host' : host})
            mess.add_data({'plugin' : plg})
            mess.add_data({'error' : error})
            self._myxpl.send(mess)
        else:
            # TODO : delete
            #self._set_component_status(plg, "OFF")
            pid = int(self._read_pid_file(plg))
            self._delete_pid_file(plg)
            self._log.debug("Check if process (pid %s) is down" % pid)
            if pid != 0:
                try:
                    time.sleep(KILL_TIMEOUT)
                    os.kill(pid, 0)
                except OSError:
                    self._log.debug("Process %s down" % pid)
                else:
                    self._log.debug("Process %s up. Try to kill it" % pid)
                    try:
                        os.kill(pid, 15)
                        self._log.debug("...killed (%s)" % pid)
                    except OSError:
                        self._log.debug("Process %s resists to kill -15... Detail : %s" % (pid, str(sys.exc_info()[1])))
                        self._log.debug("Trying kill -9 on process %s..." % pid)
                        time.sleep(KILL_TIMEOUT)
                        try:
                            os.kill(pid, 9)
                        except OSError:
                            self._log.debug("Process %s resists again... Failed to stop process. Detail : %s" % (pid, str(sys.exc_info()[1])))




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
        and wait for the answer (max 5 seconds).
        '''
        self._dbmgr = Event()
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'ping'})
        mess.add_data({'host' : gethostname()})
        mess.add_data({'plugin' : 'dbmgr'})
        Listener(self._cb_check_dbmgr_is_running, self._myxpl, {'schema':'domogik.system', \
                'xpltype':'xpl-trig','command':'ping','plugin':'dbmgr','host':gethostname()})
        max=5
        while max != 0:
            self._myxpl.send(mess)
            time.sleep(1)
            max = max - 1
            if self._dbmgr.isSet():
                break
        return self._dbmgr.isSet() #Will be set only if an answer was received

    def _cb_check_dbmgr_is_running(self, message):
        ''' Set the Event to true if an answer was received
        '''
        self._dbmgr.set()

    def _check_rest_is_running(self):
        ''' This method will send a ping request every second to rest component
        and wait for the answer (max 5 seconds).
        '''
        self._rest= Event()
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'ping'})
        mess.add_data({'host' : gethostname()})
        mess.add_data({'plugin' : 'rest'})
        Listener(self._cb_check_rest_is_running, self._myxpl, {'schema':'domogik.system',\
                'xpltype':'xpl-trig','command':'ping','plugin':'rest','host':gethostname()})
        max=5
        while max != 0:
            self._myxpl.send(mess)
            time.sleep(1)
            max = max - 1
            if self._rest.isSet():
                break
        return self._rest.isSet() #Will be set only if an answer was received

    def _cb_check_rest_is_running(self, message):
        ''' Set the Event to true if an answer was received
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
        plg_path = "domogik.xpl.bin." + name
        __import__(plg_path)
        plugin = sys.modules[plg_path]
        subp = Popen("/usr/bin/python %s" % plugin.__file__, shell=True)
        return subp.pid

    def _is_component_running(self, component):
        '''
        Check if one component is still running == the pid file exists
        '''
        self._log.debug("Test if %s is running on %s" %
                (component, self._pid_dir_path))
        pidfile = os.path.join(self._pid_dir_path,
                component + ".pid")
        return os.path.isfile(pidfile)

    def _delete_pid_file(self, component):
        '''
        Delete pid file
        '''
        self._log.debug("Delete pid file")
        pidfile = os.path.join(self._pid_dir_path,
                component + ".pid")
        return os.remove(pidfile)

    def _write_pid_file(self, component, pid):
        '''
        Write the pid in a file
        '''
        pidfile = os.path.join(self._pid_dir_path,
                component + ".pid")
        fil = open(pidfile, "w")
        fil.write(str(pid))

    def _read_pid_file(self, component):
        '''
        Read the pid in a file
        '''
        pidfile = os.path.join(self._pid_dir_path,
                component + ".pid")
        try:
            fil = open(pidfile, "r")
            return fil.read()
        except:
            return 0

    def _list_components(self, host):
        '''
        List domogik plugins
        '''
        self._log.debug("Ask to list on %s" % (host))
        self._components = []
        package = domogik.xpl.bin
        for importer, plgname, ispkg in pkgutil.iter_modules(package.__path__):
            try:
                plugin = __import__('domogik.xpl.bin.%s' % plgname, fromlist="dummy")
                self._log.debug("Plugin : %s" % plgname)
                if hasattr(plugin,'IS_DOMOGIK_PLUGIN') and plugin.IS_DOMOGIK_PLUGIN is True:
                    if plugin.DOMOGIK_PLUGIN_DESCRIPTION == None:
                        plgdesc = plgname
                    else:
                        plgdesc = plugin.DOMOGIK_PLUGIN_DESCRIPTION
                    try:
                        plgtech = plugin.DOMOGIK_PLUGIN_TECHNOLOGY
                    except:
                        plgtech = "Unknown"
                    try:
                        plgconf = plugin.DOMOGIK_PLUGIN_CONFIGURATION
                    except:
                        plgconf = []
                    if self._is_component_running(plgname):
                        status = "ON"
                    else:
                        status = "OFF"
                    self._log.debug("  => Domogik plugin (%s) :)" % plgdesc)
                    self._components.append({"name" : plgname, 
                                             "description" : plgdesc, 
                                             "technology" : plgtech, 
                                             "status" : status,
                                             "host" : gethostname(), 
                                             "configuration" : plgconf})
            except:
                self._log.error("Error during %s plugin import" % plgname)

    def _is_component(self, name):
        '''
        Is a component a plugin ?
        @param name : component name to check
        '''
        for component in self._components:
            if component["name"] == name:
                return True
        return False

    # TODO : delete
    #def _set_component_status(self, name, status):
    #    '''
    #    Set a component status in component list
    #    '''
    #    for component in self._components:
    #        if component["name"] == name:
    #            component["status"] = status

    def _send_component_list(self):
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' :  'list'})
        idx = 0
        for component in self._components:
            plg_content = "%s,%s,%s,%s" % (component["name"],
                                        component["technology"],
                                        component["status"],
                                        component["description"])
            mess.add_data({'plugin'+str(idx) : plg_content})
            idx += 1
        mess.add_data({'host' : gethostname()})
        self._myxpl.send(mess)

    def _send_component_detail(self, plg, host):
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' :  'detail'})
        print "plg=%s" % plg
        for component in self._components:
            if component["name"] == plg:
                plg_content = "%s,%s,%s" % (component["name"],
                                            component["technology"],
                                            component["status"],
                                            component["description"])
                for conf in component["configuration"]:
                    conf_content = "%s,%s,%s" % (conf["key"],
                                                conf["description"],
                                                conf["default"])
                    mess.add_data({'config'+str(conf["id"]) : conf_content})
        mess.add_data({'plugin' :  plg_content})
        mess.add_data({'host' : gethostname()})

        print mess
        self._myxpl.send(mess)


def main():
    ''' Called by the easyinstall mapping script
    '''
    SYS = SysManager()

if __name__ == "__main__":
    main()

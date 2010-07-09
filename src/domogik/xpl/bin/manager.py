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

Plugin purpose
==============

Manage xPL clients on each host

Implements
==========

# TODO : update

@author: Maxence Dunnewind <maxence@dunnewind.net>
@        Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import sys
import time
from socket import gethostname
from threading import Event, currentThread, Thread
from optparse import OptionParser
import traceback
from subprocess import Popen

from domogik.common.configloader import Loader
from domogik.xpl.common.xplconnector import Listener 
from domogik.xpl.common.xplconnector import READ_NETWORK_TIMEOUT
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin, XplResult
from domogik.xpl.common.queryconfig import Query
from xml.dom import minidom


import domogik.xpl.bin
import pkgutil


KILL_TIMEOUT = 2
PING_DURATION = 5
WAIT_TIME_BETWEEN_PING = 30


class SysManager(XplPlugin):
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
        parser.add_option("-t", action="store_true", dest="start_trigger", default=False, \
            help="Start scenario manager if not already running.")
        XplPlugin.__init__(self, name = 'manager', parser=parser)

        # Logger init
        self._log = self.get_my_logger()
        self._log.info("Host : %s" % gethostname())
    
        # Get config
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        self._pid_dir_path = conf['pid_dir_path']
    
        self._xml_plugin_directory = "%s/share/domogik/plugins/" % conf['custom_prefix']
        self._pinglist = {}
        try:
            # Get components
            self._list_components(gethostname())
    
            #Start dbmgr
            if self.options.start_dbmgr:
                if self._check_component_is_running("dbmgr"):
                    self._log.warning("Manager started with -d, but a database manager is already running")
                else:
                    self._start_plugin("dbmgr", gethostname(), 1)
                    if not self._check_component_is_running("dbmgr"):
                        self._log.error("Manager started with -d, but database manager not available after a startup.\
                                Please check dbmgr.log file")
    
            #Start rest
            if self.options.start_rest:
                if self._check_component_is_running("rest"):
                    self._log.warning("Manager started with -r, but a REST manager is already running")
                else:
                    self._start_plugin("rest", gethostname(), 1)
                    if not self._check_component_is_running("rest"):
                        self._log.error("Manager started with -r, but REST manager not available after a startup.\
                                Please check rest.log file")
    
            #Start trigger
            if self.options.start_trigger:
                if self._check_component_is_running("trigger"):
                    self._log.warning("Manager started with -t, but a trigger manager is already running")
                else:
                    self._start_plugin("trigger", gethostname(), 1)
                    if not self._check_component_is_running("trigger"):
                        self._log.error("Manager started with -t, but trigger manager not available after a startup.\
                                Please check trigger.log file")

            # Start plugins at manager startup
            self._log.debug("Check non-system plugins to start at manager startup...")
            comp_thread = {}
            for component in self._components:
                name = component["name"]
                self._log.debug("%s..." % name)
                self._config = Query(self._myxpl)
                res = XplResult()
                self._config.query(name, 'startup-plugin', res)
                startup = res.get_value()['startup-plugin']
                # start plugin
                if startup == 'True':
                    self._log.debug("            starting")
                    self._log.debug("Starting %s" % name)
                    ### old version : non threaded startup
                    #self._start_plugin(name, gethostname(), 0)
                    ### new version : thread
                    comp_thread[name] = Thread(None,
                                                   self._start_plugin,
                                                   None,
                                                   (name,
                                                    gethostname(),
                                                    0),
                                                   {})
                    comp_thread[name].start()
            
            # Define listener
            Listener(self._sys_cb, self._myxpl, {
                'schema': 'domogik.system',
                'xpltype': 'xpl-cmnd',
            })
    
            self._log.info("System manager initialized")

            ### make an eternal loop to ping plugins
            # the goal is to detect manually launched plugins
            while True:
                ping_thread = {}
                for component in self._components:
                    name = component["name"]
                    ping_thread[name] = Thread(None,
                                         self._check_component_is_running,
                                         None,
                                         (name, None),
                                         {})
                    ping_thread[name].start()
                time.sleep(WAIT_TIME_BETWEEN_PING)

        except:
            self._log.error("%s" % sys.exc_info()[1])
            print("%s" % sys.exc_info()[1])



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
            if cmd == "start" and host == gethostname() and plg != "rest":
                self._start_plugin(plg, host, force)

            # stop plugin
            if cmd == "stop" and host == gethostname() and plg != "rest":
                try:
                    error_msg = message.data["error"]
                except KeyError:
                    error_msg = ""
                self._stop_plugin(plg, host, force, error_msg)

            # list plugin
            elif cmd == "list" and host == gethostname():
                self._send_component_list()

            # detail plugin
            elif cmd == "detail" and host == gethostname():
                self._send_component_detail(plg, host)

            # host ping
            elif cmd == "host-ping":
                self._ping(host)

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
        if not force and self._check_component_is_running(plg):
            error = "Component %s is already running on %s" % (plg, host)
            self._log.info(error)
            mess.add_data({'error' : error})
        else:
            pid = self._start_comp(plg)
            if pid:
                # let's check if component successfully started
                time.sleep(READ_NETWORK_TIMEOUT + 0.5) # time a plugin took to die.
                # component started
                if self._check_component_is_running(plg):
                    self._log.debug("Component %s started with pid %s" % (plg,
                            pid))

                # component failed to start
                else:
                    error = "Component %s failed to start. Please look in this component logs files" % plg
                    self._log.error(error)
                    self._delete_pid_file(plg)
                mess.add_data({'force' :  force})
                if error != "":
                    mess.add_data({'error' :  error})
        self._myxpl.send(mess)

    def _stop_plugin(self, plg, host, force, error):
        self._log.debug("Check plugin stops : %s on %s" % (plg, host))
        if not force and self._check_component_is_running(plg) == False:
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
            pid = int(self._read_pid_file(plg))
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
                            return
                self._delete_pid_file(plg)
                 
                self._set_status(plg, "OFF")
            else:
                self._log.warning("Pid file contains no pid!")




    def _ping(self, host):
        self._log.debug("Ask to ping on %s" % (host))
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'host-ping'})
        mess.add_data({'host' : gethostname()})
        self._myxpl.send(mess)

    def _check_component_is_running(self, name, foo = None):
        ''' This method will send a ping request to a component
        and wait for the answer (max 5 seconds).
        @param name : component name
        '''
        self._log.info("Check if '%s' is running... (thread)" % name)
        self._pinglist[name] = Event()
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.system')
        mess.add_data({'command' : 'ping'})
        mess.add_data({'host' : gethostname()})
        mess.add_data({'plugin' : name})
        Listener(self._cb_check_component_is_running, self._myxpl, {'schema':'domogik.system', \
                'xpltype':'xpl-trig','command':'ping','plugin':name,'host':gethostname()}, \
                cb_params = {'name' : name})
        max = PING_DURATION
        self._set_status(name, "OFF")
        while max != 0:
            self._myxpl.send(mess)
            time.sleep(1)
            max = max - 1
            if self._pinglist[name].isSet():
                break
        if self._pinglist[name].isSet():
            self._log.info("'%s' is running" % name)
            self._set_status(name, "ON")
            return True
        else:
            self._log.info("'%s' is not running" % name)
            self._set_status(name, "OFF")
            return False

    def _cb_check_component_is_running(self, message, args):
        ''' Set the Event to true if an answer was received
        '''
        self._pinglist[args["name"]].set()

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

    def _delete_pid_file(self, component):
        '''
        Delete pid file
        '''
        self._log.debug("Delete pid file")
        pidfile = os.path.join(self._pid_dir_path,
                component + ".pid")
        return os.remove(pidfile)

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

    def _set_status(self, plg, state):
        """
        Set status for a component
        """ 
        for comp in self._components:
            if comp["name"] == plg:
                comp["status"] = state




    def _list_components(self, host):
        '''
        List domogik plugins
        '''
        self._log.debug("Start listing available plugins")

        self._components = []

        # Getplugin list
        plugins = Loader('plugins')
        plugin_list = dict(plugins.load()[1])
        state_thread = {}
        for plugin in plugin_list:
            print plugin
            self._log.info("==> %s (%s)" % (plugin, plugin_list[plugin]))
            if plugin_list[plugin] == "enabled":
                # try open xml file
                xml_file = "%s/%s.xml" % (self._xml_plugin_directory, plugin)
                try:
                    # get data for plugin
                    xml_content = minidom.parse(xml_file)
                    plgname = xml_content.getElementsByTagName("name")[0].firstChild.nodeValue
                    plgdesc = xml_content.getElementsByTagName("description")[0].firstChild.nodeValue
                    plgtech = xml_content.getElementsByTagName("technology")[0].firstChild.nodeValue
                    plgver = xml_content.getElementsByTagName("version")[0].firstChild.nodeValue
                    plgdoc = xml_content.getElementsByTagName("documentation")[0].firstChild.nodeValue

                    # config part
                    config = xml_content.getElementsByTagName("configuration-keys")[0]
                    plgconf = []
                    for key in config.getElementsByTagName("key"):
                        k_id = key.getElementsByTagName("order-id")[0].firstChild.nodeValue
                        k_key = key.getElementsByTagName("name")[0].firstChild.nodeValue
                        k_description = key.getElementsByTagName("description")[0].firstChild.nodeValue
                        k_type = key.getElementsByTagName("type")[0].firstChild.nodeValue
                        try:
                            k_default = key.getElementsByTagName("default-value")[0].firstChild.nodeValue
                        except AttributeError:
                            # no value in default
                            k_default = ""
                        plgconf.append({"id" : k_id,
                                        "key" : k_key,
                                        "description" : k_description,
                                        "type" : k_type,
                                        "default" : k_default})
                    self._log.debug("  All elements from xml file found")

                    # register plugin
                    self._components.append({"name" : plgname, 
                                             "description" : plgdesc, 
                                             "technology" : plgtech, 
                                             "status" : "OFF",
                                             "host" : gethostname(), 
                                             "version" : plgver,
                                             "documentation" : plgdoc,
                                             "configuration" : plgconf})

                    # check plugin state (will update component status)
                    state_thread[plgname] = Thread(None,
                                                   self._check_component_is_running,
                                                   None,
                                                   (plgname, None),
                                                   {})
                    state_thread[plgname].start()

                except:
                    print("Error reading xml file : %s\n%s" % (xml_file, str(traceback.format_exc())))
                    self._log.error("Error reading xml file : %s. Detail : \n%s" % (xml_file, str(traceback.format_exc())))

                # get data from xml file
        return


    def _is_component(self, name):
        '''
        Is a component a plugin ?
        @param name : component name to check
        '''
        for component in self._components:
            if component["name"] == name:
                return True
        return False

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
        for component in self._components:
            if component["name"] == plg:
                for conf in component["configuration"]:
                    conf_content = "%s,%s,%s,%s" % (conf["key"],
                                                conf["type"],
                                                conf["description"],
                                                conf["default"])
                    mess.add_data({'config'+str(conf["id"]) : conf_content})
                mess.add_data({'plugin' :  component["name"]})
                mess.add_data({'description' :  component["description"]})
                mess.add_data({'technology' :  component["technology"]})
                mess.add_data({'status' :  component["status"]})
                mess.add_data({'version' :  component["version"]})
                mess.add_data({'documentation' :  component["documentation"]})
                mess.add_data({'host' : gethostname()})

        self._myxpl.send(mess)


def main():
    ''' Called by the easyinstall mapping script
    '''
    SYS = SysManager()

if __name__ == "__main__":
    main()

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

# $LastChangedBy: domopyx $
# $LastChangedDate: 2009-03-21 00:59:18 +0100 (sam. 21 mars 2009) $
# $LastChangedRevision: 416 $

import re
import sys
from configobj import ConfigObj


_IP_ADDRESS_REGEX = "^" + (r"\.".join(r"([01]?\d\d?|2[0-4]\d|25[0-5])")) + "$"


class ConfigManager():
    '''
    General config manager which can ask user about config settings, check
    results and write config file
    '''

    def __init__(self, settings = [], session = None):
        '''
        Constructor
        @param settings List of tuples defining parameters to ask user for :
        {'name','question','check_regex',['proposed_val1','proposed_val2']}
        check_regex can be None
        Proposed value list can be None.
        If it isn't, the first value is taken as default choice
        '''
        self._settings = settings
        self._session = session

    def ask(self):
        '''
        Ask the user for each entry of self._settings
        '''
        result = {}
        if self._session != None:
            print "**** %s ****\n\n" % self._session.title()
        for entry in self._settings:
            name = entry[0]
            question = entry[1]
            check_re = entry[2]
            proposed_val = entry[3]
            #Build the question
            req = question
            if proposed_val is not None:
                req += "[%s]" % "  ".join(proposed_val)
            res_state_ok = False
            req += " : "
            while not res_state_ok:
                tmp_res = raw_input(req)
                #Check the result
                #If proposed value isn't empty
                if proposed_val != None:
                    #If tmp_res is empty, we choose the default value
                    if tmp_res == "" or tmp_res == None:
                        final_res = proposed_val[0]
                        tmp_res = proposed_val[0] #In case of regex check
                        res_state_ok = True
                     # else:
                     #    if (tmp_res not in proposed_val) and \
                     # (tmp_res.lower() not in proposed_val) and \
                     # (tmp_res.upper() not in proposed_val):
                     #        #Invalid entry
                     #        pass
                    else:
                        #Result is ok for this test
                        res_state_ok = True
                        final_res = tmp_res
                #Check against regex
                if check_re != None:
                    #WARNING : this line will throw an exception if the regex
                    #is badly formatted
                    r = re.compile(check_re)
                    if (r.match(str(tmp_res))):
                        #Result is ok for this test
                        res_state_ok = True
                        final_res = tmp_res
                    else:
                        #The result did not match regex
                        res_state_ok = False
                if not res_state_ok:
                    print "The supplied result isn't correct! Please retry.\n"
            #At this state the provided result is ok
            #We store it
            result[name] = final_res
        return result

    def write(self, filename, datas, section=None):
        '''
        Write data in a filename. May define a section
        '''
        config = ConfigObj(filename)
        if section:
            config[section] = {}
            for k in datas:
                config[section][k] = datas[k]
        else:
            for k in datas:
                config[k] = datas[k]
        config.write()


class genericPluginConfig():
    '''
    Generic list for plugins
    '''

    def __init__(self, ip):
        self.informations = [
            ('address',
            'What is the IP address the plugin must use ?',
            _IP_ADDRESS_REGEX,
            [ip]),
            # ('port',
            #'What is the port the plugin must bind ?',
            #r"^[1-9][0-9]+",
            #None),
            # No need of thyat atm, we'll use the main config parameters
            #('hub_address',
            #'What is the IP address the plugin must connect to ?',
            #_IP_ADDRESS_REGEX
            #None),
            #('hub_port',
            #'What is the port the plugin must connect to ?',
            #r"^[1-9][0-9]+",
            #[3865])
        ]

    def askandwrite(self, file, section):
        config = ConfigManager(self.informations, section)
        self.result = config.ask()
        config.write(file, self.result, section)

    def getvalue(self, value):
        return self.result.get(value, None)


class generalConfig(genericPluginConfig):
    '''
    Ask the user for general configuration and write results
    '''

    def __init__(self):
        '''
        Ask user for general parameters of Domogik to create the main cfg file
        '''
        self.informations = [
#        ('hub_address', 'What is the IP address the xPL system must bind ?',
#                _IP_ADDRESS_REGEX, None),
#        ('hub_port', 'What is the port the xPL system must bind ?',
#                r"^[1-9][0-9]+$", [3865]),
#        ('dmg_port', 'What is the port control script will use ?',
#                r"^[1-9][0-9]+", [3866]),
#        ('source', 'What is the xPL name you want control scripts use ?',
#                None, ['xpl-dmg.domogik']),
        ('log_dir_path', 'What is the path of the log directory ?\n'
                'The directory must exist with good permissions.',
                None, ['/tmp/']),
        ('log_level', 'What is the debug level for logging you want ?',
                None, ['debug', 'info', 'warning', 'error', 'critical']),
        ('pid_dir_path', 'What is the directory for pids file ?',
                None, ['/var/run/domogik/']),
#        ('components_list', 'What are the components you want to enable ?'\
#                ' (comma separated list)', None, ['x10,datetime']),
        ]
        file = "domogik.cfg"
        section = "domogik"
        self.askandwrite(file, section)


class x10Config(genericPluginConfig):
    '''
    Ask the user for specific config for X10 xPL module
    '''

    def __init__(self, ip=None):
        genericPluginConfig.__init__(self, ip=None)
        self.informations.extend([
        ('port', 'What is the port the plugin must bind ?',
                r"^[1-9][0-9]+", [5000]),
        ('source', 'What is the xPL plugin name ?',
                None, ['xpl-x10.domogik']),
        ('heyu_cfg_file', 'What is the full path to Heyu config file ?',
                None, ['/etc/heyu/x10.cfg', '/usr/local/etc/heyu/x10.cfg']),
        ])
        file = "conf.d/x10.cfg"
        section = "x10"
        self.askandwrite(file, section)


class plcbusConfig(genericPluginConfig):
    '''
    Ask the user for specific config for PLCBUS xPL module
    '''

    def __init__(self, ip=None):
        genericPluginConfig.__init__(self, ip=None)
        self.informations.extend([
        ('port', 'What is the port the plugin must bind ?',
                r"^[1-9][0-9]+", [5006]),
        ('source', 'What is the xPL plugin name ?',
                None, ['xpl-plcbus.domogik']),
        ('port_com', 'What is the com number use by PLCBUS-1141 ?',
                r"^[0-9]+", [0]),
        ])
        file = "conf.d/plcbus.cfg"
        section = "plcbus"
        self.askandwrite(file, section)


class senderConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL sender
    '''

    def __init__(self, ip=None):
        genericPluginConfig.__init__(self, ip)
        self.informations.extend([
        ('port', 'What is the port the plugin must bind ?',
                r"^[1-9][0-9]+", [5001]),
        ('source', 'What is the xPL plugin name ?',
                None, ['xpl-send.domogik']),
        ])
        file = "conf.d/send.cfg"
        section = "send"
        self.askandwrite(file, section)


class triggerConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL sender
    '''

    def __init__(self, ip=None):
        genericPluginConfig.__init__(self, ip)
        self.informations.extend([
        ('port', 'What is the port the plugin must bind ?',
                r"^[1-9][0-9]+", [5002]),
        ('source', 'What is the xPL plugin name ?',
                None, ['xpl-trigger.domogik']),
        ])
        file = "conf.d/trigger.cfg"
        section = "trigger"
        self.askandwrite(file, section)


class datetimeConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL datetime module
    '''

    def __init__(self, ip=None):
        genericPluginConfig.__init__(self, ip)
        self.informations.extend([
        ('port', 'What is the port the plugin must bind ?',
                r"^[1-9][0-9]+", [5003]),
        ('source', 'What is the xPL plugin name ?',
                None, ['xpl-datetime.domogik']),
        ])
        file = "conf.d/datetime.cfg"
        section = "datetime"
        self.askandwrite(file, section)


def OneWireConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL OneWire module
    '''

    def __init__(self, ip=None):
        genericPluginConfig.__init__(self, ip)
        self.informations.extend([
        ('port', 'What is the port the plugin must bind ?',
                r"^[1-9][0-9]+", [5004]),
        ('source', 'What is the xPL plugin name ?',
                None, ['xpl-onewiretemp.domogik']),
        ('temperature_delay',
        'What is the delay you want between temperature update (in second) ?',
                r"^[1-9][0-9]+", [15]),
        ])


class SystemManagerConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL datetime module
    '''

    def __init__(self, ip):
        genericPluginConfig.__init__(self, ip)
        self.informations.extend([
        ('port', 'What is the port the manager must bind ?',
                r"^[1-9][0-9]+", [5005]),
        ('source', 'What is the xPL plugin name ?',
                None, ['xpl-sysmanager.domogik']),
        ])
        file = "conf.d/sysmanager.cfg"
        section = "sysmanager"
        self.askandwrite(file, section)


def usage():
    print """
usage : generate_config.py config"
    config : name of the section to reconfigure"
        Can be one of : all, system, plugins, x10, 1wire, send, trigger, \
datetime"
    """
    exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice == "--help":
            usage()
    else:
        usage()

    if choice == 'all':
        ip = generalConfig()
        SystemManagerConfig(ip)
        x10Config(ip)
        plcbusConfig(ip)
        senderConfig(ip)
        triggerConfig(ip)
        datetimeConfig(ip)
    elif choice == 'main':
        generalConfig()
        #SystemManagerConfig()
    elif choice == 'plugins':
        x10Config()
        plcbusConfig()
        senderConfig()
        triggerConfig()
        datetimeConfig()
    elif choice == 'x10':
        x10Config()
    elif choice == 'plcbus':
        plcbusConfig()
    elif choice == 'send':
        senderConfig()
    elif choice == 'trigger':
        triggerConfig()
    elif choice == 'datetime':
        datetimeConfig()

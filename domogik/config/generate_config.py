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

# $LastChangedBy: mschneider $
# $LastChangedDate: 2009-02-07 21:24:27 +0100 (sam. 07 févr. 2009) $
# $LastChangedRevision: 344 $

import re
import sys
from configobj import ConfigObj

class ConfigManager():
    '''
    General config manager which can ask user about config settings, check results and write config file
    '''
    def __init__(self, settings = [], session = None):
        '''
        Constructor 
        @param settings List of tuples defining parameters to ask user for : {'name','question','check_regex',['proposed_val1','proposed_val2']}
        check_regex can be None
        Proposed value list can be None. If it isn't, the first value is taken as default choice
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
                req += " [%s" % proposed_val[0]
                for v in proposed_val[1:]:
                    req += "  %s" % v
                req +=  "]"
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
        #            else:
         #               if (tmp_res not in proposed_val) and (tmp_res.lower() not in proposed_val) and (tmp_res.upper() not in proposed_val):
         #                   #Invalid entry
         #                   pass
                    else:
                        #Result is ok for this test
                        res_state_ok = True
                        final_res = tmp_res
                #Check against regex
                if check_re != None:
                    #WARNING : this line will throw an exception if the regex is badly formatted
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



    def write(self, filename, datas, section=None ):
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

class generalConfig():
    '''
    Ask the user for general configuration and write results
    '''

    def __init__(self):
        '''
        Ask user for general parameters of Domogik to create the main config file
        '''
        informations = [ 
        ('hub_address','What is the IP address the xPL system must bind ?',r"^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$",None),
        ('hub_port','What is the port the xPL system must bind ?',r"^[1-9][0-9]+$",[3865])
        ]
        file = "domogik.cfg"
        section = "domogik"
        config = ConfigManager(informations,section)
        result = config.ask()
        config.write(file, result, section)

class genericPluginConfig():
    '''
    Generic list for plugins
    '''
    def __init__(self):
        self.informations = [
        ('address','What is the IP address the plugin must use ?',r"^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$",None),
#    ('port','What is the port the plugin must bind ?',r"^[1-9][0-9]+", None),
# No need of thyat atm, we'll use the main config parameters
#        ('hub_address','What is the IP address the plugin must connect to ?',r"^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$",None),
#        ('hub_port','What is the port the plugin must connect to ?',r"^[1-9][0-9]+", [3865])
        ]
    
    def askandwrite(self, file, section):
        config = ConfigManager(self.informations,section)
        result = config.ask()
        config.write(file, result, section)

class x10Config(genericPluginConfig):
    '''
    Ask the user for specific config for X10 xPL module
    '''
    def __init__(self):
        genericPluginConfig.__init__(self)
        self.informations.extend([
        ('port','What is the port the plugin must bind ?',r"^[1-9][0-9]+", [5000]),
        ('source','What is the xPL plugin name ?', None,['xpl-x10.domogik']),
        ('heyu_cfg_file','What is the full path to Heyu config file ?', None, ['/etc/heyu/x10.cfg','/usr/local/etc/heyu/x10.cfg'])
        ])
        file = "conf.d/x10.cfg"
        section = "x10"
        self.askandwrite(file, section)

class senderConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL sender
    '''
    def __init__(self):
        genericPluginConfig.__init__(self)
        self.informations.extend([
        ('port','What is the port the plugin must bind ?',r"^[1-9][0-9]+", [5001]),
        ('source','What is the xPL plugin name ?', None,['xpl-send.domogik']),
        ])
        file = "conf.d/send.cfg"
        section = "send"
        self.askandwrite(file, section)

class triggerConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL sender
    '''
    def __init__(self):
        genericPluginConfig.__init__(self)
        self.informations.extend([
        ('port','What is the port the plugin must bind ?',r"^[1-9][0-9]+", [5002]),
        ('source','What is the xPL plugin name ?', None,['xpl-trigger.domogik']),
        ])
        file = "conf.d/trigger.cfg"
        section = "trigger"
        self.askandwrite(file, section)

class datetimeConfig(genericPluginConfig):
    '''
    Ask the user for specific config for the xPL datetime module
    '''
    def __init__(self):
        genericPluginConfig.__init__(self)
        self.informations.extend([
        ('port','What is the port the plugin must bind ?',r"^[1-9][0-9]+", [5003]),
        ('source','What is the xPL plugin name ?', None,['xpl-datetime.domogik']),
        ])
        file = "conf.d/datetime.cfg"
        section = "datetime"
        self.askandwrite(file, section)

def usage():
    print "usage : generate_config.py config"
    print "   config : name of the section to reconfigure"
    print "            Can be one of : all, plugins, x10, 1wire, send, trigger, datetime"
    exit(1)

if __name__ == "__main__":

    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice == "--help":
            usage()
    else:
        usage()

    if choice == 'all':
        generalConfig()
        x10Config()
        senderConfig()
        triggerConfig()
        datetimeConfig()
    elif choice == 'main':
        generalConfig()
    elif choice == 'plugins':
        x10Config() 
        senderConfig()
        triggerConfig()
        datetimeConfig()
    elif choice == 'x10':
        x10Config()
    elif choice == 'send':
        senderConfig()
    elif choice == 'trigger':
        triggerConfig()
    elif choice == 'datetime':
        datetimeConfig()


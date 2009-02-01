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
# $LastChangedDate: 2009-02-01 10:26:36 +0100 (dim 01 fév 2009) $
# $LastChangedRevision: 301 $

import re
from configobj import ConfigObj

class ConfigManager():
    '''
    General config manager which can ask user about config settings, check results and write config file
    '''
    def __init__(self, settings = []):
        '''
        Constructor 
        @param settings List of tuples defining parameters to ask user for : {'name','question','check_regex',['proposed_val1','proposed_val2']}
        check_regex can be None
        Proposed value list can be None. If it isn't, the first value is took as default choice
        '''
        self._settings = settings

    def ask(self):
        '''
        Ask the user for each entry of self._settings
        '''
        result = {}
        for entry in self._settings:
            name = entry[0]
            question = entry[1]
            check_re = entry[2]
            proposed_val = entry[3]
            #Build the question
            req = question
            if proposed_val is not None:
                req += " [%s" % (proposed_val[0].upper())
                for v in proposed_val[1:]:
                    req += "/%s" % v
                req +=  "]"
            res_state_ok = False
            while not res_state_ok:
                tmp_res = raw_input(req)
                #Check the result
                #If proposed value isn't empty
                if proposed_val != None:
                    #If tmp_res is empty, we choose the default value
                    if tmp_res == "":
                        final_res = proposed_val[0]
                        res_state_ok = True
                    else:
                        if (tmp_res not in proposed_val) and (tmp_res.lower() not in proposed_val) and (tmp_res.upper() not in proposed_val):
                            #Invalid entry
                            pass
                        else:
                            #Result is ok for this test
                            res_state_ok = True
                            final_res = tmp_res
                #Check against regex
                if check_re != None:
                    #WARNING : this line will throw an exception if the regex is badly formatted
                    r = re.compile(check_re)
                    if (r.match(tmp_res)):
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
        Write datas in a filename. May define a section
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
        ('hub_port','What is the port the xPL system must bind ?',r"^[1-9][0-9]+$",None)
        ]
        file = "domogik.cfg"
        section = "domogik"
        config = ConfigManager(informations)
        result = config.ask()
        config.write(file, result, section)

if __name__ == "__main__":
    generalConfig()

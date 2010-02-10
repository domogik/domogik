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

Generate configuration

Implements
==========

- ConfigManager
- generalConfig
- genericPluginConfig
- databaseAccess

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

# TODO : rename class names with Uppercase

import os
import re
import sys
import ConfigParser


_IP_ADDRESS_REGEX = "^" + (r"\.".join(r"([01]?\d\d?|2[0-4]\d|25[0-5])")) + "$"


class ConfigManager():
    '''
    General config manager which can ask user about config settings, check
    results and write config file
    '''

    def __init__(self, settings=[], session=None):
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
                    if r.match(str(tmp_res)):
                        #Result is ok for this test
                        res_state_ok = True
                        final_res = tmp_res
                    else:
                        #The result did not match regex
                        res_state_ok = False
                if check_re == None and proposed_val == None:
                    res_state_ok = True
                    final_res = tmp_res
                if not res_state_ok:
                    print "The supplied result isn't correct! Please retry.\n"
            #At this state the provided result is ok
            #We store it
            result[name] = final_res
            final_res = ''
        return result

    def write(self, filename, datas, section=None):
        '''
        Write data in a filename. May define a section
        '''
        config = ConfigParser.ConfigParser()
        config.read(filename)
        if not config.has_section(section):
            config.add_section(section)
        for k in datas:
            config.set(section,k,datas[k])
        f = open(filename, 'wb')
        config.write(f)
        f.close()


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
        result = config.ask()
        config.write(file, result, section)
#        with open(file, 'wb') as configfile:
#                config.write(configfile)

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
#        ('cfg_path', 'What is the main config directory ?',
#            None, ['/etc/domogik/']),
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
        file = "%s/.domogik.cfg" % os.getenv("HOME")
        section = "domogik"
        self.askandwrite(file, section)

class databaseAccess(genericPluginConfig):
    """
    Ask the user for database related parameters
    """

    def __init__(self):
        self.informations = [
                ('db_type', 'Which database will you use ?\n'
                'Must be one of sqlite, mysql, postgres, oracle.\n'
                '"sqlite" is the most simple one and does not need any particular setup.',
                r"^(sqlite|mysql|postgres|oracle)$", None),
                ('db_host','Which host to connect to (empty if sqlite)', None, None),
                ('db_port','Which port to connect to (empty to use the default)', r"^[0_9]*$", None),
                ('db_user','Database user (must exists, empty if sqlite)', None, None),
                ('db_password','Database user password (empty if sqlite)', None, None),
                ('db_name','Database name (empty if sqlite)', None, None),
                ('db_prefix','Core tables prefix (keep default if you don\'t know what it is)',None, ['core']),
                ('db_path','If you use sqlite, define here the absolute path (no "~") to the sqlite database (including file name, empty if not sqlite).\n'
                'Domogik will need write permissions to create the database and write to it.', None, None)
        ]
        file = "%s/.domogik.cfg" % os.getenv("HOME")
        section = "database"
        self.askandwrite(file, section)

class pythonPathes(genericPluginConfig):
    """
    This class doesn't ask the user for config values
    Instead, it make some test to get python path
    """
    def __init__(self):
        file = "%s/.domogik.cfg" % os.getenv("HOME")
        section = "python"
        config = ConfigManager(None, section)
        result = {"path":"%s" % sys.path}
        config.write(file, result, section)

class customPrefix(genericPluginConfig):
    """ This class let the ability for the user to define a custom prefix 
    """
    def __init__(self):
        section = "domogik"
        file = "%s/.domogik.cfg" % os.getenv("HOME")
        self.informations = [
                ('custom_prefix', 'If you have installed domogik with a custom prefix (using --prefix), \
                you *must* specify this prefix now, otherwise keep default value.',
                None, [sys.prefix])
                ]
        self.askandwrite(file, section)
        

def usage():
    print """
usage : generate_config.py
    """
    exit(1)

def main():
    if len(sys.argv) > 1:
        choice = sys.argv[1]
        if choice == "--help":
            usage()
    generalConfig()
    #deprecated
#    pythonPathes()
    customPrefix()

    db = raw_input('Do you want to configure the database settings ?\n'
    'This is only needed if you are on the host which will host database. [y/N]')
    if db == 'y' or db == 'Y':
        databaseAccess()

if __name__ == "__main__":
    main()

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

Load config from file

Implements
==========

- Loader

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

global config_path

####################################################
#       DON'T CHANGE ANYTHING AFTER THIS LINE      #
####################################################
import os
import pwd 
import ConfigParser
import threading


class Loader():
    '''
    Parse Domogik config files
    '''

    config = None 

    def __init__(self, plugin_name=None):
        '''
        Load the configuration for a part of the Domogik system
        @param plugin_name name of the plugin to load config from
        '''
        self.main_conf_name = "domogik.cfg"
        self.valid_files = None
        self.plugin_name = plugin_name

        # get home dir
        sys_file = ''
        if os.path.isfile('/etc/default/domogik'):
            sys_file = '/etc/default/domogik'
        elif os.path.isfile('/etc/conf.d/domogik'):
            sys_file = '/etc/conf.d/domogik'
        homedir = os.getenv('HOME')
        if sys_file != '':
            f = open(sys_file)
            data = f.readlines()
            data = filter(lambda s:s.startswith('DOMOGIK_USER'), data)[0]
            homedir = pwd.getpwnam(data.strip().split('=')[1]).pw_dir

        self.config_file = homedir + "/.domogik/" + self.main_conf_name

    def get_config_files_path(self):
        '''
        Return config file path
        '''
        return self.__class__.valid_files

    def load(self, custom_path = "", refresh = False):
        '''
        Parse the config
        @param custom_path : Custom path to config file, will superseed others
        @param refresh : force refreshing config
        @return pair (main_config, plugin_config)
        '''
        sys_file = ''
        #if os.path.isfile('/etc/default/domogik'):
        #    sys_file = '/etc/default/domogik'
        #elif os.path.isfile('/etc/conf.d/domogik'):
        #    sys_file = '/etc/conf.d/domogik'
        #homedir = os.getenv('HOME')
        #if sys_file != '':
        #    f = open(sys_file)
        #    data = f.readlines()
        #    data = filter(lambda s:s.startswith('DOMOGIK_USER'), data)[0]
        #    homedir = pwd.getpwnam(data.strip().split('=')[1]).pw_dir
        main_result = {}
        if self.__class__.config == None or refresh == True:
            self.__class__.config = ConfigParser.ConfigParser()
            files = self.__class__.config.read([custom_path, 
                self.config_file])
            self.__class__.valid_files = files
        result = self.__class__.config.items('domogik')
        main_result = {}
        for k, v in result:
            main_result[k] = v
        #Check the plugin conf file if defined
        if self.plugin_name == None:
            return (main_result, None)

        if self.plugin_name:
            return (main_result, self.__class__.config.items(self.plugin_name))
        else:
            #If we're here, there is no plugin config
            return (main_result, None)

    def set(self, section, key, value):
        """ Set a key value for a section in config file and write it
            WARNING : using this function make config fil change : 
            - items are reordered
            - comments are lost
            @param section : section of config file
            @param key : key
            @param value : value
        """
        self.__class__.config.set(section, key, value)
        with open(self.config_file, "wb") as configfile:
            self.__class__.config.write(configfile)

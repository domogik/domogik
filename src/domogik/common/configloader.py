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
@copyright: (C) 2007-2012 Domogik project
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
import time
from threading import Semaphore

MAIN_CONFIG_FILE_NAME = "domogik.cfg"

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
        # Semaphore init
        self.__class__.sema_load = Semaphore(value=1)

        if hasattr(self.__class__, "config") == False:
            self.__class__.config = None
        self.__class__.valid_files = []
        self.plugin_name = plugin_name

        config_dir = self.get_config_dir()

        self.config_file = config_dir + MAIN_CONFIG_FILE_NAME

    def get_config_dir(self):
        ''' Get homedir 
        '''
        sys_file = ''
        #if os.path.isfile('/etc/default/domogik'):
        #    sys_file = '/etc/default/domogik'
        #elif os.path.isfile('/etc/conf.d/domogik'):
        #    sys_file = '/etc/conf.d/domogik'
        #else:
        #    raise RuntimeError("No /etc/default/domogik of /etc/conf.d/domogik exists")

        #f = open(sys_file)
        #data = f.readlines()
        #data = filter(lambda s:s.startswith('DOMOGIK_USER'), data)[0]
        #configdir = pwd.getpwnam(data.strip().split('=')[1]).pw_dir
        #return configdir + "/.domogik/"
        return "/etc/domogik/"

    def get_config_files_path(self):
        '''
        Return config file path
        '''
        return self.__class__.valid_files

    def load(self, refresh = False):
        '''
        Parse the config
        @param refresh : force refreshing config
        @return pair (main_config, plugin_config)
        '''
        self.__class__.sema_load.acquire()

        # need to reread or not ?
        if self.__class__.config == None or refresh == True:
            do_read = True
        else:
            do_read = False

        # read config file
        if do_read == True:
            self.__class__.config = ConfigParser.ConfigParser()
            files = self.__class__.config.read([self.config_file])
            self.__class__.valid_files = files

        # get 'domogik' config part
        result = self.__class__.config.items('domogik')
        domogik_part = {}
        for k, v in result:
            domogik_part[k] = v

        # no other config part requested
        if self.plugin_name == None:
            self.__class__.sema_load.release()
            return (domogik_part, None)

        # Get requested (if so) config part
        if self.plugin_name:
            ret =  (domogik_part, self.__class__.config.items(self.plugin_name))
            self.__class__.sema_load.release()
            return ret

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

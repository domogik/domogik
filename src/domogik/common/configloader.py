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

####################################################
#       DON'T CHANGE ANYTHING AFTER THIS LINE      #
####################################################
import os
import pwd 
import ConfigParser
import threading
import time
import fcntl


CONFIG_FILE = "/etc/domogik/domogik.cfg"
LOCK_FILE = "/var/lock/domogik/config.lock"

class Loader():
    '''
    Parse Domogik config files
    '''

    config = None 

    def __init__(self, part_name=None):
        '''
        Load the configuration for a part of the Domogik system
        @param part_name name of the part to load config from
        '''
        #if hasattr(self.__class__, "config") == False:
        #    self.__class__.config = None
        self.config = None
        self.part_name = part_name

    def load(self):
        '''
        Parse the config
        @return pair (main_config, plugin_config)
        '''
        # lock the file
        if not os.path.exists(os.path.dirname(LOCK_FILE)):
            try:
                # note : default creation mode : 0777
                os.mkdir(os.path.dirname(LOCK_FILE)) 
            except:
                raise Exception, "ConfigLoader : unable to create the directory '%s'" % os.path.dirname(LOCK_FILE)
        if not os.path.exists(LOCK_FILE):
            try:
                file = open(LOCK_FILE, "w")
                file.write("")
                file.close()
            except:
                raise Exception, "ConfigLoader : unable to create the lock file '%s'" % LOCK_FILE
        file = open(LOCK_FILE, "r+")
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)

        # read config file
        self.config = ConfigParser.ConfigParser()
        cfg_file = open(CONFIG_FILE)
        self.config.readfp(cfg_file)

        # get 'domogik' config part
        result = self.config.items('domogik')
        domogik_part = {}
        for k, v in result:
            domogik_part[k] = v

        # no other config part requested
        if self.part_name == None:
            result = (domogik_part, None)

        # Get requested (if so) config part
        if self.part_name:
            result =  (domogik_part, self.config.items(self.part_name))

        cfg_file.close()
        file.close()
        return result

    def set(self, section, key, value):
        """ Set a key value for a section in config file and write it
            WARNING : using this function make config fil change : 
            - items are reordered
            - comments are lost
            @param section : section of config file
            @param key : key
            @param value : value
        """
        # Check load is called before this function
        if self.config == None:
            raise Exception, "ConfigLoader : you must use load() before set() function"
        self.config.set(section, key, value)
        with open(CONFIG_FILE, "wb") as configfile:
            self.config.write(configfile)

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
import fcntl
import codecs
import chardet
try:
    # from python3 onwards
    import configparser
except ImportError:
    # python 2
    import ConfigParser as configparser


CONFIG_FILE = "/etc/domogik/domogik.cfg"
CONFIG_LCOATION = "/etc/domogik/"
LOCK_FILE = "/var/lock/domogik/config.lock"

class Loader(object):
    '''
    Parse Domogik config files
    '''

    config = None

    def __init__(self, part_name=None, cfile="domogik.cfg"):
        '''
        Load the configuration for a part of the Domogik system
        @param part_name name of the part to load config from
        '''
        #if hasattr(self.__class__, "config") == False:
        #    self.__class__.config = None
        self.cfile = "{0}{1}".format(CONFIG_LCOATION, cfile)
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
                raise Exception("ConfigLoader : unable to create the directory '{0}'".format(os.path.dirname(LOCK_FILE)))
        if not os.path.exists(LOCK_FILE):
            try:
                lfile = open(LOCK_FILE, "w")
                lfile.write("")
                lfile.close()
            except:
                raise Exception("ConfigLoader : unable to create the lock file '{0}'".format(LOCK_FILE))
        lfile = open(LOCK_FILE, "r+")
        fcntl.lockf(lfile, fcntl.LOCK_EX)

        # read config file
        self.config = configparser.ConfigParser()

        # find the configuration file encoding (default will be ascii, but depending on characters in the butler name it could be different!)
        tmp = open(self.cfile).read()
        encoding = chardet.detect(tmp)['encoding']
        # sample result of detect() :
        #{'confidence': 0.9275988341086866, 'encoding': 'ISO-8859-2'}

        #cfg_file = codecs.open(self.cfile, "r", encoding)
        #self.config.readfp(cfg_file)
        #cfg_file.close()

        # python 3.2+
        try:
            self.config.read(self.cfile, encoding=encoding)
        # python < 3.2
        except TypeError:
            cfg_file = codecs.open(self.cfile, "r", encoding)
            self.config.readfp(cfg_file)
            cfg_file.close()

        # release the file lock
        fcntl.lockf(lfile, fcntl.LOCK_UN)
        lfile.close()

        # get 'domogik' config part
        domogik_part = {}
        try:
            result = self.config.items('domogik')
            for key, val in result:
                domogik_part[key] = val
        except configparser.NoSectionError:
            pass

        # no other config part requested
        if self.part_name is None:
            result = (domogik_part, None)

        # Get requested (if so) config part
        if self.part_name:
            result = (domogik_part, self.config.items(self.part_name))

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
        if self.config is None:
            raise Exception("ConfigLoader : you must use load() before set() function")
        self.config.set(section, key, value)
        with open(self.cfile, "wb") as configfile:
            self.config.write(configfile)

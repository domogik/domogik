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

Load config from file

Implements
==========

- Loader.__init__(self, module_name=None)
- Loader.load(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

global config_path

####################################################
#       DON'T CHANGE ANYTHING AFTER THIS LINE      #
####################################################
from os.path import *
import os
import ConfigParser


class Loader():
    '''
    Parse Domogik config files
    '''

    def __init__(self, module_name=None):
        '''
        Load the configuration for a part of the Domogik system
        @param module_name name of the module to load config from
        '''
        self.main_conf_name = "domogik.cfg"
        self.module_name = module_name

    def load(self):
        '''
        Parse the config
        @return pair (main_config, plugin_config)
        '''
        main_result = {}
        config = ConfigParser.ConfigParser()
        config.read([os.getenv("HOME") + "/." + self.main_conf_name,
            '/etc/' + self.main_conf_name,
            '/usr/local/etc/' + self.main_conf_name])
        result = config.items('domogik')
        main_result = {}
        for k, v in result:
            main_result[k] = v
        #Check the plugin conf file if defined
        if self.module_name == None:
            return (main_result, None)

        if self.module_name:
            return (main_result, config.items(self.module_name))
        else:
            #If we're here, there is no plugin config
            return (main_result, None)

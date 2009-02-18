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
# $LastChangedDate: 2009-02-18 16:08:56 +0100 (mer. 18 févr. 2009) $
# $LastChangedRevision: 370 $


#Path to the configuration directory 
global config_path
config_path = "../config"

####################################################
#       DON'T CHANGE ANYTHING AFTER THIS LINE      #
####################################################
from os.path import *
import os
from configobj import ConfigObj
import logger

class Loader():
    '''
    Parse Domogik config files
    '''
    def __init__(self, module_name=None):
        '''
        Load the configuration for a part of the Domogik system
        @param module_name name of the module to load config from
        '''
        global config_path
        self.main_conf_name = "domogik.cfg"
        l = logger.Logger(module_name)
        self._log = l
        #Format the path
        if config_path[-1] != "/":
            config_path += "/"

        #Check the main conf file
        file_with_path = config_path + self.main_conf_name
        if not exists(file_with_path):
            self._log.error("The main config file can't be found !\nMake sure %s exists." %file_with_path)
            exit(1)

        self.module_name = module_name

    def load(self):
        '''
        Parse the config
        @return pair (main_config, plugin_config)
        '''
        global config_path
        main_result = {}
        config = ConfigObj(config_path + self.main_conf_name)
        main_result = config['domogik']

        #Check the plugin conf file if defined
        if self.module_name == None:
            return (main_result, None)

        #To find the plugin conf, we try all files in conf.d until we find the corresponding section
        plugin_conf_dir = config_path + "conf.d/"
        if exists(plugin_conf_dir + self.module_name + ".cfg"):
            plugin_config = ConfigObj(plugin_conf_dir + self.module_name + ".cfg")
            if plugin_config.has_key(self.module_name):
                return (main_result, plugin_config[self.module_name])

        #If we are here, it's because the plugin conf file hasn't the same name as the plugin name
        files = os.listdir(plugin_conf_dir)
        for file in files:
            if isfile(plugin_conf_dir + file):
                plugin_config = ConfigObj(plugin_conf_dir + self.module_name + ".cfg")
                if plugin_config.has_key(self.module_name):
                    return (main_result, plugin_config[self.module_name])

        #If we're here, there is no plugin config
        return (main_result, None)

if __name__ == "__main__":
    l = Loader('x10')
    print l.load()



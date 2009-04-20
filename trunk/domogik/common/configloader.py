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
# $LastChangedDate: 2009-03-04 22:29:01 +0100 (mer. 04 mars 2009) $
# $LastChangedRevision: 404 $

import os
from domogik.xpl.lib.xplconnector import *

#Path to the configuration directory
global config_path
config_path = "/home/maxence/domogik/trunk/domogik/config"

####################################################
#       DON'T CHANGE ANYTHING AFTER THIS LINE      #
####################################################
from os.path import *
import os
from configobj import ConfigObj


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
        #Format the path
        if config_path[-1] != "/":
            config_path += "/"

        #Check the main conf file
        file_with_path = config_path + self.main_conf_name
        if not exists(file_with_path):
            raise ValueError("The main config file can't be found !\n"
                    "Make sure %s exists." % file_with_path)
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

        #To find the plugin conf, we try all files in conf.d until we
        #find the corresponding section
        plugin_conf_dir = config_path + "conf.d/"
        if exists(plugin_conf_dir + self.module_name + ".cfg"):
            plugin_config = ConfigObj(plugin_conf_dir + self.module_name +
                    ".cfg")
            if self.module_name in plugin_config:
                return (main_result, plugin_config[self.module_name])

        #If we are here, it's because the plugin conf file hasn't the same
        #name as the plugin name
        files = os.listdir(plugin_conf_dir)
        for file in files:
            if isfile(plugin_conf_dir + file):
                plugin_config = ConfigObj(plugin_conf_dir + self.module_name +
                        ".cfg")
                if self.module_name in plugin_config:
                    return (main_result, plugin_config[self.module_name])

        #If we're here, there is no plugin config
        return (main_result, None)

class Query():
	'''
	Query throw xPL network to get a config item
	'''
	def __init__(self):
		'''
		Init the query system and connect it to xPL network
		'''

		l = logger.Logger('queryconfig')
		self._log = l.get_logger()
		self.__myxpl = Manager(module_name='queryconfig')
		self._log.debug("Init config query instance")

	def query(technology, key, element = None):
		'''
		Ask the config system for the value
		@param technology : the technology of the item requesting the value, must exists in the config database
		@param element : the name of the element which requests config, None if
		it's a technolgy global parameter
		@param key : the key to fetch corresponding value
		'''
		Listener(self._query_cb, self.__myxpl, {'schema':'domogik.config','type':'xpl-stat'})
		mess = Message()
		mess.set_type('xpl-trig')
		mess.set_schema('domogik.config')
		mess.set_data_key('technology', technology)
		mess.set_data_key('element', element)
		mess.set_data_key('key', key)
	
	def _query_cb(self, message):
		'''
		Callback to receive message after a query() call
		@param message : the message received
		'''
		return message.ket_key_value('value')

if __name__ == "__main__":
    l = Loader('x10')
    print l.load()

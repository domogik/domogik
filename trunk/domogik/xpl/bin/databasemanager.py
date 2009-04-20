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

# $LastChangedBy:$
# $LastChangedDate:$
# $LastChangedRevision:$

from domogik.xpl.lib.xplconnector import *
from domogik.common.configloader import *
from sqlalchemy import *

class DBConnector():
	'''
	Manage the connection between database and the xPL stuff
	Should be the *only* object to access the database in the core side
	'''

	def __init__(self):
		'''
		Initialize database and xPL connection
		'''
        self.__myxpl = Manager(module_name='database_manager')
		Listener(self._request_config_cb, self.__myxpl,
		{'schema':'domogik.config','type':'xpl-cmnd'})
        cfgloader = Loader('database')
        config = cfgloader.load()[1]
		
		#Build database url
		db_url = "%s://" % config['type']
		if config['username']:
			db_url += config['username']
			if config['password']:
				db_url += ':%s' % config['password']
			db_url += '@'
		db_url += "%s" % config['host']
		if config['port']:
			db_url += ':%s' % config['port']
		db_url += '/%s' % config['db_name']

		db = create_engine(db_url)
		self._metadata = BoundMetaData(db)
		self._prefix = config['prefix']

	def _request_config_cb(self, message):
		'''
		Callback to receive a request for some config stuff
		@param message : the xPL message
		'''
		techno = message.get_key_value('technology')
		key = message.get_key_value('key')
		element = message.get_key_value('element')
		if element:
			return self._fetch_elmt_config(techno, element, key)
		else:	
			return self._fetch_techno_config(techno, key)

	def _fetch_elmt_config(self, techno, element, key):
		'''
		Fetch an element's config value in the database
		@param techno : the technology of the element
		@param element :  the name of the element
		@param key : the key of the config tuple to fetch
		'''
		elmt_config = Table(self._prefix + 'config_element', self._metadata, autoload=True)
		s = users.select((elmt_config.c.name == element) & (elmt_config.c.key ==
		key) && (elmt_config.c.))



	def _update_stat(self, message):
		#TODO
		pass

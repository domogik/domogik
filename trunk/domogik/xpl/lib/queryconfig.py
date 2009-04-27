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

from domogik.xpl.lib.xplconnector import *
import domogik.common.logger

class Query():
    '''
    Query throw xPL network to get a config item
    '''
    def __init__(self, xpl):
        '''
        Init the query system and connect it to xPL network
        '''

        l = logger.Logger('queryconfig')
        self._log = l.get_logger()
        self.__myxpl = xpl
        self._log.debug("Init config query instance")
        #

    def query(self, technology, key, result, element = ''):
        '''
        Ask the config system for the value
        @param technology : the technology of the item requesting the value,
        must exists in the config database
        @param element : the name of the element which requests config, None if
        it's a technolgy global parameter
        @param key : the key to fetch corresponding value
        '''
        self._res = result
        Listener(self._query_cb, self.__myxpl,
                {'schema': 'domogik.config', 'type': 'xpl-stat'})
        mess = Message()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.config')
        mess.set_data_key('technology', technology)
        mess.set_data_key('element', element)
        mess.set_data_key('key', key)
        self.__myxpl.send(mess)
        self._res.get_lock().wait()

    def _query_cb(self, message):
        '''
        Callback to receive message after a query() call
        @param message : the message received
        '''
        self._log.debug("Config value received : %s" %
                message.get_key_value('value'))
        self._res.set_value(message.get_key_value('value'))
        self._res.get_lock().set()

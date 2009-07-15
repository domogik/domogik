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

Fetch configuration items using xPL

Implements
==========

- Query.__init__(self, xpl)
- Query.query(self, technology, key, result, element = '')
- Query._query_cb(self, message)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

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
        @param key : the key to fetch corresponding value, if it's an empty string,
        all the config items for this technology will be fetched
        '''
        Listener(self._query_cb, self.__myxpl,{'schema': 'domogik.config', 'type': 'xpl-stat'})
        self._res = result
        mess = Message()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.config')
        mess.set_data_key('technology', technology)
        mess.set_data_key('element', element)
        mess.set_data_key('key', key)
        self._key = key
        self.__myxpl.send(mess)
        print "Wait for answer"
        self._res.get_lock().wait()
        print "answer received"

    def _query_cb(self, message):
        '''
        Callback to receive message after a query() call
        @param message : the message received
        '''
        print "Answer received"
        #self.__myxpl.del_listener(self._list)
        self._log.debug("Config value received : %s" %
                message.get_key_value(self._key))
        result = message.get_key_value(self._key)
        self._res.set_value(result)
        self._res.get_lock().set()


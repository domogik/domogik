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

from domogik.common import logger
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from socket import gethostname


class Query():
    '''
    Query throw xPL network to get a config item
    '''

    def __init__(self, xpl, log):
        '''
        Init the query system and connect it to xPL network
        @param xpl : the XplManager instance (usually self.myxpl)
        @param log : a Logger instance (usually took from self.get_my_logger())
        '''
        self.log = log
        self.__myxpl = xpl
        self.log.debug("Init config query instance")
        self._keys = {}

    def __del__(self):
        print "End query"

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
        print "new query for t = %s, k = %s" % (technology, key)
        Listener(self._query_cb, self.__myxpl, {'schema': 'domogik.config', 'xpltype': 'xpl-stat',
                                                'technology': technology, 'hostname' : gethostname()})
        self._keys[key] = result
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_schema('domogik.config')
        mess.add_data({'technology': technology})
        mess.add_data({'hostname': gethostname()})
        if element:
            mess.add_data({'element': element})
        mess.add_data({'key': key})
        self.__myxpl.send(mess)
        # The key may already be removed if the network is really fast
        if key in self._keys:
            try:
                self._keys[key].get_lock().wait()
            except KeyError:
                pass
        print "finish query"

    def _query_cb(self, message):
        '''
        Callback to receive message after a query() call
        @param message : the message received
        '''
        print "Answer received"
        result = message.data
        for r in self._keys:
            if r in result:
                self.log.debug("Config value received : %s : %s" % (r, result[r]))
                res = self._keys.pop(r)
                res.set_value(result)
                res.get_lock().set()
                break

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

- Query

@author: Maxence Dunnewind <maxence@dunnewind.net>
         Fritz SMH <fritz.smh@gmail.com>
         Cereal
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from threading import Event

from domogik.common.utils import get_sanitized_hostname 

import zmq
from domogik.mq.message import MQMessage
from domogik.mq.reqrep.client import MQSyncReq

QUERY_CONFIG_WAIT = 5

class Query():

    def __init__(self, zmq, log):
        self.qry = QueryMQ(zmq, log)

    def query(self, id, key):
        return self.qry.query(id, key)

    def set(self, id, key, value):
        # TODO
        self.log.error("Config set feature not yet implemented")




class QueryMQ():
    '''
    Query to the mq to find the config
    '''
    def __init__(self, zmq, log):
        '''
        Init the query system and connect it to xPL network
        @param zmq : the zMQ context
        @param log : a Logger instance (usually took from self.log))
        '''
        self._zmq = zmq
        self._log = log
        self._log.debug("Init config query(mq) instance")
        self.cli = MQSyncReq(self._zmq)

    def query(self, id, key):
        '''
        Ask the config system for the value. Calling this function will make
        your program wait until it got an answer

        @param id : the plugin of the item requesting the value, must exists in the config database
        @param key : the key to fetch corresponding value
        '''
        msg = MQMessage()
        msg.set_action('config.get')
        msg.add_data('type', 'plugin')
        msg.add_data('id', id)
        msg.add_data('host', get_sanitized_hostname())
        msg.add_data('key', key)
        self._log.info("Request query config for key {0}".format(key))
        ret = self.cli.request('dbmgr', msg.get(), timeout=QUERY_CONFIG_WAIT)

        ### no response from dbmgr
        if ret is None:
            self._log.error("Query config for plugin {0} on host {1}, key {2} : no response from dbmgr".format(id, get_sanitized_hostname(), key))
            return None

        ### response from dbmgr
        else:
            if ret._data['status']:
                self._log.debug("Query config : successfull response : {0}".format(ret))
                return str(ret._data['value'])
            else:
                self._log.error("Query config : error returned. Reason : {0}".format(ret._data['reason']))
                return None



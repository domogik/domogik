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
import zmq
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
from domogik.common import logger
from domogik.common.utils import get_sanitized_hostname


QUERY_CONFIG_WAIT = 5

class Query():
    """ Query for core components and plugins
    """

    def __init__(self, zmq, log, host):
        self.qry = QueryMQ(zmq, log, host)

    def query(self, type, name, key = None):
        return self.qry.query(type, name, key)

    def set(self, type, name, key, value):
        # TODO
        self.log.error(u"Config set feature not yet implemented")


class QueryForBrain():
    """ Query for brain packages
        Brain packages have no running parts, so no logger and no zmq context...
        So we create them
    """

    def __init__(self):
        ### init zmq
        zmqc = zmq.Context() 

        ### init logger
        loginst = logger.Logger('butler')
        log = loginst.get_logger('butler')

        self.qry = QueryMQ(zmqc, log, get_sanitized_hostname())

    def query(self, type, name, key = None):
        return self.qry.query(type, name, key)



class QueryMQ():
    '''
    Query to the mq to find the config
    '''
    def __init__(self, zmq, log, host):
        '''
        Init the query system and connect it to xPL network
        @param zmq : the zMQ context
        @param log : a Logger instance (usually took from self.log))
        '''
        self._zmq = zmq
        self._log = log
        self._host = host
        self._log.debug("Init config query(mq) instance")
        self.cli = MQSyncReq(self._zmq)

    def query(self, type, name, key = None):
        '''
        Ask the config system for the value. Calling this function will make
        your program wait until it got an answer

        @param type : the client type
        @param name : the client name of the item requesting the value, must exists in the config database
        @param key : the key to fetch corresponding value
        @return : the value if key != None
                  a dictionnary will all keys/values if key = None
        '''
        msg = MQMessage()
        msg.set_action('config.get')
        msg.add_data('type', type)
        msg.add_data('name', name)
        msg.add_data('host', self._host)
        if key != None:
            msg.add_data('key', key)
        else:
            key = "*"
        self._log.info("Request query config for client {0} : key {1}".format(name, key))
        ret = self.cli.request('admin', msg.get(), timeout=QUERY_CONFIG_WAIT)

        ### no response from admin
        if ret is None:
            self._log.error("Query config for client {0} on host {1}, key {2} : no response from admin".format(name, self._host, key))
            return None

        ### response from admin
        else:
            dat = ret.get_data()
            if dat['status']:
                self._log.debug("Query config : successfull response : {0}".format(ret))
                if key == "*":
                    return dat['data']
                else:
                    val = dat['value']
                    # do some cast
                    if val == "None":
                        val = None
                    return val
            else:
                self._log.error("Query config : error returned. Reason : {0}".format(dat['reason']))
                return None



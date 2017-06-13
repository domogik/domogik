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
from domogik.common.database import DbHelper, DbHelperException
import traceback

QUERY_CONFIG_WAIT = 5

class Query():
    """ Query for core components and plugins
    """

    def __init__(self, log, host, zmq=None):
        """If zmq is not None query are get by MQ from admin. Must be used for Plugin not locate on domogik server
            Else direct DbHelper access is use (better performance)"""
        if zmq is None :
            self.qry = QueryDB(log, host)
        else :
            self.qry = QueryMQ(zmq, log, host)

    def query(self, type, name, key = None):
        return self.qry.query(type, name, key)

    def set(self, type, name, key, value):
        # TODO
        self._log.error(u"Config set feature not yet implemented")


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
        @param log : a Logger instance (usually took from self.log)
        @param host : client hostname
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
        self._log.info("Request query config from MQ for client {0} : key {1}".format(name, key))
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

class QueryDB():
    '''
    Query to the DBHelper to find the config
    '''
    def __init__(self, log, host):
        '''
        Init the query system and connect it to DBHelper
        @param log : a Logger instance (usually took from self.log)
        @param host : client hostname
        '''
        self._db = DbHelper()
        self._log = log
        self._host = host
        self._log.debug("Init config query(DB) instance")

    def query(self, type, name=None, key = None):
        '''
        Ask the config system for the value. Calling this function will make
        your program wait until it got an answer

        @param type : the client type
        @param name : the client name of the item requesting the value, must exists in the config database
        @param key : the key to fetch corresponding value
        @return : the value if key != None
                  a dictionnary will all keys/values if key = None
        '''
        self._log.info("Request query config from DBHelper for client {0} : key {1}".format(name, key))

        if type not in ["plugin", "brain", "interface"]:
            self._log.error(u"Configuration request not available for type={0}".format(type))
            return None

        if name is None:
            self._log.error(u"Config request : missing 'name' field")
            return None

        if key is None:
            get_all_keys = True
            key = "*"
        else:
            get_all_keys = False

        with self._db.session_scope():
            try:
                if get_all_keys == True:
                    config = self._db.list_plugin_config(type, name, self._host)
                    self._log.info(u"Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, config))
                    json_config = {}
                    for elt in config:
                        json_config[elt.key] = self.convert(elt.value)
                    return json_config
                else:
                    value = self._fetch_techno_config(name, type, key)
                    # temporary fix : should be done in a better way (on db side)
                    value = self.convert(value)
                    self._log.info(u"Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, value))
                    return value
            except:
                self._log.error(u"Error while getting configuration for '{0} {1} on {2}, key {3}' : {4}".format(type, name, self._host, key, traceback.format_exc()))
                return None

    def _fetch_techno_config(self, name, type, key):
        '''
        Fetch a plugin global config value in the database
        @param name : the plugin of the element
        @param host : hostname
        @param key : the key of the config tuple to fetch
        '''
        try:
            try:
                result = self._db.get_plugin_config(type, name, self._host, key)
                # tricky loop as workaround for a (sqlalchemy?) bug :
                # sometimes the given result is for another plugin/key
                # so while we don't get the good data, we loop
                # This bug happens rarely
                while result.id != name or \
                   result.type != type or \
                   result.hostname != self._host or \
                   result.key != key:
                   self._log.debug(u"Bad result : {0}-{1}/{2} != {3}/{4}".format(result.id, result.type, result.key, name, key))
                   result = self._db.get_plugin_config(type, name, self._host, key)
                val = result.value
                if val == '':
                    val = None
                return val
            except AttributeError:
                # if no result is found
                #self_.log.error(u"Attribute error : {0}".format(traceback.format_exc()))
                return None
        except:
            msg = "No config found host={0}, plugin={1}, key={2}".format(self._host, name, key)
            self._log.warning(msg)
            return None

    def convert(self, data):
        """ Do some conversions on data
        """
        if data == "True":
            data = True
        if data == "False":
            data = False
        return data

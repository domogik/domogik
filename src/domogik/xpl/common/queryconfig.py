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
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from threading import Event
#from domogik.common import logger
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import Loader

QUERY_CONFIG_NUM_TRY = 20
QUERY_CONFIG_WAIT = 5


class Query():
    '''
    Query throw xPL network to get a config item
    '''

    def __init__(self, xpl, log):
        '''
        Init the query system and connect it to xPL network
        @param xpl : the XplManager instance (usually self.myxpl)
        @param log : a Logger instance (usually took from self.log))
        '''
        self.log = log
        self.__myxpl = xpl
        self.log.debug("Init config query instance")
        self._keys = {}
        self._l = {}
        self._result = None

        # Check in config file is target is forced
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        if conf.has_key('config_provider'):
            self.target = "domogik-dbmgr.%s" % conf["config_provider"]
            msg = "Force config provider to '%s'" % self.target
            #print("Query config : %s" % msg)
            self.log.debug(msg)
        else:
            self.target = "*"
        if conf.has_key('query_xpl_timeout'):
            try:
                self.query_timeout = int(conf["query_xpl_timeout"])
                msg = "Set query timeout to '%s' from domogik.cfg" % self.query_timeout
                self.log.debug(msg)
            except ValueError:
                #There is an error in domogik.cfg. Set it to default.
                self.query_timeout = 10
                msg = "Error in domogik.cfg. query_xpl_timeout ('%s') is not an integer." % conf["query_xpl_timeout"]
                self.log.error(msg)
        else:
            #There is not option in domogik.cfg. Set it to default.
            self.query_timeout = 10

    #def __del__(self):
    #    print("Query config : end query")

    def set(self, technology, key, value):
        '''
        Send a xpl message to set value for a param

        @param technology : the technology of the item
        @param key : the key to set corresponding value,
        @param value : the value to set
        '''
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_target(self.target)
        mess.set_schema('domogik.config')
        mess.add_data({'technology': technology})
        mess.add_data({'hostname': self.__myxpl.p.get_sanitized_hostname()})
        mess.add_data({'key': key})
        mess.add_data({'value': value})
        self.__myxpl.send(mess)

    def query(self, technology, key, element = '', nb_test = QUERY_CONFIG_NUM_TRY):
        '''
        Ask the config system for the value. Calling this function will make
        your program wait until it got an answer

        @param technology : the technology of the item requesting the value,
        must exists in the config database
        @param element : the name of the element which requests config, None if
        it's a technolgy global parameter
        @param key : the key to fetch corresponding value, if it's an empty string,
        all the config items for this technology will be fetched
        '''
        if nb_test == 0:
            raise RuntimeError("Maximum tries to get config reached")
         

        msg = "QC : ask > h=%s, t=%s, k=%s" % \
            (self.__myxpl.p.get_sanitized_hostname(), technology, key)
        print(msg)
        self.log.debug(msg)
        l = Listener(self._query_cb, self.__myxpl, {'schema': 'domogik.config',
                                                    'xpltype': 'xpl-stat',
                                                    'technology': technology,
                                                    'hostname' : self.__myxpl.p.get_sanitized_hostname()})
        self._keys[key] = Event()
        self._l[key] = l
        mess = XplMessage()
        mess.set_type('xpl-cmnd')
        mess.set_target(self.target)
        mess.set_schema('domogik.config')
        mess.add_data({'technology': technology})
        mess.add_data({'hostname': self.__myxpl.p.get_sanitized_hostname()})
        if element:
            mess.add_data({'element': element})
        mess.add_data({'key': key})

        try:
            self.__myxpl.send(mess)
            self._keys[key].wait(self.query_timeout)
            if not self._keys[key].is_set():
                msg = "No answer received for t = %s, k = %s, check your xpl setup" % \
                    (technology, key)
                self.log.error(msg)
                #raise RuntimeError(msg)
                self.query(technology, key, element, nb_test - 1)
        except KeyError:
            pass

        if self._result[key] != "None":
            return self._result[key]
        else:
            return None

    def _query_cb(self, message):
        '''
        Callback to receive message after a query() call
        @param message : the message received
        '''
        result = message.data
        for r in self._keys:
            try:
                msg = "QC : res > h=%s, t=%s, k=%s, v=%s" % \
                    (result["hostname"], result["technology"], r, result[r])

            except KeyError:
                errMsg = "It seems that you received configuration elements from 2 dbmgr components. Please check if you have 2 domogik main hosts on your lan. If so, you should configure 'config_provider' in /etc/domogik/domogik.cfg. Waiting for '%s', received '%s'" % (r, result)
                print errMsg
                self.log.error(errMsg)
                return
            print(msg)
            self.log.debug(msg)
            if r in result:
                self.log.debug("Config value received : %s : %s" % \
                    (r, result[r]))
                res = self._keys.pop(r)
                self._l[r].unregister()
                del self._l[r]
                self._result = result
                res.set()
                break

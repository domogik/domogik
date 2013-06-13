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

Manage connection to the database

Implements
==========

- DBConnector

@author: Maxence Dunnewind <maxence@dunnewind.net>
         Fritz SMH <fritz.smh@gmail.com>
         Cereal
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback

from domogik.xpl.common.plugin import XplPlugin
from domogik.common.database import DbHelper
from domogik.mq.reqrep.worker import MQRep
from domogik.mq.message import MQMessage
from zmq.eventloop.ioloop import IOLoop
import time
import zmq

DATABASE_CONNECTION_NUM_TRY = 50
DATABASE_CONNECTION_WAIT = 30

class DBConnector(XplPlugin, MQRep):
    '''
    Manage the connection between database and the plugins
    Should be the *only* object along with the StatsManager to access to the database on the core side
    '''

    def __init__(self):
        '''
        Initialize database and xPL connection
        '''
        XplPlugin.__init__(self, 'dbmgr')
        # Already done in XplPlugin
        #MQRep.__init__(self, zmq.Context(), 'dbmgr')
        self.log.debug("Init database_manager instance")

        # Check for database connexion
        self._db = DbHelper()
        nb_test = 0
        db_ok = False
        while not db_ok and nb_test < DATABASE_CONNECTION_NUM_TRY:
            nb_test += 1
            try:
                self._db.list_user_accounts()
                db_ok = True
            except:
                msg = "The database is not responding. Check your configuration of if the database is up. Test {0}/{1}".format(nb_test, DATABASE_CONNECTION_NUM_TRY)
                self.log.error(msg)
                msg = "Waiting for {0} seconds".format(DATABASE_CONNECTION_WAIT)
                self.log.info(msg)
                time.sleep(DATABASE_CONNECTION_WAIT)

        if nb_test >= DATABASE_CONNECTION_NUM_TRY:
            msg = "Exiting dbmgr!"
            self.log.error(msg)
            self.force_leave()
            return

        msg = "Connected to the database"
        self.log.info(msg)
        try:
            self._engine = self._db.get_engine()
        except:
            self.log.error("Error while starting database engine : {0}".format(traceback.format_exc()))
            self.force_leave()
            return

        self.ready()
        # Already done in ready()
        #IOLoop.instance().start() 


    def on_mdp_request(self, msg):
        """ Handle Requests over MQ
            @param msg : MQ req message
        """
        # XplPlugin handles MQ Req/rep also
        XplPlugin.on_mdp_request(self, msg)

        if msg.get_action() == "config.get":
            self._mdp_reply(msg)

        elif msg.get_action() == "config.set":
            # TODO
            self.log.error("config.set action is not yet developped")


    def _mdp_reply(self, data):
        """ Reply to config.get MQ req
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('config.result')
        status = True

        msg_data = data.get_data()
        print msg_data
        if 'type' not in msg_data:
            status = False
            reason = "Config request : missing 'type' field : {0}".format(data)

        if 'id' not in msg_data:
            status = False
            reason = "Config request : missing 'id' field : {0}".format(data)

        if 'host' not in msg_data:
            status = False
            reason = "Config request : missing 'host' field : {0}".format(data)

        if 'key' not in msg_data:
            status = False
            reason = "Config request : missing 'key' field : {0}".format(data)

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            id = msg_data['id']
            host = msg_data['host']
            key = msg_data['key']
            value = self._fetch_techno_config(id, host, key)
            self.log.info("Get config for {0} {1} with key '{2}' : value = {3}".format(type, id, key, value))

            msg.add_data('status', status)
            msg.add_data('reason', reason)
            msg.add_data('type', type)
            msg.add_data('id', id)
            msg.add_data('host', host)
            msg.add_data('key', key)
            msg.add_data('value', value)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _fetch_techno_config(self, id, host, key):
        '''
        Fetch a plugin global config value in the database
        @param id : the plugin of the element
        @param host : hostname
        @param key : the key of the config tuple to fetch
        '''
        try:
            try:
                result = self._db.get_plugin_config(id, host, key)
                # tricky loop as workaround for a (sqlalchemy?) bug :
                # sometimes the given result is for another plugin/key
                # so while we don't get the good data, we loop
                # This bug happens rarely
                while result.id != id or \
                   result.hostname != host or \
                   result.key != key:
                    self.log.debug("Bad result : {0}/{1} != {2}/{3}".format(result.id, result.key, plugin, key))
                    result = self._db.get_plugin_config(id, host, key)
                val = result.value
                if val == '':
                    val = "None"
                return val
            except AttributeError:
                return "None"
        except:
            msg = "No config found host={0}, plugin={1}, key={2}" % (host, id, key)
            self.log.warn(msg)
            return "None"

if __name__ == "__main__":
    DBC = DBConnector()

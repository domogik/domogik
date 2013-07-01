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

        # configuration
        if msg.get_action() == "config.get":
            self._mdp_reply_config_get(msg)

        elif msg.get_action() == "config.set":
            self._mdp_reply_config_set(msg)

        elif msg.get_action() == "config.delete":
            self._mdp_reply_config_delete(msg)

        # devices list
        elif msg.get_action() == "devices.get":
            self._mdp_reply_devices_result(msg)


    def _mdp_reply_config_get(self, data):
        """ Reply to config.get MQ req
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('config.result')
        status = True
        msg_data = data.get_data()
        if 'type' not in msg_data:
            status = False
            reason = "Config request : missing 'type' field : {0}".format(data)

        if msg_data['type'] != "plugin":
            status = False
            reason = "Config request not available for type={0}".format(msg_data['type'])

        if 'name' not in msg_data:
            status = False
            reason = "Config request : missing 'name' field : {0}".format(data)

        if 'host' not in msg_data:
            status = False
            reason = "Config request : missing 'host' field : {0}".format(data)

        if 'key' not in msg_data:
            get_all_keys = True
            key = "*"
        else:
            get_all_keys = False
            key = msg_data['key']

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            name = msg_data['name']
            host = msg_data['host']
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            msg.add_data('key', key)  # we let this here to display key or * depending on the case
            try:
                if get_all_keys == True:
                    config = self._db.list_plugin_config(name, host)
                    self.log.info("Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, config))
                    json_config = {}
                    for elt in config:
                        json_config[elt.key] = self.convert(elt.value)
                    msg.add_data('data', json_config)
                else:
                    value = self._fetch_techno_config(name, host, key)
                    # temporary fix : should be done in a better way (on db side)
                    value = self.convert(value)
                    self.log.info("Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, value))
                    msg.add_data('value', value)
            except:
                status = False
                reason = "Error while getting configuration for '{0} {1} on {2}, key {3}' : {4}".format(type, name, host, key, traceback.format_exc())
                self.log.error(reason)

        msg.add_data('reason', reason)
        msg.add_data('status', status)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _mdp_reply_config_set(self, data):
        """ Reply to config.set MQ req
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('config.result')
        status = True
        msg_data = data.get_data()
        if 'type' not in msg_data:
            status = False
            reason = "Config set : missing 'type' field : {0}".format(data)

        if msg_data['type'] != "plugin":
            status = False
            reason = "Config set not available for type={0}".format(msg_data['type'])

        if 'name' not in msg_data:
            status = False
            reason = "Config set : missing 'name' field : {0}".format(data)

        if 'host' not in msg_data:
            status = False
            reason = "Config set : missing 'host' field : {0}".format(data)

        if 'data' not in msg_data:
            status = False
            reason = "Config set : missing 'data' field : {0}".format(data)

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            name = msg_data['name']
            host = msg_data['host']
            data = msg_data['data']
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            try: 
                # we add a configured key set to true to tell the UIs and plugins that there are some configuration elements
                self._db.set_plugin_config(name, host, "configured", True)
                for key in msg_data['data']:
                    self._db.set_plugin_config(name, host, key, data[key])
                self.publish_config_updated(type, name, host)
            except:
                reason = "Error while setting configuration for '{0} {1} on {2}, key {3}' : {4}".format(type, name, host, key, traceback.format_exc())
                status = False
                self.log.error(reason)

        msg.add_data('status', status)
        msg.add_data('reason', reason)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _mdp_reply_config_delete(self, data):
        """ Reply to config.delete MQ req
            Delete all the config items for the given type, name and host
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('config.result')
        status = True
        msg_data = data.get_data()
        if 'type' not in msg_data:
            status = False
            reason = "Config request : missing 'type' field : {0}".format(data)

        if msg_data['type'] != "plugin":
            status = False
            reason = "Config request not available for type={0}".format(msg_data['type'])

        if 'name' not in msg_data:
            status = False
            reason = "Config request : missing 'name' field : {0}".format(data)

        if 'host' not in msg_data:
            status = False
            reason = "Config request : missing 'host' field : {0}".format(data)

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            name = msg_data['name']
            host = msg_data['host']
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            try:
                self._db.del_plugin_config(name, host)
                self.log.info("Delete config for {0} {1}".format(type, name))
                self.publish_config_updated(type, name, host)
            except:
                status = False
                reason = "Error while deleting configuration for '{0} {1} on {2} : {3}".format(type, name, host, traceback.format_exc())
                self.log.error(reason)

        msg.add_data('reason', reason)
        msg.add_data('status', status)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _fetch_techno_config(self, name, host, key):
        '''
        Fetch a plugin global config value in the database
        @param name : the plugin of the element
        @param host : hostname
        @param key : the key of the config tuple to fetch
        '''
        try:
            try:
                result = self._db.get_plugin_config(name, host, key)
                # tricky loop as workaround for a (sqlalchemy?) bug :
                # sometimes the given result is for another plugin/key
                # so while we don't get the good data, we loop
                # This bug happens rarely
                while result.id != name or \
                   result.hostname != host or \
                   result.key != key:
                    self.log.debug("Bad result : {0}/{1} != {2}/{3}".format(result.id, result.key, plugin, key))
                    result = self._db.get_plugin_config(name, host, key)
                val = result.value
                if val == '':
                    val = "None"
                return val
            except AttributeError:
                return "None"
        except:
            msg = "No config found host={0}, plugin={1}, key={2}" % (host, name, key)
            self.log.warn(msg)
            return "None"


    def _mdp_reply_devices_result(self, data):
        """ Reply to devices.get MQ req
            @param data : MQ req message
        """

        # TODO : NOT FINISHED

        msg = MQMessage()
        msg.set_action('devices.result')
        status = True

        msg_data = data.get_data()
        if 'type' not in msg_data:
            status = False
            reason = "Devices request : missing 'type' field : {0}".format(data)

        if 'name' not in msg_data:
            status = False
            reason = "Devices request : missing 'name' field : {0}".format(data)

        if status == False:
            self.log.error(reason)
        else:
            reason = ""
            type = msg_data['type']
            name = msg_data['name']
            dev_list = self._db.list_devices()
            msg.add_data('status', status)
            msg.add_data('reason', reason)
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('devices', dev_list)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def convert(self, data):
        """ Do some conversions on data
        """
        if data == "True":
            data = True
        if data == "False":
            data = False
        return data

    def publish_config_updated(self, type, name, host):
        """ Publish over the MQ a message to inform that a plugin configuration has been updated
            @param type : package type (plugin)
            @param name : package name
            @param host : host
        """
        self._pub.send_event('plugin.configuration',
                             {"type" : type,
                              "name" : name,
                              "host" : host,
                              "event" : "updated"})


if __name__ == "__main__":
    DBC = DBConnector()

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

from domogik.common.jsondata import domogik_encoder
from domogik.xpl.common.plugin import DMG_VENDOR_ID
from domogik.xpl.common.plugin import Plugin
from domogik.common.database import DbHelper, DbHelperException
from domogikmq.reqrep.worker import MQRep
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from zmq.eventloop.ioloop import IOLoop
import time
import zmq
import json
import traceback

DATABASE_CONNECTION_NUM_TRY = 50
DATABASE_CONNECTION_WAIT = 30

class DBConnector(Plugin, MQRep):
    '''
    Manage the connection between database and the plugins
    Should be the *only* object along with the StatsManager to access to the database on the core side
    '''

    def __init__(self):
        '''
        Initialize database and xPL connection
        '''
        Plugin.__init__(self, 'dbmgr', log_prefix='core_')
        # Already done in Plugin
        #MQRep.__init__(self, zmq.Context(), 'dbmgr')
        self.log.debug(u"Init database_manager instance")

        # Check for database connexion
        self._db = DbHelper()
        with self._db.session_scope():
            # TODO : move in a function and use it (also used in dbmgr)
            nb_test = 0
            db_ok = False
            while not db_ok and nb_test < DATABASE_CONNECTION_NUM_TRY:
                nb_test += 1
                try:
                    self._db.list_user_accounts()
                    db_ok = True
                except:
                    msg = "The database is not responding. Check your configuration of if the database is up. Test {0}/{1}. The error while trying to connect to the database is : {2}".format(nb_test, DATABASE_CONNECTION_NUM_TRY, traceback.format_exc())
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
                self.log.error(u"Error while starting database engine : {0}".format(traceback.format_exc()))
                self.force_leave()
                return
        self.ready()
        # Already done in ready()
        #IOLoop.instance().start() 

    def on_mdp_request(self, msg):
        """ Handle Requests over MQ
            @param msg : MQ req message
        """
        try:
            with self._db.session_scope():
                # Plugin handles MQ Req/rep also
                Plugin.on_mdp_request(self, msg)

                # configuration
                if msg.get_action() == "config.get":
                    self._mdp_reply_config_get(msg)
                elif msg.get_action() == "config.set":
                    self._mdp_reply_config_set(msg)
                elif msg.get_action() == "config.delete":
                    self._mdp_reply_config_delete(msg)
                # devices list
                elif msg.get_action() == "device.get":
                    self._mdp_reply_devices_result(msg)
                # device get params
                elif msg.get_action() == "device.params":
                    self._mdp_reply_devices_params_result(msg)
                # device create
                elif msg.get_action() == "device.create":
                    self._mdp_reply_devices_create_result(msg)
                # device delete
                elif msg.get_action() == "device.delete":
                    self._mdp_reply_devices_delete_result(msg)
                # device update
                elif msg.get_action() == "device.update":
                    self._mdp_reply_devices_update_result(msg)
                # deviceparam update
                elif msg.get_action() == "deviceparam.update":
                    self._mdp_reply_deviceparam_update_result(msg)
                # sensor update
                elif msg.get_action() == "sensor.update":
                    self._mdp_reply_sensor_update_result(msg)
                # sensor history
                elif msg.get_action() == "sensor_history.get":
                    self._mdp_reply_sensor_history(msg)
        except:
            msg = "Error while processing request. Message is : {0}. Error is : {1}".format(msg, traceback.format_exc())
            self.log.error(msg)

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

        if msg_data['type'] not in ["plugin", "brain", "interface"]:
            status = False
            reason = "Configuration request not available for type={0}".format(msg_data['type'])

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
                    config = self._db.list_plugin_config(type, name, host)
                    self.log.info(u"Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, config))
                    json_config = {}
                    for elt in config:
                        json_config[elt.key] = self.convert(elt.value)
                    msg.add_data('data', json_config)
                else:
                    value = self._fetch_techno_config(name, type, host, key)
                    # temporary fix : should be done in a better way (on db side)
                    value = self.convert(value)
                    self.log.info(u"Get config for {0} {1} with key '{2}' : value = {3}".format(type, name, key, value))
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

        if msg_data['type'] not in ["plugin", "brain", "interface"]:
            status = False
            reason = "You are not able to configure items for type={0}".format(msg_data['type'])

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
                self._db.set_plugin_config(type, name, host, "configured", True)
                for key in msg_data['data']:
                    self._db.set_plugin_config(type, name, host, key, data[key])
                self.publish_config_updated(type, name, host)
            except:
                reason = "Error while setting configuration for '{0} {1} on {2}' : {3}".format(type, name, host, traceback.format_exc())
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

        if msg_data['type'] not in ["plugin", "brain", "interface"]:
            status = False
            reason = "Configuration deletion not available for type={0}".format(msg_data['type'])

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
                self._db.del_plugin_config(type, name, host)
                self.log.info(u"Delete config for {0} {1}".format(type, name))
                self.publish_config_updated(type, name, host)
            except:
                status = False
                reason = "Error while deleting configuration for '{0} {1} on {2} : {3}".format(type, name, host, traceback.format_exc())
                self.log.error(reason)

        msg.add_data('reason', reason)
        msg.add_data('status', status)

        self.log.debug(msg.get())
        self.reply(msg.get())


    def _fetch_techno_config(self, name, type, host, key):
        '''
        Fetch a plugin global config value in the database
        @param name : the plugin of the element
        @param host : hostname
        @param key : the key of the config tuple to fetch
        '''
        try:
            try:
                result = self._db.get_plugin_config(type, name, host, key)
                # tricky loop as workaround for a (sqlalchemy?) bug :
                # sometimes the given result is for another plugin/key
                # so while we don't get the good data, we loop
                # This bug happens rarely
                while result.id != name or \
                   result.type != type or \
                   result.hostname != host or \
                   result.key != key:
                    self.log.debug(u"Bad result : {0}-{1}/{2} != {3}/{4}".format(result.id, result.type, result.key, plugin, key))
                    result = self._db.get_plugin_config(type, name, host, key)
                val = result.value
                if val == '':
                    val = "None"
                return val
            except AttributeError:
                # if no result is found
                #self.log.error(u"Attribute error : {0}".format(traceback.format_exc()))
                return "None"
        except:
            msg = "No config found host={0}, plugin={1}, key={2}".format(host, name, key)
            self.log.warn(msg)
            return "None"

    def _mdp_reply_devices_delete_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Deleting device : {0}".format(data))
        try:
            did = data.get_data()['did']
            if did:
                res = self._db.del_device(did)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such device"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while deleting device: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while deleting device: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('device.delete.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            self._pub.send_event('device.update',
                     {"device_id" : did,
                      "client_id" : res.client_id})

    def _mdp_reply_sensor_update_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Updating sensor : {0}".format(data))
        try:
            data = data.get_data()
            if 'sid' in data:
                sid = data['sid']
                if 'history_round' not in data:
                    hround = None
                else:
                    hround = data['history_round']
                if 'history_store' not in data:
                    hstore = None
                else:
                    hstore = data['history_store']
                if 'history_max' not in data:
                    hmax = None
                else:
                    hmax = data['history_max']
                if 'history_expire' not in data:
                    hexpire = None
                else:
                    hexpire = data['history_expire']
                if 'timeout' not in data:
                    timeout = None
                else:
                    timeout = data['timeout']
                if 'formula' not in data:
                    formula = None
                else:
                    formula = data['formula']
                if 'data_type' not in data:
                    data_type = None
                else:
                    data_type = data['data_type']
                # do the update
                res = self._db.update_sensor(sid, \
                     history_round=hround, \
                     history_store=hstore, \
                     history_max=hmax, \
                     history_expire=hexpire, \
                     timeout=timeout, \
                     formula=formula, \
                     data_type=data_type)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such sensor"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while updating sensor: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while updating sensor: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('sensor.update.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            dev = self._db.get_device(res.device_id)
            self._pub.send_event('device.update',
                     {"device_id" : res.device_id,
                      "client_id" : dev['client_id']})

    def _mdp_reply_deviceparam_update_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Updating device param : {0}".format(data))
        try:
            data = data.get_data()
            if 'dpid' in data:
                dpid = data['dpid']
                val = data['value']
                # do the update
                res = self._db.udpate_device_param(dpid, value=val)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such device param"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while updating device param: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while updating device param: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('deviceparam.update.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())

    def _mdp_reply_devices_update_result(self, data):
        status = True
        reason = False

        self.log.debug(u"Updating device : {0}".format(data))
        try:
            data = data.get_data()
            if 'did' in data:
                did = data['did']
                if 'name' not in data:
                    name = None
                else:
                    name = data['name']
                if 'reference' not in data:
                    ref = None
                else:
                    ref = data['reference']
                if 'description' not in data:
                    desc = None
                else:
                    desc = data['description']
                # do the update
                res = self._db.update_device(did, \
                    d_name=name, \
                    d_description=desc, \
                    d_reference=ref)
                if not res:
                    status = False
                else:
                    status = True 
            else:
                status = False
                reason = "There is no such device"
                self.log.debug(reason)
            # delete done
        except DbHelperException as d:
            status = False
            reason = "Error while updating device: {0}".format(d.value)
            self.log.error(reason)
        except:
            status = False
            reason = "Error while updating device: {0}".format(traceback.format_exc())
            self.log.error(reason)
        # send the result
        msg = MQMessage()
        msg.set_action('device.update.result')
        msg.add_data('status', status)
        if reason:
            msg.add_data('reason', reason)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            self._pub.send_event('device.update',
                     {"device_id" : res.id,
                      "client_id" : res.client_id})

    def _mdp_reply_devices_create_result(self, data):
        status = True
        reason = False
        result = False
        # get the filled package json
        params = data.get_data()['data']
        # get the json
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('device_types.get')
        msg.add_data('device_type', params['device_type'])
        res = cli.request('manager', msg.get(), timeout=10)
        del cli
        if res is None:
            status = False
            reason = "Manager is not replying to the mq request" 
        pjson = res.get_data()
        if pjson is None:
            status = False
            reason = "No data for {0} found by manager".format(params['device_type']) 
        pjson = pjson[params['device_type']]
        if pjson is None:
            status = False
            reason = "The json for {0} found by manager is empty".format(params['device_type']) 

        if status:
            # call the add device function
            res = self._db.add_full_device(params, pjson)
            if not res:
                status = False
                reason = "An error occured while adding the device in database. Please check the file dbmgr.log for more informations"
            else:
                status = True
                reason = False
                result = res

        msg = MQMessage()
        msg.set_action('device.create.result')
        if reason:
            msg.add_data('reason', reason)
        if result:
            msg.add_data('result', result)
        msg.add_data('status', status)
        self.log.debug(msg.get())
        self.reply(msg.get())
        # send the pub message
        if status and res:
            self._pub.send_event('device.update',
                     {"device_id" : res['id'],
                      "client_id" : res['client_id']})

    def _mdp_reply_devices_params_result(self, data):
        """
            Reply to device.params mq req
            @param data : MQ req message
                => should contain
                    - device_type
        """
        status = True

        try:
            # check we have all the needed info
            msg_data = data.get_data()
            if 'device_type' not in msg_data:
                status = False
                reason = "Device params request : missing 'cevice_type' field : {0}".format(data)
            else:
                dev_type_id = msg_data['device_type']
    
            # check the received info
            if status:
                cli = MQSyncReq(self.zmq)
                msg = MQMessage()
                msg.set_action('device_types.get')
                msg.add_data('device_type', dev_type_id)
                res = cli.request('manager', msg.get(), timeout=10)
                del cli
                if res is None:
                    status = False
                    reason = "Manager is not replying to the mq request" 
            if status:
                pjson = res.get_data()
                if pjson is None:
                    status = False
                    reason = "No data for {0} found by manager".format(msg_data['device_type']) 
            if status:
                pjson = pjson[dev_type_id]
                if pjson is None:
                    status = False
                    reason = "The json for {0} found by manager is empty".format(msg_data['device_type']) 
                self.log.debug("Device Params result : json received by the manager is : {0}".format(pjson))
            if not status:
                # we don't have all info so exit
                msg = MQMessage()
                msg.set_action('device.params.result')
                msg.add_data('result', 'Failed')
                msg.add_data('reason', reason)
                self.log.debug(msg.get())
                self.reply(msg.get())
                return

    
            # we have the json now, build the params
            msg = MQMessage()
            msg.set_action('device.params.result')
            stats = []
            result = {}
            result['device_type'] = dev_type_id
            result['name'] = ""
            result['reference'] = ""
            result['description'] = ""
            # append the global xpl and on-xpl params
            result['xpl'] = []
            result['global'] = []
            for param in pjson['device_types'][dev_type_id]['parameters']:
                if param['xpl']:
                    del param['xpl']
                    result['xpl'].append(param)
                else:
                    del param['xpl']
                    result['global'].append(param)
            # find the xplCommands
            result['xpl_commands'] = {}
            for cmdn in pjson['device_types'][dev_type_id]['commands']:
                cmd = pjson['commands'][cmdn]
                if 'xpl_command'in cmd:
                    xcmdn = cmd['xpl_command']
                    xcmd = pjson['xpl_commands'][xcmdn]
                    result['xpl_commands'][xcmdn] = []
                    stats.append( xcmd['xplstat_name'] )
                    for param in xcmd['parameters']['device']:
                        result['xpl_commands'][xcmdn].append(param)
            # find the xplStats
            sensors = pjson['device_types'][dev_type_id]['sensors']
            #print("SENSORS = {0}".format(sensors))
            for xstatn in pjson['xpl_stats']:
                #print("XSTATN = {0}".format(xstatn))
                xstat = pjson['xpl_stats'][xstatn]
                for sparam in xstat['parameters']['dynamic']:
                    #print("XSTATN = {0}, SPARAM = {1}".format(xstatn, sparam))
                    #if 'sensor' in sparam and xstatn in sensors:
                    # => This condition was used to fix a bug which occurs while creating complexe devices for rfxcom
                    #    But is introduced a bug for the geoloc plugin...
                    #    In fact we had to fix the rfxcom info.json file (open_close uses now rssi_open_close instead of
                    #    rssi_lighting2
                    #    So, this one is NOT the good one.
                    if 'sensor' in sparam:
                    # => this condition was the original one restored to make the geoloc pluin ok for tests
                    #    Strangely, there is no issue while using the admin (which uses only mq)
                    #    but is sucks with test library which uses rest...
                    #    This one is the good one
                        if sparam['sensor'] in sensors:
                            #print("ADD") 
                            stats.append(xstatn)
            result['xpl_stats'] = {}
            #print("STATS = {0}".format(stats))
            for xstatn in stats:
                xstat = pjson['xpl_stats'][xstatn]
                result['xpl_stats'][xstatn] = []
                for param in xstat['parameters']['device']:
                    result['xpl_stats'][xstatn].append(param)
            # return the data
            msg.add_data('result', result)
            self.log.debug(msg.get())
            self.reply(msg.get())
        except:
            self.log.error("Error when replying to device.params for data={0}. Error: {1}".format(data, traceback.format_exc()))

    def _mdp_reply_devices_result(self, data):
        """ Reply to device.get MQ req
            @param data : MQ req message
        """
        msg = MQMessage()
        msg.set_action('device.result')
        status = True

        msg_data = data.get_data()

        # request for all devices
        if 'type' not in msg_data and \
           'name' not in msg_data and \
           'host' not in msg_data:

            reason = ""
            status = True
            dev_list = self._db.list_devices()

            dev_json = dev_list
            msg.add_data('status', status)
            msg.add_data('reason', reason)
            msg.add_data('devices', dev_json)

        # request for all devices of one client
        else:
            if 'type' not in msg_data:
                status = False
                reason = "Devices request : missing 'type' field : {0}".format(data)

            if 'name' not in msg_data:
                status = False
                reason = "Devices request : missing 'name' field : {0}".format(data)

            if 'host' not in msg_data:
                status = False
                reason = "Devices request : missing 'host' field : {0}".format(data)

            if status == False:
                self.log.error(reason)
            else:
                reason = ""
                type = msg_data['type']
                name = msg_data['name']
                host = msg_data['host']
                dev_list = self._db.list_devices_by_plugin("{0}-{1}.{2}".format(type, name, host))

            #dev_json = json.dumps(dev_list, cls=domogik_encoder(), check_circular=False),
            dev_json = dev_list
            msg.add_data('status', status)
            msg.add_data('reason', reason)
            msg.add_data('type', type)
            msg.add_data('name', name)
            msg.add_data('host', host)
            msg.add_data('devices', dev_json)

        self.reply(msg.get())

    def _mdp_reply_sensor_history(self, data):
        """ Reply to sensor_history.get MQ req
            @param data : MQ req message

            If no other param than the sensor id, return the last value
        """
        msg = MQMessage()
        msg.set_action('sensor_history.result')
        status = True
        reason = ""

        ### process parameters
        msg_data = data.get_data()
        if 'sensor_id' in msg_data:
            sensor_id = msg_data['sensor_id']
        else:
            reason = "ERROR when getting sensor history. No sensor_id declared in the message"
            self.log.error(reason)
            status = False
            sensor_id = None
        if 'mode' in msg_data:
            if msg_data['mode'] == "last":
                mode = "last"
            elif msg_data['mode'] == "period":
                mode = "period"
            else:
                reason = "ERROR when getting sensor history. No valid type (last, from) declared in the message"
                self.log.error(reason)
                status = False
                mode = None
        else:
            reason = "ERROR when getting sensor history. No type (last, from) declared in the message"
            self.log.error(reason)
            status = False
            sensor_id = None

        values = None

        ### last N values
        if mode == "last":
            if 'number' in msg_data:
                number = msg_data['number']
            else:
                number = 1

            try:
                history = self._db.list_sensor_history(sensor_id, number)
                if len(history) == 0:
                    values = None
                else: 
                    values = self._db.list_sensor_history(sensor_id, number)
            except:
                self.log.error("ERROR when getting sensor history for id = {0} : {1}".format(sensor_id, traceback.format_exc()))
                reason = "ERROR : {0}".format(traceback.format_exc())
                status = False

        ### period
        elif mode == "period":
            if 'from' in msg_data:
                frm = msg_data['from']
            else:
                reason = "ERROR when getting sensor history. No key 'from' defined for mode = 'period'!"
                self.log.error(reason)
                status = False
                frm = None

            if 'to' in msg_data:
                to = msg_data['to']
            else:
                to = None

            if frm != None and to == None:
                values = self._db.list_sensor_history_between(sensor_id, frm)
                print(values)

            else:
                # TODO
                values = "TODO"
        

        msg.add_data('status', status)
        msg.add_data('reason', reason)
        msg.add_data('sensor_id', sensor_id)
        msg.add_data('mode', mode)
        msg.add_data('values', values)

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
        self.log.debug("Publish configuration update notification for {0}-{1}.{2}".format(type, name, host))
        self._pub.send_event('plugin.configuration',
                             {"type" : type,
                              "name" : name,
                              "host" : host,
                              "event" : "updated"})

if __name__ == "__main__":
    DBC = DBConnector()

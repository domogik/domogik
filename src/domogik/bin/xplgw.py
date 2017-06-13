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
=============

Implements
==========

class XplManager(XplPlugin):

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.database import DbHelper
from domogik.xpl.common.xplmessage import XplMessage, XplMessageError
from domogikmq.pubsub.publisher import MQPub
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
import time
import traceback
import calendar
import zmq
#import json
try:
    import Queue as queue
except:
    import queue
import threading
from uuid import uuid4

# how long we keep a message in the cmd queue
CMDTIMEOUT = 5

################################################################################
class XplManager(XplPlugin):
    """ Statistics manager
    """

    def __init__(self):
        """ Initiate DbHelper, Logs and config
        """
        XplPlugin.__init__(self, 'xplgw', log_prefix="core_")
        self.add_mq_sub('client.conversion')
        self.add_mq_sub('client.list')
        self.add_mq_sub('client.sensor')
        self.add_mq_sub('device.update')

        self.log.info(u"XPL manager initialisation...")
        self._db = DbHelper()
        self.pub = MQPub(zmq.Context(), 'xplgw')
        # some initial data sets
        self.client_xpl_map = {}
        self.client_conversion_map = {}
        self._db_sensors = {}
        self._db_xplstats = {}

        # load devices informations
        self._dev_lock = threading.Lock()
        self._reload_devices()
        self._cmd_lock = threading.Lock()
        self._reload_commands()
        self._stats_lock = threading.Lock()
        self._reload_xpl_stats()

        # queue to store the message that needs to be ahndled for sensor checking
        self._sensor_queue = queue.Queue()
        # queue to handle the sensor storage
        self._sensor_store_queue = queue.Queue()
        # all command handling params
        # _lock => to be sure to be thread safe
        # _dict => uuid to xplstat translationg
        # _pkt => received messages to check
        self._cmd_lock_d = threading.Lock()
        self._cmd_dict = {}
        self._cmd_lock_p = threading.Lock()
        self._cmd_pkt = {}
        # load some initial data from manager and db
        self._load_client_to_xpl_target()
        self._load_conversions()
        # create a general listener
        self._create_xpl_trigger()
        # start handling the xplmessages
        self._x_thread = self._XplSensorThread(\
            self.log, self.get_stop(), self._sensor_queue, \
            self._sensor_store_queue)
        self.register_thread(self._x_thread)
        self._x_thread.start()
        # start handling the command reponses in a thread
        self._c_thread = self._XplCommandThread(\
            self.log, self.get_stop(), self._db, self._cmd_lock_d, \
            self._cmd_lock_p, self._cmd_dict, self._cmd_pkt, self.pub)
        self.register_thread(self._c_thread)
        self._c_thread.start()
        # start the sensor storage thread
        self._s_thread = self._SensorStoreThread(\
                self._sensor_store_queue, self.log, \
                self._get_conversion_map, self.pub, self.get_stop())
        self.register_thread(self._s_thread)
        self._s_thread.start()
        # start the sensorthread
        self.ready()

    def on_mdp_request(self, msg):
        """ Method called when an mq request comes in
        XplPlugin also needs this info, so we need to do a passthrough
        """
        try:
            XplPlugin.on_mdp_request(self, msg)
            if msg.get_action() == "test":
                pass
            if msg.get_action() == "cmd.send":
                self._send_command(msg)
        except :
            self.log.error(traceback.format_exc())

    def on_message(self, msgid, content):
        """ Method called on a subscribed message
        """
        try:
            if msgid != 'device.update':  # No need to reload device_list of xplgw
                XplPlugin.on_message(self, msgid, content)
            if msgid == 'client.conversion':
                self._parse_conversions(content)
            elif msgid == 'client.list':
                self._parse_xpl_target(content)
            elif msgid == 'client.sensor':
                self._handle_mq_sensor(content)
            elif msgid == 'device.update':
                self._handle_mq_device_update(content)
        except :
            self.log.error(traceback.format_exc())

    def _handle_mq_device_update(self, content):
        """ On a device change, a Mq message is received
            So we update all the devices parameters used by xplgw
        """
        self.log.debug(u"New message (from MQ) about some device changes > reload the devices parameters...")
        self._x_thread.on_device_changed()
        self._s_thread.on_device_changed()
        self._reload_devices()
        self._reload_commands()


    def _reload_devices(self):
        """ Reload the commands
        """
        with self._dev_lock:
            self.log.info("Event : one device changed. Reloading data for devices (light data)")
            self.all_devices = {}
            with self._db.session_scope():
                for dev in self._db.list_devices():
                    #print(dev)
                    #{'xpl_stats': {u'get_total_space': {'json_id': u'get_total_space', 'schema': u'sensor.basic', 'id': 3, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_total_space', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'total_space', 'key': u'type'}]}, 'name': u'Total space'}, u'get_free_space': {'json_id': u'get_free_space', 'schema': u'sensor.basic', 'id': 4, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_free_space', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'free_space', 'key': u'type'}]}, 'name': u'Free space'}, u'get_used_space': {'json_id': u'get_used_space', 'schema': u'sensor.basic', 'id': 5, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_used_space', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'used_space', 'key': u'type'}]}, 'name': u'Used space'}, u'get_percent_used': {'json_id': u'get_percent_used', 'schema': u'sensor.basic', 'id': 6, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_percent_used', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'percent_used', 'key': u'type'}]}, 'name': u'Percent used'}}, 'commands': {}, 'description': u'', 'reference': u'', 'sensors': {u'get_total_space': {'value_min': None, 'data_type': u'DT_Byte', 'incremental': False, 'id': 57, 'reference': u'get_total_space', 'conversion': u'', 'name': u'Total Space', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'14763409408', 'value_max': 14763409408.0}, u'get_free_space': {'value_min': None, 'data_type': u'DT_Byte', 'incremental': False, 'id': 59, 'reference': u'get_free_space', 'conversion': u'', 'name':u'Free Space', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'1319346176', 'value_max': 8220349952.0}, u'get_used_space': {'value_min': None, 'data_type': u'DT_Byte', 'incremental': False, 'id': 60, 'reference': u'get_used_space', 'conversion': u'', 'name': u'Used Space', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'13444063232', 'value_max': 14763409408.0}, u'get_percent_used': {'value_min': None, 'data_type':u'DT_Scaling', 'incremental': False, 'id': 58, 'reference': u'get_percent_used', 'conversion': u'', 'name': u'Percent used', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'91', 'value_max': 100.0}}, 'xpl_commands': {}, 'client_id': u'plugin-diskfree.ambre', 'device_type_id': u'diskfree.disk_usage', 'client_version': u'1.0', 'parameters': {u'interval': {'value': u'5', 'type': u'integer', 'id': 5, 'key': u'interval'}}, 'id': 3, 'name': u'Ambre /'}
                    self.all_devices[str(dev['id'])] = {
                                                    'client_id': dev['client_id'],
                                                    'id': dev['id'],
                                                    'name': dev['name'],
                                                  }
                #print(self.all_devices)
            self.log.info("Event : one device changed. Reloading data for devices (light data) -- finished")

    def _reload_commands(self):
        """ Reload the commands
        """
        with self._cmd_lock:
            self.log.info("Event : one device changed. Reloading data for commands")
            self.all_commands = {}
            with self._db.session_scope():
                for cmd in self._db.get_all_command():
                    #print(cmd)
                    #<Command: return_confirmation='True', name='Swith', reference='switch_lighting2', id='6', device_id='21'>
                    #print(cmd.params)
                    #[<CommandParam: data_type='DT_Trigger', conversion='', cmd_id='16', key='state'>]

                    self.all_commands[str(cmd.id)] = {
                                                  'return_confirmation' : cmd.return_confirmation,
                                                  'name' : cmd.name,
                                                  'reference' : cmd.reference,
                                                  'id' : cmd.id,
                                                  'device_id' : cmd.device_id,
                                                  'xpl_command' : None,
                                                  'params' : []
                                                }

                    for param in cmd.params:
                        self.all_commands[str(cmd.id)]['params'].append({
                                                                       'data_type' : param.data_type,
                                                                       'conversion' : param.conversion,
                                                                       'cmd_id' : param.cmd_id,
                                                                       'key' : param.key
                                                                   })

                    #print(cmd.xpl_command)
                    #<XplCommand: name='Switch', stat_id='82', cmd_id='6', json_id='switch_lighting2', device_id='21', id='6', schema='ac.basic'>
                    if cmd.xpl_command != None:
                        xpl_command = {
                                        'name' : cmd.xpl_command.name,
                                        'stat_id' : cmd.xpl_command.stat_id,
                                        'cmd_id' : cmd.xpl_command.cmd_id,
                                        'json_id' : cmd.xpl_command.json_id,
                                        'device_id' : cmd.xpl_command.device_id,
                                        'id' : cmd.xpl_command.id,
                                        'schema' : cmd.xpl_command.schema,
                                        'params' : []
                                      }

                        for param in cmd.xpl_command.params:
                            #print(param)
                            #<XplCommandParam: value='0x0038abfc', key='address', xplcmd_id='6'>
                            xpl_command['params'].append({'value' : param.value,
                                                          'key' : param.key,
                                                          'xplcmd_id' : param.xplcmd_id})

                        self.all_commands[str(cmd.id)]['xpl_command'] = xpl_command

            #print(self.all_commands)
            self.log.info("Event : one device changed. Reloading data for commands -- finished")

    def _reload_xpl_stats(self):
        """ Reload the commands
        """
        with self._stats_lock:
            self.log.info("Event : one device changed. Reloading data for xpl stats")
            self.all_xpl_stats = {}
            with self._db.session_scope():
                for xplstat in self._db.get_all_xpl_stat():
                    #print(xplstat)
                    #print(xplstat.params)
                    # <XplStat: name='Open/Close sensor', json_id='open_close', device_id='95', id='185', schema='ac.basic'>
                    # <XplStatParam: xplstat_id='188', multiple='None', value='None', ignore_values='', sensor_id='411', static='False', key='current', type='None'>
                    a_xplstat = {'name' : xplstat.name,
                                 'json_id' : xplstat.json_id,
                                 'device_id' : xplstat.device_id,
                                 'id' : xplstat.id,
                                 'schema' : xplstat.schema,
                                 'params' : []
                                }
                    for a_xplstat_param in xplstat.params:
                        a_xplstat['params'].append({
                                                     'xplstat_id' : a_xplstat_param.xplstat_id,
                                                     'multiple' : a_xplstat_param.multiple,
                                                     'value' : a_xplstat_param.value,
                                                     'ignore_values' : a_xplstat_param.ignore_values,
                                                     'sensor_id' : a_xplstat_param.sensor_id,
                                                     'static' : a_xplstat_param.static,
                                                     'key' : a_xplstat_param.key,
                                                     'type' : a_xplstat_param.type
                                                   })

                    self.all_xpl_stats[str(xplstat.id)] = a_xplstat
                #print(self.all_xpl_stats)

            self.log.info("Event : one device changed. Reloading data for xpl stats -- finished")


    def _handle_mq_sensor(self, content):
        """ Handles an mq sensor message and push it into the queue
        the sensorStorage thread will do all conversion
        and store it eventually in the db
        """
        self.log.debug(u"New message (from MQ) > start to store each of the sensors in the store queue...")
        # code for 334
        if 'atTimestamp' in content:
            tim = content['atTimestamp']
            del content['atTimestamp']
            self.log.debug(u"New message (from MQ) > overriding the timestamp to {0}".format(tim))
        else:
            tim = calendar.timegm(time.gmtime())
        # end code for 334
        for sensorid in content:
            data = {}
            data['sensor_id'] = sensorid
            data['time'] = tim
            data['value'] = content[sensorid]
            self._sensor_store_queue.put(data)
            self.log.debug(u"New message (from MQ) > message for sensor_id='{0}' added to the store queue, current length = {1}".format(sensorid, self._sensor_store_queue.qsize()))
        self.log.debug(u"New message (from MQ) > storing in the store queue finished")

    def _load_client_to_xpl_target(self):
        """ Request the client conversion info
            This is an mq req to manager
            If this function does not call self._parse_xpl_target(), all xpl sensors will not be procesed!
        """
        nb_try = 0
        max_try = 5
        ok = False
        while nb_try <= max_try and ok == False:
            nb_try += 1
            cli = MQSyncReq(self.zmq)
            msg = MQMessage()
            msg.set_action('client.list.get')
            response = cli.request('manager', msg.get(), timeout=10)
            if response:
                self._parse_xpl_target(response.get_data())
                ok = True
            else:
                self.log.info(\
                    u"Updating client list failed, no response from manager (try number {0}/{1})".format(nb_try, max_try))
                # We fail to load the client list, so we wait to get something
                time.sleep(5)
        if ok == True:
            self.log.info(u"Updating client list success")
        else:
            self.log.error(u"Updating client list failed too much time! The xpl sensors will not be processed by this component")

    def _parse_xpl_target(self, data):
        """ Translate the mq data info a dict
        for the xpl targets
        """
        tmp = {}
        for cli in data:
            tmp[cli] = data[cli]['xpl_source']
        self.client_xpl_map = tmp

    def _load_conversions(self):
        """ Request the client conversion info
        This is an mq req to manager
        """
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('client.conversion.get')
        response = cli.request('manager', msg.get(), timeout=10)
        if response:
            self._parse_conversions(response.get_data())
        else:
            self.log.error(\
                u"Updating conversion list failed, no response from manager")

    def _parse_conversions(self, data):
        """ Translate the mq data into a dict
        """
        tmp = {}
        for cli in data:
            tmp[cli] = data[cli]
        self.client_conversion_map = tmp

    def _get_conversion_map(self):
        """Return clients conversion maps
        """
        return self.client_conversion_map

    def _send_command(self, data):
        """
        Send a command, first find out if its an xpl or mq command
        TODO move convertion to here
        """
        # TODO : clean the 2 linew below
        #with self._db.session_scope():
        if 1 == 1:
            self.log.info(u"Received new cmd request: {0}".format(data))
            failed = False
            status = False
            uuid = None
            request = data.get_data()
            if 'cmdid' not in request:
                failed = "cmdid not in message data"
                status = False
            if 'cmdparams' not in request:
                failed = "cmdparams not in message data"
                status = False
            if not failed:
                # get the command
                #cmd = self._db.get_command(request['cmdid'])
                with self._cmd_lock:
                    cmd = self.all_commands[str(request['cmdid'])]
                if cmd is not None:
                    if cmd['xpl_command'] is not None:
                        status, uuid, failed = self._send_xpl_command(cmd, request)
                    else:
                        status, uuid, failed = self._send_mq_command(cmd, request)
                        pass
                else:
                    failed = "Can not find the command"
                    status = False
            else:
                status = False
            self.log.debug("   => status: {0}, uuid: {1}, msg: {2}".format(status, uuid, failed))
            # reply
            reply_msg = MQMessage()
            reply_msg.set_action('cmd.send.result')
            reply_msg.add_data('uuid', str(uuid))
            reply_msg.add_data('status', status)
            reply_msg.add_data('reason', failed)
            self.log.debug(u"   => mq reply to requestor")
            self.reply(reply_msg.get())

    def _send_mq_command(self, cmd, request):
        """
        Send out the command to the plugin
        data:
            - command id
            - device id
            - params
        """
        self.log.debug(u"   => Generating MQ message to plugin")
        failed = False
        status = True
        #dev = self._db.get_device(int(cmd['device_id']))
        with self._dev_lock:
            dev = self.all_devices[str(cmd['device_id'])]
        msg = MQMessage()
        msg.set_action('client.cmd')
        msg.add_data('command_id', cmd['id'])
        msg.add_data('device_id', cmd['device_id'])
        for par in cmd['params']:
            if par['key'] in request['cmdparams']:
                value = request['cmdparams'][par['key']]
                # check if we need a conversion
                if par['conversion'] is not None and par['conversion'] != '':
                    if dev['client_id'] in self.client_conversion_map:
                        if par['conversion'] in self.client_conversion_map[dev['client_id']]:
                            self.log.debug( \
                                u"      => Calling conversion {0}".format(par['conversion']))
                            exec(self.client_conversion_map[dev['client_id']][par['conversion']])
                            value = locals()[par['conversion']](value)
                self.log.debug( \
                    u"      => Command parameter after conversion {0} = {1}".format(par['key'], value))
                msg.add_data(par['key'], value)
            else:
                failed = "Parameter ({0}) for device command msg is not provided in the mq message".format(par['key'])
                status = False
        # send to the plugin
        cli = MQSyncReq(self.zmq)
        self.log.debug(u"   => Sending MQ message to the plugin")
        response = cli.request(str(dev['client_id']), msg.get(), timeout=10)
        if not response:
            failed = "Sending the command to the client failed"
            status = False
        else:
            data = response.get_data()
            if not data['status']:
                status = False
                failed = data['reason']
        return status, None, failed

    def _send_xpl_command(self, cmd, request):
        """ Reply to config.get MQ req
            @param data : MQ req message
                Needed info in data:
                - cmdid         => command id to send
                - cmdparams     => key/value pair of all params needed for this command
        """
        self.log.debug(u"   => Generating XPL message to plugin")
        failed = False
        xplcmd = cmd['xpl_command']

        #xplstat = self._db.get_xpl_stat(xplcmd['stat_id'])
        with self._stats_lock:
            xplstat = self.all_xpl_stats[str(xplcmd['stat_id'])]

        if xplstat is not None:
            # get the device from the db
            with self._dev_lock:
                dev = self.all_devices[str(cmd['device_id'])]
            msg = XplMessage()
            if not dev['client_id'] in self.client_xpl_map.keys():
                self._load_client_to_xpl_target()
            if not dev['client_id'] in self.client_xpl_map.keys():
                failed = "Can not fincd xpl source for {0} client_id".format(dev['client_id'])
            else:
                ### Fix bug #349
                # I am not totally sure why before we used the xpl_source from the client list.
                # Indeed for domogik xpl plugins it helps to target the appropriate plugin but
                # for xpl messages for outside of domogik, this is a blocking point !
                # As xpl plugins are starting to be deprecated  as the 'common plugin format', it
                # should not be an issue to retarget xpl messages to '*' for now and later on if
                # there is a real need to target on a dedicated target, implement a bette way to
                # handle this
                # -- Fritz -- oct 2016
                #msg.set_target(self.client_xpl_map[dev['client_id']])
                msg.set_target("*")
                ### End of fix

            msg.set_source(self.myxpl.get_source())
            msg.set_type("xpl-cmnd")
            msg.set_schema(xplcmd['schema'])
            # static paramsw
            for par in xplcmd['params']:
                msg.add_data({par['key'] : par['value']})
            # dynamic params
            for par in cmd['params']:
                if par['key'] in request['cmdparams']:
                    value = request['cmdparams'][par['key']]
                    # check if we need a conversion
                    if par['conversion'] is not None and par['conversion'] != '':
                        if dev['client_id'] in self.client_conversion_map:
                            if par['conversion'] in self.client_conversion_map[dev['client_id']]:
                                self.log.debug( \
                                    u"      => Calling conversion {0}".format(par['conversion']))
                                exec(self.client_conversion_map[dev['client_id']][par['conversion']])
                                value = locals()[par['conversion']](value)
                    self.log.debug( \
                        u"      => Command parameter after conversion {0} = {1}".format(par['key'], value))
                    msg.add_data({par['key'] : value})
                else:
                    failed = "Parameter ({0}) for device command msg is not provided in the mq message".format(par['key'])
            if not failed:
                # send out the msg
                self.log.debug(u"   => Sending xplmessage: {0}".format(msg))
                try:
                    self.myxpl.send(msg)
                except XplMessageError as msg:
                    failed = msg
                #xplstat = self._db.detach(xplstat)
                # generate an uuid for the matching answer published messages
                if xplstat != None:
                    resp_uuid = uuid4()
                    self._cmd_lock_d.acquire()
                    self._cmd_dict[str(resp_uuid)] = xplstat
                    self._cmd_lock_d.release()
                else:
                    resp_uuid = None
                return True, resp_uuid, None
        if failed:
            self.log.error(failed)
            return False, None, failed

    def _create_xpl_trigger(self):
        """ Create a listener to catch
        all xpl-stats and xpl-trig messages
        """
        Listener(self._xpl_callback, self.myxpl, {'xpltype': 'xpl-trig'})
        Listener(self._xpl_callback, self.myxpl, {'xpltype': 'xpl-stat'})

    def _xpl_callback(self, pkt):
        """ The callback for the xpl messages
        push them into the needed queues
        """
        item = {}
        item["msg"] = pkt
        item["received_datetime"] = calendar.timegm(time.gmtime())
        item["clientId"] = next((cli for cli, xpl in self.client_xpl_map.items() if xpl == pkt.source), None)
        self.log.debug(u"New message (from xPL) > start storing in the sensor queue...")
        self._sensor_queue.put(item)
        self.log.debug(u"New message (from xPL) > storing in the sensor queue finished, current length = {0}".format(self._sensor_queue.qsize()))
        self._cmd_lock_p.acquire()
        # only do this when we have outstanding commands
        if len(self._cmd_dict) > 0:
            self._cmd_pkt[time.time()] = pkt
            self.log.debug(u"Adding new message to the cmdQueue, current length = {0}".format(len(self._cmd_dict)))
            #self.log.debug(u"Adding new message to the cmdQueue, current length = {0}, message = {1}".format(len(self._cmd_dict), pkt))
        self._cmd_lock_p.release()

    class _XplCommandThread(threading.Thread):
        """ XplCommandThread class
        Thread that waits for the coresponding reply to a xpl command
        It will send out a pub message when the reply is found
        """
        def __init__(self, log, stop, db, lock_d, lock_p, dic, pkt, pub):
            threading.Thread.__init__(self, name="XplCommandThread")
            # TODO : remove the line below
            #self._db = DbHelper()
            self._log = log
            self._lock_d = lock_d
            self._lock_p = lock_p
            self._dict = dic
            self._pkt = pkt
            self._pub = pub
            self._stop = stop

        def run(self):
            while not self._stop.isSet():
                # remove old pkts
                self._lock_p.acquire()
                for pkt in self._pkt.keys():
                    if pkt < time.time() - CMDTIMEOUT:
                        self._log.warning(u"Delete packet too old (timeout reached) : {0}".format(pkt))
                        del(self._pkt[pkt])
                self._lock_p.release()
                # now try to match if we have enough data
                if len(self._dict) > 0 and len(self._pkt) > 0:
                    todel_pkt = []
                    todel_dict = []
                    for uuid, search in self._dict.items():
                        for tim, pkt in self._pkt.items():
                            print(search)
                            print(pkt)
                            if search['schema'] == pkt.schema:
                                found = True
                                for par in search['params']:
                                    if par['key'] not in pkt.data:
                                        if par['value'] != pkt.data[par['key']]:
                                            found = False
                                        elif par['multiple'] is not None and len(par['multiple']) == 1:
                                            if pkt.data[par['key']] not in par['value'].split(par['multiple']):
                                                found = False
                                if found:
                                    self._log.info(u"Found response message to command with uuid: {0}".format(uuid))
                                    # publish the result
                                    self._pub.send_event('command.result', \
                                              {"uuid" : uuid})
                                    todel_pkt.append(tim)
                                    todel_dict.append(uuid)
                    # now go and delete the unneeded data
                    self._lock_p.acquire()
                    for tim in todel_pkt:
                        if tim in self._pkt:
                            del(self._pkt[tim])
                    #self._log.debug(u"Deleting message from the cmdQueue, current length = {0}".format(len(self._pkt)))
                    # TODO : remove or comment the 2 following lines
                    #self._log.debug(u"Data to delete : {0}".format(todel_dict))
                    #self._log.debug(u"Content before deletion : {0}".format(self._dict))
                    self._lock_p.release()
                    self._lock_d.acquire()
                    for tim in todel_dict:
                        if tim in self._dict:
                            del(self._dict[tim])
                    self._lock_d.release()
                    todel_pkt = []
                    todel_dict = []
                else:
                    # nothing todo, sleep a second
                    time.sleep(1)

    class _XplSensorThread(threading.Thread):
        """ XplSensorThread class
        Thread that will handle the received xplStat(s) and xplTrigger(s)
        It will try to find the matching sensor and then store it into the sensor Store Queue
        This is done in a thread as it can be time consuming to do the DB lookups
        """
        def __init__(self, log, stop, queue, storeQueue):
            threading.Thread.__init__(self, name="XplSensorThread")
            self._db = DbHelper()
            self._log = log
            self._queue = queue
            self._queue_store = storeQueue
            self._stop = stop
            # lock list all_xpl_stat when updating to prevent concurrent access.
            self._lockUpdate = threading.Lock()
            # on startup, load the device parameters
            self.on_device_changed()

        def on_device_changed(self):
            """ Function called when a device have been changed to reload the devices parameters
            """
            with self._lockUpdate:
                self._log.info("Event : one device changed. Reloading data for _XplSensorThread")
                self.all_xpl_stat = []
                with self._db.session_scope():
                    for xplstat in self._db.get_all_xpl_stat():
                        #print(xplstat)
                        #print(xplstat.params)
                        # <XplStat: name='Open/Close sensor', json_id='open_close', device_id='95', id='185', schema='ac.basic'>
                        # <XplStatParam: xplstat_id='188', multiple='None', value='None', ignore_values='', sensor_id='411', static='False', key='current', type='None'>
                        a_xplstat = {'name' : xplstat.name,
                                     'json_id' : xplstat.json_id,
                                     'device_id' : xplstat.device_id,
                                     'id' : xplstat.id,
                                     'schema' : xplstat.schema,
                                     'params' : []
                                    }
                        for a_xplstat_param in xplstat.params:
                            a_xplstat['params'].append({
                                                         'xplstat_id' : a_xplstat_param.xplstat_id,
                                                         'multiple' : a_xplstat_param.multiple,
                                                         'value' : a_xplstat_param.value,
                                                         'ignore_values' : a_xplstat_param.ignore_values,
                                                         'sensor_id' : a_xplstat_param.sensor_id,
                                                         'static' : a_xplstat_param.static,
                                                         'key' : a_xplstat_param.key,
                                                         'type' : a_xplstat_param.type
                                                       })

                        self.all_xpl_stat.append(a_xplstat)
                    #print(self.all_xpl_stat)

                self._log.info("Event : one device changed. Reloading data for _XplSensorThread -- finished")

        def _find_storeparam(self, item):
            #print("ITEM = {0}".format(item['msg']))
            found = False
            tostore = []
            #for xplstat in self._db.get_all_xpl_stat():
            with self._lockUpdate:
                for xplstat in self.all_xpl_stat:
                    matching = 0
                    statics = 0
                    if xplstat['schema'] == item["msg"].schema:
                        #print("  XPLSTAT = {0}".format(xplstat))
                        # we found a possible xplstat
                        # try to match all params and try to find a sensorid and a vlaue to store
                        for param in xplstat['params']:
                            #print("    PARAM = {0}".format(param))
                            ### Caution !
                            # in case you, who are reading this, have to debug something like that :
                            # 2015-08-16 22:04:26,190 domogik-xplgw INFO Storing stat for device 'Garage' (6) and sensor 'Humidity' (69): key 'current' with value '53' after conversion.
                            # 2015-08-16 22:04:26,306 domogik-xplgw INFO Storing stat for device 'Salon' (10) and sensor 'Humidity' (76): key 'current' with value '53' after conversion.
                            # 2015-08-16 22:04:26,420 domogik-xplgw INFO Storing stat for device 'Chambre d'Ewan' (11) and sensor 'Humidity' (80): key 'current' with value '53' after conversion.
                            # 2015-08-16 22:04:26,533 domogik-xplgw INFO Storing stat for device 'Chambre des parents' (12) and sensor 'Humidity' (84): key 'current' with value '53' after conversion.
                            # 2015-08-16 22:04:26,651 domogik-xplgw INFO Storing stat for device 'Chambre de Laly' (13) and sensor 'Humidity' (88): key 'current' with value '53' after conversion.
                            # 2015-08-16 22:04:26,770 domogik-xplgw INFO Storing stat for device 'Entrée' (17) and sensor 'Humidity' (133): key 'current' with value '53' after conversion.
                            #
                            # which means that for a single xPL message, the value is stored in several sensors (WTF!!! ?)
                            # It can be related to the fact that the device address key is no more corresponding between the plugin (info.json and xpl sent by python) and the way the device was create in the databse
                            # this should not happen, but in case... well, we may try to find a fix...

                            if param['key'] in item["msg"].data and param['static']:
                                statics = statics + 1
                                if param['multiple'] is not None and len(param['multiple']) == 1 and item["msg"].data[param['key']] in param['value'].split(param['multiple']):
                                    matching = matching + 1
                                elif item["msg"].data[param['key']] == param['value']:
                                    matching = matching + 1
                        # now we have a matching xplstat, go and find all sensors
                        if matching == statics:
                            #print("  MATHING !!!!!")
                            for param in xplstat['params']:
                                if param['key'] in item["msg"].data and not param['static']:
                                    #print("    ===> TOSTORE !!!!!!!!! : {0}".format({'param': param, 'value': item["msg"].data[param['key']]}))
                                    tostore.append( {'param': param, 'value': item["msg"].data[param['key']]} )
                        if len(tostore) > 0:
                            found = True
            if found:
                return (found, tostore)
            else:
                return False

        def run(self):
            while not self._stop.isSet():
                try:
                    item = self._queue.get(timeout=1)
                    #self._log.debug(u"Getting item from the sensor queue, current length = {0}".format(self._queue.qsize()))
                    self._log.debug(u"Getting item from the sensor queue, current length = {0}, item = '{1}'".format(self._queue.qsize(), item))
                    # if clientid is none, we don't know this sender so ignore
                    # TODO check temp disabled until external members are working
                    #if item["clientId"] is not None:
                    if True:
                        # TODO : remove the 2 below lines
                        #with self._db.session_scope():
                        if 1 == 1:
                            fdata = self._find_storeparam(item)
                            if fdata:
                                #// ICI !!!
                                self._log.debug(u"Found a matching sensor, so starting the storage procedure. Sensor : {0}".format(fdata))
                                for data in fdata[1]:
                                    value = data['value']
                                    storeparam = data['param']
                                    #current_date = calendar.timegm(time.gmtime())
                                    current_date = item["received_datetime"]
                                    store = True
                                    if storeparam['ignore_values']:
                                        if value in eval(storeparam['ignore_values']):
                                            self._log.debug(u"Value {0} is in the ignore list {0}, so not storing.".format(value, storeparam['ignore_values']))
                                            store = False
                                    if store:
                                        data = {}
                                        data['sensor_id'] = storeparam['sensor_id']
                                        data['time'] = current_date
                                        data['value'] = value
                                        self._log.debug(u"Adding new message to the store queue, current length = {0}".format(self._queue_store.qsize()))
                                        self._queue_store.put(data)
                                    else:
                                        self._log.debug(u"Don't need to store this value")
                except queue.Empty:
                    # nothing in the queue, sleep for 1 second
                    time.sleep(1)
                except :
                    self._log.error(traceback.format_exc())

    class _SensorStoreThread(threading.Thread):
        """ SensorStoreThread class
        Thread that will handle the sensorStore queue
        every item in this queue should be stored in the db
        - conversion will happend
        - formula applying
        - rounding
        - and eventually storing it in the db
        Its a thread to make sure it does not block anything else
        """
        def __init__(self, queue, log, get_conversion_map, pub, stop):
            threading.Thread.__init__(self, name="SensorStoreThread")
            self._log = log
            self._db = DbHelper()
            self._conv = get_conversion_map
            self._queue = queue
            self._pub = pub
            self._stop = stop
            # lock list sensors/devices when updating to prevent concurrent access.
            self._lockUpdate = threading.Lock()
            # on startup, load the device parameters
            self.on_device_changed()

        def on_device_changed(self):
            """ Function called when a device have been changed to reload the devices parameters
            """
            with self._lockUpdate:
                self._log.info("Event : one device changed. Reloading data for _SensorStoreThread")
                self.__reload_device()
                self._log.info("Event : one device changed. Reloading data for _SensorStoreThread -- finished")

        def __reload_device(self):
            """Self._lockUpdate.acquire must be do by caller"""

            with self._db.session_scope():
                self.all_sensors = {}
                self.all_devices = {}
                for sen in self._db.get_all_sensor():
                    #print(sen)
                    #<Sensor: conversion='', value_min='None', history_round='0.0', reference='adco', data_type='DT_String', history_duplicate='False', last_received='1474968431', incremental='False', id='29', history_expire='0', timeout='180', history_store='True', history_max='0', formula='None', device_id='2', last_value='030928084432', value_max='3.09036843008e+11', name='Electric meter address'>
                    self.all_sensors[str(sen.id)] = { 'id' : sen.id,
                                                 'conversion' : sen.conversion,
                                                 'value_min' : sen.value_min,
                                                 'history_round' : sen.history_round,
                                                 'reference' : sen.reference,
                                                 'data_type' : sen.data_type,
                                                 'history_duplicate' : sen.history_duplicate,
                                                 'last_received' : sen.last_received,
                                                 'incremental' : sen.incremental,
                                                 'history_expire' : sen.history_expire,
                                                 'timeout' : sen.timeout,
                                                 'history_store' : sen.history_store,
                                                 'history_max' : sen.history_max,
                                                 'formula' : sen.formula,
                                                 'device_id' : sen.device_id,
                                                 'last_value' : sen.last_value,
                                                 'value_max' : sen.value_max,
                                                 'name' : sen.name}
                #print(self.all_sensors)

                for dev in self._db.list_devices():
                    #print(dev)
                    #{'xpl_stats': {u'get_total_space': {'json_id': u'get_total_space', 'schema': u'sensor.basic', 'id': 3, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_total_space', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'total_space', 'key': u'type'}]}, 'name': u'Total space'}, u'get_free_space': {'json_id': u'get_free_space', 'schema': u'sensor.basic', 'id': 4, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_free_space', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'free_space', 'key': u'type'}]}, 'name': u'Free space'}, u'get_used_space': {'json_id': u'get_used_space', 'schema': u'sensor.basic', 'id': 5, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_used_space', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'used_space', 'key': u'type'}]}, 'name': u'Used space'}, u'get_percent_used': {'json_id': u'get_percent_used', 'schema': u'sensor.basic', 'id': 6, 'parameters': {'dynamic': [{'ignore_values': u'', 'sensor_name': u'get_percent_used', 'key': u'current'}], 'static': [{'type': u'string', 'value': u'/', 'key': u'device'}, {'type': None, 'value': u'percent_used', 'key': u'type'}]}, 'name': u'Percent used'}}, 'commands': {}, 'description': u'', 'reference': u'', 'sensors': {u'get_total_space': {'value_min': None, 'data_type': u'DT_Byte', 'incremental': False, 'id': 57, 'reference': u'get_total_space', 'conversion': u'', 'name': u'Total Space', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'14763409408', 'value_max': 14763409408.0}, u'get_free_space': {'value_min': None, 'data_type': u'DT_Byte', 'incremental': False, 'id': 59, 'reference': u'get_free_space', 'conversion': u'', 'name':u'Free Space', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'1319346176', 'value_max': 8220349952.0}, u'get_used_space': {'value_min': None, 'data_type': u'DT_Byte', 'incremental': False, 'id': 60, 'reference': u'get_used_space', 'conversion': u'', 'name': u'Used Space', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'13444063232', 'value_max': 14763409408.0}, u'get_percent_used': {'value_min': None, 'data_type':u'DT_Scaling', 'incremental': False, 'id': 58, 'reference': u'get_percent_used', 'conversion': u'', 'name': u'Percent used', 'last_received': 1459192737, 'timeout': 0, 'formula': None, 'last_value': u'91', 'value_max': 100.0}}, 'xpl_commands': {}, 'client_id': u'plugin-diskfree.ambre', 'device_type_id': u'diskfree.disk_usage', 'client_version': u'1.0', 'parameters': {u'interval': {'value': u'5', 'type': u'integer', 'id': 5, 'key': u'interval'}}, 'id': 3, 'name': u'Ambre /'}
                    self.all_devices[str(dev['id'])] = {
                                                    'client_id': dev['client_id'],
                                                    'id': dev['id'],
                                                    'name': dev['name']
                                                  }
                #print(self.all_devices)
                self._log.debug(u"Devices and sensors reloaded for _SensorStoreThread")

        def run(self):
            while not self._stop.isSet():
                try:
                    store = True
                    item = self._queue.get(timeout=1)
                    #self._log.debug(u"Getting item from the store queue, current length = {0}".format(self._queue.qsize()))
                    self._log.debug(u"Getting item from the store queue, current length = {0}, item = '{1}'".format(self._queue.qsize(), item))
                    # handle ignore
                    value = item['value']
                    senid = item['sensor_id']
                    current_date = item['time']
                    # get the sensor and dev
                    with self._lockUpdate:
                        if str(senid) not in self.all_sensors :
                            self._log.debug(u"Sensor not find, reload sensors and device_list at once to be sure of devices_list update")
                            self.__reload_device()
                        sen = self.all_sensors[str(senid)]
                        if str(sen['device_id'])not in self.all_devices :
                            self._log.debug(u"Device not find, reload sensors and devices_list at once to be sure of devices_list update")
                            self.__reload_device()
                            sen = self.all_sensors[str(senid)]
                        dev = self.all_devices[str(sen['device_id'])]
                    # check if we need a conversion
                    if sen['conversion'] is not None and sen['conversion'] != '':
                        if dev['client_id'] in self._conv() and sen['conversion'] in self._conv()[dev['client_id']]:
                            self._log.debug( \
                                u"Calling conversion {0}".format(sen['conversion']))
                            exec(self._conv()[dev['client_id']][sen['conversion']])
                            value = locals()[sen['conversion']](value)
                    self._log.info( \
                            u"Storing stat for device '{0}' ({1}) and sensor '{2}' ({3}) with value '{4}' after conversion." \
                            .format(dev['name'], dev['id'], sen['name'], sen['id'], value))
                    try:
                        # do the store
                        with self._lockUpdate:
                            with self._db.session_scope():
                                value = self._db.add_sensor_history(\
                                        senid, \
                                        sen, \
                                        value, \
                                        current_date)
                                # publish the result
                                self._pub.send_event('device-stats', \
                                      {"timestamp" : current_date, \
                                      "device_id" : dev['id'], \
                                      "sensor_id" : senid, \
                                      "stored_value" : value})
                        # Release CPU for other work
                        time.sleep(0.1)
                    except Exception as exp:
                        self._log.error(u"Error when adding sensor history : {0}".format(traceback.format_exc()))
                except queue.Empty:
                    # nothing in the queue, sleep for 1 second
                    time.sleep(1)
                except Exception as exp:
                    self._log.error(traceback.format_exc())

if __name__ == '__main__':
    EVTN = XplManager()

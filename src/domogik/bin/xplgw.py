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
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.database import DbHelper
from domogik.xpl.common.xplmessage import XplMessage
from domogikmq.pubsub.publisher import MQPub
from domogikmq.pubsub.subscriber import MQSyncSub
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from domogikmq.pubsub.subscriber import MQAsyncSub
import time
import traceback
import calendar
import zmq
import json
import sys
import Queue
import threading

################################################################################
class XplManager(XplPlugin, MQAsyncSub):
    """ Statistics manager
    """

    def __init__(self):
        """ Initiate DbHelper, Logs and config
        """
        XplPlugin.__init__(self, 'xplgw', log_prefix = "")
        MQAsyncSub.__init__(self, self.zmq, 'xplgw', ['client.conversion', 'client.list'])

        self.log.info(u"XPL manager initialisation...")
        self._db = DbHelper()
        self.pub = MQPub(zmq.Context(), 'xplgw')
        # some initial data sets
        self.client_xpl_map = {}
        self.client_conversion_map = {}
        self._db_sensors = {}
        self._db_xplstats = {}
        self._sensor_queue = Queue.Queue()
        # load some initial data from manager and db
        self._load_client_to_xpl_target()
        self._load_conversions()
        # create a general listener
        self._create_xpl_trigger()
        # start handling the xplmessages
        self._sThread = self._SensorThread(self.log, self._sensor_queue, self.client_conversion_map, self.pub)
        self._sThread.start()
        # start the sensorthread
        self.ready()

    def on_mdp_request(self, msg):
    # XplPlugin handles MQ Req/rep also
        try:
            XplPlugin.on_mdp_request(self, msg)

            if msg.get_action() == "reload":
                msg = MQMessage()
                msg.set_action( 'reload.result' )
                self.reply(msg.get())
            elif msg.get_action() == "cmd.send":
                self._send_xpl_command(msg)
        except:
            self.log.error(traceback.format_exc())

    def on_message(self, msgid, content):
        try:
            if msgid == 'client.conversion':
                self._parse_conversions(content)
            elif msgid == 'client.list':
                self._parse_xpl_target(content)
        except:
            self.log.error(traceback.format_exc())

    def _load_client_to_xpl_target(self):
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('client.list.get')
        response = cli.request('manager', msg.get(), timeout=10)
        if response:
            self._parse_xpl_target(response.get_data())
        else:
            self.log.error(u"Updating client list was not successfull, no response from manager")

    def _parse_xpl_target(self, data):
        tmp = {}
        for cli in data:
            tmp[cli] = data[cli]['xpl_source']
        self.client_xpl_map = tmp
    
    def _load_conversions(self):
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('client.conversion.get')
        response = cli.request('manager', msg.get(), timeout=10)
        if response:
            self._parse_conversions(response.get_data())
        else:
            self.log.error(u"Updating client conversion list was not successfull, no response from manager")

    def _parse_conversions(self, data):
        tmp = {}
        for cli in data:
            tmp[cli] = data[cli]
        self.client_conversion_map = tmp

    def _send_xpl_command(self, data):
        """ Reply to config.get MQ req
            @param data : MQ req message
                Needed info in data:
                - cmdid         => command id to send
                - cmdparams     => key/value pair of all params needed for this command
        """
        with self._db.session_scope():
            self.log.info(u"Received new cmd request: {0}".format(data))
            failed = False
            request = data.get_data()
            if 'cmdid' not in request:
                failed = "cmdid not in message data"
            if 'cmdparams' not in request:
                failed = "cmdparams not in message data"
            if not failed:
                # get the command
                cmd = self._db.get_command(request['cmdid'])
                if cmd is not None:
                    if cmd.xpl_command is not None:
                        xplcmd = cmd.xpl_command
                        xplstat = self._db.get_xpl_stat(xplcmd.stat_id)
                        if xplstat is not None:
                            # get the device from the db
                            dev = self._db.get_device(int(cmd.device_id))
                            msg = XplMessage()
                            if not dev['client_id'] in self.client_xpl_map.keys():
                                self._load_client_to_xpl_target()
                            if not dev['client_id'] in self.client_xpl_map.keys():
                                failed = "Can not fincd xpl source for {0} client_id".format(dev['client_id'])
                            else:
                                msg.set_target(self.client_xpl_map[dev['client_id']])
                            msg.set_source(self.myxpl.get_source())
                            msg.set_type("xpl-cmnd")
                            msg.set_schema( xplcmd.schema)
                            # static paramsw
                            for p in xplcmd.params:
                                msg.add_data({p.key : p.value})
                            # dynamic params
                            for p in cmd.params:
                                if p.key in request['cmdparams']:
                                    value = request['cmdparams'][p.key]
                                    # chieck if we need a conversion
                                    if p.conversion is not None and p.conversion != '':
                                        if dev['client_id'] in self.client_conversion_map:
                                            if p.conversion in self.client_conversion_map[dev['client_id']]:
                                                exec(self.client_conversion_map[dev['client_id']][p.conversion])
                                                value = locals()[p.conversion](value)
                                    msg.add_data({p.key : value})
                                else:
                                    failed = "Parameter ({0}) for device command msg is not provided in the mq message".format(p.key)
                            if not failed:
                                # send out the msg
                                self.log.debug(u"Sending xplmessage: {0}".format(msg))
                                self.myxpl.send(msg)
                                ### Wait for answer
                                stat_received = 0
                                if xplstat != None:
                                    # get xpl message from queue
                                    self.log.debug(u"Command : wait for answer...")
                                    sub = MQSyncSub( self.zmq, 'xplgw-command', ['device-stats'] )
                                    stat = sub.wait_for_event()
                                    if stat is not None:
                                        reply = json.loads(stat['content'])
                                        reply_msg = MQMessage()
                                        reply_msg.set_action('cmd.send.result')
                                        reply_msg.add_data('stat', reply)
                                        reply_msg.add_data('status', True)
                                        reply_msg.add_data('reason', None)
                                        self.log.debug(u"mq reply".format(reply_msg.get()))
                                        self.reply(reply_msg.get())
        if failed:
            self.log.error(failed)
            reply_msg = MQMessage()
            reply_msg.set_action('cmd.send.result')
            reply_msg.add_data('status', False)
            reply_msg.add_data('reason', failed)
            self.log.debug(u"mq reply".format(reply_msg.get()))
            self.reply(reply_msg.get())

    def _create_xpl_trigger(self):
        Listener(self._xpl_callback, self.myxpl, {'xpltype': 'xpl-stat'})
        Listener(self._xpl_callback, self.myxpl, {'xpltype': 'xpl-trig'})

    def _xpl_callback(self, pkt):
        item = {}
        item["msg"] = pkt
        item["clientId"] = next((cli for cli, xpl in self.client_xpl_map.items() if xpl == pkt.source), None)
        self._sensor_queue.put(item)
        self.log.debug(u"Adding new message to the sensorQueue, current length = {0}".format(self._sensor_queue.qsize()))

    class _SensorThread(threading.Thread):
        def __init__(self, log, queue, conv, pub):
            threading.Thread.__init__(self)
            self._db = DbHelper()
            self._log = log
            self._queue = queue
            self._conv = conv
            self._pub = pub

        def run(self):
            while True:
                try:
                    item = self._queue.get()
                    self._log.debug(u"Getting item from the sensorQueue, current length = {0}".format(self._queue.qsize()))
                    self._log.debug(item)
                    # if clientid is none, we don't know this sender so ignore
                    if item["clientId"] is not None:
                        with self._db.session_scope():
                            found = 0 
                            for xplstat in self._db.get_all_xpl_stat():
                                matching = 0
                                value = False
                                storeparam = False
                                if xplstat.schema == item["msg"].schema:
                                    # we found a possible xplstat
                                    # try to match all params and try to find a sensorid and a vlaue to store
                                    for param in xplstat.params:
                                        if param.key in item["msg"].data:
                                            if param.static:
                                                if item["msg"].data[param.key] == param.value:
                                                    matching = matching + 1
                                            else:
                                                matching = matching + 1
                                                storeparam = param
                                                value = item["msg"].data[param.key]
                                    if storeparam:
                                        if matching == len(xplstat.params): 
                                            found = 1
                                            break
                                        else:
                                            self._log.debug(u"we found a matching xplmessage, but the length of the one in the db is not the same as the one on the xplnetwork: db={0} xpl={1}".format(len(xplstat.params), matching))
                            if found:
                                self._log.debug(u"Found a matching sensor, so starting the storage procedure")
                                current_date = calendar.timegm(time.gmtime())
                                stored_value = None
                                store = True
                                if param.ignore_values:
                                    if value in eval(storeparam.ignore_values):
                                        self._log.debug( \
                                                u"Value {0} is in the ignore list {0}, so not storing." \
                                                .format(value, storeparam.ignore_values))
                                        store = False
                                if store:
                                    # get the sensor and dev
                                    sen = self._db.get_sensor(storeparam.sensor_id)
                                    dev = self._db.get_device(sen.device_id)
                                    # check if we need a conversion
                                    if sen.conversion is not None and sen.conversion != '':
                                        if dev['client_id'] in self._conv:
                                            if sen.conversion in self._conv[dev['client_id']]:
                                                self._log.debug( \
                                                    u"Calling conversion {0}".format(sen.conversion))
                                                exec(self._conv[dev['client_id']][sen.conversion])
                                                value = locals()[sen.conversion](value)
                                    self._log.info( \
                                            u"Storing stat for device '{0}' ({1}) and sensor'{2}' ({3}): key '{4}' with value '{5}' after conversion." \
                                            .format(dev['name'], dev['id'], sen.name, sen.id, param.key, value))
                                    # do the store
                                    stored_value = value
                                    try:
                                        self._db.add_sensor_history(\
                                                storeparam.sensor_id, \
                                                value, \
                                                current_date)
                                    except:
                                        self._log.error(u"Error when adding sensor history : {0}".format(traceback.format_exc()))
                                else:
                                    self._log.debug(u"Don't need to store this value")
                                # publish the result
                                self._pub.send_event('device-stats', \
                                          {"timestamp" : current_date, \
                                          "device_id" : dev['id'], \
                                          "sensor_id" : sen.id, \
                                          "stored_value" : stored_value})

                except Queue.Empty:
                    # nothing in the queue, sleep for 1 second
                    time.sleep(1)
                except:
                    self._log_stats.error(traceback.format_exc())

if __name__ == '__main__':
    EVTN = XplManager()
        

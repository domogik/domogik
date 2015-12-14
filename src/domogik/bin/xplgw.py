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
import json
import Queue
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
        XplPlugin.__init__(self, 'xplgw', log_prefix="")
        self.add_mq_sub('client.conversion')
        self.add_mq_sub('client.list')
        self.add_mq_sub('client.sensor')

        self.log.info(u"XPL manager initialisation...")
        self._db = DbHelper()
        self.pub = MQPub(zmq.Context(), 'xplgw')
        # some initial data sets
        self.client_xpl_map = {}
        self.client_conversion_map = {}
        self._db_sensors = {}
        self._db_xplstats = {}
        # queue to store the message that needs to be ahndled for sensor checking
        self._sensor_queue = Queue.Queue()
        # queue to handle the sensor storage
        self._sensor_store_queue = Queue.Queue()
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
            self.log, self._sensor_queue, \
            self._sensor_store_queue)
        self._x_thread.start()
        # start handling the command reponses in a thread
        self._c_thread = self._XplCommandThread(\
            self.log, self._db, self._cmd_lock_d, \
            self._cmd_lock_p, self._cmd_dict, self._cmd_pkt, self.pub)
        self._c_thread.start()
        # start the sensor storage thread
        self._s_thread = self._SensorStoreThread(\
                self._sensor_store_queue, self.log, \
                self._get_conversion_map, self.pub)
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
        except Exception as exp:
            self.log.error(traceback.format_exc())

    def on_message(self, msgid, content):
        """ Method called on a subscribed message
        """
        try:
            XplPlugin.on_message(self, msgid, content)
            if msgid == 'client.conversion':
                self._parse_conversions(content)
            elif msgid == 'client.list':
                self._parse_xpl_target(content)
            elif msgid == 'client.sensor':
                self._handle_mq_sensor(content)
        except Exception as exp:
            self.log.error(traceback.format_exc())

    def _handle_mq_sensor(self, content):
        """ Handles an mq sensor message and push it into the queue
        the sensorStorage thread will do all conversion
        and store it eventually in the db
        """
        tim = calendar.timegm(time.gmtime())
        for sensorid in content:
            data = {}
            data['sensor_id'] = sensorid
            data['time'] = tim
            data['value'] = content[sensorid]
            self._sensor_store_queue.put(data)
        self.log.debug(u"Adding new message to the sensorStoreQueue, current length = {0}".format(self._sensor_store_queue.qsize()))

    def _load_client_to_xpl_target(self):
        """ Request the client conversion info
        This is an mq req to manager
        """
        cli = MQSyncReq(self.zmq)
        msg = MQMessage()
        msg.set_action('client.list.get')
        response = cli.request('manager', msg.get(), timeout=10)
        if response:
            self._parse_xpl_target(response.get_data())
        else:
            self.log.error(\
                u"Updating client list failed, no response from manager")

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
        with self._db.session_scope():
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
                cmd = self._db.get_command(request['cmdid'])
                if cmd is not None:
                    if cmd.xpl_command is not None:
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
        dev = self._db.get_device(int(cmd.device_id))
        msg = MQMessage()
        msg.set_action('client.cmd')
        msg.add_data('command_id', cmd.id)
        msg.add_data('device_id', cmd.device_id)
        for par in cmd.params:
            if par.key in request['cmdparams']:
                value = request['cmdparams'][par.key]
                # chieck if we need a conversion
                if par.conversion is not None and par.conversion != '':
                    if dev['client_id'] in self.client_conversion_map:
                        if par.conversion in self.client_conversion_map[dev['client_id']]:
                            self.log.debug( \
                                u"      => Calling conversion {0}".format(par.conversion))
                            exec(self.client_conversion_map[dev['client_id']][par.conversion])
                            value = locals()[par.conversion](value)
                self.log.debug( \
                    u"      => Command parameter after conversion {0} = {1}".format(par.key, value))
                msg.add_data(par.key, value)
            else:
                failed = "Parameter ({0}) for device command msg is not provided in the mq message".format(par.key)
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
            msg.set_schema(xplcmd.schema)
            # static paramsw
            for par in xplcmd.params:
                msg.add_data({par.key : par.value})
            # dynamic params
            for par in cmd.params:
                if par.key in request['cmdparams']:
                    value = request['cmdparams'][par.key]
                    # chieck if we need a conversion
                    if par.conversion is not None and par.conversion != '':
                        if dev['client_id'] in self.client_conversion_map:
                            if par.conversion in self.client_conversion_map[dev['client_id']]:
                                self.log.debug( \
                                    u"      => Calling conversion {0}".format(par.conversion))
                                exec(self.client_conversion_map[dev['client_id']][par.conversion])
                                value = locals()[par.conversion](value)
                    self.log.debug( \
                        u"      => Command parameter after conversion {0} = {1}".format(par.key, value))
                    msg.add_data({par.key : value})
                else:
                    failed = "Parameter ({0}) for device command msg is not provided in the mq message".format(par.key)
            if not failed:
                # send out the msg
                self.log.debug(u"   => Sending xplmessage: {0}".format(msg))
                try:
                    self.myxpl.send(msg)
                except XplMessageError as msg:
                    failed = msg
                xplstat = self._db.detach(xplstat)
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
        self._sensor_queue.put(item)
        self.log.debug(u"Adding new message to the sensorQueue, current length = {0}".format(self._sensor_queue.qsize()))
        #self.log.debug(u"Adding new message to the sensorQueue, current length = {0}, message = {1}".format(self._sensor_queue.qsize(), pkt))
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
        def __init__(self, log, db, lock_d, lock_p, dic, pkt, pub):
            threading.Thread.__init__(self)
            self._db = DbHelper()
            self._log = log
            self._lock_d = lock_d
            self._lock_p = lock_p
            self._dict = dic
            self._pkt = pkt
            self._pub = pub

        def run(self):
            while True:
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
                            if search.schema == pkt.schema:
                                found = True
                                for par in search.params:
                                    if par.key not in pkt.data:
                                        if par.value != pkt.data[par.key]:
                                            found = False
                                        elif par.multiple is not None and len(par.multiple) == 1:
                                            if pkt.data[par.key] not in par.value.split(par.multiple):
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
        It will try to fidn the matching sensor and then store it into the sensor Store Queue
        This is done in a thread as it can be time consuming to do the DB lookups
        """
        def __init__(self, log, queue, storeQueue):
            threading.Thread.__init__(self)
            self._db = DbHelper()
            self._log = log
            self._queue = queue
            self._queue_store = storeQueue

        def _find_storeparam(self, item):
            #print("ITEM = {0}".format(item['msg']))
            found = False
            tostore = []
            for xplstat in self._db.get_all_xpl_stat():
                sensors = 0
                matching = 0
                statics = 0
                if xplstat.schema == item["msg"].schema:
                    #print("  XPLSTAT = {0}".format(xplstat))
                    # we found a possible xplstat
                    # try to match all params and try to find a sensorid and a vlaue to store
                    for param in xplstat.params:
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

                        if param.key in item["msg"].data and param.static:
                            statics = statics + 1
                            if param.multiple is not None and len(param.multiple) == 1 and item["msg"].data[param.key] in param.value.split(param.multiple):
                                matching = matching + 1
                            elif item["msg"].data[param.key] == param.value:
                                matching = matching + 1
                    # now we have a matching xplstat, go and find all sensors
                    if matching == statics:
                        #print("  MATHING !!!!!")
                        for param in xplstat.params:
                            if param.key in item["msg"].data and not param.static:     
                                #print("    ===> TOSTORE !!!!!!!!! : {0}".format({'param': param, 'value': item["msg"].data[param.key]}))
                                tostore.append( {'param': param, 'value': item["msg"].data[param.key]} )
                    if len(tostore) > 0:
                        found = True
            if found:
                return (found, tostore)
            else:
                return False

        def run(self):
            while True:
                try:
                    item = self._queue.get()
                    self._log.debug(u"Getting item from the sensorQueue, current length = {0}".format(self._queue.qsize()))
                    # if clientid is none, we don't know this sender so ignore
                    # TODO check temp disabled until external members are working
                    #if item["clientId"] is not None:
                    if True:
                        with self._db.session_scope():
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
                                    if storeparam.ignore_values:
                                        if value in eval(storeparam.ignore_values):
                                            self._log.debug(u"Value {0} is in the ignore list {0}, so not storing.".format(value, storeparam.ignore_values))
                                            store = False
                                    if store:
                                        data = {}
                                        data['sensor_id'] = storeparam.sensor_id
                                        data['time'] = current_date
                                        data['value'] = value
                                        self._queue_store.put(data)
                                        self._log.debug(u"Adding new message to the sensorStoreQueue, current length = {0}".format(self._queue_store.qsize()))
                                    else:
                                        self._log.debug(u"Don't need to store this value")
                except Queue.Empty:
                    # nothing in the queue, sleep for 1 second
                    time.sleep(1)
                except Exception as exp:
                    self._log.error(traceback.format_exc())

    class _SensorStoreThread(threading.Thread):
        """ SensorStoreThread class
        Thread that will handle the sensorStore queue
        every item in this queue should eb stored in the db
        - conversion will happend
        - formula applying
        - rounding
        - and eventually storing it in the db
        Its a thread to make sure it does not block anything else
        """
        def __init__(self, queue, log, get_conversion_map, pub):
            threading.Thread.__init__(self)
            self._log = log
            self._db = DbHelper()
            self._conv = get_conversion_map
            self._queue = queue
            self._pub = pub

        def run(self):
            while True:
                try:
                    store = True
                    item = self._queue.get()
                    self._log.debug(u"Getting item from the sensorStoreQueue, current length = {0}".format(self._queue.qsize()))
                    # handle ignore
                    value = item['value']
                    senid = item['sensor_id']
                    current_date = item['time']
                    # get the sensor and dev
                    with self._db.session_scope():
                        sen = self._db.get_sensor(senid)
                        dev = self._db.get_device(sen.device_id)
                        # check if we need a conversion
                        if sen.conversion is not None and sen.conversion != '':
                            if dev['client_id'] in self._conv() and sen.conversion in self._conv()[dev['client_id']]:
                                self._log.debug( \
                                    u"Calling conversion {0}".format(sen.conversion))
                                exec(self._conv()[dev['client_id']][sen.conversion])
                                value = locals()[sen.conversion](value)
                        self._log.info( \
                                u"Storing stat for device '{0}' ({1}) and sensor '{2}' ({3}) with value '{4}' after conversion." \
                                .format(dev['name'], dev['id'], sen.name, sen.id, value))
                        # do the store
                        try:
                            self._db.add_sensor_history(\
                                    senid, \
                                    value, \
                                    current_date)
                            # publish the result
                            self._pub.send_event('device-stats', \
                                  {"timestamp" : current_date, \
                                  "device_id" : dev['id'], \
                                  "sensor_id" : sen.id, \
                                  "stored_value" : value})
                        except Exception as exp:
                            self._log.error(u"Error when adding sensor history : {0}".format(traceback.format_exc()))
                except Queue.Empty:
                    # nothing in the queue, sleep for 1 second
                    time.sleep(1)
                except Exception as exp:
                    self._log.error(traceback.format_exc())

if __name__ == '__main__':
    EVTN = XplManager() 

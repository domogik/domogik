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

Purpose
=======

Tools for regression tests

Usage
=====
** in command line **
python writesensor.py <sensor_id> <sensor_value>

@author: Nico84Dev <nico84dev at gmail.com>
@copyright: (C) 2007-2019 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.database import DbHelper
from domogikmq.pubsub.publisher import MQPub
import zmq
import time
import traceback
import sys

print(sys.argv)
senid = sys.argv[1]
value = sys.argv[2]
current_date = int(time.time())
sensor = {}
db = DbHelper(owner="Develop write sensor")

with db.session_scope():
    sen = db.get_sensor(senid)
    #<Sensor: conversion='', value_min='None', history_round='0.0', reference='adco', data_type='DT_String', history_duplicate='False', last_received='1474968431', incremental='False', id='29', history_expire='0', timeout='180', history_store='True', history_max='0', formula='None', device_id='2', last_value='030928084432', value_max='3.09036843008e+11', name='Electric meter address'>
    if sen and str(sen.id) == str(senid) :
        sensor = { 'id' : sen.id,
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
    print("**** sensor : ", sensor)
    if sensor :
        print('sensor find, write new value ...')
        pub = MQPub(zmq.Context(), 'xplgw')
        value = db.add_sensor_history(\
                senid, \
                sensor, \
                value, \
                current_date)
        # publish the result
        pub.send_event('device-stats', \
              {"timestamp" : current_date, \
              "device_id" : sensor['device_id'], \
              "sensor_id" : senid, \
              "stored_value" : value})
        print('value writed')

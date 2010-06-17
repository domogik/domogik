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

Module purpose
==============

Install the Domogik database based on config file values

Implements
==========


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys

from sqlalchemy import create_engine

from domogik.common import sql_schema
from domogik.common import database
from domogik.common.configloader import Loader

cfg = Loader('database')
config = None
if len(sys.argv) > 1:
    config = cfg.load(sys.argv[1])
else:
    config = cfg.load()
test_url = ''

try:
    db_config = dict(config[1])
    url = "%s:///" % db_config['db_type']
    if db_config['db_type'] == 'sqlite':
        url = "%s%s" % (url,db_config['db_path'])
    else:
        if db_config['db_port'] != '':
            url = "%s%s:%s@%s:%s/%s" % (url, db_config['db_user'], db_config['db_password'], \
              db_config['db_host'], db_config['db_port'], db_config['db_name'])
        else:
            url = "%s%s:%s@%s/%s" % (url, db_config['db_user'], db_config['db_password'], \
              db_config['db_host'], db_config['db_name'])
    test_url = '%s_test' % url
except Exception, e:
    print "Some errors appears during connection to the database : %s" % e

engine = create_engine(url)
engine_test = create_engine(test_url)

###
# Installer
###
sql_schema.metadata.create_all(engine)
# For unit tests
sql_schema.metadata.create_all(engine_test)

db = database.DbHelper()

# Initialize default system configuration
db.update_system_config()

# Create a default user account
db.add_default_user_account()

# Create device technologie features for X10

device_technology = db.add_device_technology(dt_id='x10', dt_name='X10', dt_description='')
device_type = db.add_device_type(dty_name='Switch', dt_id=device_technology.id)
db.add_actuator_feature(af_name='Switch', af_device_type_id=device_type.id,
                        af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                        af_value_type='binary', af_stat_key='command')
device_type = db.add_device_type(dty_name='Dimmer', dt_id=device_technology.id)
db.add_actuator_feature(af_name='Switch', af_device_type_id=device_type.id,
                        af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                        af_value_type='binary', af_stat_key='command')
db.add_actuator_feature(af_name='Dimmer', af_device_type_id=device_type.id,
                        af_parameters='{&quot;command&quot;:&quot;dim&quot;,&quot;valueMin&quot;:0, &quot;valueMax&quot;:100}',
                        af_value_type='range', af_stat_key='level')

# Create device technologie features for PLCBus
device_technology = db.add_device_technology(dt_id='plcbus', dt_name='PLCBus', dt_description='')
device_type = db.add_device_type(dty_name='Switch', dt_id=device_technology.id)
db.add_actuator_feature(af_name='Switch', af_device_type_id=device_type.id,
                        af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                        af_value_type='binary', af_return_confirmation=True)
device_type = db.add_device_type(dty_name='Dimmer', dt_id=device_technology.id)
db.add_actuator_feature(af_name='Switch', af_device_type_id=device_type.id,
                        af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                        af_value_type='binary', af_return_confirmation=True)
db.add_actuator_feature(af_name='Dimmer', af_device_type_id=device_type.id,
                        af_parameters='{&quot;command&quot;:&quot;dim&quot;,&quot;valueMin&quot;:0, &quot;valueMax&quot;:100}', af_value_type='range',
                        af_return_confirmation=True)

# Create device technology features for EIB/KNX
db.add_device_technology(dt_id='eibknx', dt_name='EIB/KNX', dt_description='')

# Create device technology features for 1wire
device_technology = db.add_device_technology(dt_id='onewire', dt_name='1-Wire', dt_description='')
device_type = db.add_device_type(dty_name='Temperature', dt_id=device_technology.id)
db.add_sensor_feature(sf_name='Temperature',
                   sf_device_type_id=device_type.id, sf_value_type='number',
                   sf_parameters='{&quot;unit&quot;:&quot;&deg;C&quot;}',
                   sf_stat_key='current')


# Create device technology features for RFXCom
db.add_device_technology(dt_id='rfxcom', dt_name='RFXCom', dt_description='')
# Create device technology features for IR
db.add_device_technology(dt_id='ir', dt_name='Infra Red', dt_description='')

# Create device technology features for Service
device_technology = db.add_device_technology(dt_id='service', dt_name='Service',
                                             dt_description='Distributed services, water, gas, electricity')
device_type = db.add_device_type(dty_name='Teleinfo', dt_id=device_technology.id)
db.add_sensor_feature(sf_name='Instantaneous intensity', sf_device_type_id=device_type.id, sf_value_type='number', sf_parameters='{&quot;unit&quot;:&quot;A&quot;}', sf_stat_key='iinst')
db.add_sensor_feature(sf_name='Off peak', sf_device_type_id=device_type.id, sf_value_type='number', sf_parameters='{&quot;unit&quot;:&quot;Wh&quot;}', sf_stat_key='hchc')
db.add_sensor_feature(sf_name='Maximum intensity', sf_device_type_id=device_type.id, sf_value_type='number', sf_parameters='{&quot;unit&quot;:&quot;A&quot;}', sf_stat_key='imax')
db.add_sensor_feature(sf_name='Tariff Period', sf_device_type_id=device_type.id, sf_value_type='string', sf_parameters=None, sf_stat_key='ptec')
db.add_sensor_feature(sf_name='Power', sf_device_type_id=device_type.id, sf_value_type='number', sf_parameters='{&quot;unit&quot;:&quot;Va&quot;}', sf_stat_key='papp')
db.add_sensor_feature(sf_name='Group schedule', sf_device_type_id=device_type.id, sf_value_type='string', sf_parameters=None, sf_stat_key='hhphc')
db.add_sensor_feature(sf_name='On Peak', sf_device_type_id=device_type.id, sf_value_type='number', sf_parameters='{&quot;unit&quot;:&quot;Wh&quot;}', sf_stat_key='hchp')

# Create device technology features for RFID
db.add_device_technology(dt_id='rfid', dt_name='RFID', dt_description='')
# Create device technology features for Computer
device_technology = db.add_device_technology(dt_id='computer', dt_name='Computer',
                                             dt_description='Computers monitoring and controling ')
device_type = db.add_device_type(dty_name='WOL', dt_id=device_technology.id)
db.add_actuator_feature(af_name='Activation', af_device_type_id=device_type.id,
                        af_parameters='{&quot;command&quot;:&quot;wol&quot;}',af_value_type='trigger',
                        af_return_confirmation=False)
# Create device technologie features for MultiMedia
db.add_device_technology(dt_id='multimedia', dt_name='MultiMedia', dt_description='Music, Video')
# Create device technologie features for Communication
db.add_device_technology(dt_id='communication', dt_name='Communication',
                         dt_description='Telephony, videophone, mails, messaging')

# Create device usages
db.add_device_usage(du_name='Light', du_description='Lamp, light usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;} }')
db.add_device_usage(du_name='Socket', du_description='Socket usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;} }')
db.add_device_usage(du_name='Shutter', du_description='Shutter usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Down&quot;, &quot;state1&quot;:&quot;Up&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;} }')
db.add_device_usage(du_name='Air conditioning', du_description='Air conditioning usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&deg;C&quot;} }')
db.add_device_usage(du_name='Ventilation', du_description='Ventilation usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;} }')
db.add_device_usage(du_name='Heating', du_description='Heating',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&deg;C&quot;} }')
db.add_device_usage(du_name='Appliance', du_description='Appliance usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;} }')
db.add_device_usage(du_name='Desktop Computer', du_description='Desktop computer usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;} }')
db.add_device_usage(du_name='Server', du_description='Server usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;} }')
db.add_device_usage(du_name='Phone', du_description='Phone usage', du_default_options='{ }')
db.add_device_usage(du_name='TV', du_description='Television usage',
                    du_default_options='{ &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;} }')
db.add_device_usage(du_name='Water', du_description='Water service', du_default_options='{ }')
db.add_device_usage(du_name='Gas', du_description='Gas service', du_default_options='{ }')
db.add_device_usage(du_name='Electricity', du_description='Electricity service', du_default_options='{ }')

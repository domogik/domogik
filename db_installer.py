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
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from sqlalchemy import create_engine

from domogik.common import sql_schema
from domogik.common import database
from domogik.common.configloader import Loader

cfg = Loader('database')
config = cfg.load()
test_url = ''

try:
    db = dict(config[1])
    url = "%s:///" % db['db_type']
    if db['db_type'] == 'sqlite':
        url = "%s%s" % (url,db['db_path'])
    else:
        if db['db_port'] != '':
            url = "%s%s:%s@%s:%s/%s" % (url, db['db_user'], db['db_password'], \
              db['db_host'], db['db_port'], db['db_name'])
        else:
            url = "%s%s:%s@%s/%s" % (url, db['db_user'], db['db_password'], \
              db['db_host'], db['db_name'])
    test_url = '%s_test' % url
except:
    print "Some errors appears during connection to the database : Can't fetch informations from config file"

engine = create_engine(url)
engine_test = create_engine(test_url)

###
# Installer
###
sql_schema.metadata.create_all(engine)
# For unit tests
sql_schema.metadata.create_all(engine_test)

_db = database.DbHelper()

# Initialize default system configuration
_db.update_system_config()

# Create a default user account
_db.add_default_user_account()

# Create device technologie features for X10
device_technology = _db.add_device_technology(dt_id='x10', dt_name='X10', dt_description='')
device_type = _db.add_device_type(dty_name='Switch', dt_id=device_technology.id)
_db.add_actuator_feature(af_name='Switch', af_value='binary', dty_id=device_type.id, af_unit=None,
                        af_configurable_states='off, on',
                        af_return_confirmation=False)
device_type = _db.add_device_type(dty_name='Dimmer', dt_id=device_technology.id)
_db.add_actuator_feature(af_name='Switch', af_value='binary', dty_id=device_type.id, af_unit=None,
                        af_configurable_states='off, on',
                        af_return_confirmation=False)
_db.add_actuator_feature(af_name='Dimmer', af_value='range', dty_id=device_type.id, af_unit='%',
                        af_configurable_states='0, 100, 10',
                        af_return_confirmation=False)

# Create device technologie features for PLCBus
device_technology = _db.add_device_technology(dt_id='plcbus', dt_name='PLCBus', dt_description='')
device_type = _db.add_device_type(dty_name='Switch', dt_id=device_technology.id)
_db.add_actuator_feature(af_name='Switch', af_value='binary', dty_id=device_type.id, af_unit=None,
                        af_configurable_states='off, on',
                        af_return_confirmation=True)
device_type = _db.add_device_type(dty_name='Dimmer', dt_id=device_technology.id)
_db.add_actuator_feature(af_name='Switch', af_value='binary', dty_id=device_type.id, af_unit=None,
                        af_configurable_states='off, on',
                        af_return_confirmation=True)
_db.add_actuator_feature(af_name='Dimmer', af_value='range', dty_id=device_type.id, af_unit='%',
                        af_configurable_states='0, 100, 10',
                        af_return_confirmation=True)

# Create device technologie features for EIB/KNX
_db.add_device_technology(dt_id='eibknx', dt_name='EIB/KNX', dt_description='')
# Create device technologie features for 1wire
_db.add_device_technology(dt_id='1wire', dt_name='1-Wire', dt_description='')
# Create device technologie features for RFXCom
_db.add_device_technology(dt_id='rfxcom', dt_name='RFXCom', dt_description='')
# Create device technologie features for IR
_db.add_device_technology(dt_id='ir', dt_name='Infra Red', dt_description='')
# Create device technologie features for Service
_db.add_device_technology(dt_id='service', dt_name='Service', dt_description='Distributed services, water, gaz, electricity')
# Create device technologie features for RFID
_db.add_device_technology(dt_id='rfid', dt_name='RFID', dt_description='')

# Create device technologie features for Computer
device_technology = _db.add_device_technology(dt_id='computer', dt_name='Computer', dt_description='Computers monitoring and controling ')
device_type = _db.add_device_type(dty_name='WOL', dt_id=device_technology.id)
_db.add_actuator_feature(af_name='Activation', af_value='trigger', dty_id=device_type.id, af_unit=None,
                        af_configurable_states=None,
                        af_return_confirmation=False)

# Create device technologie features for MultiMedia
_db.add_device_technology(dt_id='multimedia', dt_name='MultiMedia', dt_description='Music, Video')
# Create device technologie features for Communication
_db.add_device_technology(dt_id='communication', dt_name='Communication', dt_description='Telephony, videophone, mails, messaging')

# Create device usages
_db.add_device_usage(du_name='Light', du_description='Lamp, light usage', du_default_options="{ binary: {state0:'Off', state1:'On'}, range: {step:'10', unit:'%'} }")
_db.add_device_usage(du_name='Socket', du_description='Socket usage', du_default_options="{ binary: {state0:'Off', state1:'On'}, range: {step:'10', unit:'%'} }")
_db.add_device_usage(du_name='Shutter', du_description='Shutter usage', du_default_options="{ binary: {state0:'Down', state1:'Up'}, range: {step:'10', unit:'%'} }")
_db.add_device_usage(du_name='Air conditioning', du_description='Air conditioning usage', du_default_options="{ binary: {state0:'Off', state1:'On'}, range: {step:'1', unit:'&deg;C'} }")
_db.add_device_usage(du_name='Ventilation', du_description='Ventilation usage', du_default_options="{ binary: {state0:'Off', state1:'On'}, range: {step:'10', unit:'%'} }")
_db.add_device_usage(du_name='Heating', du_description='Heating', du_default_options="{ binary: {state0:'Off', state1:'On'}, range: {step:'1', unit:'&deg;C'} }")
_db.add_device_usage(du_name='Appliance', du_description='Appliance usage', du_default_options="{ binary: {state0:'Off', state1:'On'} }")
_db.add_device_usage(du_name='Desktop Computer', du_description='Desktop computer usage', du_default_options="{ binary: {state0:'Off', state1:'On'} }")
_db.add_device_usage(du_name='Server', du_description='Server usage', du_default_options="{ binary: {state0:'Off', state1:'On'} }")
_db.add_device_usage(du_name='Phone', du_description='Phone usage', du_default_options="{ }")
_db.add_device_usage(du_name='TV', du_description='Television usage', du_default_options="{ binary: {state0:'Off', state1:'On'} }")

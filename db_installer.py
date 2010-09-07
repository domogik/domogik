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

import getopt, sys

from sqlalchemy import create_engine

from domogik.common import sql_schema
from domogik.common import database
from domogik.common.configloader import Loader


###
# Installer
###

def install(only_unit_tests=False):
    db = database.DbHelper()
    print "Using database", db.get_db_type()
    url = db.get_url_connection_string()

    # For unit tests
    test_url = '%s_test' % url
    engine_test = create_engine(test_url)
    sql_schema.metadata.create_all(engine_test)

    if only_unit_tests:
        return

    # Production database
    engine = create_engine(url)
    sql_schema.metadata.create_all(engine)

    # Initialize default system configuration
    db.update_system_config()

    # Create a default user account
    db.add_default_user_account()

    # Create device technologie features for X10

    device_technology = db.add_device_technology(dt_id='x10', dt_name='X10', dt_description='')
    device_type = db.add_device_type(dty_name='Switch', dt_id=device_technology.id)
    db.add_actuator_feature_model(af_name='Switch', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                              af_value_type='binary', af_stat_key='command')
    device_type = db.add_device_type(dty_name='Dimmer', dt_id=device_technology.id)
    db.add_actuator_feature_model(af_name='Switch', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                              af_value_type='binary', af_stat_key='command')
    db.add_actuator_feature_model(af_name='Reduce', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;dim&quot;,&quot;valueMin&quot;:1, &quot;valueMax&quot;:22}',
                              af_value_type='number', af_stat_key='level')
    db.add_actuator_feature_model(af_name='Increase', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;bright&quot;,&quot;valueMin&quot;:1, &quot;valueMax&quot;:22}',
                              af_value_type='number', af_stat_key='level')

    # Create device technologie features for PLCBus
    device_technology = db.add_device_technology(dt_id='plcbus', dt_name='PLCBus', dt_description='')
    device_type = db.add_device_type(dty_name='Switch', dt_id=device_technology.id)
    db.add_actuator_feature_model(af_name='Switch', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                              af_value_type='binary', af_stat_key='command', af_return_confirmation=True)
    device_type = db.add_device_type(dty_name='Dimmer', dt_id=device_technology.id)
    db.add_actuator_feature_model(af_name='Switch', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;&quot;,&quot;value0&quot;:&quot;off&quot;, &quot;value1&quot;:&quot;on&quot;}',
                              af_value_type='binary', af_stat_key='command', af_return_confirmation=True)
    db.add_actuator_feature_model(af_name='Dimmer', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;preset_dim&quot;,&quot;valueMin&quot;:0, &quot;valueMax&quot;:100}',
                              af_value_type='range', af_stat_key='level', af_return_confirmation=True)
    db.add_actuator_feature_model(af_name='Reduce', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;dim&quot;,&quot;valueMin&quot;:0, &quot;valueMax&quot;:22}',
                              af_value_type='number', af_stat_key='level', af_return_confirmation=True)
    db.add_actuator_feature_model(af_name='Increase', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;bright&quot;,&quot;valueMin&quot;:0, &quot;valueMax&quot;:22}',
                              af_value_type='number', af_stat_key='level', af_return_confirmation=True)

    # Create device technology features for EIB/KNX
    db.add_device_technology(dt_id='eibknx', dt_name='EIB/KNX', dt_description='')

    # Create device technology features for 1wire
    device_technology = db.add_device_technology(dt_id='onewire', dt_name='1-Wire', dt_description='')
    device_type = db.add_device_type(dty_name='Temperature', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='Temperature',
                            sf_device_type_id=device_type.id, sf_value_type='number',
                            sf_parameters='{&quot;unit&quot;:&quot;&deg;C&quot;}', sf_stat_key='temperature')
    device_type = db.add_device_type(dty_name='ID', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='ID',
                            sf_device_type_id=device_type.id, sf_value_type='boolean', sf_parameters='{}',
                            sf_stat_key='present')

    # Create device technology features for RFXCom
    db.add_device_technology(dt_id='rfxcom', dt_name='RFXCom', dt_description='')
    # Create device technology features for IR
    db.add_device_technology(dt_id='ir', dt_name='Infra Red', dt_description='')

    # Create device technology features for Service
    device_technology = db.add_device_technology(dt_id='service', dt_name='Service',
                                             dt_description='Distributed services, water, gas, electricity')
    device_type = db.add_device_type(dty_name='Teleinfo', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name=u'Intensité instantanée', sf_device_type_id=device_type.id, sf_value_type='number',
                            sf_parameters='{&quot;unit&quot;:&quot;A&quot;}', sf_stat_key='iinst')
    db.add_sensor_feature_model(sf_name='Heures creuses', sf_device_type_id=device_type.id, sf_value_type='number',
                            sf_parameters='{&quot;unit&quot;:&quot;Wh&quot;}', sf_stat_key='hchc')
    db.add_sensor_feature_model(sf_name=u'Intensité maximale', sf_device_type_id=device_type.id, sf_value_type='number',
                            sf_parameters='{&quot;unit&quot;:&quot;A&quot;}', sf_stat_key='imax')
    db.add_sensor_feature_model(sf_name=u'Période tarifaire', sf_device_type_id=device_type.id, sf_value_type='string',
                            sf_parameters=None, sf_stat_key='ptec')
    db.add_sensor_feature_model(sf_name='Puissance apparente', sf_device_type_id=device_type.id, sf_value_type='number',
                            sf_parameters='{&quot;unit&quot;:&quot;Va&quot;}', sf_stat_key='papp')
    db.add_sensor_feature_model(sf_name='Groupe horaire', sf_device_type_id=device_type.id, sf_value_type='string',
                            sf_parameters=None, sf_stat_key='hhphc')
    db.add_sensor_feature_model(sf_name='Heures pleines', sf_device_type_id=device_type.id, sf_value_type='number',
                            sf_parameters='{&quot;unit&quot;:&quot;Wh&quot;}', sf_stat_key='hchp')

    # Create device technology features for RFID
    device_technology = db.add_device_technology(dt_id='rfid', dt_name='RFID', dt_description='')
    device_type = db.add_device_type(dty_name='Mirror_Base', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='Activated', sf_device_type_id=device_type.id, sf_value_type='boolean',
                            sf_parameters='{}', sf_stat_key='activated')
    device_type = db.add_device_type(dty_name='Mirror_Tag', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='Present', sf_device_type_id=device_type.id, sf_value_type='boolean',
                            sf_parameters='{}', sf_stat_key='present')

    # Create device technology features for Relay Board
    device_technology = db.add_device_technology(dt_id='relayboard', dt_name='Relay Board',
                                             dt_description='Relay boards monitoring and controling ')
    device_type = db.add_device_type(dty_name='Relay', dt_id=device_technology.id)
    db.add_actuator_feature_model(af_name='Switch', af_device_type_id=device_type.id,
                              af_parameters='{&quot;output&quot;:&quot;&quot;,&quot;value0&quot;:&quot;low&quot;, &quot;value1&quot;:&quot;high&quot;}',
                              af_value_type='binary', af_stat_key='output',
                              af_return_confirmation=True)
    db.add_actuator_feature_model(af_name='Trigger', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;pulse&quot;}',af_value_type='trigger',
                              af_return_confirmation=True)
    device_type = db.add_device_type(dty_name='Digital_Input', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='Digital Input', sf_device_type_id=device_type.id, sf_value_type='boolean', sf_parameters='{}', sf_stat_key='input')
    device_type = db.add_device_type(dty_name='Analog_Input', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='Analog Input', sf_device_type_id=device_type.id, sf_value_type='boolean', sf_parameters='{}', sf_stat_key='voltage')
    device_type = db.add_device_type(dty_name='Counter', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='Counter', sf_device_type_id=device_type.id, sf_value_type='boolean', sf_parameters='{}', sf_stat_key='count')

    # Create device technology features for Computer
    device_technology = db.add_device_technology(dt_id='computer', dt_name='Computer',
                                             dt_description='Computers monitoring and controling ')
    device_type = db.add_device_type(dty_name='Control', dt_id=device_technology.id)
    db.add_actuator_feature_model(af_name='WOL', af_device_type_id=device_type.id,
                              af_parameters='{&quot;command&quot;:&quot;wol&quot;}',af_value_type='trigger',
                              af_return_confirmation=False)
    db.add_sensor_feature_model(sf_name='Ping', sf_device_type_id=device_type.id, sf_value_type='boolean',
                            sf_parameters='{}', sf_stat_key='ping')
    # Create device technologie features for MultiMedia
    device_technology = db.add_device_technology(dt_id='multimedia', dt_name='MultiMedia', dt_description='Music, Video')

    # Create device technologie features for communication
    device_technology = db.add_device_technology(dt_id='communication', dt_name='Communication',
                         dt_description='Telephony, videophone, mails, messaging')
    device_type = db.add_device_type(dty_name='Caller_Id', dt_id=device_technology.id)
    db.add_sensor_feature_model(sf_name='Caller Id', sf_device_type_id=device_type.id, sf_value_type='string', sf_parameters='{}', sf_stat_key='phone')

    # Create device usages
    db.add_device_usage(du_name='Light', du_description='Lamp, light usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Appliance', du_description='Appliance usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Shutter', du_description='Shutter usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Down&quot;, &quot;state1&quot;:&quot;Up&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Air conditioning', du_description='Air conditioning usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Ventilation', du_description='Ventilation usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Heating', du_description='Heating',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Desktop Computer', du_description='Desktop computer usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Server', du_description='Server usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Phone', du_description='Phone usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } } ')
    db.add_device_usage(du_name='TV', du_description='Television usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    db.add_device_usage(du_name='Water', du_description='Water service',
                    du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    db.add_device_usage(du_name='Gas', du_description='Gas service',
                    du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    db.add_device_usage(du_name='Electricity', du_description='Electricity service',
                    du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')

def usage():
    print "Usage : db_installer [-t, --test]"
    print "When using -t or --test only the database for unit tests is created"

if __name__ == "__main__":
    utests = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ht", ["help", "test"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-t', '--test'):
            utests = True
    if utests:
        print "Creating database for unit tests"
        install(True)
    else:
        print "Creating unit tests and production databases"
        install(False)

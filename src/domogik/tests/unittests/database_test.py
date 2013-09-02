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

Unit test class for the database API


@author: Marc SCHNEIDER
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import unittest
from unittest import TestCase
import time
import datetime

from sqlalchemy import create_engine

from domogik.common import sql_schema
from domogik.common.database import DbHelper, DbHelperException
from domogik.common.sql_schema import DeviceStats


def make_ts(year, month, day, hours=0, minutes=0, seconds=0):
    """Make a timestamp value"""
    return time.mktime((year, month, day, hours, minutes, seconds, 0, 0, 0))


class GenericTestCase(unittest.TestCase):
    """Main class for unit tests"""

    def has_item(self, item_list, item_name_list):
        """Check if a list of names are in a list (with objects having a 'name' attribute)

        @param item_list : a list of objects having a 'name' attribute
        @param item_name_list : a list of names
        @return True if all names are in the list

        """
        found = 0
        for item in item_list:
            if item.name in item_name_list:
                found = found + 1
        return found == len(item_name_list)

    def remove_all_devices(self):
        for device in db.list_devices():
            db.del_device(device.id)

    def remove_all_device_usages(self):
        for du in db.list_device_usages():
            db.del_device_usage(du.id, cascade_delete=True)

    def remove_all_device_types(self):
        for dty in db.list_device_types():
            db.del_device_type(dty.id, cascade_delete=True)

    def remove_all_device_feature_models(self):
        for af in db.list_actuator_feature_models():
            db.del_actuator_feature_model(af.id)
        for sf in db.list_sensor_feature_models():
            db.del_sensor_feature_model(sf.id)

    def remove_all_plugin_config(self):
        for plc in db.list_all_plugin_config():
            db.del_plugin_config(plc.id, plc.hostname)

    def remove_all_device_technologies(self):
        for dt in db.list_device_technologies():
            db.del_device_technology(dt.id, cascade_delete=True)

    def remove_all_device_stats(self):
        for device in db.list_devices():
            db.del_device_stats(device.id)

    def remove_all_persons(self):
        for person in db.list_persons():
            db.del_person(person.id)

    def remove_all_user_accounts(self):
        for user in db.list_user_accounts():
            db.del_user_account(user.id)

class DeviceUsageTestCase(GenericTestCase):
    """Test device usages"""

    def setUp(self):
        self.remove_all_device_usages()

    def tearDown(self):
        self.remove_all_device_usages()

    def test_empty_list(self):
        assert len(db.list_device_usages()) == 0

    def test_add(self):
        du1 = db.add_device_usage(du_id='du1_id', du_name='du1', du_description='desc1',
                                  du_default_options='def opt1')
        print(du1)
        assert du1.name == 'du1'
        assert du1.description == 'desc1'
        assert du1.default_options == 'def opt1'
        du2 = db.add_device_usage(du_id='du2_id', du_name='du2')
        assert len(db.list_device_usages()) == 2
        assert self.has_item(db.list_device_usages(), ['du1', 'du2'])

    def test_update(self):
        du = db.add_device_usage(du_id='du1_id', du_name='du1')
        du_u = db.update_device_usage(du_id=du.id, du_name='du2', du_description='description 2',
                                      du_default_options='def opt2')
        assert du_u.name == 'du2'
        assert du_u.description == 'description 2'
        assert du_u.default_options == 'def opt2'
        du_u = db.update_device_usage(du_id=du.id, du_description='', du_default_options='')
        assert du_u.description is None
        assert du_u.default_options is None

    def test_list_and_get(self):
        du1 = db.add_device_usage(du_id='du1_id', du_name='du1')
        assert db.get_device_usage_by_name('Du1').name == 'du1'

    def test_del(self):
        du1 = db.add_device_usage(du_id='du1_id', du_name='du1')
        du2 = db.add_device_usage(du_id='du2_id', du_name='du2')
        du2_id = du2.id
        du_del = db.del_device_usage(du2.id)
        assert self.has_item(db.list_device_usages(), ['du1'])
        assert not self.has_item(db.list_device_usages(), ['du2'])
        assert du_del.id == du2_id
        try:
            db.del_device_usage(12345678910)
            TestCase.fail(self, "Device usage does not exist, an exception should have been raised")
        except DbHelperException:
            pass

class DeviceTypeTestCase(GenericTestCase):
    """Test device types"""

    def setUp(self):
        self.remove_all_device_types()
        self.remove_all_device_technologies()

    def tearDown(self):
        self.remove_all_device_types()

    def test_empty_list(self):
        assert len(db.list_device_types()) == 0

    def test_add(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        try:
            db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=u'99999999999')
            TestCase.fail(self, "An exception should have been raised : device techno id does not exist")
        except DbHelperException:
            pass
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        print(dty1)
        assert dty1.name == 'Switch'
        assert dty1.description == 'desc1'
        assert dty1.device_technology_id == dt1.id
        dty2 = db.add_device_type(dty_id='x10.dimmer', dty_name='Dimmer', dty_description='desc2', dt_id=dt1.id)
        assert len(db.list_device_types()) == 2
        assert self.has_item(db.list_device_types(), ['Switch', 'Dimmer'])

    def test_update(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = db.add_device_technology('plcbus', 'PLCBus', 'desc dt2')
        dty = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        try:
            db.update_device_type(dty_id=dty.id, dty_name='x10 Dimmer', dt_id=u'99999999999')
            TestCase.fail(self, "An exception should have been raised : device techno id does not exist")
        except DbHelperException:
            pass
        dty_u = db.update_device_type(dty_id=dty.id, dty_name='x10 Dimmer', dt_id=dt2.id, dty_description='desc2')
        assert dty_u.name == 'x10 Dimmer'
        assert dty_u.description == 'desc2'
        assert dty_u.device_technology_id == dt2.id

    def test_list_and_get(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        assert db.get_device_type_by_id('x10.switch').name == 'Switch'
        assert db.get_device_type_by_name('Switch').name == 'Switch'

    def test_del(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dt_id=dt1.id)
        dty2 = db.add_device_type(dty_id='x10.dimmer', dty_name='Dimmer', dt_id=dt1.id)
        dty2_id = dty2.id
        dty_del = db.del_device_type(dty2.id)
        assert self.has_item(db.list_device_types(), ['Switch'])
        assert not self.has_item(db.list_device_usages(), ['x10 Dimmer'])
        assert dty_del.id == dty2_id
        try:
            db.del_device_type(12345678910)
            TestCase.fail(self, "Device type does not exist, an exception should have been raised")
        except DbHelperException:
            pass

class DeviceFeatureModelTestCase(GenericTestCase):
    """Test device feature models"""

    def setUp(self):
        self.remove_all_device_feature_models()
        self.remove_all_device_technologies()

    def tearDown(self):
        self.remove_all_device_feature_models()
        self.remove_all_device_technologies()

    def test_empty_list(self):
        assert len(db.list_device_features()) == 0

    def test_add_get_list(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        dty2 = db.add_device_type(dty_id='x10.dimmer', dty_name='Dimmer', dty_description='desc2', dt_id=dt1.id)
        dty3 = db.add_device_type(dty_id='1wire.temperature', dty_name='Temperature', dty_description='desc3',
                                  dt_id=dt2.id)
        afm1 = db.add_actuator_feature_model(af_id='x10.switch.switch', af_name='Switch', af_device_type_id=dty1.id,
                                             af_parameters='myparams1',
                                             af_value_type='binary', af_return_confirmation=True)
        print(afm1)
        assert afm1.name == 'Switch'
        assert afm1.device_type_id == dty1.id
        assert afm1.parameters == 'myparams1'
        assert afm1.value_type == 'binary'
        assert afm1.return_confirmation
        assert db.get_device_feature_model_by_id(afm1.id).name == 'Switch'
        afm2 = db.add_actuator_feature_model(af_id='x10.dimmer.dimmer', af_name='Dimmer', af_device_type_id=dty2.id,
                                             af_parameters='myparams2',
                                             af_value_type='number', af_return_confirmation=True)
        sfm1 = db.add_sensor_feature_model(sf_id='1wire.temperature.thermometer', sf_name='Thermometer',
                                           sf_device_type_id=dty3.id,
                                           sf_parameters='myparams3', sf_value_type='number')
        print(sfm1)
        assert sfm1.name == 'Thermometer'
        assert sfm1.device_type_id == dty3.id
        assert sfm1.parameters == 'myparams3'
        assert sfm1.value_type == 'number'
        assert len(db.list_device_feature_models()) == 3
        assert self.has_item(db.list_device_feature_models(), ['Switch', 'Dimmer', 'Thermometer'])
        assert len(db.list_actuator_feature_models()) == 2
        assert db.get_actuator_feature_model_by_id(afm2.id).name == 'Dimmer'
        assert len(db.list_sensor_feature_models()) == 1
        assert db.get_sensor_feature_model_by_id(sfm1.id).name == 'Thermometer'
        assert len(db.list_device_feature_models_by_device_type_id(dty1.id)) == 1
        assert len(db.list_device_feature_models_by_device_type_id(dty3.id)) == 1

    def test_update(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        dty2 = db.add_device_type(dty_id='1wire.Temperature', dty_name='Temp.', dty_description='desc3', dt_id=dt2.id)
        af1 = db.add_actuator_feature_model(af_id='x10.switch.switch', af_name='Switch', af_device_type_id=dty1.id,
                                            af_value_type='number', af_parameters='myparams1')
        af1_u = db.update_actuator_feature_model(af_id=af1.id, af_name='Big switch',
                                                 af_parameters='myparams_u', af_return_confirmation=True)
        assert af1_u.name == 'Big switch'
        assert af1_u.parameters == 'myparams_u'
        assert af1_u.value_type == 'number'
        assert af1_u.return_confirmation
        sf1 = db.add_sensor_feature_model(sf_id='1wire.temperature.thermometer', sf_name='Thermometer',
                                          sf_device_type_id=dty2.id,
                                          sf_parameters='myparams2', sf_value_type='number')
        sf1_u = db.update_sensor_feature_model(sf_id=sf1.id, sf_value_type='string')
        assert sf1_u.value_type == 'string'

    def test_del(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        dty2 = db.add_device_type(dty_id='x10.dimmer', dty_name='Dimmer', dty_description='desc2', dt_id=dt1.id)
        dty3 = db.add_device_type(dty_id='1wire.temperature', dty_name='Temp.', dty_description='desc3', dt_id=dt2.id)
        af1 = db.add_actuator_feature_model(af_id='x10.switch.switch', af_name='Switch', af_device_type_id=dty1.id,
                                            af_parameters='myparams1',
                                            af_value_type='binary', af_return_confirmation=True)
        af2 = db.add_actuator_feature_model(af_id='x10.dimmer.dimmer', af_name='Dimmer', af_device_type_id=dty2.id,
                                            af_parameters='myparams2',
                                            af_value_type='number', af_return_confirmation=True)
        sf1 = db.add_sensor_feature_model(sf_id='1wire.temperature.thermometer', sf_name='Thermometer',
                                          sf_device_type_id=dty3.id, sf_parameters='myparams3', sf_value_type='number')
        af_d = db.del_actuator_feature_model(af1.id)
        assert af_d.id == af1.id
        assert len(db.list_device_feature_models()) == 2
        assert len(db.list_actuator_feature_models()) == 1
        assert len(db.list_sensor_feature_models()) == 1
        af_d = db.del_actuator_feature_model(af2.id)
        assert len(db.list_actuator_feature_models()) == 0
        sf_d = db.del_sensor_feature_model(sf1.id)
        assert len(db.list_sensor_feature_models()) == 0

class DeviceTechnologyTestCase(GenericTestCase):
    """Test device technologies"""

    def setUp(self):
        self.remove_all_device_technologies()

    def tearDown(self):
        self.remove_all_device_technologies()

    def test_empty_list(self):
        assert len(db.list_device_technologies()) == 0

    def test_add(self):
        dt1 = db.add_device_technology('1wire', '1-Wire', 'desc dt1')
        print(dt1)
        assert dt1.id == '1wire'
        assert dt1.name == '1-Wire'
        assert dt1.description == 'desc dt1'
        dt2 = db.add_device_technology('x10', 'x10', 'desc dt2')
        dt3 = db.add_device_technology('plcbus', 'PLCBus', 'desc dt3')
        assert len(db.list_device_technologies()) == 3
        assert self.has_item(db.list_device_technologies(), ['x10', '1-Wire', 'PLCBus'])

    def test_update(self):
        dt = db.add_device_technology('x10', 'x10', 'desc dt1')
        dt_u = db.update_device_technology(dt.id, dt_description='desc dt2')
        assert dt_u.description == 'desc dt2'

    def test_list_and_get(self):
        dt2 = db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        assert db.get_device_technology_by_id('1wire').id == '1wire'

    def test_del(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dt_del = dt2
        dt2_id = dt2.id
        dt3 = db.add_device_technology('plcbus', 'PLCBus', 'desc dt3')
        db.del_device_technology(dt2.id)
        assert self.has_item(db.list_device_technologies(), ['x10', 'PLCBus'])
        assert not self.has_item(db.list_device_technologies(), ['1-Wire'])
        assert dt_del.id == dt2_id
        try:
            db.del_device_technology(12345678910)
            TestCase.fail(self, "Device technology does not exist, an exception should have been raised")
        except DbHelperException:
            pass

class PluginConfigTestCase(GenericTestCase):
    """Test plugin configuration"""

    def setUp(self):
        self.remove_all_plugin_config()

    def tearDown(self):
        self.remove_all_plugin_config()

    def test_empty_list(self):
        assert len(db.list_all_plugin_config()) == 0

    def test_add_get_list(self):
        pc1_1 = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.1', pl_key='key1_1', pl_value='val1_1')
        print(pc1_1)
        assert pc1_1.id == 'x10'
        assert pc1_1.key == 'key1_1'
        assert pc1_1.value == 'val1_1'
        pc1_2 = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.1', pl_key='key1_2', pl_value='val1_2')
        pc3_1 = db.set_plugin_config(pl_id='plcbus', pl_hostname='192.168.0.1', pl_key='key3_1',
                                     pl_value='val3_1')
        pc3_2 = db.set_plugin_config(pl_id='plcbus', pl_hostname='192.168.0.1', pl_key='key3_2',
                                     pl_value='val3_2')
        pc3_3 = db.set_plugin_config(pl_id='plcbus', pl_hostname='192.168.0.1', pl_key='key3_3',
                                     pl_value='val3_3')
        pc4_1 = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.2', pl_key='key4_1', pl_value='val4_1')
        assert len(db.list_all_plugin_config()) == 6
        assert len(db.list_plugin_config('x10', '192.168.0.1')) == 2
        assert len(db.list_plugin_config('plcbus', '192.168.0.1')) == 3
        assert len(db.list_plugin_config('x10', '192.168.0.2')) == 1
        assert len(db.list_plugin_config('plcbus', '192.168.0.2')) == 0
        assert db.get_plugin_config('x10', '192.168.0.1', 'key1_2').value == 'val1_2'

    def test_update(self):
        plc = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.1', pl_key='key1', pl_value='val1')
        plc_u = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.1', pl_key='key1', pl_value='val11')
        assert plc_u.key == 'key1'
        assert plc_u.value == 'val11'
        assert db.get_plugin_config('x10', '192.168.0.1', 'key1').value == 'val11'

    def test_del(self):
        plc1_1 = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.1', pl_key='key1_1', pl_value='val1_1')
        plc1_2 = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.1', pl_key='key1_2', pl_value='val1_2')
        plc3_1 = db.set_plugin_config(pl_id='plcbus', pl_hostname='192.168.0.1', pl_key='key3_1',
                                      pl_value='val3_1')
        plc3_2 = db.set_plugin_config(pl_id='plcbus', pl_hostname='192.168.0.1', pl_key='key3_2',
                                      pl_value='val3_2')
        plc3_3 = db.set_plugin_config(pl_id='plcbus', pl_hostname='192.168.0.1', pl_key='key3_3',
                                      pl_value='val3_3')
        pc4_1 = db.set_plugin_config(pl_id='x10', pl_hostname='192.168.0.2', pl_key='key4_1', pl_value='val4_1')
        assert len(db.del_plugin_config('x10', '192.168.0.1')) == 2
        assert len(db.list_plugin_config('x10', '192.168.0.1')) == 0
        assert len(db.list_plugin_config('plcbus', '192.168.0.1')) == 3
        plugin_config = db.del_plugin_config_key('plcbus', '192.168.0.1', 'key3_2')
        assert plugin_config.key == 'key3_2'
        assert db.del_plugin_config_key('plcbus', '192.168.0.1', 'foo') is None
        assert len(db.list_plugin_config('plcbus', '192.168.0.1')) == 2
        assert len(db.list_plugin_config('x10', '192.168.0.2')) == 1


class DeviceTestCase(GenericTestCase):
    """Test device"""

    def setUp(self):
        self.remove_all_device_usages()
        self.remove_all_devices()
        self.remove_all_device_technologies()

    def tearDown(self):
        self.remove_all_device_usages()
        self.remove_all_devices()
        self.remove_all_device_technologies()

    def test_empty_list(self):
        assert len(db.list_devices()) == 0

    def test_add(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        du1 = db.add_device_usage('du1_id', 'du1')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        try:
            db.add_device(d_name='device1', d_address = 'A1', d_type_id = u'9999999999', d_usage_id = du1.id)
            TestCase.fail(self, "Device type does not exist, an exception should have been raised")
            db.add_device(d_name='device1', d_address = 'A1', d_type_id = dty1.id, d_usage_id = u'9999999999999')
            TestCase.fail(self, "Device usage does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        device1 = db.add_device(d_name='device1', d_address='A1',
                                d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        assert device1.name == 'device1' and device1.description == 'desc1'
        print(device1)
        assert len(db.list_devices()) == 1
        device2 = db.add_device(d_name='device2', d_address='A2',
                    d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        assert len(db.list_devices()) == 2

    def test_list_and_get(self):
        dt1 = db.add_device_technology('x10', 'x10', 'x10 device type')
        dt2 = db.add_device_technology('plcbus', 'PLCBus', 'PLCBus device type')
        du1 = db.add_device_usage('appliance', 'Appliance')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dt_id=dt1.id,
                                  dty_description='My beautiful switch')
        dty2 = db.add_device_type(dty_id='plcbus.switch', dty_name='Switch', dt_id=dt2.id,
                                  dty_description='Another beautiful switch')
        device1 = db.add_device(d_name='Toaster', d_address='A1',
                                d_type_id=dty1.id, d_usage_id=du1.id, d_description='My new toaster')
        device2 = db.add_device(d_name='Washing machine', d_address='A1',
                                d_type_id=dty2.id, d_usage_id=du1.id, d_description='Laden')
        device3 = db.add_device(d_name='Mixer', d_address='A2',
                                d_type_id=dty2.id, d_usage_id=du1.id, d_description='Moulinex')
        search_dev1 = db.get_device_by_technology_and_address(dt1.id, 'A1')
        assert search_dev1.name == 'Toaster'
        search_dev2 = db.get_device_by_technology_and_address(dt1.id, 'A2')
        assert search_dev2 == None

    def test_update(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = db.add_device_usage('du1_id', 'du1')
        device1 = db.add_device(d_name='device1', d_address='A1',
                                d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        device_id = device1.id
        try:
            db.update_device(d_id=device1.id, d_usage_id=u'9999999999999')
            TestCase.fail(self, "Device usage does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        device1 = db.update_device(d_id=device1.id, d_description='desc2', d_reference='A1')
        device1 = db.get_device(device_id)
        assert device1.description == 'desc2'
        assert device1.reference == 'A1'
        assert device1.device_usage_id == du1.id
        du2 = db.add_device_usage('du2_id', 'du2')
        device1 = db.update_device(d_id=device1.id, d_reference='', d_usage_id=du2.id)
        assert device1.reference == None
        assert device1.device_usage_id == du2.id

    def test_del(self):
        dt1 = db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = db.add_device_usage('du1_id', 'du1')
        du2 = db.add_device_usage('du2_id', 'du2')
        device1 = db.add_device(d_name='device1', d_address='A1',
                                d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        device2 = db.add_device(d_name='device2', d_address='A2',
                                d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')

        db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val2', 1, device2.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val1', 2, device2.id)
        assert len(db.list_device_stats(device2.id)) == 2

        device3 = db.add_device(d_name='device3', d_address='A3', d_type_id=dty1.id, d_usage_id=du1.id)
        device_del = device2
        device2_id = device2.id
        db.del_device(device2.id)
        # Check cascade deletion
        assert len(db.list_device_stats(device2.id)) == 0
        assert len(db.list_devices()) == 2
        for dev in db.list_devices():
            assert dev.address in ('A1', 'A3')
        assert device_del.id == device2.id
        try:
            db.del_device(12345678910)
            TestCase.fail(self, "Device does not exist, an exception should have been raised")
        except DbHelperException:
            pass

class DeviceStatsTestCase(GenericTestCase):
    """Test device stats"""

    def setUp(self):
        self.remove_all_device_usages()
        self.remove_all_device_technologies()
        self.remove_all_device_stats()

    def tearDown(self):
        self.remove_all_device_usages()
        self.remove_all_device_technologies()
        self.remove_all_device_stats()

    def test_empty_list(self):
        assert len(db.list_device_stats()) == 0
        assert db.device_has_stats() == False


    def __has_stat_values(self, device_stats_values, expected_values):
        if len(device_stats_values) != len(expected_values): return False
        for item in device_stats_values:
            if item.value not in expected_values: return False
        return True

    def test_add_list_get(self):
        dt1 = db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = db.add_device_usage('lighting', 'Lighting')

        # Add device stats
        device1 = db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)
        device2 = db.add_device(d_name='device2', d_address='A2', d_type_id=dty1.id, d_usage_id=du1.id)
        ds1 = db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val1', 0, device1.id)
        print(ds1)
        assert ds1.skey == 'val1' and ds1.value == '0'
        assert ds1.timestamp == make_ts(2010, 04, 9, 12, 0)
        ds2 = db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val_char', 'plop', device1.id)
        assert ds2.skey == 'val_char' and ds2.value == 'plop'

        # Add for device1
        db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val2', 1, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val1', 2, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val2', 3, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 2), 'val1', 4, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 2), 'val2', 5, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 3), 'val1', 6, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 3), 'val2', 7, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 4), 'val1', 8, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 4), 'val2', 9, device1.id)

        # Add for device2
        db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val1', 100, device2.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val2', 200, device2.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val1', 300, device2.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val2', 400, device2.id)

        assert db.get_last_stat_of_device( device1.id, 'val1').value == '8'
        assert db.get_last_stat_of_device( device1.id, 'val2').value == '9'

        stats_l = db.list_last_n_stats_of_device(device1.id,'val1', 3)
        assert len(stats_l) == 3
        assert stats_l[0].value == '4' and stats_l[1].value == '6' and stats_l[2].value == '8'

        stats_l = db.list_stats_of_device_between_by_key( device1.id, 'val1', make_ts(2010, 04, 9, 12, 2),
                                                         make_ts(2010, 04, 9, 12, 4))
        assert len(stats_l) == 3
        assert stats_l[0].value == '4' and stats_l[1].value == '6' and stats_l[2].value == '8'
        stats_l = db.list_stats_of_device_between_by_key(device1.id, 'val1',
                                                         make_ts(2010, 04, 9, 12, 3))
        assert len(stats_l) == 2
        assert stats_l[0].value == '6' and stats_l[1].value == '8'
        stats_l = db.list_stats_of_device_between_by_key(device1.id, 'val1', 
                                                         end_date_ts=make_ts(2010, 04, 9, 12, 2))
        assert len(stats_l) == 3
        assert stats_l[0].get_date_as_timestamp() == 1270810800.0

        # Verify for unified list_device_stats
        assert len(db.list_device_stats()) == 15
        assert len(db.list_device_stats(None, None)) == 15
        assert len(db.list_device_stats(device1.id)) == 11
        assert len(db.list_device_stats(device2.id)) == 4
        assert len(db.list_device_stats(device1.id,'val1')) == 5
        assert len(db.list_device_stats(device1.id,'val2')) == 5
        assert len(db.list_device_stats(device2.id,'val1')) == 2
        assert len(db.list_device_stats(device2.id,'val2')) == 2
        assert len(db.list_device_stats(None,'val1')) == 7
        assert len(db.list_device_stats(None,'val2')) == 7

        assert db.device_has_stats() == True
        assert db.device_has_stats(None, None) == True
        assert db.device_has_stats(device1.id,'val1') == True
        assert db.device_has_stats(device1.id,'val3') == False

    def test_add_with_hist_size(self):
        dt1 = db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = db.add_device_usage('lighting', 'Lighting')
        device1 = db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val2', 1000, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val1', 1, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 2), 'val1', 2, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 3), 'val1', 3, device1.id)
        db.add_device_stat(make_ts(2010, 04, 9, 12, 4), 'val1', 4, device1.id)
        assert len(db.list_device_stats(device1.id)) == 5
        assert len(db.list_device_stats(device1.id,'val1' )) == 4
        db.add_device_stat(make_ts(2010, 04, 9, 12, 5), 'val1', 5, device1.id, 2)
        stat_list = db.list_device_stats( device1.id,'val1')
        assert len(stat_list) == 2
        for stat in stat_list:
            assert stat.value in ['4', '5']
        assert len(db.list_device_stats(device1.id)) == 3

    def test_filter(self):
        dt1 = db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = db.add_device_usage('lighting', 'Lighting')
        device1 = db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)
        device2 = db.add_device(d_name='device2', d_address = "A2", d_type_id = dty1.id, d_usage_id = du1.id)

        # Minutes
        start_p = make_ts(2010, 2, 21, 15, 48, 0)
        end_p = make_ts(2010, 2, 21, 16, 8, 0)
        insert_step = 10
        for i in range(0, int(end_p - start_p), insert_step):
            db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i), timestamp=start_p + i,
                            skey=u'valm', value=(i/insert_step), device_id=device1.id)
            )
            db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i), timestamp=start_p + i,
                            skey=u'valm2', value=(i/insert_step+200), device_id=device1.id)
            )
            db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i), timestamp=start_p + i,
                            skey=u'valm', value=(i/insert_step+100), device_id=device2.id)
            )
        db._DbHelper__session.commit()

        expected_results = {
            'avg': [(2010, 2, 7, 21, 15, 57, 56.5), (2010, 2, 7, 21, 15, 58, 62.5), (2010, 2, 7, 21, 15, 59, 68.5),
                    (2010, 2, 7, 21, 16, 0, 74.5), (2010, 2, 7, 21, 16, 1, 80.5), (2010, 2, 7, 21, 16, 2, 86.5)],
            'min': [(2010, 2, 7, 21, 15, 57, 54.0), (2010, 2, 7, 21, 15, 58, 60.0), (2010, 2, 7, 21, 15, 59, 66.0),
                    (2010, 2, 7, 21, 16, 0, 72.0), (2010, 2, 7, 21, 16, 1, 78.0), (2010, 2, 7, 21, 16, 2, 84.0)],
            'max': [(2010, 2, 7, 21, 15, 57, 59.0), (2010, 2, 7, 21, 15, 58, 65.0), (2010, 2, 7, 21, 15, 59, 71.0),
                    (2010, 2, 7, 21, 16, 0, 77.0), (2010, 2, 7, 21, 16, 1, 83.0), (2010, 2, 7, 21, 16, 2, 89.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results = db.filter_stats_of_device_by_key(ds_device_id=device1.id,
                                                       ds_key='valm', 
                                                       start_date_ts=make_ts(2010, 2, 21, 15, 57, 0),
                                                       end_date_ts=make_ts(2010, 2, 21, 16, 3, 0),
                                                       step_used='minute', function_used=func)
            assert results['values'] == expected_results[func]
            # These are computed values for the whole period (min, max, avg)
            assert results['global_values']['min'] == 54 and results['global_values']['max'] == 89\
                                                         and results['global_values']['avg'] == 71.5

        start_p = make_ts(2010, 6, 21, 15, 48, 0)
        end_p = make_ts(2010, 6, 25, 21, 48, 0)
        insert_step = 2500
        for i in range(0, int(end_p - start_p), insert_step):
            db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i), timestamp=start_p + i,
                            skey=u'valh', value=i/insert_step, device_id=device1.id)
            )
        db._DbHelper__session.commit()

        # Hours
        expected_results = {
            'avg': [(2010, 6, 25, 22, 19, 38.5), (2010, 6, 25, 22, 20, 40.0), (2010, 6, 25, 22, 21, 41.5),
                    (2010, 6, 25, 22, 22, 43.0), (2010, 6, 25, 22, 23, 44.0), (2010, 6, 25, 23, 0, 45.5),
                    (2010, 6, 25, 23, 1, 47.0), (2010, 6, 25, 23, 2, 48.0)],
            'min': [(2010, 6, 25, 22, 19, 38.0), (2010, 6, 25, 22, 20, 40.0), (2010, 6, 25, 22, 21, 41.0),
                    (2010, 6, 25, 22, 22, 43.0), (2010, 6, 25, 22, 23, 44.0), (2010, 6, 25, 23, 0, 45.0),
                    (2010, 6, 25, 23, 1, 47.0), (2010, 6, 25, 23, 2, 48.0)],
            'max': [(2010, 6, 25, 22, 19, 39.0), (2010, 6, 25, 22, 20, 40.0), (2010, 6, 25, 22, 21, 42.0),
                    (2010, 6, 25, 22, 22, 43.0), (2010, 6, 25, 22, 23, 44.0), (2010, 6, 25, 23, 0, 46.0),
                    (2010, 6, 25, 23, 1, 47.0), (2010, 6, 25, 23, 2, 48.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results = db.filter_stats_of_device_by_key(ds_device_id=device1.id,
                                                       ds_key='valh', 
                                                       start_date_ts=make_ts(2010, 6, 22, 17, 48, 0),
                                                       end_date_ts=make_ts(2010, 6, 23, 1, 48, 0),
                                                       step_used='hour', function_used=func)
            assert results['values'] == expected_results[func]
            # These are computed values for the whole period (min, max, avg)
            assert results['global_values']['min'] == 38 and results['global_values']['max'] == 48\
                                                         and results['global_values']['avg'] == 43

        # Days
        start_p = make_ts(2010, 6, 21, 15, 48, 0)
        end_p = make_ts(2010, 6, 28, 21, 48, 0)
        insert_step = 28000
        for i in range(0, int(end_p - start_p), insert_step):
            db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i), timestamp=start_p + i,
                            skey=u'vald', value=i/insert_step, device_id=device1.id)
            )
        db._DbHelper__session.commit()

        expected_results = {
            'avg': [(2010, 6, 25, 22, 4.0), (2010, 6, 25, 23, 6.0), (2010, 6, 25, 24, 9.0), (2010, 6, 25, 25, 12.0),
                    (2010, 6, 25, 26, 15.0), (2010, 6, 25, 27, 18.0), (2010, 6, 26, 28, 21.0)],
            'min': [(2010, 6, 25, 22, 4.0), (2010, 6, 25, 23, 5.0), (2010, 6, 25, 24, 8.0), (2010, 6, 25, 25, 11.0),
                    (2010, 6, 25, 26, 14.0), (2010, 6, 25, 27, 17.0), (2010, 6, 26, 28, 20.0)],
            'max': [(2010, 6, 25, 22, 4.0), (2010, 6, 25, 23, 7.0), (2010, 6, 25, 24, 10.0), (2010, 6, 25, 25, 13.0),
                    (2010, 6, 25, 26, 16.0), (2010, 6, 25, 27, 19.0), (2010, 6, 26, 28, 22.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results = db.filter_stats_of_device_by_key(ds_device_id=device1.id,
                                                       ds_key='vald', 
                                                       start_date_ts=make_ts(2010, 6, 22, 15, 48, 0),
                                                       end_date_ts=make_ts(2010, 7, 26, 15, 48, 0),
                                                       step_used='day', function_used=func)
            assert results['values'] == expected_results[func]
            # These are computed values for the whole period (min, max, avg)
            assert results['global_values']['min'] == 4 and results['global_values']['max'] == 22\
                                                        and results['global_values']['avg'] == 13

        # Weeks
        start_p = make_ts(2010, 7, 11, 15, 48, 0)
        end_p = make_ts(2010, 8, 28, 21, 48, 0)
        insert_step = 12 * 3600
        for i in range(0, int(end_p - start_p), insert_step):
            db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i), timestamp=start_p + i,
                            skey=u'valw', value=i/insert_step, device_id=device1.id)
            )
        db._DbHelper__session.commit()

        expected_results = {
            'avg': [(2010, 29, 25.0), (2010, 30, 35.5), (2010, 31, 49.5), (2010, 32, 63.5),
                    (2010, 33, 77.5), (2010, 34, 88.0)],
            'min': [(2010, 29, 22.0), (2010, 30, 29.0), (2010, 31, 43.0), (2010, 32, 57.0),
                    (2010, 33, 71.0), (2010, 34, 85.0)],
            'max': [(2010, 29, 28.0), (2010, 30, 42.0), (2010, 31, 56.0), (2010, 32, 70.0),
                    (2010, 33, 84.0), (2010, 34, 91.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results = db.filter_stats_of_device_by_key(ds_key='valw', 
                                                       ds_device_id=device1.id,
                                                       start_date_ts=make_ts(2010, 7, 22, 15, 48, 0),
                                                       end_date_ts=make_ts(2010, 8, 26, 15, 48, 0),
                                                       step_used='week', function_used=func)
            assert results['values'] == expected_results[func]
            # These are computed values for the whole period (min, max, avg)
            assert results['global_values']['min'] == 22 and results['global_values']['max'] == 91\
                                                         and results['global_values']['avg'] == 56.5

        # Months
        start_p = make_ts(2010, 6, 21, 15, 48, 0)
        now = datetime.datetime.now()
        end_p = make_ts(now.year, now.month, now.day, 15, 48, 0)
        insert_step = 3600 * 24 * 15
        for i in range(0, int(end_p - start_p), insert_step):
            db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i), timestamp=start_p + i,
                            skey=u'valmy', value=i/insert_step, device_id=device1.id)
            )
        db._DbHelper__session.commit()
        expected_results = {
            'avg': [(2010, 7, 1.5), (2010, 8, 3.5), (2010, 9, 5.5), (2010, 10, 7.5), (2010, 11, 9.5), (2010, 12, 11.5),
                    (2011, 1, 13.5), (2011, 2, 15.5), (2011, 3, 17.5), (2011, 4, 19.5), (2011, 5, 21.5),
                    (2011, 6, 23.5), (2011, 7, 25.5)],
            'min': [(2010, 7, 1.0), (2010, 8, 3.0), (2010, 9, 5.0), (2010, 10, 7.0), (2010, 11, 9.0), (2010, 12, 11.0),
                    (2011, 1, 13.0), (2011, 2, 15.0), (2011, 3, 17.0), (2011, 4, 19.0), (2011, 5, 21.0),
                    (2011, 6, 23.0), (2011, 7, 25.0)],
            'max': [(2010, 7, 2.0), (2010, 8, 4.0), (2010, 9, 6.0), (2010, 10, 8.0), (2010, 11, 10.0), (2010, 12, 12.0),
                    (2011, 1, 14.0), (2011, 2, 16.0), (2011, 3, 18.0), (2011, 4, 20.0), (2011, 5, 22.0),
                    (2011, 6, 24.0), (2011, 7, 26.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results =  db.filter_stats_of_device_by_key(ds_device_id=device1.id,
                                                        ds_key='valmy', 
                                                        start_date_ts=make_ts(2010, 6, 25, 15, 48, 0),
                                                        end_date_ts=make_ts(2011, 7, 29, 15, 48, 0),
                                                        step_used='month', function_used=func)
            assert results['values'] == expected_results[func]
            # These are computed values for the whole period (min, max, avg)
            assert results['global_values']['min'] == 1 and results['global_values']['max'] == 26\
                                                        and results['global_values']['avg'] == 13.5

        # Test with no end date
        results =  db.filter_stats_of_device_by_key(ds_device_id=device1.id, ds_key='valmy', 
                                                    start_date_ts=make_ts(2010, 6, 21, 15, 48, 0),
                                                    end_date_ts=None, step_used='month', function_used='avg')
        ym_list = [(r[0], r[1]) for r in results['values']]
        assert (2010, 6) in ym_list
        # We use the previous month because it may happen that no data have been inserted for the current month
        # Especially when we are at the beginning of the month
        if now.month == 1:
            assert (now.year - 1, 12) in ym_list
        else:
            assert (now.year, int(now.month - 1)) in ym_list

        # Years
        expected_results = {
            'avg': [(2010, 6.0), (2011, 25.0), (2012, 43.0)],
            'min': [(2010, 0.0), (2011, 13.0), (2012, 38.0)],
            'max': [(2010, 12.0), (2011, 37.0), (2012, 48.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results =  db.filter_stats_of_device_by_key(ds_device_id=device1.id,
                                                        ds_key='valmy', 
                                                        start_date_ts=make_ts(2010, 6, 21, 15, 48, 0),
                                                        end_date_ts=make_ts(2012, 6, 21, 15, 48, 0),
                                                        step_used='year', function_used=func)
            assert results['values'] == expected_results[func]
            # These are computed values for the whole period (min, max, avg)
            assert results['global_values']['min'] == 0 and results['global_values']['max'] == 48\
                                                        and results['global_values']['avg'] == 24

    def test_del(self):
        dt1 = db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = db.add_device_type(dty_id='x10.switch', dty_name='Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = db.add_device_usage('lighting', 'Lighting')
        device1 = db.add_device(d_name='device1', d_address='A1', d_type_id=dty1.id, d_usage_id=du1.id)
        device2 = db.add_device(d_name='device2', d_address='A2', d_type_id=dty1.id, d_usage_id=du1.id)

        now_ts = time.mktime(datetime.datetime.now().timetuple())
        db.add_device_stat(now_ts, 'val1', '10', device1.id)
        db.add_device_stat(now_ts, 'val2', '10.5' , device1.id)
        db.add_device_stat(now_ts + 1, 'val1', '10', device1.id)
        db.add_device_stat(now_ts + 1, 'val2', '10.5' , device1.id)

        db.add_device_stat(now_ts + 2, 'val1', '40', device2.id)
        db.add_device_stat(now_ts + 2, 'val2', '41' , device2.id)

        l_stats = db.list_device_stats(device1.id)
        d_stats_list_d = db.del_device_stats(device1.id)
        assert len(d_stats_list_d) == len(l_stats)
        l_stats = db.list_device_stats(device1.id)
        assert len(l_stats) == 0
        l_stats = db.list_device_stats(device2.id)
        assert len(l_stats) == 2
        db.del_device_stats(device2.id, 'val2')
        assert len(db.list_device_stats(device2.id)) == 1
        assert db.list_device_stats(device2.id)[0].value == '40'

class PersonAndUserAccountsTestCase(GenericTestCase):
    """Test person and user accounts"""

    def setUp(self):
        self.remove_all_persons()

    def tearDown(self):
        self.remove_all_persons()

    def test_empty_list(self):
        assert len(db.list_persons()) == 0
        assert len(db.list_user_accounts()) == 0

    def test_add(self):
        person1 = db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                p_birthdate=datetime.date(1973, 4, 24))
        assert person1.last_name == 'SCHNEIDER'
        print(person1)
        default_user = db.add_default_user_account()
        assert default_user is not None
        # Make sure we can't add twice a default account
        assert db.add_default_user_account() is None
        password = '@#?Iwont*GiveIt+-'
        user1 = db.add_user_account(a_login='mschneider', a_password=password,
                                    a_person_id=person1.id, a_is_admin=True)
        print(user1)
        assert user1.person.first_name == 'Marc'
        assert db.authenticate('mschneider', password)
        assert not db.authenticate('mschneider', 'plop')
        assert not db.authenticate('hello', 'boy')
        try:
            db.add_user_account(a_login='mschneider', a_password='plop', a_person_id=person1.id)
            TestCase.fail(self, "It shouldn't have been possible to add login %s. It already exists!" % 'mschneider')
        except DbHelperException:
            pass
        try:
            db.add_user_account(a_login='mygod', a_password='plop', a_person_id=999999999)
            TestCase.fail(self, "It shouldn't have been possible to add login %s. : associated person does not exist")
        except DbHelperException:
            pass
        person2 = db.add_person(p_first_name='Marc', p_last_name='DELAMAIN',
                                p_birthdate=datetime.date(1981, 4, 24))
        user2 = db.add_user_account(a_login='lonely', a_password='boy', a_person_id=person2.id, a_is_admin=True)
        person3 = db.add_person(p_first_name='Ali', p_last_name='CANTE')
        assert len(db.list_persons()) == 4
        user3 = db.add_user_account(a_login='domo', a_password='gik', a_person_id=person3.id, a_is_admin=True)
        user4 = db.add_user_account_with_person(
                            a_login='jsteed', a_password='theavengers', a_person_first_name='John',
                            a_person_last_name='STEED', a_person_birthdate=datetime.date(1931, 4, 24),
                            a_is_admin=True, a_skin_used='skins/hat')
        assert user4.login == 'jsteed'
        assert user4.person.first_name == 'John'
        assert user4.person.last_name == 'STEED'
        assert len(db.list_user_accounts()) == 5

    def test_update(self):
        person = db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                               p_birthdate=datetime.date(1973, 4, 24))
        person_u = db.update_person(p_id=person.id, p_first_name='Marco', p_last_name='SCHNEIDERO',
                                    p_birthdate=datetime.date(1981, 4, 24))
        assert str(person_u.birthdate) == str(datetime.date(1981, 4, 24))
        assert person_u.last_name == 'SCHNEIDERO'
        assert person_u.first_name == 'Marco'
        user_acc = db.add_user_account(a_login='mschneider', a_password='IwontGiveIt',
                                       a_person_id=person_u.id, a_is_admin=True)
        assert not db.change_password(999999999, 'IwontGiveIt', 'foo')
        assert db.change_password(user_acc.id, 'IwontGiveIt', 'OkIWill')
        assert not db.change_password(user_acc.id, 'DontKnow', 'foo')

        user_acc_u = db.update_user_account(a_id=user_acc.id, a_new_login='mschneider2', a_is_admin=False)
        assert not user_acc_u.is_admin
        try:
            db.update_user_account(a_id=user_acc.id, a_person_id=999999999)
            TestCase.fail(self, "An exception should have been raised : person id does not exist")
        except DbHelperException:
            pass
        user_acc_u = db.update_user_account_with_person(a_id=user_acc.id, a_login='mschneider3',
                                                        p_first_name='Bob', p_last_name='Marley',
                                                        p_birthdate=datetime.date(1991, 4, 24),
                                                        a_is_admin=True, a_skin_used='skins/crocodile')
        assert user_acc_u.login == 'mschneider3'
        assert user_acc_u.person.first_name == 'Bob'
        assert user_acc_u.person.last_name == 'Marley'
        assert str(user_acc_u.person.birthdate) == str(datetime.date(1991, 4, 24))
        assert user_acc_u.is_admin
        assert user_acc_u.skin_used == 'skins/crocodile'

    def testGet(self):
        person1 = db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                p_birthdate=datetime.date(1973, 4, 24))
        person2 = db.add_person(p_first_name='Monthy', p_last_name='PYTHON',
                                p_birthdate=datetime.date(1981, 4, 24))
        person3 = db.add_person(p_first_name='Alberto', p_last_name='MATE',
                                p_birthdate=datetime.date(1947, 8, 6))
        user1 = db.add_user_account(a_login='mschneider', a_password='IwontGiveIt',
                                    a_person_id=person1.id, a_is_admin=True)
        user2 = db.add_user_account(a_login='lonely', a_password='boy',
                                    a_person_id=person2.id, a_is_admin=True)
        assert db.get_user_account_by_person(person3.id) is None
        user_acc = db.get_user_account(user1.id)
        assert user_acc.login == 'mschneider'
        assert user_acc.person.last_name == 'SCHNEIDER'
        user_acc = db.get_user_account_by_login('mschneider')
        assert user_acc is not None
        assert db.get_user_account_by_login('mschneider').id == user1.id
        assert db.get_user_account_by_login('lucyfer') is None

        user_acc = db.get_user_account_by_person(person1.id)
        assert user_acc.login == 'mschneider'
        assert db.get_person(person1.id).first_name == 'Marc'
        assert db.get_person(person2.id).last_name == 'PYTHON'

    def test_del(self):
        person1 = db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                p_birthdate=datetime.date(1973, 4, 24))
        person2 = db.add_person(p_first_name='Monthy', p_last_name='PYTHON',
                                p_birthdate=datetime.date(1981, 4, 24))
        person3 = db.add_person(p_first_name='Alberto', p_last_name='MATE',
                                p_birthdate=datetime.date(1947, 8, 6))
        user1 = db.add_user_account(a_login='mschneider', a_password='IwontGiveIt', a_person_id=person1.id)
        user2 = db.add_user_account(a_login='lonely', a_password='boy', a_person_id=person2.id)
        user3 = db.add_user_account(a_login='domo', a_password='gik', a_person_id=person3.id)
        user3_id = user3.id
        user_acc_del = db.del_user_account(user3.id)
        assert user_acc_del.id == user3_id
        assert len(db.list_persons()) == 3
        l_user = db.list_user_accounts()
        assert len(l_user) == 2
        for user in l_user:
            assert user.login != 'domo'
        person1_id = person1.id
        person_del = db.del_person(person1.id)
        assert person_del.id == person1_id
        assert len(db.list_persons()) == 2
        assert len(db.list_user_accounts()) == 1
        try:
            db.del_person(12345678910)
            TestCase.fail(self, "Person does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        try:
            db.del_user_account(12345678910)
            TestCase.fail(self, "User account does not exist, an exception should have been raised")
        except DbHelperException:
            pass

if __name__ == "__main__":
    print("Creating test database...")
    db = DbHelper(use_test_db=True)
    url = db.get_url_connection_string()
    test_url = '%s_test' % url
    engine_test = create_engine(test_url)
    sql_schema.metadata.reflect(engine_test)
    sql_schema.metadata.drop_all(engine_test)
    sql_schema.metadata.create_all(engine_test)
    
    print("*** Using database %s ***\n" % db.get_db_type())
    unittest.main()

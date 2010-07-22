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
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import unittest
from unittest import TestCase
import time
import datetime

from domogik.common.database import DbHelper, DbHelperException
from domogik.common.sql_schema import Area, Device, DeviceFeatureModel, DeviceUsage, DeviceConfig, DeviceStats, \
                                      DeviceFeatureAssociation, DeviceTechnology, PluginConfig, \
                                      DeviceType, UIItemConfig, Room, UserAccount, SystemConfig, Trigger, Person


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

    def remove_all_areas(self, db):
        for area in db.list_areas():
            db.del_area(area.id)

    def remove_all_rooms(self, db):
        for room in db.list_rooms():
            db.del_room(room.id)

    def remove_all_devices(self, db):
        for device in db.list_devices():
            db.del_device(device.id)

    def remove_all_device_usages(self, db):
        for du in db.list_device_usages():
            db.del_device_usage(du.id, cascade_delete=True)

    def remove_all_device_types(self, db):
        for dty in db.list_device_types():
            db.del_device_type(dty.id, cascade_delete=True)

    def remove_all_device_config(self, db):
        device_list = db.list_devices()
        for device in device_list:
            db.del_device_config(device.id)

    def remove_all_device_feature_models(self, db):
        for af in db.list_actuator_feature_models():
            db.del_actuator_feature_model(af.id)
        for sf in db.list_sensor_feature_models():
            db.del_sensor_feature_model(sf.id)

    def remove_all_device_feature_associations(self, db):
        for dfa in db.list_device_feature_associations():
            db.del_device_feature_association(dfa.id)

    def remove_all_plugin_config(self, db):
        for plc in db.list_all_plugin_config():
            db.del_plugin_config(plc.name, plc.hostname)

    def remove_all_device_technologies(self, db):
        for dt in db.list_device_technologies():
            db.del_device_technology(dt.id, cascade_delete=True)

    def remove_all_device_stats(self, db):
        for device in db.list_devices():
            db.del_device_stats(device.id)

    def remove_all_triggers(self, db):
        for trigger in db.list_triggers():
            db.del_trigger(trigger.id)

    def remove_all_persons(self, db):
        for person in self.db.list_persons():
            self.db.del_person(person.id)

    def remove_all_user_accounts(self, db):
        for user in self.db.list_user_accounts():
            self.db.del_user_account(user.id)

    def remove_all_ui_item_config(self, db):
        for uic in db.list_all_ui_item_config():
            db.delete_ui_item_config(uic.name, uic.reference, uic.key)


class AreaTestCase(GenericTestCase):
    """Test areas"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_areas(self.db)

    def tearDown(self):
        self.remove_all_areas(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_areas()) == 0

    def test_add(self):
        try:
            self.db.add_area(None, None)
            TestCase.fail(self, "An exception should have been raised : impossible to create an area without a name")
        except DbHelperException:
            pass
        area0 = self.db.add_area('area0','description 0')
        print(area0)
        assert area0.name == 'area0'
        assert self.db.list_areas()[0].name == 'area0'

    def test_update(self):
        area = self.db.add_area('area0','description 0')
        area_u = self.db.update_area(area.id, 'area1','description 1')
        assert area_u.name == 'area1'
        assert area_u.description == 'description 1'

    def test_fetch_information(self):
        area = self.db.add_area('area0','description 0')
        area0 = self.db.get_area_by_name('Area0')
        assert area0.name == 'area0', 'area0 not found'
        basement = self.db.add_area('Basement')
        first_floor = self.db.add_area('First floor')
        self.db.add_room(r_name='Bedroom1', r_area_id=first_floor.id)
        self.db.add_room(r_name='Bedroom2', r_area_id=first_floor.id)
        self.db.add_room(r_name='Kitchen', r_area_id=basement.id)
        self.db.add_room(r_name='Bathroom', r_area_id=basement.id)
        self.db.add_room(r_name='Lounge', r_area_id=basement.id)
        for area in self.db.list_areas():
            if area.name == 'Basement':
                assert len(area.rooms) == 3
                for room in area.rooms:
                    assert room.name in ['Kitchen', 'Bathroom', 'Lounge']
            elif area.name == 'First floor':
                assert len(area.rooms) == 2
                for room in area.rooms:
                    assert room.name in ['Bedroom1', 'Bedroom2']

    def test_del(self):
        area0 = self.db.add_area('area0','description 0')
        area0_id = area0.id
        area_d = self.db.del_area(area0.id)
        assert not self.has_item(self.db.list_areas(), ['area0'])
        assert area_d.id == area0.id
        assert len(self.db.list_device_feature_associations_by_area_id(area_d.id)) == 0
        try:
            self.db.del_area(12345678910)
            TestCase.fail(self, "Area does not exist, an exception should have been raised")
        except DbHelperException:
            pass


class RoomTestCase(GenericTestCase):
    """Test rooms"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_rooms(self.db)
        self.remove_all_areas(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_rooms(self.db)
        self.remove_all_areas(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_rooms()) == 0

    def test_add(self):
        try:
            self.db.add_room(r_name='foo', r_area_id=99999999999, r_description='foo')
            TestCase.fail(self, "An exception should have been raised : area id does not exist")
        except DbHelperException:
            pass
        room = self.db.add_room(r_name='my_room', r_area_id=None, r_description='my_description')
        print(room)
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        assert room1.name == 'room1'
        assert room1.description == 'description 1'
        assert room1.area_id == area1.id
        room2 = self.db.add_room(r_name='room2', r_description='description 2', r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3', r_area_id=area2.id)
        assert len(self.db.list_rooms()) == 4
        room4 = self.db.add_room(r_name='room4')

    def test_update(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        try:
            self.db.update_room(room.id, r_name='room2', r_description='description 2', r_area_id=99999999999)
            TestCase.fail(self, "An exception should have been raised : area id does not exist")
        except DbHelperException:
            pass
        room_u = self.db.update_room(room.id, r_name='room2', r_description='description 2', r_area_id=area2.id)
        assert room_u.name == 'room2'
        assert room_u.description == 'description 2'
        assert room_u.area_id == area2.id
        room_u = self.db.update_room(room.id, r_area_id='')
        assert room_u.area_id == None

    def test_del(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        room2 = self.db.add_room(r_name='room2', r_description='description 2', r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3', r_area_id=area2.id)
        room1_id = room1.id
        room_deleted = self.db.del_room(room1.id)
        assert not self.has_item(self.db.list_rooms(), ['room1'])
        assert self.has_item(self.db.list_rooms(), ['room2', 'room3'])
        assert room_deleted.id == room1_id
        assert len(self.db.list_device_feature_associations_by_room_id(room_deleted.id)) == 0
        try:
            self.db.del_room(12345678910)
            TestCase.fail(self, "Room does not exist, an exception should have been raised")
        except DbHelperException:
            pass

    def test_list_and_get(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        assert self.db.get_room_by_name('Room1').name == 'room1'

        area2 = self.db.add_area('area2','description 2')
        room2 = self.db.add_room(r_name='room2', r_description='description 2', r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3',r_area_id=area2.id)
        assert len(self.db.get_all_rooms_of_area(area1.id)) == 2
        assert len(self.db.get_all_rooms_of_area(area2.id)) == 1


class DeviceUsageTestCase(GenericTestCase):
    """Test device usages"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_usages(self.db)

    def tearDown(self):
        self.remove_all_device_usages(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_device_usages()) == 0

    def test_add(self):
        du1 = self.db.add_device_usage(du_name='du1', du_description='desc1', du_default_options='def opt1')
        print(du1)
        assert du1.name == 'du1'
        assert du1.description == 'desc1'
        assert du1.default_options == 'def opt1'
        du2 = self.db.add_device_usage('du2')
        assert len(self.db.list_device_usages()) == 2
        assert self.has_item(self.db.list_device_usages(), ['du1', 'du2'])

    def test_update(self):
        du = self.db.add_device_usage('du1')
        du_u = self.db.update_device_usage(du_id=du.id, du_name='du2',
                                           du_description='description 2',
                                           du_default_options='def opt2')
        assert du_u.name == 'du2'
        assert du_u.description == 'description 2'
        assert du_u.default_options == 'def opt2'
        du_u = self.db.update_device_usage(du_id=du.id, du_description='', du_default_options='')
        assert du_u.description is None
        assert du_u.default_options is None

    def test_list_and_get(self):
        du1 = self.db.add_device_usage('du1')
        assert self.db.get_device_usage_by_name('Du1').name == 'du1'

    def test_del(self):
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        du2_id = du2.id
        du_del = self.db.del_device_usage(du2.id)
        assert self.has_item(self.db.list_device_usages(), ['du1'])
        assert not self.has_item(self.db.list_device_usages(), ['du2'])
        assert du_del.id == du2_id
        try:
            self.db.del_device_usage(12345678910)
            TestCase.fail(self, "Device usage does not exist, an exception should have been raised")
        except DbHelperException:
            pass

class DeviceTypeTestCase(GenericTestCase):
    """Test device types"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_types(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_types(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_device_types()) == 0

    def test_add(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        try:
            self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=u'99999999999')
            TestCase.fail(self, "An exception should have been raised : device techno id does not exist")
        except DbHelperException:
            pass
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        print(dty1)
        assert dty1.name == 'x10 Switch'
        assert dty1.description == 'desc1'
        assert dty1.device_technology_id == dt1.id
        dty2 = self.db.add_device_type(dty_name='x10 Dimmer', dty_description='desc2', dt_id=dt1.id)
        assert len(self.db.list_device_types()) == 2
        assert self.has_item(self.db.list_device_types(), ['x10 Switch', 'x10 Dimmer'])

    def test_update(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = self.db.add_device_technology('plcbus', 'PLCBus', 'desc dt2')
        dty = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        try:
            self.db.update_device_type(dty_id=dty.id, dty_name='x10 Dimmer', dt_id=u'99999999999')
            TestCase.fail(self, "An exception should have been raised : device techno id does not exist")
        except DbHelperException:
            pass
        dty_u = self.db.update_device_type(dty_id=dty.id, dty_name='x10 Dimmer', dt_id=dt2.id, dty_description='desc2')
        assert dty_u.name == 'x10 Dimmer'
        assert dty_u.description == 'desc2'
        assert dty_u.device_technology_id == dt2.id

    def test_list_and_get(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        assert self.db.get_device_type_by_name('x10 switch').name == 'x10 Switch'

    def test_del(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='x10 Dimmer', dt_id=dt1.id)
        dty2_id = dty2.id
        dty_del = self.db.del_device_type(dty2.id)
        assert self.has_item(self.db.list_device_types(), ['x10 Switch'])
        assert not self.has_item(self.db.list_device_usages(), ['x10 Dimmer'])
        assert dty_del.id == dty2_id
        try:
            self.db.del_device_type(12345678910)
            TestCase.fail(self, "Device type does not exist, an exception should have been raised")
        except DbHelperException:
            pass

class DeviceFeatureModelTestCase(GenericTestCase):
    """Test device feature models"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_feature_models(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_feature_models(self.db)
        self.remove_all_device_technologies(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_device_features()) == 0

    def test_add_get_list(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = self.db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='x10 Dimmer', dty_description='desc2', dt_id=dt1.id)
        dty3 = self.db.add_device_type(dty_name='1wire.Temperature', dty_description='desc3', dt_id=dt2.id)
        afm1 = self.db.add_actuator_feature_model(af_name='Switch', af_device_type_id=dty1.id, af_parameters='myparams1',
                                                 af_value_type='binary', af_return_confirmation=True)
        print(afm1)
        assert afm1.name == 'Switch'
        assert afm1.device_type_id == dty1.id
        assert afm1.parameters == 'myparams1'
        assert afm1.value_type == 'binary'
        assert afm1.return_confirmation
        assert self.db.get_device_feature_model_by_id(afm1.id).name == 'Switch'
        afm2 = self.db.add_actuator_feature_model(af_name='Dimmer', af_device_type_id=dty2.id, af_parameters='myparams2',
                                                  af_value_type='number', af_return_confirmation=True)
        sfm1 = self.db.add_sensor_feature_model(sf_name='Thermometer', sf_device_type_id=dty3.id,
                                                sf_parameters='myparams3', sf_value_type='number')
        print(sfm1)
        assert sfm1.name == 'Thermometer'
        assert sfm1.device_type_id == dty3.id
        assert sfm1.parameters == 'myparams3'
        assert sfm1.value_type == 'number'
        assert len(self.db.list_device_feature_models()) == 3
        assert self.has_item(self.db.list_device_feature_models(), ['Switch', 'Dimmer', 'Thermometer'])
        assert len(self.db.list_actuator_feature_models()) == 2
        assert self.db.get_actuator_feature_model_by_id(afm2.id).name == 'Dimmer'
        assert len(self.db.list_sensor_feature_models()) == 1
        assert self.db.get_sensor_feature_model_by_id(sfm1.id).name == 'Thermometer'
        assert len(self.db.list_device_feature_models_by_device_type_id(dty1.id)) == 1
        assert len(self.db.list_device_feature_models_by_device_type_id(dty3.id)) == 1

    def test_update(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = self.db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='1wire.Temperature', dty_description='desc3', dt_id=dt2.id)
        af1 = self.db.add_actuator_feature_model(af_name='Switch', af_device_type_id=dty1.id, af_value_type='number',
                                                 af_parameters='myparams1')
        af1_u = self.db.update_actuator_feature_model(af_id=af1.id, af_name='Big switch',
                                                      af_parameters='myparams_u', af_return_confirmation=True)
        assert af1_u.name == 'Big switch'
        assert af1_u.parameters == 'myparams_u'
        assert af1_u.value_type == 'number'
        assert af1_u.return_confirmation
        sf1 = self.db.add_sensor_feature_model(sf_name='Thermometer', sf_device_type_id=dty2.id,
                                               sf_parameters='myparams2', sf_value_type='number')
        sf1_u = self.db.update_sensor_feature_model(sf_id=sf1.id, sf_value_type='string')
        assert sf1_u.value_type == 'string'

    def test_del(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = self.db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='x10 Dimmer', dty_description='desc2', dt_id=dt1.id)
        dty3 = self.db.add_device_type(dty_name='1wire.Temperature', dty_description='desc3', dt_id=dt2.id)
        af1 = self.db.add_actuator_feature_model(af_name='Switch', af_device_type_id=dty1.id, af_parameters='myparams1',
                                                 af_value_type='binary', af_return_confirmation=True)
        af2 = self.db.add_actuator_feature_model(af_name='Dimmer', af_device_type_id=dty2.id, af_parameters='myparams2',
                                                 af_value_type='number', af_return_confirmation=True)
        sf1 = self.db.add_sensor_feature_model(sf_name='Thermometer', sf_device_type_id=dty3.id,
                                               sf_parameters='myparams3', sf_value_type='number')
        af_d = self.db.del_actuator_feature_model(af1.id)
        assert af_d.id == af1.id
        assert len(self.db.list_device_feature_associations_by_feature_id(af_d.id)) == 0
        assert len(self.db.list_device_feature_models()) == 2
        assert len(self.db.list_actuator_feature_models()) == 1
        assert len(self.db.list_sensor_feature_models()) == 1
        af_d = self.db.del_actuator_feature_model(af2.id)
        assert len(self.db.list_actuator_feature_models()) == 0
        sf_d = self.db.del_sensor_feature_model(sf1.id)
        assert len(self.db.list_sensor_feature_models()) == 0


class DeviceFeatureAssociationTestCase(GenericTestCase):
    """Test device / feature association"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_feature_associations(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_feature_associations(self.db)
        self.remove_all_device_technologies(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_device_feature_associations()) == 0

    def test_add_get_list(self):
        area1 = self.db.add_area('Basement')
        area2 = self.db.add_area('First floor')
        room1 = self.db.add_room('Kitchen', area1.id)
        room2 = self.db.add_room('Room', area1.id)
        dt1 = self.db.add_device_technology('x10', 'x10', 'x10 device type')
        dt2 = self.db.add_device_technology('plcbus', 'PLCBus', 'PLCBus device type')
        du1 = self.db.add_device_usage('Appliance')
        du2 = self.db.add_device_usage('Lamp')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dt_id=dt1.id, dty_description='My beautiful switch')
        dty2 = self.db.add_device_type(dty_name='PLCBus Lamp', dt_id=dt2.id)
        af1 = self.db.add_actuator_feature_model(af_name='Switch', af_device_type_id=dty1.id, af_parameters='myparams1',
                                                 af_value_type='binary')
        af2 = self.db.add_actuator_feature_model(af_name='Dimmer', af_device_type_id=dty2.id, af_parameters='myparams2',
                                                 af_value_type='number')
        af3 = self.db.add_actuator_feature_model(af_name='Switch', af_device_type_id=dty2.id, af_parameters='myparams3',
                                                 af_value_type='number')
        device1 = self.db.add_device(d_name='Toaster', d_address='A1', d_type_id=dty1.id, d_usage_id=du1.id)
        #assert self.db.get_device_feature_by_id(
        device2 = self.db.add_device(d_name='Air conditioning', d_address='A2', d_type_id=dty1.id, d_usage_id=du1.id,
                                     d_description='Cold thing')
        device3 = self.db.add_device(d_name='Lamp', d_address='A1', d_type_id=dty2.id, d_usage_id=du2.id,
                                     d_description='')
        df_list = self.db.list_device_features_by_device_id(device3.id)
        assert len(df_list) == 2
        assert self.db.get_device_feature_by_id(df_list[0].id) is not None
        df_list = self.db.list_device_feature_by_device_feature_model_id(af1.id)
        dfa = self.db.add_device_feature_association(d_feature_id=df_list[0].id, d_place_type='house')
        assert self.db.get_device_feature_association_by_id(dfa.id) is not None
        print(dfa)
        df_list = self.db.list_device_feature_by_device_feature_model_id(af2.id)
        self.db.add_device_feature_association(d_feature_id=df_list[0].id, d_place_id=room1.id, d_place_type='room')
        df_list = self.db.list_device_feature_by_device_feature_model_id(af3.id)
        self.db.add_device_feature_association(d_feature_id=df_list[0].id, d_place_id=room1.id, d_place_type='room')
        df_list = self.db.list_device_feature_by_device_id(device2.id)
        self.db.add_device_feature_association(d_feature_id=df_list[0].id, d_place_id=area1.id, d_place_type='area')
        assert len(self.db.list_device_feature_associations()) == 4
        assert len(self.db.list_device_feature_associations_by_house()) == 1
        assert len(self.db.list_device_feature_associations_by_room_id(room1.id)) == 2
        assert len(self.db.list_device_feature_associations_by_room_id(room2.id)) == 0
        assert len(self.db.list_device_feature_associations_by_area_id(area1.id)) == 1
        assert len(self.db.list_device_feature_associations_by_area_id(area2.id)) == 0

    def test_del(self):
        area1 = self.db.add_area('Basement')
        area2 = self.db.add_area('First floor')
        room1 = self.db.add_room('Kitchen', area1.id)
        room2 = self.db.add_room('Room', area1.id)
        dt1 = self.db.add_device_technology('x10', 'x10', 'x10 device type')
        dt2 = self.db.add_device_technology('plcbus', 'PLCBus', 'PLCBus device type')
        du1 = self.db.add_device_usage('Appliance')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dt_id=dt1.id,
                                       dty_description='My beautiful switch')
        dty2 = self.db.add_device_type(dty_name='PLCBus Switch', dt_id=dt2.id,
                                       dty_description='Another beautiful switch')
        afm1 = self.db.add_actuator_feature_model(af_name='Switch', af_device_type_id=dty1.id, af_value_type='binary',
                                                  af_parameters='myparams1')
        afm2 = self.db.add_actuator_feature_model(af_name='Dimmer', af_device_type_id=dty2.id, af_value_type='number',
                                                  af_parameters='myparams2')
        device1 = self.db.add_device(d_name='Toaster', d_address='A1', d_type_id=dty1.id, d_usage_id=du1.id,
                                     d_description='My new toaster')
        device2 = self.db.add_device(d_name='Washing machine', d_address='A1', d_type_id=dty2.id, d_usage_id=du1.id,
                                     d_description='Laden')
        device3 = self.db.add_device(d_name='Mixer', d_address='A2', d_type_id=dty2.id, d_usage_id=du1.id,
                                     d_description='Moulinex')
        df1 = self.db.get_device_feature(device1.id, afm1.id)
        dfa1 = self.db.add_device_feature_association(d_feature_id=df1.id, d_place_type='house')
        df2 = self.db.get_device_feature(device2.id, afm2.id)
        dfa2 = self.db.add_device_feature_association(d_feature_id=df2.id, d_place_id=room1.id, d_place_type='room')
        dfa3 = self.db.add_device_feature_association(d_feature_id=df2.id, d_place_id=area2.id, d_place_type='area')
        df3 = self.db.get_device_feature(device3.id, afm2.id)
        dfa4 = self.db.add_device_feature_association(d_feature_id=df3.id, d_place_id=area1.id, d_place_type='area')
        dfa5 = self.db.add_device_feature_association(d_feature_id=df3.id, d_place_type='house')
        assert len(self.db.list_device_feature_associations()) == 5
        dfa = self.db.del_device_feature_association(dfa1.id)
        assert dfa.id == dfa1.id
        assert len(self.db.list_device_feature_associations()) == 4
        assert len(self.db.list_device_feature_associations_by_room_id(room1.id)) == 1
        assert len(self.db.list_device_feature_associations_by_area_id(area1.id)) == 1
        assert len(self.db.del_device_feature_association_by_device_feature_id(df3.id)) == 2
        assert len(self.db.del_device_feature_association_by_place_id(area2.id)) == 1
        assert len(self.db.del_device_feature_association_by_place_type('room')) == 1
        assert len(self.db.list_device_feature_associations()) == 0

class DeviceTechnologyTestCase(GenericTestCase):
    """Test device technologies"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_technologies(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_device_technologies()) == 0

    def test_add(self):
        dt1 = self.db.add_device_technology('1wire', '1-Wire', 'desc dt1')
        print(dt1)
        assert dt1.id == '1wire'
        assert dt1.name == '1-Wire'
        assert dt1.description == 'desc dt1'
        dt2 = self.db.add_device_technology('x10', 'x10', 'desc dt2')
        dt3 = self.db.add_device_technology('plcbus', 'PLCBus', 'desc dt3')
        assert len(self.db.list_device_technologies()) == 3
        assert self.has_item(self.db.list_device_technologies(), ['x10', '1-Wire', 'PLCBus'])

    def test_update(self):
        dt = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dt_u = self.db.update_device_technology(dt.id, dt_description='desc dt2')
        assert dt_u.description == 'desc dt2'

    def test_list_and_get(self):
        dt2 = self.db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        assert self.db.get_device_technology_by_id('1wire').id == '1wire'

    def test_del(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dt2 = self.db.add_device_technology('1wire', '1-Wire', 'desc dt2')
        dt_del = dt2
        dt2_id = dt2.id
        dt3 = self.db.add_device_technology('plcbus', 'PLCBus', 'desc dt3')
        self.db.del_device_technology(dt2.id)
        assert self.has_item(self.db.list_device_technologies(), ['x10', 'PLCBus'])
        assert not self.has_item(self.db.list_device_technologies(), ['1-Wire'])
        assert dt_del.id == dt2_id
        try:
            self.db.del_device_technology(12345678910)
            TestCase.fail(self, "Device technology does not exist, an exception should have been raised")
        except DbHelperException:
            pass

class PluginConfigTestCase(GenericTestCase):
    """Test plugin configuration"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_plugin_config(self.db)

    def tearDown(self):
        self.remove_all_plugin_config(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_all_plugin_config()) == 0

    def test_add_get_list(self):
        pc1_1 = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.1', pl_key='key1_1', pl_value='val1_1')
        print(pc1_1)
        assert pc1_1.name == 'x10'
        assert pc1_1.key == 'key1_1'
        assert pc1_1.value == 'val1_1'
        pc1_2 = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.1', pl_key='key1_2', pl_value='val1_2')
        pc3_1 = self.db.set_plugin_config(pl_name='plcbus', pl_hostname='192.168.0.1', pl_key='key3_1',
                                          pl_value='val3_1')
        pc3_2 = self.db.set_plugin_config(pl_name='plcbus', pl_hostname='192.168.0.1', pl_key='key3_2',
                                          pl_value='val3_2')
        pc3_3 = self.db.set_plugin_config(pl_name='plcbus', pl_hostname='192.168.0.1', pl_key='key3_3',
                                          pl_value='val3_3')
        pc4_1 = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.2', pl_key='key4_1', pl_value='val4_1')
        assert len(self.db.list_all_plugin_config()) == 6
        assert len(self.db.list_plugin_config('x10', '192.168.0.1')) == 2
        assert len(self.db.list_plugin_config('plcbus', '192.168.0.1')) == 3
        assert len(self.db.list_plugin_config('x10', '192.168.0.2')) == 1
        assert len(self.db.list_plugin_config('plcbus', '192.168.0.2')) == 0
        assert self.db.get_plugin_config('x10', '192.168.0.1', 'key1_2').value == 'val1_2'

    def test_update(self):
        plc = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.1', pl_key='key1', pl_value='val1')
        plc_u = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.1', pl_key='key1', pl_value='val11')
        assert plc_u.key == 'key1'
        assert plc_u.value == 'val11'
        assert self.db.get_plugin_config('x10', '192.168.0.1', 'key1').value == 'val11'

    def test_del(self):
        plc1_1 = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.1', pl_key='key1_1', pl_value='val1_1')
        plc1_2 = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.1', pl_key='key1_2', pl_value='val1_2')
        plc3_1 = self.db.set_plugin_config(pl_name='plcbus', pl_hostname='192.168.0.1', pl_key='key3_1',
                                           pl_value='val3_1')
        plc3_2 = self.db.set_plugin_config(pl_name='plcbus', pl_hostname='192.168.0.1', pl_key='key3_2',
                                           pl_value='val3_2')
        plc3_3 = self.db.set_plugin_config(pl_name='plcbus', pl_hostname='192.168.0.1', pl_key='key3_3',
                                           pl_value='val3_3')
        pc4_1 = self.db.set_plugin_config(pl_name='x10', pl_hostname='192.168.0.2', pl_key='key4_1', pl_value='val4_1')
        assert len(self.db.del_plugin_config('x10', '192.168.0.1')) == 2
        assert len(self.db.list_plugin_config('x10', '192.168.0.1')) == 0
        assert len(self.db.list_plugin_config('plcbus', '192.168.0.1')) == 3
        assert len(self.db.list_plugin_config('x10', '192.168.0.2')) == 1


class DeviceTestCase(GenericTestCase):
    """Test device"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_devices(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_devices(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_devices()) == 0

    def test_add(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        du1 = self.db.add_device_usage('du1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        try:
            self.db.add_device(d_name='device1', d_address = 'A1', d_type_id = 9999999999, d_usage_id = du1.id)
            TestCase.fail(self, "Device type does not exist, an exception should have been raised")
            self.db.add_device(d_name='device1', d_address = 'A1', d_type_id = dty1.id, d_usage_id = 9999999999999)
            TestCase.fail(self, "Device usage does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        device1 = self.db.add_device(d_name='device1', d_address='A1',
                                     d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        assert device1.name == 'device1' and device1.description == 'desc1'
        print(device1)
        assert len(self.db.list_devices()) == 1
        device2 = self.db.add_device(d_name='device2', d_address='A2',
                    d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        assert len(self.db.list_devices()) == 2

    def test_list_and_get(self):
        area1 = self.db.add_area('Basement','description 1')
        room1 = self.db.add_room('Kitchen', area1.id)
        room2 = self.db.add_room('Bathroom', area1.id)
        dt1 = self.db.add_device_technology('x10', 'x10', 'x10 device type')
        dt2 = self.db.add_device_technology('plcbus', 'PLCBus', 'PLCBus device type')
        du1 = self.db.add_device_usage('Appliance')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dt_id=dt1.id,
                                       dty_description='My beautiful switch')
        dty2 = self.db.add_device_type(dty_name='PLCBus Switch', dt_id=dt2.id,
                                       dty_description='Another beautiful switch')
        device1 = self.db.add_device(d_name='Toaster', d_address='A1',
                                     d_type_id=dty1.id, d_usage_id=du1.id, d_description='My new toaster')
        device2 = self.db.add_device(d_name='Washing machine', d_address='A1',
                                     d_type_id=dty2.id, d_usage_id=du1.id, d_description='Laden')
        device3 = self.db.add_device(d_name='Mixer', d_address='A2',
                                     d_type_id=dty2.id, d_usage_id=du1.id, d_description='Moulinex')
        search_dev1 = self.db.get_device_by_technology_and_address(dt1.id, 'A1')
        assert search_dev1.name == 'Toaster'
        search_dev2 = self.db.get_device_by_technology_and_address(dt1.id, 'A2')
        assert search_dev2 == None

    def test_update(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        room2 = self.db.add_room('room2', area1.id)
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage('du1')
        device1 = self.db.add_device(d_name='device1', d_address='A1',
                    d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        device_id = device1.id
        try:
            self.db.update_device(d_id=device1.id, d_usage_id=9999999999999)
            TestCase.fail(self, "Device usage does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        device1 = self.db.update_device(d_id=device1.id, d_description='desc2', d_reference='A1')
        device1 = self.db.get_device(device_id)
        assert device1.description == 'desc2'
        assert device1.reference == 'A1'
        device1 = self.db.update_device(d_id=device1.id, d_reference='')
        assert device1.reference == None

    def test_del(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room('room1', area1.id)
        room2 = self.db.add_room('room2', area2.id)
        dt1 = self.db.add_device_technology('x10', 'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        device1 = self.db.add_device(d_name='device1', d_address='A1',
                                     d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        device2 = self.db.add_device(d_name='device2', d_address='A2',
                                     d_type_id=dty1.id, d_usage_id=du1.id, d_description='desc1')
        device3 = self.db.add_device(d_name='device3', d_address='A3', d_type_id=dty1.id, d_usage_id=du1.id)
        device_del = device2
        device2_id = device2.id
        self.db.del_device(device2.id)
        assert len(self.db.list_devices()) == 2
        for dev in self.db.list_devices():
            assert dev.address in ('A1', 'A3')
        assert device_del.id == device2.id
        #assert len(self.db.list_device_feature_association_by_device_id(device_del.id)) == 0
        try:
            self.db.del_device(12345678910)
            TestCase.fail(self, "Device does not exist, an exception should have been raised")
        except DbHelperException:
            pass


class DeviceConfigTestCase(GenericTestCase):
    """Test Device config"""

    def __create_sample_device(self, device_name, device_technology_name):
        dt = self.db.add_device_technology(device_technology_name, 'a name', 'this is my device tech')
        du = self.db.add_device_usage("lighting")
        dty = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt.id)
        area = self.db.add_area('area1','description 1')
        room = self.db.add_room('room1', area.id)
        device = self.db.add_device(d_name=device_name, d_address = "A1", d_type_id=dty.id, d_usage_id=du.id)
        return device

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_config(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_config(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_all_device_config()) == 0

    def test_add(self):
        device1 = self.__create_sample_device('device1', 'dt1')
        device2 = self.__create_sample_device('device2', 'dt2')
        device_config1_1 = self.db.set_device_config('key1_1', 'val1_1', device1.id)
        print(device_config1_1)
        assert device_config1_1.key == 'key1_1'
        assert device_config1_1.value == 'val1_1'
        device_config2_1 = self.db.set_device_config('key2_1', 'val2_1', device1.id)
        device_config3_1 = self.db.set_device_config('key3_1', 'val3_1', device1.id)
        device_config1_2 = self.db.set_device_config('key1_2', 'val1_2', device2.id)
        device_config2_2 = self.db.set_device_config('key2_2', 'val2_2', device2.id)
        assert len(self.db.list_device_config(device1.id)) == 3
        assert len(self.db.list_device_config(device2.id)) == 2

    def test_update(self):
        device1 = self.__create_sample_device('device1', 'dt1')
        device_config1_1 = self.db.set_device_config('key1_1', 'val1_1', device1.id)
        device_config1_1 = self.db.set_device_config('key1_1', 'val1_1_u', device1.id)
        assert device_config1_1.value == 'val1_1_u'

    def test_get(self):
        device1 = self.__create_sample_device('device1', 'dt1')
        device2 = self.__create_sample_device('device2', 'dt2')
        device_config1_1 = self.db.set_device_config('key1_1', 'val1_1', device1.id)
        device_config2_1 = self.db.set_device_config('key2_1', 'val2_1', device1.id)
        device_config3_1 = self.db.set_device_config('key3_1', 'val3_1', device1.id)
        device_config1_2 = self.db.set_device_config('key1_2', 'val1_2', device2.id)
        device_config2_2 = self.db.set_device_config('key2_2', 'val2_2', device2.id)
        assert self.db.get_device_config_by_key('key3_1', device1.id).value == 'val3_1'
        assert self.db.get_device_config_by_key('key1_2', device2.id).value == 'val1_2'

    def test_del(self):
        device1 = self.__create_sample_device('device1', 'dt1')
        device2 = self.__create_sample_device('device2', 'dt2')
        device_config1_1 = self.db.set_device_config('key1_1', 'val1_1', device1.id)
        device_config2_1 = self.db.set_device_config('key2_1', 'val2_1', device1.id)
        device_config3_1 = self.db.set_device_config('key3_1', 'val3_1', device1.id)
        device_config1_2 = self.db.set_device_config('key1_2', 'val1_2', device2.id)
        device_config2_2 = self.db.set_device_config('key2_2', 'val2_2', device2.id)
        assert len(self.db.del_device_config(device1.id)) == 3
        assert len(self.db.list_all_device_config()) == 2
        assert len(self.db.del_device_config(device2.id)) == 2
        assert len(self.db.list_all_device_config()) == 0


class DeviceStatsTestCase(GenericTestCase):
    """Test device stats"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_stats(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_stats(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_all_device_stats()) == 0

    def __has_stat_values(self, device_stats_values, expected_values):
        if len(device_stats_values) != len(expected_values): return False
        for item in device_stats_values:
            if item.value not in expected_values: return False
        return True

    def test_add_list_get(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)
        device2 = self.db.add_device(d_name='device2', d_address='A2', d_type_id=dty1.id, d_usage_id=du1.id)
        ds1 = self.db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val1', 0, device1.id)
        print(ds1)
        assert ds1.key == 'val1' and ds1.value == '0'
        ds2 = self.db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val_char', 'plop', device1.id)
        assert ds2.key == 'val_char' and ds2.value == 'plop'
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val2', 1, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val1', 2, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val2', 3, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 2), 'val1', 4, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 2), 'val2', 5, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 3), 'val1', 6, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 3), 'val2', 7, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 4), 'val1', 8, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 4), 'val2', 9, device1.id)

        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val1', 100, device2.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val2', 200, device2.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val1', 300, device2.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val2', 400, device2.id)

        assert len(self.db.list_device_stats(device1.id)) == 11
        assert self.db.get_last_stat_of_device_by_key('val1', device1.id).value == '8'
        assert self.db.get_last_stat_of_device_by_key('val2', device1.id).value == '9'

        stats_l = self.db.list_last_n_stats_of_device_by_key('val1', device1.id, 3)
        assert len(stats_l) == 3
        assert stats_l[0].value == '4' and stats_l[1].value == '6' and stats_l[2].value == '8'

        stats_l = self.db.list_stats_of_device_between_by_key('val1', device1.id, make_ts(2010, 04, 9, 12, 2),
                                                              make_ts(2010, 04, 9, 12, 4))
        assert len(stats_l) == 3
        assert stats_l[0].value == '4' and stats_l[1].value == '6' and stats_l[2].value == '8'
        stats_l = self.db.list_stats_of_device_between_by_key('val1', device1.id,
                                                              make_ts(2010, 04, 9, 12, 3))
        assert len(stats_l) == 2
        assert stats_l[0].value == '6' and stats_l[1].value == '8'
        stats_l = self.db.list_stats_of_device_between_by_key('val1', device1.id,
                                                              end_date_ts=make_ts(2010, 04, 9, 12, 2))
        assert len(stats_l) == 3
        assert stats_l[0].get_date_as_timestamp() == 1270810800.0

    def test_add_with_hist_size(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage("lighting")
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 0), 'val2', 1000, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 1), 'val1', 1, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 2), 'val1', 2, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 3), 'val1', 3, device1.id)
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 4), 'val1', 4, device1.id)
        assert len(self.db.list_device_stats(device1.id)) == 5
        assert len(self.db.list_device_stats_by_key('val1', device1.id)) == 4
        self.db.add_device_stat(make_ts(2010, 04, 9, 12, 5), 'val1', 5, device1.id, 2)
        stat_list = self.db.list_device_stats_by_key('val1', device1.id)
        assert len(stat_list) == 2
        for stat in stat_list:
            assert stat.value in ['4', '5']
        #assert len(self.db.list_device_stats(device1.id)) == 3

    def test_filter(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_type_id = dty1.id, d_usage_id = du1.id)

        # Minutes
        start_p = make_ts(2010, 2, 21, 15, 48, 0)
        end_p = make_ts(2010, 2, 21, 16, 8, 0)
        insert_step = 10
        for i in range(0, int(end_p - start_p), insert_step):
            self.db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i),
                            key=u'valm', value=(i/insert_step), device_id=device1.id)
            )
        self.db._DbHelper__session.commit()

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
            results = self.db.filter_stats_of_device_by_key(ds_key='valm', ds_device_id=device1.id,
                                                            start_date_ts=make_ts(2010, 2, 21, 15, 57, 0),
                                                            end_date_ts=make_ts(2010, 2, 21, 16, 3, 0),
                                                            step_used='minute', function_used=func)
            assert results == expected_results[func]

        start_p = make_ts(2010, 6, 21, 15, 48, 0)
        end_p = make_ts(2010, 6, 25, 21, 48, 0)
        insert_step = 2500
        for i in range(0, int(end_p - start_p), insert_step):
            self.db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i),
                            key=u'valh', value=i/insert_step, device_id=device1.id)
            )
        self.db._DbHelper__session.commit()

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
            results = self.db.filter_stats_of_device_by_key(ds_key='valh', ds_device_id=device1.id,
                                                            start_date_ts=make_ts(2010, 6, 22, 17, 48, 0),
                                                            end_date_ts=make_ts(2010, 6, 23, 1, 48, 0),
                                                            step_used='hour', function_used=func)
            assert results == expected_results[func]

        # Days
        start_p = make_ts(2010, 6, 21, 15, 48, 0)
        end_p = make_ts(2010, 6, 28, 21, 48, 0)
        insert_step = 28000
        for i in range(0, int(end_p - start_p), insert_step):
            self.db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i),
                            key=u'vald', value=i/insert_step, device_id=device1.id)
            )
        self.db._DbHelper__session.commit()

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
            results = self.db.filter_stats_of_device_by_key(ds_key='vald', ds_device_id=device1.id,
                                                            start_date_ts=make_ts(2010, 6, 22, 15, 48, 0),
                                                            end_date_ts=make_ts(2010, 7, 26, 15, 48, 0),
                                                            step_used='day', function_used=func)
            assert results == expected_results[func]

        # Weeks
        start_p = make_ts(2010, 6, 11, 15, 48, 0)
        end_p = make_ts(2010, 7, 28, 21, 48, 0)
        insert_step = 12 * 3600
        for i in range(0, int(end_p - start_p), insert_step):
            self.db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i),
                            key=u'valw', value=i/insert_step, device_id=device1.id)
            )
        self.db._DbHelper__session.commit()

        expected_results = {
            'avg': [(2010, 6, 25, 27.0), (2010, 6, 26, 39.5), (2010, 7, 27, 53.5), (2010, 7, 28, 67.5),
                    (2010, 7, 29, 81.5), (2010, 7, 30, 89.0)],
            'min': [(2010, 6, 25, 22.0), (2010, 6, 26, 33.0), (2010, 7, 27, 47.0), (2010, 7, 28, 61.0),
                    (2010, 7, 29, 75.0), (2010, 7, 30, 89.0)],
            'max': [(2010, 6, 25, 32.0), (2010, 6, 26, 46.0), (2010, 7, 27, 60.0), (2010, 7, 28, 74.0),
                    (2010, 7, 29, 88.0), (2010, 7, 30, 89.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results = self.db.filter_stats_of_device_by_key(ds_key='valw', ds_device_id=device1.id,
                                                            start_date_ts=make_ts(2010, 6, 22, 15, 48, 0),
                                                            end_date_ts=make_ts(2010, 7, 26, 15, 48, 0),
                                                            step_used='week', function_used=func)
            assert results == expected_results[func]

        # Months
        start_p = make_ts(2010, 6, 21, 15, 48, 0)
        end_p = make_ts(2013, 6, 21, 15, 48, 0)
        insert_step = 3600 * 24 * 15
        for i in range(0, int(end_p - start_p), insert_step):
            self.db._DbHelper__session.add(
                DeviceStats(date=datetime.datetime.fromtimestamp(start_p + i),
                            key=u'valmy', value=i/insert_step, device_id=device1.id)
            )
        self.db._DbHelper__session.commit()
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
            results =  self.db.filter_stats_of_device_by_key(ds_key='valmy', ds_device_id=device1.id,
                                                             start_date_ts=make_ts(2010, 6, 25, 15, 48, 0),
                                                             end_date_ts=make_ts(2011, 7, 29, 15, 48, 0),
                                                             step_used='month', function_used=func)
            assert results == expected_results[func]

        # Years
        expected_results = {
            'avg': [(2010, 6.0), (2011, 25.0), (2012, 43.0)],
            'min': [(2010, 0.0), (2011, 13.0), (2012, 38.0)],
            'max': [(2010, 12.0), (2011, 37.0), (2012, 48.0)]
        }
        for func in ('avg', 'min', 'max'):
            start_t = time.time()
            results=  self.db.filter_stats_of_device_by_key(ds_key='valmy', ds_device_id=device1.id,
                                                            start_date_ts=make_ts(2010, 6, 21, 15, 48, 0),
                                                            end_date_ts=make_ts(2012, 6, 21, 15, 48, 0),
                                                            step_used='year', function_used=func)
            assert results == expected_results[func]

    def test_del(self):
        dt1 = self.db.add_device_technology('x10', 'x10', 'this is x10')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address='A1', d_type_id=dty1.id, d_usage_id=du1.id)
        device2 = self.db.add_device(d_name='device2', d_address='A2', d_type_id=dty1.id, d_usage_id=du1.id)

        now_ts = time.mktime(datetime.datetime.now().timetuple())
        self.db.add_device_stat(now_ts, 'val1', '10', device1.id)
        self.db.add_device_stat(now_ts, 'val2', '10.5' , device1.id)
        self.db.add_device_stat(now_ts + 1, 'val1', '10', device1.id)
        self.db.add_device_stat(now_ts + 1, 'val2', '10.5' , device1.id)

        self.db.add_device_stat(now_ts + 2, 'val1', '40', device2.id)
        self.db.add_device_stat(now_ts + 2, 'val2', '41' , device2.id)

        l_stats = self.db.list_device_stats(device1.id)
        d_stats_list_d = self.db.del_device_stats(device1.id)
        assert len(d_stats_list_d) == len(l_stats)
        l_stats = self.db.list_device_stats(device1.id)
        assert len(l_stats) == 0
        l_stats = self.db.list_device_stats(device2.id)
        assert len(l_stats) == 2
        self.db.del_device_stats(device2.id, 'val2')
        assert len(self.db.list_device_stats(device2.id)) == 1
        assert self.db.list_device_stats(device2.id)[0].value == '40'


class TriggersTestCase(GenericTestCase):
    """Test triggers"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_triggers(self.db)

    def tearDown(self):
        self.remove_all_triggers(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_triggers()) == 0

    def test_add(self):
        trigger1 = self.db.add_trigger(t_description='desc1', t_rule='AND(x,OR(y,z))',
                                       t_result=['x10_on("a3")', '1wire()'])
        print(trigger1)
        assert trigger1.description == 'desc1'
        assert trigger1.rule == 'AND(x,OR(y,z))'
        trigger2 = self.db.add_trigger(t_description = 'desc2', t_rule='OR(x,AND(y,z))',
                                       t_result=['x10_on("a2")', '1wire()'])
        assert len(self.db.list_triggers()) == 2
        assert self.db.get_trigger(trigger1.id).description == 'desc1'

    def test_update(self):
        trigger = self.db.add_trigger(t_description='desc1', t_rule='AND(x,OR(y,z))',
                                      t_result=['x10_on("a3")', '1wire()'])
        trigger_u = self.db.update_trigger(t_id=trigger.id, t_description='desc2', t_rule='OR(x,AND(y,z))',
                                      t_result=['x10_on("a2")', '1wire()'])
        assert trigger_u.description == 'desc2'
        assert trigger_u.rule == 'OR(x,AND(y,z))'
        assert trigger_u.result == 'x10_on("a2");1wire()'

    def test_del(self):
        trigger1 = self.db.add_trigger(t_description = 'desc1', t_rule = 'AND(x,OR(y,z))',
                                       t_result= ['x10_on("a3")', '1wire()'])
        trigger2 = self.db.add_trigger(t_description = 'desc2', t_rule = 'OR(x,AND(y,z))',
                                       t_result= ['x10_on("a2")', '1wire()'])
        for trigger in self.db.list_triggers():
            trigger_id = trigger.id
            trigger_del = trigger
            self.db.del_trigger(trigger.id)
            assert trigger_del.id == trigger.id
        assert len(self.db.list_triggers()) == 0
        try:
            self.db.del_trigger(12345678910)
            TestCase.fail(self, "Trigger does not exist, an exception should have been raised")
        except DbHelperException:
            pass


class PersonAndUserAccountsTestCase(GenericTestCase):
    """Test person and user accounts"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_persons(self.db)

    def tearDown(self):
        self.remove_all_persons(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_persons()) == 0
        assert len(self.db.list_user_accounts()) == 0

    def test_add(self):
        person1 = self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                     p_birthdate=datetime.date(1973, 4, 24))
        assert person1.last_name == 'SCHNEIDER'
        print(person1)
        user1 = self.db.add_user_account(a_login='mschneider', a_password='IwontGiveIt',
                                         a_person_id=person1.id, a_is_admin=True)
        print(user1)
        assert user1.person.first_name == 'Marc'
        assert self.db.authenticate('mschneider', 'IwontGiveIt')
        assert not self.db.authenticate('mschneider', 'plop')
        assert not self.db.authenticate('hello', 'boy')
        try:
            self.db.add_user_account(a_login='mschneider', a_password='plop', a_person_id=person1.id)
            TestCase.fail(self, "It shouldn't have been possible to add login %s. It already exists!" % 'mschneider')
        except DbHelperException:
            pass
        try:
            self.db.add_user_account(a_login='mygod', a_password='plop', a_person_id=999999999)
            TestCase.fail(self, "It shouldn't have been possible to add login %s. : associated person does not exist")
        except DbHelperException:
            pass
        person2 = self.db.add_person(p_first_name='Marc', p_last_name='DELAMAIN',
                                     p_birthdate=datetime.date(1981, 4, 24))
        user2 = self.db.add_user_account(a_login='lonely', a_password='boy', a_person_id=person2.id, a_is_admin=True)
        person3 = self.db.add_person(p_first_name='Ali', p_last_name='CANTE')
        assert len(self.db.list_persons()) == 3
        user3 = self.db.add_user_account(a_login='domo', a_password='gik', a_person_id=person3.id, a_is_admin=True)
        user4 = self.db.add_user_account_with_person(
                            a_login='jsteed', a_password='theavengers', a_person_first_name='John',
                            a_person_last_name='STEED', a_person_birthdate=datetime.date(1931, 4, 24),
                            a_is_admin=True, a_skin_used='skins/hat')
        assert user4.login == 'jsteed'
        assert user4.person.first_name == 'John'
        assert user4.person.last_name == 'STEED'
        assert len(self.db.list_user_accounts()) == 4

    def test_update(self):
        person = self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                    p_birthdate=datetime.date(1973, 4, 24))
        person_u = self.db.update_person(p_id=person.id, p_first_name='Marco', p_last_name='SCHNEIDERO',
                                         p_birthdate=datetime.date(1981, 4, 24))
        assert str(person_u.birthdate) == str(datetime.date(1981, 4, 24))
        assert person_u.last_name == 'SCHNEIDERO'
        assert person_u.first_name == 'Marco'
        user_acc = self.db.add_user_account(a_login='mschneider', a_password='IwontGiveIt',
                                            a_person_id=person_u.id, a_is_admin=True)
        assert not self.db.change_password(999999999, 'IwontGiveIt', 'foo')
        assert self.db.change_password(user_acc.id, 'IwontGiveIt', 'OkIWill')
        assert not self.db.change_password(user_acc.id, 'DontKnow', 'foo')

        user_acc_u = self.db.update_user_account(a_id=user_acc.id, a_new_login='mschneider2', a_is_admin=False)
        assert not user_acc_u.is_admin
        try:
            self.db.update_user_account(a_id=user_acc.id, a_person_id=999999999)
            TestCase.fail(self, "An exception should have been raised : person id does not exist")
        except DbHelperException:
            pass
        user_acc_u = self.db.update_user_account_with_person(a_id=user_acc.id, a_login='mschneider3',
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
        person1 = self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                     p_birthdate=datetime.date(1973, 4, 24))
        person2 = self.db.add_person(p_first_name='Monthy', p_last_name='PYTHON',
                                     p_birthdate=datetime.date(1981, 4, 24))
        person3 = self.db.add_person(p_first_name='Alberto', p_last_name='MATE',
                                     p_birthdate=datetime.date(1947, 8, 6))
        user1 = self.db.add_user_account(a_login='mschneider', a_password='IwontGiveIt',
                                         a_person_id=person1.id, a_is_admin=True)
        user2 = self.db.add_user_account(a_login='lonely', a_password='boy',
                                         a_person_id=person2.id, a_is_admin=True)
        assert self.db.get_user_account_by_person(person3.id) is None
        user_acc = self.db.get_user_account(user1.id)
        assert user_acc.login == 'mschneider'
        assert user_acc.person.last_name == 'SCHNEIDER'
        user_acc = self.db.get_user_account_by_login('mschneider')
        assert user_acc is not None
        assert self.db.get_user_account_by_login('mschneider').id == user1.id
        assert self.db.get_user_account_by_login('lucyfer') is None

        user_acc = self.db.get_user_account_by_person(person1.id)
        assert user_acc.login == 'mschneider'
        assert self.db.get_person(person1.id).first_name == 'Marc'
        assert self.db.get_person(person2.id).last_name == 'PYTHON'

    def test_del(self):
        person1 = self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                     p_birthdate=datetime.date(1973, 4, 24))
        person2 = self.db.add_person(p_first_name='Monthy', p_last_name='PYTHON',
                                     p_birthdate=datetime.date(1981, 4, 24))
        person3 = self.db.add_person(p_first_name='Alberto', p_last_name='MATE',
                                     p_birthdate=datetime.date(1947, 8, 6))
        user1 = self.db.add_user_account(a_login='mschneider', a_password='IwontGiveIt', a_person_id=person1.id)
        user2 = self.db.add_user_account(a_login='lonely', a_password='boy', a_person_id=person2.id)
        user3 = self.db.add_user_account(a_login='domo', a_password='gik', a_person_id=person3.id)
        user3_id = user3.id
        user_acc_del = self.db.del_user_account(user3.id)
        assert user_acc_del.id == user3_id
        assert len(self.db.list_persons()) == 3
        l_user = self.db.list_user_accounts()
        assert len(l_user) == 2
        for user in l_user:
            assert user.login != 'domo'
        person1_id = person1.id
        person_del = self.db.del_person(person1.id)
        assert person_del.id == person1_id
        assert len(self.db.list_persons()) == 2
        assert len(self.db.list_user_accounts()) == 1
        try:
            self.db.del_person(12345678910)
            TestCase.fail(self, "Person does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        try:
            self.db.del_user_account(12345678910)
            TestCase.fail(self, "User account does not exist, an exception should have been raised")
        except DbHelperException:
            pass


class UIItemConfigTestCase(GenericTestCase):
    """Test item UI config"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_ui_item_config(self.db)

    def tearDown(self):
        self.remove_all_ui_item_config(self.db)
        del self.db

    def test_empty_list(self):
        assert len(self.db.list_all_ui_item_config()) == 0

    def test_add(self):
        ui_config = self.db.set_ui_item_config('area', 2, 'icon', 'basement')
        assert ui_config.name == 'area'
        assert ui_config.reference == '2'
        assert ui_config.key == 'icon'
        assert ui_config.value == 'basement'
        print(ui_config)
        self.db.set_ui_item_config('room', 1, 'icon', 'kitchen')
        self.db.set_ui_item_config('room', 4, 'icon', 'bathroom')
        self.db.set_ui_item_config('room', 4, 'param_r2', 'value_r2')
        ui_config_list_all = self.db.list_all_ui_item_config()
        assert len(ui_config_list_all) == 4, len(ui_config_list_all)
        assert len(self.db.list_ui_item_config_by_key(ui_item_name='room', ui_item_key='icon')) == 2
        ui_config_list_r = self.db.list_ui_item_config_by_ref(ui_item_name='room', ui_item_reference=4)
        assert len(ui_config_list_r) == 2 \
               and ui_config_list_r[0].name == 'room' \
               and ui_config_list_r[0].reference == '4' \
               and ui_config_list_r[0].key == 'icon' \
               and ui_config_list_r[0].value == 'bathroom' \
               and ui_config_list_r[1].name == 'room' \
               and ui_config_list_r[1].reference == '4' \
               and ui_config_list_r[1].key == 'param_r2' \
               and ui_config_list_r[1].value == 'value_r2', "%s" % ui_config_list_r
        uic = self.db.get_ui_item_config('room', 4, 'param_r2')
        assert uic.value == 'value_r2'
        uic = self.db.get_ui_item_config('area', 2, 'icon')
        assert uic.value == 'basement'
        assert self.db.get_ui_item_config('foo', 13, 'param_a1') is None

    def test_update(self):
        self.db.set_ui_item_config('area', 1, 'icon', 'basement')
        self.db.set_ui_item_config('room', 1, 'icon', 'bathroom')
        self.db.set_ui_item_config('room', 1, 'param_r2', 'value_r2')
        uic = self.db.set_ui_item_config('area', 1, 'icon', 'first_floor')
        assert uic.value == 'first_floor'
        self.db.set_ui_item_config('room', 1, 'icon', 'kitchen')
        assert self.db.get_ui_item_config('room', 1, 'icon').value == 'kitchen'

    def test_list_and_get(self):
        self.db.set_ui_item_config('area', 1, 'icon', 'basement')
        self.db.set_ui_item_config('room', 1, 'icon', 'bathroom')
        self.db.set_ui_item_config('room', 1, 'param_r2', 'value_r2')
        self.db.set_ui_item_config('room', 2, 'icon', 'kitchen')
        assert len(self.db.list_all_ui_item_config()) == 4
        assert len(self.db.list_ui_item_config(ui_item_name='room')) == 3
        assert len(self.db.list_ui_item_config_by_ref(ui_item_name='room', ui_item_reference=1)) == 2
        item=self.db.get_ui_item_config(ui_item_name='room', ui_item_reference=2, ui_item_key='icon')
        assert item.value == 'kitchen'

    def test_del(self):
        self.db.set_ui_item_config('area', 1, 'icon', 'basement')
        self.db.set_ui_item_config('room', 1, 'icon', 'bathroom')
        self.db.set_ui_item_config('room', 1, 'param_r2', 'value_r2')
        self.db.delete_ui_item_config('area', 1, 'icon')
        assert len(self.db.list_all_ui_item_config()) == 2
        assert self.db.get_ui_item_config('room', 1, 'icon') is not None
        self.db.delete_ui_item_config(ui_item_name='room', ui_item_reference=1)
        assert len(self.db.list_all_ui_item_config()) == 0
        assert self.db.get_ui_item_config('area', 1, 'icon') is None
        self.db.set_ui_item_config('area', 2, 'icon', 'first_floor')
        self.db.set_ui_item_config('area', 2, 'pa1', 'va1')
        self.db.set_ui_item_config('room', 2, 'icon', 'kitchen')
        self.db.set_ui_item_config('room', 2, 'pr1', 'vr1')
        self.db.delete_ui_item_config(ui_item_name='area', ui_item_reference=2)
        assert len(self.db.list_ui_item_config(ui_item_name='area')) == 0
        self.db.delete_ui_item_config(ui_item_name='room', ui_item_key='icon')
        ui_item_list = self.db.list_ui_item_config(ui_item_name='room')
        assert len(ui_item_list) == 1
        assert ui_item_list[0].key == 'pr1'


class SystemConfigTestCase(GenericTestCase):
    """Test system config"""

    def setUp(self):
        self.db = DbHelper(use_test_db=True)

    def tearDown(self):
        del self.db

    def test_update(self):
        system_config = self.db.update_system_config(s_simulation_mode=True, s_debug_mode=True)
        print system_config
        assert system_config.simulation_mode
        assert system_config.debug_mode
        system_config = self.db.update_system_config(s_simulation_mode=False)
        assert not system_config.simulation_mode
        system_config = self.db.get_system_config()
        assert system_config.debug_mode


if __name__ == "__main__":
    unittest.main()

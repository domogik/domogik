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
from domogik.common.sql_schema import ActuatorFeature, Area, Device, DeviceUsage, \
                                      DeviceConfig, DeviceStats, DeviceStatsValue, \
                                      DeviceTechnology, DeviceTechnologyConfig, \
                                      DeviceType, UIItemConfig, Room, \
                                      SensorReferenceData, UserAccount, \
                                      SystemConfig, SystemStats, SystemStatsValue, \
                                      Trigger, Person

class GenericTestCase(unittest.TestCase):
    """
    Main class for unit tests
    """

    def has_item(self, item_list, item_name_list):
        """
        Check if a list of names are in a list (with objects having a 'name' attribute)
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
        """
        Remove all areas
        @param db : db API instance
        """
        for area in db.list_areas():
            db.del_area(area.id)

    def remove_all_rooms(self, db):
        """
        Remove all rooms
        @param db : db API instance
        """
        for room in db.list_rooms():
            db.del_room(room.id)

    def remove_all_devices(self, db):
        """
        Remove all devices
        @param db : db API instance
        """
        for device in db.list_devices():
            db.del_device(device.id)

    def remove_all_device_usages(self, db):
        """
        Remove all device usages
        @param db : db API instance
        """
        for du in db.list_device_usages():
            db.del_device_usage(du.id, cascade_delete=True)

    def remove_all_device_types(self, db):
        """
        Remove all device types
        @param db : db API instance
        """
        for dty in db.list_device_types():
            db.del_device_type(dty.id, cascade_delete=True)

    def remove_all_sensor_reference_data(self, db):
        for srd in db.list_sensor_reference_data():
            db.del_sensor_reference_data(srd.id)

    def remove_all_actuator_features(self, db):
        for af in db.list_actuator_features():
            db.del_actuator_feature(af.id)

    def remove_all_device_technology_config(self, db):
        """
        Remove all configurations of device technologies
        @param db : db API instance
        """
        for dtc in db._session.query(DeviceTechnologyConfig).all():
            db._session.delete(dtc)

    def remove_all_device_technologies(self, db):
        """
        Remove all device technologies
        @param db : db API instance
        """
        self.remove_all_device_technology_config(db)
        for dt in db.list_device_technologies():
            db.del_device_technology(dt.id, cascade_delete=True)

    def remove_all_device_stats(self, db):
        """
        Remove all device stats
        @param db : db API instance
        """
        for device in db.list_devices():
            db.del_all_device_stats(device.id)

    def remove_all_triggers(self, db):
        """
        Remove all triggers
        @param db : db API instance
        """
        for trigger in db.list_triggers():
            db.del_trigger(trigger.id)

    def remove_all_persons(self, db):
        """
        Remove all person accounts
        @param db : db API instance
        """
        for person in self.db.list_persons():
            self.db.del_person(person.id)

    def remove_all_user_accounts(self, db):
        """
        Remove all user accounts
        @param db : db API instance
        """
        for user in self.db.list_user_accounts():
            self.db.del_user_account(user.id)

    def remove_all_ui_item_config(self, db):
        """
        Remove all ui configuration parameters of all items (area, room, device)
        @param db : db API instance
        """
        for uic in db.list_all_ui_item_config():
            db.delete_ui_item_config(uic.item_name, uic.item_reference)


class AreaTestCase(GenericTestCase):
    """
    Test areas
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_areas(self.db)

    def tearDown(self):
        self.remove_all_areas(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_areas()) == 0

    def testAdd(self):
        try:
            self.db.add_area(None, None)
            TestCase.fail(self, "An exception should have been raised : \
                          impossible to create an area without a name")
        except DbHelperException:
            pass
        area0 = self.db.add_area('area0','description 0')
        print area0
        assert self.db.list_areas()[0].name == 'area0'

    def testUpdate(self):
        area = self.db.add_area('area0','description 0')
        area_u = self.db.update_area(area.id, 'area1','description 1')
        assert area_u.name == 'area1'
        assert area_u.description == 'description 1'

    def testFetchInformation(self):
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
        area_w_rooms_list = self.db.list_areas_with_rooms()
        for my_area in area_w_rooms_list:
            if my_area.name == 'Basement':
                assert len(my_area.Room) == 3
                for room in my_area.Room:
                    assert room.name in ['Kitchen', 'Bathroom', 'Lounge']
            elif my_area.name == 'First floor':
                assert len(my_area.Room) == 2
                for room in my_area.Room:
                    assert room.name in ['Bedroom1', 'Bedroom2']

    def testDel(self):
        area0 = self.db.add_area('area0','description 0')
        area0_id = area0.id
        area_d = self.db.del_area(area0.id)
        assert not self.has_item(self.db.list_areas(), ['area0'])
        assert area_d.id == area0.id
        try:
            self.db.del_area(12345678910)
            TestCase.fail(self, "Area does not exist, an exception \
                                 should have been raised")
        except DbHelperException:
            pass


class RoomTestCase(GenericTestCase):
    """
    Test rooms
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_rooms(self.db)
        self.remove_all_areas(self.db)

    def tearDown(self):
        self.remove_all_rooms(self.db)
        self.remove_all_areas(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_rooms()) == 0

    def testAdd(self):
        try:
            self.db.add_room(r_name='foo', r_area_id=99999999999,
                             r_description='foo')
            TestCase.fail(self, "An exception should have been raised : \
                          area id does not exist")
        except DbHelperException:
            pass
        room = self.db.add_room(r_name='my_room', r_area_id=None,
                                r_description='my_description')
        print room
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room(r_name='room1', r_description='description 1',
                                 r_area_id=area1.id)
        assert room1.name == 'room1'
        assert room1.description == 'description 1'
        assert room1.area_id == area1.id
        room2 = self.db.add_room(r_name='room2', r_description='description 2',
                                 r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3',
                                 r_area_id=area2.id)
        assert len(self.db.list_rooms()) == 4
        room4 = self.db.add_room(r_name='room4')

    def testUpdate(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room = self.db.add_room(r_name='room1', r_description='description 1',
                                r_area_id=area1.id)
        try:
            self.db.update_room(room.id, r_name='room2',
                                r_description='description 2',
                                r_area_id=99999999999)
            TestCase.fail(self, "An exception should have been raised : \
                          area id does not exist")
        except DbHelperException:
            pass
        room_u = self.db.update_room(room.id, r_name='room2',
                                     r_description='description 2',
                                     r_area_id=area2.id)
        assert room_u.name == 'room2'
        assert room_u.description == 'description 2'
        assert room_u.area_id == area2.id
        room_u = self.db.update_room(room.id, r_area_id='')
        assert room_u.area_id == None

    def testDel(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room(r_name='room1', r_description='description 1',
                                 r_area_id=area1.id)
        room2 = self.db.add_room(r_name='room2', r_description='description 2',
                                 r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3',
                                 r_area_id=area2.id)
        room1_id = room1.id
        room_deleted = self.db.del_room(room1.id)
        assert not self.has_item(self.db.list_rooms(), ['room1'])
        assert self.has_item(self.db.list_rooms(), ['room2', 'room3'])
        assert room_deleted.id == room1_id
        try:
            self.db.del_room(12345678910)
            TestCase.fail(self, "Room does not exist, an exception \
                                 should have been raised")
        except DbHelperException:
            pass

    def testListAndGet(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room(r_name='room1', r_description='description 1',
                                 r_area_id=area1.id)
        assert self.db.get_room_by_name('Room1').name == 'room1'

        area2 = self.db.add_area('area2','description 2')
        room2 = self.db.add_room(r_name='room2', r_description='description 2',
                                 r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3',
                                 r_area_id=area2.id)
        assert len(self.db.get_all_rooms_of_area(area1.id)) == 2
        assert len(self.db.get_all_rooms_of_area(area2.id)) == 1

        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        du1 = self.db.add_device_usage('du1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        device1 = self.db.add_device(d_name='Toaster', d_address='A1',
                    d_type_id=dty1.id, d_usage_id=du1.id,
                    d_room_id=room1.id, d_description='My new toaster')
        device2 = self.db.add_device(d_name='Washing machine', d_address='A1',
                    d_type_id=dty1.id, d_usage_id=du1.id,
                    d_room_id=room1.id, d_description='Laden')
        device3 = self.db.add_device(d_name='Mixer', d_address='A2',
                    d_type_id=dty1.id, d_usage_id=du1.id,
                    d_room_id=room2.id, d_description='Moulinex')
        for room in self.db.list_rooms_with_devices():
            if room.id == room1.id:
                assert len(room.Device) == 2
            if room.id == room2.id:
                assert len(room.Device) == 1
        #print room2
        #print room3
        #assert len(room3.Device) == 0


class DeviceUsageTestCase(GenericTestCase):
    """
    Test device usages
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_usages(self.db)

    def tearDown(self):
        self.remove_all_device_usages(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_device_usages()) == 0

    def testAdd(self):
        du1 = self.db.add_device_usage('du1')
        print du1
        assert du1.name == 'du1'
        du2 = self.db.add_device_usage('du2')
        assert len(self.db.list_device_usages()) == 2
        assert self.has_item(self.db.list_device_usages(), ['du1', 'du2'])

    def testUpdate(self):
        du = self.db.add_device_usage('du1')
        du_u = self.db.update_device_usage(du_id=du.id, du_name='du2',
                                           du_description='description 2')
        assert du_u.name == 'du2'
        assert du_u.description == 'description 2'

    def testFetchInformation(self):
        du1 = self.db.add_device_usage('du1')
        assert self.db.get_device_usage_by_name('Du1').name == 'du1'

    def testDel(self):
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        du2_id = du2.id
        du_del = self.db.del_device_usage(du2.id)
        assert self.has_item(self.db.list_device_usages(), ['du1'])
        assert not self.has_item(self.db.list_device_usages(), ['du2'])
        assert du_del.id == du2_id
        try:
            self.db.del_device_usage(12345678910)
            TestCase.fail(self, "Device usage does not exist, an exception \
                                 should have been raised")
        except DbHelperException:
            pass

class DeviceTypeTestCase(GenericTestCase):
    """
    Test device types
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_types(self.db)

    def tearDown(self):
        self.remove_all_device_types(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_device_types()) == 0

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        try:
            self.db.add_device_type(dty_name='x10 Switch',
                                    dty_description='desc1', dt_id=99999999999)
            TestCase.fail(self, "An exception should have been raised : \
                          device techno id does not exist")
        except DbHelperException:
            pass
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        print dty1
        assert dty1.name == 'x10 Switch'
        assert dty1.description == 'desc1'
        assert dty1.technology_id == dt1.id
        dty2 = self.db.add_device_type(dty_name='x10 Dimmer',
                                       dty_description='desc2', dt_id=dt1.id)
        assert len(self.db.list_device_types()) == 2
        assert self.has_item(self.db.list_device_types(), ['x10 Switch', 'x10 Dimmer'])

    def testUpdate(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dt2 = self.db.add_device_technology(u'PLCBus', 'desc dt2')
        dty = self.db.add_device_type(dty_name='x10 Switch',
                                      dty_description='desc1', dt_id=dt1.id)
        try:
            self.db.update_device_type(dty_id=dty.id, dty_name='x10 Dimmer',
                                       dt_id=99999999999)
            TestCase.fail(self, "An exception should have been raised : \
                          device techno id does not exist")
        except DbHelperException:
            pass
        dty_u = self.db.update_device_type(dty_id=dty.id, dty_name='x10 Dimmer',
                                           dt_id=dt2.id, dty_description='desc2')
        assert dty_u.name == 'x10 Dimmer'
        assert dty_u.description == 'desc2'
        assert dty_u.technology_id == dt2.id

    def testFetchInformation(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        assert self.db.get_device_type_by_name('x10 switch').name == 'x10 Switch'

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='x10 Dimmer', dt_id=dt1.id)
        dty2_id = dty2.id
        dty_del = self.db.del_device_type(dty2.id)
        assert self.has_item(self.db.list_device_types(), ['x10 Switch'])
        assert not self.has_item(self.db.list_device_usages(), ['x10 Dimmer'])
        assert dty_del.id == dty2_id
        try:
            self.db.del_device_type(12345678910)
            TestCase.fail(self, "Device type does not exist, an exception \
                                 should have been raised")
        except DbHelperException:
            pass

class SensorReferenceDataTestCase(GenericTestCase):
    """
    Test sensor reference data
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_sensor_reference_data(self.db)

    def tearDown(self):
        self.remove_all_sensor_reference_data(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_sensor_reference_data()) == 0

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'1wire', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='1wire.Temperature',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='1wire.Voltmeter',
                                       dty_description='desc2', dt_id=dt1.id)
        try:
            self.db.add_sensor_reference_data(srd_name='Temperature',
                    srd_value='number', dty_id=99999999999, srd_unit='degreeC',
                    srd_stat_key='key1')
            TestCase.fail(self, "An exception should have been raised : \
                          device type id does not exist")
        except DbHelperException:
            pass
        srd1 = self.db.add_sensor_reference_data(srd_name='Temperature',
                    srd_value='number', dty_id=dty1.id, srd_unit='degreeC',
                    srd_stat_key='key1')
        print srd1
        assert srd1.name == 'Temperature'
        assert srd1.value == 'number'
        assert srd1.device_type_id == dty1.id
        assert srd1.unit == 'degreeC'
        assert srd1.stat_key == 'key1'
        srd2 = self.db.add_sensor_reference_data(srd_name='Voltage',
                    srd_value='number', dty_id=dty2.id, srd_unit='V',
                    srd_stat_key='key2')
        assert len(self.db.list_sensor_reference_data()) == 2
        assert self.has_item(self.db.list_sensor_reference_data(), \
               ['Temperature', 'Voltage'])

    def testUpdate(self):
        dt1 = self.db.add_device_technology(u'1wire', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='1wire.Temperature',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='1wire.Voltmeter',
                                       dty_description='desc2', dt_id=dt1.id)
        srd = self.db.add_sensor_reference_data(srd_name='Temperature',
                    srd_value='number', dty_id=dty1.id, srd_unit='degreeC',
                    srd_stat_key='key1')
        srd_u = self.db.update_sensor_reference_data(srd_id=srd.id, srd_name='Voltage',
                    srd_value='number', dty_id=dty2.id, srd_unit='V',
                    srd_stat_key='key2')
        try:
            self.db.update_sensor_reference_data(srd_id=srd.id, srd_name='Voltage',
                    srd_value='number', dty_id=99999999999, srd_unit='V',
                    srd_stat_key='key2')
            TestCase.fail(self, "An exception should have been raised : \
                          device type id does not exist")
        except DbHelperException:
            pass
        assert srd_u.name == 'Voltage'
        assert srd_u.value == 'number'
        assert srd_u.device_type_id == dty2.id
        assert srd_u.unit == 'V'
        assert srd_u.stat_key == 'key2'

    def testFetchInformation(self):
        dt1 = self.db.add_device_technology(u'1wire', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='1wire.Temperature',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='1wire.Voltmeter',
                                       dty_description='desc2', dt_id=dt1.id)
        srd1 = self.db.add_sensor_reference_data(srd_name='Temperature',
                    srd_value='number', dty_id=dty1.id, srd_unit='degreeC',
                    srd_stat_key='key1')
        srd2 = self.db.add_sensor_reference_data(srd_name='Voltage',
                    srd_value='number', dty_id=dty2.id, srd_unit='V',
                    srd_stat_key='key2')
        assert self.db.get_sensor_reference_data_by_name('temperature').unit == srd1.unit

    def testDel(self):
        dt1 = self.db.add_device_technology(u'1wire', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='1wire.Temperature',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='1wire.Voltmeter',
                                       dty_description='desc2', dt_id=dt1.id)
        srd1 = self.db.add_sensor_reference_data(srd_name='Temperature',
                    srd_value='number', dty_id=dty1.id, srd_unit='degreeC',
                    srd_stat_key='key1')
        srd1_id = srd1.id
        srd2 = self.db.add_sensor_reference_data(srd_name='Voltage',
                    srd_value='number', dty_id=dty2.id, srd_unit='V',
                    srd_stat_key='key2')
        srd_del = self.db.del_sensor_reference_data(srd1.id)
        assert self.has_item(self.db.list_sensor_reference_data(), ['Voltage'])
        assert not self.has_item(self.db.list_device_usages(), ['Temperature'])
        assert srd_del.id == srd1_id
        try:
            self.db.del_sensor_reference_data(12345678910)
            TestCase.fail(self, "SensorReferenceData does not exist, an \
                                 exception should have been raised")
        except DbHelperException:
            pass

class ActuatorFeatureTestCase(GenericTestCase):
    """
    Test actuator features
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_actuator_features(self.db)

    def tearDown(self):
        self.remove_all_actuator_features(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_actuator_features()) == 0

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'PLCBus', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='PLCBus Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='PLCBus.Dimmer',
                                       dty_description='desc2', dt_id=dt1.id)
        try:
            self.db.add_actuator_feature(af_name='Dimmer',
                    af_value='range', dty_id=99999999999, af_unit='Percent',
                    af_configurable_states='0,100,10', af_return_confirmation=True)
            TestCase.fail(self, "An exception should have been raised : \
                          device type id does not exist")
        except DbHelperException:
            pass
        af1 = self.db.add_actuator_feature(af_name='Dimmer',
                    af_value='range', dty_id=dty2.id, af_unit='Percent',
                    af_configurable_states='0,100,10', af_return_confirmation=True)
        print af1
        assert af1.name == 'Dimmer'
        assert af1.value == 'range'
        assert af1.device_type_id == dty2.id
        assert af1.unit == 'Percent'
        assert af1.configurable_states == '0,100,10'
        assert af1.return_confirmation == True
        af2 = self.db.add_actuator_feature(af_name='Switch',
                    af_value='binary', dty_id=dty1.id,
                    af_configurable_states='off/on', af_return_confirmation=True)
        assert len(self.db.list_actuator_features()) == 2
        assert self.has_item(self.db.list_actuator_features(), ['Switch', 'Dimmer'])

    def testUpdate(self):
        dt1 = self.db.add_device_technology(u'PLCBus', 'desc dt1')
        dt2 = self.db.add_device_technology(u'x10', 'desc dt2')
        dty1 = self.db.add_device_type(dty_name='PLCBus Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='x10.Dimmer',
                                       dty_description='desc2', dt_id=dt2.id)
        af = self.db.add_actuator_feature(af_name='Switch',
                    af_value='binary', dty_id=dty1.id,
                    af_configurable_states='off/on', af_return_confirmation=True)
        try:
            self.db.update_actuator_feature(af_id=af.id, af_name='Dimmer',
                    af_value='range', dty_id=99999999999, af_unit='Percent',
                    af_configurable_states='0,100,10', af_return_confirmation=False)
            TestCase.fail(self, "An exception should have been raised : \
                          device type id does not exist")
        except DbHelperException:
            pass
        af_u = self.db.update_actuator_feature(af_id=af.id, af_name='Dimmer',
                    af_value='range', dty_id=dty2.id, af_unit='Percent',
                    af_configurable_states='0,100,10', af_return_confirmation=False)
        assert af_u.name == 'Dimmer'
        assert af_u.value == 'range'
        assert af_u.device_type_id == dty2.id
        assert af_u.unit == 'Percent'
        assert af_u.configurable_states == '0,100,10'
        assert af_u.return_confirmation == False

    def testFetchInformation(self):
        dt1 = self.db.add_device_technology(u'PLCBus', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='PLCBus Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='PLCBus.Dimmer',
                                       dty_description='desc2', dt_id=dt1.id)
        af1 = self.db.add_actuator_feature(af_name='Dimmer',
                    af_value='range', dty_id=dty2.id, af_unit='Percent',
                    af_configurable_states='0,100,10', af_return_confirmation=True)
        af2 = self.db.add_actuator_feature(af_name='Switch',
                    af_value='binary', dty_id=dty1.id,
                    af_configurable_states='off/on', af_return_confirmation=True)
        assert self.db.get_actuator_feature_by_name('dimmer').unit == af1.unit

    def testDel(self):
        dt1 = self.db.add_device_technology(u'PLCBus', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='PLCBus Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='PLCBus.Dimmer',
                                       dty_description='desc2', dt_id=dt1.id)
        af1 = self.db.add_actuator_feature(af_name='Dimmer',
                    af_value='range', dty_id=dty2.id, af_unit='Percent',
                    af_configurable_states='0,100,10', af_return_confirmation=True)
        af2 = self.db.add_actuator_feature(af_name='Switch',
                    af_value='binary', dty_id=dty1.id,
                    af_configurable_states='off/on', af_return_confirmation=True)
        af1_id = af1.id
        af_del = self.db.del_actuator_feature(af1.id)
        assert self.has_item(self.db.list_actuator_features(), ['Switch'])
        assert not self.has_item(self.db.list_actuator_features(), ['Dimmer'])
        assert af_del.id == af1_id
        try:
            self.db.del_actuator_feature(12345678910)
            TestCase.fail(self, "ActuatorFeature does not exist, an \
                                 exception should have been raised")
        except DbHelperException:
            pass

class DeviceTechnologyTestCase(GenericTestCase):
    """
    Test device technologies
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_technologies(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_device_technologies()) == 0

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        print dt1
        assert dt1.name == 'x10'
        assert dt1.description == 'desc dt1'
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3')
        assert len(self.db.list_device_technologies()) == 3
        assert self.has_item(self.db.list_device_technologies(),
                             [u'x10', u'1wire', u'PLCBus'])

    def testUpdate(self):
        dt = self.db.add_device_technology(u'x10', 'desc dt1')
        dt_u = self.db.update_device_technology(dt.id, u'PLCBus', 'desc dt2')
        assert dt_u.name == 'PLCBus'
        assert dt_u.description == 'desc dt2'

    def testFetchInformation(self):
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2')
        assert self.db.get_device_technology_by_name(u'1Wire').name == u'1wire'

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2')
        dt_del = dt2
        dt2_id = dt2.id
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3')
        self.db.del_device_technology(dt2.id)
        assert self.has_item(self.db.list_device_technologies(), [u'x10', u'PLCBus'])
        assert not self.has_item(self.db.list_device_technologies(), [u'1wire'])
        assert dt_del.id == dt2_id
        try:
            self.db.del_device_technology(12345678910)
            TestCase.fail(self, "Device technology does not exist, an exception \
                                 should have been raised")
        except DbHelperException:
            pass

class DeviceTechnologyConfigTestCase(GenericTestCase):
    """
    Test device technology configurations
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_technology_config(self.db)
        self.remove_all_device_technologies(self.db)

    def tearDown(self):
        self.remove_all_device_technology_config(self.db)
        self.remove_all_device_technologies(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_all_device_technology_config()) == 0

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3')
        try:
            self.db.add_device_technology_config(99999999999, 'key1_1', 'val1_1',
                                                 'desc1')
            TestCase.fail(self, "An exception should have been raised : \
                          device technology id does not exist")
        except DbHelperException:
            pass
        dtc1_1 = self.db.add_device_technology_config(dt1.id, 'key1_1', 'val1_1',
                                                      'desc1')
        print dtc1_1
        assert dtc1_1.technology_id == dt1.id
        assert dtc1_1.key == 'key1_1'
        assert dtc1_1.value == 'val1_1'
        assert dtc1_1.description == 'desc1'
        dtc1_2 = self.db.add_device_technology_config(dt1.id, 'key1_2', 'val1_2',
                                                     'desc2')
        dtc3_1 = self.db.add_device_technology_config(dt3.id, 'key3_1', 'val3_1',
                                                      'desc3')
        dtc3_2 = self.db.add_device_technology_config(dt3.id, 'key3_2', 'val3_2',
                                                      'desc4')
        dtc3_3 = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3',
                                                      'desc5')
        try:
            dtc = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3',
                                                       'desc')
            TestCase.fail(self, "It shouldn't have been possible to add 'key3_3'\
                          for device technology %s : it already exists" % dt3.id)
        except DbHelperException:
            pass
        assert len(self.db.list_device_technology_config(dt1.id)) == 2, \
                "%s devices technologies config found, instead of 2 " \
                % len(self.db.list_device_technology_config(dt1.id))
        assert len(self.db.list_device_technology_config(dt3.id)) == 3, \
                "%s devices technologies config found, instead of 3 " \
                % len(self.db.list_device_technology_config(dt3.id))

    def testUpdate(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dt2 = self.db.add_device_technology(u'PLCBus', 'desc dt2')
        dtc = self.db.add_device_technology_config(dt1.id, 'key1', 'val1', 'desc1')
        dtc_u = self.db.update_device_technology_config(dtc.id, dt_id=dt2.id,
                      dtc_key='key2', dtc_value='val2', dtc_description='desc2')
        assert dtc_u.technology_id == dt2.id
        assert dtc_u.key == 'key2'
        assert dtc_u.value == 'val2'
        assert dtc_u.description == 'desc2'

    def testGet(self):
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3')
        dtc3_1 = self.db.add_device_technology_config(dt3.id, 'key3_1', 'val3_1',
                                                      'desc3_1')
        dtc3_2 = self.db.add_device_technology_config(dt3.id, 'key3_2', 'val3_2',
                                                      'desc3_2')
        dtc3_3 = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3',
                                                      'desc3_3')
        dtc = self.db.get_device_technology_config(dt3.id, 'key3_2')
        assert dtc.value == 'val3_2'

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3')
        dtc1_1 = self.db.add_device_technology_config(dt1.id, 'key1_1', 'val1_1',
                                                      'desc1')
        dtc1_2 = self.db.add_device_technology_config(dt1.id, 'key1_2', 'val1_2',
                                                      'desc2')
        dtc3_1 = self.db.add_device_technology_config(dt3.id, 'key3_1', 'val3_1',
                                                      'desc3')
        dtc3_2 = self.db.add_device_technology_config(dt3.id, 'key3_2', 'val3_2',
                                                      'desc4')
        dtc3_3 = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3',
                                                      'desc5')
        dtc3_2_id = dtc3_2.id
        dtc_del = self.db.del_device_technology_config(dtc3_2.id)
        assert self.db.get_device_technology_config(dt3.id, 'key3_2') == None
        assert dtc_del.id == dtc3_2_id
        try:
            self.db.del_device_technology_config(12345678910)
            TestCase.fail(self, "Device technology config does not exist, \
                                 an exception should have been raised")
        except DbHelperException:
            pass

class DeviceTestCase(GenericTestCase):
    """
    Test device
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_devices(self.db)

    def tearDown(self):
        self.remove_all_devices(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_devices()) == 0

    def testAdd(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        du1 = self.db.add_device_usage('du1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        try:
            self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = 9999999999, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1')
            TestCase.fail(self, "Device type does not exist, \
                                 an exception should have been raised")
            self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = 9999999999999,
                    d_room_id = room1.id, d_description = 'desc1')
            TestCase.fail(self, "Device usage does not exist, \
                                 an exception should have been raised")
            self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = 9999999999999, d_description = 'desc1')
            TestCase.fail(self, "Room does not exist, \
                                 an exception should have been raised")
        except DbHelperException:
            pass
        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1')
        print device1
        assert len(self.db.list_devices()) == 1, "Device was NOT added"
        device2 = self.db.add_device(d_name='device2', d_address = 'A2',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1')
        assert len(self.db.list_devices()) == 2
        # TODO see if these methods are still used
        # assert device1.is_lamp(), "device1.is_lamp() returns False.
        # Should have returned True"
        # assert not device1.is_appliance(), "device1.is_appliance()
        # returns True. Should have returned False"

    def testListAndGet(self):
        area1 = self.db.add_area('Basement','description 1')
        room1 = self.db.add_room('Kitchen', area1.id)
        room2 = self.db.add_room('Bathroom', area1.id)
        dt1 = self.db.add_device_technology(u'x10', 'x10 device type')
        dt2 = self.db.add_device_technology(u'PLCBus', 'PLCBus device type')
        du1 = self.db.add_device_usage('Appliance')
        dty1 = self.db.add_device_type(dty_name='x10 Switch', dt_id=dt1.id,
                                       dty_description='My beautiful switch')
        dty2 = self.db.add_device_type(dty_name='PLCBus Switch', dt_id=dt2.id,
                                       dty_description='Another beautiful switch')
        device1 = self.db.add_device(d_name='Toaster', d_address='A1',
                    d_type_id=dty1.id, d_usage_id=du1.id,
                    d_room_id=room1.id, d_description='My new toaster')
        device2 = self.db.add_device(d_name='Washing machine', d_address='A1',
                    d_type_id=dty2.id, d_usage_id=du1.id,
                    d_room_id=room1.id, d_description='Laden')
        device3 = self.db.add_device(d_name='Mixer', d_address='A2',
                    d_type_id=dty2.id, d_usage_id=du1.id,
                    d_room_id=room1.id, d_description='Moulinex')
        search_dev1 =self.db.get_device_by_technology_and_address(dt1.name, 'A1')
        assert search_dev1.name == 'Toaster'
        search_dev2 =self.db.get_device_by_technology_and_address(dt1.name, 'A2')
        assert search_dev2 == None

    def testUpdate(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage('du1')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1')
        device_id = device1.id
        try:
            self.db.update_device(d_id = device1.id, d_type_id = 9999999999)
            TestCase.fail(self, "Device type does not exist, \
                                 an exception should have been raised")
            self.db.update_device(d_id = device1.id, d_usage_id = 9999999999999)
            TestCase.fail(self, "Device usage does not exist, \
                                 an exception should have been raised")
            self.db.update_device(d_id = device1.id, d_room_id = 9999999999999)
            TestCase.fail(self, "Room does not exist, \
                                 an exception should have been raised")
        except DbHelperException:
            pass
        device1 = self.db.update_device(d_id = device1.id,
                                        d_description = 'desc2', d_reference='A1')
        device1 = self.db.get_device(device_id)
        assert device1.description == 'desc2'
        assert device1.reference == 'A1'
        device1 = self.db.update_device(d_id = device1.id, d_reference='',
                                        d_room_id='')
        assert device1.reference == None
        assert device1.room_id == None

    def testFindAndSearch(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room('room1', area1.id)
        room2 = self.db.add_room('room2', area2.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        dty2 = self.db.add_device_type(dty_name='x10 Dimmer',
                                       dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1')
        device2 = self.db.add_device(d_name='device2', d_address='A2',
                    d_type_id = dty2.id, d_usage_id=du1.id, d_room_id=room1.id)
        device3 = self.db.add_device(d_name='device3', d_address='A3',
                    d_type_id = dty2.id, d_usage_id=du2.id, d_room_id=room2.id)

        assert len(self.db.list_devices()) == 3
        assert len(self.db.get_all_devices_of_room(room1.id)) == 2
        assert len(self.db.get_all_devices_of_room(room2.id)) == 1
        assert len(self.db.get_all_devices_of_area(area1.id)) == 2
        assert len(self.db.get_all_devices_of_area(area2.id)) == 1

        assert len(self.db.search_devices({'usage_id':du1.id,
                                          'room_id':room1.id})) == 2
        assert len(self.db.search_devices({'address':'A2'})) == 1
        assert len(self.db.search_devices({'address':'A1544'})) == 0

        assert len(self.db.find_devices(None, None)) == 3
        assert len(self.db.find_devices([], [])) == 3
        assert len(self.db.find_devices([room1.id, room2.id],
                                        [du1.id, du2.id])) == 3
        assert len(self.db.find_devices([room1.id], [du1.id, du2.id])) == 2
        assert len(self.db.find_devices([room2.id], None)) == 1
        assert len(self.db.find_devices([room2.id], [])) == 1
        assert len(self.db.find_devices([room1.id], [du2.id])) == 0
        assert len(self.db.find_devices([room1.id, room2.id], [du2.id])) == 1

    def testDel(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room('room1', area1.id)
        room2 = self.db.add_room('room2', area2.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1')
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1')
        device2 = self.db.add_device(d_name='device2', d_address='A2',
                    d_type_id = dty1.id, d_usage_id=du1.id, d_room_id=room1.id)
        device3 = self.db.add_device(d_name='device3', d_address='A3',
                    d_type_id = dty1.id, d_usage_id=du2.id, d_room_id=room2.id)
        device_del = device2
        device2_id = device2.id
        self.db.del_device(device2.id)
        assert len(self.db.list_devices()) == 2
        assert self.db.list_devices()[0].address == 'A1'
        assert device_del.id == device2.id
        try:
            self.db.del_device(12345678910)
            TestCase.fail(self, "Device does not exist, an exception should \
                          have been raised")
        except DbHelperException:
            pass


class DeviceStatsTestCase(GenericTestCase):
    """
    Test device stats
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_device_stats(self.db)

    def tearDown(self):
        self.remove_all_device_stats(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_all_device_stats()) == 0

    def testAdd(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10")
        du1 = self.db.add_device_usage("lighting")
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device2 = self.db.add_device(d_name='device2', d_address = "A2",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device3 = self.db.add_device(d_name='device3', d_address = "A3",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device4 = self.db.add_device(d_name='device4', d_address = "A4",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1.id, now,
                                            {'val1': '10', 'val2': '10.5' })
        print d_stat1_1
        try:
            self.db.add_device_stat(99999999999, now,
                                    {'val1': '10', 'val2': '10.5' })
            TestCase.fail(self, "An exception should have been raised : \
                          device id does not exist")
        except DbHelperException:
            pass
        d_stat1_2 = self.db.add_device_stat(device1.id,
                                            now + datetime.timedelta(seconds=1),
                                            {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2.id, now,
                                            {'val1': '40', 'val2': '41' })
        d_stat3_1 = self.db.add_device_stat(device3.id, now,
                                            {'val1': '100', 'val2': '101' })
        assert len(self.db.list_device_stats(device1.id)) == 2
        assert len(self.db.list_device_stats(device2.id)) == 1
        assert self.db.device_has_stats(device1.id)
        assert not self.db.device_has_stats(device4.id)

    def testLastStatOfOneDevice(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10")
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1",
                                     d_type_id = dty1.id, d_usage_id = du1.id,
                                     d_room_id = room1.id)
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1.id, now,
                                            {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1.id,
                                            now + datetime.timedelta(seconds=1),
                                            {'val1': '11', 'val2': '12' })

        stat = self.db.get_last_stat_of_device(device1.id)
        dsv = self.db.list_device_stats_values(stat.id)
        for item in dsv:
            if item.name == 'val1':
                assert item.value == '11'
            elif item.name == 'val2':
                assert item.value == '12'

    def testLastStatOfDevices(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10")
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device2 = self.db.add_device(d_name='device2', d_address = "A2",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device3 = self.db.add_device(d_name='device3', d_address = "A3",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device4 = self.db.add_device(d_name='device4', d_address = "A4",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1.id,
                                            now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1.id,
                                            now + datetime.timedelta(seconds=1),
                                            {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2.id,
                                            now, {'val1': '40', 'val2': '41' })
        d_stat3_1 = self.db.add_device_stat(device3.id,
                                            now, {'val1': '100', 'val2': '101' })
        #l_stats = self.db.list_device_stats(device1.id)

        l_stats = self.db.get_last_stat_of_devices([device1.id, device2.id])
        assert len(l_stats) == 2
        device_id_list = []
        for stat in l_stats:
            device_id_list.append(stat.device_id)
            if stat.device_id == device1.id:
                # Make sure we get the LAST stat for device1
                dsv = self.db.list_device_stats_values(stat.id)
                value_list = []
                for item in dsv:
                    value_list.append(item.value)
                assert '11' in value_list and '12' in value_list
        assert device1.id in device_id_list
        assert device2.id in device_id_list

    def testDel(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10")
        dty1 = self.db.add_device_type(dty_name='x10 Switch',
                                       dty_description='desc1', dt_id=dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device2 = self.db.add_device(d_name='device2', d_address = "A2",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1.id,
                                            now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1.id,
                                            now + datetime.timedelta(seconds=1),
                                            {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2.id, now,
                                            {'val1': '40', 'val2': '41' })
        l_stats = self.db.list_device_stats(device1.id)
        d_stats_list_d = self.db.del_all_device_stats(device1.id)
        assert len(d_stats_list_d) == len(l_stats)
        l_stats = self.db.list_device_stats(device1.id)
        assert len(l_stats) == 0
        l_stats = self.db.list_device_stats(device2.id)
        assert len(l_stats) == 1


class TriggersTestCase(GenericTestCase):
    """
    Test triggers
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_triggers(self.db)

    def tearDown(self):
        self.remove_all_triggers(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_triggers()) == 0

    def testAdd(self):
        trigger1 = self.db.add_trigger(t_description='desc1',
                                       t_rule='AND(x,OR(y,z))',
                                       t_result=['x10_on("a3")','1wire()'])
        print trigger1
        trigger2 = self.db.add_trigger(t_description = 'desc2',
                                       t_rule='OR(x,AND(y,z))',
                                       t_result=['x10_on("a2")','1wire()'])
        assert len(self.db.list_triggers()) == 2
        assert self.db.get_trigger(trigger1.id).description == 'desc1'

    def testUpdate(self):
        trigger = self.db.add_trigger(t_description='desc1', t_rule='AND(x,OR(y,z))',
                                      t_result=['x10_on("a3")','1wire()'])
        trigger_u = self.db.update_trigger(t_id=trigger.id, t_description='desc2',
                                      t_rule='OR(x,AND(y,z))',
                                      t_result=['x10_on("a2")','1wire()'])
        assert trigger_u.description == 'desc2'
        assert trigger_u.rule == 'OR(x,AND(y,z))'
        assert trigger_u.result == 'x10_on("a2");1wire()'

    def testDel(self):
        trigger1 = self.db.add_trigger(t_description = 'desc1',
                                       t_rule = 'AND(x,OR(y,z))',
                                       t_result= ['x10_on("a3")','1wire()'])
        trigger2 = self.db.add_trigger(t_description = 'desc2',
                                       t_rule = 'OR(x,AND(y,z))',
                                       t_result= ['x10_on("a2")','1wire()'])
        for trigger in self.db.list_triggers():
            trigger_id = trigger.id
            trigger_del = trigger
            self.db.del_trigger(trigger.id)
            assert trigger_del.id == trigger.id
        assert len(self.db.list_triggers()) == 0
        try:
            self.db.del_trigger(12345678910)
            TestCase.fail(self, "Trigger does not exist, an exception should \
                                 have been raised")
        except DbHelperException:
            pass


class PersonAndUserAccountsTestCase(GenericTestCase):
    """
    Test person and user accounts
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_persons(self.db)
        self.remove_all_user_accounts(self.db)

    def tearDown(self):
        self.remove_all_persons(self.db)
        self.remove_all_user_accounts(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_user_accounts()) == 0
        assert len(self.db.list_persons()) == 0

    def testAdd(self):
        user1 = self.db.add_user_account(a_login='mschneider',
                                         a_password='IwontGiveIt',
                                         a_is_admin=True)
        assert self.db.authenticate('mschneider', 'IwontGiveIt')
        assert not self.db.authenticate('mschneider', 'plop')
        assert not self.db.authenticate('hello', 'boy')
        user1 = self.db.get_user_account_by_login_and_pass('mschneider',
                                                           'IwontGiveIt')
        assert user1 is not None
        assert user1.login == 'mschneider'
        assert user1.password == None
        try:
            self.db.add_user_account(a_login='mschneider', a_password='plop',
                                     a_is_admin = True)
            TestCase.fail(self, "It shouldn't have been possible to add \
                          login %s. It already exists!" % 'mschneider')
        except DbHelperException:
            pass
        user2 = self.db.add_user_account(a_login='lonely', a_password='boy',
                                         a_is_admin=True, a_skin_used='myskin')
        user3 = self.db.add_user_account(a_login='domo', a_password='gik',
                                         a_is_admin=True)
        for user_acc in self.db.list_user_accounts():
            assert user_acc.password == None
        person1 = self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                     p_birthdate=datetime.date(1973, 4, 24),
                                     p_user_account_id = user1.id)
        try:
            self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                               p_birthdate=datetime.date(1973, 4, 24),
                               p_user_account_id=99999999999)
            TestCase.fail(self, "An exception should have been raised : \
                          account id does not exist")
        except DbHelperException:
            pass
        person2 = self.db.add_person(p_first_name='Monthy', p_last_name='PYTHON',
                                     p_birthdate=datetime.date(1981, 4, 24))
        assert len(self.db.list_persons()) == 2
        assert len(self.db.list_user_accounts()) == 3

    def testUpdate(self):
        user_acc = self.db.add_user_account(a_login='mschneider',
                                            a_password='IwontGiveIt',
                                            a_is_admin=True)
        user_acc_u = self.db.update_user_account(
                        a_id=user_acc.id,
                        a_new_login='mschneider2', a_password='ItWasWrong',
                        a_is_admin=False)
        user_acc_msc = self.db.get_user_account_by_login_and_pass(
                        'mschneider2', 'ItWasWrong')
        assert user_acc_msc is not None
        assert user_acc_u.is_admin == False
        person = self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                    p_birthdate=datetime.date(1973, 4, 24),
                                    p_user_account_id=user_acc.id)
        person_u = self.db.update_person(p_id=person.id, p_first_name='Marco',
                                         p_last_name='SCHNEIDERO',
                                         p_birthdate=datetime.date(1981, 4, 24),
                                         p_user_account_id=user_acc_u.id)
        try:
            self.db.update_person(p_id=person.id,
                                  p_user_account_id=99999999999)
            TestCase.fail(self, "An exception should have been raised : \
                          account id does not exist")
        except DbHelperException:
            pass
        assert person_u.first_name == 'Marco'
        assert person_u.last_name == 'SCHNEIDERO'
        assert person_u.birthdate == datetime.date(1981, 4, 24)
        assert person_u.user_account_id == user_acc_u.id
        person_u = self.db.update_person(p_id=person.id, p_user_account_id='')
        assert person_u.user_account_id == None

    def testGet(self):
        user1 = self.db.add_user_account(a_login='mschneider',
                                         a_password='IwontGiveIt', a_is_admin=True)
        user2 = self.db.add_user_account(a_login='lonely', a_password='boy',
                                         a_is_admin = True, a_skin_used='myskin')
        user3 = self.db.add_user_account(a_login='domo', a_password='gik',
                                         a_is_admin=True)
        person1 = self.db.add_person(p_first_name='Marc', p_last_name='SCHNEIDER',
                                     p_birthdate=datetime.date(1973, 4, 24),
                                     p_user_account_id = user1.id)
        person2 = self.db.add_person(p_first_name='Monthy',
                                     p_last_name='PYTHON',
                                     p_birthdate=datetime.date(1981, 4, 24))
        user_acc = self.db.get_user_account(user1.id)
        assert user_acc.login == 'mschneider'
        assert user_acc.password == None
        user_acc = self.db.get_user_account_by_login('mschneider')
        assert user_acc is not None
        assert user_acc.password == None
        assert self.db.get_user_account_by_login('mschneider').id == user1.id
        assert self.db.get_user_account_by_login('lucyfer') is None

        user_acc = self.db.get_user_account_by_person(person1.id)
        assert user_acc.login == 'mschneider'
        assert user_acc.password == None
        assert self.db.get_person(person1.id).first_name == 'Marc'
        assert self.db.get_person(person2.id).last_name == 'PYTHON'
        assert self.db.get_person_by_user_account(user1.id) is not None
        assert self.db.get_person_by_user_account(user1.id).first_name == 'Marc'
        assert self.db.get_person_by_user_account(user3.id) is None

    def testDel(self):
        user1 = self.db.add_user_account(a_login='mschneider', a_password='IwontGiveIt',
                                         a_is_admin=True)
        user2 = self.db.add_user_account(a_login='lonely', a_password='boy',
                                         a_is_admin=True, a_skin_used='myskin')
        user3 = self.db.add_user_account(a_login='domo', a_password='gik',
                                         a_is_admin=True)
        person1 = self.db.add_person(p_first_name='Marc',
                                     p_last_name='SCHNEIDER',
                                     p_birthdate=datetime.date(1973, 4, 24),
                                     p_user_account_id = user1.id)
        try:
            self.db.del_user_account(user1.id)
            TestCase.fail(self, "It shouldn't have been possible to delete this"
                               +" user account, a person has a reference to it")
        except DbHelperException:
            pass
        person2 = self.db.add_person(p_first_name='Monthy',
                                     p_last_name='PYTHON',
                                     p_birthdate=datetime.date(1981, 4, 24))
        user_temp = self.db.add_user_account(a_login='fantom', a_password='as',
                                             a_is_admin = False)
        user_temp_id = user_temp.id
        user_acc_del = self.db.del_user_account(user_temp.id)
        assert user_acc_del.id == user_temp.id
        l_user = self.db.list_user_accounts()
        assert len(l_user) > 0
        for user in l_user:
            assert user.login != 'fantom'
        person1_id = person1.id
        person_del = self.db.del_person(person1.id)
        assert person_del.id == person1_id
        found_person2 = False
        for person in self.db.list_persons():
            assert person.id != person1.id
            found_person2 = (person.id == person2.id)
        assert found_person2
        # Make sure associated user account has been deleted
        l_user = self.db.list_user_accounts()
        assert len(l_user) > 0
        for user in l_user:
            assert user.login != 'mschneider'
        try:
            self.db.del_person(12345678910)
            TestCase.fail(self, "Person does not exist, an exception should "
                               +"have been raised")
        except DbHelperException:
            pass
        try:
            self.db.del_user_account(12345678910)
            TestCase.fail(self, "User account does not exist, an exception "
                               +"should have been raised")
        except DbHelperException:
            pass

class SystemStatsTestCase(GenericTestCase):
    """
    Test system stats
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.db.del_all_system_stats()

    def tearDown(self):
        self.db.del_all_system_stats()
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_system_stats()) == 0

    def testAdd(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat = self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv)
            print sstat
            sstat_list.append(sstat)
        assert len(self.db.list_system_stats()) == 4, \
                   "List of system stats should have 4 items : %s" \
                   % self.db.list_system_stats()

    def testListAndGet(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                              now + datetime.timedelta(seconds=i), ssv))
        system_stat1 = self.db.get_system_stat(sstat_list[1].id)
        ssv = self.db.list_system_stats_values(system_stat1.id)
        assert len(ssv) == 2
        assert ssv[0].value == '2'

    def testDel(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv))
        sstat_del = self.db.del_system_stat("sstat0")
        assert sstat_del.name == "sstat0"
        assert len(self.db.list_system_stats()) == 3
        try:
            self.db.del_system_stat("i_dont_exist")
            TestCase.fail(self, "System stat does not exist, an exception \
                                 should have been raised")
        except DbHelperException:
            pass
        ss_list = self.db.list_system_stats()
        ss_list_del = self.db.del_all_system_stats()
        assert len(ss_list) == len(ss_list_del)
        assert len(self.db.list_system_stats()) == 0
        ssv = self.db._session.query(SystemStatsValue).all()
        assert len(ssv) == 0


class UIItemConfigTestCase(GenericTestCase):
    """
    Test item UI config
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_ui_item_config(self.db)

    def tearDown(self):
        self.remove_all_ui_item_config(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_all_ui_item_config()) == 0

    def testAdd(self):
        ui_config = self.db.set_ui_item_config('area', 2, 'icon',
                                                      'basement')
        print ui_config
        self.db.set_ui_item_config('room', 1, 'icon', 'kitchen')
        self.db.set_ui_item_config('room', 4, 'icon', 'bathroom')
        self.db.set_ui_item_config('room', 4, 'param_r2', 'value_r2')
        ui_config_list_all = self.db.list_all_ui_item_config()
        assert len(ui_config_list_all) == 4, len(ui_config_list_all)
        assert len(self.db.get_ui_item_config(ui_item_name='room', ui_key='icon')) == 2
        ui_config_list_r = self.db.get_ui_item_config(ui_item_name='room',
                                                      ui_item_reference=4)
        assert len(ui_config_list_r) == 2 \
               and ui_config_list_r[0].item_name == 'room' \
               and ui_config_list_r[0].item_reference == '4' \
               and ui_config_list_r[0].key == 'icon' \
               and ui_config_list_r[0].value == 'bathroom' \
               and ui_config_list_r[1].item_name == 'room' \
               and ui_config_list_r[1].item_reference == '4' \
               and ui_config_list_r[1].key == 'param_r2' \
               and ui_config_list_r[1].value == 'value_r2', "%s" % ui_config_list_r
        uic = self.db.get_ui_item_config('room', 4, 'param_r2')
        assert uic.value == 'value_r2'
        uic = self.db.get_ui_item_config('area', 2, 'icon')
        assert uic.value == 'basement'
        assert self.db.get_ui_item_config('foo', 13, 'param_a1') is None

    def testUpdate(self):
        self.db.set_ui_item_config('area', 1, 'icon', 'basement')
        self.db.set_ui_item_config('room', 1, 'icon', 'bathroom')
        self.db.set_ui_item_config('room', 1, 'param_r2', 'value_r2')
        uic = self.db.set_ui_item_config('area', 1, 'icon', 'first_floor')
        assert uic.value == 'first_floor'

    def testListAndGet(self):
        self.db.set_ui_item_config('area', 1, 'icon', 'basement')
        self.db.set_ui_item_config('room', 1, 'icon', 'bathroom')
        self.db.set_ui_item_config('room', 1, 'param_r2', 'value_r2')
        self.db.set_ui_item_config('room', 2, 'icon', 'kitchen')
        assert len(self.db.list_all_ui_item_config()) == 4
        assert len(self.db.get_ui_item_config(ui_item_name='room')) == 3
        assert len(self.db.get_ui_item_config(ui_item_name='room',
                                              ui_item_reference=1)) == 2
        item=self.db.get_ui_item_config(ui_item_name='room',
                                        ui_item_reference=2, ui_key='icon')
        assert item.value == 'kitchen'

    def testDel(self):
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
        assert len(self.db.get_ui_item_config(ui_item_name='area')) == 0
        self.db.delete_ui_item_config(ui_item_name='room', ui_key='icon')
        ui_item_list = self.db.get_ui_item_config(ui_item_name='room')
        assert len(ui_item_list) == 1
        assert ui_item_list[0].key == 'pr1'


class SystemConfigTestCase(GenericTestCase):
    """
    Test system config
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)

    def tearDown(self):
        del self.db

    def testUpdate(self):
        system_config = self.db.update_system_config(s_simulation_mode=True,
                                                     s_debug_mode=True)
        assert system_config.simulation_mode
        assert system_config.debug_mode
        system_config = self.db.update_system_config(s_simulation_mode=False)
        assert not system_config.simulation_mode
        system_config = self.db.get_system_config()
        assert system_config.debug_mode


if __name__ == "__main__":
    unittest.main()

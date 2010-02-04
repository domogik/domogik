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
from domogik.common.sql_schema import Area, Device, DeviceUsage, DeviceConfig, \
                                      DeviceStats, DeviceStatsValue, DeviceTechnology, DeviceTechnologyConfig, \
                                      DeviceType, ItemUIConfig, Room, UserAccount, SystemAccount, SystemConfig, \
                                      SystemStats, SystemStatsValue, Trigger

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

    def remove_all_user_accounts(self, db):
        """
        Remove all user accounts
        @param db : db API instance
        """
        for user in self.db.list_user_accounts():
            self.db.del_user_account(user.id)

    def remove_all_system_accounts(self, db):
        """
        Remove all system accounts
        @param db : db API instance
        """
        for sys in self.db.list_system_accounts():
            self.db.del_system_account(sys.id)

    def remove_all_item_ui_config(self, db):
        """
        Remove all ui configuration parameters of all items (area, room, device)
        @param db : db API instance
        """
        for iuc in db.list_all_item_ui_config():
            db.delete_all_item_ui_config(iuc.item_id, iuc.item_type)


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
        assert len(self.db.list_areas()) == 0, "Area list is not empty"

    def testAdd(self):
        try:
            self.db.add_area(None, None)
            TestCase.fail(self, "An exception should have been raised : \
                          impossible to create an area without a name")
        except DbHelperException:
            pass
        area0 = self.db.add_area('area0','description 0')
        assert self.db.list_areas()[0].name == 'area0', "area0 not found"

    def testFetchInformation(self):
        area = self.db.add_area('area0','description 0')
        area0 = self.db.get_area_by_name('area0')
        assert area0.name == 'area0', 'area0 not found'

    def testDel(self):
        area0 = self.db.add_area('area0','description 0')
        area0_id = area0.id
        area_d = self.db.del_area(area0.id)
        assert not self.has_item(self.db.list_areas(), ['area0']), "area0 was NOT deleted"
        assert area_d.id == area0.id, "The returned area is not the one that was deleted"
        try:
            self.db.del_area(12345678910)
            TestCase.fail(self, "Area does not exist, an exception should have been raised")
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
        assert len(self.db.list_rooms()) == 0, "Room list is not empty : %s" % self.db.list_rooms()

    def testAdd(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        room2 = self.db.add_room(r_name='room2', r_description='description 2', r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3', r_area_id=area2.id)
        assert len(self.db.list_rooms()) == 3, "Room list should have 3 items, it has %s" % len(self.db.list_rooms())

    def testDel(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        room2 = self.db.add_room(r_name='room2', r_description='description 2', r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3', r_area_id=area2.id)
        room1_id = room1.id
        room_deleted = self.db.del_room(room1.id)
        assert not self.has_item(self.db.list_rooms(), ['room1']), "room1 was NOT deleted"
        assert self.has_item(self.db.list_rooms(), ['room2', 'room3']), "rooms were deleted but shouldn't have been"
        assert room_deleted.id == room1_id, "Returned room was not the one that was deleted"
        try:
            self.db.del_room(12345678910)
            TestCase.fail(self, "Room does not exist, an exception should have been raised")
        except DbHelperException:
            pass

    def testGetRoomByName(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        assert self.db.get_room_by_name('room1').name == 'room1', "Couldn't find room1"

    def testGetRoomsOfArea(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room(r_name='room1', r_description='description 1', r_area_id=area1.id)
        room2 = self.db.add_room(r_name='room2', r_description='description 2', r_area_id=area1.id)
        room3 = self.db.add_room(r_name='room3', r_description='description 3', r_area_id=area2.id)
        assert len(self.db.get_all_rooms_of_area(area1.id)) == 2, \
          "Area1 should have 2 rooms, it has %s" % len(self.db.get_all_rooms_of_area(area1.id))
        assert len(self.db.get_all_rooms_of_area(area2.id)) == 1, \
          "Area2 should have 1 room, it has %s" % len(self.db.get_all_rooms_of_area(area2.id))

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
        assert len(self.db.list_device_usages()) == 0, "There should have no device usage"

    def testAdd(self):
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        assert len(self.db.list_device_usages()) == 2, "%s devices usages found, instead of 2 " \
                                                      % len(self.db.list_device_usages())
        assert self.has_item(self.db.list_device_usages(), ['du1', 'du2']), "Couldn't find all device usages"

    def testFetchInformation(self):
        du1 = self.db.add_device_usage('du1')
        assert self.db.get_device_usage_by_name('du1').name == 'du1', "DeviceUsage du1 was not found"

    def testDel(self):
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        du2_id = du2.id
        du_del = self.db.del_device_usage(du2.id)
        assert self.has_item(self.db.list_device_usages(), ['du1']), "Couldn't find 'du1'"
        assert not self.has_item(self.db.list_device_usages(), ['du2']), "'du2' was NOT deleted"
        assert du_del.id == du2_id, "Returned DeviceUsage is not the one that was deleted"
        try:
            self.db.del_device_usage(12345678910)
            TestCase.fail(self, "Device usage does not exist, an exception should have been raised")
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
        assert len(self.db.list_device_types()) == 0, "There should have no device type"

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
        dty2 = self.db.add_device_type('x10 Dimmer', 'desc2', dt1.id)
        assert len(self.db.list_device_types()) == 2, "%s devices types found, instead of 2 " \
                                                      % len(self.db.list_device_types())
        assert self.has_item(self.db.list_device_types(), ['x10 Switch', 'x10 Dimmer']), "Couldn't find all device types"

    def testFetchInformation(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
        assert self.db.get_device_type_by_name('x10 Switch').name == 'x10 Switch', "DeviceType 'x10 Switch' was not found"

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dty1 = self.db.add_device_type('x10 Switch', dt1.id)
        dty2 = self.db.add_device_type('x10 Dimmer', dt1.id)
        dty2_id = dty2.id
        dty_del = self.db.del_device_type(dty2.id)
        assert self.has_item(self.db.list_device_types(), ['x10 Switch']), "Couldn't find 'x10 Switch'"
        assert not self.has_item(self.db.list_device_usages(), ['x10 Dimmer']), "'x10 Dimmer' was NOT deleted"
        assert dty_del.id == dty2_id, "The returned DeviceType is not the one that was deleted"
        try:
            self.db.del_device_type(12345678910)
            TestCase.fail(self, "Device type does not exist, an exception should have been raised")
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
        assert len(self.db.list_device_technologies()) == 0, "There should have no device technology"

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2', u'wired')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        assert len(self.db.list_device_technologies()) == 3, "%s devices technologies found, instead of 3 " \
                                                      % len(self.db.list_device_technologies())
        assert self.has_item(self.db.list_device_technologies(), [u'x10', u'1wire', u'PLCBus']), \
                                                      "Couldn't find all device technologies"

    def testFetchInformation(self):
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2', u'wired')
        assert self.db.get_device_technology_by_name(u'1wire').name == u'1wire', "DeviceTechnology '1wire' was not found"

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2', u'wired')
        dt_del = dt2
        dt2_id = dt2.id
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        self.db.del_device_technology(dt2.id)
        assert self.has_item(self.db.list_device_technologies(), [u'x10', u'PLCBus']), "Couldn't find 'x10' and 'PLCBus'"
        assert not self.has_item(self.db.list_device_technologies(), [u'1wire']), "'1wire' was NOT deleted"
        assert dt_del.id == dt2_id, "The returned DeviceTechnology object is not the one that was deleted"
        try:
            self.db.del_device_technology(12345678910)
            TestCase.fail(self, "Device technology does not exist, an exception should have been raised")
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
        assert len(self.db.list_all_device_technology_config()) == 0, "There should have no device technology configurations"

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        dtc1_1 = self.db.add_device_technology_config(dt1.id, 'key1_1', 'val1_1', 'desc1')
        dtc1_2 = self.db.add_device_technology_config(dt1.id, 'key1_2', 'val1_2', 'desc2')
        dtc3_1 = self.db.add_device_technology_config(dt3.id, 'key3_1', 'val3_1', 'desc3')
        dtc3_2 = self.db.add_device_technology_config(dt3.id, 'key3_2', 'val3_2', 'desc4')
        dtc3_3 = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3', 'desc5')
        try:
            duplicate_key = False
            dtc = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3', 'desc')
            duplicate_key = True
        except DbHelperException:
            pass

        assert not duplicate_key, "It shouldn't have been possible to add 'key3_3' for device technology %s : it already exists" % dt3.id
        assert len(self.db.list_device_technology_config(dt1.id)) == 2, \
                "%s devices technologies config found, instead of 2 " \
                % len(self.db.list_device_technology_config(dt1.id))
        assert len(self.db.list_device_technology_config(dt3.id)) == 3, \
                "%s devices technologies config found, instead of 3 " \
                % len(self.db.list_device_technology_config(dt3.id))

    def testGet(self):
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        dtc3_1 = self.db.add_device_technology_config(dt3.id, 'key3_1', 'val3_1', 'desc3_1')
        dtc3_2 = self.db.add_device_technology_config(dt3.id, 'key3_2', 'val3_2', 'desc3_2')
        dtc3_3 = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3', 'desc3_3')
        dtc = self.db.get_device_technology_config(dt3.id, 'key3_2')
        assert dtc.value == 'val3_2', "Wrong value for %s. Should be val3_2" % dtc.value

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        dtc1_1 = self.db.add_device_technology_config(dt1.id, 'key1_1', 'val1_1', 'desc1')
        dtc1_2 = self.db.add_device_technology_config(dt1.id, 'key1_2', 'val1_2', 'desc2')
        dtc3_1 = self.db.add_device_technology_config(dt3.id, 'key3_1', 'val3_1', 'desc3')
        dtc3_2 = self.db.add_device_technology_config(dt3.id, 'key3_2', 'val3_2', 'desc4')
        dtc3_3 = self.db.add_device_technology_config(dt3.id, 'key3_3', 'val3_3', 'desc5')
        dtc3_2_id = dtc3_2.id
        dtc_del = self.db.del_device_technology_config(dtc3_2.id)
        assert self.db.get_device_technology_config(dt3.id, 'key3_2') == None, "key3_2 was NOT deleted"
        assert dtc_del.id == dtc3_2_id, "The return DeviceTechnologyConfig object was not the one that was deleted"
        try:
            self.db.del_device_technology_config(12345678910)
            TestCase.fail(self, "Device technology config does not exist, an exception should have been raised")
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
        assert len(self.db.list_devices()) == 0, "Device list is NOT empty"

    def testAdd(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        du1 = self.db.add_device_usage('du1')
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)

        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1',
                    d_is_resetable = True, d_initial_value = 30,
                    d_is_value_changeable_by_user = False,
                    d_unit_of_stored_values = u'Percent')
        assert len(self.db.list_devices()) == 1, "Device was NOT added"
        # TODO see if these methods are still used
        #assert device1.is_lamp(), "device1.is_lamp() returns False. Should have returned True"
        #assert not device1.is_appliance(), "device1.is_appliance() returns True. Should have returned False"

    def testUpdate(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
        du1 = self.db.add_device_usage('du1')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1',
                    d_is_resetable = True, d_initial_value = 30,
                    d_is_value_changeable_by_user = False,
                    d_unit_of_stored_values = u'Percent')
        device_id = device1.id
        device1 = self.db.update_device(d_id = device1.id, d_description = 'desc2')
        self.db._session.expunge(device1) # Remove object from session
        device1 = self.db.get_device(device_id)
        assert device1.description == 'desc2',\
              "Device desc. was NOT changed : should be 'desc2' but is '%s'" % device1.description

    def testFindAndSearch(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room('room1', area1.id)
        room2 = self.db.add_room('room2', area2.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
        dty2 = self.db.add_device_type('x10 Dimmer', 'desc1', dt1.id)
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1',
                    d_is_resetable = True, d_initial_value = 30,
                    d_is_value_changeable_by_user = False,
                    d_unit_of_stored_values = u'Percent')
        device2 = self.db.add_device(d_name='device2', d_address='A2',
                    d_type_id = dty2.id, d_usage_id=du1.id, d_room_id=room1.id)
        device3 = self.db.add_device(d_name='device3', d_address='A3',
                    d_type_id = dty2.id, d_usage_id=du2.id, d_room_id=room2.id)

        assert len(self.db.list_devices()) == 3, "Device list should have 3 items, but it has %s" % self.db.list_devices()
        assert len(self.db.get_all_devices_of_room(room1.id)) == 2, \
                  "Room id %s should have 2 devices but has %s" % (room1.id, len(self.db.get_all_devices_of_room(room1.id)))
        assert len(self.db.get_all_devices_of_room(room2.id)) == 1, \
                  "Room id %s should have 1 device but has %s" % (room2.id, len(self.db.get_all_devices_of_room(room2.id)))
        assert len(self.db.get_all_devices_of_area(area1.id)) == 2, \
                  "Area id %s should have 2 devices but has %s" % (area1.id, len(self.db.get_all_devices_of_area(area1.id)))
        assert len(self.db.get_all_devices_of_area(area2.id)) == 1, \
                  "Area id %s should have 1 device but has %s" % (area2.id, len(self.db.get_all_devices_of_area(area2.id)))

        nb_of_dev = len(self.db.search_devices({'usage_id':du1.id, 'room_id':room1.id}))
        assert nb_of_dev == 2, "Should have found 2 devices, but found %s" % nb_of_dev
        nb_of_dev = len(self.db.search_devices({'address':'A2'}))
        assert nb_of_dev == 1, "Should have found 1 device, but found %s" % nb_of_dev
        nb_of_dev = len(self.db.search_devices({'address':'A1544'}))
        assert nb_of_dev == 0, "Should have found 0 device, but found %s" % nb_of_dev

        device_list = self.db.find_devices(None, None)
        assert len(device_list) == 3, "Should have found 3 devices, but found %s" % len(device_list)
        device_list = self.db.find_devices([], [])
        assert len(device_list) == 3, "Should have found 3 devices, but found %s" % len(device_list)
        device_list = self.db.find_devices([room1.id, room2.id], [du1.id, du2.id])
        assert len(device_list) == 3, "Should have found 3 devices, but found %s" % len(device_list)
        device_list = self.db.find_devices([room1.id], [du1.id, du2.id])
        assert len(device_list) == 2, "Should have found 2 devices, but found %s" % len(device_list)
        device_list = self.db.find_devices([room2.id], None)
        assert len(device_list) == 1, "Should have found 1 device, but found %s" % len(device_list)
        device_list = self.db.find_devices([room2.id], [])
        assert len(device_list) == 1, "Should have found 1 device, but found %s" % len(device_list)
        device_list = self.db.find_devices([room1.id], [du2.id])
        assert len(device_list) == 0, "Should have found NO device, but found %s" % len(device_list)
        device_list = self.db.find_devices([room1.id, room2.id], [du2.id])
        assert len(device_list) == 1, "Should have found 1 device, but found %s" % len(device_list)

    def testDel(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room('room1', area1.id)
        room2 = self.db.add_room('room2', area2.id)
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
        du1 = self.db.add_device_usage('du1')
        du2 = self.db.add_device_usage('du2')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1',
                    d_type_id = dty1.id, d_usage_id = du1.id,
                    d_room_id = room1.id, d_description = 'desc1',
                    d_is_resetable = True, d_initial_value = 30,
                    d_is_value_changeable_by_user = False,
                    d_unit_of_stored_values = u'Percent')
        device2 = self.db.add_device(d_name='device2', d_address='A2',
                    d_type_id = dty1.id, d_usage_id=du1.id, d_room_id=room1.id)
        device3 = self.db.add_device(d_name='device3', d_address='A3',
                    d_type_id = dty1.id, d_usage_id=du2.id, d_room_id=room2.id)
        device_del = device2
        device2_id = device2.id
        self.db.del_device(device2.id)
        assert len(self.db.list_devices()) == 2, "Found %s device(s), should be %s" % (self.db.list_devices(), 1)
        assert self.db.list_devices()[0].address == 'A1', \
              "Device should have 'A1' address but has : %s instead" % self.db.list_devices()[0].address
        assert device_del.id == device2.id, "The return Device object is not the one that was deleted"
        try:
            self.db.del_device(12345678910)
            TestCase.fail(self, "Device does not exist, an exception should have been raised")
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
        assert len(self.db.list_all_device_stats()) == 0, "Device stats list is NOT empty"

    def testAdd(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        du1 = self.db.add_device_usage("lighting")
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
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
        d_stat1_1 = self.db.add_device_stat(device1.id, now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1.id, now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2.id, now, {'val1': '40', 'val2': '41' })
        d_stat3_1 = self.db.add_device_stat(device3.id, now, {'val1': '100', 'val2': '101' })
        l_stats = self.db.list_device_stats(device1.id)
        assert len(l_stats) == 2, \
              "device stats for device id %s should have 2 items. It has %s" % (device1.id, len(l_stats))
        l_stats = self.db.list_device_stats(device2.id)
        assert len(l_stats) == 1, \
              "device stats for device id %s should have 1 item. It has %s" % (device2.id, len(l_stats))
        assert self.db.device_has_stats(device1.id), \
              "device_hast_stats should have returned True for device id %s " % device1.id
        assert not self.db.device_has_stats(device4.id), \
              "device_hast_stats should have returned False for device id %s " % device4.id

    def testLastStatOfOneDevice(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1.id, now,
                                            {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1.id, now + datetime.timedelta(seconds=1),
                                            {'val1': '11', 'val2': '12' })

        stat = self.db.get_last_stat_of_device(device1.id)
        dsv = self.db.list_device_stats_values(stat.id)
        for item in dsv:
            if item.name == 'val1':
                assert item.value == '11', "Should get value '11' for last stat of device %s. Got %s instead" \
                                              % (device1.id, dsv[0].value)
            elif item.name == 'val2':
                assert item.value == '12', "Should get value '12' for last stat of device %s. Got %s instead" \
                                              % (device1.id, dsv[1].value)

    def testLastStatOfDevices(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
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
        assert len(l_stats) == 2, "last device stats should have 2 items. It has %s" % len(l_stats)
        device_id_list = []
        for stat in l_stats:
            device_id_list.append(stat.device_id)
            if stat.device_id == device1.id:
                # Make sure we get the LAST stat for device1
                dsv = self.db.list_device_stats_values(stat.id)
                value_list = []
                for item in dsv:
                    value_list.append(item.value)
                assert '11' in value_list and '12' in value_list, \
                      "Should have found values '11' and '12' for last device stat"
        assert device1.id in device_id_list, "device1 is not in the list but should have been"
        assert device2.id in device_id_list, "device2 is not in the list but should have been"

    def testDel(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dty1 = self.db.add_device_type('x10 Switch', 'desc1', dt1.id)
        du1 = self.db.add_device_usage("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        device1 = self.db.add_device(d_name='device1', d_address = "A1",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        device2 = self.db.add_device(d_name='device2', d_address = "A2",
                    d_type_id = dty1.id, d_usage_id = du1.id, d_room_id = room1.id)
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1.id, now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1.id, now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2.id, now, {'val1': '40', 'val2': '41' })
        l_stats = self.db.list_device_stats(device1.id)
        d_stats_list_d = self.db.del_all_device_stats(device1.id)
        assert len(d_stats_list_d) == len(l_stats), "Returned length of device stats deleted differs from the one that was deleted (%s != %s)" % (d_stats_list_d, l_stats)
        l_stats = self.db.list_device_stats(device1.id)
        assert len(l_stats) == 0, "List of stats should be empty for device1, but it has %s items" % len(l_stats)
        l_stats = self.db.list_device_stats(device2.id)
        assert len(l_stats) == 1, "List of stats should have 1 item for device2, but it has %s items" % len(l_stats)


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
        assert len(self.db.list_triggers()) == 0, "Trigger list is NOT empty"

    def testAdd(self):
        trigger1 = self.db.add_trigger(t_description = 'desc1',
                                t_rule = 'AND(x,OR(y,z))', t_result= ['x10_on("a3")','1wire()'])
        trigger2 = self.db.add_trigger(t_description = 'desc2',
                                t_rule = 'OR(x,AND(y,z))', t_result= ['x10_on("a2")','1wire()'])
        assert len(self.db.list_triggers()) == 2, "Trigger list should have 2 items but it has %s item(s)" % len(self.db.list_triggers())
        assert self.db.get_trigger(trigger1.id).description == 'desc1', "Trigger1 should have 'desc1', but it has not"

    def testDel(self):
        trigger1 = self.db.add_trigger(t_description = 'desc1',
                                t_rule = 'AND(x,OR(y,z))', t_result= ['x10_on("a3")','1wire()'])
        trigger2 = self.db.add_trigger(t_description = 'desc2',
                                t_rule = 'OR(x,AND(y,z))', t_result= ['x10_on("a2")','1wire()'])
        for trigger in self.db.list_triggers():
            trigger_id = trigger.id
            trigger_del = trigger
            self.db.del_trigger(trigger.id)
            assert trigger_del.id == trigger.id, "The returned Trigger is not the one that was deleted"
        assert len(self.db.list_triggers()) == 0, "Trigger list should be empty, but it has % item(s)" % len(self.db.list_triggers())
        try:
            self.db.del_trigger(12345678910)
            TestCase.fail(self, "Trigger does not exist, an exception should have been raised")
        except DbHelperException:
            pass


class UserAndSystemAccountsTestCase(GenericTestCase):
    """
    Test user and system accounts
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_user_accounts(self.db)
        self.remove_all_system_accounts(self.db)

    def tearDown(self):
        self.remove_all_user_accounts(self.db)
        self.remove_all_system_accounts(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_system_accounts()) == 0, "System account list is NOT empty"
        assert len(self.db.list_user_accounts()) == 0, "User account list is NOT empty"

    def testAdd(self):
        sys1 = self.db.add_system_account(a_login = 'mschneider', a_password = 'IwontGiveIt', a_is_admin = True)
        assert self.db.is_system_account('mschneider', 'IwontGiveIt'), "is_system_account should have returned True"
        assert not self.db.is_system_account('mschneider', 'plop'), "is_system_account should have returned False"
        assert not self.db.is_system_account('hello', 'boy'), "is_system_account should have returned False"
        sys1 = self.db.get_system_account_by_login_and_pass('mschneider', 'IwontGiveIt')
        assert sys1 is not None, "Should have found an account 'mschneider'"
        assert sys1.login == 'mschneider', "Login should be 'mschneider' but is '%s'" %sys1.login
        try:
            self.db.add_system_account(a_login = 'mschneider', a_password = 'plop', a_is_admin = True)
            error = False
        except DbHelperException:
            error = True
        assert error, "It shouldn't have been possible to add login %s. It already exists!" % 'mschneider'
        sys2 = self.db.add_system_account(a_login = 'lonely', a_password = 'boy', a_is_admin = True, a_skin_used='myskin')
        sys3 = self.db.add_system_account(a_login = 'domo', a_password = 'gik', a_is_admin = True)
        user1 = self.db.add_user_account(u_first_name='Marc', u_last_name='SCHNEIDER', u_birthdate=datetime.date(1973, 4, 24),
                                  u_system_account_id = sys1.id)
        user2 = self.db.add_user_account(u_first_name='Monthy', u_last_name='PYTHON', u_birthdate=datetime.date(1981, 4, 24))
        assert len(self.db.list_user_accounts()) == 2, \
                  "List of user accounts should have 2 items, but it has NOT %s" % self.db.list_user_accounts()
        assert len(self.db.list_system_accounts()) == 3, \
                  "List of system accounts should have 3 items, but it has NOT %s" % self.db.list_system_accounts()

    def testGet(self):
        sys1 = self.db.add_system_account(a_login = 'mschneider', a_password = 'IwontGiveIt', a_is_admin = True)
        sys2 = self.db.add_system_account(a_login = 'lonely', a_password = 'boy', a_is_admin = True, a_skin_used='myskin')
        sys3 = self.db.add_system_account(a_login = 'domo', a_password = 'gik', a_is_admin = True)
        user1 = self.db.add_user_account(u_first_name='Marc', u_last_name='SCHNEIDER', u_birthdate=datetime.date(1973, 4, 24),
                                  u_system_account_id = sys1.id)
        user2 = self.db.add_user_account(u_first_name='Monthy', u_last_name='PYTHON', u_birthdate=datetime.date(1981, 4, 24))

        assert self.db.get_system_account(sys1.id).login == 'mschneider', \
              "Login for system id %s should be 'mschneider' but is %s" % (sys1.id, sys1.login)
        assert self.db.get_system_account_by_login('mschneider') is not None
        assert self.db.get_system_account_by_login('mschneider').id == sys1.id, \
              "Id for login 'mschneider' should be %s but is %s" % (sys1.id, self.db.get_system_account('mschneider').id)
        assert self.db.get_system_account_by_login('lucyfer') is None

        login = self.db.get_system_account_by_user(user1.id).login
        assert login == 'mschneider', \
              "System account login for user id %s should be 'mschneider' but is %s" % (user1.id, login)
        assert self.db.get_user_account(user1.id).first_name == 'Marc', \
              "First name for user id %s should be 'Marc' but is %s" % (user1.id, user1.first_name)
        assert self.db.get_user_account(user2.id).last_name == 'PYTHON', \
              "Last name for user id %s should be 'PYTHON' but is %s" % (user2.id, user2.last_name)

        assert self.db.get_user_account_by_system_account(sys1.id) is not None, \
              "System account with id '%s' should have a User account, but it doesn't have" % sys1.id
        assert self.db.get_user_account_by_system_account(sys1.id).first_name == 'Marc', \
              "System account with id '%s' should have as first name 'Marc' but have '%s' instead" \
              % (sys1.id, self.db.get_user_account_by_system_account(sys1.id).first_name)
        assert self.db.get_user_account_by_system_account(sys3.id) is None, \
              "System account with id '%s' shouldn't have a User account, but it has one" % sys3.id

    def testDel(self):
        sys1 = self.db.add_system_account(a_login = 'mschneider', a_password = 'IwontGiveIt', a_is_admin = True)
        sys2 = self.db.add_system_account(a_login = 'lonely', a_password = 'boy', a_is_admin = True, a_skin_used='myskin')
        sys3 = self.db.add_system_account(a_login = 'domo', a_password = 'gik', a_is_admin = True)
        user1 = self.db.add_user_account(u_first_name='Marc', u_last_name='SCHNEIDER', u_birthdate=datetime.date(1973, 4, 24),
                                  u_system_account_id = sys1.id)
        user2 = self.db.add_user_account(u_first_name='Monthy', u_last_name='PYTHON', u_birthdate=datetime.date(1981, 4, 24))
        sys_temp = self.db.add_system_account(a_login = 'fantom', a_password = 'as', a_is_admin = False)
        sys_temp_id = sys_temp.id
        sys_acc_del = self.db.del_system_account(sys_temp.id)
        assert sys_acc_del.id == sys_temp.id, "The return SystemAccount is not the one that was deleted"
        l_sys = self.db.list_system_accounts()
        assert len(l_sys) > 0, "The list is empty but it shouldn't"
        for sys in l_sys:
            assert sys.login != 'fantom', "System account with 'fantom' login was NOT deleted"
        user1_acc_id = user1.id
        user_acc_del = self.db.del_user_account(user1.id)
        assert user_acc_del.id == user1_acc_id, "The return UserAccount is not the one that was deleted"
        found_user2 = False
        for user in self.db.list_user_accounts():
            assert user.id != user1.id, "User %s was NOT deleted" % user1.id
            found_user2 = (user.id == user2.id)
        assert found_user2, "User %s was deleted, but shouldn't have been" % user2.id
        # Make sure associated system account has been deleted
        l_sys = self.db.list_system_accounts()
        assert len(l_sys) > 0, "The list is empty but it shouldn't"
        for sys in l_sys:
            assert sys.login != 'mschneider', "System account with 'mschneider' login was NOT deleted"
        try:
            self.db.del_user_account(12345678910)
            TestCase.fail(self, "User account does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        try:
            self.db.del_system_account(12345678910)
            TestCase.fail(self, "System account does not exist, an exception should have been raised")
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
        assert len(self.db.list_system_stats()) == 0, "List of system stats should be empty : %s" % self.db.list_system_stats()


    def testAdd(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv))
        assert len(self.db.list_system_stats()) == 4, "List of system stats should have 4 items : %s" % self.db.list_system_stats()

    def testListAndGet(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv))
        system_stat1 = self.db.get_system_stat(sstat_list[1].id)
        ssv = self.db.list_system_stats_values(system_stat1.id)
        assert len(ssv) == 2, "%s should have 2 statistics values, it has %s" %(system_stat1.name, len(ssv))
        assert ssv[0].value == '2', "Wrong value for stat %s : %s. Should be '2'" % (ssv[0].name, ssv[0].value)

    def testDel(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv))
        sstat_del = self.db.del_system_stat("sstat0")
        assert sstat_del.name == "sstat0", "The returned SystemStats is not the one that was deleted"
        assert len(self.db.list_system_stats()) == 3, "List of system stats should have 3 items : %s" % self.db.list_system_stats()
        try:
            self.db.del_system_stat("i_dont_exist")
            TestCase.fail(self, "System stat does not exist, an exception should have been raised")
        except DbHelperException:
            pass
        ss_list = self.db.list_system_stats()
        ss_list_del = self.db.del_all_system_stats()
        assert len(ss_list) == len(ss_list_del), "The returned SystemStats list is not the one that was deleted"
        assert len(self.db.list_system_stats()) == 0, "System statistics should be empty, but it is NOT"
        ssv = self.db._session.query(SystemStatsValue).all()
        assert len(ssv) == 0, "System statistic values should be empty, but it is NOT"


class ItemUIConfigTestCase(GenericTestCase):
    """
    Test item UI config
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)
        self.remove_all_item_ui_config(self.db)

    def tearDown(self):
        self.remove_all_item_ui_config(self.db)
        del self.db

    def testEmptyList(self):
        assert len(self.db.list_all_item_ui_config()) == 0, "List of UI config parameters should be empty : %s" \
                                                            % self.db.list_all_item_ui_config()

    def testAdd(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        ui_config_list_a = self.db.add_item_ui_config(area1.id, 'area', {'param_a1':'value_a1','param_a2':'value_a2'})
        assert len(ui_config_list_a) == 2
        self.db.add_item_ui_config(room1.id, 'room', {'param_r1':'value_r1', 'param_r2':'value_r2'})
        ui_config_list_all = self.db.list_all_item_ui_config()
        assert len(ui_config_list_all) == 4, "List should contain 4 items but has %s" % len(ui_config_list_all)
        ui_config_list_r = self.db.list_item_ui_config(room1.id, 'room')
        assert len(ui_config_list_r) == 2 and ui_config_list_r[0].item_type == 'room' \
               and ui_config_list_r[0].key == 'param_r1' and ui_config_list_r[0].value == 'value_r1' \
               and ui_config_list_r[1].item_type == 'room' and ui_config_list_r[1].key == 'param_r2' \
               and ui_config_list_r[1].value == 'value_r2', "Wrong list returned %s" % ui_config_list_r
        uic = self.db.get_item_ui_config(room1.id, 'room', 'param_r2')
        assert uic.value == 'value_r2', "item should have the value 'value_r2' but it has %s" % uic.value
        uic = self.db.get_item_ui_config(area1.id, 'area', 'param_a1')
        assert uic.value == 'value_a1', "item should have the value 'value_a1' but it has %s" % uic.value
        error = False
        try:
            self.db.get_item_ui_config(area1.id, 'foo', 'param_a1')
        except DbHelperException:
            error = True
        assert error is True, "Shouldn't have found any param values for (%s, %s)" % (area1.id, 'foo')
        try:
            self.db.add_item_ui_config(800000000, 'area', {'param_a1':'value_a1', 'param_a2':'value_a2'})
        except DbHelperException:
            error = True
        assert error is True, "Shouldn't have been able to add parameters with this item.id which doesn't exist"

    def testUpdate(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        self.db.add_item_ui_config(area1.id, 'area', {'param_a1':'value_a1', 'param_a2':'value_a2'})
        self.db.add_item_ui_config(room1.id, 'room', {'param_r1':'value_r1', 'param_r2':'value_r2'})
        uic = self.db.update_item_ui_config(area1.id, 'area', 'param_a1', 'new_value_a1')
        uic = self.db.get_item_ui_config(area1.id, 'area', 'param_a1')
        assert uic.value == 'new_value_a1', "Parameter should have the value '%s' but it has '%s'" \
                            % ('new_value_a1', uic.value)

    def testDel(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1.id)
        self.db.add_item_ui_config(area1.id, 'area', {'param_a1':'value_a1', 'param_a2':'value_a2'})
        self.db.add_item_ui_config(room1.id, 'room', {'param_r1':'value_r1', 'param_r2':'value_r2'})
        self.db.delete_item_ui_config(area1.id, 'area', 'param_a2')
        ui_config_list_all = self.db.list_all_item_ui_config()
        assert len(ui_config_list_all) == 3, "List should contain 3 items but has %s" % len(ui_config_list_all)
        assert self.db.get_item_ui_config(room1.id, 'area', 'param_a1') is not None
        assert self.db.get_item_ui_config(room1.id, 'area', 'param_a2') is None
        item_ui_config_list = self.db.list_item_ui_config(area1.id, 'area')
        item_ui_config_del_list = self.db.delete_all_item_ui_config(area1.id, 'area')
        assert len(self.db.list_item_ui_config(area1.id, 'area')) == 0, "No parameter should have been found"


class SystemConfigTestCase(GenericTestCase):
    """
    Test system config
    """

    def setUp(self):
        self.db = DbHelper(use_test_db=True)

    def tearDown(self):
        del self.db

    def testUpdate(self):
        system_config = self.db.update_system_config(s_simulation_mode=True, s_debug_mode=True)
        assert system_config.simulation_mode, "System should be in simulation mode but it is NOT"
        assert system_config.debug_mode, "System should be in debug mode but it is NOT"
        system_config = self.db.update_system_config(s_simulation_mode=False)
        assert not system_config.simulation_mode, "System shouldn't be in simulation mode, but it IS"
        system_config = self.db.get_system_config()
        assert system_config.debug_mode, "System should be in debug mode but it is NOT"


if __name__ == "__main__":
    unittest.main()

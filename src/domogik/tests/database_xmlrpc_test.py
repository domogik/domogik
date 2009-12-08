#!/usr/bin/python
# -*- coding: utf-8 -*-

''' This file is part of B{Domogik} project (U{http://www.domogik.org}).

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

Test database xmlrpc mapping

Implements
==========


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
'''

import unittest
import datetime
from domogik.common.database_xmlrpc import XmlRpcDbHelper
from domogik.common.database import DbHelperException

class GenericTestCase(unittest.TestCase):

    def has_item(self, item_list, item_name_list):
        """
        Check if a list of names are in a list (with objects having a 'name' attribute)
        @param item_list : a list of objects having a 'name' attribute
        @param item_name_list : a list of names
        @return True if all names are in the list
        """
        found = 0
        for item in item_list:
            if item[1] in item_name_list:
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

    def remove_all_device_categories(self, db):
        """
        Remove all device categories
        @param db : db API instance
        """
        for dc in db.list_device_categories():
            db.del_device_category(dc.id)

    def remove_all_device_technologies(self, db):
        """
        Remove all device technologies
        @param db : db API instance
        """
        self.remove_all_device_technology_config(db)
        for dt in db.list_device_technologies():
            db.del_device_technology(dt.id)

    def remove_all_device_technology_config(self, db):
        """
        Remove all configurations of device technologies
        @param db : db API instance
        """
        for dtc in db.list_all_device_technology_config():
            db.del_device_technology_config(dtc.id)

    def remove_all_device_stats(self, db):
        """
        Remove all device stats
        @param db : db API instance
        """
        for device in db.list_devices():
            db.del_all_device_stats(device.id)

    def remove_all_user_accounts(self, db):
        """
        Remove all user accounts
        @param db : db API instance
        """
        for user in db.list_user_accounts():
            db.del_user_account(user.id)

    def remove_all_system_accounts(self, db):
        """
        Remove all system accounts
        @param db : db API instance
        """
        for sys in db.list_system_accounts():
            db.del_system_account(sys.id)

    
    def remove_all_item_ui_config(self, db):
        """
        Remove all ui configuration parameters of all items (area, room, device)
        @param db : db API instance
        """
        for iuc in db.list_all_item_ui_config():
            db.delete_item_ui_config(iuc.item_id, iuc.item_type, iuc.key)
            
    def remove_all_triggers(self, db):
        """
        Remove all triggers
        @param db : db API instance
        """
        for trigger in db.list_triggers():
            db.del_trigger(trigger.id)

class AreaTestCase(GenericTestCase):
    ''' Test areas mapping
    '''
    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_areas(self.db.get_helper())

    def tearDown(self):
        self.remove_all_areas(self.db.get_helper())
        del self.db

    def testEmptyListAreas(self):
        ''' List all existing areas '''
        list_areas = self.db.list_areas()
        assert list_areas == []

    def testAddArea(self):
        ''' Add an area'''
        area = self.db.add_area("area1_name", "area1_description")
        id, name, description = area 
        assert name == "area1_name" and description == "area1_description"

    def testNonEmptyListAreas(self):
        area = self.db.add_area("area1_name", "area1_description")
        list_areas = self.db.list_areas()
        self.assertEqual(len(list_areas),1)
        id, name, description = list_areas[0]
        assert name == "area1_name" and description == "area1_description"

    def testGetAreaById(self):
        ''' Add an area and find it by id '''
        area = self.db.add_area("area2_name", "area2_description")
        id, name, description = area 
        area2 = self.db.get_area_by_id(id)
        id2, name2, description2 = area2 
        assert id2 == id and name2 == "area2_name" and description2 == "area2_description"

    def testGetAreaByName(self):
        ''' Add an area and find it by name '''
        area = self.db.add_area("area3_name", "area3_description")
        id, name, description = area 
        area3 = self.db.get_area_by_name(name)
        id3, name3, description3 = area3 
        assert id3 == id and name3 == "area3_name" and description3 == "area3_description"

    def testDelArea(self):
        ''' Add and delete an area'''
        area = self.db.add_area("area4_name", "area4_description")
        id, name, description = area 
        self.db.del_area(id)
        area_id = self.db.get_area_by_id(id)
        area_name = self.db.get_area_by_name(name)
        assert area_id is None and area_name is None 

    def testSearchAreas(self):
        ''' Add an area and search it '''
        area = self.db.add_area("area5_name", "area5_description")
        id, name, description = area 
        area_searched = self.db.search_areas(name="area5_name")
        assert area_searched != []
        id2, name2, description2 = area_searched[0] 
        assert id == id2 and name == name2 and description == description2

            
class RoomTestCase(GenericTestCase):
    ''' Test rooms mapping
    '''
    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_rooms(self.db.get_helper())
        area = self.db.add_area("area1_name", "area1_description")
        self.area_id = area[0]

    def tearDown(self):
        self.remove_all_rooms(self.db.get_helper())
        self.remove_all_areas(self.db.get_helper())
        del self.db

    def testEmptyListRooms(self):
        ''' List all existing rooms'''
        list_rooms = self.db.list_rooms()
        self.assertEqual(list_rooms,[])

    def testAddRoom(self):
        ''' Add a room'''
        room = self.db.add_room("room1_name", self.area_id, "room1_description")
        id, name, description, area_id = room 
        self.assertEqual(name, "room1_name")
        self.assertEqual(description, "room1_description")
        self.assertEqual(area_id, self.area_id)

    def testNonEmptyListRooms(self):
        room = self.db.add_room("room1_name", self.area_id, "room1_description")
        list_rooms = self.db.list_rooms()
        self.assertEqual(len(list_rooms), 1)
        id, name, description, area_id = list_rooms[0]
        self.assertEqual(name, "room1_name")
        self.assertEqual(description, "room1_description")
        self.assertEqual(area_id, self.area_id)

    def testGetRoomById(self):
        ''' Add an room and find it by id '''
        room = self.db.add_room("room2_name", self.area_id, "room2_description")
        id, name, description, area_id = room 
        room2 = self.db.get_room_by_id(id)
        id2, name2, description2, area_id2 = room2 
        self.assertEqual(id2, id)
        self.assertEqual(name2, "room2_name")
        self.assertEqual(description2, "room2_description")
        self.assertEqual(area_id2, self.area_id)

    def testGetRoomByName(self):
        ''' Add an room and find it by name '''
        room = self.db.add_room("room3_name", self.area_id, "room3_description")
        id, name, description, area_id = room 
        room3 = self.db.get_room_by_name(name)
        id3, name3, description3, area_id3 = room3 
        self.assertEqual(id3, id)
        self.assertEqual(name3, "room3_name")
        self.assertEqual(description3, "room3_description")
        self.assertEqual(area_id3, self.area_id)

    def testDelRoom(self):
        ''' Add and delete an room'''
        room = self.db.add_room("room4_name", self.area_id, "room4_description")
        id, name, description, area_id = room 
        self.db.del_room(id)
        room_id = self.db.get_room_by_id(id)
        room_name = self.db.get_room_by_name(name)
        self.assertEqual(room_id, None)
        self.assertEqual(room_name, None)

    def testSearchRooms(self):
        ''' Add an room and search it '''
        room = self.db.add_room("room5_name", self.area_id, "room5_description")
        id, name, description, area_id = room 
        room_searched = self.db.search_rooms(name="room5_name")
        self.assertNotEqual(room_searched, [])
        id2, name2, description2, area_id2 = room_searched[0] 
        self.assertEqual(id2, id)
        self.assertEqual(name2, "room5_name")
        self.assertEqual(description2, "room5_description")
        self.assertEqual(area_id2, self.area_id)

    def testGetAllRoomsOfArea(self):
        ''' Add some rooms in an area and check they are listed '''
        rooms = []
        for i in range(4):
            room = self.db.add_room("room_name" + str(i), self.area_id, "room_description" + str(i))
            rooms.append(room)
        rooms_listed = self.db.get_all_rooms_of_area(self.area_id)
        self.assertEqual(len(rooms_listed), len(rooms))
        for room in rooms:
            assert room in rooms_listed

    def testDeleteAreaAndAllRooms(self):
        ''' Check all rooms of an area are deleted when the area is '''
        for i in range(4):
            room = self.db.add_room("room_name" + str(i), self.area_id, "room_description" + str(i))
        self.db.del_area(self.area_id)
        self.assertEqual(self.db.list_rooms(), [])

            
class DeviceCategoryTestCase(GenericTestCase):
    ''' Test device category mapping
    '''
    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_device_categories(self.db.get_helper())

    def tearDown(self):
        self.remove_all_device_categories(self.db.get_helper())
        del self.db

    def testEmptyListDeviceCategories(self):
        ''' List all existing device_categories'''
        list_device_categories = self.db.list_device_categories()
        self.assertEqual(list_device_categories,[])

    def testAddDeviceCategory(self):
        ''' Add a device_category'''
        device_category = self.db.add_device_category("device_category1_name", "device_category1_description")
        id, name, description = device_category 
        self.assertEqual(name, "device_category1_name")
        self.assertEqual(description, "device_category1_description")

    def testNonEmptyListDeviceCategories(self):
        device_category = self.db.add_device_category("device_category2_name", "device_category2_description")
        list_device_categories = self.db.list_device_categories()
        self.assertEqual(len(list_device_categories), 1)
        id, name, description = list_device_categories[0]
        self.assertEqual(name, "device_category2_name")
        self.assertEqual(description, "device_category2_description")

    def testGetDeviceCategoryByName(self):
        ''' Add an device_category and find it by name '''
        device_category = self.db.add_device_category("device_category3_name", "device_category3_description")
        id, name, description = device_category 
        device_category3 = self.db.get_device_category_by_name(name)
        id3, name3, description3 = device_category3 
        self.assertEqual(id3, id)
        self.assertEqual(name3, "device_category3_name")
        self.assertEqual(description3, "device_category3_description")

    def testGetUnexistingDeviceCategoryByName(self):
        ''' try to find an unexisting device '''
        self.assertEqual(self.db.get_device_category_by_name("nonexisting"), None)

    def testGetAllDevicesOfCategory(self):
        ''' Add a few devices and check the method find them '''
        dc1 = self.db.add_device_category("device_category3_name", "device_category3_description")
        area1 = self.db.add_area('area1','description 1')
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        room1 = self.db.add_room('room1', area1[0])
        devices = []
        for i in range(5):
            devices.append(self.db.add_device(d_name='device' + str(i), d_address = 'A' + str(i), d_technology_id = dt1[0], d_type = u'lamp',
                              d_category_id = dc1[0], d_room_id = room1[0], d_description = 'desc' + str(i),
                              d_is_resetable = True, d_initial_value = 30,
                              d_is_value_changeable_by_user = False, d_unit_of_stored_values = u'Percent'))
        devices2 = self.db.get_all_devices_of_category(dc1[0])
        for device in devices2:
            assert device in devices
        self.assertEqual(len(devices), len(devices2))
        

    def testDelDeviceCategory(self):
        ''' Add and delete an device_category'''
        device_category = self.db.add_device_category("device_category4_name", "device_category4_description")
        id, name, description = device_category 
        self.db.del_device_category(id)
        device_category_name = self.db.get_device_category_by_name(name)
        self.assertEqual(device_category_name, None)


class DeviceTechnologyTestCase(GenericTestCase):
    """
    Test device technologies
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_device_technologies(self.db.get_helper())

    def tearDown(self):
        self.remove_all_device_technologies(self.db.get_helper())
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_device_technologies()), 0)

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2', u'wired')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        self.assertEqual(len(self.db.list_device_technologies()), 3)
        assert self.has_item(self.db.list_device_technologies(), [u'x10', u'1wire', u'PLCBus'])

    def testGetDeviceTechnologyByName(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        self.assertEqual(self.db.get_device_technology_by_name('x10'), dt1)
        self.assertEqual(self.db.get_device_technology_by_name('nonexisting'), None)

    def testFetchInformation(self):
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2', u'wired')
        self.assertEqual(self.db.get_device_technology_by_name(u'1wire')[1], u'1wire')

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt2 = self.db.add_device_technology(u'1wire', 'desc dt2', u'wired')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        self.db.del_device_technology(dt2[0])
        assert self.has_item(self.db.list_device_technologies(), [u'x10', u'PLCBus']), "Couldn't find 'x10' and 'PLCBus'"
        assert not self.has_item(self.db.list_device_technologies(), [u'1wire']), "'1wire' was NOT deleted"

    def testGetAllDevicesOfTechnology(self):
        ''' Add a few devices and check the method find them '''
        dc1 = self.db.add_device_category("device_category3_name", "device_category3_description")
        area1 = self.db.add_area('area1','description 1')
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        room1 = self.db.add_room('room1', area1[0])
        devices = []
        for i in range(5):
            devices.append(self.db.add_device(d_name='device' + str(i), d_address = 'A' + str(i), d_technology_id = dt1[0], d_type = u'lamp',
                              d_category_id = dc1[0], d_room_id = room1[0], d_description = 'desc' + str(i),
                              d_is_resetable = True, d_initial_value = 30,
                              d_is_value_changeable_by_user = False, d_unit_of_stored_values = u'Percent'))
        devices2 = self.db.get_all_devices_of_technology(dt1[0])
        for device in devices2:
            assert device in devices
        self.assertEqual(len(devices), len(devices2))
       

class DeviceTechnologyConfigTestCase(GenericTestCase):
    """
    Test device technology configurations
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_device_technology_config(self.db.get_helper())
        self.remove_all_device_technologies(self.db.get_helper())

    def tearDown(self):
        self.remove_all_device_technology_config(self.db.get_helper())
        self.remove_all_device_technologies(self.db.get_helper())
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_all_device_technology_config()), 0)

    def testAdd(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        dtc1_1 = self.db.add_device_technology_config(dt1[0], 'key1_1', 'val1_1', 'desc1')
        dtc1_2 = self.db.add_device_technology_config(dt1[0], 'key1_2', 'val1_2', 'desc2')
        dtc3_1 = self.db.add_device_technology_config(dt3[0], 'key3_1', 'val3_1', 'desc3')
        dtc3_2 = self.db.add_device_technology_config(dt3[0], 'key3_2', 'val3_2', 'desc4')
        dtc3_3 = self.db.add_device_technology_config(dt3[0], 'key3_3', 'val3_3', 'desc5')
        try:
            duplicate_key = False
            dtc = self.db.add_device_technology_config(dt3[0], 'key3_3', 'val3_3', 'desc')
            duplicate_key = True
        except DbHelperException:
            pass

        assert not duplicate_key, "It shouldn't have been possible to add 'key3_3' for device technology %s : it already exists" % dt3[0]
        self.assertEqual(len(self.db.list_device_technology_config(dt1[0])),  2)
        self.assertEqual(len(self.db.list_device_technology_config(dt3[0])), 3)

    def testNonEmptyList(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dtc1_1 = self.db.add_device_technology_config(dt1[0], 'key1_1', 'val1_1', 'desc1')
        dtc1_2 = self.db.add_device_technology_config(dt1[0], 'key1_2', 'val1_2', 'desc2')
        self.assertEqual(len(self.db.list_all_device_technology_config()), 2)

    def testGet(self):
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        dtc3_1 = self.db.add_device_technology_config(dt3[0], 'key3_1', 'val3_1', 'desc3_1')
        dtc3_2 = self.db.add_device_technology_config(dt3[0], 'key3_2', 'val3_2', 'desc3_2')
        dtc3_3 = self.db.add_device_technology_config(dt3[0], 'key3_3', 'val3_3', 'desc3_3')
        dtc = self.db.get_device_technology_config(dt3[0], 'key3_2')
        self.assertEqual(dtc[2], 'val3_2')

    def testDel(self):
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dt3 = self.db.add_device_technology(u'PLCBus', 'desc dt3', u'cpl')
        dtc1_1 = self.db.add_device_technology_config(dt1[0], 'key1_1', 'val1_1', 'desc1')
        dtc1_2 = self.db.add_device_technology_config(dt1[0], 'key1_2', 'val1_2', 'desc2')
        dtc3_1 = self.db.add_device_technology_config(dt3[0], 'key3_1', 'val3_1', 'desc3')
        dtc3_2 = self.db.add_device_technology_config(dt3[0], 'key3_2', 'val3_2', 'desc4')
        dtc3_3 = self.db.add_device_technology_config(dt3[0], 'key3_3', 'val3_3', 'desc5')
        self.db.del_device_technology_config(dtc3_2[0])
        self.assertEqual(self.db.get_device_technology_config(dt3[0], 'key3_2'), None)


class DeviceTestCase(GenericTestCase):
    """
    Test device
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_devices(self.db.get_helper())

    def tearDown(self):
        self.remove_all_devices(self.db.get_helper())
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_devices()),0)

    def testAdd(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dc1 = self.db.add_device_category('dc1')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1', d_technology_id = dt1[0], d_type = u'lamp',
                              d_category_id = dc1[0], d_room_id = room1[0], d_description = 'desc1',
                              d_is_resetable = True, d_initial_value = 30,
                              d_is_value_changeable_by_user = False, d_unit_of_stored_values = u'Percent')
        self.assertEqual(len(self.db.list_devices()),1)
        self.assertEqual(device1[6], "lamp")
        self.assertNotEqual(device1, "appliance")

    def testEmptyGetDevice(self):
        """ Test a get of unexisting device """
        self.assertEqual(self.db.get_device(11111111111), None)

    def testUpdate(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dc1 = self.db.add_device_category('dc1')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1', d_technology_id = dt1[0], d_type = u'lamp',
                              d_category_id = dc1[0], d_room_id = room1[0], d_description = 'desc1',
                              d_is_resetable = True, d_initial_value = 30,
                              d_is_value_changeable_by_user = False, d_unit_of_stored_values = u'Percent')
        device_id = device1[0]
        device1 = self.db.update_device(d_id = device1[0], d_description = 'desc2')
        device2 = self.db.get_device(device_id)
        self.assertEqual(device2[2], 'desc2')

    def testFindAndSearch(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room('room1', area1[0])
        room2 = self.db.add_room('room2', area2[0])
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dc1 = self.db.add_device_category('dc1')
        dc2 = self.db.add_device_category('dc2')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1', d_technology_id = dt1[0], d_type = u'lamp',
                              d_category_id = dc1[0], d_room_id = room1[0], d_description = 'desc1',
                              d_is_resetable = True, d_initial_value = 30,
                              d_is_value_changeable_by_user = False, d_unit_of_stored_values = u'Percent')
        device2 = self.db.add_device(d_name='device2', d_address='A2', d_technology_id=dt1[0], d_type = u'appliance',
                              d_category_id=dc1[0], d_room_id=room1[0])
        device3 = self.db.add_device(d_name='device3', d_address='A3', d_technology_id=dt1[0], d_type = u'appliance',
                              d_category_id=dc2[0], d_room_id=room2[0])

        self.assertEqual(len(self.db.list_devices()),3)
        self.assertEqual(len(self.db.get_all_devices_of_room(room1[0])),2)
        self.assertEqual(len(self.db.get_all_devices_of_room(room2[0])),1)
        self.assertEqual(len(self.db.get_all_devices_of_area(area1[0])),2)
        self.assertEqual(len(self.db.get_all_devices_of_area(area2[0])),1)


        nb_of_dev = len(self.db.search_devices(category_id=dc1[0], room_id=room1[0]))
        self.assertEqual(nb_of_dev,2)
        nb_of_dev = len(self.db.search_devices(address='A2'))
        self.assertEqual(nb_of_dev,1)
        nb_of_dev = len(self.db.search_devices(address='A1544'))
        self.assertEqual(nb_of_dev,0)

        device_list = self.db.find_devices(None, None)
        self.assertEqual(len(device_list),3)
        device_list = self.db.find_devices([], [])
        self.assertEqual(len(device_list),3)
        device_list = self.db.find_devices([room1[0], room2[0]], [dc1[0], dc2[0]])
        self.assertEqual(len(device_list),3)
        device_list = self.db.find_devices([room1[0]], [dc1[0], dc2[0]])
        self.assertEqual(len(device_list),2)
        device_list = self.db.find_devices([room2[0]], None)
        self.assertEqual(len(device_list),1)
        device_list = self.db.find_devices([room2[0]], [])
        self.assertEqual(len(device_list),1)
        device_list = self.db.find_devices([room1[0]], [dc2[0]])
        self.assertEqual(len(device_list),0)
        device_list = self.db.find_devices([room1[0], room2[0]], [dc2[0]])
        self.assertEqual(len(device_list),1)

    def testDel(self):
        area1 = self.db.add_area('area1','description 1')
        area2 = self.db.add_area('area2','description 2')
        room1 = self.db.add_room('room1', area1[0])
        room2 = self.db.add_room('room2', area2[0])
        dt1 = self.db.add_device_technology(u'x10', 'desc dt1', u'cpl')
        dc1 = self.db.add_device_category('dc1')
        dc2 = self.db.add_device_category('dc2')
        device1 = self.db.add_device(d_name='device1', d_address = 'A1', d_technology_id = dt1[0], d_type = u'lamp',
                              d_category_id = dc1[0], d_room_id = room1[0], d_description = 'desc1',
                              d_is_resetable = True, d_initial_value = 30,
                              d_is_value_changeable_by_user = False, d_unit_of_stored_values = u'Percent')
        device2 = self.db.add_device(d_name='device2', d_address='A2', d_technology_id=dt1[0], d_type = u'appliance',
                              d_category_id=dc1[0], d_room_id=room1[0])
        device3 = self.db.add_device(d_name='device3', d_address='A3', d_technology_id=dt1[0], d_type = u'appliance',
                              d_category_id=dc2[0], d_room_id=room2[0])
        self.db.del_device(device2[0])
        self.assertEqual(len(self.db.list_devices()),2)
        self.assertEqual(self.db.list_devices()[0][3], 'A1')


class DeviceStatsTestCase(GenericTestCase):
    """
    Test device stats
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_device_stats(self.db.get_helper())

    def tearDown(self):
        self.remove_all_device_stats(self.db.get_helper())
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_all_device_stats()),0)

    def testAdd(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dc1 = self.db.add_device_category("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        device2 = self.db.add_device(d_name='device2', d_address = "A2", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        device3 = self.db.add_device(d_name='device3', d_address = "A3", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        device4 = self.db.add_device(d_name='device4', d_address = "A4", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1[0], now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1[0], now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2[0], now, {'val1': '40', 'val2': '41' })
        d_stat3_1 = self.db.add_device_stat(device3[0], now, {'val1': '100', 'val2': '101' })
        l_stats = self.db.list_device_stats(device1[0])
        self.assertEqual(len(l_stats),2)

        l_stats = self.db.list_device_stats(device2[0])
        self.assertEqual(len(l_stats),1)

        assert self.db.device_has_stats(device1[0])
        assert not self.db.device_has_stats(device4[0])

    def testDelDeviceStat(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dc1 = self.db.add_device_category("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1[0], now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1[0], now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })
        self.db.del_device_stat(d_stat1_1[0])
        self.db.del_device_stat(d_stat1_2[0])
        self.assertEqual(len(self.db.list_all_device_stats()),0)

    def testNonEmptyList(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dc1 = self.db.add_device_category("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1[0], now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1[0], now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })
        self.assertEqual(len(self.db.list_all_device_stats()),2)
        for device in self.db.list_all_device_stats():
            assert device in [d_stat1_1, d_stat1_2]

    def testLastStatOfOneDevice(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dc1 = self.db.add_device_category("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1[0], now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1[0], now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })

        stat = self.db.get_last_stat_of_device(device1[0])
        dsv = self.db.list_device_stats_values(stat[0])
        for item in dsv:
            if item[1] == 'val1':
                assert item[2] == '11', "Should get value '11' for last stat of device %s. Got %s instead" \
                                              % (device1[0], dsv[0].value)
            elif item[1] == 'val2':
                assert item[2] == '12', "Should get value '12' for last stat of device %s. Got %s instead" \
                                              % (device1[0], dsv[1].value)

    def testLastStatOfDevices(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dc1 = self.db.add_device_category("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        device2 = self.db.add_device(d_name='device2', d_address = "A2", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        device3 = self.db.add_device(d_name='device3', d_address = "A3", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        device4 = self.db.add_device(d_name='device4', d_address = "A4", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1[0], now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1[0], now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2[0], now, {'val1': '40', 'val2': '41' })
        d_stat3_1 = self.db.add_device_stat(device3[0], now, {'val1': '100', 'val2': '101' })
        #l_stats = self.db.list_device_stats(device1[0])

        l_stats = self.db.get_last_stat_of_devices([device1[0], device2[0]])
        self.assertEqual(len(l_stats),2)
        device_id_list = []
        for stat in l_stats:
            device_id_list.append(stat[1])
            if stat[1] == device1[0]:
                # Make sure we get the LAST stat for device1
                dsv = self.db.list_device_stats_values(stat[0])
                value_list = []
                for item in dsv:
                    value_list.append(item[2])
                assert '11' in value_list and '12' in value_list
        assert device1[0] in device_id_list, "device1 is not in the list but should have been"
        assert device2[0] in device_id_list, "device2 is not in the list but should have been"

    def testDel(self):
        dt1 = self.db.add_device_technology(u"x10", "this is x10", u"cpl")
        dc1 = self.db.add_device_category("lighting")
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        device1 = self.db.add_device(d_name='device1', d_address = "A1", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        device2 = self.db.add_device(d_name='device2', d_address = "A2", d_technology_id = dt1[0], d_type = u"lamp",
                              d_category_id = dc1[0], d_room_id = room1[0])
        now = datetime.datetime.now()
        d_stat1_1 = self.db.add_device_stat(device1[0], now, {'val1': '10', 'val2': '10.5' })
        d_stat1_2 = self.db.add_device_stat(device1[0], now + datetime.timedelta(seconds=1), {'val1': '11', 'val2': '12' })
        d_stat2_1 = self.db.add_device_stat(device2[0], now, {'val1': '40', 'val2': '41' })
        self.db.del_all_device_stats(device1[0])
        l_stats = self.db.list_device_stats(device1[0])
        self.assertEqual(len(l_stats),0)
        l_stats = self.db.list_device_stats(device2[0])
        self.assertEqual(len(l_stats),1)


class TriggersTestCase(GenericTestCase):
    """
    Test triggers
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_triggers(self.db.get_helper())

    def tearDown(self):
        self.remove_all_triggers(self.db.get_helper())
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_triggers()),0)

    def testAdd(self):
        trigger1 = self.db.add_trigger(t_description = 'desc1',
                                t_rule = 'AND(x,OR(y,z))', t_result= ['x10_on("a3")','1wire()'])
        trigger2 = self.db.add_trigger(t_description = 'desc2',
                                t_rule = 'OR(x,AND(y,z))', t_result= ['x10_on("a2")','1wire()'])
        self.assertEqual(len(self.db.list_triggers()),2)
        self.assertEqual(self.db.get_trigger(trigger1[0])[1], 'desc1')

    def testDel(self):
        trigger1 = self.db.add_trigger(t_description = 'desc1',
                                t_rule = 'AND(x,OR(y,z))', t_result= ['x10_on("a3")','1wire()'])
        trigger2 = self.db.add_trigger(t_description = 'desc2',
                                t_rule = 'OR(x,AND(y,z))', t_result= ['x10_on("a2")','1wire()'])
        for trigger in self.db.list_triggers():
            self.db.del_trigger(trigger[0])
        self.assertEqual(len(self.db.list_triggers()),0)


class UserAndSystemAccountsTestCase(GenericTestCase):
    """
    Test user and system accounts
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_user_accounts(self.db.get_helper())
        self.remove_all_system_accounts(self.db.get_helper())

    def tearDown(self):
        self.remove_all_user_accounts(self.db.get_helper())
        self.remove_all_system_accounts(self.db.get_helper())
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_system_accounts()),0)
        self.assertEqual(len(self.db.list_user_accounts()),0)

    def testAdd(self):
        sys1 = self.db.add_system_account(a_login = 'mschneider', a_password = 'IwontGiveIt', a_is_admin = True)
        assert self.db.is_system_account('mschneider', 'IwontGiveIt'), "is_system_account should have returned True"
        assert not self.db.is_system_account('mschneider', 'plop'), "is_system_account should have returned False"
        assert not self.db.is_system_account('hello', 'boy'), "is_system_account should have returned False"
        sys1 = self.db.get_system_account_by_login_and_pass('mschneider', 'IwontGiveIt')
        assert sys1 is not None, "Should have found an account 'mschneider'"
        assert sys1[1] == 'mschneider', "Login should be 'mschneider' but is '%s'" %sys1[1]
        try:
            self.db.add_system_account(a_login = 'mschneider', a_password = 'plop', a_is_admin = True)
            error = False
        except DbHelperException:
            error = True
        assert error, "It shouldn't have been possible to add login %s. It already exists!" % 'mschneider'
        sys2 = self.db.add_system_account(a_login = 'lonely', a_password = 'boy', a_is_admin = True, a_skin_used='myskin')
        sys3 = self.db.add_system_account(a_login = 'domo', a_password = 'gik', a_is_admin = True)
        user1 = self.db.add_user_account(u_first_name='Marc', u_last_name='SCHNEIDER', u_birthdate=datetime.date(1973, 4, 24),
                                  u_system_account_id = sys1[0])
        user2 = self.db.add_user_account(u_first_name='Monthy', u_last_name='PYTHON', u_birthdate=datetime.date(1981, 4, 24))
        self.assertEqual(len(self.db.list_user_accounts()),2)

        self.assertEqual(len(self.db.list_system_accounts()),3)

    def testAddDefaultSystemAccount(self):
        id, login, is_admin, skin_used = self.db.add_default_system_account()
        self.assertEqual(login, "admin")
        self.assertEqual(is_admin, True)

    def testGet(self):
        sys1 = self.db.add_system_account(a_login = 'mschneider', a_password = 'IwontGiveIt', a_is_admin = True)
        sys2 = self.db.add_system_account(a_login = 'lonely', a_password = 'boy', a_is_admin = True, a_skin_used='myskin')
        sys3 = self.db.add_system_account(a_login = 'domo', a_password = 'gik', a_is_admin = True)
        user1 = self.db.add_user_account(u_first_name='Marc', u_last_name='SCHNEIDER', u_birthdate=datetime.date(1973, 4, 24),
                                  u_system_account_id = sys1[0])
        user2 = self.db.add_user_account(u_first_name='Monthy', u_last_name='PYTHON', u_birthdate=datetime.date(1981, 4, 24))

        self.assertEqual(self.db.get_system_account(sys1[0])[1], 'mschneider')

        assert self.db.get_system_account_by_login('mschneider') is not None
        self.assertEqual(self.db.get_system_account_by_login('mschneider')[0], sys1[0])
        assert self.db.get_system_account_by_login('lucyfer') is None
        login = self.db.get_system_account_by_user(user1[0])[1]
        self.assertEqual(login, 'mschneider')

        self.assertEqual(self.db.get_user_account(user1[0])[1], 'Marc')

        self.assertEqual(self.db.get_user_account(user2[0])[2], 'PYTHON')


        assert self.db.get_user_account_by_system_account(sys1[0]) is not None

        self.assertEqual(self.db.get_user_account_by_system_account(sys1[0])[1], 'Marc')
        assert self.db.get_user_account_by_system_account(sys3[0]) is None


    def testDel(self):
        sys1 = self.db.add_system_account(a_login = 'mschneider', a_password = 'IwontGiveIt', a_is_admin = True)
        sys2 = self.db.add_system_account(a_login = 'lonely', a_password = 'boy', a_is_admin = True, a_skin_used='myskin')
        sys3 = self.db.add_system_account(a_login = 'domo', a_password = 'gik', a_is_admin = True)
        user1 = self.db.add_user_account(u_first_name='Marc', u_last_name='SCHNEIDER', u_birthdate=datetime.date(1973, 4, 24),
                                  u_system_account_id = sys1[0])
        user2 = self.db.add_user_account(u_first_name='Monthy', u_last_name='PYTHON', u_birthdate=datetime.date(1981, 4, 24))
        sys_temp = self.db.add_system_account(a_login = 'fantom', a_password = 'as', a_is_admin = False)
        self.db.del_system_account(sys_temp[0])
        l_sys = self.db.list_system_accounts()
        self.assertNotEqual(len(l_sys), 0)
        for sys in l_sys:
            assert sys[1] != 'fantom', "System account with 'fantom' login was NOT deleted"
        self.db.del_user_account(user1[0])
        found_user2 = False
        for user in self.db.list_user_accounts():
            assert user[0] != user1[0], "User %s was NOT deleted" % user1[0]
            found_user2 = (user[0] == user2[0])
        assert found_user2, "User %s was deleted, but shouldn't have been" % user2[0]
        # Make sure associated system account has been deleted
        l_sys = self.db.list_system_accounts()
        assert len(l_sys) > 0, "The list is empty but it shouldn't"
        for sys in l_sys:
            assert sys[1] != 'mschneider', "System account with 'mschneider' login was NOT deleted"


class SystemStatsTestCase(GenericTestCase):
    """
    Test system stats
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.db.del_all_system_stats()

    def tearDown(self):
        self.db.del_all_system_stats()
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_system_stats()),0)


    def testAdd(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv))
        self.assertEqual(len(self.db.list_system_stats()),4)

    def testListAndGet(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv))
        system_stat1 = self.db.get_system_stat(sstat_list[1][0])
        ssv = self.db.list_system_stats_values(system_stat1[0])
        self.assertEqual(len(ssv),2)
        self.assertEqual(ssv[0][-1], '2')

    def testDel(self):
        now = datetime.datetime.now()
        sstat_list = []
        for i in range(4):
            ssv = {'ssv1': (i*2), 'ssv2': (i*3),}
            sstat_list.append(self.db.add_system_stat("sstat%s" %i, 'localhost',
                                now + datetime.timedelta(seconds=i), ssv))
        self.db.del_system_stat("sstat0")
        self.assertEqual(len(self.db.list_system_stats()),3)
        self.db.del_all_system_stats()
        self.assertEqual(len(self.db.list_system_stats()),0)
        ssv = self.db.list_system_stats()
        self.assertEqual(len(ssv),0)


class ItemUIConfigTestCase(GenericTestCase):
    """
    Test item UI config
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()
        self.remove_all_item_ui_config(self.db.get_helper())

    def tearDown(self):
        self.remove_all_item_ui_config(self.db.get_helper())
        del self.db

    def testEmptyList(self):
        self.assertEqual(len(self.db.list_all_item_ui_config()),0)

    def testAdd(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        self.db.add_item_ui_config(area1[0], 'area', param_a1='value_a1', param_a2='value_a2')
        self.db.add_item_ui_config(room1[0], 'room', param_r1='value_r1', param_r2='value_r2')
        value_dict = self.db.list_item_ui_config(room1[0], 'room')
        self.assertEqual(value_dict, {'param_r1': 'value_r1', 'param_r2': 'value_r2'})
        uic = self.db.get_item_ui_config(room1[0], 'room', 'param_r2')
        self.assertEqual(uic[3], 'value_r2')
        uic = self.db.get_item_ui_config(area1[0], 'area', 'param_a1')
        self.assertEqual(uic[3], 'value_a1')
        error = False
        try:
            self.db.get_item_ui_config(area1[0], 'foo', 'param_a1')
        except DbHelperException:
            error = True
        assert error is True, "Shouldn't have found any param values for (%s, %s)" % (area1[0], 'foo')
        try:
            self.db.add_item_ui_config(800000000, 'area', param_a1='value_a1', param_a2='value_a2')
        except DbHelperException:
            error = True
        assert error is True, "Shouldn't have been able to add parameters with this item[0] which doesn't exist"

    def testNotEmptyList(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        self.db.add_item_ui_config(area1[0], 'area', param_a1='value_a1', param_a2='value_a2')
        self.db.add_item_ui_config(room1[0], 'room', param_r1='value_r1', param_r2='value_r2')
        self.assertEqual(len(self.db.list_all_item_ui_config()),4)

    def testUpdate(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        self.db.add_item_ui_config(area1[0], 'area', param_a1='value_a1', param_a2='value_a2')
        self.db.add_item_ui_config(room1[0], 'room', param_r1='value_r1', param_r2='value_r2')
        uic = self.db.update_item_ui_config(area1[0], 'area', 'param_a1', 'new_value_a1')
        uic = self.db.get_item_ui_config(area1[0], 'area', 'param_a1')
        self.assertEqual(uic[3], 'new_value_a1')

    def testDel(self):
        area1 = self.db.add_area('area1','description 1')
        room1 = self.db.add_room('room1', area1[0])
        self.db.add_item_ui_config(area1[0], 'area', param_a1='value_a1', param_a2='value_a2')
        self.db.add_item_ui_config(room1[0], 'room', param_r1='value_r1', param_r2='value_r2')
        self.db.add_item_ui_config(area1[0], 'area', param_a3='value_a3')
        self.db.delete_item_ui_config(area1[0], 'area', 'param_a3')
        assert 'param_a1' in self.db.list_item_ui_config(area1[0], 'area').keys(), "param_a1 should have been found"
        assert 'param_a3' not in self.db.list_item_ui_config(area1[0], 'area').keys(), "param_a3 should NOT have been found"
        self.db.delete_all_item_ui_config(area1[0], 'area')
        self.assertEqual(len(self.db.list_item_ui_config(area1[0], 'area')),0)


class SystemConfigTestCase(GenericTestCase):
    """
    Test system config
    """

    def setUp(self):
        self.db = XmlRpcDbHelper()

    def tearDown(self):
        del self.db

    def testUpdate(self):
        system_config = self.db.update_system_config(s_simulation_mode=True, s_debug_mode=True)
        assert system_config[1], "System should be in simulation mode but it is NOT"
        assert system_config[2], "System should be in debug mode but it is NOT"
        system_config = self.db.update_system_config(s_simulation_mode=False)
        assert not system_config[1], "System shouldn't be in simulation mode, but it IS"
        system_config = self.db.get_system_config()
        assert system_config[2], "System should be in debug mode but it is NOT"


if __name__ == "__main__":
    unittest.main()
if __name__ == "__main__":
    unittest.main()

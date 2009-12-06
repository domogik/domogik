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

from domogik.common.database_xmlrpc import XmlRpcDbHelper

class GenericTestCase(unittest.TestCase):
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
        remove_all_device_technology_config(self, db)
        for dt in db.list_device_technologies():
            db.del_device_technology(dt.id)

    def remove_all_device_technology_config(self, db):
        """
        Remove all configurations of device technologies
        @param db : db API instance
        """
        for dtc in db._session.query(DeviceTechnologyConfig).all():
            db._session.delete(dtc)

    def remove_all_device_stats(self, db):
        """
        Remove all device stats
        @param db : db API instance
        """
        for device in db.list_devices():
            db.del_all_device_stats(device.id)

    def remove_all_item_ui_config(self, db):
        """
        Remove all ui configuration parameters of all items (area, room, device)
        @param db : db API instance
        """
        for iuc in db._session.query(ItemUIConfig).all():
            db._session.delete(iuc)
            
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
        assert len(list_areas) == 1
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

    def testDelDeviceCategory(self):
        ''' Add and delete an device_category'''
        device_category = self.db.add_device_category("device_category4_name", "device_category4_description")
        id, name, description = device_category 
        self.db.del_device_category(id)
        device_category_name = self.db.get_device_category_by_name(name)
        self.assertEqual(device_category_name, None)


if __name__ == "__main__":
    unittest.main()

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

Implements
==========

- No class

@author: Marc SCHNEIDER
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import time
import datetime

from domogik.common.database import DbHelper, DbHelperException
from domogik.common.sql_schema import Area, Device, DeviceCategory, DeviceConfig, \
                                      DeviceStats, DeviceTechnology, DeviceTechnologyConfig, \
                                      Room, UserAccount, SystemAccount, Trigger


def print_title(title):
    """
    Print a title in color
    """
    COLOR = '\033[92m'
    ENDC = '\033[0m'
    print "\n\n"
    print COLOR
    print "=" * (len(title) + 8)
    print "=== %s ===" % title
    print "=" * (len(title) + 8)
    print ENDC

def print_test(test):
    """
    Print a test title in color
    """
    COLOR = '\033[31m'
    ENDC = '\033[37m'
    print COLOR
    print "= %s =" % test
    print ENDC

def has_item(item_list, item_name_list):
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

def remove_all_areas(db):
    """
    Remove all areas
    @param db : db API instance
    """
    for area in db.list_areas():
        db.del_area(area.id)

def remove_all_rooms(db):
    """
    Remove all rooms
    @param db : db API instance
    """
    for room in db.list_rooms():
        db.del_room(room.id)

def remove_all_device_categories(db):
    """
    Remove all device categories
    @param db : db API instance
    """
    for dc in db.list_device_categories():
        db.del_device_category(dc.id)

def remove_all_device_technologies(db):
    """
    Remove all device technologies
    @param db : db API instance
    """
    for dt in db.list_device_technologies():
        db.del_device_technology(dt.id)

def remove_all_device_technology_config(db):
    """
    Remove all configurations of device technologies
    @param db : db API instance
    """
    for dtc in db._session.query(DeviceTechnologyConfig).all():
        db._session.delete(dtc)

def remove_all_device_stats(db):
    """
    Remove all device stats
    @param db : db API instance
    """
    for device in db.list_devices():
        db.del_all_device_stats(device.id)

if __name__ == "__main__":
    print_test('*********** Starting tests ***********')
    d = DbHelper()

    print_title('test area')
    remove_all_areas(d)
    assert len(d.list_areas()) == 0, "Area list is not empty"
    print_test('add area')
    area0 = d.add_area('area0','description 0')
    assert d.list_areas()[0].name == 'area0', "area0 not found"
    print_test('fetch informations for area0')
    area0 = d.get_area_by_name('area0')
    assert area0.name == 'area0', 'area0 not found'
    print_test('del area')
    d.del_area(area0.id)
    assert not has_item(d.list_areas(), ['area0']), "area0 was NOT deleted"

    print_title('test room')
    remove_all_areas(d)
    remove_all_rooms(d)
    area1 = d.add_area('area1','description 1')
    area2 = d.add_area('area2','description 2')
    assert len(d.list_areas()) == 2, "Area list should have 2 items, it has %s" % len(d.list_areas())
    print_test('list room')
    assert len(d.list_rooms()) == 0, "Room list is not empty : %s" % d.list_rooms()
    print_test('add room')
    room1 = d.add_room('room1', 'description 1', area1.id)
    room2 = d.add_room('room2', 'description 2', area1.id)
    room3 = d.add_room('room3', 'description 3', area2.id)
    print_test('list room')
    assert len(d.list_rooms()) == 3, "Room list should have 3 items, it has %s" % len(d.list_rooms())
    print_test('= get all rooms of area1')
    assert len(d.get_all_room_of_area(area1)) == 2, \
      "Area1 should have 2 rooms, it has %s" % len(d.get_all_room_of_area(area1))
    print_test('= get all rooms of area2')
    assert len(d.get_all_room_of_area(area2)) == 1, \
      "Area2 should have 1 room, it has %s" % len(d.get_all_room_of_area(area2))
    print_test('get room by name')
    assert d.get_room_by_name('room1').name == 'room1', "Couldn't find room1"
    print_test('del room')
    d.del_room(room1.id)
    assert not has_item(d.list_rooms(), ['room1']), "room1 was NOT deleted"
    assert has_item(d.list_rooms(), ['room2', 'room3']), "rooms were deleted but shouldn't have been"

    print_title('test device_category')
    remove_all_device_categories(d)
    print_test('list device_category')
    assert len(d.list_device_categories()) == 0, "There should have no device category"
    print_test('add device_category')
    dc1 = d.add_device_category('dc1')
    dc2 = d.add_device_category('dc2')
    assert len(d.list_device_categories()) == 2, "%s devices categories found, instead of 2 " \
                                                  % len(d.list_device_categories())
    assert has_item(d.list_device_categories(), ['dc1', 'dc2']), "Couldn't find all device categories"
    print_test('fetch informations')
    assert d.get_device_category_by_name('dc1').name == 'dc1', "DeviceCategory dc1 was not found"
    print_test('del device category')
    d.del_device_category(dc2.id)
    assert has_item(d.list_device_categories(), ['dc1']), "Couldn't find 'dc1'"
    assert not has_item(d.list_device_categories(), ['dc2']), "'dc2' was NOT deleted"

    print_title('test device_technology')
    remove_all_device_technologies(d)
    print_test('list device_technology')
    assert len(d.list_device_technologies()) == 0, "There should have no device technology"
    print_test('add device_technology')
    dt1 = d.add_device_technology('dt1', 'desc dt1', 'cpl')
    dt2 = d.add_device_technology('dt2', 'desc dt2', 'wired')
    dt3 = d.add_device_technology('dt3', 'desc dt3', 'wifi')
    assert len(d.list_device_technologies()) == 3, "%s devices technologies found, instead of 3 " \
                                                  % len(d.list_device_technologies())
    assert has_item(d.list_device_technologies(), ['dt1', 'dt2', 'dt3']), \
                                                  "Couldn't find all device technologies" 
    print_test('fetch informations')
    assert d.get_device_technology_by_name('dt1').name == 'dt1', "DeviceTechnology dt1 was not found"
    print_test('del device technology')
    d.del_device_technology(dt2.id)
    assert has_item(d.list_device_technologies(), ['dt1', 'dt3']), "Couldn't find 'dt1' and 'dt3'"
    assert not has_item(d.list_device_technologies(), ['dt2']), "'dt2' was NOT deleted"

    print_title('test device technology config')
    remove_all_device_technology_config(d)
    print_test('add device technology config')
    dtc1_1 = d.add_device_technology_config(dt1.id, 'key1_1', 'val1_1')
    dtc1_2 = d.add_device_technology_config(dt1.id, 'key1_2', 'val1_2')
    dtc3_1 = d.add_device_technology_config(dt3.id, 'key3_1', 'val3_1')
    dtc3_2 = d.add_device_technology_config(dt3.id, 'key3_2', 'val3_2')
    dtc3_3 = d.add_device_technology_config(dt3.id, 'key3_3', 'val3_3')
    try:
        duplicate_key = False
        dtc = d.add_device_technology_config(dt3.id, 'key3_3', 'val3_3')
        duplicate_key = True
    except DbHelperException:
        pass
    assert not duplicate_key, "It shouldn't have been possible to add 'key3_3' for device technology %s : it already exists" % dt3.id

    assert len(d.list_device_technology_config(dt1.id)) == 2, \
            "%s devices technologies config found, instead of 2 " \
            % len(d.list_device_technology_config(dt1.id))
    assert len(d.list_device_technology_config(dt3.id)) == 3, \
            "%s devices technologies config found, instead of 3 " \
            % len(d.list_device_technology_config(dt3.id))
    print_test("get_device_technology_config")
    dtc = d.get_device_technology_config(dt3.id, 'key3_2')
    assert dtc.value == 'val3_2', "Wrong value for %s. Should be val3_2" % dtc.value

    print_test("del_device_technology_config")
    d.del_device_technology_config(dtc.id)
    assert d.get_device_technology_config(dt3.id, 'key3_2') == None, "key3_2 was NOT deleted"

    print_title('test device')
    remove_all_areas(d)
    remove_all_device_categories(d)
    remove_all_device_technologies(d)
    assert len(d.list_devices()) == 0, "Device list is NOT empty"
    print_test("add_device")
    area1 = d.add_area('area1','description 1')
    room1 = d.add_room('room1', 'description 1', area1.id)
    room2 = d.add_room('room2', 'description 2', area1.id)
    dt1 = d.add_device_technology('dt1', 'desc dt1', 'cpl')
    dc1 = d.add_device_category('dc1')
    device1 = d.add_device(d_address = 'A1', d_technology_id = dt1.id, d_type = 'lamp', 
                          d_category_id = dc1.id, d_room_id = room1.id, d_description = 'desc1', 
                          d_is_resetable = True, d_initial_value = 30, 
                          d_is_value_changeable_by_user = False, d_unit_of_stored_values = 'Percent')
    assert len(d.list_devices()) == 1, "Device was NOT added"
    print_test("update_device")
    device_id = device1.id
    device1 = d.update_device(d_id = device1.id, d_description = 'desc2')
    d._session.expunge(device1) # Remove object from session
    device1 = d.get_device(device_id)
    assert device1.description == 'desc2',\
          "Device desc. was NOT changed : should be 'desc2' but is '%s'" % device1.description
    device2 = d.add_device(d_address='A2', d_technology_id=dt1.id, d_type = 'appliance',
                          d_category_id=dc1.id, d_room_id=room1.id)
    device3 = d.add_device(d_address='A3', d_technology_id=dt1.id, d_type = 'appliance',
                          d_category_id=dc1.id, d_room_id=room2.id)
    assert len(d.list_devices()) == 3, "Device list should have 3 items, but it has %s" % d.list_devices()
    assert len(d.get_all_devices_of_room(room1.id)) == 2, \
              "Room id %s should have 2 devices but has %s" % (room1.id, len(d.get_all_devices_of_room(room1.id)))
    assert len(d.get_all_devices_of_room(room2.id)) == 1, \
              "Room id %s should have 1 device but has %s" % (room2.id, len(d.get_all_devices_of_room(room2.id)))
    print_test("find_devices")
    nb_of_dev = len(d.find_devices(category_id = dc1.id, room_id = room1.id))
    assert nb_of_dev == 2, "Should have found 2 devices, but found %s" % nb_of_dev
    nb_of_dev = len(d.find_devices(address = 'A2'))
    assert nb_of_dev == 1, "Should have found 1 device, but found %s" % nb_of_dev
    nb_of_dev = len(d.find_devices(address = 'A1544'))
    assert nb_of_dev == 0, "Should have found 0 device, but found %s" % nb_of_dev
    print_test("del_device")
    d.del_device(device2.id)
    assert len(d.list_devices()) == 2, "Found %s device(s), should be %s" % (d.list_devices(), 1)
    assert d.list_devices()[0].address == 'A1', \
          "Device should have 'A1' address but has : %s instead" % d.list_devices()[0].address

    print_title("device stats")
    remove_all_device_stats(d)
    dt1 = d.add_device_technology("x10", "this is x10", "cpl")
    dc1 = d.add_device_category("lighting")
    area1 = d.add_area('area1','description 1')
    room1 = d.add_room('room1', 'description 1', area1.id)
    device1 = d.add_device(d_address = "A1", d_technology_id = dt1.id, d_type = "lamp", 
                          d_category_id = dc1.id, d_room_id = room1.id)
    device2 = d.add_device(d_address = "A2", d_technology_id = dt1.id, d_type = "lamp", 
                          d_category_id = dc1.id, d_room_id = room1.id)
    device3 = d.add_device(d_address = "A3", d_technology_id = dt1.id, d_type = "lamp", 
                          d_category_id = dc1.id, d_room_id = room1.id)
    print_test("add_device_stat")
    now = datetime.datetime.now()
    d_stat1_1 = d.add_device_stat(device1.id, now, '10')
    d_stat1_2 = d.add_device_stat(device1.id, now + datetime.timedelta(seconds=1), '11')
    d_stat2_1 = d.add_device_stat(device2.id, now, '40')
    d_stat3_1 = d.add_device_stat(device3.id, now, '100')
    l_stats = d.list_device_stats(device1.id)
    assert len(l_stats) == 2, \
          "device stats for device id %s should have 2 items. It has %s" % (device1.id, len(l_stats))
    l_stats = d.list_device_stats(device2.id)
    assert len(l_stats) == 1, \
          "device stats for device id %s should have 1 item. It has %s" % (device2.id, len(l_stats))
    print_test("get_last_stat_of_devices")
    l_stats = d.get_last_stat_of_devices([device1.id, device2.id])
    print l_stats
    assert len(l_stats) == 2, "last device stats should have 2 items. It has %s" % len(l_stats)
    device_id_list = []
    for stat in l_stats:
        device_id_list.append(stat.device_id)
        if stat.device_id == device1.id:
            # Make sure we get the LAST stat for device1
            assert stat.value == '11', "Wrong stat was retrieved. Value should be 11, but is %s" % stat.value
    assert device1.id in device_id_list, "device1 is not in the list but should have been"
    assert device2.id in device_id_list, "device2 is not in the list but should have been"
    print_test("del_all_device_stats")
    d.del_all_device_stats(device1.id)
    l_stats = d.list_device_stats(device1.id)
    assert len(l_stats) == 0, "List of stats should be empty for device1, but it has %s items" % len(l_stats)
    l_stats = d.list_device_stats(device2.id)
    assert len(l_stats) == 1, "List of stats should have 1 item for device2, but it has %s items" % len(l_stats)

    print_title("test triggers")
    for trigger in d.list_triggers():
        d.del_trigger(trigger.id)
    assert len(d.list_triggers()) == 0, "Trigger list should be empty, but it has % item(s)" % len(d.list_triggers())
    trigger1 = d.add_trigger(t_description = 'desc1', 
                            t_rule = 'AND(x,OR(y,z))', t_result= ['x10_on("a3")','1wire()'])
    trigger2 = d.add_trigger(t_description = 'desc2', 
                            t_rule = 'OR(x,AND(y,z))', t_result= ['x10_on("a2")','1wire()'])
    print trigger1.id
    assert len(d.list_triggers()) == 2, "Trigger list should have 2 items but it has %s item(s)" % len(d.list_triggers())
    assert d.get_trigger(trigger1.id).description == 'desc1', "Trigger1 should have 'desc1', but it has not"

    print_title("test user and system accounts")
    for user in d.list_user_accounts():
        d.del_user_account(user.id)
    assert len(d.list_user_accounts()) == 0, \
          "User account list should be empty but it is NOT %s" % d.list_user_accounts()
    for sys in d.list_system_accounts():
        d.del_system_account(sys.id)
    assert len(d.list_system_accounts()) == 0, \
          "System account list should be empty but it is NOT %s" % d.list_system_accounts()
    print_test("add_user_account")
    sys1 = d.add_system_account(a_login = 'mschneider', a_password = 'IwontGiveIt', a_is_admin = True)
    sys2 = d.add_system_account(a_login = 'lonely', a_password = 'boy', a_is_admin = True)
    sys3 = d.add_system_account(a_login = 'domo', a_password = 'gik', a_is_admin = True)
    user1 = d.add_user_account(u_first_name='Marc', u_last_name='SCHNEIDER', u_birthdate=datetime.date(1973, 4, 24), 
                              u_system_account_id = sys1.id)
    user2 = d.add_user_account(u_first_name='Monthy', u_last_name='PYTHON', u_birthdate=datetime.date(1981, 4, 24))
    assert len(d.list_user_accounts()) == 2, \
              "List of user accounts should have 2 items, but it has NOT %s" % d.list_user_accounts()
    assert len(d.list_system_accounts()) == 3, \
              "List of system accounts should have 3 items, but it has NOT %s" % d.list_system_accounts()
    print_test("get_system_account")
    assert d.get_system_account(sys1.id).login == 'mschneider', \
          "Login for system id %s should be 'mschneider' but is %s" % (sys1.id, sys1.login)
    print_test("get_user_account")
    assert d.get_user_account(user1.id).first_name == 'Marc', \
          "First name for user id %s should be 'Marc' but is %s" % (user1.id, user1.first_name)
    assert d.get_user_account(user2.id).last_name == 'PYTHON', \
          "Last name for user id %s should be 'PYTHON' but is %s" % (user2.id, user2.last_name)
    print_test("get_user_system_account")
    login = d.get_user_system_account(user1.id).login
    assert login == 'mschneider', \
          "System account login for user id %s should be 'mschneider' but is %s" % (user1.id, login)
    print_test("del_system_account")
    sys_temp = d.add_system_account(a_login = 'fantom', a_password = 'as', a_is_admin = False)
    d.del_system_account(sys_temp.id)
    l_sys = d.list_system_accounts()
    assert len(l_sys) > 0, "The list is empty but it shouldn't"
    for sys in l_sys:
        assert sys.login != 'fantom', "System account with 'fantom' login was NOT deleted"
    print_test("del_user_account")
    d.del_user_account(user1.id)
    found_user2 = False
    for user in d.list_user_accounts():
        assert user.id != user1.id, "User %s was NOT deleted" % user1.id
        found_user2 = (user.id == user2.id)
    assert found_user2, "User %s was deleted, but shouldn't have been" % user2.id
    # Make sure associated system account has been deleted
    l_sys = d.list_system_accounts()
    assert len(l_sys) > 0, "The list is empty but it shouldn't"
    for sys in l_sys:
        assert sys.login != 'mschneider', "System account with 'mschneider' login was NOT deleted"

    print_test('*********** All tests successfully passed! ***********')

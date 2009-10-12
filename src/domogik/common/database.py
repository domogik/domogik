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

API to use Domogik database.
Please don't forget to add unit test in 'database_test.py' if you add a new method.
Please always run 'python database_test.py' if you change something in this file.

Implements
==========

- class DbHelperException(Exception) : exceptions linked to the DbHelper class
- class DbHelper : API to use Domogik database

@author: Maxence DUNNEWIND / Marc SCHNEIDER
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

####
# Existing tables :
# areas
# rooms
# device_category
# device_technology
# device_technology_config
# device
# device_config
# device_stats
# trigger
# system_account
# user_account
####


import hashlib
from types import DictType, ListType, NoneType

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from domogik.common.configloader import Loader
from domogik.common.sql_schema import Area, Device, DeviceCategory, DeviceConfig, \
                                      DeviceStats, DeviceTechnology, DeviceTechnologyConfig, \
                                      Room, UserAccount, SystemAccount, SystemConfig, \
                                      SystemStats, Trigger
from domogik.common.sql_schema import DEVICE_TECHNOLOGY_LIST, DEVICE_TECHNOLOGY_TYPE_LIST, \
                                      DEVICE_TYPE_LIST, SYSTEMSTATS_TYPE_LIST, UNIT_OF_STORED_VALUE_LIST


class DbHelperException(Exception):
    """
    This class provides exceptions related to the DbHelper class
    """

    def __init__(self, value):
        """
        Class constructor
        @param value : value of the exception
        """
        self.value = value

    def __str__(self):
        """
        Return the object representation
        @return value of the exception
        """
        return repr(self.value)


class DbHelper():
    """
    This class provides methods to fetch and put informations on the Domogik database
    The user should only use methods from this class and don't access the database directly
    """
    _dbprefix = None
    _engine = None
    _session = None

    def __init__(self, echo_output=False, use_test_db=False):
        """
        Class constructor
        @param echo_output : if True displays sqlAlchemy queries (optional, default False)
        @param use_test_db : if True use a test database (optional, default False)
        """
        cfg = Loader('database')
        config = cfg.load()
        db = dict(config[1])
        url = "%s://" % db['db_type']
        if db['db_type'] == 'sqlite':
            url = "%s/%s" % (url, db['db_path'])
        else:
            if db['db_port'] != '':
                url = "%s%s:%s@%s:%s/%s" % (url, db['db_user'], db['db_password'], 
                                            db['db_host'], db['db_port'], db['db_name'])
            else:
                url = "%s%s:%s@%s/%s" % (url, db['db_user'], db['db_password'], 
                                        db['db_host'], db['db_name'])

        if use_test_db:
            url = '%s_test' % url

        # Connecting to the database
        self._dbprefix = db['db_prefix']
        self._engine = sqlalchemy.create_engine(url, echo=echo_output)
        Session = sessionmaker(bind=self._engine)
        self._session = Session()

####
# Areas
####
    def list_areas(self):
        """
        Return a list of areas
        @return list of Area objects
        """
        return self._session.query(Area).all()

    def get_area_by_name(self, area_name):
        """
        Fetch area information
        @param area : The area name
        @return an area object
        """
        area = self._session.query(Area).filter_by(name=area_name).first()
        if area:
            return area
        else:
            return None

    def add_area(self, a_name, a_description=None):
        """
        Add an area
        @param a_name : area name
        @param a_description : area detailed description (optional)
        @return an area object
        """
        area = Area(name=a_name, description=a_description)
        self._session.add(area)
        self._session.commit()
        return area

    def del_area(self, area_del_id):
        """
        Delete an area record.
        Warning this also remove all the rooms in this area
        and all the devices (+ their stats) in each deleted rooms !
        @param area_id : id of the area to delete
        """
        area = self._session.query(Area).filter_by(id=area_del_id).first()
        if area:
            for room in self._session.query(Room).filter_by(area_id=area_del_id).all():
                self.del_room(room.id)
            self._session.delete(area)
            self._session.commit()

####
# Rooms
####
    def list_rooms(self):
        """
        Return a list of rooms
        @return list of Room objects
        """
        return self._session.query(Room).all()

    def get_room_by_name(self, r_name):
        """
        Return information about a room
        @param r_name : The room name
        @return a room object 
        """
        room = self._session.query(Room).filter_by(name=r_name).first()
        if room:
            return room
        else:
            return None

    def add_room(self, r_name, r_area_id, r_description=None):
        """
        Add a room
        @param r_name : room name
        @param area_id : id of the area where the room is
        @param r_description : room detailed description (optional)
        @return : a room object
        """
        try: 
            area = self._session.query(Area).filter_by(id=r_area_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add room with area id %s. It does not exist" % r_area_id)

        room = Room(name=r_name, description=r_description, area_id=r_area_id)
        self._session.add(room)
        self._session.commit()
        return room

    def del_room(self, r_id):
        """
        Delete a room record
        Warning this also remove all the devices in each deleted rooms!
        @param r_id : id of the room to delete
        """
        room = self._session.query(Room).filter_by(id=r_id).first()
        if room:
            for device in self._session.query(Device).filter_by(room_id=r_id).all():
                self.del_device(device.id)
            self._session.delete(room)
            self._session.commit()

    def get_all_rooms_of_area(self, a_area_id):
        """
        Returns all the rooms of an area
        @param a_area_id : the area id
        @return a list of Room objects
        """
        return self._session.query(Room).filter_by(area_id=a_area_id).all()

####
# Device category
####
    def list_device_categories(self):
        """
        Return a list of device categories
        @return a list of DeviceCategory objects
        """
        return self._session.query(DeviceCategory).all()

    def get_device_category_by_name(self, dc_name,):
        """
        Return information about a device category
        @param dc_name : The device category name
        @return a DeviceCategory object 
        """
        return self._session.query(DeviceCategory).filter_by(name=dc_name).first()

    def add_device_category(self, dc_name, dc_description=None):
        """
        Add a device_category (temperature, heating, lighting, music, ...)
        @param dc_name : device category name
        @param dc_description : device category description (optional)
        @return a DeviceCategory (the newly created one)
        """
        dc = DeviceCategory(name=dc_name, description=dc_description)
        self._session.add(dc)
        self._session.commit()
        return dc

    def del_device_category(self, dc_id):
        """
        Delete a device category record
        Warning, it will also remove all the devices using this category
        @param dc_id : id of the device category to delete
        """
        dc = self._session.query(DeviceCategory).filter_by(id=dc_id).first()
        if dc:
            for device in self._session.query(Device).filter_by(category_id=dc.id).all():
                self.del_device(device.id)
            self._session.delete(dc)
            self._session.commit()

####
# Device technology
####
    def list_device_technologies(self):
        """
        Return a list of device technologies
        @return a list of DeviceTechnology objects
        """
        return self._session.query(DeviceTechnology).all()

    def get_device_technology_by_name(self, dt_name):
        """
        Return information about a device technology
        @param dt_name : the device technology name
        @return a DeviceTechnology object
        """
        return self._session.query(DeviceTechnology).filter_by(name=dt_name).first()

    def add_device_technology(self, dt_name, dt_description, dt_type):
        """
        Add a device_technology
        @param dt_name : device technology name, one of 'x10', '1wire', 'PLCBus', 'RFXCom', 'IR'
        @param dt_description : extended description of the technology
        @param type : type of the technology, one of 'cpl','wired','wifi','wireless','ir'
        """
        if dt_name not in DEVICE_TECHNOLOGY_LIST:
            raise ValueError, "dt_name must be one of %s" % DEVICE_TECHNOLOGY_LIST
        if dt_type not in DEVICE_TECHNOLOGY_TYPE_LIST:
            raise ValueError, "dt_type must be one of %s" % DEVICE_TECHNOLOGY_TYPE_LIST
        dt = DeviceTechnology(name=dt_name, description=dt_description, type=dt_type)
        self._session.add(dt)
        self._session.commit()
        return dt

    def del_device_technology(self, dt_id):
        """
        Delete a device technology record
        Warning, it will also remove all the devices using this technology
        @param dt_id : id of the device technology to delete
        """
        dt = self._session.query(DeviceTechnology).filter_by(id=dt_id).first()
        if dt:
            for device in self._session.query(Device).filter_by(technology_id=dt.id).all():
                self.del_device(device.id)
            self._session.delete(dt)
            self._session.commit()

####
# Device technology config
####
    def list_device_technology_config(self, dt_id):
        """
        Return all keys and values of a device technology
        @param dt_id : id of the device technology
        @return a list of DeviceTechnologyConfig objects
        """
        return self._session.query(DeviceTechnologyConfig).filter_by(technology_id=dt_id).all()

    def get_device_technology_config(self, dt_id, dtc_key):
        """
        Return information about a device technology config item
        @param dt_id : id of the device technology
        @param dtc_key : key of the device technology config
        @return a DeviceTechnologyConfig object
        """
        return self._session.query(DeviceTechnologyConfig).filter_by(technology_id=dt_id)\
                                                          .filter_by(key=dtc_key)\
                                                          .first()

    def add_device_technology_config(self, dt_id, dtc_key, dtc_value):
        """
        Add a device's technology config item
        @param dt_id : the device technology id
        @param dtc_key : The device technology config key
        @param dtc_value : The device technology config value
        @return the new DeviceTechnologyConfig item
        """
        try: 
            dt = self._session.query(DeviceTechnology).filter_by(id=dt_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device technology config with device technology id %s. \
                            It does not exist" % dt_id)
        if self.get_device_technology_config(dt_id, dtc_key):
            raise DbHelperException("This key '%s' already exists for device technology %s" % (dtc_key, dt_id))
        dtc = DeviceTechnologyConfig(technology_id=dt_id, key=dtc_key, value=dtc_value)
        self._session.add(dtc)
        self._session.commit()
        return dtc

    def del_device_technology_config(self, dtc_id):
        """
        Delete a device technology config record
        @param dtc_id : config item id
        """
        dt = self._session.query(DeviceTechnologyConfig).filter_by(id=dtc_id).first()
        self._session.delete(dt)
        self._session.commit()

###
# Devices
###
    def list_devices(self):
        """
        Returns a list of devices
        @return a list of Device objects
        """
        return self._session.query(Device).all()

    def search_devices(self, **filters):
        """
        Look for device(s) with filter on their attributes
        @param filters :  filter fields can be one of id, address, type, room, initial_value, 
                          is_value_changeable_by_user, unit_of_stored_values.
        @return a list of Device objects
        """
        assert type(filters) is DictType

        device_list = self._session.query(Device)
        for filter in filters:
            filter_arg = "%s = '%s'" % (filter, filters[filter])
            device_list = device_list.filter(filter_arg)

        return device_list.all()

    def find_devices(self, d_room_id_list, d_category_id_list):
        """
        Look for devices that have at least 1 item in room_id_list AND 1 item in category_id_list
        @param room_id_list : list of room ids
        @param category_id_list : list of category ids
        @return a list of DeviceObject items
        """
        assert type(d_room_id_list) is ListType or type(d_room_id_list) is NoneType
        assert type(d_category_id_list) is ListType or type(d_category_id_list) is NoneType

        device_list = self._session.query(Device)
        if d_room_id_list is not None and len(d_room_id_list) != 0:
            device_list = device_list.filter(Device.room_id.in_(d_room_id_list))
        if d_category_id_list is not None and len(d_category_id_list) != 0:
            device_list = device_list.filter(Device.category_id.in_(d_category_id_list))
        return device_list.all()

    def get_device(self, d_id):
        """
        Return a device by its it
        @param d_id : The device id
        @return a Device object
        """
        return self._session.query(Device).filter_by(id=d_id).first()

    def get_all_devices_of_room(self, d_room_id):
        """
        Return all the devices of a room
        @param d_room_id: room id
        @return a list of Device objects
        """
        return self._session.query(Device).filter_by(room_id=d_room_id).all()

    def get_all_devices_of_area(self, d_area_id):
        """
        Return all the devices of an area
        @param d_area_id : the area id
        @return a list of Device objects
        """
        device_list = []
        for room in self.get_all_rooms_of_area(d_area_id):
            for device in self.get_all_devices_of_room(room.id):
              device_list.append(device)
        return device_list

    def get_all_devices_of_category(self, dc_id):
        """
        Return all the devices of a category
        @param dc_id: category id 
        @return a list of Device objects
        """
        return self._session.query(Device).filter_by(category_id=dc_id).all()

    def get_all_devices_of_technology(self, dt_id):
        """
        Returns all the devices of a technology
        @param dt_id : technology id
        @return a list of Device objects
        """
        return self._session.query(Device).filter_by(technology_id=dt_id).all()

    def add_device(self, d_name, d_address, d_technology_id, d_type, d_category_id, d_room_id, 
        d_description=None, d_reference=None, d_is_resetable=False, d_initial_value=None,
        d_is_value_changeable_by_user=False, d_unit_of_stored_values=None):
        """
        Add a device item
        @param d_name : name of the device
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_technology_id : technology id
        @param d_type : One of 'appliance','light','music','sensor'
        @param d_category_id : category id
        @param d_room_id : room id
        @param d_description : Extended item description (100 char max)
        @param d_reference : device reference (ex. AM12 for x10)
        @param d_is_resetable : Can the item be reseted to some initial state (optional, default=False)
        @param d_initial_value : What's the initial value of the item, should be
            the state when the item is created (except for sensors, music) (optional, default=None)
        @param d_is_value_changeable_by_user : Can a user change item state (ex : false for sensor)
            (optional, default=False)
        @param d_unit_of_stored_values : What is the unit of item values,
                must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean' (optional, default=None)
        @return the new Device object
        """
        try:
            room = self._session.query(Room).filter_by(id=d_room_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device with room id %s. It does not exist" % d_room_id)
        try:
            dc = self._session.query(DeviceCategory).filter_by(id=d_category_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device with category id %s. It does not exist" % d_category_id)
        try:
            dt = self._session.query(DeviceTechnology).filter_by(id=d_technology_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device with technology id %s. It does not exist" % d_technology_id)

        if d_unit_of_stored_values not in UNIT_OF_STORED_VALUE_LIST:
            raise ValueError, "d_unit_of_stored_values must be one of %s" % UNIT_OF_STORED_VALUE_LIST
        if d_type not in DEVICE_TYPE_LIST:
            raise ValueError, "d_type must be one of %s" % DEVICE_TYPE_LIST

        device = Device(name=d_name, address=d_address, description=d_description, 
                        reference=d_reference, technology_id=d_technology_id, type=d_type, 
                        category_id=d_category_id, room_id=d_room_id, 
                        is_resetable=d_is_resetable, initial_value=d_initial_value, 
                        is_value_changeable_by_user=d_is_value_changeable_by_user, 
                        unit_of_stored_values=d_unit_of_stored_values)
        self._session.add(device)
        self._session.commit()
        return device

    def update_device(self, d_id, d_name=None, d_address=None, d_technology_id=None, d_type=None, 
        d_category_id=None, d_room_id=None, d_description=None, d_reference=None, d_is_resetable=None, 
        d_initial_value=None, d_is_value_changeable_by_user=None, d_unit_of_stored_values =None):
        """
        Update a device item
        If a param is None, then the old value will be kept
        @param d_id : Device id
        @param d_name : device name (optional)
        @param d_address : Item address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire) (optional)
        @param d_description : Extended item description (optional)
        @param d_technology : Item technology id (optional)
        @param d_type : One of 'appliance','light','music','sensor' (optional)
        @param d_category : Item category id (optional) 
        @param d_room : Item room id (optional)
        @param d_is_resetable : Can the item be reseted to some initial state (optional)
        @param d_initial_value : What's the initial value of the item, should be
            the state when the item is created (except for sensors, music) (optional)
        @param d_is_value_changeable_by_user : Can a user change item state (ex : false for sensor) (optional)
        @param d_unit_of_stored_values : What is the unit of item values,
            must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean' (optional)
        @return the updated Device object
        """
        if d_unit_of_stored_values not in [UNIT_OF_STORED_VALUE_LIST, None]: 
            raise ValueError, "d_unit_of_stored_values must be one of %s" % UNIT_OF_STORED_VALUE_LIST
        if d_type not in [DEVICE_TYPE_LIST, None]:
            raise ValueError, "d_type must be one of %s" % DEVICE_TYPE_LIST

        device = self._session.query(Device).filter_by(id=d_id).first()
        if device is None:
            raise DbHelperException("Device with id %s couldn't be found" % d_id)

        if d_name is not None:
            device.name = d_name
        if d_address is not None:
            device.address = d_address
        if d_technology_id is not None:
            try:
                dt = self._session.query(DeviceTechnology).filter_by(id=d_technology_id).one()
                device.technology = d_technology_id
            except NoResultFound, e:
                raise DbHelperException("Couldn't update device with technology id %s. It does not exist" % d_technology_id)
        if d_description is not None:
            device.description = d_description
        if d_reference is not None:
            device.reference = d_reference
        if d_type is not None:
            device.type = d_type
        if d_category_id is not None:
          try:
              dc = self._session.query(DeviceCategory).filter_by(id=d_category_id).one()
              device.category = d_category_id
          except NoResultFound, e:
              raise DbHelperException("Couldn't update device with category id %s. It does not exist" % d_category_id)
        if d_room_id is not None:
            try:
                room = self._session.query(Room).filter_by(id=d_room_id).one()
                device.room = d_room_id
            except NoResultFound, e:
                raise DbHelperException("Couldn't update device with room id %s. It does not exist" % d_room_id)
        if d_is_resetable is not None:
            device.is_resetable = d_is_resetable
        if d_initial_value is not None:
            device.initial_value = d_initial_value
        if d_is_value_changeable_by_user is not None:
            device.is_value_changeable_by_user = d_is_value_changeable_by_user
        if d_unit_of_stored_values is not None:
            device.unit_of_stored_values = d_unit_of_stored_values
        
        self._session.add(device)
        self._session.commit()
        return device

    def del_device(self, d_id):
        """
        Delete a device
        Warning : this deletes also the associated objects (DeviceConfig, DeviceStats)
        @param d_id : item id
        """
        device = self.get_device(d_id)
        if device is None:
            raise DbHelperException("Device with id %s couldn't be found" % d_id)

        for device_conf in self._session.query(DeviceConfig).filter_by(device_id=d_id).all():
            self._session.delete(device_conf)
        for device_stats in self._session.query(DeviceStats).filter_by(device_id=d_id).all():
            self._session.delete(device_stats)
        self._session.delete(device)
        self._session.commit()

####
# Device stats
####
    def list_device_stats(self, d_device_id):
        """
        Return a list of all stats for a device
        @param d_device_id : the device id
        @return a list of DeviceStats objects
        """
        return self._session.query(DeviceStats).filter_by(device_id=d_device_id).all()

    def get_last_stat_of_device(self, d_device_id):
        """
        Fetch the last record of stats for a device
        @param d_device_id : device id
        @return a DeviceStat object
        """
        return self._session.query(DeviceStats)\
                              .filter_by(device_id=d_device_id)\
                              .order_by(sqlalchemy.desc(DeviceStats.date)).first()

    def get_last_stat_of_devices(self, device_list):
        """
        Fetch the last record for all devices in d_list
        @param device_list : list of device ids
        @return a list of DeviceStats objects
        """
        assert type(device_list) is ListType

        result = []
        for d_id in device_list:
            last_record = self._session.query(DeviceStats)\
                              .filter_by(device_id=d_id)\
                              .order_by(sqlalchemy.desc(DeviceStats.date)).first()
            result.append(last_record)
        return result

    def device_has_stats(self, d_device_id):
        """
        Check if the device has stats that were recorded
        @param d_device_id : device id
        @return True or False
        """
        return self._session.query(DeviceStats).filter_by(device_id=d_device_id).count() > 0

    def add_device_stat(self, d_id, ds_date, ds_value):
        """
        Add a device stat record
        @param device_id : device id
        @param ds_date : when the stat was gathered (timestamp)
        @param ds_value : stat value
        @return the new DeviceStats object
        """
        device_stat = DeviceStats(device_id=d_id, date=ds_date, value=ds_value)
        self._session.add(device_stat)
        self._session.commit()
        return device_stat

    def del_device_stat(self, ds_id):
        """
        Delete a stat record
        @param ds_id : record id
        """
        device_stat = self._session.query(DeviceStats).filter_by(id=ds_id).first()
        if device_stat:
            self._session.delete(device_stat)
            self._session.commit()

    def del_all_device_stats(self, d_id):
        """
        Delete all stats for a device
        @param d_id : device id
        """
        #TODO : this could be optimized
        device_stats = self._session.query(DeviceStats).filter_by(device_id=d_id).all()
        for device_stat in device_stats:
            self._session.delete(device_stat)
        self._session.commit()
 
####
# Triggers
####
    def list_triggers(self):
        """
        Returns a list of all triggers
        @return a list of Trigger objects
        """
        return self._session.query(Trigger).all()

    def get_trigger(self, t_id):
        """
        Returns a trigger information from id
        @param t_id : trigger id
        @return a Trigger object
        """
        return self._session.query(Trigger).filter_by(id=t_id).first()

    def add_trigger(self, t_description, t_rule, t_result):
        """
        Add a trigger
        @param t_desc : trigger description
        @param t_rule : trigger rule
        @param t_res : trigger result
        @return the new Trigger object
        """
        trigger = Trigger(description=t_description, rule=t_rule, result=';'.join(t_result))
        self._session.add(trigger)
        self._session.commit()
        return trigger

    def del_trigger(self, t_id):
        """
        Delete a trigger
        @param t_id : trigger id
        """
        trigger = self._session.query(Trigger).filter_by(id=t_id).first()
        self._session.delete(trigger)
        self._session.commit()

####
# System accounts
####
    def list_system_accounts(self):
        """
        Returns a list of all accounts
        @return a list of SystemAccount objects
        """
        return self._session.query(SystemAccount).all()

    def get_system_account(self, a_id):
        """
        Return system account information from id
        @param a_id : account id
        @return a SystemAccount object
        """
        return self._session.query(SystemAccount).filter_by(id=a_id).first()

    def get_system_account_by_login(self, a_login):
        """
        Return system account information from login
        @param a_login : login
        @return a SystemAccount object
        """
        return self._session.query(SystemAccount).filter_by(login=a_login).first()

    def get_system_account_by_user(self, u_id):
        """
        Return a system account associated to a user, if existing
        @param u_id : The user account id
        @return a SystemAccount object
        """
        user_account = self._session.query(UserAccount).filter_by(id=u_id).first()
        if user_account is not None:
            try:
                return self._session.query(SystemAccount).filter_by(id=user_account.system_account_id).one()
            except MultipleResultsFound, e:
                raise DbHelperException("Database may be incoherent, user with id %s has more than one account" % u_id)
        else:
            return None

    def is_system_account(self, a_login, a_password):
        """
        Check if a system account with a_login, a_password exists
        @param a_login : Account login
        @param a_password : Account password (clear)
        """
        system_account = self.get_system_account_by_login(a_login)
        if system_account is not None:
            password = hashlib.sha256()
            password.update(a_password)
            if system_account.password == password.hexdigest():
                return True
        return False

    def add_system_account(self, a_login, a_password, a_is_admin=False):
        """
        Add a system_account
        @param a_login : Account login
        @param a_password : Account clear password (will be hashed in sha256)
        @param a_is_admin : True if it is an admin account, False otherwise (optional, default=False)
        @return the new SystemAccount object or raise a DbHelperException if it already exists
        """
        system_account = self.get_system_account_by_login(a_login)
        if system_account is not None:
            raise DbHelperException("Error %s login already exists" % a_login)
        password = hashlib.sha256()
        password.update(a_password)
        system_account = SystemAccount(login=a_login, password=password.hexdigest(), is_admin=a_is_admin)
        self._session.add(system_account)
        self._session.commit()
        return system_account

    def add_default_system_account(self):
        """
        Add a default system account (login = admin, password = domogik, is_admin = True)
        @return a SystemAccount object
        """
        return self.add_system_account(a_login='admin', a_password='12345', a_is_admin=True)

    def del_system_account(self, a_id):
        """
        Delete a system account 
        @param a_id : account id
        """
        system_account = self._session.query(SystemAccount).filter_by(id=a_id).first()
        self._session.delete(system_account)
        self._session.commit()
    
####
# User accounts
####
    def list_user_accounts(self):
        """
        Returns a list of all user accounts
        @return a list of UserAccount objects
        """
        return self._session.query(UserAccount).all()

    def get_user_account(self, u_id):
        """
        Returns account information from id
        @param u_id : user account id
        @return a UserAccount object
        """
        return self._session.query(UserAccount).filter_by(id=u_id).first()

    def get_user_account_by_system_account(self, s_id):
        """
        Return a user account associated to a system account, if existing
        @param s_id : the system account id
        @return a UserAccount object or None
        """
        try:
            return self._session.query(UserAccount).filter_by(system_account_id=s_id).one()
        except NoResultFound:
            return None
        except MultipleResultsFound, e:
            raise DbHelperException("Database may be incoherent, user with id %s has more than one account" % u_id)

    def add_user_account(self, u_first_name, u_last_name, u_birthdate, u_system_account_id=None):
        """
        Add a user account
        @param u_first_name : User's first name
        @param u_last_name : User's last name
        @param u_birthdate : User's birthdate
        @param u_system_account : User's account on the system (optional)
        @return the new UserAccount object
        """
        user_account = UserAccount(first_name=u_first_name, last_name=u_last_name, 
                                  birthdate=u_birthdate, system_account_id=u_system_account_id)
        self._session.add(user_account)
        self._session.commit()
        return user_account

    def del_user_account(self, u_id):
        """
        Delete a user account and the associated system account if it exists
        @param u_id : user's account id
        """
        user_account = self._session.query(UserAccount).filter_by(id=u_id).first()
        if user_account is not None:
            if user_account.system_account_id is not None:
                self.del_system_account(user_account.system_account_id)
            self._session.delete(user_account)
            self._session.commit()

####
# System stats
####
    def list_system_stats(self):
        """
        Return a list of all system stats
        @return a list of SystemStats objects
        """
        return self._session.query(SystemStats).all()

    def get_system_stat(self, s_id):
        """
        Return a system stat
        @param s_name : the name of the stat to be retrieved
        @return a SystemStats object
        """
        return self._session.query(SystemStats).filter_by(id=s_id).first()


    def get_system_stats_by_type(self, s_type):
        """
        Return a list of all system stats
        @param s_type : type of the stats to be retrieved
        @return a list of SystemStats objects
        """
        return self._session.query(SystemStats).filter_by(type=s_type).all()

    def add_system_stat(self, s_name, s_hostname, s_date, s_type, s_value):
        """
        Add a system stat record
        @param s_name : name of the  module
        @param s_hostname : name of the  host
        @param s_date : when the stat was gathered (timestamp)
        @param s_type : stat type (must be one of sql_schema.SYSTEMSTATS_TYPE_LIST list)
        @param s_value : stat value
        @return the new SystemStats object
        """
        if s_type not in SYSTEMSTATS_TYPE_LIST:
            raise ValueError, "s_type must be one of %s" % SYSTEMSTATS_TYPE_LIST
        system_stat = SystemStats(module_name=s_name, host_name=s_hostname, date=s_date, type=s_type, value=s_value)
        self._session.add(system_stat)
        self._session.commit()
        return system_stat

    def del_system_stat(self, s_name):
        """
        Delete a system stat record
        @param s_name : name of the stat that has to be deleted
        """
        system_stat = self._session.query(SystemStats).filter_by(name=s_name).first()
        if system_stat:
            self._session.delete(system_stat)
            self._session.commit()

    def del_all_system_stats(self):
        """
        Delete all stats of the system
        """
        system_stats = self._session.query(SystemStats).all()
        for system_stat in system_stats:
            self._session.delete(system_stat)
        self._session.commit()

###
# SystemConfig
###
    def get_system_config(self):
        """
        Get current system configuration
        @return a SystemConfig object
        """
        try:
            return self._session.query(SystemConfig).one()
        except MultipleResultsFound, e:
            raise DbHelperException("Error : SystemConfig has more than one line")
        except NoResultFound, e:
            pass

    def update_system_config(self, s_simulation_mode=None, s_debug_mode=None):
        """
        Update (or create) system configuration
        @param s_simulation_mode : True if the system is running in simulation mode (optional)
        @param s_debug_mode : True if the system is running in debug mode (optional)
        @return a SystemConfig object
        """
        system_config = self.get_system_config()
        if system_config is not None:
            if s_simulation_mode is not None:
                system_config.simulation_mode = s_simulation_mode
            if s_debug_mode is not None:
                system_config.debug_mode = s_debug_mode
        else:
            system_config = SystemConfig(simulation_mode=s_simulation_mode, 
                                        debug_mode=s_debug_mode)
        self._session.add(system_config)
        self._session.commit()
        return system_config

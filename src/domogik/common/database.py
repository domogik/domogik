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

import sqlalchemy
from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from domogik.common.configloader import Loader
from domogik.common.sql_schema import Area, Device, DeviceCategory, DeviceConfig, \
                                      DeviceStats, DeviceTechnology, DeviceTechnologyConfig, \
                                      Room, UserAccount, SystemAccount, SystemStats, Trigger
from domogik.common.sql_schema import DEVICE_TECHNOLOGY_TYPE_LIST, DEVICE_TYPE_LIST, SYSTEMSTATS_TYPE_LIST, \
                                      UNIT_OF_STORED_VALUE_LIST


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

    def __init__(self, echo_output = False):
        """
        Class constructor
        @param echo_output : if set to True displays sqlAlchemy queries (default set to False)
        """
        cfg = Loader('database')
        config = cfg.load()
        db = dict(config[1])
        url = "%s:///" % db['db_type']
        if db['db_type'] == 'sqlite':
            url = "%s%s" % (url,db['db_path'])
        else:
            if db['db_port'] != '':
                url = "%s%s:%s@%s:%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_port'], db['db_name'])
            else:
                url = "%s%s:%s@%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_name'])

        # Connecting to the database
        self._dbprefix = db['db_prefix']
        self._engine = sqlalchemy.create_engine(url, echo = echo_output)
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
        area = self._session.query(Area).filter_by(name = area_name).first()
        if area:
            return area
        else:
            return None

    def add_area(self, a_name, a_description):
        """
        Add an area
        @param a_name : area name
        @param a_description : area detailled description
        @return an area object
        """
        area = Area(name = a_name, description = a_description)
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
            for room in self._session.query(Room).filter_by(area_id = area_del_id).all():
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
        room = self._session.query(Room).filter_by(name = r_name).first()
        if room:
            return room
        else:
            return None

    def add_room(self, r_name, r_description, r_area_id):
        """
        Add a room
        @param r_name : room name
        @param area_id : id of the area where the room is
        @param r_description : room detailled description
        @return : a room object
        """
        try: 
            area = self._session.query(Area).filter_by(id = r_area_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add room with area id %s. It does not exist" % r_area_id)

        room = Room(name = r_name, description = r_description, area_id = r_area_id)
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
            for device in self._session.query(Device).filter_by(room_id = r_id).all():
                self.del_device(device.id)
            self._session.delete(room)
            self._session.commit()

    def get_all_rooms_of_area(self, a_area_id):
        """
        Returns all the rooms of an area
        @param a_area_id : the area id
        @return a list of Room objects
        """
        return self._session.query(Room).filter_by(area_id = a_area_id).all()

####
# Device category
####
    def list_device_categories(self):
        """
        Return a list of device categories
        @return a list of DeviceCategory objects
        """
        return self._session.query(DeviceCategory).all()

    def get_device_category_by_name(self, dc_name):
        """
        Return information about a device category
        @param dc_name : The device category name
        @return a DeviceCategory object 
        """
        return self._session.query(DeviceCategory).filter_by(name = dc_name).first()

    def add_device_category(self, dc_name):
        """
        Add a device_category (temperature, heating, lighting, music, ...)
        @param dc_name : device category name
        @return a DeviceCategory (the newly created one)
        """
        dc = DeviceCategory(name = dc_name)
        self._session.add(dc)
        self._session.commit()
        return dc

    def del_device_category(self, dc_id):
        """
        Delete a device category record
        Warning, it will also remove all the devices using this category
        @param dc_id : id of the device category to delete
        """
        dc = self._session.query(DeviceCategory).filter_by(id = dc_id).first()
        if dc:
            for device in self._session.query(Device).filter_by(category_id = dc.id).all():
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
        return self._session.query(DeviceTechnology).filter_by(name = dt_name).first()

    def add_device_technology(self, dt_name, dt_description, dt_type):
        """
        Add a device_technology
        @param dt_name : device technology name
        @param dt_description : extended description of the technology
        @param type : type of the technology, one of 'cpl','wired','wifi','wireless','ir'
        """
        if dt_type not in DEVICE_TECHNOLOGY_TYPE_LIST:
            raise ValueError, "dt_type must be one of %s" % DEVICE_TECHNOLOGY_TYPE_LIST
        dt = DeviceTechnology(name = dt_name, description = dt_description, type= dt_type)
        self._session.add(dt)
        self._session.commit()
        return dt

    def del_device_technology(self, dt_id):
        """
        Delete a device technology record
        Warning, it will also remove all the devices using this technology
        @param dt_id : id of the device technology to delete
        """
        dt = self._session.query(DeviceTechnology).filter_by(id = dt_id).first()
        if dt:
            for device in self._session.query(Device).filter_by(technology_id = dt.id).all():
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
        return self._session.query(DeviceTechnologyConfig).filter_by(technology_id = dt_id).all()

    def get_device_technology_config(self, dt_id, dtc_key):
        """
        Return information about a device technology config item
        @param dt_id : id of the device technology
        @param dtc_key : key of the device technology config
        @return a DeviceTechnologyConfig object
        """
        return self._session.query(DeviceTechnologyConfig).filter_by(technology_id = dt_id)\
                                                          .filter_by(key = dtc_key)\
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
            dt = self._session.query(DeviceTechnology).filter_by(id = dt_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device technology config with device technology id %s. \
                            It does not exist" % dt_id)
        if self.get_device_technology_config(dt_id, dtc_key):
            raise DbHelperException("This key '%s' already exists for device technology %s" % (dtc_key, dt_id))
        dtc = DeviceTechnologyConfig(technology_id = dt_id, key = dtc_key, value = dtc_value)
        self._session.add(dtc)
        self._session.commit()
        return dtc

    def del_device_technology_config(self, dtc_id):
        """
        Delete a device technology config record
        @param dtc_id : config item id
        """
        dt = self._session.query(DeviceTechnologyConfig).filter_by(id = dtc_id).first()
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

    def find_devices(self, **filters):
        """
        Look for device(s) with filter on their attributes
        @param filters :  filter fields can be one of id, address, type, room, initial_value, 
                          is_value_changeable_by_user, unit_of_stored_values.
        @return a list of Device objects
        """
        device_list = self._session.query(Device)
        for filter in filters:
            filter_arg = "%s = '%s'" % (filter, filters[filter])
            device_list = device_list.filter(filter_arg)

        return device_list.all()

    def get_device(self, d_id):
        """
        Return a device by its it
        @param d_id : The device id
        @return a Device object
        """
        return self._session.query(Device).filter_by(id = d_id).first()

    def add_device(self, d_address, d_technology_id, d_type, d_category_id, d_room_id, 
        d_description = None, d_is_resetable = False, d_initial_value = None,
        d_is_value_changeable_by_user = False, d_unit_of_stored_values ='Percent'):
        """
        Add a device item
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_technology_id : technology id
        @param d_type : One of 'appliance','light','music','sensor'
        @param d_category_id : category id
        @param d_room_id : room id
        @param d_description : Extended item description (100 char max)
        @param d_is_resetable : Can the item be reseted to some initial state
        @param d_initial_value : What's the initial value of the item, should be 
            the state when the item is created (except for sensors, music)
        @param d_is_value_changeable_by_user : Can a user change item state (ex : false for sensor)
        @param d_unit_of_stored_values : What is the unit of item values,
                must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean'
        @return the new Device object
        """
        try:
            room = self._session.query(Room).filter_by(id = d_room_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device with room id %s. It does not exist" % d_room_id)
        try:
            dc = self._session.query(DeviceCategory).filter_by(id = d_category_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device with category id %s. It does not exist" % d_category_id)
        try:
            dt = self._session.query(DeviceTechnology).filter_by(id = d_technology_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device with technology id %s. It does not exist" % d_technology_id)

        if d_unit_of_stored_values not in UNIT_OF_STORED_VALUE_LIST:
            raise ValueError, "d_unit_of_stored_values must be one of %s" % UNIT_OF_STORED_VALUE_LIST
        if d_type not in DEVICE_TYPE_LIST:
            raise ValueError, "d_type must be one of %s" % DEVICE_TYPE_LIST

        device = Device(address = d_address, description = d_description, 
                        technology_id = d_technology_id, type = d_type, 
                        category_id = d_category_id, room_id = d_room_id, 
                        is_resetable = d_is_resetable, initial_value = d_initial_value, 
                        is_value_changeable_by_user = d_is_value_changeable_by_user, 
                        unit_of_stored_values = d_unit_of_stored_values)
        self._session.add(device)
        self._session.commit()
        return device

    def update_device(self, d_id, d_address = None, d_technology_id = None, d_type = None, 
        d_category_id = None, d_room_id = None, d_description = None, d_is_resetable = None, 
        d_initial_value = None, d_is_value_changeable_by_user = None, d_unit_of_stored_values = None):
        """
        Update a device item
        If a param is None, then the old value will be kept
        @param d_id : Device id
        @param d_address : Item address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_description : Extended item description (100 char max)
        @param d_technology : Item technology id
        @param d_type : One of 'appliance','light','music','sensor'
        @param d_category : Item category id
        @param d_room : Item room id
        @param d_is_resetable : Can the item be reseted to some initial state
        @param d_initial_value : What's the initial value of the item, should be 
            the state when the item is created (except for sensors, music)
        @param d_is_value_changeable_by_user : Can a user change item state (ex : false for sensor)
        @param d_unit_of_stored_values : What is the unit of item values,
            must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean'
        @return the updated Device object
        """
        if d_unit_of_stored_values not in [UNIT_OF_STORED_VALUE_LIST, None]: 
            raise ValueError, "d_unit_of_stored_values must be one of %s" % UNIT_OF_STORED_VALUE_LIST
        if d_type not in [DEVICE_TYPE_LIST, None]:
            raise ValueError, "d_type must be one of %s" % DEVICE_TYPE_LIST

        device = self._session.query(Device).filter_by(id = d_id).first()
        if device is None:
            raise DbHelperException("Device with id %s couldn't be found" % d_id)

        if d_address is not None:
            device.address = d_address
        if d_technology_id is not None:
            try:
                dt = self._session.query(DeviceTechnology).filter_by(id = d_technology_id).one()
                device.technology = d_technology_id
            except NoResultFound, e:
                raise DbHelperException("Couldn't update device with technology id %s. It does not exist" % d_technology_id)
        if d_description is not None:
            device.description = d_description
        if d_type is not None:
            device.type = d_type
        if d_category_id is not None:
          try:
              dc = self._session.query(DeviceCategory).filter_by(id = d_category_id).one()
              device.category = d_category_id
          except NoResultFound, e:
              raise DbHelperException("Couldn't update device with category id %s. It does not exist" % d_category_id)
        if d_room_id is not None:
            try:
                room = self._session.query(Room).filter_by(id = d_room_id).one()
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

    def get_all_devices_of_room(self, d_room_id):
        """
        Return all the devices of a room
        @param d_room_id: room id
        @return a list of Device objects
        """
        return self._session.query(Device).filter_by(room_id = d_room_id).all()

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
        return self._session.query(Device).filter_by(category_id = dc_id).all()

    def get_all_devices_of_technology(self, dt_id):
        """
        Returns all the devices of a technology
        @param dt_id : technology id
        @return a list of Device objects
        """
        return self._session.query(Device).filter_by(technology_id = dt_id).all()

####
# Device stats
####
    def list_device_stats(self, device_id):
        """
        Return a list of all stats for a device
        @param device_id : the device id
        @return a list of DeviceStats objects
        """
        return self._session.query(DeviceStats).filter_by(device_id = device_id).all()

    def get_last_stat_of_devices(self, device_list):
        """
        Fetch the last record for all devices in d_list
        @param device_list : list of device ids
        @return a list of DeviceStats objects
        """
        result = []
        for d_id in device_list:
            last_record = self._session.query(DeviceStats)\
                              .filter_by(device_id = d_id)\
                              .order_by(sqlalchemy.desc(DeviceStats.date)).first()
            result.append(last_record)
        return result

    def add_device_stat(self, d_id, ds_date, ds_value):
        """
        Add a device stat record
        @param device_id : device id
        @param ds_date : when the stat was gathered (timestamp)
        @param ds_value : stat value
        @return the new DeviceStats object
        """
        device_stat = DeviceStats(device_id = d_id, date = ds_date, value = ds_value)
        self._session.add(device_stat)
        self._session.commit()
        return device_stat

    def del_device_stat(self, ds_id):
        """
        Delete a stat record
        @param ds_id : record id
        """
        device_stat = self._session.query(DeviceStats).filter_by(id = ds_id).first()
        if device_stat:
            self._session.delete(device_stat)
            self._session.commit()

    def del_all_device_stats(self, d_id):
        """
        Delete all stats for a device
        @param d_id : device id
        """
        #TODO : this could be optimized
        device_stats = self._session.query(DeviceStats).filter_by(device_id = d_id).all()
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
        return self._session.query(Trigger).filter_by(id = t_id).first()

    def add_trigger(self, t_description, t_rule, t_result):
        """
        Add a trigger
        @param t_desc : trigger description
        @param t_rule : trigger rule
        @param t_res : trigger result
        @return the new Trigger object
        """
        trigger = Trigger(description = t_description, rule = t_rule, result = ';'.join(t_result))
        self._session.add(trigger)
        self._session.commit()
        return trigger

    def del_trigger(self, t_id):
        """
        Delete a trigger
        @param t_id : trigger id
        """
        trigger = self._session.query(Trigger).filter_by(id = t_id).first()
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
        return self._session.query(SystemAccount).filter_by(id = a_id).first()

    def add_system_account(self, a_login, a_password, a_is_admin = False):
        """
        Add a system_account
        @param a_login : Account login
        @param a_password : Account clear password (will be hashed in sha256)
        @param a_is_admin : True if it is an admin account, False otherwise
        @return the new SystemAccount object
        """
        password = hashlib.sha256()
        password.update(a_password)
        system_account = SystemAccount(login = a_login, password = password.hexdigest(), is_admin = a_is_admin)
        self._session.add(system_account)
        self._session.commit()
        return system_account

    def del_system_account(self, a_id):
        """
        Delete a system account 
        @param a_id : account id
        """
        system_account = self._session.query(SystemAccount).filter_by(id = a_id).first()
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
        return self._session.query(UserAccount).filter_by(id = u_id).first()

    def get_user_system_account(self, u_id):
        """
        Return a system account associated to a user, if existing
        @param u_id : The user (not system !) account id
        @return a SystemAccount object
        """
        user_account = self._session.query(UserAccount).filter_by(id = u_id).first()
        if user_account is not None:
            try:
                return self._session.query(SystemAccount).filter_by(id = user_account.system_account_id).one()
            except MultipleResultFound, e:
                raise DbHelperException("Database may be incoherent, user with id %s has more than one account" % u_id)

        else:
            return None

    def add_user_account(self, u_first_name, u_last_name, u_birthdate, u_system_account_id = None):
        """
        Add a user account
        @param u_first_name : User's first name
        @param u_last_name : User's last name
        @param u_birthdate : User's birthdate
        @param u_system_account : User's account on the system (can be None)
        @return the new UserAccount object
        """
        user_account = UserAccount(first_name = u_first_name, last_name = u_last_name, 
                                  birthdate = u_birthdate, system_account_id = u_system_account_id)
        self._session.add(user_account)
        self._session.commit()
        return user_account

    def del_user_account(self, u_id):
        """
        Delete a user account and the associated system account if it exists
        @param u_id : user's account id
        """
        user_account = self._session.query(UserAccount).filter_by(id = u_id).first()
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

    def get_system_stat(self, s_name):
        """
        Return a system stat
        @param s_name : the name of the stat to be retrieved
        @return a SystemStats object
        """
        return self._session.query(SystemStats).filter_by(name = s_name).first()


    def get_system_stats_by_type(self, s_type):
        """
        Return a list of all system stats
        @param s_type : type of the stats to be retrieved
        @return a list of SystemStats objects
        """
        return self._session.query(SystemStats).filter_by(type = s_type).all()

    def add_system_stat(self, s_name, s_date, s_type, s_value):
        """
        Add a system stat record
        @param s_name : name of the stat
        @param s_date : when the stat was gathered (timestamp)
        @param s_type : stat type (must be one of sql_schema.SYSTEMSTATS_TYPE_LIST list)
        @param s_value : stat value
        @return the new SystemStats object
        """
        if s_type not in SYSTEMSTATS_TYPE_LIST:
            raise ValueError, "s_type must be one of %s" % SYSTEMSTATS_TYPE_LIST
        system_stat = SystemStats(name = s_name, date = s_date, type = s_type, value = s_value)
        self._session.add(system_stat)
        self._session.commit()
        return system_stat

    def del_system_stat(self, s_name):
        """
        Delete a system stat record
        @param s_name : name of the stat that has to be deleted
        """
        system_stat = self._session.query(SystemStats).filter_by(name = s_name).first()
        if system_stat:
            self._session.delete(system_stat)
            self._session.commit()

    def del_all_system_stats(self):
        """
        Delete all stats for a device
        """
        system_stats = self._session.query(SystemStats).all()
        for system_stat in system_stats:
            self._session.delete(system_stat)
        self._session.commit()

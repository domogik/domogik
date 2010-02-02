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
# device_usage
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
from domogik.common.sql_schema import Area, Device, DeviceUsage, DeviceConfig, \
                                      DeviceStats, DeviceStatsValue, DeviceTechnology, DeviceTechnologyConfig, \
                                      DeviceType, ItemUIConfig, Room, UserAccount, SystemAccount, SystemConfig, \
                                      SystemStats, SystemStatsValue, Trigger
from domogik.common.sql_schema import DEVICE_TECHNOLOGY_LIST, DEVICE_TECHNOLOGY_TYPE_LIST, \
                                      DEVICE_TYPE_LIST, ITEM_TYPE_LIST, UNIT_OF_STORED_VALUE_LIST


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

    def search_areas(self, filters):
        """
        Look for area(s) with filter on their attributes
        @param filters :  filter fields can be one of
        @return a list of Area objects
        """
        assert type(filters) is DictType

        area_list = self._session.query(Area)
        for filter in filters:
            filter_arg = "%s = '%s'" % (filter, filters[filter])
            area_list = area_list.filter(filter_arg)

        return area_list.all()

    def get_area_by_id(self, area_id):
        """
        Fetch area information
        @param area_id : The area id
        @return an area object
        """
        return self._session.query(Area).filter_by(id=area_id).first()

    def get_area_by_name(self, area_name):
        """
        Fetch area information
        @param area_name : The area name
        @return an area object
        """
        return self._session.query(Area).filter_by(name=area_name).first()

    def add_area(self, a_name, a_description=None):
        """
        Add an area
        @param a_name : area name
        @param a_description : area detailed description (optional)
        @return an Area object
        """
        area = Area(name=a_name, description=a_description)
        self._session.add(area)
        self._session.commit()
        return area

    def del_area(self, area_del_id, cascade_delete=False):
        """
        Delete an area record
        @param area_id : id of the area to delete
        @param cascade_delete : True if we wish to delete associated items
        @return the deleted Area object
        """
        area = self._session.query(Area).filter_by(id=area_del_id).first()
        if area:
            area_d = area
            if cascade_delete:
                for room in self._session.query(Room).filter_by(area_id=area_del_id).all():
                    self.del_room(room.id, True)
            self.delete_all_item_ui_config(area.id, 'area')
            self._session.delete(area)
            self._session.commit()
            return area_d
        else:
            raise DbHelperException("Couldn't delete area id %s : it doesn't exist" % area_del_id)

####
# Rooms
####
    def list_rooms(self):
        """
        Return a list of rooms
        @return list of Room objects
        """
        return self._session.query(Room).all()

    def search_rooms(self, filters):
        """
        Look for room(s) with filter on their attributes
        @param filters :  filter fields can be one of
        @return a list of Room objects
        """
        assert type(filters) is DictType

        room_list = self._session.query(Room)
        for filter in filters:
            filter_arg = "%s = '%s'" % (filter, filters[filter])
            room_list = room_list.filter(filter_arg)

        return room_list.all()

    def get_room_by_name(self, r_name):
        """
        Return information about a room
        @param r_name : The room name
        @return a room object
        """
        return self._session.query(Room).filter_by(name=r_name).first()

    def get_room_by_id(self, r_id):
        """
        Return information about a room
        @param r_id : The room id
        @return a room object
        """
        return self._session.query(Room).filter_by(id=r_id).first()

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

    def del_room(self, r_id, cascade_delete=False):
        """
        Delete a room record
        @param r_id : id of the room to delete
        @param cascade_delete : True if we wish to delete associated items
        @return the deleted Room object
        """
        room = self._session.query(Room).filter_by(id=r_id).first()
        if room:
            room_d = room
            if cascade_delete:
                for device in self._session.query(Device).filter_by(room_id=r_id).all():
                    self.del_device(device.id)
            self.delete_all_item_ui_config(room.id, 'room')
            self._session.delete(room)
            self._session.commit()
            return room_d
        else:
            raise DbHelperException("Couldn't delete room id %s : it doesn't exist" % r_id)

    def get_all_rooms_of_area(self, a_area_id):
        """
        Returns all the rooms of an area
        @param a_area_id : the area id
        @return a list of Room objects
        """
        return self._session.query(Room).filter_by(area_id=a_area_id).all()

####
# Device usage
####
    def list_device_usages(self):
        """
        Return a list of device usages
        @return a list of DeviceUsage objects
        """
        return self._session.query(DeviceUsage).all()

    def get_device_usage_by_name(self, du_name,):
        """
        Return information about a device usage
        @param du_name : The device usage name
        @return a DeviceUsage object
        """
        return self._session.query(DeviceUsage).filter_by(name=du_name).first()

    def add_device_usage(self, du_name, du_description=None):
        """
        Add a device_usage (temperature, heating, lighting, music, ...)
        @param du_name : device usage name
        @param du_description : device usage description (optional)
        @return a DeviceUsage (the newly created one)
        """
        du = DeviceUsage(name=du_name, description=du_description)
        self._session.add(du)
        self._session.commit()
        return du

    def del_device_usage(self, du_id, cascade_delete=False):
        """
        Delete a device usage record
        @param dc_id : id of the device usage to delete
        @return the deleted DeviceUsage object
        """
        du = self._session.query(DeviceUsage).filter_by(id=du_id).first()
        if du:
            du_d = du
            if cascade_delete:
                for device in self._session.query(Device).filter_by(usage_id=du.id).all():
                    self.del_device(device.id)
            else:
                device_list = self._session.query(Device).filter_by(usage_id=du.id).all()
                if len(device_list) > 0:
                    raise DbHelperException("Couldn't delete device usage %s : there are associated devices" % du_id)

            self._session.delete(du)
            self._session.commit()
            return du_d
        else:
            raise DbHelperException("Couldn't delete device usage id %s : it doesn't exist" % du_id)

####
# Device type
####
    def list_device_types(self):
        """
        Return a list of device types
        @return a list of DeviceType objects
        """
        return self._session.query(DeviceType).all()

    def get_device_type_by_name(self, dty_name):
        """
        Return information about a device type
        @param dty_name : The device type name
        @return a DeviceType object
        """
        return self._session.query(DeviceType).filter_by(name=dty_name).first()

    def add_device_type(self, dty_name, dt_id, dty_description=None):
        """
        Add a device_type (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param dty_name : device type name
        @param dt_id : technology id (x10, plcbus,...)
        @param dty_description : device type description (optional)
        @return a DeviceType (the newly created one)
        """
        dty = DeviceType(name=dty_name, description=dty_description, technology_id=dt_id)
        self._session.add(dty)
        self._session.commit()
        return dty

    def del_device_type(self, dty_id, cascade_delete=False):
        """
        Delete a device type record
        @param dc_id : id of the device type to delete
        @return the deleted DeviceType object
        """
        dty = self._session.query(DeviceType).filter_by(id=dty_id).first()
        if dty:
            dty_d = dty
            if cascade_delete:
                for device in self._session.query(Device).filter_by(usage_id=dty.id).all():
                    self.del_device(device.id)
            else:
                device_list = self._session.query(Device).filter_by(usage_id=dty.id).all()
                if len(device_list) > 0:
                    raise DbHelperException("Couldn't delete device type %s : there are associated devices" % dty_id)

            self._session.delete(dty)
            self._session.commit()
            return dty_d
        else:
            raise DbHelperException("Couldn't delete device type id %s : it doesn't exist" % dty_id)

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

    def del_device_technology(self, dt_id, cascade_delete=False):
        """
        Delete a device technology record
        @param dt_id : id of the device technology to delete
        @return the deleted DeviceTechnology object
        """
        dt = self._session.query(DeviceTechnology).filter_by(id=dt_id).first()
        if dt:
            dt_d = dt
            if cascade_delete:
                for device_type in self._session.query(DeviceType).filter_by(technology_id=dt.id).all():
                    self.del_device_type(device_type.id)
            else:
                device_type_list = self._session.query(DeviceType).filter_by(technology_id=dt.id).all()
                if len(device_type_list) > 0:
                    raise DbHelperException("Couldn't delete device technology %s : there are associated device types" % dt_id)
            dtc_list = self._session.query(DeviceTechnologyConfig).filter_by(technology_id=dt.id).all()
            for dtc in dtc_list:
                self.del_device_technology_config(dtc.id)

            self._session.delete(dt)
            self._session.commit()
            return dt_d
        else:
            raise DbHelperException("Couldn't delete device technology id %s : it doesn't exist" % dt_id)

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

    def list_all_device_technology_config(self):
        """
        Return a list of all device technology configuration
        @param dt_id : id of the device technology
        @return a list of DeviceTechnologyConfig objects
        """
        return self._session.query(DeviceTechnologyConfig).all()

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

    def add_device_technology_config(self, dt_id, dtc_key, dtc_value, dtc_description):
        """
        Add a device's technology config item
        @param dt_id : the device technology id
        @param dtc_key : The device technology config key
        @param dtc_value : The device technology config value
        @param dtc_description : The device technology config description
        @return the new DeviceTechnologyConfig item
        """
        try:
            dt = self._session.query(DeviceTechnology).filter_by(id=dt_id).one()
        except NoResultFound, e:
            raise DbHelperException("Couldn't add device technology config with device technology id %s. \
                            It does not exist" % dt_id)
        if self.get_device_technology_config(dt_id, dtc_key):
            raise DbHelperException("This key '%s' already exists for device technology %s" % (dtc_key, dt_id))
        dtc = DeviceTechnologyConfig(technology_id=dt_id, key=dtc_key, value=dtc_value, description=dtc_description)
        self._session.add(dtc)
        self._session.commit()
        return dtc

    def del_device_technology_config(self, dtc_id):
        """
        Delete a device technology config record
        @param dtc_id : config item id
        @return the deleted DeviceTechnologyConfig object
        """
        dtc = self._session.query(DeviceTechnologyConfig).filter_by(id=dtc_id).first()
        if dtc:
            dtc_d = dtc
            self._session.delete(dtc)
            self._session.commit()
            return dtc_d
        else:
            raise DbHelperException("Couldn't delete device technology config id %s : it doesn't exist" % dtc_id)

###
# Devices
###
    def list_devices(self):
        """
        Returns a list of devices
        @return a list of Device objects
        """
        return self._session.query(Device).all()

    def search_devices(self, filters):
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

    def find_devices(self, d_room_id_list, d_usage_id_list):
        """
        Look for devices that have at least 1 item in room_id_list AND 1 item in usage_id_list
        @param room_id_list : list of room ids
        @param usage_id_list : list of usage ids
        @return a list of DeviceObject items
        """
        assert type(d_room_id_list) is ListType or type(d_room_id_list) is NoneType
        assert type(d_usage_id_list) is ListType or type(d_usage_id_list) is NoneType

        device_list = self._session.query(Device)
        if d_room_id_list is not None and len(d_room_id_list) != 0:
            device_list = device_list.filter(Device.room_id.in_(d_room_id_list))
        if d_usage_id_list is not None and len(d_usage_id_list) != 0:
            device_list = device_list.filter(Device.usage_id.in_(d_usage_id_list))
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

    def get_all_devices_of_usage(self, dc_id):
        """
        Return all the devices of a usage
        @param du_id: usage id
        @return a list of Device objects
        """
        return self._session.query(Device).filter_by(usage_id=du_id).all()

    def get_all_devices_of_technology(self, dt_id):
        """
        Returns all the devices of a technology
        @param dt_id : technology id
        @return a list of Device objects
        """
        return self._session.query(Device).filter_by(technology_id=dt_id).all()

    def add_device(self, d_name, d_address, d_type_id, d_usage_id, d_room_id,
        d_description=None, d_reference=None, d_is_resetable=False, d_initial_value=None,
        d_is_value_changeable_by_user=False, d_unit_of_stored_values=None):
        """
        Add a device item
        @param d_name : name of the device
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_type_id : type id (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param d_usage_id : usage id
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
        if d_unit_of_stored_values not in UNIT_OF_STORED_VALUE_LIST:
            raise ValueError, "d_unit_of_stored_values must be one of %s" % UNIT_OF_STORED_VALUE_LIST

        device = Device(name=d_name, address=d_address, description=d_description,
                        reference=d_reference, type_id=d_type_id,
                        usage_id=d_usage_id, room_id=d_room_id,
                        is_resetable=d_is_resetable, initial_value=d_initial_value,
                        is_value_changeable_by_user=d_is_value_changeable_by_user,
                        unit_of_stored_values=d_unit_of_stored_values)
        self._session.add(device)
        self._session.commit()
        return device

    def update_device(self, d_id, d_name=None, d_address=None, d_technology_id=None, d_type_id=None,
        d_usage_id=None, d_room_id=None, d_description=None, d_reference=None, d_is_resetable=None,
        d_initial_value=None, d_is_value_changeable_by_user=None, d_unit_of_stored_values =None):
        """
        Update a device item
        If a param is None, then the old value will be kept
        @param d_id : Device id
        @param d_name : device name (optional)
        @param d_address : Item address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire) (optional)
        @param d_description : Extended item description (optional)
        @param d_type_id : type id (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param d_usage : Item usage id (optional)
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

        device = self._session.query(Device).filter_by(id=d_id).first()
        if device is None:
            raise DbHelperException("Device with id %s couldn't be found" % d_id)

        if d_name is not None:
            device.name = d_name
        if d_address is not None:
            device.address = d_address
        if d_description is not None:
            device.description = d_description
        if d_reference is not None:
            device.reference = d_reference
        if d_type_id is not None:
            device.type_id = d_type_id
        if d_usage_id is not None:
          try:
              dc = self._session.query(DeviceUsage).filter_by(id=d_usage_id).one()
              device.usage = d_usage_id
          except NoResultFound, e:
              raise DbHelperException("Couldn't update device with usage id %s. It does not exist" % d_usage_id)
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
        Warning : this deletes also the associated objects (DeviceConfig, DeviceStats, DeviceStatsValue)
        @param d_id : item id
        @return the deleted Device object
        """
        device = self.get_device(d_id)
        if device is None:
            raise DbHelperException("Device with id %s couldn't be found" % d_id)

        device_d = device
        for device_conf in self._session.query(DeviceConfig).filter_by(device_id=d_id).all():
            self._session.delete(device_conf)

        for device_stats in self._session.query(DeviceStats).filter_by(device_id=d_id).all():
            for device_stats_value in self._session.query(DeviceStatsValue)\
                                          .filter_by(device_stats_id=device_stats.id).all():
                self._session.delete(device_stats_value)
            self._session.delete(device_stats)
        self.delete_all_item_ui_config(device.id, 'device')
        self._session.delete(device)
        self._session.commit()
        return device_d

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

    def list_all_device_stats(self):
        """
        Return a list of all device stats
        @return a list of DeviceStats objects
        """
        return self._session.query(DeviceStats).all()

    def list_device_stats_values(self, d_device_stats_id):
        """
        Return a list of all values associated to a device statistic
        @param d_device_stats_id : the device statistic id
        @return a list of DeviceStatsValue objects
        """
        return self._session.query(DeviceStatsValue).filter_by(device_stats_id=d_device_stats_id).all()

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

    def add_device_stat(self, d_id, ds_date, ds_values):
        """
        Add a device stat record
        @param device_id : device id
        @param ds_date : when the stat was gathered (timestamp)
        @param ds_value : dictionnary of statistics values
        @return the new DeviceStats object
        """
        device_stat = DeviceStats(device_id=d_id, date=ds_date)
        self._session.add(device_stat)
        self._session.commit()
        for ds_name in ds_values.keys():
            dsv = DeviceStatsValue(name=ds_name, value=ds_values[ds_name], device_stats_id=device_stat.id)
            self._session.add(dsv)

        self._session.commit()
        return device_stat

    def del_device_stat(self, ds_id):
        """
        Delete a stat record
        @param ds_id : record id
        @return the deleted DeviceStat object
        """
        device_stat = self._session.query(DeviceStats).filter_by(id=ds_id).first()
        if device_stat:
            device_stat_d = device_stat
            self._session.delete(device_stat)
            for device_stats_value in self._session.query(DeviceStatsValue) \
                                          .filter_by(device_stats_id=device_stat.id).all():
                self._session.delete(device_stats_value)
            self._session.commit()
            return device_stat_d
        else:
            raise DbHelperException("Couldn't delete device stat id %s : it doesn't exist" % ds_id)

    def del_all_device_stats(self, d_id):
        """
        Delete all stats for a device
        @param d_id : device id
        @return the list of DeviceStatsValue objects that were deleted
        """
        #TODO : this could be optimized
        device_stats = self._session.query(DeviceStats).filter_by(device_id=d_id).all()
        device_stats_d_list = []
        for device_stat in device_stats:
            for device_stats_value in self._session.query(DeviceStatsValue) \
                                          .filter_by(device_stats_id=device_stat.id).all():
                self._session.delete(device_stats_value)
            device_stats_d_list.append(device_stat)
            self._session.delete(device_stat)
        self._session.commit()
        return device_stats_d_list

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
        @return the deleted Trigger object
        """
        trigger = self._session.query(Trigger).filter_by(id=t_id).first()
        if trigger:
            trigger_d = trigger
            self._session.delete(trigger)
            self._session.commit()
            return trigger
        else:
            raise DbHelperException("Couldn't delete trigger id %s : it doesn't exist" % t_id)

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

    def get_system_account_by_login_and_pass(self, a_login, a_password):
        """
        Return system account information from login
        @param a_login : login
        @param a_pass : password (clear)
        @return a SystemAccount object or None if login / password is wrong
        """
        sha_pass = hashlib.sha256()
        sha_pass.update(a_password)
        return self._session.query(SystemAccount).filter_by(login=a_login, password=sha_pass.hexdigest()).first()

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
        @return True or False
        """
        system_account = self.get_system_account_by_login(a_login)
        if system_account is not None:
            password = hashlib.sha256()
            password.update(a_password)
            if system_account.password == password.hexdigest():
                return True
        return False

    def add_system_account(self, a_login, a_password, a_is_admin=False, a_skin_used='skins/default'):
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
        system_account = SystemAccount(login=a_login, password=password.hexdigest(),
                                      is_admin=a_is_admin, skin_used=a_skin_used)
        self._session.add(system_account)
        self._session.commit()
        return system_account

    def add_default_system_account(self):
        """
        Add a default system account (login = admin, password = domogik, is_admin = True)
        @return a SystemAccount object
        """
        return self.add_system_account(a_login='admin', a_password='123', a_is_admin=True)

    def del_system_account(self, a_id):
        """
        Delete a system account
        @param a_id : account id
        @return the deleted SystemAccount object
        """
        system_account = self._session.query(SystemAccount).filter_by(id=a_id).first()
        if system_account:
            system_account_d = system_account
            self._session.delete(system_account)
            self._session.commit()
            return system_account_d
        else:
            raise DbHelperException("Couldn't delete system account id %s : it doesn't exist" % a_id)

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
        @return the deleted UserAccount object
        """
        user_account = self._session.query(UserAccount).filter_by(id=u_id).first()
        if user_account is not None:
            user_account_d = user_account
            if user_account.system_account_id is not None:
                self.del_system_account(user_account.system_account_id)
            self._session.delete(user_account)
            self._session.commit()
            return user_account_d
        else:
            raise DbHelperException("Couldn't delete user account id %s : it doesn't exist" % u_id)

####
# System stats
####
    def list_system_stats(self):
        """
        Return a list of all system stats
        @return a list of SystemStats objects
        """
        return self._session.query(SystemStats).all()

    def list_system_stats_values(self, s_system_stats_id):
        """
        Return a list of all values associated to a system statistic
        @param s_system_stats_id : the system statistic id
        @return a list of SystemStatsValue objects
        """
        return self._session.query(SystemStatsValue).filter_by(system_stats_id=s_system_stats_id).all()

    def get_system_stat(self, s_id):
        """
        Return a system stat
        @param s_name : the name of the stat to be retrieved
        @return a SystemStats object
        """
        return self._session.query(SystemStats).filter_by(id=s_id).first()

    def add_system_stat(self, s_name, s_hostname, s_date, s_values):
        """
        Add a system stat record
        @param s_name : name of the  module
        @param s_hostname : name of the  host
        @param s_date : when the stat was gathered (timestamp)
        @param s_values : a dictionnary of system statistics values
        @return the new SystemStats object
        """
        system_stat = SystemStats(module_name=s_name, host_name=s_hostname, date=s_date)
        self._session.add(system_stat)
        self._session.commit()
        for stat_value_name in s_values.keys():
            ssv = SystemStatsValue(name=stat_value_name, value=s_values[stat_value_name],
                                  system_stats_id=system_stat.id)
            self._session.add(ssv)

        self._session.commit()
        return system_stat

    def del_system_stat(self, s_name):
        """
        Delete a system stat record
        @param s_name : name of the stat that has to be deleted
        @return the deleted SystemStats object
        """
        system_stat = self._session.query(SystemStats).filter_by(name=s_name).first()
        if system_stat:
            system_stat_d = system_stat
            system_stats_values = self._session.query(SystemStatsValue)\
                                      .filter_by(system_stats_id=system_stat.id).all()
            for ssv in system_stats_values:
                self._session.delete(ssv)
            self._session.delete(system_stat)
            self._session.commit()
            return system_stat
        else:
            raise DbHelperException("Couldn't delete system stat %s : it doesn't exist" % s_name)

    def del_all_system_stats(self):
        """
        Delete all stats of the system
        @return the list of deleted SystemStats objects
        """
        system_stats_list = self._session.query(SystemStats).all()
        system_stats_d_list = []
        for system_stat in system_stats_list:
            system_stats_values = self._session.query(SystemStatsValue)\
                                      .filter_by(system_stats_id=system_stat.id).all()
            for ssv in system_stats_values:
                self._session.delete(ssv)
            system_stats_d_list.append(system_stat)
            self._session.delete(system_stat)
        self._session.commit()
        return system_stats_d_list


###
# ItemUIConfig
###

    def add_item_ui_config(self, i_item_id, i_item_type, i_parameters):
        """
        Add a UI parameter for an item
        @param i_item_id : id of the item we want to bind a parameter
        @param i_item_type : the item type (area, room, device) to add a configuration parameter
        @param i_parameters : dictionnary of named parameters to add {key1:value1, key2:value2,...}
        """
        item_ui_config = None
        if i_item_type not in ITEM_TYPE_LIST:
            raise DbHelperException("Unknown item type '%s', should be one of : %s" \
                                    % (i_item_type, ITEM_TYPE_LIST))
        item = None
        if i_item_type == 'device':
            item = self.get_device(i_item_id)
        elif i_item_type == 'area':
            item = self.get_area_by_id(i_item_id)
        elif i_item_type == 'room':
            item = self.get_room_by_id(i_item_id)

        if item is None:
            raise DbHelperException("Can't find this item  (%s,%s)" % (i_item_id, i_item_type))

        for param in i_parameters:
            item_ui_config = ItemUIConfig(item_id=i_item_id, item_type=i_item_type,
                                          key=param, value=i_parameters[param])
            self._session.add(item_ui_config)
            self._session.commit()

    def update_item_ui_config(self, i_item_id, i_item_type, i_key, i_value):
        """
        Update a UI parameter of an item
        @param i_item_id : id of the item we want to update the parameter
        @param i_item_type : type of the item (area, room, device)
        @param i_key : key we want to update
        @param i_value : key value
        @return : the updated ItemUIConfig item
        """
        if i_item_type not in ITEM_TYPE_LIST:
            raise DbHelperException("Unknown item type '%s', should be one of : %s" \
                                    % (i_item_type, ITEM_TYPE_LIST))
        item_ui_config = self._session.query(ItemUIConfig)\
                                      .filter_by(item_id=i_item_id, item_type=i_item_type, key=i_key).first()
        if item_ui_config is None:
            raise DbHelperException("Can't find item (%s,%s) with key '%s' : can't update it" \
                                    % (i_item_id, i_item_key, i_key))
        item_ui_config.value = i_value
        self._session.add(item_ui_config)
        self._session.commit()
        return item_ui_config

    def get_item_ui_config(self, i_item_id, i_item_type, i_key):
        """
        Get a UI parameter of an item
        @param i_item_id : id of the item we want to update the parameter
        @param i_item_type : type of the item (area, room, device)
        @param i_key : key we want to get the value
        @return an ItemUIConfig object
        """
        if i_item_type not in ITEM_TYPE_LIST:
            raise DbHelperException("Unknown item type '%s', should be one of : %s" \
                                    % (i_item_type, ITEM_TYPE_LIST))
        item_ui_config = self._session.query(ItemUIConfig)\
                                      .filter_by(item_id=i_item_id, item_type=i_item_type, key=i_key).first()
        return item_ui_config

    def list_item_ui_config(self, i_item_id, i_item_type):
        """
        List all UI parameters of an item
        @param i_item_id : if of the item we want to list the parameters
        @param i_item_type : type of the item (area, room, device)
        @return a list of ItemUIConfig objects
        """
        if i_item_type not in ITEM_TYPE_LIST:
            raise DbHelperException("Unknown item type '%s', should be one of : %s" \
                                    % (i_item_type, ITEM_TYPE_LIST))
        return self._session.query(ItemUIConfig).filter_by(item_id=i_item_id,
                                                    item_type=i_item_type).all()

    def list_all_item_ui_config(self):
        """
        List all UI parameters
        @return a list of ItemUIConfig objects
        """
        return self._session.query(ItemUIConfig).all()

    def delete_item_ui_config(self, i_item_id, i_item_type, i_key):
        """
        Delete a UI parameter of an item
        @param i_item_id : id of the item we want to delete its parameter
        @param i_item_type : type of the item (area, room, device)
        @param i_key : key corresponding to the parameter name we want to delete
        @return the deleted ItemUIConfig object
        """
        if i_item_type not in ITEM_TYPE_LIST:
            raise DbHelperException("Unknown item type '%s', should be one of : %s" \
                                    % (i_item_type, ITEM_TYPE_LIST))
        item_ui_config = self._session.query(ItemUIConfig)\
                                      .filter_by(item_id=i_item_id, item_type=i_item_type, key=i_key).first()
        if item_ui_config is None:
            raise DbHelperException("Can't find item (%s,%s) with key '%s'" \
                                    % (i_item_id, i_item_type, i_key))
        item_ui_config_d = item_ui_config
        self._session.delete(item_ui_config)
        self._session.commit()
        return item_ui_config_d

    def delete_all_item_ui_config(self, i_item_id, i_item_type):
        """
        Delete all UI parameter of an item
        @param i_item_id : id of the item we want to delete its parameter
        @param i_item_type : type of the item (area, room, device)
        """
        if i_item_type not in ITEM_TYPE_LIST:
            raise DbHelperException("Unknown item type '%s', should be one of : %s" \
                                    % (i_item_type, ITEM_TYPE_LIST))
        item_ui_config_list = self._session.query(ItemUIConfig)\
                                           .filter_by(item_id=i_item_id, item_type=i_item_type).all()
        item_ui_config_d_list = []
        for item_ui_config in item_ui_config_list:
            self._session.delete(item_ui_config)
            self._session.commit()
            item_ui_config_d_list.append(item_ui_config)

        return item_ui_config_d_list

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

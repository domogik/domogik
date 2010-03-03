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
Please don't forget to add unit test in 'database_test.py' if you add a new
method. Please always run 'python database_test.py' if you change something in
this file.

Implements
==========

- class DbHelperException(Exception) : exceptions linked to the DbHelper class
- class DbHelper : API to use Domogik database

@author: Maxence DUNNEWIND / Marc SCHNEIDER
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import copy, datetime, hashlib
from types import DictType, ListType, NoneType

import sqlalchemy
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound


from domogik.common.configloader import Loader
from domogik.common.sql_schema import ActuatorFeature, Area, Device, DeviceUsage, \
                                      DeviceConfig, DeviceStats, DeviceStatsValue, \
                                      DeviceTechnology, DeviceTechnologyConfig, \
                                      DeviceType, UIItemConfig, Room, Person, \
                                      SensorReferenceData, UserAccount, SystemConfig, \
                                      SystemStats, SystemStatsValue, Trigger
from domogik.common.sql_schema import DEVICE_TECHNOLOGY_LIST


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
    __dbprefix = None
    __engine = None
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
                url = "%s%s:%s@%s:%s/%s" % (url, db['db_user'], \
                                            db['db_password'],
                                            db['db_host'], db['db_port'], \
                                            db['db_name'])
            else:
                url = "%s%s:%s@%s/%s" % (url, db['db_user'], db['db_password'],
                                         db['db_host'], db['db_name'])

        if use_test_db:
            url = '%s_test' % url
        # Connecting to the database
        self.__dbprefix = db['db_prefix']
        self.__engine = sqlalchemy.create_engine(url, echo=echo_output)
        Session = sessionmaker(bind=self.__engine, autoflush=False)
        self._session = Session()

    def __rollback(self):
        """
        Issue a rollback to a SQL transaction (for dev purposes only)
        """
        self._session.rollback()

####
# Areas
####
    def list_areas(self):
        """
        Return all areas
        @return list of Area objects
        """
        return self._session.query(Area).all()

    def list_areas_with_rooms(self):
        """
        Return all areas with associated rooms
        @return a list of Area objects containing the associated room list
        """
        area_list = self._session.query(Area).all()
        area_rooms_list = []
        for area in area_list:
            # to avoid creating a join with following request
            room_list = self._session.query(Room)\
                            .filter_by(area_id=area.id).all()
            # set Room in area object
            area.Room = room_list
            area_rooms_list.append(area)
        return area_rooms_list

    def search_areas(self, filters):
        """
        Look for area(s) with filter on their attributes
        @param filters :  filter fields can be one of
        @return a list of Area objects
        """
        if type(filters) is not DictType:
            raise DbHelperException("Wrong type of 'filters', Should be a dictionnary")
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
        return self._session.query(Area)\
                            .filter(func.lower(Area.name)==area_name.lower())\
                            .first()

    def add_area(self, a_name, a_description=None):
        """
        Add an area
        @param a_name : area name
        @param a_description : area detailed description (optional)
        @return an Area object
        """
        self._session.expire_all()
        area = Area(name=a_name, description=a_description)
        self._session.add(area)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return area

    def update_area(self, a_id, a_name=None, a_description=None):
        """
        Update an area
        @param a_id : area id to be updated
        @param a_name : area name (optional)
        @param a_description : area detailed description (optional)
        @return an Area object
        """
        self._session.expire_all()
        area = self._session.query(Area).filter_by(id=a_id).first()
        if area is None:
            raise DbHelperException("Area with id %s couldn't be found" % a_id)
        if a_name is not None:
            area.name = a_name
        if a_description is not None:
            if a_description == '': a_description = None
            area.description = a_description
        self._session.add(area)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return area

    def del_area(self, area_del_id, cascade_delete=False):
        """
        Delete an area record
        @param area_id : id of the area to delete
        @param cascade_delete : True if we wish to delete associated items
        @return the deleted Area object
        """
        self._session.expire_all()
        area = self._session.query(Area).filter_by(id=area_del_id).first()
        if area:
            area_d = area
            if cascade_delete:
                for room in self._session.query(Room)\
                                         .filter_by(area_id=area_del_id).all():
                    self.del_room(room.id, True)
            self._session.delete(area)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return area_d
        else:
            raise DbHelperException("Couldn't delete area with id %s : \
                                    it doesn't exist" % area_del_id)

####
# Rooms
####
    def list_rooms(self):
        """
        Return a list of rooms
        @return list of Room objects
        """
        return self._session.query(Room).all()

    def list_rooms_with_devices(self):
        """
        Return all rooms with associated devices
        @return a list of Room objects containing the associated device list
        """
        room_list = self._session.query(Room).all()
        room_devices_list = []
        for room in room_list:
            device_list = self._session.query(Device)\
                              .filter_by(room_id=room.id).all()
            # set Room in area object
            room.Device = device_list
            room_devices_list.append(room)
        return room_devices_list

    def search_rooms(self, filters):
        """
        Look for room(s) with filter on their attributes
        @param filters :  filter fields (dictionnary)
        @return a list of Room objects
        """
        if type(filters) is not DictType:
            raise DbHelperException("Wrong type of 'filters', Should be a dictionnary")
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
        return self._session.query(Room)\
                            .filter(func.lower(Room.name)==r_name.lower())\
                            .first()

    def get_room_by_id(self, r_id):
        """
        Return information about a room
        @param r_id : The room id
        @return a room object
        """
        return self._session.query(Room).filter_by(id=r_id).first()

    def add_room(self, r_name, r_area_id=None, r_description=None):
        """
        Add a room
        @param r_name : room name
        @param area_id : id of the area where the room is, optional
        @param r_description : room detailed description, optional
        @return : a room object
        """
        self._session.expire_all()
        if r_area_id != None:
            try:
                self._session.query(Area).filter_by(id=r_area_id).one()
            except NoResultFound:
                raise DbHelperException("Couldn't add room with area id %s. It does not exist" % r_area_id)
        room = Room(name=r_name, description=r_description, area_id=r_area_id)
        self._session.add(room)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return room

    def update_room(self, r_id, r_name=None, r_area_id=None, r_description=None):
        """
        Update a room
        @param r_id : room id to be updated
        @param r_name : room name (optional)
        @param r_description : room detailed description (optional)
        @param r_area_id : id of the area the room belongs to (optional)
        @return a Room object
        """
        self._session.expire_all()
        room = self._session.query(Room).filter_by(id=r_id).first()
        if room is None:
            raise DbHelperException("Room with id %s couldn't be found" % r_id)
        if r_name is not None:
            room.name = r_name
        if r_description is not None:
            if r_description == '': r_description = None
            room.description = r_description
        if r_area_id is not None:
            if r_area_id != '':
                try:
                    self._session.query(Area).filter_by(id=r_area_id).one()
                except NoResultFound:
                    raise DbHelperException("Couldn't find area id %s. It does not exist" % r_area_id)
            else:
                r_area_id = None
            room.area_id = r_area_id
        self._session.add(room)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return room

    def del_room(self, r_id, cascade_delete=False):
        """
        Delete a room record
        @param r_id : id of the room to delete
        @param cascade_delete : True if we wish to delete associated items
        @return the deleted Room object
        """
        self._session.expire_all()
        room = self._session.query(Room).filter_by(id=r_id).first()
        if room:
            room_d = room
            if cascade_delete:
                for device in self._session.query(Device)\
                                           .filter_by(room_id=r_id).all():
                    self.del_device(device.id)
            self._session.delete(room)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return room_d
        else:
            raise DbHelperException("Couldn't delete room with id %s : \
                                     it doesn't exist" % r_id)

    def get_all_rooms_of_area(self, a_area_id):
        """
        Returns all the rooms of an area
        @param a_area_id : the area id
        @return a list of Room objects
        """
        return self._session.query(Room)\
                            .filter_by(area_id=a_area_id).all()

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
        return self._session.query(DeviceUsage)\
                            .filter(func.lower(DeviceUsage.name)==du_name.lower())\
                            .first()

    def add_device_usage(self, du_name, du_description=None):
        """
        Add a device_usage (temperature, heating, lighting, music, ...)
        @param du_name : device usage name
        @param du_description : device usage description (optional)
        @return a DeviceUsage (the newly created one)
        """
        self._session.expire_all()
        du = DeviceUsage(name=du_name, description=du_description)
        self._session.add(du)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return du

    def update_device_usage(self, du_id, du_name=None, du_description=None):
        """
        Update a device usage
        @param du_id : device usage id to be updated
        @param du_name : device usage name (optional)
        @param du_description : device usage detailed description (optional)
        @return a DeviceUsage object
        """
        self._session.expire_all()
        device_usage = self._session.query(DeviceUsage)\
                                    .filter_by(id=du_id).first()
        if device_usage is None:
            raise DbHelperException("DeviceUsage with id %s couldn't be found" % du_id)
        if du_name is not None:
            device_usage.name = du_name
        if du_description is not None:
            if du_description == '': du_description = None
            device_usage.description = du_description
        self._session.add(device_usage)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return device_usage

    def del_device_usage(self, du_id, cascade_delete=False):
        """
        Delete a device usage record
        @param dc_id : id of the device usage to delete
        @return the deleted DeviceUsage object
        """
        self._session.expire_all()
        du = self._session.query(DeviceUsage).filter_by(id=du_id).first()
        if du:
            du_d = du
            if cascade_delete:
                for device in self._session.query(Device)\
                                           .filter_by(usage_id=du.id).all():
                    self.del_device(device.id)
            else:
                device_list = self._session.query(Device)\
                                           .filter_by(usage_id=du.id).all()
                if len(device_list) > 0:
                    raise DbHelperException("Couldn't delete device usage %s : \
                                            there are associated devices" % du_id)

            self._session.delete(du)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return du_d
        else:
            raise DbHelperException("Couldn't delete device usage with id %s : \
                                    it doesn't exist" % du_id)

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
        return self._session.query(DeviceType)\
                            .filter(func.lower(DeviceType.name)==dty_name.lower())\
                            .first()

    def add_device_type(self, dty_name, dt_id, dty_description=None):
        """
        Add a device_type (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param dty_name : device type name
        @param dt_id : technology id (x10, plcbus,...)
        @param dty_description : device type description (optional)
        @return a DeviceType (the newly created one)
        """
        self._session.expire_all()
        try:
            self._session.query(DeviceTechnology).filter_by(id=dt_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add device type with technology id %s. \
                                    It does not exist" % dt_id)
        dty = DeviceType(name=dty_name, description=dty_description,
                         technology_id=dt_id)
        self._session.add(dty)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return dty

    def update_device_type(self, dty_id, dty_name=None, dt_id=None,
                           dty_description=None):
        """
        Update a device type
        @param dty_id : device type id to be updated
        @param dty_name : device type name (optional)
        @param dt_id : id of the associated technology (optional)
        @param dty_description : device type detailed description (optional)
        @return a DeviceType object
        """
        self._session.expire_all()
        device_type = self._session.query(DeviceType).filter_by(id=dty_id).first()
        if device_type is None:
            raise DbHelperException("DeviceType with id %s couldn't be found" % dty_id)
        if dty_name is not None:
            device_type.name = dty_name
        if dt_id is not None:
            try:
                self._session.query(DeviceTechnology).filter_by(id=dt_id).one()
            except NoResultFound:
                raise DbHelperException("Couldn't find technology id %s. It does not exist" % dt_id)
            device_type.technology_id = dt_id
        self._session.add(device_type)
        if dty_description is not None:
            if dty_description == '': dty_description = None
            device_type.description = dty_description
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return device_type

    def del_device_type(self, dty_id, cascade_delete=False):
        """
        Delete a device type record
        @param dty_id : id of the device type to delete
        @return the deleted DeviceType object
        """
        self._session.expire_all()
        dty = self._session.query(DeviceType).filter_by(id=dty_id).first()
        if dty:
            dty_d = dty
            if cascade_delete:
                for device in self._session.query(Device)\
                                           .filter_by(type_id=dty.id).all():
                    self.del_device(device.id)
                for srd in self._session.query(SensorReferenceData)\
                                        .filter_by(device_type_id=dty.id).all():
                    self.del_sensor_reference_data(srd.id)
                for af in self._session.query(ActuatorFeature)\
                                        .filter_by(device_type_id=dty.id).all():
                    self.del_actuator_feature(af.id)
            else:
                device_list = self._session.query(Device).filter_by(type_id=dty.id).all()
                if len(device_list) > 0:
                    raise DbHelperException("Couldn't delete device type %s : \
                                             there are associated device(s)" % dty_id)
                srd_list = self._session.query(SensorReferenceData)\
                                        .filter_by(device_type_id=dty.id).all()
                if len(srd_list) > 0:
                    raise DbHelperException("Couldn't delete device type %s : \
                                             there are associated sensor \
                                             reference data" % dty_id)
                af_list = self._session.query(ActuatorFeature)\
                                       .filter_by(device_type_id=dty.id).all()
                if len(af_list) > 0:
                    raise DbHelperException("Couldn't delete device type %s : \
                                             there are associated actuator\
                                             feature(s)" % dty_id)
            self._session.delete(dty)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return dty_d
        else:
            raise DbHelperException("Couldn't delete device type with id %s : \
                                    it doesn't exist" % dty_id)

####
# Sensor reference data
####
    def list_sensor_reference_data(self):
        """
        Return a list of sensor reference data
        @return a list of SensorReferenceData objects
        """
        return self._session.query(SensorReferenceData).all()

    def get_sensor_reference_data_by_name(self, srd_name):
        """
        Return information about a sensor reference data
        @param srd_name : The sensor reference data name
        @return a SensorReferenceData object
        """
        return self._session.query(SensorReferenceData)\
                            .filter(func.lower(SensorReferenceData.name)==srd_name.lower())\
                            .first()

    def add_sensor_reference_data(self, srd_name, srd_value, dty_id,
                                  srd_unit=None, srd_stat_key=None):
        """
        Add a sensor reference data
        @param srd_name : name (ex. Temperature)
        @param srd_value : value (number, string, trigger, complex...)
        @param dty_id : id of the device type
        @param srd_unit  unit of the value (ex. degreeC), optional
        @param srd_stat_key : reference to a stat, optional
        @return a SensorReferenceData (the newly created one)
        """
        self._session.expire_all()
        try:
            self._session.query(DeviceType).filter_by(id=dty_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add sensor reference with device type id %s. \
                                    It does not exist" % dty_id)
        srd = SensorReferenceData(name=srd_name, value=srd_value,
                    device_type_id=dty_id, unit=srd_unit, stat_key=srd_stat_key)
        self._session.add(srd)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return srd

    def update_sensor_reference_data(self, srd_id, srd_name=None, srd_value=None,
                                     dty_id=None, srd_unit=None,
                                     srd_stat_key=None):
        """
        Update a sensor reference data
        @param srd_id : id of the sensor reference data to update
        @param srd_name : name (ex. Temperature), optional
        @param srd_value : value (number, string, trigger, complex...), optional
        @param dty_id : id of the device type, optional
        @param srd_unit  unit of the value (ex. degreeC), optional
        @param srd_stat_key : reference to a stat, optional
        @return a SensorReferenceData (the updated one)
        """
        self._session.expire_all()
        srd = self._session.query(SensorReferenceData)\
                           .filter_by(id=srd_id)\
                           .first()
        if srd is None:
            raise DbHelperException("SensorReferenceData with id %s couldn't be found" % srd_id)
        if srd_name is not None:
            srd.name = srd_name
        if srd_value is not None:
            srd.value = srd_value
        if dty_id is not None:
            try:
                self._session.query(DeviceType).filter_by(id=dty_id).one()
            except NoResultFound:
                raise DbHelperException("Couldn't find device type id %s. It does not exist" % dty_id)
            srd.device_type_id = dty_id
        if srd_unit is not None:
            if srd_unit == '': srd_unit = None
            srd.unit = srd_unit
        if srd_stat_key is not None:
            if srd_stat_key == '': srd_stat_key = None
            srd.stat_key = srd_stat_key
        self._session.add(srd)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return srd

    def del_sensor_reference_data(self, srd_id):
        """
        Delete a sensor reference data record
        @param srd_id : id of the sensor reference data to delete
        @return the deleted SensorReferenceData object
        """
        self._session.expire_all()
        srd = self._session.query(SensorReferenceData)\
                           .filter_by(id=srd_id)\
                           .first()
        if srd:
            srd_d = srd
            self._session.delete(srd)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return srd_d
        else:
            raise DbHelperException("Couldn't delete sensor reference \
                                    data with id \
                                    %s : it doesn't exist" % srd_id)

####
# Actuator feature
####
    def list_actuator_features(self):
        """
        Return a list of actuator features
        @return a list of ActuatorFeature objects
        """
        return self._session.query(ActuatorFeature).all()

    def get_actuator_feature_by_name(self, af_name):
        """
        Return information about an actuator feature
        @param af_name : The name of the actuator feature
        @return an ActuatorFeature object
        """
        return self._session.query(ActuatorFeature)\
                            .filter(func.lower(ActuatorFeature.name)==af_name.lower())\
                            .first()

    def add_actuator_feature(self, af_name, af_value, dty_id, af_unit=None,
                             af_configurable_states=None,
                             af_return_confirmation=False):
        """
        Add a sensor reference data
        @param af_name : name (ex. Switch, Dimmer, ...)
        @param af_value : value (binary, number, string, trigger, complex, list, range)
        @param dty_id : id of the device type
        @param af_unit  unit of the value (ex. %), optional
        @param af_configurable_states : configurable states
                                        (0, 10, 100 - on / off, ...), optional
        @param af_return_confirmation : True if the device returns a confirmation
                                     after executing a command, default is false
        @return an ActuatorFeature (the newly created one)
        """
        self._session.expire_all()
        try:
            self._session.query(DeviceType).filter_by(id=dty_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add actuator feature with device type id %s. \
                                    It does not exist" % dty_id)
        af = ActuatorFeature(name=af_name, value=af_value,
                    device_type_id=dty_id, unit=af_unit,
                    configurable_states=af_configurable_states,
                    return_confirmation=af_return_confirmation)
        self._session.add(af)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return af

    def update_actuator_feature(self, af_id, af_name=None, af_value=None,
                                dty_id=None, af_unit=None,
                                af_configurable_states=None,
                                af_return_confirmation=None):
        """
        Update an actuator feature
        @param af_id : id of the actuator feature to update
        @param af_name : name (ex. Switch, Dimmer, ...), optional
        @param af_value : value (binary, number, string, trigger, complex, list, range), optional
        @param dty_id : id of the device type, optional
        @param af_unit  unit of the value (ex. %), optional
        @param af_configurable_states : configurable states (0, 10, 100 - on / off, ...), optional
        @param af_return_confirmation : True if the device returns a confirmation after executing a command, optional
        @return an ActuatorFeature (the updated one)
        """
        self._session.expire_all()
        af = self._session.query(ActuatorFeature).filter_by(id=af_id).first()
        if af is None:
            raise DbHelperException("ActuatorFeature with id %s \
                                    couldn't be found" % af_id)
        if af_name is not None:
            af.name = af_name
        if af_value is not None:
            if af_value == '': af_value = None
            af.value = af_value
        if dty_id is not None:
            try:
                self._session.query(DeviceType).filter_by(id=dty_id).one()
            except NoResultFound:
                raise DbHelperException("Couldn't find device type id %s. It does not exist" % dty_id)
            af.device_type_id = dty_id
        if af_unit is not None:
            if af_unit == '': af_unit = None
            af.unit = af_unit
        if af_configurable_states is not None:
            if af_configurable_states == '': af_configurable_states = None
            af.configurable_states = af_configurable_states
        if af_return_confirmation is not None:
            af.return_confirmation = af_return_confirmation
        self._session.add(af)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return af

    def del_actuator_feature(self, af_id):
        """
        Delete an actuator feature record
        @param srd_id : id of the actuator feature to delete
        @return the deleted ActuatorFeature object
        """
        self._session.expire_all()
        af = self._session.query(ActuatorFeature).filter_by(id=af_id).first()
        if af:
            af_d = af
            self._session.delete(af)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return af_d
        else:
            raise DbHelperException("Couldn't delete actuator feature with id \
                                    %s : it doesn't exist" % af_id)

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
        return self._session.query(DeviceTechnology)\
                            .filter(func.lower(DeviceTechnology.name)==dt_name.lower())\
                            .first()

    def add_device_technology(self, dt_name, dt_description):
        """
        Add a device_technology
        @param dt_name : device technology name, one of 'x10', '1wire', 'PLCBus', 'RFXCom', 'IR'
        @param dt_description : extended description of the technology
        """
        self._session.expire_all()
        self._session.expire_all()
        if dt_name not in DEVICE_TECHNOLOGY_LIST:
            raise ValueError, "dt_name must be one of %s" % DEVICE_TECHNOLOGY_LIST
        dt = DeviceTechnology(name=dt_name, description=dt_description)
        self._session.add(dt)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return dt

    def update_device_technology(self, dt_id, dt_name=None, dt_description=None):
        """
        Update a device technology
        @param dt_id : device technology id to be updated
        @param dt_name : device technology name (optional)
        @param dt_description : device technology detailed description (optional)
        @return a DeviceTechnology object
        """
        self._session.expire_all()
        device_tech = self._session.query(DeviceTechnology)\
                                   .filter_by(id=dt_id)\
                                   .first()
        if device_tech is None:
            raise DbHelperException("DeviceTechnology with id %s couldn't be found" % dt_id)
        if dt_name is not None:
            device_tech.name = dt_name
        if dt_description is not None:
            if dt_description == '': dt_description = None
            device_tech.description = dt_description
        self._session.add(device_tech)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return device_tech

    def del_device_technology(self, dt_id, cascade_delete=False):
        """
        Delete a device technology record
        @param dt_id : id of the device technology to delete
        @return the deleted DeviceTechnology object
        """
        self._session.expire_all()
        dt = self._session.query(DeviceTechnology).filter_by(id=dt_id).first()
        if dt:
            dt_d = dt
            if cascade_delete:
                for device_type in self._session.query(DeviceType)\
                                                .filter_by(technology_id=dt.id).all():
                    self.del_device_type(device_type.id, cascade_delete=True)
            else:
                device_type_list = self._session.query(DeviceType)\
                                                .filter_by(technology_id=dt.id).all()
                if len(device_type_list) > 0:
                    raise DbHelperException("Couldn't delete device technology \
                            %s : there are associated device types" % dt_id)
            dtc_list = self._session.query(DeviceTechnologyConfig)\
                                    .filter_by(technology_id=dt.id).all()
            for dtc in dtc_list:
                self._session.delete(dtc)
                #self.del_device_technology_config(dtc.id)

            self._session.delete(dt)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return dt_d
        else:
            raise DbHelperException("Couldn't delete device technology with id \
                                    %s : it doesn't exist" % dt_id)

####
# Device technology config
####
    def list_device_technology_config(self, dt_id):
        """
        Return all keys and values of a device technology
        @param dt_id : id of the device technology
        @return a list of DeviceTechnologyConfig objects
        """
        return self._session.query(DeviceTechnologyConfig)\
                            .filter_by(technology_id=dt_id).all()

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
        return self._session.query(DeviceTechnologyConfig)\
                            .filter_by(technology_id=dt_id)\
                            .filter_by(key=dtc_key)\
                            .first()

    def add_device_technology_config(self, dt_id, dtc_key, dtc_value,
                                     dtc_description):
        """
        Add a device's technology config item
        @param dt_id : the device technology id
        @param dtc_key : The device technology config key
        @param dtc_value : The device technology config value
        @param dtc_description : The device technology config description
        @return the new DeviceTechnologyConfig item
        """
        self._session.expire_all()
        try:
            self._session.query(DeviceTechnology).filter_by(id=dt_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add device technology config \
                                    with device technology id %s. \
                                    It does not exist" % dt_id)
        if self.get_device_technology_config(dt_id, dtc_key):
            raise DbHelperException("This key '%s' already exists for device \
                                    technology %s" % (dtc_key, dt_id))
        dtc = DeviceTechnologyConfig(technology_id=dt_id, key=dtc_key,
                                     value=dtc_value,
                                     description=dtc_description)
        self._session.add(dtc)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return dtc

    def update_device_technology_config(self, dtc_id, dt_id=None, dtc_key=None,
                                        dtc_value=None, dtc_description=None):
        """
        Update a device technology config
        @param dtc_id : device technology config id to be updated
        @param dt_id : device technology id (optional)
        @param dtc_key : parameter key (optional)
        @param dtc_value : parameter value (optional)
        @param dtc_description : device technology config detailed description (optional)
        @return a DeviceTechnologyConfig object
        """
        self._session.expire_all()
        dtc = self._session.query(DeviceTechnologyConfig).filter_by(id=dtc_id).first()
        if dtc is None:
            raise DbHelperException("DeviceTypeConfig with id %s couldn't be found" % dtc_id)
        if dt_id is not None:
            try:
                self._session.query(DeviceTechnology).filter_by(id=dt_id).one()
            except NoResultFound:
                raise DbHelperException("Couldn't find device technology id %s. It does not exist" % dt_id)
            dtc.technology_id = dt_id
        if dtc_key is not None:
            dtc.key = dtc_key
        if dtc_value is not None:
            dtc.value = dtc_value
        if dtc_description is not None:
            if dtc_description == '': dtc_description = None
            dtc.description = dtc_description
        self._session.add(dtc)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return dtc

    def del_device_technology_config(self, dtc_id):
        """
        Delete a device technology config record
        @param dtc_id : config item id
        @return the deleted DeviceTechnologyConfig object
        """
        self._session.expire_all()
        dtc = self._session.query(DeviceTechnologyConfig)\
                           .filter_by(id=dtc_id).first()
        if dtc:
            dtc_d = dtc
            self._session.delete(dtc)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return dtc_d
        else:
            raise DbHelperException("Couldn't delete device technology config with id %s : it doesn't exist" % dtc_id)

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
        Return a device by its id
        @param d_id : The device id
        @return a Device object
        """
        return self._session.query(Device).filter_by(id=d_id).first()

    def get_device_by_technology_and_address(self, techno_name, device_address):
        """
        Return a device by its technology and address
        @param techno_name : technology name
        @param device address : device address
        @return a device object
        """
        device_list = self._session.query(Device)\
                                   .filter_by(address=device_address)\
                                   .all()
        if len(device_list) == 0:
            return None
        device = []
        for device in device_list:
            device_type = self._session.query(DeviceType)\
                                       .filter_by(id=device.type_id).first()
            device_tech = self._session.query(DeviceTechnology)\
                                       .filter_by(id=device_type.technology_id)\
                                       .first()
            if device_tech.name.lower() == techno_name.lower():
                return device
        return None

    def get_all_devices_of_room(self, d_room_id):
        """
        Return all the devices of a room
        @param d_room_id: room id
        @return a list of Device objects
        """
        return self._session.query(Device)\
                            .filter_by(room_id=d_room_id).all()

    def get_all_devices_of_area(self, d_area_id):
        """
        Return all the devices of an area
        @param d_area_id : the area id
        @return a list of Device objects
        """
        device_list = []
        for room in self._session.query(Room).filter_by(area_id=d_area_id).all():
            for device in self._session.query(Device).filter_by(room_id=room.id).all():
                device_list.append(device)
        return device_list

    def get_all_devices_of_usage(self, du_id):
        """
        Return all the devices of a usage
        @param du_id: usage id
        @return a list of Device objects
        """
        return self._session.query(Device)\
                            .filter_by(usage_id=du_id).all()

    def get_all_devices_of_technology(self, dt_id):
        """
        Returns all the devices of a technology
        @param dt_id : technology id
        @return a list of Device objects
        """
        return self._session.query(Device)\
                            .filter_by(technology_id=dt_id).all()

    def add_device(self, d_name, d_address, d_type_id, d_usage_id, d_room_id,
        d_description=None, d_reference=None):
        """
        Add a device item
        @param d_name : name of the device
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_type_id : type id (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param d_usage_id : usage id
        @param d_room_id : room id
        @param d_description : Extended item description (100 char max)
        @param d_reference : device reference (ex. AM12 for x10)
        @return the new Device object
        """
        self._session.expire_all()
        try:
            self._session.query(DeviceType).filter_by(id=d_type_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add device with device type id %s \
                                    It does not exist" % d_type_id)
        try:
            self._session.query(DeviceUsage).filter_by(id=d_usage_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add device with device usage id %s \
                                    It does not exist" % d_usage_id)
        try:
            self._session.query(Room).filter_by(id=d_room_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add device with room id %s \
                                    It does not exist" % d_room_id)
        device = Device(name=d_name, address=d_address, description=d_description,
                        reference=d_reference, type_id=d_type_id,
                        usage_id=d_usage_id, room_id=d_room_id)
        self._session.add(device)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return device

    def update_device(self, d_id, d_name=None, d_address=None, d_type_id=None,
            d_usage_id=None, d_room_id=None, d_description=None,
            d_reference=None):
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
        @return the updated Device object
        """
        self._session.expire_all()
        device = self._session.query(Device).filter_by(id=d_id).first()
        if device is None:
            raise DbHelperException("Device with id %s couldn't be found" % d_id)
        if d_name is not None:
            device.name = d_name
        if d_address is not None:
            device.address = d_address
        if d_description is not None:
            if d_description == '': d_description = None
            device.description = d_description
        if d_reference is not None:
            if d_reference == '': d_reference = None
            device.reference = d_reference
        if d_type_id is not None:
            try:
                self._session.query(DeviceType).filter_by(id=d_type_id).one()
            except NoResultFound:
                raise DbHelperException("Couldn't find device type id %s. It does not exist" % d_type_id)
            device.type_id = d_type_id
        if d_usage_id is not None:
            try:
              self._session.query(DeviceUsage).filter_by(id=d_usage_id).one()
            except NoResultFound:
              raise DbHelperException("Couldn't find device usage id %s. It does not exist" % d_usage_id)
            device.usage = d_usage_id
        if d_room_id is not None:
            if d_room_id != '':
                try:
                    self._session.query(Room).filter_by(id=d_room_id).one()
                except NoResultFound:
                    raise DbHelperException("Couldn't find room id %s. It does not exist" % d_room_id)
            else:
                d_room_id = None
            device.room = d_room_id
        self._session.add(device)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return device

    def del_device(self, d_id):
        """
        Delete a device
        Warning : this deletes also the associated objects (DeviceConfig, DeviceStats, DeviceStatsValue)
        @param d_id : item id
        @return the deleted Device object
        """
        self._session.expire_all()
        device = self._session.query(Device).filter_by(id=d_id).first()
        if device is None:
            raise DbHelperException("Device with id %s couldn't be found" % d_id)

        device_d = device
        for device_conf in self._session.query(DeviceConfig)\
                                        .filter_by(device_id=d_id).all():
            self._session.delete(device_conf)

        for device_stats in self._session.query(DeviceStats).filter_by(device_id=d_id).all():
            for device_stats_value in self._session.query(DeviceStatsValue)\
                                                   .filter_by(device_stats_id=device_stats.id).all():
                self._session.delete(device_stats_value)
            self._session.delete(device_stats)
        self._session.delete(device)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
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
        return self._session.query(DeviceStats)\
                            .filter_by(device_id=d_device_id).all()

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
        return self._session.query(DeviceStatsValue)\
                            .filter_by(device_stats_id=d_device_stats_id).all()

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
        return self._session.query(DeviceStats)\
                            .filter_by(device_id=d_device_id).count() > 0

    def add_device_stat(self, d_id, ds_date, ds_values):
        """
        Add a device stat record
        @param d_id : device id
        @param ds_date : when the stat was gathered (timestamp)
        @param ds_value : dictionnary of statistics values
        @return the new DeviceStats object
        """
        self._session.expire_all()
        try:
            self._session.query(Device).filter_by(id=d_id).one()
        except NoResultFound:
            raise DbHelperException("Couldn't add device stat with device id %s \
                                    It does not exist" % d_id)
        device_stat = DeviceStats(device_id=d_id, date=ds_date)
        self._session.add(device_stat)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        for ds_name in ds_values.keys():
            dsv = DeviceStatsValue(name=ds_name, value=ds_values[ds_name],
                                   device_stats_id=device_stat.id)
            self._session.add(dsv)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return device_stat

    def del_device_stat(self, ds_id):
        """
        Delete a stat record
        @param ds_id : record id
        @return the deleted DeviceStat object
        """
        self._session.expire_all()
        device_stat = self._session.query(DeviceStats).filter_by(id=ds_id).first()
        if device_stat:
            device_stat_d = device_stat
            self._session.delete(device_stat)
            for device_stats_value in self._session.query(DeviceStatsValue) \
                                          .filter_by(device_stats_id=device_stat.id).all():
                self._session.delete(device_stats_value)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return device_stat_d
        else:
            raise DbHelperException("Couldn't delete device stat with id %s : \
                                    it doesn't exist" % ds_id)

    def del_all_device_stats(self, d_id):
        """
        Delete all stats for a device
        @param d_id : device id
        @return the list of DeviceStatsValue objects that were deleted
        """
        self._session.expire_all()
        #TODO : this could be optimized
        device_stats = self._session.query(DeviceStats).filter_by(device_id=d_id).all()
        device_stats_d_list = []
        for device_stat in device_stats:
            for device_stats_value in self._session.query(DeviceStatsValue) \
                                                   .filter_by(device_stats_id=device_stat.id).all():
                self._session.delete(device_stats_value)
            device_stats_d_list.append(device_stat)
            self._session.delete(device_stat)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
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
        @param t_description : trigger description
        @param t_rule : trigger rule
        @param t_result : trigger result (list of strings)
        @return the new Trigger object
        """
        self._session.expire_all()
        trigger = Trigger(description=t_description, rule=t_rule,
                          result=';'.join(t_result))
        self._session.add(trigger)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return trigger

    def update_trigger(self, t_id, t_description=None, t_rule=None, t_result=None):
        """
        Update a trigger
        @param dt_id : trigger id to be updated
        @param t_description : trigger description
        @param t_rule : trigger rule
        @param t_result : trigger result (list of strings)
        @return a Trigger object
        """
        self._session.expire_all()
        trigger = self._session.query(Trigger).filter_by(id=t_id).first()
        if trigger is None:
            raise DbHelperException("Trigger with id %s couldn't be found" % t_id)
        if t_description is not None:
            if t_description == '': t_description = None
            trigger.description = t_description
        if t_rule is not None:
            trigger.rule = t_rule
        if t_result is not None:
            trigger.result = ';'.join(t_result)
        self._session.add(trigger)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return trigger

    def del_trigger(self, t_id):
        """
        Delete a trigger
        @param t_id : trigger id
        @return the deleted Trigger object
        """
        self._session.expire_all()
        trigger = self._session.query(Trigger).filter_by(id=t_id).first()
        if trigger:
            trigger_d = trigger
            self._session.delete(trigger)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return trigger_d
        else:
            raise DbHelperException("Couldn't delete trigger with id %s : \
                                    it doesn't exist" % t_id)

####
# User accounts
####
    def list_user_accounts(self):
        """
        Returns a list of all accounts
        @return a list of UserAccount objects
        """
        list_sa = self._session.query(UserAccount).all()
        for user_acc in list_sa:
            # I won't send the password, right?
            user_acc.password = None
        return list_sa

    def get_user_account(self, a_id):
        """
        Return user account information from id
        @param a_id : account id
        @return a UserAccount object
        """
        user_acc = self._session.query(UserAccount)\
                                .filter_by(id=a_id).first()
        if user_acc is not None:
            user_acc.password = None
        return user_acc

    def get_user_account_by_login(self, a_login):
        """
        Return user account information from login
        @param a_login : login
        @return a UserAccount object
        """
        user_acc = self._session.query(UserAccount).filter_by(login=a_login)\
                                                   .first()
        if user_acc is not None:
            user_acc.password = None
        return user_acc

    def get_user_account_by_login_and_pass(self, a_login, a_password):
        """
        Return user account information from login
        @param a_login : login
        @param a_pass : password (clear text)
        @return a UserAccount object or None if login / password is wrong
        """
        crypted_pass = self.__make_crypted_password(a_password)
        user_acc = self._session.query(UserAccount)\
                                .filter_by(login=a_login, password=crypted_pass)\
                                .first()
        if user_acc is not None:
            user_acc.password = None
        return user_acc

    def get_user_account_by_person(self, p_id):
        """
        Return a user account associated to a person, if existing
        @param p_id : The person id
        @return a UserAccount object
        """
        person = self._session.query(Person).filter_by(id=p_id).first()
        if person is not None:
            try:
                user_acc = self._session.query(UserAccount)\
                                        .filter_by(id=person.user_account_id)\
                                        .one()
                user_acc.password = None
                return user_acc
            except MultipleResultsFound:
                raise DbHelperException("Database may be incoherent, person with id %s has more than one account" % p_id)
        else:
            return None

    def authenticate(self, a_login, a_password):
        """
        Check if a user account with a_login, a_password exists
        @param a_login : Account login
        @param a_password : Account password (clear)
        @return True or False
        """
        self._session.expire_all()
        user_acc = self._session.query(UserAccount).filter_by(login=a_login)\
                                                   .first()
        if user_acc is not None:
            password = hashlib.sha256()
            password.update(a_password)
            if user_acc.password == password.hexdigest():
                return True
        return False

    def add_user_account(self, a_login, a_password, a_is_admin=False,
                         a_skin_used='skins/default'):
        """
        Add a user account
        @param a_login : Account login
        @param a_password : Account clear text password (will be hashed in sha256)
        @param a_is_admin : True if it is an admin account, False otherwise (optional, default=False)
        @return the new UserAccount object or raise a DbHelperException if it already exists
        """
        self._session.expire_all()
        user_account = self._session.query(UserAccount).filter_by(login=a_login).first()
        if user_account is not None:
            raise DbHelperException("Error %s login already exists" % a_login)
        user_account = UserAccount(login=a_login,
                                   password=self.__make_crypted_password(a_password),
                                   is_admin=a_is_admin, skin_used=a_skin_used)
        self._session.add(user_account)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        user_account.password = None
        return user_account

    def update_user_account(self, a_id, a_new_login=None, a_password=None,
                            a_is_admin=None, a_skin_used=None):
        """
        Update a user account
        @param a_id : Account id to be updated
        @param a_new_login : The new login (optional)
        @param a_password : Account clear text password (will be hashed in sha256, optional)
        @param a_is_admin : True if it is an admin account, False otherwise (optional)
        @return a UserAccount object
        """
        self._session.expire_all()
        user_acc = self._session.query(UserAccount).filter_by(id=a_id).first()
        if user_acc is None:
            raise DbHelperException("UserAccount with id %s couldn't be found" % a_id)
        if a_new_login is not None:
            user_acc.login = a_new_login
        if a_password is not None:
            user_acc.password = self.__make_crypted_password(a_password)
        if a_is_admin is not None:
            user_acc.is_admin = a_is_admin
        if a_skin_used is not None:
            user_acc.skin_used = a_skin_used
        self._session.add(user_acc)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        user_acc.password = None
        return user_acc

    def __make_crypted_password(self, clear_text_password):
        """
        Make a crypted password (using sha256)
        @param clear_text_password : password in clear text
        @return crypted password
        """
        password = hashlib.sha256()
        password.update(clear_text_password)
        return password.hexdigest()

    def add_default_user_account(self):
        """
        Add a default user account (login = admin, password = domogik, is_admin = True)
        @return a UserAccount object
        """
        return self.add_user_account(a_login='admin', a_password='123',
                                     a_is_admin=True)

    def del_user_account(self, a_id):
        """
        Delete a user account
        @param a_id : account id
        @return the deleted UserAccount object
        """
        self._session.expire_all()
        user_account = self._session.query(UserAccount).filter_by(id=a_id).first()
        if user_account:
            user_account_d = user_account
            self._session.delete(user_account)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return user_account_d
        else:
            raise DbHelperException("Couldn't delete user account with id %s : it doesn't exist" % a_id)

####
# Persons
####
    def list_persons(self):
        """
        Returns the list of all persons
        @return a list of Person objects
        """
        return self._session.query(Person).all()

    def get_person(self, p_id):
        """
        Returns person information
        @param p_id : person id
        @return a Person object
        """
        return self._session.query(Person).filter_by(id=p_id).first()

    def get_person_by_user_account(self, u_id):
        """
        Return a person associated to a user account, if existing
        @param u_id : the user account id
        @return a Person object or None
        """
        try:
            return self._session.query(Person)\
                                .filter_by(user_account_id=u_id).one()
        except NoResultFound:
            return None
        except MultipleResultsFound:
            raise DbHelperException("Database may be incoherent, person with \
                                    id %s has more than one account" % u_id)

    def add_person(self, p_first_name, p_last_name, p_birthdate,
                   p_user_account_id=None):
        """
        Add a person
        @param p_first_name     : first name
        @param p_last_name      : last name
        @param p_birthdate      : birthdate
        @param p_user_account   : Person account on the user (optional)
        @return the new Person object
        """
        self._session.expire_all()
        if p_user_account_id is not None:
            try:
                self._session.query(UserAccount)\
                             .filter_by(id=p_user_account_id).one()
            except NoResultFound:
                raise DbHelperException("Couldn't add person with account id %s : it doesn't exist" % p_user_account_id)
        person = Person(first_name=p_first_name, last_name=p_last_name,
                        birthdate=p_birthdate,
                        user_account_id=p_user_account_id)
        self._session.add(person)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return person

    def update_person(self, p_id, p_first_name=None, p_last_name=None,
                      p_birthdate=None, p_user_account_id=None):
        """
        Update a person
        @param p_id             : person id to be updated
        @param p_first_name     : first name (optional)
        @param p_last_name      : last name (optional)
        @param p_birthdate      : birthdate (optional)
        @param p_user_account   : person account on the user (optional)
        @return a Person object
        """
        self._session.expire_all()
        person = self._session.query(Person).filter_by(id=p_id).first()
        if person is None:
            raise DbHelperException("Person with id %s couldn't be found" % p_id)
        if p_first_name is not None:
            person.first_name = p_first_name
        if p_last_name is not None:
            person.last_name = p_last_name
        if p_birthdate is not None:
            person.birthdate = p_birthdate
        if p_user_account_id is not None:
            if p_user_account_id != '':
                try:
                    self._session.query(UserAccount)\
                                 .filter_by(id=p_user_account_id).one()
                except NoResultFound:
                    raise DbHelperException("Couldn't find account id %s It does not exist" % p_user_account_id)
            else:
                p_user_account_id = None
            person.user_account_id = p_user_account_id
        self._session.add(person)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return person

    def del_person(self, p_id):
        """
        Delete a person and the associated user account if it exists
        @param p_id : person account id
        @return the deleted Person object
        """
        self._session.expire_all()
        person = self._session.query(Person).filter_by(id=p_id).first()
        if person is not None:
            if person.user_account_id is not None:
                self.del_user_account(person.user_account_id)
            person_d = person
            self._session.delete(person)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return person_d
        else:
            raise DbHelperException("Couldn't delete person with id %s : it doesn't exist" % p_id)

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
        return self._session.query(SystemStatsValue)\
                            .filter_by(system_stats_id=s_system_stats_id).all()

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
        self._session.expire_all()
        system_stat = SystemStats(module_name=s_name, host_name=s_hostname, date=s_date)
        self._session.add(system_stat)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        for stat_value_name in s_values.keys():
            ssv = SystemStatsValue(name=stat_value_name, value=s_values[stat_value_name],
                                  system_stats_id=system_stat.id)
            self._session.add(ssv)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return system_stat

    def del_system_stat(self, s_name):
        """
        Delete a system stat record
        @param s_name : name of the stat that has to be deleted
        @return the deleted SystemStats object
        """
        self._session.expire_all()
        system_stat = self._session.query(SystemStats).filter_by(name=s_name).first()
        if system_stat:
            system_stat_d = system_stat
            system_stats_values = self._session.query(SystemStatsValue)\
                                               .filter_by(system_stats_id=system_stat.id).all()
            for ssv in system_stats_values:
                self._session.delete(ssv)
            self._session.delete(system_stat)
            try:
                self._session.commit()
            except Exception, sql_exception:
                self._session.rollback()
                raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
            return system_stat_d
        else:
            raise DbHelperException("Couldn't delete system stat %s : it doesn't exist" % s_name)

    def del_all_system_stats(self):
        """
        Delete all stats of the system
        @return the list of deleted SystemStats objects
        """
        self._session.expire_all()
        system_stats_list = self._session.query(SystemStats).all()
        system_stats_d_list = []
        for system_stat in system_stats_list:
            system_stats_values = self._session.query(SystemStatsValue)\
                                      .filter_by(system_stats_id=system_stat.id).all()
            for ssv in system_stats_values:
                self._session.delete(ssv)
            system_stats_d_list.append(system_stat)
            self._session.delete(system_stat)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return system_stats_d_list


###
# UIItemConfig
###

    def set_ui_item_config(self, ui_item_name, ui_item_reference, ui_key,
                           ui_value):
        """
        Add / update an UI parameter
        @param ui_item_name : item name
        @param ui_item_reference : the item reference
        @param ui_key : key we want to add / update
        @param ui_value : key value we want to add / update
        @return : the updated UIItemConfig item
        """
        self._session.expire_all()
        ui_item_config = self.get_ui_item_config(ui_item_name, ui_item_reference, ui_key)
        if ui_item_config is None:
            ui_item_config = UIItemConfig(item_name=ui_item_name,
                                          item_reference=ui_item_reference,
                                          key=ui_key, value=ui_value)
        else:
            ui_item_config.value = ui_value
        self._session.add(ui_item_config)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return ui_item_config

    def get_ui_item_config(self, ui_item_name, ui_item_reference, ui_key):
        """
        Get a UI parameter of an item
        @param ui_item_name : item name
        @param ui_item_reference : item reference
        @param ui_key : key
        @return an UIItemConfig object
        """
        return self._session.query(UIItemConfig)\
                            .filter_by(item_name=ui_item_name,
                                       item_reference=ui_item_reference,
                                       key=ui_key)\
                            .first()

    def list_ui_item_config_by_ref(self, ui_item_name, ui_item_reference):
        """
        List all UI parameters of an item
        @param ui_item_name : item name
        @param ui_item_reference : item reference
        @return a list of UIItemConfig objects
        """
        return self._session.query(UIItemConfig)\
                            .filter_by(item_name=ui_item_name,
                                       item_reference=ui_item_reference)\
                            .all()

    def list_ui_item_config_by_key(self, ui_item_name, ui_key):
        """
        List all UI parameters of an item
        @param ui_item_name : item name
        @param ui_key : item key
        @return a list of UIItemConfig objects
        """
        return self._session.query(UIItemConfig)\
                            .filter_by(item_name=ui_item_name, key=ui_key)\
                            .all()

    def list_ui_item_config(self, ui_item_name):
        """
        List all UI parameters of an item
        @param ui_item_name : item name
        @return a list of UIItemConfig objects
        """
        return self._session.query(UIItemConfig)\
                            .filter_by(item_name=ui_item_name)\
                            .all()

    def list_all_ui_item_config(self):
        """
        List all UI parameters
        @return a list of UIItemConfig objects
        """
        return self._session.query(UIItemConfig).all()

    def delete_ui_item_config(self, ui_item_name, ui_item_reference=None, ui_key=None):
        """
        Delete a UI parameter of an item
        @param ui_item_name : item name
        @param ui_item_reference : item reference, optional
        @param ui_key : key of the item, optional
        @return the deleted UIItemConfig object(s)
        """
        self._session.expire_all()
        ui_item_config_list = []
        if ui_item_reference == None and ui_key == None:
            ui_item_config_list = self._session.query(UIItemConfig)\
                                               .filter_by(item_name=ui_item_name).all()
        elif ui_key is None:
            ui_item_config_list = self._session.query(UIItemConfig)\
                                               .filter_by(item_name=ui_item_name,
                                                          item_reference=ui_item_reference)\
                                               .all()
        elif ui_item_reference is None:
            ui_item_config_list = self._session.query(UIItemConfig)\
                                               .filter_by(item_name=ui_item_name,
                                                          key=ui_key)\
                                               .all()
        else:
            ui_item_config = self.get_ui_item_config(ui_item_name, ui_item_reference, ui_key)
            if ui_item_config is not None:
                ui_item_config_list.append(ui_item_config)

        if len(ui_item_config_list) == 0:
            raise DbHelperException("Can't find item for (%s, %s, %s)" % (ui_item_name, ui_item_reference, ui_key))
        ui_item_config_list_d = ui_item_config_list
        for item in ui_item_config_list:
            self._session.delete(item)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return ui_item_config_list_d

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
        except MultipleResultsFound:
            raise DbHelperException("Error : SystemConfig has more than one line")
        except NoResultFound:
            pass

    def update_system_config(self, s_simulation_mode=None, s_debug_mode=None):
        """
        Update (or create) system configuration
        @param s_simulation_mode : True if the system is running in simulation mode (optional)
        @param s_debug_mode : True if the system is running in debug mode (optional)
        @return a SystemConfig object
        """
        self._session.expire_all()
        system_config = self._session.query(SystemConfig).first()
        if system_config is not None:
            if s_simulation_mode is not None:
                system_config.simulation_mode = s_simulation_mode
            if s_debug_mode is not None:
                system_config.debug_mode = s_debug_mode
        else:
            system_config = SystemConfig(simulation_mode=s_simulation_mode,
                                         debug_mode=s_debug_mode)
        self._session.add(system_config)
        try:
            self._session.commit()
        except Exception, sql_exception:
            self._session.rollback()
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return system_config

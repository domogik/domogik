

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

import calendar, datetime, hashlib, time
from types import DictType

import sqlalchemy
from sqlalchemy.sql.expression import func, extract, alias
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from domogik.common.utils import ucode
from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.common.sql_schema import (
        ACTUATOR_VALUE_TYPE_LIST, Area, Device, DeviceFeature, DeviceFeatureModel,
        DeviceUsage, DeviceFeatureAssociation, DeviceConfig, DeviceStats,
        DeviceTechnology, PluginConfig, DeviceType, UIItemConfig, Room, Person,
        UserAccount, SENSOR_VALUE_TYPE_LIST, SystemConfig, Trigger
)


def _make_crypted_password(clear_text_password):
    """Make a crypted password (using sha256)

    @param clear_text_password : password in clear text
    @return crypted password

    """
    password = hashlib.sha256()
    password.update(clear_text_password)
    return password.hexdigest()

def _datetime_to_string(dt, db_used):
    """Convert a date to a string according to the DB used"""
    date = str(dt)
    if db_used == 'sqlite':
        # This is a hack to perform exact date comparisons
        # sqlAlchemy 0.6.1 doc : "In the case of SQLite, date and time types are stored as strings which are then
        # converted back to datetime objects when rows are returned."
        # With sqllite, DATETIME data is stored in this format : 2010-06-23 15:15:00.000000 (mysql:2010-06-23 15:15:00)
        # If you don't add this string performing 'date <= 2010-06-23 15:15:00' will exlude 2010-06-23 15:15:00.000000
        # values as they are considered as bigger
        date += ".000000"
    return date

def _datetime_string_from_tstamp(ts, db_used):
    """Make a date from a timestamp according to the DB used"""
    return _datetime_to_string(datetime.datetime.fromtimestamp(ts), db_used)

def _get_week_nb(dt):
    """Return the week number of a datetime expression"""
    #return (dt - datetime.datetime(dt.year, 1, 1)).days / 7
    return dt.isocalendar()[1]

class DbHelperException(Exception):
    """This class provides exceptions related to the DbHelper class

    """

    def __init__(self, value):
        """Class constructor

        @param value : value of the exception

        """
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        """Return the object representation

        @return value of the exception

        """
        return repr(self.value)


class DbHelper():
    """This class provides methods to fetch and put informations on the Domogik database

    The user should only use methods from this class and don't access the database directly

    """
    __engine = None
    __session = None

    def __init__(self, echo_output=False, use_test_db=False, engine=None, custom_path = None):
        """Class constructor

        @param echo_output : if True displays sqlAlchemy queries (optional, default False)
        @param use_test_db : if True use a test database (optional, default False)
        @param engine : an existing engine, if not provided, a new one will be created
        @param custom_path : full path to domogik config file
        """
        l = logger.Logger('db_api')
        self.log = l.get_logger()
        cfg = Loader('database')
        if custom_path == None:
            config = cfg.load()
        else:
            config = cfg.load(custom_path = custom_path)
        self.__db_config = dict(config[1])

        url = self.get_url_connection_string()
        if use_test_db:
            url = '%s_test' % url
        # Connecting to the database
        if engine != None:
            self.__engine = engine
        else:
            self.__engine = sqlalchemy.create_engine(url, echo = echo_output)
        Session = sessionmaker(bind=self.__engine, autoflush=True)
        self.__session = Session()

    def get_engine(self):
        """Return the existing engine or None if not set
        @return self.__engine

        """
        return self.__engine

    def __del__(self):
        self.__session.close()
        self.__engine.dispose()

    def __rollback(self):
        """Issue a rollback to a SQL transaction (for dev purposes only)

        """
        self.__session.rollback()

    def get_url_connection_string(self):
        """Get url connection string to the database reading the configuration file"""
        url = "%s://" % self.__db_config['db_type']
        if self.__db_config['db_type'] == 'sqlite':
            url = "%s/%s" % (url, self.__db_config['db_path'])
        else:
            if self.__db_config['db_port'] != '':
                url = "%s%s:%s@%s:%s/%s" % (url, self.__db_config['db_user'], self.__db_config['db_password'],
                                            self.__db_config['db_host'], self.__db_config['db_port'], self.__db_config['db_name'])
            else:
                url = "%s%s:%s@%s/%s" % (url, self.__db_config['db_user'], self.__db_config['db_password'],
                                         self.__db_config['db_host'], self.__db_config['db_name'])
        return url

    def get_db_type(self):
        """Return DB type which is currently used (sqlite, mysql, postgresql)"""
        return self.__db_config['db_type'].lower()

####
# Areas
####
    def list_areas(self):
        """Return all areas

        @return a list of Area objects

        """
        return self.__session.query(Area).all()

    def search_areas(self, filters):
        """Look for area(s) with filter on their attributes

        @param filters :  filter fields can be one of
        @return a list of Area objects

        """
        if type(filters) is not DictType:
            self.__raise_dbhelper_exception("Wrong type of 'filters', Should be a dictionnary")
        area_list = self.__session.query(Area)
        for f in filters:
            filter_arg = "%s = '%s'" % (f, ucode(filters[f]))
            area_list = area_list.filter(filter_arg)
        return area_list.all()

    def get_area_by_id(self, area_id):
        """Fetch area information

        @param area_id : The area id
        @return an area object

        """
        return self.__session.query(Area).filter_by(id=area_id).first()


    def get_area_by_name(self, area_name):
        """Fetch area information

        @param area_name : The area name
        @return an area object

        """
        return self.__session.query(Area).filter(func.lower(Area.name)==ucode(area_name.lower())).first()

    def add_area(self, a_name, a_description=None):
        """Add an area

        @param a_name : area name
        @param a_description : area detailed description (optional)
        @return an Area object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        area = Area(name=a_name, description=a_description)
        self.__session.add(area)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return area

    def update_area(self, a_id, a_name=None, a_description=None):
        """Update an area

        @param a_id : area id to be updated
        @param a_name : area name (optional)
        @param a_description : area detailed description (optional)
        @return an Area object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        area = self.__session.query(Area).filter_by(id=a_id).first()
        if area is None:
            self.__raise_dbhelper_exception("Area with id %s couldn't be found" % a_id)
        if a_name is not None:
            area.name = ucode(a_name)
        if a_description is not None:
            if a_description == '': a_description = None
            area.description = ucode(a_description)
        self.__session.add(area)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return area

    def del_area(self, area_del_id, cascade_delete=False):
        """Delete an area record

        @param area_id : id of the area to delete
        @param cascade_delete : True if we wish to delete associated items
        @return the deleted Area object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        area = self.__session.query(Area).filter_by(id=area_del_id).first()
        if area:
            for room in self.__session.query(Room).filter_by(area_id=area_del_id).all():
                if cascade_delete:
                    self.del_room(room.id)
                else:
                    # Just unlink the room from the area
                    room.area_id = None
                    self.__session.add(room)
            dfa_list = self.__session.query(
                                DeviceFeatureAssociation
                            ).filter_by(place_id=area.id, place_type=u'area'
                            ).all()
            for dfa in dfa_list:
                self.__session.delete(dfa)
            self.__session.delete(area)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return area
        else:
            self.__raise_dbhelper_exception("Couldn't delete area with id %s : it doesn't exist" % area_del_id)

####
# Rooms
####
    def list_rooms(self):
        """Return a list of rooms

        @return list of Room objects

        """
        return self.__session.query(Room).all()

    def search_rooms(self, filters):
        """Look for room(s) with filter on their attributes

        @param filters :  filter fields (dictionnary)
        @return a list of Room objects

        """
        if type(filters) is not DictType:
            self.__raise_dbhelper_exception("Wrong type of 'filters', Should be a dictionnary")
        room_list = self.__session.query(Room)
        for f in filters:
            filter_arg = "%s = '%s'" % (f, ucode(filters[f]))
            room_list = room_list.filter(filter_arg)
        return room_list.all()

    def get_room_by_name(self, r_name):
        """Return information about a room

        @param r_name : The room name
        @return a room object

        """
        return self.__session.query(Room).filter(func.lower(Room.name)==ucode(r_name.lower())).first()

    def get_room_by_id(self, r_id):
        """Return information about a room

        @param r_id : The room id
        @return a room object

        """
        return self.__session.query(Room).filter_by(id=r_id).first()

    def add_room(self, r_name, r_area_id=None, r_description=None):
        """Add a room

        @param r_name : room name
        @param area_id : id of the area where the room is, optional
        @param r_description : room detailed description, optional
        @return : a room object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if r_area_id != None:
            if not self.__session.query(Area).filter_by(id=r_area_id).first():
                self.__raise_dbhelper_exception("Couldn't add room with area id %s. It does not exist" % r_area_id)
        room = Room(r_name, description=r_description, area_id=r_area_id)
        self.__session.add(room)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return room

    def update_room(self, r_id, r_name=None, r_area_id=None, r_description=None):
        """Update a room

        @param r_id : room id to be updated
        @param r_name : room name (optional)
        @param r_description : room detailed description (optional)
        @param r_area_id : id of the area the room belongs to (optional)
        @return a Room object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        room = self.__session.query(Room).filter_by(id=r_id).first()
        if room is None:
            self.__raise_dbhelper_exception("Room with id %s couldn't be found" % r_id)
        if r_name is not None:
            room.name = ucode(r_name)
        if r_description is not None:
            if r_description == '': r_description = None
            room.description = ucode(r_description)
        if r_area_id is not None:
            if r_area_id != '':
                if not self.__session.query(Area).filter_by(id=r_area_id).first():
                    self.__raise_dbhelper_exception("Couldn't find area id %s. It does not exist" % r_area_id)
            else:
                r_area_id = None
            room.area_id = r_area_id
        self.__session.add(room)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return room

    def del_room(self, r_id):
        """ Delete a room with a given id

        @param r_id : room id
        @return the deleted room object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        room = self.__session.query(Room).filter_by(id=r_id).first()
        if room:
            dfa_list = self.__session.query(
                                DeviceFeatureAssociation
                            ).filter_by(place_id=room.id, place_type=u'room'
                            ).all()
            for dfa in dfa_list:
                self.__session.delete(dfa)
            self.__session.delete(room)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return room
        else:
            self.__raise_dbhelper_exception("Couldn't delete room with id %s : it doesn't exist" % r_id)

    def get_all_rooms_of_area(self, a_area_id):
        """Return all the rooms of an area

        @param a_area_id : the area id
        @return a list of Room objects

        """
        return self.__session.query(Room).filter_by(area_id=a_area_id).all()

####
# Device usage
####
    def list_device_usages(self):
        """Return a list of device usages

        @return a list of DeviceUsage objects

        """
        return self.__session.query(DeviceUsage).all()

    def get_device_usage_by_name(self, du_name,):
        """Return information about a device usage

        @param du_name : The device usage name
        @return a DeviceUsage object

        """
        return self.__session.query(
                            DeviceUsage
                    ).filter(func.lower(DeviceUsage.name)==ucode(du_name.lower())
                    ).first()

    def add_device_usage(self, du_id, du_name, du_description=None, du_default_options=None):
        """Add a device_usage (temperature, heating, lighting, music, ...)

        @param du_id : device id
        @param du_name : device usage name
        @param du_description : device usage description (optional)
        @param du_default_options : default options (optional)
        @return a DeviceUsage (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        du = DeviceUsage(id=ucode(du_id), name=ucode(du_name), description=du_description,
                         default_options=du_default_options)
        self.__session.add(du)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return du

    def update_device_usage(self, du_id, du_name=None, du_description=None, du_default_options=None):
        """Update a device usage

        @param du_id : device usage id to be updated
        @param du_name : device usage name (optional)
        @param du_description : device usage detailed description (optional)
        @param du_default_options : default options (optional)
        @return a DeviceUsage object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_usage = self.__session.query(DeviceUsage).filter_by(id=du_id).first()
        if device_usage is None:
            self.__raise_dbhelper_exception("DeviceUsage with id %s couldn't be found" % du_id)
        if du_id is not None:
            device_usage.id = ucode(du_id)
        if du_name is not None:
            device_usage.name = ucode(du_name)
        if du_description is not None:
            if du_description == '': du_description = None
            device_usage.description = ucode(du_description)
        if du_default_options is not None:
            if du_default_options == '': du_default_options = None
            device_usage.default_options = ucode(du_default_options)
        self.__session.add(device_usage)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_usage

    def del_device_usage(self, du_id, cascade_delete=False):
        """Delete a device usage record

        @param dc_id : id of the device usage to delete
        @return the deleted DeviceUsage object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        du = self.__session.query(DeviceUsage).filter_by(id=ucode(du_id)).first()
        if du:
            if cascade_delete:
                for device in self.__session.query(Device).filter_by(device_usage_id=ucode(du.id)).all():
                    self.del_device(device.id)
            else:
                device_list = self.__session.query(Device).filter_by(device_usage_id=ucode(du.id)).all()
                if len(device_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device usage %s : there are associated devices" % du_id)

            self.__session.delete(du)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return du
        else:
            self.__raise_dbhelper_exception("Couldn't delete device usage with id %s : it doesn't exist" % du_id)

####
# Device type
####
    def list_device_types(self):
        """Return a list of device types

        @return a list of DeviceType objects

        """
        return self.__session.query(DeviceType).all()

    def get_device_type_by_name(self, dty_name):
        """Return information about a device type

        @param dty_name : The device type name
        @return a DeviceType object

        """
        return self.__session.query(
                        DeviceType
                    ).filter(func.lower(DeviceType.name)==ucode(dty_name.lower())
                    ).first()
    
    def get_device_type_by_id(self, dty_id):
        """Return information about a device type

        @param dty_id : The device type id
        @return a DeviceType object

        """
        return self.__session.query(
                        DeviceType
                    ).filter(func.lower(DeviceType.id)==ucode(dty_id)
                    ).first()

    def add_device_type(self, dty_id, dty_name, dt_id, dty_description=None):
        """Add a device_type (Switch, Dimmer, WOL...)

        @param dty_id : device type id
        @param dty_name : device type name
        @param dt_id : technology id (x10, plcbus,...)
        @param dty_description : device type description (optional)
        @return a DeviceType (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if not self.__session.query(DeviceTechnology).filter_by(id=dt_id).first():
            self.__raise_dbhelper_exception("Couldn't add device type with technology id %s. It does not exist" % dt_id)
        dty = DeviceType(id=ucode(dty_id), name=ucode(dty_name), description=ucode(dty_description),
                         device_technology_id=dt_id)
        self.__session.add(dty)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return dty

    def update_device_type(self, dty_id, dty_name=None, dt_id=None, dty_description=None):
        """Update a device type

        @param dty_id : device type id to be updated
        @param dty_name : device type name (optional)
        @param dt_id : id of the associated technology (optional)
        @param dty_description : device type detailed description (optional)
        @return a DeviceType object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_type = self.__session.query(DeviceType).filter_by(id=dty_id).first()
        if device_type is None:
            self.__raise_dbhelper_exception("DeviceType with id %s couldn't be found" % dty_id)
        if dty_id is not None:
            device_type.id = ucode(dty_id)
        if dty_name is not None:
            device_type.name = ucode(dty_name)
        if dt_id is not None:
            if not self.__session.query(DeviceTechnology).filter_by(id=dt_id).first():
                self.__raise_dbhelper_exception("Couldn't find technology id %s. It does not exist" % dt_id)
            device_type.device_technology_id = dt_id
        self.__session.add(device_type)
        if dty_description is not None:
            if dty_description == '': dty_description = None
            device_type.description = ucode(dty_description)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception)
        return device_type

    def del_device_type(self, dty_id, cascade_delete=False):
        """Delete a device type

        @param dty_id : device type id
        @param cascade_delete : if set to True records of binded tables will be deleted (default is False)
        @return the deleted DeviceType object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dty = self.__session.query(DeviceType).filter_by(id=ucode(dty_id)).first()
        if dty:
            if cascade_delete:
                for device in self.__session.query(Device).filter_by(device_type_id=ucode(dty.id)).all():
                    self.del_device(device.id)
                for df in self.__session.query(DeviceFeatureModel).filter_by(device_type_id=ucode(dty.id)).all():
                    if df.feature_type == 'actuator':
                        self.del_actuator_feature_model(df.id)
                    elif df.feature_type == 'sensor':
                        self.del_sensor_feature_model(df.id)
            else:
                device_list = self.__session.query(Device).filter_by(device_type_id=ucode(dty.id)).all()
                if len(device_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device type %s : there are associated device(s)" % dty_id)
                df_list = self.__session.query(DeviceFeatureModel).filter_by(device_type_id=ucode(dty.id)).all()
                if len(df_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device type %s : there are associated device type "
                                               + "feature(s)" % dty_id)
            self.__session.delete(dty)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return dty
        else:
            self.__raise_dbhelper_exception("Couldn't delete device type with id %s : it doesn't exist" % dty_id)

####
# Device features
####
    def get_device_feature(self, df_device_id, df_device_feature_model_id):
        """Return a device feature

        @param df_device_id : device id
        @param df_device_feature_model_id : id of the device feature model
        @return a DeviceFeature object

        """
        return self.__session.query(
                        DeviceFeature
                    ).filter_by(device_id=df_device_id, device_feature_model_id=df_device_feature_model_id
                    ).first()

    def get_device_feature_by_id(self, df_id):
        """Return a device feature

        @param df_id : device feature id
        @return a DeviceFeature object

        """
        return self.__session.query(DeviceFeature).filter_by(id=df_id).first()

    def list_device_features_by_device_id(self, df_device_id):
        """List device features for a device

        @param df_device_id : device id
        @return a list of DeviceFeature objects

        """
        return self.__session.query(DeviceFeature).filter_by(device_id=df_device_id).all()

####
# Device feature models
####
    def list_device_feature_models(self):
        """Return a list of models for device type feature

        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(DeviceFeatureModel).all()

    def list_device_feature_models_by_device_type_id(self, dtf_device_type_id):
        """Return a list of models for device type features (actuator, sensor) knowing the device type id

        @param dtf_device_type_id : device type id
        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(device_type_id=dtf_device_type_id
                    ).all()

    def get_device_feature_model_by_id(self, dtf_id):
        """Return information about a model for a device type feature

        @param dtf_id : model id
        @return a DeviceFeatureModel object

        """
        return self.__session.query(DeviceFeatureModel).filter_by(id=dtf_id).first()

####
# Actuator feature model
####
    def list_actuator_feature_models(self):
        """Return a list of models for actuator features

        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(feature_type=u'actuator'
                    ).all()

    def get_actuator_feature_model_by_id(self, af_id):
        """Return information about a model for an actuator feature

        @param af_id : actuator feature model id
        @return an DeviceFeatureModel object

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(af_id)
                    ).filter_by(feature_type=u'actuator'
                    ).first()

    def add_actuator_feature_model(self, af_id, af_name, af_device_type_id, af_value_type, af_return_confirmation=False,
                                   af_parameters=None, af_stat_key=None):
        """Add a model for an actuator feature

        @param af_id : actuator id
        @param af_name : actuator name
        @param af_device_type_id : device type id
        @param af_value_type : value type the actuator can accept
        @param af_return_confirmation : True if the actuator returns a confirmation after having executed a command, optional (default False)
        @param af_parameters : parameters about the command or the returned data associated to the device, optional
        @param af_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if af_value_type not in ACTUATOR_VALUE_TYPE_LIST:
            self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                       % (af_value_type, ACTUATOR_VALUE_TYPE_LIST))
        if self.__session.query(DeviceType).filter_by(id=af_device_type_id).first() is None:
            self.__raise_dbhelper_exception("Can't add actuator feature : device type id '%s' doesn't exist"
                                       % af_device_type_id)
        device_feature_m = DeviceFeatureModel(id=ucode(af_id), name=ucode(af_name), feature_type=u'actuator',
                                              device_type_id=af_device_type_id, value_type=af_value_type,
                                              return_confirmation=af_return_confirmation,
                                              parameters=af_parameters, stat_key=af_stat_key)
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def update_actuator_feature_model(self, af_id, af_name=None, af_parameters=None, af_value_type=None,
                                      af_return_confirmation=None, af_stat_key=None):
        """Update a model for an actuator feature

        @param af_id : actuator feature model id
        @param af_name : actuator feature name (Switch, Dimmer, ...), optional
        @param af_parameters : parameters about the command or the returned data associated to the device, optional
        @param af_value_type : value type the actuator can accept, optional
        @param af_return_confirmation : True if the actuator returns a confirmation after having executed a command, optional
        @param af_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly updated one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_feature_m = self.__session.query(
                                    DeviceFeatureModel
                                ).filter_by(id=ucode(af_id)
                                ).filter_by(feature_type=u'actuator'
                                ).first()
        if device_feature_m is None:
            self.__raise_dbhelper_exception("DeviceFeatureModel with id %s (actuator) couldn't be found - can't update it"
                                       % af_id)
        if af_id is not None:
            device_feature_m.id = ucode(af_id)
        if af_name is not None:
            device_feature_m.name = ucode(af_name)
        if af_parameters is not None:
            if af_parameters == '':
                af_parameters = None
            device_feature_m.parameters = ucode(af_parameters)
        if af_value_type is not None:
            if af_value_type not in ACTUATOR_VALUE_TYPE_LIST:
                self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                           % (af_value_type, ACTUATOR_VALUE_TYPE_LIST))
            device_feature_m.value_type = ucode(af_value_type)
        if af_return_confirmation is not None:
            device_feature_m.return_confirmation = af_return_confirmation
        if af_stat_key is not None:
            device_feature_m.stat_key = ucode(af_stat_key)
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def del_actuator_feature_model(self, afm_id):
        """Delete a model for an actuator feature

        @param afm_id : actuator feature model id
        @return : the deleted object (DeviceFeatureModel)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dfm = self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(afm_id)
                    ).filter_by(feature_type=u'actuator'
                    ).first()
        if not dfm:
            self.__raise_dbhelper_exception("Can't delete device feature model %s (actuator) : it doesn't exist" % afm_id)
        self.__session.delete(dfm)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dfm

####
# Sensor feature model
####
    def list_sensor_feature_models(self):
        """Return a list of models for sensor features

        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(feature_type=u'sensor'
                    ).all()

    def get_sensor_feature_model_by_id(self, sf_id):
        """Return information about a model for a sensor feature

        @param sf_id : sensor feature model id
        @return a DeviceFeatureModel object

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(sf_id)
                    ).filter_by(feature_type=u'sensor'
                    ).first()

    def add_sensor_feature_model(self, sf_id, sf_name, sf_device_type_id, sf_value_type, sf_parameters=None,
                                 sf_stat_key=None):
        """Add a model for sensor feature

        @param sf_id : sensor feature id
        @param sf_name : sensor feature name (Thermometer, Voltmeter...)
        @param sf_device_type_id : device type id
        @param sf_value_type : value type the sensor can return
        @param sf_parameters : parameters about the command or the returned data associated to the device, optional
        @param sf_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if sf_value_type not in SENSOR_VALUE_TYPE_LIST:
            self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                       % (sf_value_type, SENSOR_VALUE_TYPE_LIST))
        if self.__session.query(DeviceType).filter_by(id=ucode(sf_device_type_id)).first() is None:
            self.__raise_dbhelper_exception("Can't add sensor : device type id '%s' doesn't exist" % sf_device_type_id)
        device_feature_m = DeviceFeatureModel(id=ucode(sf_id), name=ucode(sf_name), feature_type=u'sensor',
                                              device_type_id=sf_device_type_id, value_type=ucode(sf_value_type),
                                              parameters=ucode(sf_parameters), stat_key=ucode(sf_stat_key))
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def update_sensor_feature_model(self, sf_id, sf_name=None, sf_parameters=None, sf_value_type=None,
                                    sf_stat_key=None):
        """Update a model for a sensor feature

        @param sf_id : sensor feature model id
        @param sf_name : sensor feature name (Thermometer, Voltmeter...), optional
        @param sf_parameters : parameters about the command or the returned data associated to the device, optional
        @param sf_value_type : value type the sensor can return, optional
        @param sf_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly updated one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_feature_m = self.__session.query(
                                    DeviceFeatureModel
                                ).filter_by(id=ucode(sf_id)
                                ).filter_by(feature_type=u'sensor'
                                ).first()
        if device_feature_m is None:
            self.__raise_dbhelper_exception("DeviceFeatureModel with id %s couldn't be found - can't update it" % sf_id)
        if sf_id is not None:
            device_feature_m.id = ucode(sf_id)
        if sf_name is not None:
            device_feature_m.name = ucode(sf_name)
        if sf_parameters is not None:
            if sf_parameters == '':
                sf_parameters = None
            device_feature_m.parameters = ucode(sf_parameters)
        if sf_value_type is not None:
            if sf_value_type not in SENSOR_VALUE_TYPE_LIST:
                self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                           % (sf_value_type, SENSOR_VALUE_TYPE_LIST))
            device_feature_m.value_type = ucode(sf_value_type)
        if sf_stat_key is not None:
            device_feature_m.stat_key = ucode(sf_stat_key)
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def del_sensor_feature_model(self, sfm_id):
        """Delete a model for a sensor feature

        @param sfm_id : sensor feature model id
        @return : the deleted object (DeviceFeatureModel)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dfm = self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(sfm_id)
                    ).filter_by(feature_type=u'sensor'
                    ).first()
        if not dfm:
            self.__raise_dbhelper_exception("Can't delete device feature model %s (actuator) : it doesn't exist" % sfm_id)
        self.__session.delete(dfm)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dfm

####
# Device Feature
####
    def list_device_features(self):
        """List all device features"""
        return self.__session.query(DeviceFeature).all()

    def list_device_feature_by_device_id(self, df_device_id):
        """List device features for a given device id

        @param df_device_id : device id
        @return a list of DeviceFeature objects

        """
        return self.__session.query(DeviceFeature).filter_by(device_id=df_device_id).all()

    def list_device_feature_by_device_feature_model_id(self, df_device_feature_model_id):
        """List device features for a given device id

        @param df_device_feature_model_id : device feature model id
        @return a list of DeviceFeature objects

        """
        return self.__session.query(
                        DeviceFeature
                    ).filter_by(device_feature_model_id=df_device_feature_model_id
                    ).all()

####
# Device feature association
####
    def list_device_feature_associations(self):
        """List all records for the device / feature association

        @return a list of DeviceFeatureAssociation objects

        """
        return self.__session.query(DeviceFeatureAssociation).all()

    def list_device_feature_associations_by_house(self):
        """List device / feature association for the house

        @return a list of DeviceFeatureAssociation objects

        """
        return self.__session.query(
                        DeviceFeatureAssociation
                    ).filter_by(place_type=u'house'
                    ).all()

    def list_deep_device_feature_associations_by_house(self):
        """List device / feature association for the house : house, areas and non-affected rooms

        @return a list of DeviceFeatureAssociation objects

        """
        # Get all non-affected rooms which are part of a device feature association
        dfa_list = self.__session.query(
                    DeviceFeatureAssociation
                  ).filter(Room.id == DeviceFeatureAssociation.place_id
                  ).filter(DeviceFeatureAssociation.place_type == u'room'
                  ).filter(Room.area_id == None
                  ).all()
        # Get all areas which are part of a device feature association
        dfa_list.extend(self.__session.query(
                            DeviceFeatureAssociation
                        ).filter_by(place_type=u'area'
                        ).all())
        dfa_list.extend(self.list_device_feature_associations_by_house())
        return dfa_list

    def list_device_feature_associations_by_room_id(self, room_id):
        """List device / feature association for a room

        @param room_id : room id
        @return a list of DeviceFeatureAssociation objects

        """
        return self.__session.query(
                        DeviceFeatureAssociation
                    ).filter_by(place_id=room_id, place_type=u'room'
                    ).all()

    def list_device_feature_associations_by_area_id(self, area_id):
        """List device / feature association for an area

        @param area_id : area id
        @return a list of DeviceFeatureAssociation objects

        """
        return self.__session.query(
                        DeviceFeatureAssociation
                    ).filter_by(place_id=area_id, place_type=u'area'
                    ).all()

    def list_deep_device_feature_associations_by_area_id(self, area_id):
        """List device / feature association for an area and its associated rooms

        @param area_id : area id
        @return a list of DeviceFeatureAssociation objects

        """
        dfa_list = self.list_device_feature_associations_by_area_id(area_id)
        room_list = self.__session.query(Room).filter_by(area_id=area_id).all()
        for room in room_list:
            dfa_list.extend(self.list_device_feature_associations_by_room_id(room.id))
        return dfa_list

    def list_device_feature_associations_by_feature_id(self, dfa_device_feature_id):
        """List device / feature association for a device feature id

        @param dfa_device_feature_id : device feature id
        @return a list of DeviceFeatureAssociation objects

        """
        return self.__session.query(
                        DeviceFeatureAssociation
                    ).filter_by(device_feature_id=dfa_device_feature_id
                    ).all()

    def get_device_feature_association_by_id(self, dfa_id):
        """Get a device feature association

        @param dfa_id : device feature association id
        @return a DeviceFeatureAssociation object

        """
        return self.__session.query(
                        DeviceFeatureAssociation
                    ).filter_by(id=dfa_id
                    ).first()

    def add_device_feature_association(self, d_feature_id, d_place_type=None, d_place_id=None):
        """Add a device feature association

        @param d_feature_id : device feature id
        @param d_place_id : room id, area id or None for the house the device is associated to
        @param d_place_type : room, area or house (None means the device is not associated)
        @return the DeviceFeatureAssociation object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_feature = self.__session.query(DeviceFeature).filter_by(id=d_feature_id).first()
        if not device_feature:
            self.__raise_dbhelper_exception("DeviceFeature id %s doesn't exist" % d_feature_id)
        if d_place_id is not None and d_place_type != 'house':
            if d_place_type == 'room':
                if not self.__session.query(Room).filter_by(id=d_place_id).first():
                    self.__raise_dbhelper_exception("Room id %s It does not exist" % d_place_id)
            else: # it is an area
                if not self.__session.query(Area).filter_by(id=d_place_id).first():
                    self.__raise_dbhelper_exception("Couldn't add device with area id %s It does not exist" % d_place_id)

        device_feature_asso = DeviceFeatureAssociation(device_feature_id=d_feature_id, place_type=d_place_type,
                                                       place_id=d_place_id)
        self.__session.add(device_feature_asso)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_asso

    def del_device_feature_association(self, dfa_id):
        """Delete a device feature association

        @param dfa_id : device feature association id
        @return the DeviceFeatureAssociation object which was deleted

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dfa = self.__session.query(
                        DeviceFeatureAssociation
                    ).filter_by(id=dfa_id
                    ).first()
        if not dfa:
            return None
        self.__session.delete(dfa)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dfa

    def del_device_feature_association_by_device_feature_id(self, dfa_device_feature_id):
        """Delete device feature associations for a given device feature id

        @param dfa_device_feature_id : device feature id
        @return the list of DeviceFeatureAssociation object which were deleted

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dfa_list = self.__session.query(
                            DeviceFeatureAssociation
                        ).filter_by(device_feature_id=dfa_device_feature_id
                        ).all()
        for dfa in dfa_list:
            self.__session.delete(dfa)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dfa_list

    def del_device_feature_association_by_place(self, dfa_place_id, dfa_place_type):
        """Delete device feature associations for a given place

        @param dfa_place_id : place id
        @param dfa_place_type : place type (house, area, room)
        @return the list of DeviceFeatureAssociation object which were deleted

        """
        dfa_list = self.__session.query(
                            DeviceFeatureAssociation
                        ).filter_by(place_type=dfa_place_type
                        ).filter_by(place_id=dfa_place_id
                        ).all()
        for dfa in dfa_list:
            self.__session.delete(dfa)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dfa_list

####
# Device technology
####
    def list_device_technologies(self):
        """Return a list of device technologies

        @return a list of DeviceTechnology objects

        """
        return self.__session.query(DeviceTechnology).all()

    def get_device_technology_by_id(self, dt_id):
        """Return information about a device technology

        @param dt_id : the device technology id
        @return a DeviceTechnology object

        """
        return self.__session.query(
                        DeviceTechnology
                    ).filter_by(id=ucode(dt_id)
                    ).first()

    def add_device_technology(self, dt_id, dt_name, dt_description=None):
        """Add a device_technology

        @param dt_id : technology id (ie x10, plcbus, eibknx...) with no spaces / accents or special characters
        @param dt_name : device technology name, one of 'x10', '1wire', 'PLCBus', 'RFXCom', 'IR'
        @param dt_description : extended description of the technology

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dt = DeviceTechnology(id=dt_id, name=dt_name, description=dt_description)
        self.__session.add(dt)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dt

    def update_device_technology(self, dt_id, dt_name=None, dt_description=None):
        """Update a device technology

        @param dt_id : device technology id to be updated
        @param dt_name : device technology name (optional)
        @param dt_description : device technology detailed description (optional)
        @return a DeviceTechnology object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_tech = self.__session.query(
                                DeviceTechnology
                            ).filter_by(id=ucode(dt_id)
                            ).first()
        if device_tech is None:
            self.__raise_dbhelper_exception("DeviceTechnology with id %s couldn't be found" % dt_id)
        if dt_name is not None:
            device_tech.name = ucode(dt_name)
        if dt_description is not None:
            if dt_description == '': dt_description = None
            device_tech.description = ucode(dt_description)
        self.__session.add(device_tech)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_tech

    def del_device_technology(self, dt_id, cascade_delete=False):
        """Delete a device technology record

        @param dt_id : id of the device technology to delete
        @param cascade_delete : True if related objects should be deleted, optional default set to False
        @return the deleted DeviceTechnology object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dt = self.__session.query(DeviceTechnology).filter_by(id=ucode(dt_id)).first()
        if dt:
            if cascade_delete:
                for device_type in self.__session.query(DeviceType).filter_by(device_technology_id=ucode(dt.id)).all():
                    self.del_device_type(device_type.id, cascade_delete=True)
                    self.__session.commit()
            else:
                device_type_list = self.__session.query(
                                            DeviceType
                                        ).filter_by(device_technology_id=ucode(dt.id)
                                        ).all()
                if len(device_type_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device technology %s : there are associated device types"
                                               % dt_id)

            self.__session.delete(dt)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return dt
        else:
            self.__raise_dbhelper_exception("Couldn't delete device technology with id %s : it doesn't exist" % dt_id)

####
# Plugin config
####
    def list_all_plugin_config(self):
        """Return a list of all plugin config parameters

        @return a list of PluginConfig objects

        """
        return self.__session.query(PluginConfig).all()

    def list_plugin_config(self, pl_name, pl_hostname):
        """Return all parameters of a plugin

        @param pl_name : plugin name
        @param pl_hostname : hostname the plugin is installed on
        @return a list of PluginConfig objects

        """
        return self.__session.query(
                        PluginConfig
                    ).filter_by(name=ucode(pl_name)
                    ).filter_by(hostname=ucode(pl_hostname)
                    ).all()

    def get_plugin_config(self, pl_name, pl_hostname, pl_key):
        """Return information about a plugin parameter

        @param pl_name : plugin name
        @param pl_hostname : hostname the plugin is installed on
        @param pl_key : key we want the value from
        @return a PluginConfig object

        """
        return self.__session.query(
                        PluginConfig
                    ).filter_by(name=ucode(pl_name)
                    ).filter_by(hostname=ucode(pl_hostname)
                    ).filter_by(key=ucode(pl_key)
                    ).first()

    def set_plugin_config(self, pl_name, pl_hostname, pl_key, pl_value):
        """Add / update a plugin parameter

        @param pl_name : plugin name
        @param pl_hostname : hostname the plugin is installed on
        @param pl_key : key we want to add / update
        @param pl_value : key value we want to add / update
        @return : the added / updated PluginConfig item

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        plugin_config = self.__session.query(
                                PluginConfig
                            ).filter_by(name=ucode(pl_name)
                            ).filter_by(hostname=ucode(pl_hostname)
                            ).filter_by(key=ucode(pl_key)).first()
        if not plugin_config:
            plugin_config = PluginConfig(name=pl_name, hostname=pl_hostname, key=pl_key, value=pl_value)
        else:
            plugin_config.value = ucode(pl_value)
        self.__session.add(plugin_config)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : " % sql_exception, True)
        return plugin_config

    def del_plugin_config(self, pl_name, pl_hostname):
        """Delete all parameters of a plugin config

        @param pl_name : plugin name
        @param pl_hostname : hostname the plugin is installed on
        @return the deleted PluginConfig objects

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        plugin_config_list = self.__session.query(
                                    PluginConfig
                                ).filter_by(name=ucode(pl_name)
                                ).filter_by(hostname=ucode(pl_hostname)).all()
        for plc in plugin_config_list:
            self.__session.delete(plc)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : " % sql_exception, True)
        return plugin_config_list

###
# Devices
###
    def list_devices(self):
        """Return a list of devices

        @return a list of Device objects

        """
        return self.__session.query(Device).all()

    def get_device(self, d_id):
        """Return a device by its id

        @param d_id : The device id
        @return a Device object

        """
        return self.__session.query(Device).filter_by(id=d_id).first()

    def get_device_by_technology_and_address(self, techno_id, device_address):
        """Return a device by its technology and address

        @param techno_id : technology id
        @param device address : device address
        @return a device object

        """
        device_list = self.__session.query(
                                Device
                            ).filter_by(address=ucode(device_address)
                            ).all()
        if len(device_list) == 0:
            return None
        device = []
        for device in device_list:
            device_type = self.__session.query(
                                    DeviceType
                                ).filter_by(id=device.device_type_id
                                ).first()
            device_tech = self.__session.query(
                                    DeviceTechnology
                                ).filter_by(id=device_type.device_technology_id
                                ).first()
            if device_tech.id.lower() == ucode(techno_id.lower()):
                return device
        return None

    def get_all_devices_of_room(self, d_room_id):
        """Return all the devices of a room

        @param d_room_id: room id
        @return a list of Device objects

        """
        return self.__session.query(Device).filter_by(room_id=d_room_id).all()

    def get_all_devices_of_usage(self, du_id):
        """Return all the devices of a usage

        @param du_id: usage id
        @return a list of Device objects

        """
        return self.__session.query(Device).filter_by(usage_id=du_id).all()

    def add_device(self, d_name, d_address, d_type_id, d_usage_id, d_description=None, d_reference=None):
        """Add a device item

        @param d_name : name of the device
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_type_id : device type id (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param d_usage_id : usage id (ex. temperature)
        @param d_description : extended device description, optional
        @param d_reference : device reference (ex. AM12 for x10), optional
        @return the new Device object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if not self.__session.query(DeviceType).filter_by(id=d_type_id).first():
            self.__raise_dbhelper_exception("Couldn't add device with device type id %s It does not exist" % d_type_id)
        if not self.__session.query(DeviceUsage).filter_by(id=d_usage_id).first():
            self.__raise_dbhelper_exception("Couldn't add device with device usage id %s It does not exist" % d_usage_id)
        device = Device(name=d_name, address=d_address, description=d_description, reference=d_reference,
                        device_type_id=d_type_id, device_usage_id=d_usage_id)
        self.__session.add(device)
        try:
            self.__session.commit()
            # Look up for device feature models according to the device type and create corresponding association
            # between the device and the device feature model
            dfm_list = self.__session.query(
                                DeviceFeatureModel
                            ).filter_by(device_type_id=device.device_type_id
                            ).all()
            for dfm in dfm_list:
                df = DeviceFeature(device_id=device.id, device_feature_model_id=dfm.id)
                self.__session.add(df)
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

    def update_device(self, d_id, d_name=None, d_address=None, d_usage_id=None, d_description=None, d_reference=None):
        """Update a device item

        If a param is None, then the old value will be kept

        @param d_id : Device id
        @param d_name : device name (optional)
        @param d_address : Item address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire) (optional)
        @param d_description : Extended item description (optional)
        @param d_usage : Item usage id (optional)
        @param d_room : Item room id (optional)
        @return the updated Device object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device = self.__session.query(Device).filter_by(id=d_id).first()
        if device is None:
            self.__raise_dbhelper_exception("Device with id %s couldn't be found" % d_id)
        if d_name is not None:
            device.name = ucode(d_name)
        if d_address is not None:
            device.address = ucode(d_address)
        if d_description is not None:
            if d_description == '': d_description = None
            device.description = ucode(d_description)
        if d_reference is not None:
            if d_reference == '': d_reference = None
            device.reference = ucode(d_reference)
        if d_usage_id is not None:
            if not self.__session.query(DeviceUsage).filter_by(id=d_usage_id).first():
                self.__raise_dbhelper_exception("Couldn't find device usage id %s. It does not exist" % d_usage_id)
            device.device_usage = d_usage_id
        self.__session.add(device)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

    def del_device(self, d_id):
        """Delete a device

        @param d_id : device id
        @return the deleted device

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device = self.__session.query(Device).filter_by(id=d_id).first()
        if device is None:
            self.__raise_dbhelper_exception("Device with id %s couldn't be found" % d_id)
        self.__session.delete(device)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

####
# Device config
####
    def list_all_device_config(self):
        """List all device config parameters

        @return A list of DeviceConfig objects

        """
        return self.__session.query(DeviceConfig).all()

    def list_device_config(self, dc_device_id):
        """List all config keys of a device

        @param dc_device_id : device id
        @return A list of DeviceConfig objects

        """
        return self.__session.query(
                        DeviceConfig
                    ).filter_by(device_id=dc_device_id
                    ).all()

    def get_device_config_by_key(self, dc_key, dc_device_id):
        """Get a key of a device configuration

        @param dc_key : key name
        @param dc_device_id : device id
        @return A DeviceConfig object

        """
        return self.__session.query(
                        DeviceConfig
                    ).filter_by(key=ucode(dc_key), device_id=dc_device_id
                    ).first()

    def set_device_config(self, dc_key, dc_value, dc_device_id):
        """Add / update an device config key

        @param dc_key : key name
        @param dc_value : associated value
        @param dc_device_id : device id
        @return : the added/updated DeviceConfig object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_config = self.__session.query(
                                DeviceConfig
                            ).filter_by(key=ucode(dc_key), device_id=dc_device_id
                            ).first()
        if device_config is None:
            device_config = DeviceConfig(key=dc_key, value=dc_value, device_id=dc_device_id)
        else:
            device_config.value = ucode(dc_value)
        self.__session.add(device_config)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_config

    def del_device_config(self, dc_device_id):
        """Delete a device configuration key

        @param dc_device_id : device id
        @return The DeviceConfig object which was deleted

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dc_list = self.__session.query(
                            DeviceConfig
                        ).filter_by(device_id=dc_device_id
                        ).all()
        if dc_list is None:
            self.__raise_dbhelper_exception("Couldnt delete device config for device id %s : it doesn't exist" % dc_device_id)
        dc_list_d = []
        for device_config in dc_list:
            dc_list_d.append(device_config)
            self.__session.delete(device_config)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dc_list_d

####
# Device stats
####
    def list_all_device_stats(self):
        """Return a list of all device stats

        @return a list of DeviceStats objects

        """
        return self.__session.query(DeviceStats).all()

    def list_device_stats(self, ds_device_id):
        """Return a list of all stats for a device

        @param ds_device_id : the device id
        @return a list of DeviceStats objects

        """
        return self.__session.query(
                        DeviceStats
                    ).filter_by(device_id=ds_device_id
                    ).all()

    def list_device_stats_by_key(self, ds_key, ds_device_id):
        """Return a list of all stats for a key and a device

        @param ds_key : the stat key
        @param ds_device_id : the device id
        @return a list of DeviceStats objects

        """
        return self.__session.query(
                        DeviceStats
                    ).filter_by(device_id=ds_device_id
                    ).filter_by(key=ucode(ds_key)
                    ).all()

    def list_last_n_stats_of_device_by_key(self, ds_key, ds_device_id, ds_number):
        """Get the N latest statistics of a device for a given key

        @param ds_key : statistic key
        @param ds_device_id : device id
        @param ds_number : the number of statistics we want to retreive
        @return a list of DeviceStats objects (older records first)

        """
        list_s = self.__session.query(
                            DeviceStats
                        ).filter_by(key=ucode(ds_key)
                        ).filter_by(device_id=ds_device_id
                        ).order_by(sqlalchemy.desc(DeviceStats.date)
                        ).limit(ds_number
                        ).all()
        list_s.reverse()
        return list_s

    def list_stats_of_device_between_by_key(self, ds_key, ds_device_id, start_date_ts=None, end_date_ts=None):
        """Get statistics of a device between two dates for a given key

        @param ds_key : statistic key
        @param ds_device_id : device id
        @param start_date_ts : datetime start, optional (timestamp)
        @param end_date_ts : datetime end, optional (timestamp)
        @return a list of DeviceStats objects (older records first)

        """
        if start_date_ts and end_date_ts:
            if end_date_ts < start_date_ts:
                self.__raise_dbhelper_exception("'end_date' can't be prior to 'start_date'")
        query = self.__session.query(
                        DeviceStats
                    ).filter_by(key=ucode(ds_key)
                    ).filter_by(device_id=ds_device_id)
        if start_date_ts:
            query = query.filter("date >= '" + str(_datetime_string_from_tstamp(start_date_ts, self.get_db_type()))+"'")
        if end_date_ts:
            query = query.filter("date <= '" + str(_datetime_string_from_tstamp(end_date_ts, self.get_db_type())) + "'")
        list_s = query.order_by(sqlalchemy.asc(DeviceStats.date)).all()
        return list_s

    def get_last_stat_of_device_by_key(self, ds_key, ds_device_id):
        """Get the latest statistic of a device for a given key

        @param ds_key : statistic key
        @param ds_device_id : device id
        @return a DeviceStats object

        """
        return self.__session.query(
                        DeviceStats
                    ).filter_by(key=ucode(ds_key)
                    ).filter_by(device_id=ds_device_id
                    ).order_by(sqlalchemy.desc(DeviceStats.date)
                    ).first()

    def filter_stats_of_device_by_key(self, ds_key, ds_device_id, start_date_ts, end_date_ts, step_used, function_used):
        """Filter statistic values within a period for a given step (minute, hour, day, week, month, year). It then
        applies a function (min, max, avg) for the values within the step.

        @param ds_key : statistic key
        @param ds_device_id : device_id
        @param start_date_ts : date representing the begin of the period (timestamp)
        @param end_date_ts : date reprensenting the end of the period (timestamp)
        @param step_used : minute, hour, day, week, month, year
        @param function_used : min, max, avg
        @return a list of tuples (date, computed value)

        """
        if not start_date_ts:
            self.__raise_dbhelper_exception("You have to provide a start date")
        if end_date_ts:
            if start_date_ts > end_date_ts:
                self.__raise_dbhelper_exception("'end_date' can't be prior to 'start_date'")
        else:
            end_date_ts = time.mktime(datetime.datetime.now().timetuple())

        if function_used is None or function_used.lower() not in ('min', 'max', 'avg'):
            self.__raise_dbhelper_exception("'function_used' parameter should be one of : min, max, avg")
        if step_used is None or step_used.lower() not in ('minute', 'hour', 'day', 'week', 'month', 'year'):
            self.__raise_dbhelper_exception("'period' parameter should be one of : minute, hour, day, week, month, year")
        function = {
            'min': func.min(DeviceStats._DeviceStats__value_num),
            'max': func.max(DeviceStats._DeviceStats__value_num),
            'avg': func.avg(DeviceStats._DeviceStats__value_num),
        }
        sql_query = {
            'minute' : {
                # Query for mysql
                # func.week(DeviceStats.date, 3) is equivalent to python's isocalendar()[2] method
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.week(DeviceStats.date, 3), func.day(DeviceStats.date),
                            func.hour(DeviceStats.date), func.minute(DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.day(DeviceStats.date), func.hour(DeviceStats.date),
                            func.minute(DeviceStats.date)
                        ),
                 'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date), extract('minute', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date), extract('minute', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'hour' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.week(DeviceStats.date, 3), func.day(DeviceStats.date),
                            func.hour(DeviceStats.date), function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.day(DeviceStats.date), func.hour(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'day' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.week(DeviceStats.date, 3), func.day(DeviceStats.date),
                                      function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.day(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'week' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.week(DeviceStats.date, 1), function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.week(DeviceStats.date, 1)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('week', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date).label('year_c'), extract('week', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'month' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date),
                            func.month(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'year' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            }
        }

        step = {
            'minute' : (
                 # Get result format of the query
                 lambda dt : [dt.year, dt.month, _get_week_nb(dt), dt.day, dt.hour, dt.minute],
                 # Get max date of the period
                 lambda dt : datetime.datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, 59),
            ),
            'hour' : (
                 lambda dt : [dt.year, dt.month, _get_week_nb(dt), dt.day, dt.hour],
                 lambda dt : datetime.datetime(dt.year, dt.month, dt.day, dt.hour, 59, 59),
            ),
            'day' : (
                 lambda dt : [dt.year, dt.month, _get_week_nb(dt), dt.day],
                 lambda dt : datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59),
            ),
            'week' : (
                 lambda dt : [dt.year, _get_week_nb(dt)],
                 lambda dt : datetime.datetime(dt.year, dt.month, dt.day, 23, 59, 59)
                             + datetime.timedelta(days=6-dt.weekday()),
            ),
            'month' : (
                 lambda dt : [dt.year, dt.month],
                 lambda dt : datetime.datetime(dt.year, dt.month, calendar.monthrange(dt.year, dt.month)[1]),
            ),
            'year' : (
                 lambda dt : [dt.year,],
                 lambda dt : datetime.datetime(dt.year, 12, 31, 23, 59, 59),
            ),
        }

        result_list = []
        if self.get_db_type() in ('mysql', 'postgresql'):
            query = sql_query[step_used][self.get_db_type()]
            query = query.filter_by(key=ucode(ds_key)).filter_by(device_id=ds_device_id
                        ).filter("date >= '" + _datetime_string_from_tstamp(start_date_ts, self.get_db_type()) + "'"
                        ).filter("date < '" + _datetime_string_from_tstamp(end_date_ts, self.get_db_type()) + "'")
            result_list = query.all()
        else:
            datetime_cursor = datetime.datetime.fromtimestamp(start_date_ts)
            end_datetime = datetime.datetime.fromtimestamp(end_date_ts)
            while (datetime_cursor < end_datetime):
                datetime_max_in_the_period = step[step_used][1](datetime_cursor)
                datetime_sup = min(datetime_max_in_the_period, end_datetime)
                query = self.__session.query(
                                func.min(DeviceStats.date), function[function_used]
                            ).filter_by(key=ucode(ds_key)).filter_by(device_id=ds_device_id
                            ).filter("date >= '" + _datetime_to_string(datetime_cursor, self.get_db_type()) + "'"
                            ).filter("date < '" + _datetime_to_string(datetime_sup, self.get_db_type()) + "'")
                result = query.first()
                cur_date = result[0]
                if cur_date is not None:
                    values_returned = step[step_used][0](datetime_cursor)
                    values_returned.append(result[1])
                    result_list.append(tuple(values_returned))
                datetime_cursor = datetime_sup + datetime.timedelta(seconds=1)
        return result_list

    def device_has_stats(self, ds_device_id):
        """Check if the device has stats that were recorded

        @param d_device_id : device id
        @return True or False

        """
        return self.__session.query(
                        DeviceStats
                    ).filter_by(device_id=ds_device_id
                    ).count() > 0

    def add_device_stat(self, ds_timestamp, ds_key, ds_value, ds_device_id, hist_size=0):
        """Add a device stat record

        @param ds_key : key for the stat
        @param ds_timestamp : when the stat was gathered
        @param ds_value : stat value
        @param ds_device_id : device id
        @param hist_size : keep only the last hist_size records after having inserted the item (default is 0 which
        means to keep all values)
        @return the new DeviceStats object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if not self.__session.query(Device).filter_by(id=ds_device_id).first():
            self.__raise_dbhelper_exception("Couldn't add device stat with device id %s. It does not exist" % ds_device_id)
        device_stat = DeviceStats(date=datetime.datetime.fromtimestamp(ds_timestamp), timestamp=ds_timestamp,
                                  key=ds_key, value=ds_value, device_id=ds_device_id)
        self.__session.add(device_stat)
        try:
            self.__session.commit()
        except Exception, sql_exception:
           self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        # Eventually remove old stats
        if hist_size > 0:
            stats_list = self.__session.query(
                                    DeviceStats
                                ).filter_by(device_id=ds_device_id
                                ).filter_by(key=ucode(ds_key)
                                ).order_by(sqlalchemy.desc(DeviceStats.date))[:hist_size]
            last_date_to_keep = stats_list[len(stats_list)-1].date
            stats_list = self.__session.query(
                                    DeviceStats
                                ).filter_by(device_id=ds_device_id
                                ).filter_by(key=ucode(ds_key)
                                ).filter("date < '" + _datetime_to_string(last_date_to_keep,
                                         self.get_db_type()) + "'"
                                ).all()
            for stat in stats_list:
                self.__session.delete(stat)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_stat

    def del_device_stats(self, ds_device_id, ds_key=None):
        """Delete a stat record for a given key and device

        @param ds_device_id : device id
        @param ds_key : stat key, optional
        @return list of deleted DeviceStat objects

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        query = self.__session.query(DeviceStats).filter_by(device_id=ds_device_id)
        if ds_key:
            query = query.filter_by(key=ucode(ds_key))
        device_stats_l = query.all()
        for ds in device_stats_l:
            self.__session.delete(ds)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_stats_l

####
# Triggers
####
    def list_triggers(self):
        """Return a list of all triggers

        @return a list of Trigger objects

        """
        return self.__session.query(Trigger).all()

    def get_trigger(self, t_id):
        """Return a trigger information from id

        @param t_id : trigger id
        @return a Trigger object

        """
        return self.__session.query(Trigger).filter_by(id=t_id).first()

    def add_trigger(self, t_description, t_rule, t_result):
        """Add a trigger

        @param t_description : trigger description
        @param t_rule : trigger rule
        @param t_result : trigger result (list of strings)
        @return the new Trigger object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        trigger = Trigger(description=t_description, rule=t_rule, result=';'.join(t_result))
        self.__session.add(trigger)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return trigger

    def update_trigger(self, t_id, t_description=None, t_rule=None, t_result=None):
        """Update a trigger

        @param dt_id : trigger id to be updated
        @param t_description : trigger description
        @param t_rule : trigger rule
        @param t_result : trigger result (list of strings)
        @return a Trigger object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        trigger = self.__session.query(Trigger).filter_by(id=t_id).first()
        if trigger is None:
            self.__raise_dbhelper_exception("Trigger with id %s couldn't be found" % t_id)
        if t_description is not None:
            if t_description == '':
                t_description = None
            trigger.description = ucode(t_description)
        if t_rule is not None:
            trigger.rule = ucode(t_rule)
        if t_result is not None:
            trigger.result = ucode(';'.join(t_result))
        self.__session.add(trigger)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return trigger

    def del_trigger(self, t_id):
        """Delete a trigger

        @param t_id : trigger id
        @return the deleted Trigger object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        trigger = self.__session.query(Trigger).filter_by(id=t_id).first()
        if trigger:
            self.__session.delete(trigger)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return trigger
        else:
            self.__raise_dbhelper_exception("Couldn't delete trigger with id %s : it doesn't exist" % t_id)

####
# User accounts
####
    def list_user_accounts(self):
        """Return a list of all accounts

        @return a list of UserAccount objects

        """
        list_sa = self.__session.query(UserAccount).all()
        return list_sa

    def get_user_account(self, a_id):
        """Return user account information from id

        @param a_id : account id
        @return a UserAccount object

        """
        user_acc = self.__session.query(UserAccount).filter_by(id=a_id).first()
        return user_acc

    def get_user_account_by_login(self, a_login):
        """Return user account information from login

        @param a_login : login
        @return a UserAccount object

        """
        return self.__session.query(
                            UserAccount
                        ).filter_by(login=ucode(a_login)
                        ).first()

    def get_user_account_by_person(self, p_id):
        """Return a user account associated to a person, if existing

        @param p_id : The person id
        @return a UserAccount object

        """
        return self.__session.query(
                        UserAccount
                    ).filter_by(person_id=p_id
                    ).first()

    def authenticate(self, a_login, a_password):
        """Check if a user account with a_login, a_password exists

        @param a_login : Account login
        @param a_password : Account password (clear)
        @return True or False

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_acc = self.__session.query(
                            UserAccount
                        ).filter_by(login=ucode(a_login)
                        ).first()
        return user_acc is not None and user_acc._UserAccount__password == _make_crypted_password(a_password)

    def add_user_account(self, a_login, a_password, a_person_id, a_is_admin=False, a_skin_used=''):
        """Add a user account

        @param a_login : Account login
        @param a_password : Account clear text password (will be hashed in sha256)
        @param a_person_id : id of the person associated to the account
        @param a_is_admin : True if it is an admin account, False otherwise (optional, default=False)
        @return the new UserAccount object or raise a DbHelperException if it already exists

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_account = self.__session.query(
                                UserAccount
                            ).filter_by(login=ucode(a_login)
                            ).first()
        if user_account is not None:
            self.__raise_dbhelper_exception("Error %s login already exists" % a_login)
        person = self.__session.query(Person).filter_by(id=a_person_id).first()
        if person is None:
            self.__raise_dbhelper_exception("Person id '%s' does not exist" % a_person_id)
        user_account = UserAccount(login=a_login, password=_make_crypted_password(a_password),
                                   person_id=a_person_id, is_admin=a_is_admin, skin_used=a_skin_used)
        self.__session.add(user_account)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return user_account

    def add_user_account_with_person(self, a_login, a_password, a_person_first_name, a_person_last_name,
                                     a_person_birthdate=None, a_is_admin=False, a_skin_used=''):
        """Add a user account and a person

        @param a_login : Account login
        @param a_password : Account clear text password (will be hashed in sha256)
        @param a_person_first_name : first name of the person associated to the account
        @param a_person_last_name : last name of the person associated to the account
        @param a_person_birthdate : birthdate of the person associated to the account, optional
        @param a_is_admin : True if it is an admin account, False otherwise (optional, default=False)
        @param a_skin_used : name of the skin choosen by the user (optional, default='skins/default')
        @return the new UserAccount object or raise a DbHelperException if it already exists

        """
        person = self.add_person(a_person_first_name, a_person_last_name, a_person_birthdate)
        return self.add_user_account(a_login, a_password, person.id, a_is_admin, a_skin_used)

    def update_user_account(self, a_id, a_new_login=None, a_person_id=None, a_is_admin=None, a_skin_used=None):
        """Update a user account

        @param a_id : Account id to be updated
        @param a_new_login : The new login (optional)
        @param a_person_id : id of the person associated to the account
        @param a_is_admin : True if it is an admin account, False otherwise (optional)
        @param a_skin_used : name of the skin choosen by the user (optional, default='skins/default')
        @return a UserAccount object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_acc = self.__session.query(UserAccount).filter_by(id=a_id).first()
        if user_acc is None:
            self.__raise_dbhelper_exception("UserAccount with id %s couldn't be found" % a_id)
        if a_new_login is not None:
            user_acc.login = ucode(a_new_login)
        if a_person_id is not None:
            person = self.__session.query(Person).filter_by(id=a_person_id).first()
            if person is None:
                self.__raise_dbhelper_exception("Person id '%s' does not exist" % a_person_id)
            user_acc.person_id = a_person_id
        if a_is_admin is not None:
            user_acc.is_admin = a_is_admin
        if a_skin_used is not None:
            user_acc.skin_used = ucode(a_skin_used)
        self.__session.add(user_acc)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return user_acc

    def update_user_account_with_person(self, a_id, a_login=None, p_first_name=None, p_last_name=None, p_birthdate=None,
                                        a_is_admin=None, a_skin_used=None):
        """Update a user account a person information

        @param a_id : Account id to be updated
        @param a_login : The new login (optional)
        @param p_first_name : first name of the person associated to the account, optional
        @param p_last_name : last name of the person associated to the account, optional
        @param p_birthdate : birthdate of the person associated to the account, optional
        @param a_is_admin : True if it is an admin account, False otherwise, optional
        @param a_skin_used : name of the skin choosen by the user (optional, default='skins/default')
        @return a UserAccount object

        """
        user_acc = self.update_user_account(a_id, a_login, None, a_is_admin, a_skin_used)
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        person = user_acc.person
        if p_first_name is not None:
            person.first_name = ucode(p_first_name)
        if p_last_name is not None:
            person.last_name = ucode(p_last_name)
        if p_birthdate is not None:
            person.birthdate = p_birthdate
        self.__session.add(person)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return user_acc

    def change_password(self, a_id, a_old_password, a_new_password):
        """Change the password

        @param a_id : account id
        @param a_old_password : the password to change (the old one, in clear text)
        @param a_new_password : the new password, in clear text (will be hashed in sha256)
        @return True if the password could be changed, False otherwise (login or old_password is wrong)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_acc = self.__session.query(UserAccount).filter_by(id=a_id).first()
        if user_acc is not None:
            old_pass = ucode(_make_crypted_password(a_old_password))
            if user_acc._UserAccount__password != old_pass:
                return False
        else:
            return False
        user_acc.set_password(ucode(_make_crypted_password(a_new_password)))
        self.__session.add(user_acc)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return True

    def add_default_user_account(self):
        """Add a default user account (login = admin, password = domogik, is_admin = True)

        @return a UserAccount object

        """
        person = self.add_person(p_first_name='Admin', p_last_name='Admin', p_birthdate=datetime.date(1900, 01, 01))
        return self.add_user_account(a_login='admin', a_password='123', a_person_id=person.id, a_is_admin=True)

    def del_user_account(self, a_id):
        """Delete a user account

        @param a_id : account id
        @return the deleted UserAccount object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_account = self.__session.query(UserAccount).filter_by(id=a_id).first()
        if user_account:
            self.__session.delete(user_account)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return user_account
        else:
            self.__raise_dbhelper_exception("Couldn't delete user account with id %s : it doesn't exist" % a_id)

####
# Persons
####
    def list_persons(self):
        """Return the list of all persons

        @return a list of Person objects

        """
        return self.__session.query(Person).all()

    def get_person(self, p_id):
        """Return person information

        @param p_id : person id
        @return a Person object

        """
        return self.__session.query(Person).filter_by(id=p_id).first()

    def add_person(self, p_first_name, p_last_name, p_birthdate=None):
        """Add a person

        @param p_first_name     : first name
        @param p_last_name      : last name
        @param p_birthdate      : birthdate, optional
        @param p_user_account   : Person account on the user (optional)
        @return the new Person object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        person = Person(first_name=p_first_name, last_name=p_last_name, birthdate=p_birthdate)
        self.__session.add(person)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return person

    def update_person(self, p_id, p_first_name=None, p_last_name=None, p_birthdate=None):
        """Update a person

        @param p_id             : person id to be updated
        @param p_first_name     : first name (optional)
        @param p_last_name      : last name (optional)
        @param p_birthdate      : birthdate (optional)
        @return a Person object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        person = self.__session.query(Person).filter_by(id=p_id).first()
        if person is None:
            self.__raise_dbhelper_exception("Person with id %s couldn't be found" % p_id)
        if p_first_name is not None:
            person.first_name = ucode(p_first_name)
        if p_last_name is not None:
            person.last_name = ucode(p_last_name)
        if p_birthdate is not None:
            if p_birthdate == '':
                p_birthdate = None
            person.birthdate = p_birthdate
        self.__session.add(person)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return person

    def del_person(self, p_id):
        """Delete a person and the associated user account if it exists

        @param p_id : person account id
        @return the deleted Person object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        person = self.__session.query(Person).filter_by(id=p_id).first()
        if person is not None:
            self.__session.delete(person)
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return person
        else:
            self.__raise_dbhelper_exception("Couldn't delete person with id %s : it doesn't exist" % p_id)

###
# UIItemConfig
###

    def set_ui_item_config(self, ui_item_name, ui_item_reference, ui_item_key, ui_item_value):
        """Add / update an UI parameter

        @param ui_item_name : item name
        @param ui_item_reference : the item reference
        @param ui_item_key : key we want to add / update
        @param ui_item_value : key value we want to add / update
        @return : the updated UIItemConfig item

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        ui_item_config = self.get_ui_item_config(ui_item_name, ui_item_reference, ui_item_key)
        if ui_item_config is None:
            ui_item_config = UIItemConfig(name=ui_item_name, reference=ui_item_reference, key=ui_item_key,
                                          value=ui_item_value)
        else:
            ui_item_config.value = ucode(ui_item_value)
        self.__session.add(ui_item_config)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return ui_item_config

    def get_ui_item_config(self, ui_item_name, ui_item_reference, ui_item_key):
        """Get a UI parameter of an item

        @param ui_item_name : item name
        @param ui_item_reference : item reference
        @param ui_item_key : key
        @return an UIItemConfig object

        """
        return self.__session.query(
                        UIItemConfig
                    ).filter_by(name=ucode(ui_item_name), reference=ucode(ui_item_reference),
                                key=ucode(ui_item_key)
                    ).first()

    def list_ui_item_config_by_ref(self, ui_item_name, ui_item_reference):
        """List all UI parameters of an item

        @param ui_item_name : item name
        @param ui_item_reference : item reference
        @return a list of UIItemConfig objects

        """
        return self.__session.query(
                        UIItemConfig
                    ).filter_by(name=ucode(ui_item_name), reference=ucode(ui_item_reference)
                    ).all()

    def list_ui_item_config_by_key(self, ui_item_name, ui_item_key):
        """List all UI parameters of an item

        @param ui_item_name : item name
        @param ui_item_key : item key
        @return a list of UIItemConfig objects

        """
        return self.__session.query(
                        UIItemConfig
                    ).filter_by(name=ucode(ui_item_name), key=ucode(ui_item_key)
                    ).all()

    def list_ui_item_config(self, ui_item_name):
        """List all UI parameters of an item

        @param ui_item_name : item name
        @return a list of UIItemConfig objects

        """
        return self.__session.query(
                        UIItemConfig
                    ).filter_by(name=ucode(ui_item_name)
                    ).all()

    def list_all_ui_item_config(self):
        """List all UI parameters

        @return a list of UIItemConfig objects

        """
        return self.__session.query(UIItemConfig).all()

    def del_ui_item_config(self, ui_item_name, ui_item_reference=None, ui_item_key=None):
        """Delete a UI parameter of an item

        @param ui_item_name : item name
        @param ui_item_reference : item reference, optional
        @param ui_item_key : key of the item, optional
        @return the deleted UIItemConfig object(s)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        ui_item_config_list = []
        if ui_item_reference == None and ui_item_key == None:
            ui_item_config_list = self.__session.query(
                                            UIItemConfig
                                        ).filter_by(name=ucode(ui_item_name)
                                        ).all()
        elif ui_item_key is None:
            ui_item_config_list = self.__session.query(
                                            UIItemConfig
                                        ).filter_by(name=ucode(ui_item_name),
                                                    reference=ucode(ui_item_reference)
                                        ).all()
        elif ui_item_reference is None:
            ui_item_config_list = self.__session.query(
                                            UIItemConfig
                                        ).filter_by(name=ucode(ui_item_name), key=ucode(ui_item_key)
                                        ).all()
        else:
            ui_item_config = self.get_ui_item_config(ui_item_name, ui_item_reference, ui_item_key)
            if ui_item_config is not None:
                ui_item_config_list.append(ui_item_config)

        for item in ui_item_config_list:
            self.__session.delete(item)
        if len(ui_item_config_list) > 0:
            try:
                self.__session.commit()
            except Exception, sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return ui_item_config_list

###
# SystemConfig
###
    def get_system_config(self):
        """Get current system configuration

        @return a SystemConfig object

        """
        try:
            return self.__session.query(SystemConfig).one()
        except MultipleResultsFound:
            self.__raise_dbhelper_exception("Error : SystemConfig has more than one line")
        except NoResultFound:
            pass

    def update_system_config(self, s_simulation_mode=None, s_debug_mode=None):
        """Update (or create) system configuration

        @param s_simulation_mode : True if the system is running in simulation mode (optional)
        @param s_debug_mode : True if the system is running in debug mode (optional)
        @return a SystemConfig object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        system_config = self.__session.query(SystemConfig).first()
        if system_config is not None:
            if s_simulation_mode is not None:
                system_config.simulation_mode = s_simulation_mode
            if s_debug_mode is not None:
                system_config.debug_mode = s_debug_mode
        else:
            system_config = SystemConfig(simulation_mode=s_simulation_mode, debug_mode=s_debug_mode)
        self.__session.add(system_config)
        try:
            self.__session.commit()
        except Exception, sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return system_config

    def __raise_dbhelper_exception(self, error_msg, with_rollback=False):
        """Raise a DbHelperException and log it

        @param error_msg : error message
        @param with_rollback : True if a rollback should be done (default is set to False)

        """
        self.log.error(error_msg)
        if with_rollback:
            self.__session.rollback()
        raise DbHelperException(error_msg)


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

Plugin purpose
==============

Defines the sql schema used by Domogik

Implements
==========

- class Area
- class Room
- class DeviceUsage
- class DeviceTechnology
- class PluginConfig
- class DeviceType(Base):
- class Device
- class DeviceFeature
- class DeviceFeatureAssociation
- class DeviceConfig
- class DeviceStats
- class Trigger
- class Person
- class UserAccount
- class SystemStats(Base):
- class SystemStatsValue
- class UIItemConfig
- class SystemConfig

@author: Marc SCHNEIDER <marc@domogik.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import time, sys
from exceptions import AssertionError

from sqlalchemy import (
        types, create_engine, Table, Column, Index, Integer, Float, String, Enum,
        MetaData, ForeignKey, Boolean, DateTime, Date, Text,
        Unicode, UnicodeText, UniqueConstraint
)
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref

from domogik.common.utils import ucode
from domogik.common.configloader import Loader


DEVICE_TYPE_LIST = ['appliance', 'lamp', 'music', 'sensor']
ACTUATOR_VALUE_TYPE_LIST = ['binary', 'range', 'list', 'trigger', 'number', 'string', 'complex',]
SENSOR_VALUE_TYPE_LIST = ['boolean', 'number', 'string']

Base = declarative_base()
metadata = Base.metadata

_cfg = Loader('database')
_config = None
# TODO : if no need
#if len(sys.argv) > 1:
#    _config = _cfg.load(sys.argv[1])
#else:
_config = _cfg.load()
_db_prefix = dict(_config[1])['db_prefix']


# Define objects
class Page(Base):
    """Page: is something to display widgets in the ui"""

    __tablename__ = '%s_ui_page' % _db_prefix
    id = Column(Integer, primary_key=True)
    lft = Column(Integer, primary_key=True)
    rgt = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText(), nullable=True)
    icon = Column(Unicode(30), nullable=True)

    def __init__(self, name, description=None, icon=None):
        """Class constructor
        @param lft : left value
        @param rgt : rgt value
        @param name : short name of the area
        @param description : extended description, optional
        @param icon : the icon to display
        """
        self.name = ucode(name)
        self.description = ucode(description)
        self.icon = ucode(icon)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Page(id=%s, lft=%s, rgt=%s, name='%s', desc='%s', icon='%s')>" % (self.id,self.lft, self.rgt,  self.name, self.description, self.icon)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Area.__tablename__


class Area(Base):
    """Area : it is something like "first floor", "garden", etc ..."""

    __tablename__ = '%s_area' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    rooms = relation('Room', backref=__tablename__)

    def __init__(self, name, description=None):
        """Class constructor

        @param name : short name of the area
        @param description : extended description, optional

        """
        self.name = ucode(name)
        self.description = ucode(description)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Area(id=%s, name='%s', desc='%s')>" % (self.id, self.name, self.description)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Area.__tablename__


class Room(Base):
    """Room"""

    __tablename__ = '%s_room' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    area_id = Column(Integer, ForeignKey('%s.id' % Area.get_tablename()))
    area = relation(Area)

    def __init__(self, name, description=None, area_id=None):
        """Class constructor

        @param name : short name of the area
        @param description : extended description, optional
        @param area_id : id of the area where the room is, optional

        """
        self.name = ucode(name)
        self.description = ucode(description)
        self.area_id = area_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Room(id=%s, name='%s', desc='%s', area=%s)>" % (self.id, self.name, self.description, self.area)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Room.__tablename__


class DeviceUsage(Base):
    """Usage of a device (temperature, heating, lighting, music...)"""

    __tablename__ = '%s_device_usage' % _db_prefix
    id = Column(Unicode(80), primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    default_options = Column(UnicodeText())

    def __init__(self, id, name, description=None, default_options=None):
        """Class constructor

        @param id : usage id
        @param name : short name of the usage
        @param description : extended description, optional
        @param default_options : default options, optional

        """
        self.id = ucode(id)
        self.name = ucode(name)
        self.description = ucode(description)
        self.default_options = ucode(default_options)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceUsage(id=%s, name='%s', desc='%s', default opt='%s')>"\
                % (self.id, self.name, self.description, self.default_options)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceUsage.__tablename__


class DeviceTechnology(Base):
    """Technology of a device (X10, PLCBus, 1wire, RFXCOM,...)"""

    __tablename__ = '%s_device_technology' % _db_prefix
    id = Column(Unicode(30), primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())

    def __init__(self, id, name, description=None):
        """Class constructor

        @param id : technology id (ie x10, plcbus, eibknx...) with no spaces / accents or special characters
        @param name : short name of the technology
        @param description : extended description, optional

        """
        self.id = ucode(id)
        self.name = ucode(name)
        self.description = ucode(description)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceTechnology(id=%s, name='%s', desc='%s')>" % (self.id, self.name, self.description)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceTechnology.__tablename__


class PluginConfig(Base):
    """Configuration for a plugin (x10, plcbus, ...)"""

    __tablename__ = '%s_plugin_config' % _db_prefix
    id = Column(Unicode(30), primary_key=True)
    hostname = Column(Unicode(40), primary_key=True)
    key = Column(Unicode(30), primary_key=True)
    value = Column(Unicode(255), nullable=False)

    def __init__(self, id, hostname, key, value):
        """Class constructor

        @param id : plugin id
        @param hostname : hostname the plugin is installed on
        @param key : key
        @param value : value

        """
        self.id = ucode(id)
        self.hostname = ucode(hostname)
        self.key = ucode(key)
        self.value = ucode(value)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<PluginConfig(id=%s, hostname=%s, (%s, %s))>" % (self.id, self.hostname, self.key, self.value)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return PluginConfig.__tablename__


class DeviceType(Base):
    """Type of a device (x10.Switch, x10.Dimmer, Computer.WOL...)"""

    __tablename__ = '%s_device_type' % _db_prefix
    id = Column(Unicode(80), primary_key=True)
    device_technology_id = Column(Unicode(30), ForeignKey('%s.id' % DeviceTechnology.get_tablename()), nullable=False)
    device_technology = relation(DeviceTechnology)
    name = Column(Unicode(80), nullable=False)
    description = Column(UnicodeText())

    def __init__(self, id, name, device_technology_id, description=None):
        """Class constructor

        @paral id : device type id
        @param name : short name of the type
        @param description : extended description, optional
        @param device_technology_id : technology id

        """
        self.id = ucode(id)
        self.name = ucode(name)
        self.description = ucode(description)
        self.device_technology_id = ucode(device_technology_id)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceType(id='%s', name='%s', desc='%s', device techno='%s')>"\
               % (self.id, self.name, self.description, self.device_technology)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceType.__tablename__


class Device(Base):
    """Device"""

    __tablename__ = '%s_device' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    address = Column(Unicode(255), nullable=False)
    reference = Column(Unicode(30))
    device_usage_id = Column(Unicode(80), ForeignKey('%s.id' % DeviceUsage.get_tablename()), nullable=False)
    device_usage = relation(DeviceUsage)
    device_type_id = Column(Unicode(80), ForeignKey('%s.id' % DeviceType.get_tablename()), nullable=False)
    device_type = relation(DeviceType)
    device_stats = relation("DeviceStats", backref=__tablename__, cascade="all, delete")
    device_configs = relation("DeviceConfig", backref=__tablename__, cascade="all, delete")
    device_features = relation("DeviceFeature", backref=__tablename__, cascade="all, delete")

    def __init__(self, name, address, reference, device_usage_id, device_type_id, description=None):
        """Class constructor

        @param name : short name of the device
        @param address : device address (like 'A3' for x10, or '01.123456789ABC' for 1wire)
        @param reference : internal reference of the device (like AM12 for a X10 device)
        @param device_usage_id : link to the device usage
        @param device_type_id : 'link to the device type (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param description : extended description, optional

        """
        self.name = ucode(name)
        self.address = ucode(address)
        self.reference = ucode(reference)
        self.device_type_id = device_type_id
        self.device_usage_id = device_usage_id
        self.description = ucode(description)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Device(id=%s, name='%s', addr='%s', desc='%s', ref='%s', type='%s', usage=%s)>"\
               % (self.id, self.name, self.address, self.description, self.reference,\
                  self.device_type, self.device_usage)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Device.__tablename__


class DeviceFeatureModel(Base):
    """Device features that can be associated to a device (type) : switch, dimmer, temperature..."""

    __tablename__ = '%s_device_feature_model' % _db_prefix
    id = Column(Unicode(80), primary_key=True)
    name = Column(Unicode(30), nullable=False)
    feature_type = Column(Enum('actuator', 'sensor', name='feature_type_list'), nullable=False)
    device_type_id = Column(Unicode(80), ForeignKey('%s.id' % DeviceType.get_tablename()), nullable=False)
    device_type = relation(DeviceType)
    parameters = Column(UnicodeText())
    value_type = Column(Unicode(30), nullable=False)
    stat_key = Column(Unicode(30))
    return_confirmation = Column(Boolean, nullable=False)
    device_features = relation("DeviceFeature", backref=__tablename__, cascade="all, delete")

    def __init__(self, id, name, feature_type, device_type_id, value_type, parameters=None, stat_key=None,
                return_confirmation=False):
        """Class constructor

        @param id : device feature id
        @param name : device feature name (Switch, Dimmer, Thermometer, Voltmeter...)
        @param feature_type : device feature type (actuator / sensor)
        @param device_type_id : device type id
        @param value_type : value type the actuator can accept / the sensor can return
        @param parameters : parameters about the command or the returned data associated to the device, optional
        @param stat_key : key reference in the core_device_stats table, optional
        @param return_confirmation : True if the device returns a confirmation after having executed a command, optional (default False)
                                     Only relevant for actuators

        """
        self.id = ucode(id)
        self.name = ucode(name)
        if feature_type not in ('actuator', 'sensor'):
            raise Exception("Feature type must me either 'actuator' or 'sensor' but NOT %s" % feature_type)
        self.feature_type = feature_type
        if self.feature_type == 'actuator' and value_type not in ACTUATOR_VALUE_TYPE_LIST:
            raise Exception("Can't add value type %s to an actuator it doesn't belong to list %s"
                            % (value_type, ACTUATOR_VALUE_TYPE_LIST))
        elif self.feature_type == 'sensor' and value_type not in SENSOR_VALUE_TYPE_LIST:
            raise Exception("Can't add value type %s to a sensor it doesn't belong to list %s"
                            % (value_type, SENSOR_VALUE_TYPE_LIST))
        self.device_type_id = device_type_id
        self.value_type = ucode(value_type)
        self.parameters = ucode(parameters)
        self.stat_key = ucode(stat_key)
        self.return_confirmation = return_confirmation

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceFeatureModel(%s, %s, device_type=%s, param=%s, value_type=%s, stat_key=%s, return_conf=%s)>"\
               % (self.id, self.feature_type, self.device_type, self.parameters, self.value_type,\
                  self.stat_key, self.return_confirmation)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceFeatureModel.__tablename__


class DeviceFeature(Base):
    """Association between Device and DeviceFeatureModel entities"""

    __tablename__ = '%s_device_feature' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()))
    device = relation(Device, backref=backref(__tablename__))
    device_feature_model_id = Column(Unicode(80), ForeignKey('%s.id' % DeviceFeatureModel.get_tablename()))
    device_feature_model = relation(DeviceFeatureModel)
    device_feature_associations = relation("DeviceFeatureAssociation", backref=__tablename__, cascade="all, delete")

    UniqueConstraint(device_id, device_feature_model_id)

    def __init__(self, device_id, device_feature_model_id):
        """Class constructor

        @param device_id : device id
        @param device_feature_model_id : device feature model id

        """
        self.device_id = device_id
        self.device_feature_model_id = device_feature_model_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceFeature(%s, %s, %s)>" % (self.id, self.device, self.device_feature_model)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceFeature.__tablename__


class DeviceFeatureAssociation(Base):
    """Association between devices, features and an item (room, area, house)"""

    __tablename__ = '%s_device_feature_association' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_feature_id = Column(Integer, ForeignKey('%s.id' % DeviceFeature.get_tablename()))
    device_feature = relation(DeviceFeature)
    place_type = Column(Enum('room', 'area', 'house', name='place_type_list'), nullable=True)
    place_id = Column(Integer, nullable=True)

    def __init__(self, device_feature_id, place_type=None, place_id=None):
        """Class constructor

        @param device_feature_id : device feature id
        @param place_type : room, area or house, optional (None if the feature is not associated to one of the places)
        @param place_id : place id (None if it is the house, or if the feature is not associated to one of the places)

        """
        device_feat_ass_list = [None, 'room', 'area', 'house']
        if place_type not in device_feat_ass_list:
            raise DbHelperException("Place type should be one of : %s" % device_feat_ass_list)
        if place_type is None and place_id is not None:
            raise DbHelperException("Place id should be None as item type is None")
        if (place_type == 'room' or place_type == 'area') and place_id is None:
            raise DbHelperException("A place id should have been provided, place type is %s" % place_type)
        self.device_feature_id = device_feature_id
        self.place_type = place_type
        self.place_id = place_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceFeatureAssociation(%s, %s, %s, place_id=%s)>"\
               % (self.id, self.device_feature, self.place_type, self.place_id)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceFeatureAssociation.__tablename__


class DeviceConfig(Base):
    """Device configuration"""

    __tablename__ = '%s_device_config' % _db_prefix
    key = Column(Unicode(30), primary_key=True)
    value = Column(Unicode(255), nullable=False)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), primary_key=True)
    device = relation(Device)

    def __init__(self, key, device_id, value):
        """Class constructor

        @param key : configuration item
        @param value : configuration value
        @param device_id : device id

        """
        self.key = ucode(key)
        self.value = ucode(value)
        self.device_id = device_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceConfig(('%s', '%s'), device=%s)>" % (self.key, self.value, self.device)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceConfig.__tablename__


class DeviceStats(Base):
    """Device stats (values that were associated to the device)"""

    __tablename__ = '%s_device_stats' % _db_prefix
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, index=True)
    # This is used for mysql compatibility reasons as timestamps are NOT handled in Unix Time format
    timestamp = Column(Integer, nullable=False)
    skey = Column(Unicode(30), nullable=False, index=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), nullable=False)
    device = relation(Device)
    # We have both types for value field because we need an explicit numerical field in case we want to compute
    # arithmetical operations (min/max/avg etc.). If it is a numerical value, both fields are filled in. If it is a
    # character value only 'value' field is filled in.
    __value_num = Column('value_num', Float)
    value = Column('value_str', Unicode(255))
    __table_args__ = (Index('ix_core_device_stats_date_skey_device_id', "date", "skey", "device_id"), )

    def __init__(self, date, timestamp, skey, device_id, value):
        """Class constructor

        @param date : date when the stat was recorded
        @param timestamp : corresponding timestamp
        @param skey : key for the stat
        @param device_id : device id
        @param value : stat value (numerical or string)

        """
        self.date = date
        self.timestamp = timestamp
        self.skey = ucode(skey)
        try:
            self.__value_num = float(value)
        except ValueError:
            pass
        self.value = ucode(value)
        self.device_id = device_id

    def get_date_as_timestamp(self):
        """Convert DateTime value to timestamp"""
        return time.mktime(self.date.timetuple())

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceStats(%s, date='%s', (%s, %s), device=%s)>" % (self.id, self.date, self.skey, self.value,
                                                                      self.device)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceStats.__tablename__


class Trigger(Base):
    """Trigger : execute commands when conditions are met"""

    __tablename__ = '%s_trigger' % _db_prefix
    id = Column(Integer, primary_key=True)
    description = Column(UnicodeText())
    rule = Column(UnicodeText(), nullable=False)
    result = Column(UnicodeText(), nullable=False)

    def __init__(self, rule, result, description=None):
        """Class constructor

        @param rule : formatted trigger rule
        @param result : list of xpl message to send when the rule is met
        @param description : long description of the rule, optional

        """
        self.rule = ucode(rule)
        self.result = ucode(result)
        self.description = ucode(description)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Trigger(id=%s, desc='%s', rule='%s', result='%s')>"\
               % (self.id, self.description, self.rule, self.result)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Trigger.__tablename__


class Person(Base):
    """Persons registered in the app"""

    __tablename__ = '%s_person' % _db_prefix
    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(20), nullable=False)
    last_name = Column(Unicode(20), nullable=False)
    birthdate = Column(Date)
    user_accounts = relation("UserAccount", backref=__tablename__, cascade="all, delete")

    def __init__(self, first_name, last_name, birthdate):
        """Class constructor

        @param first_name : first name
        @param last_name : last name
        @param birthdate : birthdate

        """
        self.first_name = ucode(first_name)
        self.last_name = ucode(last_name)
        self.birthdate = birthdate

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Person(id=%s, first_name='%s', last_name='%s', birthdate='%s')>"\
               % (self.id, self.first_name, self.last_name, self.birthdate)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Person.__tablename__


class UserAccount(Base):
    """User account for persons : it is only used by the UI"""

    __tablename__ = '%s_user_account' % _db_prefix
    id = Column(Integer, primary_key=True)
    login = Column(Unicode(20), nullable=False, unique=True)
    __password = Column("password", Unicode(255), nullable=False)
    person_id = Column(Integer, ForeignKey('%s.id' % Person.get_tablename()))
    person = relation(Person)
    is_admin = Column(Boolean, nullable=False, default=False)
    skin_used = Column(Unicode(80), nullable=False)

    def __init__(self, login, password, is_admin, skin_used, person_id):
        """Class constructor

        @param login : login
        @param password : password
        @param person_id : id of the person associated to this account
        @param is_admin : True if the user has administrator privileges
        @param skin_used : skin used in the UI (default value = 'default')

        """
        self.login = ucode(login)
        self.__password = ucode(password)
        self.person_id = person_id
        self.is_admin = is_admin
        self.skin_used = ucode(skin_used)

    def set_password(self, password):
        """Set a password for the user"""
        self.__password = ucode(password)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<UserAccount(id=%s, login='%s', is_admin=%s, person=%s)>"\
               % (self.id, self.login, self.is_admin, self.person)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return UserAccount.__tablename__


class UIItemConfig(Base):
    """UI configuration parameters for items (area, room, device) such as css class name for icons"""

    __tablename__ = '%s_ui_item_config' % _db_prefix
    name =  Column(Unicode(30), primary_key=True)
    reference = Column(Unicode(30), primary_key=True)
    key = Column(Unicode(30), primary_key=True)
    value = Column(UnicodeText(), nullable=False)

    def __init__(self, name, reference, key, value):
        """Class constructor

        @param name : item name (ex. area)
        @param reference : item reference (ex. 2)
        @param key : key (ex. icon)
        @param value : associated value (ex. basement)

        """
        self.name = ucode(name)
        self.reference = ucode(reference)
        self.key = ucode(key)
        self.value = ucode(value)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<UIItemConfig(name='%s' reference='%s', key='%s', value='%s')>"\
               % (self.name, self.reference, self.key, self.value)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return UIItemConfig.__tablename__


class SystemInfo(Base):
    """General information about the system"""

    __tablename__ = '%s_system_info' % _db_prefix
    id = Column(Integer, primary_key=True)
    app_version = Column(Unicode(30))

    def __init__(self, app_version=None):
        """Class constructor

        @param app_version : version of the application

        """
        self.app_version = app_version

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<SystemInfo(db_version='%s')>" % (self.app_version)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return SystemInfo.__tablename__


class SystemConfig(Base):
    """Configuration parameters for the system. This object contains only one record"""

    __tablename__ = '%s_system_config' % _db_prefix
    id = Column(Integer, primary_key=True)
    simulation_mode = Column(Boolean, nullable=False, default=False)
    debug_mode = Column(Boolean, nullable=False, default=False)

    def __init__(self, simulation_mode, debug_mode):
        """Class constructor

        @param simulation_mode : if we are running the app in simulation mode
        @param admin_mode : if we are running the app in administrator mode
        @param debug_mode : if we are running the app in debug mode

        """
        self.simulation_mode = simulation_mode
        self.debug_mode = debug_mode

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<SystemConfig(id=%s, simulation=%s, debug=%s)>" % (self.id, self.simulation_mode, self.debug_mode)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return SystemConfig.__tablename__

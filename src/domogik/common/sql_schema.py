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

Plugin purpose
==============

Defines the sql schema used by Domogik

Implements
==========

- class Enum
- class Area
- class Room
- class DeviceUsage
- class DeviceTechnology
- class PluginConfig
- class DeviceType(Base):
- class Device
- class DeviceTypeFeature
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
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from exceptions import AssertionError

from sqlalchemy import types, create_engine, Table, Column, Integer, String, \
                       MetaData, ForeignKey, Boolean, DateTime, Date, Text, Unicode, UnicodeText, UniqueConstraint
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref

from domogik.common.configloader import Loader

DEVICE_TYPE_LIST = ['appliance', 'lamp', 'music', 'sensor']
DEVICE_FEATURE_ASSOCIATION_LIST = [None, 'room', 'area', 'house']
FEATURE_TYPE_LIST = ['actuator', 'sensor']
ACTUATOR_VALUE_TYPE_LIST = ['binary', 'complex', 'list', 'number', 'range', 'string', 'trigger']
SENSOR_VALUE_TYPE_LIST = ['binary', 'complex', 'number', 'string', 'trigger']

Base = declarative_base()
metadata = Base.metadata

_cfg = Loader('database')
_config = _cfg.load()
_db_prefix = dict(_config[1])['db_prefix']


class Enum(types.TypeDecorator):
    """Emulate an Enum type (see http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Enum)"""
    impl = types.Unicode

    def __init__(self, values, empty_to_none=True, strict=False):
        """Class constructor

        @param values : a list of valid values for this column
        @param empty_to_none : treat the empty string '' as None (optional default = False)
        @param strict : also insist that columns read from the database are in the
                        list of valid values.  Note that, with strict=True, you won't
                        be able to clean out bad data from the database through your
                        code. (optional default = False)

        """

        if values is None or len(values) is 0:
            raise AssertionError('Enum requires a list of values')
        self.empty_to_none = empty_to_none
        self.strict = strict
        self.values = values[:]

        # The length of the string/unicode column should be the longest string
        # in values
        size = max([len(v) for v in values if v is not None])
        super(Enum, self).__init__(size)

    def process_bind_param(self, value, dialect):
        if self.empty_to_none and value is '':
            value = None
        if value not in self.values:
            raise AssertionError('"%s" not in Enum.values' % value)
        return value

    def process_result_value(self, value, dialect):
        if self.strict and value not in self.values:
            raise AssertionError('"%s" not in Enum.values' % value)
        return value


# Define objects

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
        self.name = name
        self.description = description

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
        self.name = name
        self.description = description
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
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    default_options = Column(UnicodeText())

    def __init__(self, name, description=None, default_options=None):
        """Class constructor

        @param name : short name of the usage
        @param description : extended description, optional
        @param default_options : default options, optional

        """
        self.name = name
        self.description = description
        self.default_options = default_options

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceUsage(id=%s, name='%s', desc='%s', default opt='%s')>" \
               % (self.id, self.name, self.description, self.default_options)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceUsage.__tablename__


class DeviceTechnology(Base):
    """Technology of a device (X10, PLCBus, 1wire, RFXCOM,...)"""

    __tablename__ = '%s_device_technology' % _db_prefix
    id = Column(String(30), primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())

    def __init__(self, id, name, description=None):
        """Class constructor

        @param id : technology id (ie x10, plcbus, eibknx...) with no spaces / accents or special characters
        @param name : short name of the technology
        @param description : extended description, optional

        """
        self.id = id
        self.name = name
        self.description = description

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
    name = Column(Unicode(30), primary_key=True)
    hostname = Column(Unicode(40), primary_key=True)
    key = Column(Unicode(30), primary_key=True)
    value = Column(Unicode(255), nullable=False)

    def __init__(self, name, hostname, key, value):
        """Class constructor

        @param name : plugin name
        @param hostname : hostname the plugin is installed on
        @param key : key
        @param value : value

        """
        self.name = name
        self.hostname = hostname
        self.key = key
        self.value = value

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<PluginConfig(name=%s, hostname=%s, (%s, %s))>" % (self.name, self.hostname, self.key, self.value)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return PluginConfig.__tablename__


class DeviceType(Base):
    """Type of a device (x10.Switch, x10.Dimmer, Computer.WOL...)"""

    __tablename__ = '%s_device_type' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_technology_id = Column(Unicode(30), ForeignKey('%s.id' % \
                           DeviceTechnology.get_tablename()), nullable=False)
    device_technology = relation(DeviceTechnology)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())

    def __init__(self, name, device_technology_id, description=None):
        """Class constructor

        @param name : short name of the type
        @param description : extended description, optional
        @param device_technology_id : technology id

        """
        self.name = name
        self.description = description
        self.device_technology_id = device_technology_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceType(id=%s, name='%s', desc='%s', device techno='%s')>" \
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
    address = Column(Unicode(30), nullable=False)
    reference = Column(Unicode(30))
    device_usage_id = Column(Integer, ForeignKey('%s.id' % DeviceUsage.get_tablename()), nullable=False)
    device_usage = relation(DeviceUsage)
    device_type_id = Column(Integer, ForeignKey('%s.id' % DeviceType.get_tablename()), nullable=False)
    device_type = relation(DeviceType)
    device_stats = relation("DeviceStats", order_by="DeviceStats.date.desc()", backref=__tablename__)

    def __init__(self, name, address, reference, device_usage_id, device_type_id, description=None):
        """Class constructor

        @param name : short name of the device
        @param address : device address (like 'A3' for x10, or '01.123456789ABC' for 1wire)
        @param reference : internal reference of the device (like AM12 for a X10 device)
        @param device_usage_id : link to the device usage
        @param device_type_id : 'link to the device type (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param description : extended description, optional

        """
        self.name = name
        self.address = address
        self.reference = reference
        self.device_type_id = device_type_id
        self.device_usage_id = device_usage_id
        self.description = description

    # TODO see if following methods are still useful
    def is_lamp(self):
        """
        Check if the device is a lamp
        @return True or False
        """
        return self.type.lower() == u'lamp'

    def is_appliance(self):
        """
        Check if the device is an appliance
        @return True or False
        """
        return self.type.lower() == u'appliance'

    def get_last_value(self):
        """
        Return the last value that was recorded for the device
        @return the value
        """
        if len(self._stats) == 0:
            return self.initial_value
        else:
            return self._stats[0].value

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Device(id=%s, name='%s', addr='%s', desc='%s', ref='%s', type='%s', usage=%s)>" \
               % (self.id, self.name, self.address, self.description, self.reference, \
                  self.device_type, self.device_usage)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Device.__tablename__


class DeviceTypeFeature(Base):
    """Device type features (actuator, sensor)"""

    __tablename__ = '%s_device_type_feature' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    feature_type = Column(Enum(FEATURE_TYPE_LIST), nullable=False)
    device_type_id = Column(Integer, ForeignKey('%s.id' % DeviceType.get_tablename()), nullable=False)
    device_type = relation(DeviceType)
    parameters = Column(UnicodeText())
    value_type = Column(Unicode(30), nullable=False)
    stat_key = Column(Unicode(30))
    return_confirmation = Column(Boolean, nullable=False)

    def __init__(self, name, feature_type, device_type_id, value_type, parameters=None, stat_key=None,
                return_confirmation=False):
        """Class constructor

        @param name : device feature name (Switch, Dimmer, Thermometer, Voltmeter...)
        @param feature_type : device feature type
        @param device_type_id : device type id
        @param value_type : value type the actuator can accept / the sensor can return
        @param parameters : parameters about the command or the returned data associated to the device, optional
        @param stat_key : key reference in the core_device_stats table, optional
        @param return_confirmation : True if the device returns a confirmation after having executed a command ,optional (default False)
                                     Only relevant for actuators

        """
        self.name = name
        if feature_type != 'actuator' and feature_type != 'sensor':
            raise Exception("Feature type must me either 'actuator' or 'sensor' but NOT %s" % feature_type)
        self.feature_type = feature_type
        if self.feature_type == 'actuator' and value_type not in ACTUATOR_VALUE_TYPE_LIST:
            raise Exception("Can't add value type %s to an actuator it doesn't belong to list %s" \
                            % (value_type, ACTUATOR_VALUE_TYPE_LIST))
        elif self.feature_type == 'sensor' and value_type not in SENSOR_VALUE_TYPE_LIST:
            raise Exception("Can't add value type %s to a sensor it doesn't belong to list %s" \
                            % (value_type, SENSOR_VALUE_TYPE_LIST))
        self.device_type_id = device_type_id
        self.value_type = value_type
        self.parameters = parameters
        self.stat_key = stat_key
        self.return_confirmation = return_confirmation

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceTypeFeature(%s, %s, device_type=%s, param=%s, value_type=%s, stat_key=%s, return_conf=%s)>" \
               % (self.id, self.feature_type, self.device_type, self.parameters, self.value_type, \
                  self.stat_key, self.return_confirmation)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceTypeFeature.__tablename__


class DeviceFeatureAssociation(Base):
    """Association between devices, features and an item (room, area, house)"""

    __tablename__ = '%s_device_feature_association' % _db_prefix
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), primary_key=True)
    device = relation(Device, backref=backref(__tablename__))
    device_type_feature_id = Column(Integer, ForeignKey('%s.id' % DeviceTypeFeature.get_tablename()), primary_key=True)
    device_type_feature = relation(DeviceTypeFeature)
    place_type = Column(Enum(DEVICE_FEATURE_ASSOCIATION_LIST), nullable=True)
    place_id = Column(Integer, nullable=True)

    def __init__(self, device_id, device_type_feature_id, place_type=None, place_id=None):
        """Class constructor

        @param device_id : device id
        @param device_type_feature_id : id of device type feature
        @param place_type : room, area or house, optional (None if the feature is not associated to one of the places)
        @param place_id : place id (None if it is the house, or if the feature is not associated to one of the places)

        """
        self.device_id = device_id
        self.device_type_feature_id = device_type_feature_id
        self.place_type = place_type
        self.place_id = place_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceFeatureAssociation(%s, %s, %s, place_id=%s)>" \
               % (self.device, self.device_type_feature, self.place_type, self.place_id)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceFeatureAssociation.__tablename__


class DeviceConfig(Base):
    """Device configuration"""

    __tablename__ = '%s_device_config' % _db_prefix
    key = Column(String(30), primary_key=True)
    value = Column(Unicode(255), nullable=False)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), primary_key=True)
    device = relation(Device)

    def __init__(self, key, device_id, value):
        """Class constructor

        @param key : configuration item
        @param value : configuration value
        @param device_id : device id

        """
        self.key = key
        self.value = value
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
    date = Column(TIMESTAMP, primary_key=True)
    key = Column(Unicode(30), primary_key=True)
    value = Column(Unicode(255), nullable=False)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), nullable=False, primary_key=True)
    device = relation(Device)

    def __init__(self, date, key, value, device_id):
        """Class constructor

        @param device_id : device id
        @param date : timestamp when the stat was recorded
        @param key : key
        @param value : value

        """
        self.date = date
        self.key = key
        self.value = value
        self.device_id = device_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceStats(date='%s', (%s, %s), device=%s)>" % (self.date, self.key, self.value, self.device)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return DeviceStats.__tablename__


class Trigger(Base):
    """Trigger : execute commands when conditions are met"""

    __tablename__ = '%s_trigger' % _db_prefix
    id = Column(Integer, primary_key=True)
    description = Column(UnicodeText())
    rule = Column(Text, nullable=False)
    result = Column(Text, nullable=False)

    def __init__(self, rule, result, description=None):
        """Class constructor

        @param rule : formatted trigger rule
        @param result : list of xpl message to send when the rule is met
        @param description : long description of the rule, optional

        """
        self.rule = rule
        self.result = result
        self.description = description

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Trigger(id=%s, desc='%s', rule='%s', result='%s')>" \
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

    def __init__(self, first_name, last_name, birthdate):
        """Class constructor

        @param first_name : first name
        @param last_name : last name
        @param birthdate : birthdate

        """
        self.first_name = first_name
        self.last_name = last_name
        self.birthdate = birthdate

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Person(id=%s, first_name='%s', last_name='%s', birthdate='%s')>" \
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
    password = Column(Unicode(255), nullable=False)
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
        self.login = login
        self.password = password
        self.person_id = person_id
        self.is_admin = is_admin
        self.skin_used = skin_used

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<UserAccount(id=%s, login='%s', is_admin=%s, person=%s)>" \
                % (self.id, self.login, self.is_admin, self.person)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return UserAccount.__tablename__


class SystemStats(Base):
    """Statistics for the system"""

    __tablename__ = '%s_system_stats' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    hostname = Column(Unicode(40), nullable=False)
    date = Column(DateTime, nullable=False)

    def __init__(self, plugin_name, host_name, date):
        """Class constructor

        @param plugin_name : plugin name
        @param host_name : host name
        @param date : datetime when the statistic was recorded

        """
        self.name = plugin_name
        self.hostname = host_name
        self.date = date

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<SystemStats(id=%s, plugin_name=%s, host_name=%s, date=%s)>" % (self.id, self.name, self.hostname, self.date)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return SystemStats.__tablename__


class SystemStatsValue(Base):
    """Value(s) associated to a system statistic"""

    __tablename__ = '%s_system_stats_value' % _db_prefix
    id = Column(Integer, primary_key=True)
    system_stats_id = Column(Integer, ForeignKey('%s.id' % SystemStats.get_tablename()), nullable=False)
    system_stats = relation(SystemStats)
    name = Column(Unicode(30), nullable=False)
    value = Column(Unicode(255), nullable=False)

    def __init__(self, name, value, system_stats_id):
        """Class constructor

        @param name : value name
        @param value : value
        @param system_stats_id : statistic id

        """
        self.name = name
        self.value = value
        self.system_stats_id = system_stats_id

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<SystemStatsValue(id=%s, name=%s, value=%s, stat_id=%s)>" % (self.id, self.name, self.value, self.system_stats)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return SystemStatsValue.__tablename__


class UIItemConfig(Base):
    """UI configuration parameters for items (area, room, device) such as css class name for icons"""

    __tablename__ = '%s_ui_item_config' % _db_prefix
    name =  Column(Unicode(30), primary_key=True)
    reference = Column(Unicode(30), primary_key=True)
    key = Column(Unicode(30), primary_key=True)
    value = Column(Unicode(255), nullable=False)

    def __init__(self, name, reference, key, value):
        """Class constructor

        @param name : item name (ex. area)
        @param reference : item reference (ex. 2)
        @param key : key (ex. icon)
        @param value : associated value (ex. basement)

        """
        self.name = name
        self.reference = reference
        self.key = key
        self.value = value

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<UIItemConfig(name='%s' reference='%s', key='%s', value='%s')>" % (self.name, self.reference, self.key, self.value)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return UIItemConfig.__tablename__


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

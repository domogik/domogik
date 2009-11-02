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

Defines the sql schema used by Domogik

Implements
==========

- class Enum(types.TypeDecorator) : enum stuff for sqlAlchemy
- class Area(Base) : areas of the house (1st floor, ground...)
- class Room(Base) : rooms of the house
- class Deviceategory(Base) : temperature, lighting, heating, music...
- class DeviceTechnology(Base) : cpl, wired, wireless, wifi, ir...
- class DeviceTechnologyConfig(Base) : list of parameters for the device technology
- class Device(Base) : devices which are manages by the automation system
- class DeviceConfig(Base) : list of parameters for the device
- class DeviceStats(Base) : statistics associated to the device (history of values stored)
- class Trigger(Base) : to trigger an action when a condition is met
- class SystemAccount(Base) : accounts to log into the app
- class UserAccount(Base) : users

@author: Marc SCHNEIDER <marc@domogik.org>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from exceptions import AssertionError

from sqlalchemy import types, create_engine, Table, Column, Integer, String, \
      MetaData, ForeignKey, Boolean, DateTime, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref

from domogik.common.configloader import Loader

UNIT_OF_STORED_VALUE_LIST = [u'Volt', u'Celsius', u'Farenheit', u'Percent', u'Boolean', None]
DEVICE_TECHNOLOGY_LIST = [u'x10',u'1wire',u'PLCBus',u'RFXCom',u'IR',u'EIB/KNX']
DEVICE_TECHNOLOGY_TYPE_LIST = [u'cpl', u'wired', u'wifi', u'wireless', u'ir']
DEVICE_TYPE_LIST = [u'appliance', u'lamp', u'music', u'sensor']
ITEM_TYPE_LIST = [u'area', u'room', u'device'] 

Base = declarative_base()
metadata = Base.metadata

_cfg = Loader('database')
_config = _cfg.load()
_db_prefix = dict(_config[1])['db_prefix']


class Enum(types.TypeDecorator):
    """
    Emulate an Enum type (see http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Enum)
    """
    impl = types.Unicode

    def __init__(self, values, empty_to_none=False, strict=False):
        """
        Class constructor
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
    """
    Area : it is something like "first floor", "garden", etc ...
    """
    __tablename__ = '%s_area' % _db_prefix

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    description = Column(String(255))

    def __init__(self, name, description):
        """
        Class constructor
        @param name : short name of the area
        @param description : extended description
        """
        self.name = name
        self.description = description

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<Area(id=%s, name='%s', desc='%s')>" % (self.id, self.name, self.description)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return Area.__tablename__


class Room(Base):
    """
    Room
    """
    __tablename__ = '%s_room' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    description = Column(String(255))
    area_id = Column(Integer, ForeignKey('%s.id' % Area.get_tablename()), nullable=False)
    area = relation(Area, backref=backref(__tablename__, order_by=id))

    def __init__(self, name, description, area_id):
        """
        Class constructor
        @param name : short name of the area
        @param description : extended description
        @param area_id : id of the area where the room is
        """
        self.name = name
        self.description = description
        self.area_id = area_id

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<Room(id=%s, name='%s', desc='%s', area=%s)>" \
          % (self.id, self.name, self.description, self.area_id)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return Room.__tablename__


class DeviceCategory(Base):
    """
    Category of a device (temperature, heating, lighting, music...)
    """
    __tablename__ = '%s_device_category' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    description = Column(String(255))

    def __init__(self, name, description):
        """
        Class constructor
        @param name : short name of the category
        @param description : extended description
        """
        self.name = name
        self.description = description

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<DeviceCategory(id=%s, name='%s', desc='%s')>" % (self.id, self.name, self.description)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return DeviceCategory.__tablename__


class DeviceTechnology(Base):
    """
    Technology of a device (X10, PLCBus, 1wire, RFXCOM,...)
    """
    __tablename__ = '%s_device_technology' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(Enum(DEVICE_TECHNOLOGY_LIST), nullable=False)
    description = Column(String(255))
    type = Column(Enum(DEVICE_TECHNOLOGY_TYPE_LIST))

    def __init__(self, name, description, type):
        """
        Class constructor
        @param name : short name of the technology
        @param description : extended description
        @param type : cpl (power lines), wired (ex. 1wire), wifi, 
        @param wireless (RF based, for example RFXCOM), ir (infrared)
        """
        self.name = name
        self.description = description
        self.type = type

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<DeviceTechnology(id=%s, name='%s', desc='%s', type='%s')>" \
          % (self.id, self.name, self.description, self.type)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return DeviceTechnology.__tablename__


class DeviceTechnologyConfig(Base):
    """
    Configuration for device technology
    """
    __tablename__ = '%s_device_technology_config' % _db_prefix
    id = Column(Integer, primary_key=True)
    technology_id = Column(Integer, ForeignKey('%s.id' % DeviceTechnology.get_tablename()), nullable=False)
    technology = relation(DeviceTechnology, backref=backref(__tablename__))
    key = Column(String(30), nullable=False)
    value = Column(String(80), nullable=False)
    description = Column(String(255), nullable=True)

    def __init__(self, technology_id, key, value):
        """
        Class constructor
        @param technology_id : link to the device technology
        @param key : configuration item
        @param value : configuration value
        """
        self.technology_id = technology_id
        self.key = key
        self.value = value

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<DeviceTechnologyConfig(id=%s, techno=%s, ('%s', '%s'))>" \
          % (self.id, self.technology_id, self.key, self.value)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return DeviceTechnologyConfig.__tablename__


class Device(Base):
    """
    Device
    """
    __tablename__ = '%s_device' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    description = Column(String(255))
    address = Column(String(30), nullable=False)
    reference = Column(String(30))
    technology_id = Column(Integer, ForeignKey('%s.id' % DeviceTechnology.get_tablename()), nullable=False)
    technology = relation(DeviceTechnology, backref=backref(__tablename__))
    type = Column(Enum(DEVICE_TYPE_LIST))
    category_id = Column(Integer, ForeignKey('%s.id' % DeviceCategory.get_tablename()), nullable=False)
    category = relation(DeviceCategory, backref=backref(__tablename__))
    room_id = Column(Integer, ForeignKey('%s.id' % Room.get_tablename()))
    room = relation(Room, backref=backref(__tablename__))
    is_resetable = Column(Boolean, nullable=False)
    initial_value = Column(String(10))
    is_value_changeable_by_user = Column(Boolean, nullable=False)
    unit_of_stored_values = Column(Enum(UNIT_OF_STORED_VALUE_LIST))
    _stats = relation("DeviceStats", order_by="DeviceStats.date.desc()", backref=__tablename__)

    def __init__(self, name, address, description, reference, technology_id, type, category_id, room_id, \
        is_resetable, initial_value, is_value_changeable_by_user, unit_of_stored_values):
        """
        Class constructor
        @param name : short name of the device
        @param description : extended description
        @param address : device address (like 'A3' for x10, or '01.123456789ABC' for 1wire)
        @param reference : internal reference of the device (like AM12 for a X10 device)
        @param technology_id : link to the device technology
        @param type : 'appliance', 'lamp', 'music'
        @param category_id : link to the device category
        @param room_id : link to the room where the device is
        @param is_resetable : True if a default value can be set to the device
        @param initial_value : initial value set to the device when it is switched on
        @param is_value_changeable_by_user : True if the user can set a value to the device
        @param unit_of_stored_values : unit associated to the value (Volt, Celsius, Farenheit, Percent, Boolean)
        """
        self.name = name
        self.address = address
        self.description = description
        self.reference = reference
        self.technology_id = technology_id
        self.type = type
        self.category_id = category_id
        self.room_id = room_id
        self.is_resetable = is_resetable
        self.initial_value = initial_value
        self.is_value_changeable_by_user = is_value_changeable_by_user
        self.unit_of_stored_values = unit_of_stored_values

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
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<Device(id=%s, name='%s', addr='%s', desc='%s', ref='%s', techno=%s, type='%s', cat=%s, \
          room=%s, is_reset='%s', initial_val='%s', is_value_change='%s', unit='%s')>" \
          % (self.id, self.name, self.address, self.description, self.reference, self.technology_id, \
             self.type, self.category_id, self.room_id, self.is_resetable, self.initial_value,\
             self.is_value_changeable_by_user, self.unit_of_stored_values)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return Device.__tablename__


class DeviceConfig(Base):
    """
    Device configuration
    """
    __tablename__ = '%s_device_config' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), nullable=False)
    device = relation(Device, backref=backref(__tablename__))
    key = Column(String(30), nullable=False)
    value = Column(String(80), nullable=False)
    description = Column(String(255), nullable=True)

    def __init__(self, device_id, key, value):
        """
        Class constructor
        @param device_id : device id
        @param key : configuration item
        @param value : configuration value
        """
        self.device_id = device_id
        self.key = key
        self.value = value

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<DeviceConfig(id=%s, device=%s, ('%s', '%s'))>" \
          % (self.id, self.device_id, self.key, self.value)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return DeviceConfig.__tablename__


class DeviceStats(Base):
    """
    Device stats (values that were associated to the device)
    """
    __tablename__ = '%s_device_stats' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename()), nullable=False)
    device = relation(Device, backref=backref(__tablename__))
    date = Column(DateTime, nullable=False)

    def __init__(self, device_id, date):
        """
        Class constructor
        @param device_id : device id
        @param date : datetime when the stat was recorded
        """
        self.device_id = device_id
        self.date = date

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<DeviceStats(id=%s, device=%s, date='%s')>" \
          % (self.id, self.device_id, self.date)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return DeviceStats.__tablename__


class DeviceStatsValue(Base):
    """
    Value(s) associated to a device statistic
    """
    __tablename__ = '%s_device_stats_value' % _db_prefix
    id = Column(Integer, primary_key=True)
    device_stats_id = Column(Integer, ForeignKey('%s.id' % DeviceStats.get_tablename()), nullable=False)
    name = Column(String(30), nullable=False)
    value = Column(String(80), nullable=False)

    def __init__(self, name, value, device_stats_id):
        """
        Class constructor
        @param name : value name
        @param value : value
        @param device_stats_id : id of the device statistic
        """
        self.name = name
        self.value = value
        self.device_stats_id = device_stats_id

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<DeviceStatsValue(id=%s, name=%s, value=%s, stat_id=%s)>" \
          % (self.id, self.name, self.value, self.device_stats_id)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return DeviceStatsValue.__tablename__


class Trigger(Base):
    """
    Trigger : execute commands when conditions are met
    """
    __tablename__ = '%s_trigger' % _db_prefix
    id = Column(Integer, primary_key=True)
    description = Column(String(255))
    rule = Column(Text, nullable=False)
    result = Column(Text, nullable=False)

    def __init__(self, description, rule, result):
        """
        Class constructor
        @param description : long description of the rule
        @param rule : formatted trigger rule
        @param result : list of xpl message to send when the rule is met
        """
        self.description = description
        self.rule = rule
        self.result = result

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<Trigger(id=%s, desc='%s', rule='%s', result='%s')>" \
          % (self.id, self.description, self.rule, self.result)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return Trigger.__tablename__


class SystemAccount(Base):
    """
    System account for users : it is only used by the UI
    """
    __tablename__ = '%s_system_account' % _db_prefix
    id = Column(Integer, primary_key=True)
    login = Column(String(20), nullable=False)
    password = Column(Text, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    skin_used = Column(String(80), nullable=False)

    def __init__(self, login, password, is_admin, skin_used):
        """
        Class constructor
        @param login : login
        @param password : password
        @param is_admin : True if the user has administrator privileges
        @param skin_used : skin used in the UI (default value = 'default')
        """
        self.login = login
        self.password = password
        self.is_admin = is_admin
        self.skin_used = skin_used

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<SystemAccount(id=%s, login='%s', pass='%s' is_admin='%s')>" \
          % (self.id, self.login, self. password, self.is_admin)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return SystemAccount.__tablename__


class UserAccount(Base):
    """
    Personnal information of the user
    """
    __tablename__ = '%s_user_account' % _db_prefix
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(60), nullable=False)
    birthdate = Column(Date, nullable=False)
    system_account_id = Column(Integer, ForeignKey('%s.id' % SystemAccount.get_tablename()))
    system_account = relation(SystemAccount, backref=backref(__tablename__))

    def __init__(self, first_name, last_name, birthdate, system_account_id):
        """
        Class constructor
        @param first_name : first name
        @param last_name : last name
        @param birthdate : birthdate
        @param system_account_id : link to the system account (optional)
        """
        self.first_name = first_name
        self.last_name = last_name
        self.birthdate = birthdate
        self.system_account_id = system_account_id

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<UserAccount(id=%s, first_name='%s', last_name='%s', system_account=%s)>" \
          % (self.id, self.first_name, self.last_name, self.system_account_id)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return UserAccount.__tablename__


class SystemStats(Base):
    """
    Statistics for the system
    """
    __tablename__ = '%s_system_stats' % _db_prefix
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    hostname = Column(String(40), nullable=False)
    date = Column(DateTime, nullable=False)

    def __init__(self, module_name, host_name, date):
        """
        Class constructor
        @param module_name : module name
        @param host_name : host name
        @param date : datetime when the statistic was recorded
        """
        self.name = module_name
        self.hostname = host_name
        self.date = date

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<SystemStats(id=%s, module_name=%s, host_name=%s, date=%s)>" \
          % (self.id, self.name, self.hostname, self.date)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return SystemStats.__tablename__


class SystemStatsValue(Base):
    """
    Value(s) associated to a system statistic
    """
    __tablename__ = '%s_system_stats_value' % _db_prefix
    id = Column(Integer, primary_key=True)
    system_stats_id = Column(Integer, ForeignKey('%s.id' % SystemStats.get_tablename()), nullable=False)
    name = Column(String(30), nullable=False)
    value = Column(String(80), nullable=False)

    def __init__(self, name, value, system_stats_id):
        """
        Class constructor
        @param name : value name
        @param value : value
        @param system_stats_id : statistic id
        """
        self.name = name
        self.value = value
        self.system_stats_id = system_stats_id

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<SystemStatsValue(id=%s, name=%s, value=%s, stat_id=%s)>" \
          % (self.id, self.name, self.value, self.system_stats_id)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return SystemStatsValue.__tablename__


class ItemUIConfig(Base):
    """
    UI configuration parameters for items (area, room, device) such as class name for icons
    """
    __tablename__ = '%s_item_ui_config' % _db_prefix

    item_id = Column(Integer, primary_key=True)
    item_type = Column(Enum(ITEM_TYPE_LIST), nullable=False, primary_key=True)
    key = Column(String(30), nullable=False, primary_key=True)
    value = Column(String(30), nullable=False)

    def __init__(self, item_id, item_type, key, value):
        """
        Class constructor
        @param item_id : reference to the item id (area id, room id or device_id)
        @param item_type : area, room, device
        @param key : key
        @param value : associated value
        """
        self.item_id = item_id
        self.item_type = item_type
        self.key = key
        self.value = value

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<ItemUIConfig(id=%s, item_type='%s', key='%s', value='%s')>" \
                % (self.item_id, self.item_type, self.key, self.value)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return ItemUIConfig.__tablename__


class SystemConfig(Base):
    """
    Configuration parameters for the system. This object contains only one record
    """
    __tablename__ = '%s_system_config' % _db_prefix
    id = Column(Integer, primary_key=True)
    simulation_mode = Column(Boolean, nullable=False, default=False)
    debug_mode = Column(Boolean, nullable=False, default=False)

    def __init__(self, simulation_mode, debug_mode):
        """
        Class constructor
        @param simulation_mode : if we are running the app in simulation mode
        @param admin_mode : if we are running the app in administrator mode
        @param debug_mode : if we are running the app in debug mode
        """
        self.simulation_mode = simulation_mode
        self.debug_mode = debug_mode

    def __repr__(self):
        """
        Print an internal representation of the class
        @return an internal representation
        """
        return "<SystemConfig(id=%s, simulation=%s, debug=%s)>" \
          % (self.id, self.simulation_mode, self.debug_mode)

    @staticmethod
    def get_tablename():
        """
        Return the table name associated to the class
        @return table name
        """
        return SystemConfig.__tablename__

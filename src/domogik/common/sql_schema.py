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

- class DeviceUsage
- class DeviceTechnology
- class PluginConfig
- class DeviceType
- class Device
- class DeviceFeature
- class DeviceStats
- class Person
- class UserAccount

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

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

- class PluginConfig
- class Device
- class DeviceStats
- class Person
- class UserAccount

@author: Marc SCHNEIDER <marc@domogik.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import time, sys
#from exceptions import AssertionError

from sqlalchemy import (
        types, create_engine, Table, Column, Index, Integer, Float, String, Enum,
        MetaData, ForeignKey, Boolean, DateTime, Date, Text,
        Unicode, UnicodeText, UniqueConstraint
)
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref, relationship

from domogik.common.utils import ucode
from domogik.common.configloader import Loader

Base = declarative_base()
metadata = Base.metadata

_cfg = Loader('database')
_config = None
# TODO : if no need
#if len(sys.argv) > 1:
#    _config = _cfg.load(sys.argv[1])
#else:
_config = _cfg.load()
_db_prefix = dict(_config[1])['prefix']

# Define objects
class PluginConfig(Base):
    """Configuration for a plugin (x10, plcbus, ...)"""

    __tablename__ = '%s_plugin_config' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Unicode(30), primary_key=True)
    hostname = Column(Unicode(40), primary_key=True)
    key = Column(Unicode(255), primary_key=True)
    value = Column(UnicodeText(), nullable=False)

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

class Device(Base):
    """Device"""

    __tablename__ = '%s_device' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(30), nullable=False)
    description = Column(UnicodeText())
    reference = Column(Unicode(30))
    address = Column(Unicode(255), nullable=True)
    device_type_id = Column(Unicode(80), nullable=False, index=True)
    client_id = Column(Unicode(80), nullable=False)
    client_version = Column(Unicode(32), nullable=False)
    params = relationship("DeviceParam", backref=__tablename__, cascade="all", passive_deletes=True)
    commands = relationship("Command", backref=__tablename__, cascade="all", passive_deletes=True)
    sensors = relationship("Sensor", backref=__tablename__, cascade="all", passive_deletes=True)
    xpl_commands = relationship("XplCommand", backref=__tablename__, cascade="all", passive_deletes=True)
    xpl_stats = relationship("XplStat", backref=__tablename__, cascade="all", passive_deletes=True)

    def __init__(self, name, reference, device_type_id, client_id, client_version, description=None):
        """Class constructor

        @param name : short name of the device
        @param address : device address (like 'A3' for x10, or '01.123456789ABC' for 1wire)
        @param reference : internal reference of the device (like AM12 for a X10 device)
        @param client_id : what plugin controls this device
        @param device_type_id : 'link to the device type (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param description : extended description, optional

        """
        self.name = ucode(name)
        self.reference = ucode(reference)
        self.device_type_id = ucode(device_type_id)
        self.client_id = ucode(client_id)
        self.client_version = ucode(client_version)
        self.description = ucode(description)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Device(id=%s, name='%s', desc='%s', ref='%s', type='%s', client='%s', client_version='%s', commands=%s, sensors=%s, xplcommands=%s, xplstats=%s)>"\
               % (self.id, self.name, self.description, self.reference,\
                  self.device_type_id, self.client_id, self.client_version, \
                  self.commands, \
                  self.sensors, self.xpl_commands, self.xpl_stats)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Device.__tablename__

class DeviceParam(Base):
    """Device config, some config parameters that are only accessable over the mq, or inside domogik, these have nothin todo with xpl"""

    __tablename__ = '%s_device_param' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename(), ondelete="cascade"), nullable=False)
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255), nullable=True)
    type = Column(Unicode(32), nullable=True)

    def __init__(self, device_id, key, value, type):
        """Class constructor

        @param device_id : The device where this parameter is linked to 
        @param key : The param name
        @param value : The param value
        @param type : The type param
        """
        self.device_id = device_id
        self.key = ucode(key)
        self.value = ucode(value)
        self.type = ucode(type)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<DeviceParam(id={0}, device_id={1}, key='{2}', value='{3}', type='{4}')>"\
               .format(self.id, self.device_id, self.key, self.value, self.type)\

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Device.__tablename__

class DeviceStats(Base):
    """Device stats (values that were associated to the device)"""

    __tablename__ = '%s_device_stats' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
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
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(20), nullable=False)
    last_name = Column(Unicode(20), nullable=False)
    birthdate = Column(Date)
    user_accounts = relation("UserAccount", backref=__tablename__, cascade="all")

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
    __table_args__ = {'mysql_engine':'InnoDB'}
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
   # Flask-Login integration
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return self.id
    # Required for administrative interface
    def __unicode__(self):
        return self.login


    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return UserAccount.__tablename__

class Command(Base):
    __tablename__ = '%s_command' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True) 
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename(), ondelete="cascade"), nullable=False)
    name = Column(Unicode(255), nullable=False)
    reference = Column(Unicode(64))
    return_confirmation = Column(Boolean, nullable=False)
    xpl_command = relation("XplCommand", backref=__tablename__, cascade="all", uselist=False)
    params = relationship("CommandParam", backref=__tablename__, cascade="all", passive_deletes=True)

    def __init__(self, device_id, name, reference, return_confirmation):
        self.device_id = device_id
        self.name = ucode(name)
        self.return_confirmation = return_confirmation
        self.reference = ucode(reference)
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Command(id=%s device_id=%s reference='%s' name='%s' return_confirmation=%s params=%s xpl_command=%s)>"\
               % (self.id, self.device_id, self.reference, self.name, self.return_confirmation, self.params, self.xpl_command)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Command.__tablename__

class CommandParam(Base):
    __tablename__ = '%s_command_param' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    cmd_id = Column(Integer, ForeignKey('%s.id' % Command.get_tablename(), ondelete="cascade"), primary_key=True, nullable=False, autoincrement=False) 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement='ignore_fk')
    data_type = Column(Unicode(32), nullable=False)
    conversion = Column(Unicode(255), nullable=True)
    UniqueConstraint('cmd_id', 'key', name='uix_1')

    def __init__(self, cmd_id, key, data_type, conversion):
        self.cmd_id = cmd_id
        self.key = ucode(key)
        self.data_type = ucode(data_type)
        self.conversion = ucode(conversion)
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<CommandParam(cmd_id=%s key='%s' data_type='%s' conversion='%s')>"\
               % (self.cmd_id, self.key, self.data_type, self.conversion)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return CommandParams.__tablename__

class Sensor(Base):
    __tablename__ = '%s_sensor' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True) 
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename(), ondelete="cascade"), nullable=False)
    name = Column(Unicode(255))
    reference = Column(Unicode(64))
    type = Column(Unicode(32), nullable=False)
    data_type = Column(Unicode(32), nullable=False)
    conversion = Column(Unicode(255), nullable=True)
    last_value = Column(Unicode(32), nullable=True)
    last_received = Column(Integer, nullable=True)
    history_store = Column(Boolean, nullable=False)
    history_max = Column(Integer, nullable=True)
    history_expire = Column(Integer, nullable=True)
    history_round = Column(Float, nullable=True)

    def __init__(self, device_id, name, reference, type, data_type, conversion, h_store, h_max, h_expire, h_round):
        self.device_id = device_id
        self.name = ucode(name)
        self.reference = ucode(reference)
        self.type = ucode(type)
        self.data_type = ucode(data_type)
        self.conversion = ucode(conversion)
        self.history_store = h_store
        self.history_max = h_max
        self.history_expire = h_expire
        self.history_round = h_round
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Sensor(id=%s device_id=%s reference='%s' type='%s' name='%s' data_type='%s' conversion='%s' h_store=%s h_max=%s h_expire=%s h_round=%s)>"\
               % (self.id, self.device_id, self.reference, self.type, self.name, self.data_type, self.conversion, \
                   self.history_store, self.history_max, self.history_expire, self.history_round)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Sensor.__tablename__

class SensorHistory(Base):
    __tablename__ = '%s_sensor_history' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True) 
    sensor_id = Column(Integer, ForeignKey('%s.id' % Sensor.get_tablename(), ondelete="cascade"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    value_num = Column(Float, nullable=True)
    value_str = Column(Unicode(32), nullable=False)
    original_value_num = Column(Float, nullable=True)

    def __init__(self, sensor_id, date, value, orig_value):
        self.sensor_id = sensor_id
        self.date = date
        try:
            self.value_num = float(value)
            self.original_value_num = float(orig_value)
        except ValueError:
            pass
        except TypeError:
            pass
        self.value_str = ucode(value)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<SensorHistory(sensor_id=%s date=%s value_str='%s' value_num=%s orig_value_num=%s)>"\
               % (self.sensor_id, self.date, self.value_str, self.value_num, self.original_value_num)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return SensorHistory.__tablename__

class XplStat(Base):
    __tablename__ = '%s_xplstat' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename(), ondelete="cascade"), nullable=False)
    json_id = Column(Unicode(64), nullable=False)
    name = Column(Unicode(64), nullable=False)
    schema = Column(Unicode(32), nullable=False)
    params = relationship("XplStatParam", backref=__tablename__, cascade="all", passive_deletes=True)
    
    def __init__(self, device_id, name, schema, json_id):
        self.device_id = device_id
        self.name = ucode(name)
        self.schema = ucode(schema)
        self.json_id = ucode(json_id)
   
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<XplStat(id=%s device_id=%s name='%s' schema='%s' params=%s json_id=%s)>"\
               % (self.id, self.device_id, self.name, self.schema, self.params, self.json_id)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplStat.__tablename__


class XplStatParam(Base):
    __tablename__ = '%s_xplstat_param' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    xplstat_id = Column(Integer, ForeignKey('%s.id' % XplStat.get_tablename(), ondelete="cascade"), primary_key=True, nullable=False, autoincrement=False) 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255), nullable=True)
    static = Column(Boolean, nullable=True)
    sensor_id = Column(Integer, ForeignKey('%s.id' % Sensor.get_tablename(), ondelete="cascade"), nullable=True) 
    ignore_values = Column(Unicode(255), nullable=True)
    type = Column(Unicode(32), nullable=True)
    UniqueConstraint('xplstat_id', 'key', name='uix_1')

    def __init__(self, xplstat_id, key, value, static, sensor_id, ignore_values, type):
        self.xplstat_id = xplstat_id
        self.key = ucode(key)
        self.value = ucode(value)
        self.static = static
        self.sensor_id = sensor_id
        self.ignore_values = ucode(ignore_values)
        self.type = ucode(type)
    
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<XplStatParam(stat_id=%s key='%s' value='%s' static=%s sensor_id=%s ignore='%s' type='%s')>"\
               % (self.xplstat_id, self.key, self.value, self.static, self.sensor_id, self.ignore_values, self.type)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplStatParam.__tablename__


class XplCommand(Base):
    __tablename__ = '%s_xplcommand' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('%s.id' % Device.get_tablename(), ondelete="cascade"), nullable=False)
    cmd_id = Column(Integer, ForeignKey('%s.id' % Command.get_tablename(), ondelete="cascade"), nullable=False)
    json_id = Column(Unicode(64), nullable=False)
    name = Column(Unicode(64), nullable=False)
    schema = Column(Unicode(32), nullable=False)
    stat_id = Column(Integer, ForeignKey('%s.id' % XplStat.get_tablename(), ondelete="cascade"), nullable=True)
    stat = relation("XplStat", backref=__tablename__, cascade="all")
    params = relationship("XplCommandParam", backref=__tablename__, cascade="all", passive_deletes=True)

    def __init__(self, name, device_id, cmd_id, json_id, schema, stat_id):
        self.name = ucode(name)
        self.device_id = device_id
        self.cmd_id = cmd_id
        self.schema = ucode(schema)
        self.stat_id = stat_id
        self.json_id = json_id
    
    def __repr__(self):
       """Return an internal representation of the class"""
       return "<XplCommand(id=%s device_id=%s cmd_id=%s name='%s' json_id='%s' schema='%s' stat=%s params=%s)>"\
               % (self.id, self.device_id, self.cmd_id, self.name, self.json_id, self.schema, self.stat, self.params)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplCommand.__tablename__


class XplCommandParam(Base):
    __tablename__ = '%s_xplcommand_param' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    xplcmd_id = Column(Integer, ForeignKey('%s.id' % XplCommand.get_tablename(), ondelete="cascade"), primary_key=True, nullable=False, autoincrement=False) 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255))
    UniqueConstraint('xplcmd_id', 'key', name='uix_1')

    def __init__(self, cmd_id, key, value):
        self.xplcmd_id = cmd_id
        self.key = ucode(key)
        self.value = ucode(value)
    
    def __repr__(self):
        """Return an internal representation of the class"""
        return "<XplCommandParam(cmd_id=%s key='%s' value='%s')>"\
               % (self.xplcmd_id, self.key, self.value)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return XplCommandParam.__tablename__

class Scenario(Base):
    __tablename__ = '%s_scenario' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(Unicode(32), nullable=False, autoincrement=False)
    json = Column(UnicodeText(), nullable=False)
    uuids = relationship("ScenarioUUID", backref=__tablename__, cascade="all", passive_deletes=True)

    def __init__(self, name, json):
        self.name = ucode(name)
        self.json = ucode(json)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<Scenario(id=%s name='%s' json='%s' uuids=%s)>"\
               % (self.id, self.name, self.json, self.uuids)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return Scenario.__tablename__

class ScenarioUUID(Base):
    __tablename__ = '%s_scenario_uuid' % _db_prefix
    __table_args__ = {'mysql_engine':'InnoDB'}
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    scenario_id = Column(Integer, ForeignKey('%s.id' % Scenario.get_tablename(), ondelete="cascade"), primary_key=True, nullable=False)
    uuid = Column(Unicode(128), nullable=False, autoincrement=False)
    key = Column(UnicodeText(), nullable=False)
    is_test = Column(Boolean, nullable=False, default=False)
    UniqueConstraint('uuid', name='uuid')

    def __init__(self, s_id, uuid, key, is_test):
        self.scenario_id = s_id
        self.uuid = ucode(uuid)
        self.key = ucode(key)
        self.is_test = is_test

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<ScenarioUUID(id=%s scenario_id=%s name='%s' json='%s' is_test=%s)>"\
               % (self.id, self.scenario_id, self.uuid, self.key, self.is_test)

    @staticmethod
    def get_tablename():
        """Return the table name associated to the class"""
        return ScenarioUUID.__tablename__


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

_cfg = Loader('database')
_config = None
# TODO : if no need
#if len(sys.argv) > 1:
#    _config = _cfg.load(sys.argv[1])
#else:
_config = _cfg.load()
_db_prefix = dict(_config[1])['prefix']

class RepresentableBase(object):
    def __repr__(self):
        items = ("{0}='{1}'".format(k, v) for k, v in self.__dict__.items() if not k.startswith('_'))
        return "<{0}: {1}>".format(self.__class__.__name__, ', '.join(items))
    
    @classmethod
    def get_tablename(self):
        return self.__tablename__

DomogikBase = declarative_base(cls=RepresentableBase)
metadata = DomogikBase.metadata

# Define objects
class PluginConfig(DomogikBase):
    """Configuration for a plugin (x10, plcbus, ...)"""

    __tablename__ = '{0}_plugin_config'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Unicode(30), primary_key=True)
    type = Column(Unicode(30), primary_key=True, default=u'plugin')
    hostname = Column(Unicode(40), primary_key=True)
    key = Column(Unicode(255), primary_key=True)
    value = Column(UnicodeText(), nullable=False)

    def __init__(self, id, type, hostname, key, value):
        """Class constructor

        @param id : plugin id
        @param hostname : hostname the plugin is installed on
        @param key : key
        @param value : value

        """
        self.id = ucode(id)
        self.type = ucode(type)
        self.hostname = ucode(hostname)
        self.key = ucode(key)
        self.value = ucode(value)

class Device(DomogikBase):
    """Device"""

    __tablename__ = '{0}_device'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(Unicode(128), nullable=False)
    description = Column(UnicodeText())
    reference = Column(Unicode(30))
    device_type_id = Column(Unicode(255), nullable=False, index=True)
    client_id = Column(Unicode(80), nullable=False, index=True)
    client_version = Column(Unicode(32), nullable=False)
    info_changed = Column(DateTime, nullable=False, index=True)
    state = Column(Unicode(30), nullable=False, index=True, default=u'active')
    params = relationship("DeviceParam", backref=__tablename__, cascade="all", passive_deletes=True)
    commands = relationship("Command", backref=__tablename__, cascade="all", passive_deletes=True)
    sensors = relationship("Sensor", backref=__tablename__, cascade="all", passive_deletes=True)
    xpl_commands = relationship("XplCommand", backref=__tablename__, cascade="all", passive_deletes=True)
    xpl_stats = relationship("XplStat", backref=__tablename__, cascade="all", passive_deletes=True)

    def __init__(self, name, reference, device_type_id, client_id, client_version, description=None, info_changed=None, state='active'):
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
        self.info_changed = info_changed

class DeviceParam(DomogikBase):
    """Device config, some config parameters that are only accessable over the mq, or inside domogik, these have nothin todo with xpl"""

    __tablename__ = '{0}_device_param'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey('{0}.id'.format(Device.get_tablename()), ondelete="cascade"), nullable=False)
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

class Command(DomogikBase):
    __tablename__ = '{0}_command'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False) 
    device_id = Column(Integer, ForeignKey('{0}.id'.format(Device.get_tablename()), ondelete="cascade"), nullable=False)
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

class CommandParam(DomogikBase):
    __tablename__ = '{0}_command_param'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    cmd_id = Column(Integer, ForeignKey('{0}.id'.format(Command.get_tablename()), ondelete="cascade"), primary_key=True, nullable=False, autoincrement=False) 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement='ignore_fk')
    data_type = Column(Unicode(32), nullable=False)
    conversion = Column(Unicode(255), nullable=True)
    UniqueConstraint('cmd_id', 'key', name='uix_1')

    def __init__(self, cmd_id, key, data_type, conversion):
        self.cmd_id = cmd_id
        self.key = ucode(key)
        self.data_type = ucode(data_type)
        self.conversion = ucode(conversion)

class Sensor(DomogikBase):
    __tablename__ = '{0}_sensor'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False) 
    device_id = Column(Integer, ForeignKey('{0}.id'.format(Device.get_tablename()), ondelete="cascade"), nullable=False)
    name = Column(Unicode(255))
    reference = Column(Unicode(64))
    incremental = Column(Boolean, nullable=False)
    formula = Column(UnicodeText(), nullable=True) 
    data_type = Column(Unicode(32), nullable=False)
    conversion = Column(Unicode(255), nullable=True)
    last_value = Column(Unicode(255), nullable=True)
    last_received = Column(Integer, nullable=True)
    value_min = Column(Float(53), nullable=True)
    value_max = Column(Float(53), nullable=True)
    history_store = Column(Boolean, nullable=False)
    history_max = Column(Integer, nullable=True)
    history_expire = Column(Integer, nullable=True)
    history_round = Column(Float(53), nullable=True)
    history_duplicate = Column(Boolean, nullable=False)
    timeout = Column(Integer, nullable=True, default=0)

    def __init__(self, device_id, name, reference, incremental, formula, data_type, conversion, h_store, h_max, h_expire, h_round, h_duplicate, timeout):
        self.device_id = device_id
        self.name = ucode(name)
        self.reference = ucode(reference)
        self.incremental = incremental
        self.formula = ucode(formula)
        self.data_type = ucode(data_type)
        self.conversion = ucode(conversion)
        self.history_store = h_store
        self.history_max = h_max
        self.history_expire = h_expire
        self.history_round = h_round
        self.history_duplicate = h_duplicate
        self.timeout = timeout
        self.value_min = None
        self.value_max = None

class SensorHistory(DomogikBase):
    __tablename__ = '{0}_sensor_history'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False) 
    sensor_id = Column(Integer, ForeignKey('{0}.id'.format(Sensor.get_tablename()), ondelete="cascade"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    value_num = Column(Float(53), nullable=True)
    value_str = Column(Unicode(255), nullable=False)
    original_value_num = Column(Float(53), nullable=True)

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

class XplStat(DomogikBase):
    __tablename__ = '{0}_xplstat'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey('{0}.id'.format(Device.get_tablename()), ondelete="cascade"), nullable=False)
    json_id = Column(Unicode(64), nullable=False)
    name = Column(Unicode(64), nullable=False)
    schema = Column(Unicode(32), nullable=False)
    params = relationship("XplStatParam", backref=__tablename__, cascade="all", passive_deletes=True)
    
    def __init__(self, device_id, name, schema, json_id):
        self.device_id = device_id
        self.name = ucode(name)
        self.schema = ucode(schema)
        self.json_id = ucode(json_id)

class XplStatParam(DomogikBase):
    __tablename__ = '{0}_xplstat_param'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    xplstat_id = Column(Integer, ForeignKey('{0}.id'.format(XplStat.get_tablename()), ondelete="cascade"), primary_key=True, nullable=False, autoincrement=False) 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255), nullable=True)
    multiple = Column(Unicode(1), nullable=True)
    static = Column(Boolean, nullable=True)
    sensor_id = Column(Integer, ForeignKey('{0}.id'.format(Sensor.get_tablename()), ondelete="cascade"), nullable=True) 
    ignore_values = Column(Unicode(255), nullable=True)
    type = Column(Unicode(32), nullable=True)
    UniqueConstraint('xplstat_id', 'key', name='uix_1')

    def __init__(self, xplstat_id, key, value, static, sensor_id, ignore_values, type, multiple=None):
        self.xplstat_id = xplstat_id
        self.key = ucode(key)
        self.value = ucode(value)
        self.static = static
        self.sensor_id = sensor_id
        self.ignore_values = ucode(ignore_values)
        self.type = ucode(type)
        self.multiple = ucode(multiple)

class XplCommand(DomogikBase):
    __tablename__ = '{0}_xplcommand'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    device_id = Column(Integer, ForeignKey('{0}.id'.format(Device.get_tablename()), ondelete="cascade"), nullable=False)
    cmd_id = Column(Integer, ForeignKey('{0}.id'.format(Command.get_tablename()), ondelete="cascade"), nullable=False)
    json_id = Column(Unicode(64), nullable=False)
    name = Column(Unicode(64), nullable=False)
    schema = Column(Unicode(32), nullable=False)
    stat_id = Column(Integer, ForeignKey('{0}.id'.format(XplStat.get_tablename()), ondelete="cascade"), nullable=True)
    stat = relation("XplStat", backref=__tablename__, cascade="all")
    params = relationship("XplCommandParam", backref=__tablename__, cascade="all", passive_deletes=True)

    def __init__(self, name, device_id, cmd_id, json_id, schema, stat_id):
        self.name = ucode(name)
        self.device_id = device_id
        self.cmd_id = cmd_id
        self.schema = ucode(schema)
        self.stat_id = stat_id
        self.json_id = json_id

class XplCommandParam(DomogikBase):
    __tablename__ = '{0}_xplcommand_param'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    xplcmd_id = Column(Integer, ForeignKey('{0}.id'.format(XplCommand.get_tablename()), ondelete="cascade"), primary_key=True, nullable=False, autoincrement=False) 
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255))
    UniqueConstraint('xplcmd_id', 'key', name='uix_1')

    def __init__(self, cmd_id, key, value):
        self.xplcmd_id = cmd_id
        self.key = ucode(key)
        self.value = ucode(value)

class Scenario(DomogikBase):
    __tablename__ = '{0}_scenario'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(Unicode(32), nullable=False, autoincrement=False)
    json = Column(UnicodeText(), nullable=False)
    disabled = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=True)
    state = Column(Unicode(32), nullable=False, default=False)

    def __init__(self, name, json, disabled=False, description=None, state=None):
        self.name = ucode(name)
        self.json = ucode(json)
        self.disabled = disabled
        self.description = description
        self.state = state

class Person(DomogikBase):
    """Persons registered in the app"""

    __tablename__ = '{0}_person'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    first_name = Column(Unicode(20), nullable=False)
    last_name = Column(Unicode(20), nullable=False)
    birthdate = Column(Date)
    location_sensor = Column(Integer, ForeignKey('{0}.id'.format(Sensor.get_tablename()), ondelete="cascade"), nullable=True)
    user_accounts = relation("UserAccount", backref=__tablename__, cascade="all")

    def __init__(self, first_name, last_name, birthdate, location_sensor=None):
        """Class constructor

        @param first_name : first name
        @param last_name : last name
        @param birthdate : birthdate

        """
        self.first_name = ucode(first_name)
        self.last_name = ucode(last_name)
        self.birthdate = birthdate
        self.location_sensor = location_sensor

class UserAccount(DomogikBase):
    """User account for persons : it is only used by the UI"""

    __tablename__ = '{0}_user_account'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    login = Column(Unicode(20), nullable=False, unique=True)
    password = Column("password", Unicode(255), nullable=False)
    person_id = Column(Integer, ForeignKey('{0}.id'.format(Person.get_tablename())))
    person = relation(Person)
    is_admin = Column(Boolean, nullable=False, default=False)
    skin_used = Column(Unicode(80), nullable=False, default=Unicode('default'))
    lock_edit = Column(Boolean, nullable=False, default=False)
    lock_delete = Column(Boolean, nullable=False, default=False)

    def __init__(self, login, password, is_admin, skin_used, person_id, lock_edit, lock_delete):
        """Class constructor

        @param login : login
        @param password : password
        @param person_id : id of the person associated to this account
        @param is_admin : True if the user has administrator privileges
        @param skin_used : skin used in the UI (default value = 'default')
        @param lock_edit: True id the account is locked for editing
        @param lock_delete: True id the account is locked for deleting

        """
        self.login = ucode(login)
        self.password = ucode(password)
        self.person_id = person_id
        self.is_admin = is_admin
        self.skin_used = ucode(skin_used)
        self.lock_edit = lock_edit
        self.lock_delete = lock_delete

    def set_password(self, password):
        """Set a password for the user"""
        self.password = ucode(password)

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


class Location(DomogikBase):
    __tablename__ = '{0}_location'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    name = Column(Unicode(32), nullable=False, autoincrement=False)
    isHome = Column(Boolean, nullable=False, default=False)
    type = Column(Unicode(10), nullable=True)
    params = relationship("LocationParam", backref=__tablename__, cascade="all", passive_deletes=True)

    def __init__(self, name, type, isHome=False):
        self.name = ucode(name)
        self.type = type
        self.isHome = isHome

class LocationParam(DomogikBase):
    __tablename__ = '{0}_location_param'.format(_db_prefix)
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_character_set':'utf8'}
    location_id = Column(Integer, ForeignKey('{0}.id'.format(Location.get_tablename()), ondelete="cascade"), primary_key=True, nullable=False, autoincrement=False)
    key = Column(Unicode(32), nullable=False, primary_key=True, autoincrement=False)
    value = Column(Unicode(255), nullable=True)

    def __init__(self, location_id, key, value):
        self.location_id = location_id
        self.key = ucode(key)
        self.value = ucode(value)

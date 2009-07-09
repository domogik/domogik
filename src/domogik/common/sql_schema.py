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



@author: Marc SCHNEIDER <marc@domogik.org>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from sqlalchemy import types, create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Boolean, DateTime, Date, Text
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


###
# Enum stuff
# http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Enum
###
class Enum(types.TypeDecorator):
  impl = types.Unicode
  
  def __init__(self, values, empty_to_none=False, strict=False):
    """Emulate an Enum type.

    values:
       A list of valid values for this column
    empty_to_none:
       Optional, treat the empty string '' as None
    strict:
       Also insist that columns read from the database are in the
       list of valid values.  Note that, with strict=True, you won't
       be able to clean out bad data from the database through your
       code.
    """

    if values is None or len(values) is 0:
        raise exceptions.AssertionError('Enum requires a list of values')
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
        raise exceptions.AssertionError('"%s" not in Enum.values' % value)
    return value
      
      
  def process_result_value(self, value, dialect):
    if self.strict and value not in self.values:
      raise exceptions.AssertionError('"%s" not in Enum.values' % value)
    return value

#Define objects

### TODO : add db prefix to table names

###
# Areas
# name : The "short" name of the area (a few words, 30 char max)
# description : Extended description, up to 100 chars
#
# An area is something like "first floor", "garden", etc ...
# That is not a room !
###

class Area(Base):
  __tablename__ = 'area'
  id = Column(Integer, primary_key=True)
  name = Column(String(30), nullable=False)
  description = Column(String(100))

  def __init__(self, name, description):
    self.name = name
    self.description = description

  def __repr__(self):
    return "<Area('%s', '%s')>" % (self.name, self.description)

###
# Rooms
# name : The "short" name (a few words, 30 char max)
# area : id of the area where the room is
# description : Extended description, up ti 100 chars
###

class Room(Base):
  __tablename__ = 'room'
  id = Column(Integer, primary_key=True)
  name = Column(String(30), nullable=False)
  description = Column(String(100))
  #area = Column(Integer, ForeignKey('%s_area.name' % db['db_prefix'])),
  area = Column(Integer, ForeignKey('area.id'))

  def __init__(self, name, description, area):
    self.name = name
    self.description = description
    self.area = area

  def __repr__(self):
    return "<Room('%s', '%s')>" % (self.name, self.description)

###
# Categories for devices
# name : the category name (1 word, max 30 chars)
# ex : temperature, heating, lighting, music
#
# The category is used to "tag" a device
###

class DeviceCategory(Base):
  __tablename__ = 'device_category'
  id = Column(Integer, primary_key=True)
  name = Column(String(30), nullable=False)

  def __init__(self, name, description):
    self.name = name

  def __repr__(self):
    return "<DeviceCategory('%s')>" % (self.name)

###
# Descriptions of the different technologies
# name : Name of the technology (ex : X10, 1wire, PLCBUS)
# description : Extended description, max 10 chars
# type : Basic type of the technology, one of
#       'cpl' : use power lines,
#       'wired' : Use a wired bus (1wire for ex),
#       'wifi' : Use wifi,
#       'wireless' : Use other wireless (RF based) technologies (ex : RFXCOM)
#       'ir' : Infrared
#
# Each device must be linked to one of these categories
###

class DeviceTechnology(Base):
  __tablename__ = 'device_technology'
  id = Column(Integer, primary_key=True)
  name = Column(String(30), nullable=False)
  description = Column(String(100))
  type = Column(Enum([u'cpl',u'wired',u'wifi',u'wireless',u'ir']))

  def __init__(self, name, description, type):
    self.name = name
    self.description = description
    self.type = type

  def __repr__(self):
    return "<DeviceTechnology('%s', '%s', '%s')>" % (self.name, self.description, self.type)

###
# Config for technologies
# key : the config item
# value : the config value
# 
# This table describes the technology wide configurations
###

class DeviceTechnologyConfig(Base):
  __tablename__ = 'device_technology_config'
  id = Column(Integer, primary_key=True)
  technology = Column(Integer, ForeignKey('device_technology.id'))
  key = Column(String(30), nullable=False)
  value = Column(String(80), nullable=False)

  def __init__(self, technology, key, value):
    self.technology = technology
    self.key = key
    self.value = value

  def __repr__(self):
    return "<DeviceTechnologyConfig('%s', '%s')>" % (self.key, self.value)

###
# Devices
# name : The short (30 char max) name of the device
# address : The device address (like 'a3' for x10, or '01.123456789ABC' for 1wire)
# description : Explain what this device is used to
# technology : Device technology (foreign key)
# type: One of 'appliance','lamp','music'
# category : Device category (foreign key)
#  room : The room where the device is (foreign key)
# is_resetable : Can we set the device to a default value
# initial_value : Value to reset the device
# is_value_changeable_by_user : Can the device receive orders from the user
# unit_of_stored_values : Unit to display the values, one of
# Volt, Celsius, Farenheit, Percent, Boolean
###

class Device(Base):
  __tablename__ = 'device'
  id = Column(Integer, primary_key=True)
  address = Column(String(30), nullable=False)
  description = Column(String(100))
  technology = Column(Integer, ForeignKey('device_technology.id'))
  type = Column(Enum([u'appliance',u'lamp',u'music',u'sensor']))
  category = Column(Integer, ForeignKey('device_category.id'))
  room = Column(Integer, ForeignKey('room.id'))
  is_resetable = Column(Boolean, nullable=False)
  initial_value = Column(String(10))
  is_value_changeable_by_user = Column(Boolean, nullable=False)
  unit_of_stored_values = Column(Enum([u'Volt',u'Celsius',u'Fahrenheit',u'Percent',u'Boolean']))

  def __init__(self, address, description, technology, type, category, room, is_resetable, initial_value, is_value_changeable_by_user, unit_of_stored_values):
    self.address = address
    self.description = description
    self.technology = technology
    self.type = type
    self.category = category
    self.room = room
    self.is_resetable = is_resetable
    self.initial_value = initial_value
    self.is_value_changeable_by_user = is_value_changeable_by_user
    self.unit_of_stored_values = unit_of_stored_values

  def __repr__(self):
    return "<Device('%s', '%s')>" % (self.address, self.description)

###
# Config for devices
# key : the config item
# value : the config value
# 
# This table describes the device related configurations
###

class DeviceConfig(Base):
  __tablename__ = 'device_config'
  id = Column(Integer, primary_key=True)
  device = Column(Integer, ForeignKey('device.id'))
  key = Column(String(30), nullable=False)
  value = Column(String(80), nullable=False)

  def __init__(self, device, key, value):
    self.device = device
    self.key = key
    self.value = value

  def __repr__(self):
    return "<DeviceConfig('%s', '%s')>" % (self.key, self.value)

###
# Stats for device's states
# date : timestamp of the record
# device : the device which send value
# value : The vale of the device
###

class DeviceStats(Base):
  __tablename__ = 'device_stats'
  id = Column(Integer, primary_key=True)
  device = Column(Integer, ForeignKey('device.id'))
  date = Column(DateTime, nullable=False)
  value = Column(String(80), nullable=False)

  def __init__(self, device, date, value):
    self.device = device
    self.date = date
    self.value = value

  def __repr__(self):
    return "<DeviceStats('%s', '%s')>" % (self.date, self.value)

###
# Define triggers
# name : The name of the rule
# description : Long" description of the rule
# rule : formatted trigger rule
# result : list of xpl messages to send
#
# Triggers are set or (device, condition). 
# When all the devices respects the condition, 
# the 'result' is executed
###

class Trigger(Base):
  __tablename__ = 'trigger'
  id = Column(Integer, primary_key=True)
  description = Column(String(100))
  rule = Column(Text, nullable=False)
  result = Column(Text, nullable=False)

  def __init__(self, description, rule, result):
    self.description = description
    self.rule = rule
    self.result = result

  def __repr__(self):
    return "<Trigger('%s', '%s', '%s')>" % (self.description, self.rule, self.result)

###
# Define users' system account
# login : username used for login
# password : account password
# is_admin : does this account have administrative power ?
#
# This table is only used by interface
###

class SystemAccount(Base):
  __tablename__ = 'system_account'
  id = Column(Integer, primary_key=True)
  login = Column(String(20), nullable=False)
  password = Column(Text, nullable=False)
  is_admin = Column(Boolean, nullable=False, default=False)

  def __init__(self, login, password, is_admin):
    self.login = description
    self.password = password
    self.is_admin = is_admin

  def __repr__(self):
    return "<SystemAccount('%s', '%s')>" % (self.login, self.is_admin)

###
# User account - personnal informations
# first_name : User's first name
# last_name : User's last date
# birthdate : User's date of birth
# system_account : User account on the system (if exists)
#
# This table is only used by interface
###

class UserAccount(Base):
  __tablename__ = 'user_account'
  id = Column(Integer, primary_key=True)
  first_name = Column(String(50), nullable=False)
  last_name = Column(String(60), nullable=False)
  birthdate = Column(Date, nullable=False)
  system_account = Column(Integer, ForeignKey('system_account.id'))

  def __init__(self, first_name, last_name, birthdate, system_account):
    self.first_name = first_name
    self.last_name = last_name
    self.birthdate = birthdate
    self.system_account = system_account

  def __repr__(self):
    return "<UserAccount('%s', '%s')>" % (self.first_name, self.last_name)

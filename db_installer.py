#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

#Create and populate database

from sqlalchemy import types, create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Boolean, DateTime, Text

from domogik.common.configloader import Loader

cfg = Loader('database')
config = cfg.load()
try:
	db = dict(config[1])
	url = "%s:///" % db['db_type']
	if db['db_type'] == 'sqlite':
		url = "%s%s" % (url,db['db_path'])
	else:
		if db['db_port'] != '':
			url = "%s%s:%s@%s:%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_port'], db['db_name'])
		else:
			url = "%s%s:%s@%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_name'])
except:
	print "Some errors appears during connection to the database : Can't fetch informations from config file"

engine = create_engine(url)
metadata = MetaData()

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


#Define tables

###
# Areas
# name : The "short" name of the area (a few words, 30 char max)
# description : Extended description, up to 100 chars
#
# An area is something like "first floor", "garden", etc ...
# That is not a room !
###
areas_table =  Table('%s_area' % db['db_prefix'], metadata, 
	    Column('id', Integer, primary_key=True),
	    Column('name', String(30), nullable=False),
	    Column('description', String(100)),
	)

###
# Rooms
# name : The "short" name (a few words, 30 char max)
# area : id of the area where the room is
# description : Extended description, up ti 100 chars
###
rooms_table =  Table('%s_room' % db['db_prefix'], metadata, 
	    Column('id', Integer, primary_key=True),
	    Column('name', String(30), nullable=False),
	    Column('area', Integer, ForeignKey('%s_area.name' % db['db_prefix'])),
	    Column('description', String(100)),
	)

###
# Categories for devices
# name : the category name (1 word, max 30 chars)
# ex : temperature, heating, lighting, music
#
# The category is used to "tag" a device
###
device_category_table = Table('%s_device_category' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
	    Column('name', String(30), nullable=False)
	)

###
# Descriptions of the different technologies
# name : Name of the technology (ex : X10, 1wire, PLCBUS)
# description : Extended description, max 10 chars
# type : Basic type of the technology,
# 		one of 	'cpl' : use power lines,
#				'wired' : Use a wired bus (1wire for ex),
#				'wifi' : Use wifi,
#				'wireless' : Use other wireless (RF based) technologies (ex : RFXCOM)
#				'ir' : Infrared
#
# Each device must be linked to one of these categories
###
device_technology_table = Table('%s_device_technology' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
	    Column('name', String(30), nullable=False),
	    Column('description', String(100)),
		Column('type', Enum([u'cpl',u'wired',u'wifi',u'wireless',u'ir']))
	)

###
# Config for technologies
# key : the config item
# value : the config value
# 
# This table describes the technology wide configurations
###
device_technology_config_table = Table('%s_device_technology_config' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
		Column('technology', Integer, ForeignKey('%s_device_technology.id' % db['db_prefix'])),
	    Column('key', String(30), nullable=False),
	    Column('value', String(80), nullable=False)
	)

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
# Volt, Celsius, Farenight, Percent, Boolean
###
device_table = Table('%s_device' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
	    Column('address', String(30), nullable=False),
	    Column('description', String(100)),
		Column('technology', Integer, ForeignKey('%s_device_technology.id' % db['db_prefix'])),
		Column('type', Enum([u'appliance',u'lamp',u'music',u'sensor'])),
		Column('category', Integer, ForeignKey('%s_device_category.id' % db['db_prefix'])),
	    Column('room', Integer, ForeignKey('%s_room.id' % db['db_prefix'])),
	    Column('is_resetable', Boolean, nullable=False),
		Column('initial_value', String(10)),
	    Column('is_value_changeable_by_user', Boolean, nullable=False),
		Column('unit_of_stored_values', Enum([u'Volt',u'Celsius',u'Fahrenheit',u'Percent',u'Boolean']))
	)

###
# Config for devices
# key : the config item
# value : the config value
# 
# This table describes the device related configurations
###
device_config_table = Table('%s_device_config' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
		Column('device', Integer, ForeignKey('%s_device.id' % db['db_prefix'])),
	    Column('key', String(30), nullable=False),
	    Column('value', String(80), nullable=False)
	)

###
# Stats for device's states
# date : timestamp of the record
# device : the device which send value
# value : The vale of the device
###
device_stats_table =  Table('%s_device_stats' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
		Column('device', Integer, ForeignKey('%s_device.id' % db['db_prefix'])),
	    Column('date', DateTime, nullable=False),
	    Column('value', String(80), nullable=False)
	)

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
trigger_table = Table('%s_trigger' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
	    Column('rule', Text, nullable=False),
	    Column('result', Text, nullable=False)
	)

###
# Define users' system account
# login : username used for login
# password : account password
# is_admin : does this account have administrative power ?
#
# This table is only used by interface
###
system_account_table = Table('%s_system_account' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
	    Column('login', String(20), nullable=False),
	    Column('password', Text, nullable=False),
		Column('is_admin', Boolean, nullable=False, default=False),
	)

###
# User account - personnal informations
# first_name : User's first name
# last_name : User's last date
# birthdate : User's date of birth
# system_account : User account on the system (if exists)
#
# This table is only used by interface
###
user_account_table = Table('%s_user_account' % db['db_prefix'], metadata,
		Column('id', Integer, primary_key=True),
	    Column('first_name', String(50), nullable=False),
	    Column('last_name', String(60), nullable=False),
		Column('birthdate', DateTime, nullable=False),
		Column('system_account', Integer, ForeignKey('%s_system_account.id' % db['db_prefix'])),
	)

###
# Installer
###
metadata.create_all(engine) 

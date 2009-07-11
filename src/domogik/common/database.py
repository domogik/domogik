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

API to use Domogik database

Implements
==========

- DbHelper.__init__(self)
- DbHelper._get_table(self, table_name)
- DbHelper.list_areas_name(self)
- DbHelper.fetch_area_informations(self, area)
- DbHelper.add_area(self, a_name, a_description)
- DbHelper.del_area(self, a_name)
- DbHelper.list_rooms_name(self)
- DbHelper.fetch_room_informations(self, room)
- DbHelper.add_room(self, r_name, r_area_id, r_description)
- DbHelper.del_room(self, r_name)
- DbHelper.get_all_room_of_area(self, a_name)
- DbHelper.list_device_categories_name(self)
- DbHelper.fetch_device_category_informations(self, dc_name)
- DbHelper.add_device_category(self, dc_name)
- DbHelper.del_device_category(self, dc_name)
- DbHelper.get_all_devices_of_category(self, dc_id)
- DbHelper.get_all_devices_of_technology(self, dt_id)
- DbHelper.list_device_technologies_name(self)
- DbHelper.fetch_device_technology_informations(self, dc_name)
- DbHelper.add_device_technology(self, dc_name, dt_description, dt_type)
- DbHelper.del_device_technology(self, dc_name)
- DbHelper.list_device_technology_config_keys(self)
- DbHelper.fetch_device_technology_config_informations(self, dtc_technology, dtc_key)
- DbHelper.fetch_device_technology_config_value(self, dtc_technology, dtc_key)
- DbHelper.add_device_technology_config(self, dtc_technology, dtc_key, dtc_value)
- DbHelper.del_device_technology_config(self, dtc_id)
- DbHelper.get_all_config_of_technology(self, dt_id)
- DbHelper.list_devices(self)
- DbHelper.find_devices(self, **filters)
- DbHelper.fetch_device_informations(self, d_id)
- DbHelper.def add_device(self, d_address, d_technology, d_type, d_category,
- DbHelper.del_device(self, d_id)
- DbHelper.list_device_stats(self, ds_id)
- DbHelper.get_last_stat_of_devices(self, d_list)
- DbHelper.add_device_stat(self, ds_device, ds_date, ds_value)
- DbHelper.del_device_stat(self, ds_id)
- DbHelper.del_all_device_stats(self, d_id)
- DbHelper.list_triggers(self)
- DbHelper.get_trigger(self, t_id)
- DbHelper.add_trigger(self, t_desc, t_rule, t_res)
- DbHelper.del_trigger(self, t_id)
- DbHelper.list_system_accounts(self)
- DbHelper.fetch_system_account_informations(self, a_id)
- DbHelper.add_system_account(self, a_login, a_password, a_is_admin = False)
- DbHelper.del_system_account(self, a_id)
- DbHelper.get_user_system_account(self, u_id)
- DbHelper.list_user_accounts(self)
- DbHelper.fetch_user_account_informations(self, u_id)
- DbHelper.add_user_account(self, u_first_name, u_last_name, u_birthdate, u_system_account = None)
- DbHelper.del_user_account(self, u_id)
- print_title(title)
- print_test(test)

@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

####
# Existing tables :
# areas
# rooms
# device_category
# device_technology
# device_technology_config
# device
# device_config
# device_stats
# trigger
# system_account
# user_account
####

from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy import asc, desc
import time
from datetime import datetime
import hashlib

from domogik.common.configloader import Loader

class DbHelper():
    """
    This class provides methods to fetch and put informations on the Domogik database
    The user should only use methods from this class and don't access the database directly
    """
    self._soup = None
    self._dbprefix = None

    def __init__(self):
        cfg = Loader('database')
        config = cfg.load()
        db = dict(config[1])
        url = "%s:///" % db['db_type']
        if db['db_type'] == 'sqlite':
            url = "%s%s" % (url,db['db_path'])
        else:
            if db['db_port'] != '':
                url = "%s%s:%s@%s:%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_port'], db['db_name'])
            else:
                url = "%s%s:%s@%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_name'])

        #Connecting to the database    
        soup = SqlSoup(url)
        self._soup = soup
        self._dbprefix = db['db_prefix']

    def _get_table(self, table_name):
        """
        Returns a referenceto the table
        This method takes care of the prefix used
        """
        ref =  getattr(self._soup, str('%s_%s') % (self._dbprefix, table_name))
        return ref

####
# Areas
####
    def list_areas_name(self):
        """
        Returns a list of areas' name
        """
        result = []
        for area in self._get_table('area').all():
            result.append(area.name)
        return result

    def fetch_area_informations(self, area):
        """
        Return informations about an area
        @param area : The area name
        @return a dictionnary of name:value 
        """
        req = self._get_table('area').filter_by(name = area)
        if req.count() > 0:
            request = req.first()
            return {'id' : request.id, 'name' : request.name, 'description' : request.description}
        else:
            return None

    def add_area(self, a_name, a_description):
        """
        Add an area
        @param a_name : area name
        @param a_description : area detailled description
        """
        self._get_table('area').insert(name = a_name, description = a_description)
        self._soup.flush()

    def del_area(self, a_name):
        """
        Delete an area record and
        Warning this also remove all the rooms in this area
        and all the devices (+ their stats) in each deleted rooms !
        @param a_name : name of the area to delete
        """
        req = self._get_table('area').filter_by(name = a_name)
        if req.count() > 0:
            area = req.first()
            rooms = self._get_table('room').filter_by(area = area.id)
            devices = []
            for room in rooms:
                devices.extends(self._get_table('device').filter_by(room = room.id))
                self._get_table('room').delete(id == room.id)
            for device in devices:
                self._get_table('device').delete(id == device.id)
            self._get_table('area').delete(id == area.id)
            self._soup.flush()


####
# Rooms
####
    def list_rooms_name(self):
        """
        Returns a list of rooms' name
        """
        result = []
        for room in  self._get_table('room').all():
            result.append(room.name)
        return result

    def fetch_room_informations(self, room):
        """
        Return informations about a room
        @param room : The room name
        @return a dictionnary of name:value 
        """
        req = self._get_table('room').filter_by(name = room)
        if req.count() > 0:
            request = req.first()
            return {'id' : request.id, 'name' : request.name, 'area' : request.area,'description' : request.description}
        else:
            return None

    def add_room(self, r_name, r_area_id, r_description):
        """
        Add a room
        @param r_name : room name
        @param r_area_id : id of the area where the room is
        @param r_description : room detailled description
        """
        self._get_table('room').insert(name = r_name, area = r_area_id, description = r_description)
        self._soup.flush()

    def del_room(self, r_name):
        """
        Delete a room record
        Warning this also remove all the devices (+ their stats) in each deleted rooms !
        @param a_name : name of the room to delete
        """
        req = self._get_table('room').filter_by(name = r_name)
        if req.count() > 0:
            room = req.first()
            devices = self._get_table('device').filter_by(room = room.id).all()
            self._get_table('room').delete(id == room.id)
            for device in devices:
                self._get_table('device').delete(id == device.id)
            self._soup.flush()

    def get_all_room_of_area(self, a_name):
        """
        Returns all the rooms of an area
        @param a_name : area name
        @return a list of dictionary {'id':'xxx','name':'yyy','description':'zzzz', 'area':a_name}
        """
        rooms = self._get_table('room').filter_by(area= a_name).all()
        result = []
        for room in rooms:
            result.append({'id':room.id, 'name':room.name, 'area':room.area, 'description':room.description})
        return result

####
# Device category
####
    def list_device_categories_name(self):
        """
        Returns a list of device_categories' name
        """
        result = []
        for device_category in  self._get_table(str('device_category')).all():
            result.append(device_category.name)
        return result

    def fetch_device_category_informations(self, dc_name):
        """
        Return informations about a device category
        @param dc_name : The device category name
        @return a dictionnary of name:value 
        """
        req = self._get_table('device_category').filter_by(name = dc_name)
        if req.count() > 0:
            request = req.first()
            return {'id' : request.id, 'name' : request.name}
        else:
            return None

    def add_device_category(self, dc_name):
        """
        Add a device_category (temperature, heating, lighting, music, ...)
        @param dc_name : device category name
        """
        self._get_table('device_category').insert(name = dc_name)
        self._soup.flush()

    def del_device_category(self, dc_name):
        """
        Delete a device category record
        Warning, it will also remove all the devices using this category
        @param dc_name : name of the device category to delete
        """
        req = self._get_table('device_category').filter_by(name = dc_name)
        if req.count() > 0:
            device_category = req.first()
            devices = self._get_table('device').filter_by(category = device_category.id).all()
            self._get_table('device_category').delete(id == device_category.id)
            for device in devices:
                self._get_table('device').delete(id == device.id)
            self._soup.flush()
    
    def get_all_devices_of_category(self, dc_id):
        """
        Returns all the devices of a category
        @param a_id: categoryid 
        @return a list of dictionary {'id':'xxx','address':'yyy','technology':'zzzz'}
        It does *not* return all attributes of devices
        """
        devices = self._get_table('device').filter_by(category = dc_id).all()
        result = []
        for device in devices:
            result.append({'id':device.id, 'address':device.address, 'technology':device.technology})
        return result

    def get_all_devices_of_technology(self, dt_id):
        """
        Returns all the devices of a technology
        @param dt_id : technology id
        @return a list of dictionary {'id':'xxx','address':'yyy','technology':'zzzz'}
        It does *not* return all attributes of devices
        """
        devices = self._get_table('device').filter_by(technology = dt_id).all()
        result = []
        for device in devices:
            result.append({'id':device.id, 'address':device.address, 'technology':device.technology})
        return result
####
# Device technology
####
    def list_device_technologies_name(self):
        """
        Returns a list of device_technologies' name
        """
        result = []
        for device_technology in  self._get_table(str('device_technology')).all():
            result.append(device_technology.name)
        return result

    def fetch_device_technology_informations(self, dc_name):
        """
        Return informations about a device technology
        @param dc_name : The device technology name
        @return a dictionnary of name:value 
        """
        req = self._get_table('device_technology').filter_by(name = dc_name)
        if req.count() > 0:
            request = req.first()
            return {'id' : request.id, 'name' : request.name, 
                    'description' : request.description, 'type' : request.type}
        else:
            return None

    def add_device_technology(self, dc_name, dt_description, dt_type):
        """
        Add a device_technology
        @param dc_name : device technology name
        @param dt_description : extended description of the technology
        @param type : type of the technology, one of 'cpl','wired','wifi','wireless','ir'
        """
        if dt_type not in ['cpl','wired','wifi','wireless','ir']:
            raise ValueError, 'dt_type must be one of cpl,wired,wifi,wireless,ir'
        self._get_table('device_technology').insert(name = dc_name, 
                description = dt_description, type = dt_type)
        self._soup.flush()

    def del_device_technology(self, dc_name):
        """
        Delete a device technology record
        Warning, it will also remove all the devices using this technology
        @param dc_name : name of the device technology to delete
        """
        req = self._get_table('device_technology').filter_by(name = dc_name)
        if req.count() > 0:
            device_technology = req.first()
            devices = self._get_table('device').filter_by(technology = device_technology.id).all()
            self._get_table('device_technology').delete(id == device_technology.id)
            for device in devices:
                self._get_table('device').delete(id == device.id)
            self._soup.flush()

####
# Device technology config
####
    def list_device_technology_config_keys(self):
        """
        Returns a list of device_technologies'config keys
        """
        result = []
        for device_technology in  self._get_table(str('device_technology_config')).all():
            result.append(device_technology.key)
        return result

    def fetch_device_technology_config_informations(self, dtc_technology, dtc_key):
        """
        Return informations about a device technology config item
        @param dtc_technology : The device technology 
        @param dtc_key : The device technology config key
        @return a dictionnary of name:value 
        """
        req = self._get_table('device_technology_config').filter_by(key= dtc_key, 
                technology = dtc_technology)
        if req.count() > 0:
            request = req.first()
            return {'id' : request.id, 'technology' : request.technology, 
                    'key' : request.key, 'value' : request.value}
        else:
            return None

    def fetch_device_technology_config_value(self, dtc_technology, dtc_key):
        """
        Only returns the value for a config key
        @param dtc_technology : The device technology 
        @param dtc_key : The device technology config key
        @return the value of the config item 'dtc_key' for the technology 'dtc_technology'
        """
        req = self._get_table('device_technology_config').filter_by(key= dtc_key, 
                technology = dtc_technology)
        if req.count() > 0:
            request = req.first()
            return request.value
        else:
            return None

    def add_device_technology_config(self, dtc_technology, dtc_key, dtc_value):
        """
        Add a device's technology config item
        @param dtc_technology : The device technology 
        @param dtc_key : The device technology config key
        @param dtc_value : The device technology config value
        """
        if dt_type not in ['cpl','wired','wifi','wireless','ir']:
            raise ValueError, 'dt_type must be one of cpl,wired,wifi,wireless,ir'
        self._get_table('device_technology').insert(name = dc_name, 
                description = dt_description, type = dt_type)
        self._soup.flush()

    def del_device_technology_config(self, dtc_id):
        """
        Delete a device technology config record
        @param dtc_id : config item id
        """
        req = self._get_table('device_technology_config').filter_by(id = dtc_id)
        if req.count() > 0:
            device_technology_config = req.first()
            self._get_table('device_technology_config').delete(id == device_technology_config.id)
            self._soup.flush()
    
    def get_all_config_of_technology(self, dt_id):
        """
        Returns all the devices of a technology
        @param dt_id : technology id
        @return a list of dictionary {'id':'xxx','address':'yyy','technology':'zzzz'}
        It does *not* return all attributes of devices
        """
        devices = self._get_table('device').filter_by(technology = dt_id).all()
        result = []
        for device in devices:
            result.append({'id':device.id, 'address':device.address, 'technology':device.technology})
        return result

###
# Devices
###
    def list_devices(self):
        """
        Returns a list of some devices informations
        This method doesn't return all informations
        @return a list of dictionnaries {'id': device_id, 
            'technology': device_technology, 'address' : device_address}

        """
        result = []
        for device in  self._get_table(str('device')).all():
            result.append({'id' : device.id, 'technology' : device.technology, 
                'address' : device.address})
        return result

    def find_devices(self, **filters):
        """
        Looks for device with filter on their attributes
        filter fileds can be one of id, address, type, room, initial_value, 
        is_value_changeable_by_user, unit_of_stored_values.
        @return a list of dictionnaries for each corresponding device
        """
        data = None
        if not filters:
            data = self._get_table(str('device')).all()
        else:
            request = []
            for filter in filters:
                request.append("%s == '%s'" % (filter, filters[filter]))
            filter = " and ".join(request)
            data = self._get_table(str('device')).filter(filter)
        result = []
        for d in data:
            result.append(self.fetch_device_informations(d.id))
        return result

    def fetch_device_informations(self, d_id):
        """
        Return informations about a device 
        @param d_id : The device id
        @return a dictionnary of name:value 
        """
        req = self._get_table('device').filter_by(id = d_id)
        if req.count() > 0:
            request = req.first()
            return {'id' : request.id, 'technology' : request.technology, 
                    'address' : request.address, 'description' : request.description,
                    'type' : request.type, 'category' : request.category,
                    'room' : request.room, 'is_resetable' : request.is_resetable,
                    'initial_value' : request.initial_value, 
                    'is_value_changeable_by_user': request.is_value_changeable_by_user,
                    'unit_of_stored_values' : request.unit_of_stored_values
                    }
        else:
            return None

    def add_device(self, d_address, d_technology, d_type, d_category,
        d_room, d_initial_value = None, d_description = None, d_is_resetable = False, 
        d_is_changeable_by_user = False, d_unit_of_stored_values ='Percent'):
        """
        Add a device item
        @param technology : Item technology id
        @param address : Item address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param description : Extended item description (100 char max)
        @param type : One of 'appliance','light','music','sensor'
        @param category : Item category id
        @param room : Item room id
        @param is_resetable : Can the item be reseted to some initial state
        @param initial_value : What's the initial value of the item, should be 
            the state when the item is created (except for sensors, music)
        @param is_value_changeable_by_user : Can a user change item state (ex : false for sensor)
        @param unit_of_stored_values : What is the unit of item values,
            must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean'
        """
        if d_unit_of_stored_values not in ['Volt','Celsius','Farenight','Percent','Boolean']:
            raise ValueError, "d_unit_of_stored_values must be one of \
            'Volt','Celsius','Farenight','Percent','Boolean'."
        if d_type not in ['appliance','lamp','music']:
            raise ValueError, "d_type must be one of 'appliance','lamp','music'"
        self._get_table('device').insert(address = d_address, technology = d_technology, 
            type = d_type, category = d_category, room = d_room, initial_value = d_initial_value, 
            description = d_description, is_resetable = d_is_resetable, 
            is_value_changeable_by_user = d_is_changeable_by_user,
            unit_of_stored_values =  d_unit_of_stored_values)
        self._soup.flush()

    def update_device(self, d_id, d_address = None, d_technology = None, d_type = None, d_category = None,
        d_room = None, d_initial_value = None, d_description = None, d_is_resetable = None, 
        d_is_changeable_by_user = None, d_unit_of_stored_values = None):
        """
        Update a device item
        If a param is None, then the old value will be kept
        @param d_id : Device id
        @param technology : Item technology id
        @param address : Item address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param description : Extended item description (100 char max)
        @param type : One of 'appliance','light','music','sensor'
        @param category : Item category id
        @param room : Item room id
        @param is_resetable : Can the item be reseted to some initial state
        @param initial_value : What's the initial value of the item, should be 
            the state when the item is created (except for sensors, music)
        @param is_value_changeable_by_user : Can a user change item state (ex : false for sensor)
        @param unit_of_stored_values : What is the unit of item values,
            must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean'
        """
        if d_unit_of_stored_values not in [None,'Volt','Celsius','Farenight','Percent','Boolean']:
            raise ValueError, "d_unit_of_stored_values must be one of \
            'Volt','Celsius','Farenight','Percent','Boolean'."
        if d_type not in [None,'appliance','lamp','music']:
            raise ValueError, "d_type must be one of 'appliance','lamp','music'"
        req = self._get_table('device').filter_by(id = d_id)
        if req.count() > 0:
            device = req.first()
            if d_address is not None:
                device.address = d_address
            if d_technology is not None:
                device.technology = d_technology
            if d_description is not None:
                device.description = d_description
            if d_type is not None:
                device.type = d_type
            if d_category is not None:
                device.category = d_category
            if d_room is not None:
                device.room = d_room
            if d_is_resetable is not None:
                device.is_resetable = d_is_resetable
            if d_initial_value is not None:
                device.initial_value = d_initial_value
            if d_is_changeable_by_user is not None:
                device.is_changeable_by_user = d_is_changeable_by_user
            if d_unit_of_stored_values is not None:
                device.unit_of_stored_values = d_unit_of_stored_values
            self._soup.flush()

    def del_device(self, d_id):
        """
        Delete a device 
        @param d_id : item id
        """
        req = self._get_table('device').filter_by(id = d_id)
        if req.count() > 0:
            device = req.first()
            self._get_table('device').delete(id == device.id)
            self._soup.flush()
    
####
# Device stats
####
    def list_device_stats(self, ds_id):
        """
        Returns a list of all stats for a device
        @param ds_id : the device id
        @return A list of dictionnary {'date' : stat date/time, 'value' : stat value}
        """
        result = []
        for device_stat in  self._get_table('device_stats').filter_by(device = ds_id):
            result.append({'date': device_stat.date, 'value': device_stat.value})
        return result

    def get_last_stat_of_devices(self, d_list):
        """
        Fetch the last record for all devices in d_list
        @param d_list : list of device ids
        @return a list of dictionnary
        """
        result = []
        for device in d_list:
            last_record = self._get_table('device_stats').\
                filter_by(id = device).\
                order_by(desc(self._get_table('device_stats').date)).first()
            result.append({'device' : device, 'date' : last_record.date, 'value' : last_record.value})
        return result

    def add_device_stat(self, ds_device, ds_date, ds_value):
        """
        Add a device stat record
        @param ds_device : device id
        @param ds_date : timestamp
        @param ds_value : stat value
        """
        self._get_table('device_stats').insert(device = ds_device, date = ds_date,
                value = ds_value)
        self._soup.flush()

    def del_device_stat(self, ds_id):
        """
        Delete a stat record
        @param ds_id : record id
        """
        req = self._get_table('device_stats').filter_by(id = ds_id)
        if req.count() > 0:
            device_stat = req.first()
            self._get_table('device_stats').delete(id == device_stat.id)
            self._soup.flush()

    def del_all_device_stats(self, d_id):
        """
        Delete all stats for a device
        @param d_id : device id
        """
        self._get_table('device_stats').delete(self._get_table('device_stats').device == d_id)
        self._soup.flush()
   
 
####
# Triggers
####
    def list_triggers(self):
        """
        Returns a list of all triggers
        @return A list of dictionnary {'id' : trigger id, 'decription' : trigger descripition,
            'rule' : trigger rule, 'result' : trigger result}
        """
        result = []
        for trigger in  self._get_table('trigger').all():
            result.append({'id': trigger.id, 'description': trigger.description, 'rule': trigger.rule, 'result': trigger.result})
        return result

    def get_trigger(self, t_id):
        """
        Returns a trigger information from id
        @param t_id : trigger id
        @return A dictionnary {'id' : trigger id, 'description': trigger decription,
            'rule' : trigger rule, 'result' : trigger result}
        """
        result = []
        request = self._get_table('trigger').filter_by(id = t_id)
        if request.count() > 0:
            trigger = request.first()
            return {'id': trigger.id, 'description': trigger.description, 'rule': trigger.rule, 'result': trigger.result}

    def add_trigger(self, t_desc, t_rule, t_res):
        """
        Add a trigger
        @param t_desc : trigger description
        @param t_rule : trigger rule
        @param t_res : trigger result
        """
        self._get_table('trigger').insert(description = t_desc, rule = t_rule, result = ';'.join(t_res))
        self._soup.flush()

    def del_trigger(self, t_id):
        """
        Delete a trigger
        @param t_id : trigger id
        """
        req = self._get_table('trigger').filter_by(id = t_id)
        if req.count() > 0:
            device_stat = req.first()
            self._get_table('trigger').delete(id == device_stat.id)
            self._soup.flush()


####
# System accounts
####
    def list_system_accounts(self):
        """
        Returns a list of all accounts id/login
        @return A list of dictionnary {'id' : account_id, 'login': account_login}
        """
        result = []
        for account in  self._get_table('system_account').all():
            result.append({'id': account.id, 'login': account.login})
        return result

    def fetch_system_account_informations(self, a_id):
        """
        Returns account informations from id
        @param a_id : account id
        @return A dictionnary {'id' : account id, 'login': account login,
            'password' : account ssha256 encrypted password, 'is_admin' : True if the user is an admin}
        """
        request = self._get_table('system_account').filter_by(id = a_id)
        if request.count() > 0:
            account = request.first()
            return {'id': account.id, 'login': account.login, 
                    'password': account.password, 'is_admin': account.is_admin}

    def add_system_account(self, a_login, a_password, a_is_admin = False):
        """
        Add a system_account
        @param a_login : Account login
        @param a_password : Account clear password (will be hashed in sha256)
        @param a_is_admin : Is an admin account ? 
        """
        
        password = hashlib.sha256()
        password.update(a_password)
        self._get_table('system_account').insert(login = a_login, 
                password = password.hexdigest(), is_admin = a_is_admin)
        self._soup.flush()

    def del_system_account(self, a_id):
        """
        Delete a system account 
        @param a_id : account id
        """
        req = self._get_table('system_account').filter_by(id = a_id)
        if req.count() > 0:
            account = req.first()
            self._get_table('system_account').delete(id == account.id)
            self._soup.flush()
    
    def get_user_system_account(self, u_id):
        """
        Returns the system account associated to a user, if existing
        @param u_id : The user (not system !) account id
        """
        request = self._get_table('user_account').filter_by(id = u_id)
        if request.count() > 0:
            sys_id = request.first().system_account
            return self.fetch_system_account_informations(sys_id)

####
# User accounts
####
    def list_user_accounts(self):
        """
        Returns a list of all user accounts id/first_name/last_name
        @return A list of dictionnary {'id' : account_id, 'first_name' : first_name, 'last_name': last_name}
        """
        result = []
        for account in  self._get_table('user_account').all():
            result.append({'id': account.id, 'first_name' : account.first_name, 'last_name': account.last_name})
        return result

    def fetch_user_account_informations(self, u_id):
        """
        Returns account informations from id
        @param u_id : user account id
        @return A dictionnary {'id' : account id, 'login': account login,
            'password' : account ssha256 encrypted password, 'is_admin' : True if the user is an admin}
        """
        request = self._get_table('user_account').filter_by(id = u_id)
        if request.count() > 0:
            account = request.first()
            return {'id': account.id, 'first_name' : account.first_name, 'last_name': account.last_name, 
                    'birthdate' : account.birthdate, 'system_account' : account.system_account}

    def add_user_account(self, u_first_name, u_last_name, u_birthdate, u_system_account = None):
        """
        Add a user account
        @param u_first_name : User's first name
        @param u_last_name : User's last name
        @param u_birthdate : User's birthdate
        @param u_system_account : User's account on the system (can be None)
        """
        self._get_table('user_account').insert(first_name = u_first_name, last_name = u_last_name,
                birthdate = u_birthdate, system_account = u_system_account)
        self._soup.flush()

    def del_user_account(self, u_id):
        """
        Delete a user account and the associated system  account if it exists
        @param u_id : user's account id
        """
        req = self._get_table('user_account').filter_by(id = u_id)
        if req.count() > 0:
            account = req.first()
            self.del_system_account(self.get_user_system_account(u_id)['id'])
            self._get_table('user_account').delete(id == account.id)
            self._soup.flush()
    

###
# display tests
###
def print_title(title):
    """
    Print a title in color
    """
    COLOR = '\033[92m'
    ENDC = '\033[0m'
    print "\n\n"
    print COLOR
    print "=" * (len(title) + 8)
    print "=== %s ===" % title
    print "=" * (len(title) + 8)
    print ENDC

def print_test(test):
    """
    Print a test title in color
    """
    COLOR = '\033[93m'
    ENDC = '\033[0m'
    print COLOR
    print "= %s =" % test
    print ENDC

if __name__ == "__main__":
    d = DbHelper()
    print_title('test area')
    print_test('list areas')
    print d.list_areas_name()
    print_test('add area')
    print d.add_area('area1','description 1')
    print_test('list areas')
    print d.list_areas_name()
    print_test('fetch informations')
    print d.fetch_area_informations('area1')
    print_test('del area')
    print d.del_area('area1')    
    print_test('list areas')
    print d.list_areas_name() 

    print_title('test room')
    print "== add area =="
    print d.add_area('area1','description 1')
    print_test('list room')
    print d.list_rooms_name()
    print_test('add room')
    print d.add_room('room1', 'area1', 'description 1')
    print_test('list room')
    print d.list_rooms_name()
    print "= get all rooms of area1 "
    print d.get_all_room_of_area('area1')
    print_test('fetch informations')
    print d.fetch_room_informations('room1')
    print_test('del room')
    print d.del_room('room1')    
    print_test('list rooms')
    print d.list_rooms_name() 

    print_title('test device_category')
    print_test('list device_category')
    print d.list_device_categories_name()
    print_test('add device_category')
    print d.add_device_category('device_category 1')
    print_test('list device_category')
    print d.list_device_categories_name()
    print_test('fetch informations')
    print d.fetch_device_category_informations('device_category 1')
    print_test('Get all devices of category')
    print d.get_all_devices_of_category(d.fetch_device_category_informations('device_category 1')['id'])
    print_test('del room')
    print d.del_device_category('device_category 1')    
    print_test('list rooms')
    print d.list_device_categories_name()

    print_title('test device_technology')
    print_test('list device_technology')
    print d.list_device_technologies_name()
    print_test('add device_technology')
    print d.add_device_technology('device_technology 1', 'Device_technology 1 descrition', 'wired')
    print_test('list device_technology')
    print d.list_device_technologies_name()
    print_test('fetch informations')
    print d.fetch_device_technology_informations('device_technology 1')
    print_test('Get all devices of technology')
    print d.get_all_devices_of_technology(d.fetch_device_technology_informations('device_technology 1')['id'])
    print_test('del technology')
    print d.del_device_technology('device_technology 1')    
    print_test('list technology')
    print d.list_device_technologies_name()

    print_title('test device')
    print_test('list device')
    print d.list_devices()
    print_test('add device')
    print "== add device_technology =="
    print d.add_device_technology('device_technology 1', 'Device_technology 1 descrition', 'wired')
    dt_id = d.fetch_device_technology_informations('device_technology 1')['id']
    print "== add device_category =="
    print d.add_device_category('device_category 1')
    dc_id = d.fetch_device_category_informations('device_category 1')['id']
    print "== add area =="
    print d.add_area('area1','description 1')
    print "== add room =="
    print d.add_room('room1', 'area1', 'description 1')
    room_id = d.fetch_room_informations('room1')['id']
    print d.add_device(d_address = 'A3', d_technology = dt_id, d_type = 'appliance', 
        d_category = dc_id, d_room = room_id, d_initial_value = 'off', d_description = 'My first device', 
        d_is_resetable = False, d_is_changeable_by_user = True, d_unit_of_stored_values ='Percent')
    print_test('list device')
    print d.list_devices()
    dev_id = d.list_devices()[0]['id']
    print_test('update device')
    print d.update_device(d_id = dev_id, d_address = 'E2', d_initial_value = 'on')
    print_test('list device')
    print d.list_devices()
    print_test('find devices')
    print d.find_devices(address = 'E2', initial_value = 'on')
    print_test('fetch informations')
    print d.fetch_device_informations(1)
    print_test('del device')
    print d.del_device(1)    
    print_test('list devices')
    print d.list_devices()

    print_title('test device stats')
    print_test('list device')
    print d.list_devices()
    print_test('add device')
    print "== add device_technology =="
    print d.add_device_technology('device_technology 1', 'Device_technology 1 descrition', 'wired')
    dt_id = d.fetch_device_technology_informations('device_technology 1')['id']
    print "== add device_category =="
    print d.add_device_category('device_category 1')
    dc_id = d.fetch_device_category_informations('device_category 1')['id']
    print "== add area =="
    print d.add_area('area1','description 1')
    print "== add room =="
    print d.add_room('room1', 'area1', 'description 1')
    room_id = d.fetch_room_informations('room1')['id']
    print d.add_device(d_address = 'A3', d_technology = dt_id, d_type = 'appliance', 
        d_category = dc_id, d_room = room_id, d_initial_value = 'off', d_description = 'My first device', 
        d_is_resetable = False, d_is_changeable_by_user = True, d_unit_of_stored_values ='Percent')
    print_test('list device')
    print d.list_devices()
    d_id = d.list_devices()[0]['id']
    print_test('fetch informations')
    print d.fetch_device_informations(d_id)
    print_test('list stats')
    print d.list_device_stats(d_id)
    print_test('Add stat')
    from datetime import datetime
    print d.add_device_stat(d_id, datetime.now(), 12)
    print "[[[ sleep 3s ]]]"
    time.sleep(3)
    print d.add_device_stat(d_id, datetime.now(), 12)
    print_test('list stats')
    print d.list_device_stats(d_id)
    print_test('last stat')
    print d.get_last_stat_of_devices([d_id])
    print_test('del stats')
    print d.del_all_device_stats(d_id)
    print_test('list stats')
    print d.list_device_stats(d_id)
    print_test('del device')
    print d.del_device(d_id)    
    print_test('list devices')
    print d.list_devices()

    print_title('test trigger')
    print_test('list triggers')
    print d.list_triggers()
    print_test('add triger')
    print d.add_trigger('Trigger description 1','AND(x,OR(y,z))',['x10_on("a3")','1wire()'])
    print_test('list triggers')
    print d.list_triggers()
    trig_id = d.list_triggers()[0]['id']
    print_test('get trigger')
    print d.get_trigger(trig_id)
    print_test('delete trigger')
    print d.del_trigger(trig_id)
    print_test('list triggers')
    print d.list_triggers()

    print_title('test system account')
    print_test('list system accounts')
    print d.list_system_accounts()
    print_test('add system account')
    print d.add_system_account('login 1','password 1',True)
    print_test('list system accounts')
    print d.list_system_accounts()
    acc_id = d.list_system_accounts()[0]['id']
    print_test('get system account')
    print d.fetch_system_account_informations(acc_id)
    print_test('delete system account')
    print d.del_system_account(acc_id)
    print_test('list system accounts')
    print d.list_system_accounts()

    print_title('test user account')
    print_test('list users accounts')
    print d.list_user_accounts()
    print_test('add system account')
    print d.add_system_account('login 1','password 1',True)
    sys_id = d.list_system_accounts()[0]['id']
    print_test('add user account')
    print d.add_user_account('first name 1', 'last name 1', datetime.now(), sys_id)
    print_test('list user accounts')
    print d.list_user_accounts()
    acc_id = d.list_user_accounts()[0]['id']
    print_test('get user account')
    print d.fetch_user_account_informations(acc_id)
    print_test('get user system account')
    print d.get_user_system_account(acc_id)
    print_test('delete user account')
    print d.del_user_account(acc_id)
    print_test('list user accounts')
    print d.list_user_accounts()


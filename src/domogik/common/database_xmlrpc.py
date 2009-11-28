#!/usr/bin/python
# -*- coding: utf-8 -*-

''' This file is part of B{Domogik} project (U{http://www.domogik.org}).

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

Mapping of database API for use with XMLRPC

Implements
==========

- XmlRpcDbHelper

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
'''

from database import DbHelper 

class XmlRpcDbHelper():
    ''' This class provides a mapping of DbHelper methods to use them throw xmlrpc
    '''

    def __init__(self):
        self._db = DbHelper()

####
# Areas 
####

    def list_areas(self):
        ''' Get the list of areas and return it as a list of tuples 
        @return a list of tuple (id, name, description)
        '''
        areas = self._db.list_areas()
        res = []
        for area in areas:
            res.append((area.id, area.name, area.description))
        return res

    def search_areas(self, **filters):
        ''' Look for area(s) with filter on their attributes
        @return a list of areas as tuple (id, name, description)
        '''
        areas = self._db.search_areas(filters)
        res = []
        for area in areas:
            res.append((area.id, area.name, area.description))
        return res

    def get_area_by_id(self, area_id):
        ''' Fetch area informations 
        @param area_id : The area's id 
        @return a tuple (id, name, description)
        '''
        area = self._db.get_area_by_id(area_id)
        if area is not None:
            return (area.id, area.name, area.description)
        else:
            return None

    def get_area_by_name(self, area_name):
        ''' Fetch area informations 
        @param area_name : The area's name 
        @return a tuple (id, name, description)
        '''
        area = self._db.get_area_by_name(area_name)
        if area is not None:
            return (area.id, area.name, area.description)
        else:
            return None

    def add_area(self, a_name, a_description = None):
        '''Add an area
        @param a_name : area's name
        @param a_description : area detailed description (optional)
        @return an area definition : (id, name, description)
        '''
        area = self._db.add_area(a_name, a_description)
        return (area.id, area.name, area.description)

    def del_area(self, area_id):
        ''' Delete an area record
        @warning it will also remove all the rooms in the area and all devices 
        + stats in each deleted rooms
        @param area_id : area's id
        '''
        self._db.del_area(area_id)
        


####
# Rooms
####

    def list_rooms(self):
        ''' Get the list of rooms and return it as a list of tuples 
        @return a list of tuple (id, name, description, area_id)
        '''
        rooms = self._db.list_rooms()
        res = []
        for room in rooms:
            res.append((room.id, room.name, room.description, room.area_id))
        return res

    def search_rooms(self, **filters):
        ''' Look for room(s) with filter on their attributes
        @return a list of rooms as tuple (id, name, description, area_id)
        '''
        rooms = self._db.search_rooms(filters)
        res = []
        for room in rooms:
            res.append((room.id, room.name, room.description, room.area_id)
        return res

    
    def get_room_by_id(self, room_id):
        ''' Fetch room informations 
        @param room_id : The room's id 
        @return a tuple (id, name, description)
        '''
        room = self._db.get_room_by_id(room_id)
        if room is not None:
            return (room.id, room.name, room.description, room.area_id)
        else:
            return None

    def get_room_by_name(self, room_name):
        ''' Fetch room informations 
        @param room_name : The room's name 
        @return a tuple (id, name, description)
        '''
        room = self._db.get_room_by_name(room_name)
        if room is not None:
            return (room.id, room.name, room.description, room.area_id)
        else:
            return None

    def add_room(self, r_name, r_area_id, r_description = None):
        '''Add an room
        @param r_name : room's name
        @param r_description : room detailed description (optional)
        @param r_area_id : id of the area where the room is
        @return an room definition : (id, name, description)
        '''
        room = self._db.add_room(r_name, r_area_id, r_description)
        return (room.id, room.name, room.description, room.area_id)

    def del_room(self, room_id):
        ''' Delete an room record
        @warning it will also remove all the rooms in the room and all devices 
        + stats in each deleted rooms
        @param room_id : room's id
        '''
        self._db.del_room(room_id)

    def get_all_rooms_of_area(self, a_area_id):
        ''' Returns all the rooms of an area 
        @param a_area_id : the area id
        @return a list of Room objects
        '''
        rooms = self._db.get_all_rooms_of_area(a_area_id)
        for room in rooms:
            res.append((room.id, room.name, room.description, room.area_id, room.area))
        return res

####
# Device category
####

    def list_device_categories(self):
        ''' Get the list of device_categories and return it as a list of tuples 
        @return a list of tuple (id, name, description)
        '''
        device_categories = self._db.list_device_categories()
        res = []
        for device_category in device_categories:
            res.append((device_category.id, device_category.name, device_category.description))
        return res

    def get_device_category_by_name(self, device_category_name):
        ''' Fetch device_category informations 
        @param device_category_name : The device_category's name 
        @return a tuple (id, name, description)
        '''
        device_category = self._db.get_device_category_by_name(device_category_name)
        if device_category is not None:
            return (device_category.id, device_category.name, device_category.description)
        else:
            return None

    def add_device_category(self, d_name, d_description = None):
        '''Add an device_category
        @param d_name : device_category's name
        @param d_description : device_category detailed description (optional)
        @return a device_category definition : (id, name)
        '''
        device_category = self._db.add_device_category(d_name, d_description)
        return (device_category.id, device_category.name, device_category.description)

    def del_device_category(self, device_category_id):
        ''' Delete an device_category record
        Warning, it will also remove all the devices using this category
        @param device_category_id : device_category's id
        '''
        self._db.del_device_category(device_category_id)


####
# Device technology
####

    def list_device_technologies(self):
        ''' Get the list of device_technologies and return it as a list of tuples 
        @return a list of tuple (id, name, description, type)
        '''
        device_technologies = self._db.list_device_technologies()
        res = []
        for device_technology in device_technologies:
            res.append((device_technology.id, device_technology.name, device_technology.description, device_technology.type))
        return res

    def get_device_technology_by_name(self, device_technology_name):
        ''' Fetch device_technology informations 
        @param device_technology_name : The device_technology's name 
        @return a tuple (id, name, description, type)
        '''
        device_technology = self._db.get_device_technology_by_name(device_technology_name)
        if device_technology is not None:
            return (device_technology.id, device_technology.name, device_technology.description, device_technology.type)
        else:
            return None

    def add_device_technology(self, d_name, d_description = None, d_type = None):
        '''Add an device_technology
        @param d_name : device_technology's name
        @param d_description : device_technology detailed description (optional)
        @param d_type : type of the technology, one of 'cpl', 'wired', 'wifi', 'wireless', 'ir'
        @return a device_technology definition : (id, name, description, type)
        '''
        device_technology = self._db.add_device_technology(d_name, d_description)
        return (device_technology.id, device_technology.name, device_technology.description, device_technology.type)

    def del_device_technology(self, device_technology_id):
        ''' Delete an device_technology record
        Warning, it will also remove all the devices using this technology
        @param device_technology_id : device_technology's id
        '''
        self._db.del_device_technology(device_technology_id)


####
# Device technology_config
####

    def list_device_technology_config(self):
        ''' Get the list of device_technology_config and return it as a list of tuples 
        @return a list of tuple (id, key, value, description, technology_id)
        '''
        device_technology_config = self._db.list_device_technology_config()
        res = []
        for device_technology_config in device_technology_config:
            res.append((device_technology_config.id, device_technology_config.key, device_technology_config.value, 
                    device_technology_config.description, device_technology_config.technology_id))
        return res

    def get_device_technology_config(self, device_technology_id, device_technology_config_key):
        ''' Return informations about a device technology config item
        @param device_technology_config_name : The device_technology_config's name 
        @return a tuple (id, key, value, description, technology_id)
        '''
        device_technology_config = self._db.get_device_technology_config_by_name(device_technology_config_name)
        if device_technology_config is not None:
            return (device_technology_config.id, device_technology_config.key, device_technology_config.value, 
                    device_technology_config.description, device_technology_config.technology_id)
        else:
            return None

    def add_device_technology_config(self, device_technology_id, device_technology_config_key, 
            device_technology_config_value, device_technology_config_description=None):
        '''Add an device_technology_config
        @param device_technology_config_id: The device technology id
        @param device_technology_config_key : configuration item
        @param device_technology_config_value : configuration value
        @param device_technology_config_description : configuration description
        @return a device_technology_config definition : (id, key, value, description, technology_id)
        '''
        device_technology_config = self._db.add_device_technology_config(device_technology_id, 
                device_technology_config_key, device_technology_config_value, device_technology_config_description)
        return (device_technology_config.id, device_technology_config.key, 
                device_technology_config.value, device_technology_config.description, 
                device_technology_config.technology_id)

    def del_device_technology_config(self, device_technology_config_id):
        ''' Delete a device technology config record
        @param device_technology_config_id : config item's id
        '''
        self._db.del_device_technology_config(device_technology_config_id)


####
# devices 
####

    def list_devices(self):
        ''' Get the list of devices and return it as a list of tuples 
        @return a list of tuple (id, name, description, address, reference, technology_id,
        type, category_id, room_id, is_resetable, initial_value,is_value_changeable_by_user, 
        unit_of_stored_values)
        '''
        devices = self._db.list_devices()
        res = []
        for device in devices:
            res.append((device.id, device.name, device.description, device.address, device.reference,
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values))
        return res

    def search_devices(self, **filters):
        ''' Look for device(s) with filter on their attributes
        @return a list of tuple (id, name, description, address, reference, technology_id,
        type, category_id, room_id, is_resetable, initial_value,is_value_changeable_by_user, 
        unit_of_stored_values)
        '''
        devices = self._db.search_devices(filters)
        res = []
        for device in devices:
            res.append((device.id, device.name, device.description, device.address, device.reference,
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values))
        return res

    def find_devices(self, d_room_id_list, d_category_id_list):
        '''Look for devices that have at least 1 item in room_id_list AND 1 item in category_id_list
        @param room_id_list : list of room ids
        @param category_id_list : list of category ids
        @return a list of tuple (id, name, description, address, reference, technology_id,
        type, category_id, room_id, is_resetable, initial_value,is_value_changeable_by_user, 
        unit_of_stored_values)
        '''
        devices = self._db.find_devices(d_room_id_list, d_category_id_list)
        res = []
        for device in devices:
            res.append((device.id, device.name, device.description, device.address, device.reference,
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values))
        return res

    def get_device(self, device_id):
        ''' Return a device by its id
        @param device_id : The device's id
        @return a list of tuple (id, name, description, address, reference, technology_id,
        type, category_id, room_id, is_resetable, initial_value,is_value_changeable_by_user, 
        unit_of_stored_values)
        '''
        device = self._db.get_device(device_id)
        if device is not None:
            return (device.id, device.name, device.description, device.address, device.reference
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values)
        else:
            return None

    def add_device(self, d_name, d_address, d_technology_id, d_type, d_category_id, d_room_id, 
        d_description=None, d_reference=None, d_is_resetable=False, d_initial_value=None,
        d_is_value_changeable_by_user=False, d_unit_of_stored_values=None):
        ''' Add a device item
        @param d_name : name of the device
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_technology_id : technology id
        @param d_type : One of 'appliance','light','music','sensor'
        @param d_category_id : category id
        @param d_room_id : room id
        @param d_description : Extended item description (100 char max)
        @param d_reference : device reference (ex. AM12 for x10)
        @param d_is_resetable : Can the item be reseted to some initial state (optional, default=False)
        @param d_initial_value : What's the initial value of the item, should be
            the state when the item is created (except for sensors, music) (optional, default=None)
        @param d_is_value_changeable_by_user : Can a user change item state (ex : false for sensor)
            (optional, default=False)
        @param d_unit_of_stored_values : What is the unit of item values,
                must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean' (optional, default=None)
        @return the new Device object
        '''        
        device = self._db.add_device(d_name, d_address, d_technology_id, d_type, d_category_id, d_room_id, 
        d_description, d_reference, d_is_resetable=False, d_initial_value,
        d_is_value_changeable_by_user=False, d_unit_of_stored_values)
        if device is not None:
            return (device.id, device.name, device.description, device.address, device.reference
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values)

    def update_device(self = None, d_id = None, d_name = None, d_address = None, d_technology_id = None,
        d_type = None, d_category_id = None, d_room_id = None, 
        d_description= None, d_reference= None, d_is_resetable=False, d_initial_value= None,
        d_is_value_changeable_by_user=False, d_unit_of_stored_values=None):
        ''' Update a device item
        @param d_id : device id
        @param d_name : name of the device
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_technology_id : technology id
        @param d_type : One of 'appliance','light','music','sensor'
        @param d_category_id : category id
        @param d_room_id : room id
        @param d_description : Extended item description (100 char max)
        @param d_reference : device reference (ex. AM12 for x10)
        @param d_is_resetable : Can the item be reseted to some initial state (optional, default=False)
        @param d_initial_value : What's the initial value of the item, should be
            the state when the item is created (except for sensors, music) (optional, default=None)
        @param d_is_value_changeable_by_user : Can a user change item state (ex : false for sensor)
            (optional, default=False)
        @param d_unit_of_stored_values : What is the unit of item values,
                must be one of 'Volt', 'Celsius', 'Fahrenheit', 'Percent', 'Boolean' (optional, default=None)
        @return the new Device object
        '''        
        device = self._db.update_device(d_id, d_name, d_address, d_technology_id, d_type, d_category_id, d_room_id, 
        d_description, d_reference, d_is_resetable=False, d_initial_value,
        d_is_value_changeable_by_user=False, d_unit_of_stored_values)
        if device is not None:
            return (device.id, device.name, device.description, device.address, device.reference
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values)

    def get_all_devices_of_room(self, room_id):
        ''' Return all the devices of a rooms
        @param room_id : The id of the room 
        @return a list a tuple 
        '''
        devices = self._db.get_all_devices_of_room(room_id)
        res = []
        for device in devices:
            res.append((device.id, device.name, device.description, device.address, device.reference,
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values))
        return res

    def get_all_devices_of_area(self, area_id):
        ''' Return all the devices of a areas
        @param area_id : The id of the area 
        @return a list a tuple 
        '''
        devices = self._db.get_all_devices_of_area(area_id)
        res = []
        for device in devices:
            res.append((device.id, device.name, device.description, device.address, device.reference,
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values))
        return res

    def get_all_devices_of_category(self, category_id):
        ''' Return all the devices of a category
        @param category_id : The id of the category 
        @return a list of tuple 
        '''
        devices = self._db.get_all_devices_of_category(category_id)
        res = []
        for device in devices:
            res.append((device.id, device.name, device.description, device.address, device.reference,
                device.technology_id, device.type, device.category_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values))
        return res

     def get_all_devices_of_technology(self, technology_id):
        ''' Return all the devices of a technology
        @param technology_id : The id of the technology 
        @return a list of tuple 
        '''
        devices = self._db.get_all_devices_of_technology(technology_id)
        res = []
        for device in devices:
            res.append((device.id, device.name, device.description, device.address, device.reference,
                device.technology_id, device.type, device.technology_id, device.room_id,
                device.is_resetable, device.initial_value, device.is_value_changeable_by_user,
                device.unit_of_stored_values))
        return res
    
    def del_device(self, device_id):
        ''' Delete a device record
        Warning : this deletes also the associated objects (DeviceConfig, DeviceStats, DeviceStatsValue)
        @param device_id : device's id
        '''
        self._db.del_device(device_id)
        
####
# Device stats
####
    def list_device_stats(self, d_device_id):
        ''' Return a list of all stats for a device
        @param d_device_id : the device id
        @warning this won't list device  stat values
        @return a list of tuple (id, device_id, date) 
        '''
        stat = self._db.list_device_stats(d_device_id)
        if stat is not None:
            return (stat.id, stat.device_id, stat.date)

    def list_device_stats_values(self, d_device_stats_id):
        ''' Return a list of all values associated to a device statistic
        @param d_device_stats_id : the device statistic id
        @return a list of tuple (device_stat_value.id, device_stat_value.name, device_stat_value.value)
        '''
        stats = self._db.list_device_stats_values(d_device_stats_id)
        res = []
        for stat in stats:
            res.append((stat.id, stat.name, stat.value))
        return res

    def get_last_stat_of_device(self, d_device_id):
        '''Fetch the last record of stats for a device
        @param d_device_id : device id
        @return a tuple (device_stat.id, device_stat.device_id, device_stat.date)
        '''
        stat = self._db.get_last_stat_of_devices(d_device_id)
        if stat is not None:
            return ((stat.id, stat.device_id, stat.date)

    def get_last_stat_of_devices(self, device_list):
        '''
        Fetch the last record for all devices in d_list
        @param device_list : list of device ids
        @return a list of tuples (device_stat.id, device_stat.device_id, device_stat.date)
        '''
        stats = self._db.get_last_stat_of_devices(device_list)
        res = []
        for stat in stats:
            res.append((stat.id, stat.device_id, stat.date))
        return res

    def device_has_stats(self, d_device_id):
        '''Check if the device has stats that were recorded
        @param d_device_id : device id
        @return True or False
        '''
        return self._db.device_has_stats(d_device_id)

    def add_device_stat(self, d_id, ds_date, ds_values):
        ''' Add a device stat record
        @param device_id : device id
        @param ds_date : when the stat was gathered (timestamp)
        @param ds_value : dictionnary of statistics values
        @return a tupe of the new devicestat object: (id, device_id, date)
        '''
        stat = self._db.add_device_stat(d_id, ds_date, ds_values)
        if stat is not None:
            return (stat.id, stat.device_id, stat.date)

    def del_device_stat(self, ds_id):
        ''' Delete a stat record
        It will delete all stat values of this stat entry
        @param ds_id : record id
        '''
        self._db.del_device_stat(ds_id)

    def del_all_device_stats(self, d_id):
        '''
        Delete all stats for a device
        @param d_id : device id
        '''
        self._db.del_all_device_stats(d_id)

 
####
# Triggers
####
    def list_triggers(self):
        ''' Returns a list of all triggers
        @return a list of tuple (id, description, rule, result)
        '''
        triggers = self._db.list_triggers()
        res = []
        for trigger in triggers:
            res.append((trigger.id, trigger.description, trigger.rule, trigger.result))
        return res

    def get_trigger(self, t_id):
        ''' Returns a trigger information from id
        @param t_id : trigger id
        @return a Trigger object
        '''
        trigger = self._db.get_trigger(t_id)
        return (trigger.id, trigger.description, trigger.rule, trigger.result)

    def add_trigger(self, t_description, t_rule, t_result):
        ''' Add a trigger
        @param t_desc : trigger description
        @param t_rule : trigger rule
        @param t_res : trigger result
        @return the new Trigger object
        '''
        trigger = self._db.add_trigger(t_description, t_rule, t_result)
        return (trigger.id, trigger.description, trigger.rule, trigger.result)

    def del_trigger(self, t_id):
        '''
        Delete a trigger
        @param t_id : trigger id
        '''
        trigger = self._session.query(Trigger).filter_by(id=t_id).first()
        self._session.delete(trigger)
        self._session.commit()

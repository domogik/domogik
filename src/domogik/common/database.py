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

# $LastChangedBy:$
# $LastChangedDate:$
# $LastChangedRevision:$

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

from domogik.common.configloader import Loader

class DbHelper():
    """
    This class provides methods to fetch and put informations on the Domogik database
    The user should only use methods from this class and don't access the database directly
    """

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
        ref = eval("self._soup.%s_%s" % (self._dbprefix, table_name))
        return ref

####
# Areas
####
    def list_areas_name(self):
        """
        Returns a list of areas' name
        """
        result = []
        for area in  self._get_table('area').all():
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
        Return informations about an room
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
        Add an room
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
        Add an device_category
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
        Add an device_technology
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



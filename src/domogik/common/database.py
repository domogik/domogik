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
# 
if __name__ == "__main__":
    d = DbHelper()
    print "================="
    print "=== test area ==="
    print "================="
    print "= list areas ="
    print d.list_areas_name()
    print "= add area ="
    print d.add_area('area1','description 1')
    print "= list areas ="
    print d.list_areas_name()
    print "= fetch informations ="
    print d.fetch_area_informations('area1')
    print "= del area ="
    print d.del_area('area1')    
    print "= list areas ="
    print d.list_areas_name() 
    print "\n\n================="
    print "=== test room ==="
    print "================="
    print "= add area ="
    print d.add_area('area1','description 1')
    print "= list room ="
    print d.list_rooms_name()
    print "= add room ="
    print d.add_room('room1', 'area1', 'description 1')
    print "= list room ="
    print d.list_rooms_name()
    print "= get all rooms of area1 "
    print d.get_all_room_of_area('area1')
    print "= fetch informations ="
    print d.fetch_room_informations('room1')
    print "= del room ="
    print d.del_room('room1')    
    print "= list rooms ="
    print d.list_rooms_name() 
    print "\n\n================="
    print "=== test device_category ==="
    print "================="
    print "= list device_category ="
    print d.list_device_categories_name()
    print "= add device_category ="
    print d.add_device_category('device_category 1')
    print "= list device_category ="
    print d.list_device_categories_name()
    print "= fetch informations ="
    print d.fetch_device_category_informations('device_category 1')
    print "= Get all devices of category ="
    print d.get_all_devices_of_category(d.fetch_device_category_informations('device_category 1')['id'])
    print "= del room ="
    print d.del_device_category('device_category 1')    
    print "= list rooms ="
    print d.list_device_categories_name()
    print "\n\n================="
    print "=== test device_tegnology==="
    print "================="
    print "= list device_technology ="
    print d.list_device_technologies_name()
    print "= add device_technology ="
    print d.add_device_technology('device_technology 1', 'Device_technology 1 descrition', 'wired')
    print "= list device_technology ="
    print d.list_device_technologies_name()
    print "= fetch informations ="
    print d.fetch_device_technology_informations('device_technology 1')
    print "= Get all devices of technology ="
    print d.get_all_devices_of_technology(d.fetch_device_technology_informations('device_technology 1')['id'])
    print "= del room ="
    print d.del_device_technology('device_technology 1')    
    print "= list rooms ="
    print d.list_device_technologies_name()

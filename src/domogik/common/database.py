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
    def list_areas(self):
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
        try:
            request = self._get_table('area').filter_by(name = area).first()
            return {'id' : request.id, 'name' : request.name, 'description' : request.description}
        except AttributeError:
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
        area = self._get_table('area').filter_by(name = a_name).first()
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
    def list_rooms(self):
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
#        try:
        request = self._get_table('room').filter_by(name = room).first()
        return {'id' : request.id, 'name' : request.name, 'area' : request.area,'description' : request.description}
#        except AttributeError:
#            return None

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
        room = self._get_table('room').filter_by(name = r_name).first()
        devices = self._get_table('device').filter_by(room = room.id).all()
        self._get_table('room').delete(id == room.id)
        for device in devices:
            self._get_table('device').delete(id == device.id)
        self._get_table('room').delete(id == room.id)
        self._soup.flush()


if __name__ == "__main__":
    d = DbHelper()
    print "================="
    print "=== test area ==="
    print "================="
    print "= list areas ="
    print d.list_areas()
    print "= add area ="
    print d.add_area('area1','description 1')
    print "= list areas ="
    print d.list_areas()
    print "= fetch informations ="
    print d.fetch_area_informations('area1')
    print "= del area ="
    print d.del_area('area1')    
    print "= list areas ="
    print d.list_areas() 
    print "\n\n================="
    print "=== test room ==="
    print "================="
    print "= add area ="
    print d.add_area('area1','description 1')
    print "= list room ="
    print d.list_rooms()
    print "= add room ="
    print d.add_room('room1', 'area1', 'description 1')
    print "= list room ="
    print d.list_rooms()
    print "= fetch informations ="
    print d.fetch_room_informations('room1')
    print "= del room ="
    print d.del_room('room1')    
    print "= list rooms ="
    print d.list_rooms() 

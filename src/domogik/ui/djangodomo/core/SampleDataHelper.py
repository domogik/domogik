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

Load sample data

Implements
==========

- class SampleDataHelper

@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

#!/usr/bin/python
#-*- encoding:utf-8 *-*

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

# Author : Marc Schneider <marc@domogik.org>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2009-02-22 11:45:39 +0100 (dim. 22 févr. 2009) $
# $LastChangedRevision: 391 $


class SampleDataHelper:
    """
    Class to load / clear sample data
    """

    def __init__(self, db):
        """
        Class constructor
        @param db : an instance of DbHelper class to connect to the db API
        """
        self._db = db

    def remove(self):
        """
        Remove all sample data
        """
        for area in self._db.list_areas():
            self._db.del_area(area.id)

        for dt in self._db.list_device_technologies():
            self._db.del_device_technology(dt.id)

        for dc in self._db.list_device_categories():
            self._db.del_device_category(dc.id)

        for trigger in self._db.list_triggers():
            self._db.del_trigger(trigger.id)

        for user_acc in self._db.list_user_accounts():
            self._db.del_user_account(user_acc.id)

        for sys_acc in self._db.list_system_accounts():
            self._db.del_system_account(sys_acc.id)

        self._db.del_all_system_stats()

    def create(self):
        """
        Create sample data
        """
        self.remove()

        self._db.update_system_config(s_simulation_mode=True, s_admin_mode=True, s_debug_mode=True)

        # Create sample objects
        x10 = self._db.add_device_technology(dt_name="x10", 
                                            dt_description="x10 techno", 
                                            dt_type="cpl")
        plcbus = self._db.add_device_technology(dt_name="plcbus", 
                                                dt_description="plcbus techno", 
                                                dt_type="cpl")
        onewire = self._db.add_device_technology(dt_name="1-wire", 
                                                dt_description="1-wire techno", 
                                                dt_type="wired")

        temperature_cat = self._db.add_device_category(dc_name="Temperature")
        heating_cat = self._db.add_device_category(dc_name="Heating")
        lighting_cat = self._db.add_device_category(dc_name="Lighting")
        music_cat = self._db.add_device_category(dc_name="Music")
        appliance_cat = self._db.add_device_category(dc_name="Appliance")

        basement = self._db.add_area(a_name="Basement")
        ground_floor = self._db.add_area(a_name="Ground floor")
        first_floor = self._db.add_area(a_name="First floor")

        bedroom1 = self._db.add_room(r_name="Bedroom 1", r_area_id=first_floor.id)
        bedroom2 = self._db.add_room(r_name="Bedroom 2", r_area_id=first_floor.id)
        lounge = self._db.add_room(r_name="Lounge", r_area_id=ground_floor.id)
        kitchen = self._db.add_room(r_name="Kitchen", r_area_id=ground_floor.id)
        bathroom = self._db.add_room(r_name="Bathroom", r_area_id=first_floor.id)
        cellar = self._db.add_room(r_name="Cellar", r_area_id=basement.id)

        bedroom1_beside_lamp = self._db.add_device(
            d_name="Beside lamp", d_address="A1", d_technology_id=x10.id, d_type=u"appliance", d_reference="AM12",
            d_category_id=lighting_cat.id, d_room_id=bedroom1.id, d_is_resetable=True, d_initial_value="off", 
            d_is_value_changeable_by_user=True, d_unit_of_stored_values=None
        )
        bedroom1_lamp = self._db.add_device(
            d_name="Lamp", d_address="A2", d_technology_id=x10.id, d_type=u"lamp", d_category_id=lighting_cat.id,
            d_reference="LM12", d_room_id=bedroom1.id, d_is_resetable=True, 
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values="Percent"
        )
        bedroom2_beside_lamp = self._db.add_device(
            d_name="Beside lamp", d_address="B1", d_technology_id=x10.id, d_type=u"appliance", d_reference="AM12",
            d_category_id=lighting_cat.id, d_room_id=bedroom2.id, d_is_resetable=True, d_initial_value="off", 
            d_is_value_changeable_by_user=True, d_unit_of_stored_values=None
        )
        bedroom2_lamp = self._db.add_device(
            d_name="Lamp", d_address="B2", d_technology_id=x10.id, d_type=u"lamp", d_category_id=lighting_cat.id,
            d_reference="LM12", d_room_id=bedroom2.id, d_is_resetable=True, 
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values="Percent"
        )
        lounge_lamp = self._db.add_device(
            d_name="Lamp", d_address="C1", d_technology_id=x10.id, d_type=u"lamp", d_category_id=lighting_cat.id,
            d_reference="LM12", d_room_id=lounge.id, d_is_resetable=True, 
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values="Percent"
        )
        kitchen_lamp = self._db.add_device(
            d_name="Lamp", d_address="D1", d_technology_id=x10.id, d_type=u"lamp", d_category_id=lighting_cat.id,
            d_reference="LM12", d_room_id=kitchen.id, d_is_resetable=True, 
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values="Percent"
        )
        kitchen_coffee_machine = self._db.add_device(
            d_name="Coffee machine", d_address="D2", d_technology_id=x10.id, d_type=u"appliance", 
            d_category_id=appliance_cat.id, d_reference="AM12", d_room_id=kitchen.id, d_is_resetable=True, 
            d_initial_value="off", d_is_value_changeable_by_user=True, d_unit_of_stored_values=None
        )

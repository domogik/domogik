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


class SampleDataHelper:
    """
    Class to load / clear sample data
    """

    def __init__(self, db):
        """
        Class constructor
        @param db : an instance of DbHelper class to connect to the db API
        """
        self.__db = db

    def remove(self):
        """
        Remove all sample data
        """
        for area in self.__db.list_areas():
            self.__db.del_area(area.id, cascade_delete=True)

        for dt in self.__db.list_device_technologies():
            self.__db.del_device_technology(dt.id, cascade_delete=True)

        for du in self.__db.list_device_usages():
            self.__db.del_device_usage(du.id, cascade_delete=True)

        for dty in self.__db.list_device_types():
            self.__db.del_device_type(dty.id, cascade_delete=True)

        for trigger in self.__db.list_triggers():
            self.__db.del_trigger(trigger.id, cascade_delete=True)

        for user_acc in self.__db.list_user_accounts():
            self.__db.del_user_account(user_acc.id)

        self.__db.del_all_system_stats()

    def create(self):
        """
        Create sample data
        """
        self.remove()

        # Add default administrator
        self.__db.add_default_user_account()

        self.__db.update_system_config(s_simulation_mode=True, s_debug_mode=True)

        # Create sample objects
        x10 = self.__db.add_device_technology(dt_name=u"x10",
                                            dt_description="x10 techno")
        plcbus = self.__db.add_device_technology(dt_name=u"PLCBus",
                                                dt_description="plcbus techno")
        onewire = self.__db.add_device_technology(dt_name=u"1wire",
                                                dt_description="1-wire techno")

        temperature_cat = self.__db.add_device_usage(du_name="Temperature")
        heating_cat = self.__db.add_device_usage(du_name="Heating")
        lighting_cat = self.__db.add_device_usage(du_name="Lighting")
        music_cat = self.__db.add_device_usage(du_name="Music")
        appliance_cat = self.__db.add_device_usage(du_name="Appliance")

        x10_switch = self.__db.add_device_type('Switch', x10.id, 'x10 Switch')
        x10_dimmer = self.__db.add_device_type('Dimmer', x10.id, 'x10 Dimmer')
        plcbus_switch = self.__db.add_device_type('Switch', plcbus.id, 'PLCBus switch')
        plcbus_dimmer = self.__db.add_device_type('Dimmer', plcbus.id, 'PLCBus dimmer')

        basement = self.__db.add_area(a_name="Basement")
        ground_floor = self.__db.add_area(a_name="Ground floor")
        first_floor = self.__db.add_area(a_name="First floor")

        bedroom1 = self.__db.add_room(r_name="Bedroom 1", r_area_id=first_floor.id)
        bedroom2 = self.__db.add_room(r_name="Bedroom 2", r_area_id=first_floor.id)
        lounge = self.__db.add_room(r_name="Lounge", r_area_id=ground_floor.id)
        kitchen = self.__db.add_room(r_name="Kitchen", r_area_id=ground_floor.id)
        bathroom = self.__db.add_room(r_name="Bathroom", r_area_id=first_floor.id)
        cellar = self.__db.add_room(r_name="Cellar", r_area_id=basement.id)

        bedroom1_beside_lamp = self.__db.add_device(
            d_name="Beside lamp", d_address="A1", d_reference="AM12",
            d_usage_id=lighting_cat.id, d_type_id=x10_switch.id,
            d_room_id=bedroom1.id, d_is_resetable=True, d_initial_value="off",
            d_is_value_changeable_by_user=True, d_unit_of_stored_values=None
        )
        bedroom1_lamp = self.__db.add_device(
            d_name="Lamp", d_address="A2", d_type_id=x10_dimmer.id, d_usage_id=lighting_cat.id,
            d_reference="LM12", d_room_id=bedroom1.id, d_is_resetable=True,
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values=u"Percent"
        )
        bedroom2_beside_lamp = self.__db.add_device(
            d_name="Beside lamp", d_address="B1", d_reference="AM12",
            d_usage_id=lighting_cat.id, d_type_id=plcbus_switch.id,
            d_room_id=bedroom2.id, d_is_resetable=True, d_initial_value="off",
            d_is_value_changeable_by_user=True, d_unit_of_stored_values=None
        )
        bedroom2_lamp = self.__db.add_device(
            d_name="Lamp", d_address="B2", d_usage_id=lighting_cat.id,
            d_reference="LM12", d_type_id=plcbus_dimmer.id, d_room_id=bedroom2.id, d_is_resetable=True,
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values=u"Percent"
        )
        lounge_lamp = self.__db.add_device(
            d_name="Lamp", d_address="C1", d_usage_id=lighting_cat.id,
            d_reference="LM12", d_type_id=plcbus_dimmer.id, d_room_id=lounge.id, d_is_resetable=True,
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values=u"Percent"
        )
        kitchen_lamp = self.__db.add_device(
            d_name="Lamp", d_address="D1", d_usage_id=lighting_cat.id,
            d_reference="LM12", d_type_id=x10_dimmer.id, d_room_id=kitchen.id, d_is_resetable=True,
            d_initial_value="100", d_is_value_changeable_by_user=True, d_unit_of_stored_values=u"Percent"
        )
        kitchen_coffee_machine = self.__db.add_device(
            d_name="Coffee machine", d_address="D2", d_usage_id=appliance_cat.id,
            d_type_id=plcbus_switch.id, d_reference="AM12", d_room_id=kitchen.id, d_is_resetable=True,
            d_initial_value="off", d_is_value_changeable_by_user=True, d_unit_of_stored_values=None
        )
        """
        bedroom1_icon = self.__db.add_item_ui_config(bedroom1.id, 'room', {'icon':'bedroom'})
        bedroom2_icon = self.__db.add_item_ui_config(bedroom2.id, 'room', {'icon':'bedroom'})
        lounge_icon = self.__db.add_item_ui_config(lounge.id, 'room', {'icon':'tvlounge'})
        kitchen_icon = self.__db.add_item_ui_config(kitchen.id, 'room', {'icon':'kitchen'})
        bathroom_icon = self.__db.add_item_ui_config(bathroom.id, 'room', {'icon':'bathroom'})

        basement_icon = self.__db.add_item_ui_config(basement.id, 'area', {'icon':'basement'})
        groundfloor_icon = self.__db.add_item_ui_config(ground_floor.id, 'area', {'icon':'grndfloor'})
        firstfloor_icon = self.__db.add_item_ui_config(first_floor.id, 'area', {'icon':'firstfloor'})
        """

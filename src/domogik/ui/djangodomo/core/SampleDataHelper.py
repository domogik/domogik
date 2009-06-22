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

Load sample datas (deprecated)

Implements
==========

- SampleDataHelper:.remove(self)
- SampleDataHelper:.create(self)

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

from djangodomo.core.models import Area
from djangodomo.core.models import Room
from djangodomo.core.models import DeviceCategory
from djangodomo.core.models import DeviceTechnology
from djangodomo.core.models import DeviceStats
from djangodomo.core.models import Device
from djangodomo.core.models import ApplicationSetting


class SampleDataHelper:
    """
    Class to load / clear sample data
    """

    def remove(self):
        ApplicationSetting.objects.all().delete()
        DeviceCategory.objects.all().delete()
        DeviceTechnology.objects.all().delete()
        DeviceStats.objects.all().delete()
        Device.objects.all().delete()
        Room.objects.all().delete()
        Area.objects.all().delete()

    def create(self):
        self.remove()

        ApplicationSetting.objects.create(simulation_mode=True, admin_mode=True,
                debug_mode=True)

        # Create sample objects
        x10 = DeviceTechnology.objects.create(name="x10", type="cpl")
        plcbus = DeviceTechnology.objects.create(name="plcbus", type="cpl")
        onewire = DeviceTechnology.objects.create(name="1-wire",
                                                  type="wired_bus")

        temperatureCat = DeviceCategory.objects.create(name="Temperature")
        heatingCat = DeviceCategory.objects.create(name="Heating")
        lightingCat = DeviceCategory.objects.create(name="Lighting")
        musicCat = DeviceCategory.objects.create(name="Music")
        applianceCat = DeviceCategory.objects.create(name="Appliance")

        basement = Area.objects.create(name="Basement")
        groundFloor = Area.objects.create(name="Ground floor")
        firstFloor = Area.objects.create(name="First floor")

        bedroom1 = Room.objects.create(name="Bedroom 1", area=firstFloor)
        bedroom2 = Room.objects.create(name="Bedroom 2", area=firstFloor)
        lounge = Room.objects.create(name="Lounge", area=groundFloor)
        kitchen = Room.objects.create(name="Kitchen", area=groundFloor)
        bathroom = Room.objects.create(name="Bathroom", area=firstFloor)
        cellar = Room.objects.create(name="Cellar", area=basement)

        bedroom1BedsideLamp = Device.objects.create(
                name="Beside lamp",
                technology=x10,
                reference="AM12",
                address="A1",
                room=bedroom1,
                type="appliance",
                category=lightingCat,
                initial_value="off",
                unit_of_stored_values="",
                is_value_changeable_by_user=True,
                is_resetable=True)

        bedroom1Lamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="A2",
                room=bedroom1,
                type="lamp",
                category=lightingCat,
                initial_value="100",
                unit_of_stored_values="%",
                is_value_changeable_by_user=True,
                is_resetable=True)

        bedroom2BedsideLamp = Device.objects.create(
                name="Beside lamp",
                technology=x10,
                reference="AM12",
                address="B1",
                room=bedroom2,
                type="appliance",
                category=lightingCat,
                initial_value="off",
                unit_of_stored_values="",
                is_value_changeable_by_user=True,
                is_resetable=True)

        bedroom2Lamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="B2",
                room=bedroom2,
                type="lamp",
                category=lightingCat,
                initial_value="100",
                unit_of_stored_values="%",
                is_value_changeable_by_user=True,
                is_resetable=True)

        loungeLamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="C1",
                room=lounge,
                type="lamp",
                category=lightingCat,
                initial_value="100",
                unit_of_stored_values="%",
                is_value_changeable_by_user=True,
                is_resetable=True)

        kitchenLamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="D1",
                room=kitchen,
                type="lamp",
                category=lightingCat,
                initial_value="100",
                unit_of_stored_values="%",
                is_value_changeable_by_user=True,
                is_resetable=True)

        kitchenCoffeeMachine = Device.objects.create(
                name="Coffee machine",
                technology=x10,
                reference="AM12",
                address="D2",
                room=kitchen,
                type="appliance",
                category=applianceCat,
                initial_value="off",
                unit_of_stored_values="",
                is_value_changeable_by_user=True,
                is_resetable=True)

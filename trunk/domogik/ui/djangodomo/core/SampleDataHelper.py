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
from djangodomo.core.models import DeviceProperty
from djangodomo.core.models import DeviceCmdLog
from djangodomo.core.models import Device
from djangodomo.core.models import StateReading
from djangodomo.core.models import ApplicationSetting


class SampleDataHelper:
    """
    Class to load / clear sample data
    """

    def remove(self):
        ApplicationSetting.objects.all().delete()
        StateReading.objects.all().delete()
        DeviceCategory.objects.all().delete()
        DeviceTechnology.objects.all().delete()
        DeviceProperty.objects.all().delete()
        DeviceCmdLog.objects.all().delete()
        Device.objects.all().delete()
        Room.objects.all().delete()
        Area.objects.all().delete()

    def create(self):
        self.remove()

        ApplicationSetting.objects.create(simulationMode=True, adminMode=True,
                debugMode=True)

        # Create sample objects
        x10 = DeviceTechnology.objects.create(name="x10", type="cpl")
        plcbus = DeviceTechnology.objects.create(name="plcbus", type="cpl")
        onewire = DeviceTechnology.objects.create(name="1-wire", type="wired_bus")

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
                isResetable=True)
        DeviceProperty.objects.create(
                key="value",
                value="off",
                valueType="BOOLEAN",
                isChangeableByUser=True,
                device=bedroom1BedsideLamp)
        bedroom1Lamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="A2",
                room=bedroom1,
                type="lamp",
                category=lightingCat,
                isResetable=True)
        DeviceProperty.objects.create(
                key="value",
                value="100", # Variable value (dimmer)
                valueType="ALPHANUM",
                valueUnit="%",
                isChangeableByUser=True,
                device=bedroom1Lamp)

        bedroom2BedsideLamp = Device.objects.create(
                name="Beside lamp",
                technology=x10,
                reference="AM12",
                address="B1",
                room=bedroom2,
                type="appliance",
                category=lightingCat,
                isResetable=True)
        DeviceProperty.objects.create(
                key="value",
                value="off",
                valueType="BOOLEAN",
                valueUnit="%",
                isChangeableByUser=True,
                device=bedroom2BedsideLamp)

        bedroom2Lamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="B2",
                room=bedroom2,
                type="lamp",
                category=lightingCat,
                isResetable=True)
        DeviceProperty.objects.create(
                key="value",
                value="100", # Variable value (dimmer)
                valueType="ALPHANUM",
                valueUnit="%",
                isChangeableByUser=True,
                device=bedroom2Lamp)

        loungeLamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="C1",
                room=lounge,
                type="lamp",
                category=lightingCat,
                isResetable=True)
        DeviceProperty.objects.create(
                key="value",
                value="100", # Variable value (dimmer)
                valueType="ALPHANUM",
                valueUnit="%",
                isChangeableByUser=True,
                device=loungeLamp)

        kitchenLamp = Device.objects.create(
                name="Lamp",
                technology=x10,
                reference="LM12",
                address="D1",
                room=kitchen,
                type="lamp",
                category=lightingCat,
                isResetable=True)

        DeviceProperty.objects.create(
                key="value",
                value="100", # Variable value (dimmer)
                valueType="ALPHANUM",
                valueUnit="%",
                isChangeableByUser=True,
                device=kitchenLamp)

        kitchenCoffeeMachine = Device.objects.create(
                name="Coffee machine",
                technology=x10,
                reference="AM12",
                address="D2",
                room=kitchen,
                type="appliance",
                category=applianceCat,
                isResetable=True)

        DeviceProperty.objects.create(
                key="value",
                value="off",
                valueType="BOOLEAN",
                isChangeableByUser=True,
                device=kitchenCoffeeMachine)

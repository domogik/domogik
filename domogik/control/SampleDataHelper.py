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
# $LastChangedDate: 2008-12-21 11:02:48 +0100 (dim. 21 déc. 2008) $
# $LastChangedRevision: 285 $

from domogik.control.models import DeviceTechnology
from domogik.control.models import Area
from domogik.control.models import Room
from domogik.control.models import DeviceCapacity
from domogik.control.models import DeviceProperty
from domogik.control.models import DeviceCmdLog
from domogik.control.models import Device
from domogik.control.models import StateReading
from domogik.control.models import ApplicationSetting

class SampleDataHelper:
	"""
	Class to load / clear sample data
	"""

	def remove(self):
		ApplicationSetting.objects.all().delete()
		StateReading.objects.all().delete()
		DeviceProperty.objects.all().delete()
		DeviceCmdLog.objects.all().delete()
		Device.objects.all().delete()
		DeviceCapacity.objects.all().delete()
		DeviceTechnology.objects.all().delete()
		Room.objects.all().delete()
		Area.objects.all().delete()

	def create(self):
		self.remove()

		ApplicationSetting.objects.create(simulationMode=True, adminMode=True, debugMode=True)

		# Create sample objects
		basement = Area.objects.create(name="Basement")
		groundFloor = Area.objects.create(name="Ground floor")
		firstFloor = Area.objects.create(name="First floor")

		bedroom1 = Room.objects.create(name="Bedroom 1", area=firstFloor)
		bedroom2 = Room.objects.create(name="Bedroom 2", area=firstFloor)
		lounge = Room.objects.create(name="Lounge", area=groundFloor)
		kitchen = Room.objects.create(name="Kitchen", area=groundFloor)
		bathroom = Room.objects.create(name="Bathroom", area=firstFloor)
		cellar = Room.objects.create(name="Cellar", area=basement)

		x10 = DeviceTechnology.objects.create(name="X10")
		oneWire = DeviceTechnology.objects.create(name="OneWire")
		ir = DeviceTechnology.objects.create(name="IR")
		plcBus = DeviceTechnology.objects.create(name="PLCBus")

		lightingCap = DeviceCapacity.objects.create(name="Lighting")
		powerPointCap = DeviceCapacity.objects.create(name="Power point")

		bedroom1BedsideLamp = Device.objects.create(name="Beside lamp", technology=x10, capacity=lightingCap, reference="AM12", address="A1", room=bedroom1)
		DeviceProperty.objects.create(key="value", value="1", valueType="BOOLEAN", isChangeableByUser=True, device=bedroom1BedsideLamp) # On (static)

		bedroom1Lamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="A2", room=bedroom1)
		DeviceProperty.objects.create(key="value", value="75", valueType="ALPHANUM", valueUnit="%", isChangeableByUser=True, device=bedroom1Lamp) # Variable value (dimmer)

		bedroom2BedsideLamp = Device.objects.create(name="Beside lamp", technology=x10, capacity=lightingCap, reference="AM12", address="B1", room=bedroom2)
		DeviceProperty.objects.create(key="value", value="0", valueType="ALPHANUM", valueUnit="%", isChangeableByUser=True, device=bedroom2BedsideLamp) # Off (static)

		bedroom2Lamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="B2", room=bedroom2)
		DeviceProperty.objects.create(key="value", value="30", valueType="ALPHANUM", valueUnit="%", isChangeableByUser=True, device=bedroom2Lamp) # Variable value (dimmer)
		#bedroomMusic = Item.objects.create(name="Music in the bedroom", room=bedroom, capacity=music)

		loungeLamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="C1", room=lounge)
		DeviceProperty.objects.create(key="value", value="50", valueType="ALPHANUM", valueUnit="%", isChangeableByUser=True, device=loungeLamp) # Variable value (dimmer)
		#loungeMusic = Item.objects.create(name="Music in the lounge", room=lounge, capacity=music)

		kitchenLamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="D1", room=kitchen)
		DeviceProperty.objects.create(key="value", value="50", valueType="ALPHANUM", valueUnit="%", isChangeableByUser=True, device=kitchenLamp) # Variable value (dimmer)

		kitchenCoffeeMachine = Device.objects.create(name="Coffee machine", technology=x10, capacity=powerPointCap, reference="AM12", address="D2", room=kitchen)
		DeviceProperty.objects.create(key="value", value="1", valueType="BOOLEAN", isChangeableByUser=True, device=kitchenCoffeeMachine) # On (static)

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
# $LastChangedDate: 2008-12-03 22:33:25 +0100 (mer. 03 déc. 2008) $
# $LastChangedRevision: 214 $

from django.db.models import Q
from django.http import Http404
from django.http import QueryDict
from django.shortcuts import render_to_response

from domogik.control.models import DeviceTechnology
from domogik.control.models import Area
from domogik.control.models import Room
from domogik.control.models import DeviceCapacity
from domogik.control.models import DeviceProperty
from domogik.control.models import Device
from domogik.control.models import StateReading
from domogik.control.models import ApplicationSetting
from domogik.control.forms import ApplicationSettingForm

def index(request):
	adminMode = ""
	pageTitle = "Control overview"

	qListArea = Q()
	qListRoom = Q()
	qListCapacity = Q()
	if request.method == 'POST': # A search was submitted
		for area in QueryDict.getlist(request.POST, "area"):
			qListArea = qListArea | Q(room__area__id = area)
		for room in QueryDict.getlist(request.POST, "room"):
			qListRoom = qListRoom | Q(room__id = room)
		for capacity in QueryDict.getlist(request.POST, "capacity"):
			qListCapacity = qListCapacity | Q(capacity__id = capacity)

	# select_related() should avoid one extra db query per property
	deviceList = Device.objects.filter(qListArea).filter(qListRoom).filter(qListCapacity).select_related()

	areaList = Area.objects.all()
	roomList = Room.objects.all()
	capacityList = DeviceCapacity.objects.all()
	techList = DeviceTechnology.objects.all()

	appSetting = __readApplicationSetting()

	if appSetting.adminMode == True:
		adminMode = "True"
	return render_to_response(
		'index.html',
		{
			'areaList'		: areaList,
			'roomList'		: roomList,
			'capacityList'	: capacityList,
			'deviceList'	: deviceList,
			'techList'		: techList,
			'adminMode'		: adminMode,
			'pageTitle'		: pageTitle
		}
	)

def device(request, deviceId):
	adminMode = ""
	pageTitle = "Device details"

	appSetting = __readApplicationSetting()
	if appSetting.adminMode == True:
		adminMode = "True"

	# Read device information
	try:
		device = Device.objects.get(pk=deviceId)
	except Device.DoesNotExist:
		raise Http404

	return render_to_response(
		'device.html',
		{
			'device'		: device,
			'adminMode'		: adminMode,
			'pageTitle'		: pageTitle
		}
	)

# Views for the admin part

def adminIndex(request):
	pageTitle = "Admin page"
	action = "index"

	appSettingForm = ApplicationSettingForm(instance=__readApplicationSetting())
	return render_to_response(
		'admin_index.html',
		{
			'appSettingForm'	: appSettingForm,
			'pageTitle'			: pageTitle,
			'action'			: action
		}
	)

def saveSettings(request):
	if request.method == 'POST':
		# Update existing applicationSetting instance with POST values
		form = ApplicationSettingForm(request.POST, instance=__readApplicationSetting())
		if form.is_valid():
			form.save()

	return adminIndex(request)

def loadSampleData(request):
	pageTitle = "Load sample data"
	action = "loadSampleData"

	appSetting = __readApplicationSetting()
	if appSetting.simulationMode != True:
		errorMsg = "The application is not running in simulation mode : can't load sample data"
		return render_to_response(
			'admin_index.html',
			{
				'pageTitle'		: pageTitle,
				'action'		: action,
				'errorMsg'		: errorMsg
			}
		)

	__createSampleData()

	areaList = Area.objects.all()
	roomList = Room.objects.all()
	capacityList = DeviceCapacity.objects.all()
	deviceList = Device.objects.all()
	techList = DeviceTechnology.objects.all()

	return render_to_response(
		'admin_index.html',
		{
			'pageTitle'		: pageTitle,
			'action'		: action,
			'areaList'		: areaList,
			'roomList'		: roomList,
			'capacityList'	: capacityList,
			'deviceList'	: deviceList,
			'techList'		: techList,
		}
	)

def clearData(request):
	pageTitle = "Remove all data"
	action = "clearData"

	appSetting = __readApplicationSetting()
	if appSetting.simulationMode != True:
		errorMsg = "The application is not running in simulation mode : can't clear data"
		return render_to_response(
			'admin_index.html',
			{
				'pageTitle'		: pageTitle,
				'action'		: action,
				'errorMsg'		: errorMsg
			}
		)

	__removeAllData()

	return render_to_response(
		'admin_index.html',
		{
			'pageTitle'	: pageTitle,
			'action'	: action
		}
	)

### Private methods

def __readApplicationSetting():
	if ApplicationSetting.objects.all().count() == 1:
		return ApplicationSetting.objects.all()[0]
	else:
		return ApplicationSetting()

def __createSampleData():
	__removeAllData()

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
	plcBus = DeviceTechnology.objects.create(name="IR")

	lightingCap = DeviceCapacity.objects.create(name="Lighting")
	powerPointCap = DeviceCapacity.objects.create(name="Power point")

	bedroom1BedsideLamp = Device.objects.create(name="Beside lamp", technology=x10, capacity=lightingCap, reference="AM12", address="A1", room=bedroom1)
	DeviceProperty.objects.create(key="value", value="1", device=bedroom1BedsideLamp) # On (static)

	bedroom1Lamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="A2", room=bedroom1)
	DeviceProperty.objects.create(key="value", value="75", device=bedroom1Lamp) # Variable value (dimmer)

	bedroom2BedsideLamp = Device.objects.create(name="Beside lamp", technology=x10, capacity=lightingCap, reference="AM12", address="B1", room=bedroom2)
	DeviceProperty.objects.create(key="value", value="0", device=bedroom2BedsideLamp) # Off (static)

	bedroom2Lamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="B2", room=bedroom2)
	DeviceProperty.objects.create(key="value", value="30", device=bedroom2Lamp) # Variable value (dimmer)
	#bedroomMusic = Item.objects.create(name="Music in the bedroom", room=bedroom, capacity=music)

	loungeLamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="C1", room=lounge)
	DeviceProperty.objects.create(key="value", value="50", device=loungeLamp) # Variable value (dimmer)
	#loungeMusic = Item.objects.create(name="Music in the lounge", room=lounge, capacity=music)

	kitchenLamp = Device.objects.create(name="Lamp", technology=x10, capacity=lightingCap, reference="LM12", address="D1", room=kitchen)
	DeviceProperty.objects.create(key="value", value="50", device=kitchenLamp) # Variable value (dimmer)

	kitchenCoffeeMachine = Device.objects.create(name="Coffee machine", technology=x10, capacity=powerPointCap, reference="AM12", address="D2", room=kitchen)
	DeviceProperty.objects.create(key="value", value="1", device=kitchenCoffeeMachine) # On (static)

def __removeAllData():
	# Normally the list should contain only one row
	appSettingList = ApplicationSetting.objects.all()
	for appSetting in appSettingList:
		appSetting.delete()

	stateReadingList = StateReading.objects.all()
	for stateReading in stateReadingList:
		stateReading.delete()

	devicePropertyList = DeviceProperty.objects.all()
	for deviceProperty in devicePropertyList:
		deviceProperty.delete()

	deviceList = Device.objects.all()
	for device in deviceList:
		device.delete()

	deviceCapacityList = DeviceCapacity.objects.all()
	for deviceCapacity in deviceCapacityList:
		deviceCapacity.delete()

	deviceTechnologyList = DeviceTechnology.objects.all()
	for deviceTechnology in deviceTechnologyList:
		deviceTechnology.delete()

	roomList = Room.objects.all()
	for room in roomList:
		room.delete()

	areaList = Area.objects.all()
	for area in areaList:
		area.delete()


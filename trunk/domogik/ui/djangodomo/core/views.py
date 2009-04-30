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
# $LastChangedDate: 2009-02-22 11:46:25 +0100 (dim. 22 févr. 2009) $
# $LastChangedRevision: 392 $

import datetime
import math
import os
from subprocess import *

from django.db.models import Q
from django.http import Http404
from django.http import QueryDict
from django.shortcuts import render_to_response

from djangodomo.core.models import Area
from djangodomo.core.models import Room
from djangodomo.core.models import DeviceCategory
from djangodomo.core.models import DeviceTechnology
from djangodomo.core.models import DeviceStats
from djangodomo.core.models import Device
from djangodomo.core.models import ApplicationSetting
from djangodomo.core.forms import ApplicationSettingForm

from djangodomo.core.SampleDataHelper import SampleDataHelper
from djangodomo.core.XPLHelper import XPLHelper


def index(request):
    """
    Main page
    """
    adminMode = ""
    pageTitle = "Control overview"

    appSetting = __read_application_setting()

    qListArea = Q()
    qListRoom = Q()
    qListDeviceCategory = Q()
    if request.method == 'POST': # An action was submitted
        cmd = QueryDict.get(request.POST, "cmd", "")
        if cmd == "filter":
            for area in QueryDict.getlist(request.POST, "area"):
                qListArea = qListArea | Q(room__area__id = area)
            for room in QueryDict.getlist(request.POST, "room"):
                qListRoom = qListRoom | Q(room__id = room)
            for deviceCategory in QueryDict.getlist(request.POST,
                    "deviceCategory"):
                qListDeviceCategory = qListDeviceCategory | Q(category__id=
                    deviceCategory)
        elif cmd == "updateValues":
            __update_device_values(request, appSetting)

    # select_related() should avoid one extra db query per property
    deviceList = Device.objects.filter(qListArea).filter(qListRoom).filter(
            qListDeviceCategory).select_related()

    areaList = Area.objects.all()
    roomList = Room.objects.all()
    deviceCategoryList = DeviceCategory.objects.all()
    techList = DeviceTechnology.objects.all()

    if appSetting.adminMode == True:
        adminMode = "True"

    return render_to_response('index.html', {
        'areaList': areaList,
        'roomList': roomList,
        'deviceCategoryList': deviceCategoryList,
        'deviceList': deviceList,
        'techList': techList,
        'adminMode': adminMode,
        'pageTitle': pageTitle,
    })


def __update_device_values(request, appSetting):
    """
    Update device values (main control page)
    """
    for deviceId in QueryDict.getlist(request.POST, "deviceId"):
        valueList = QueryDict.getlist(request.POST, "value" + deviceId)
        for i in range(len(valueList)):
            if valueList[i]:
              __send_value_to_device(deviceId, valueList[i], appSetting)

    # Get all values posted over the form
    # For each device :
    #       Check if value was changed
    #       If yes, try to send new value to the device
    #       Log the result


def __send_value_to_device(deviceId, newValue, appSetting):
    """
    Send a value to a device
    """
    error = ""
    # Read previous value, and update it if necessary
    device = Device.objects.get(pk=deviceId)
    oldValue = device.get_last_value()
    if oldValue != newValue:
        if device.technology.name.lower() == 'x10':
            error = __send_x10_cmd(device, oldValue, newValue,
                    appSetting.simulationMode)

        if error == "":
            if device.is_lamp():
                if newValue == "on":
                    newValue = "100"
                elif newValue == "off":
                    newValue = "0"

            __write_device_stats(deviceId, newValue,
                    "Nothing special", True)


def __send_x10_cmd(device, oldValue, newValue, simulationMode):
    """
    Send x10 cmd
    """
    output = ""
    xPLSchema = "x10.basic"
    xPLParam = ""
    if device.is_appliance():
        xPLParam = "device="+device.address+","+"command="+newValue
    elif device.is_lamp():
        if newValue == "on" or newValue == "off":
            xPLParam = "device="+device.address+","+"command="+newValue
        else:
            # TODO check if type is int and 0 <= value <= 100
            if int(newValue)-int(oldValue) > 0:
                cmd = "bright"
            else:
                cmd = "dim"
            level = abs(int(newValue)-int(oldValue))
            xPLParam = "command=" + cmd + "," + "device=" + device.address + \
                    "," + "level=" + str(level)

    print "**** xPLParam = %s" %xPLParam
    if not simulationMode:
        output = XPLHelper().send(xPLSchema, xPLParam)
    return output


def __write_device_stats(deviceId, newValue, newComment, newIsSuccessful):
    """
    Write device stats
    """
    new_device = Device.objects.get(id=deviceId)
    device_stats = DeviceStats(
        date = datetime.datetime.now(),
        device = new_device,
        value = newValue,
        unit = new_device.unit_of_stored_values,
    )
    device_stats.save()


def device(request, deviceId):
    """
    Details of a device
    """
    hasStats = ""
    adminMode = ""
    pageTitle = "Device details"

    appSetting = __read_application_setting()
    if appSetting.adminMode == True:
        adminMode = "True"

    if request.method == 'POST': # An action was submitted
        # TODO check the value of the button (reset or update value)
        __update_device_values(request, appSetting)

    # Read device information
    try:
        device = Device.objects.get(pk=deviceId)
    except Device.DoesNotExist:
        raise Http404

    if DeviceStats.objects.filter(device__id=device.id).count() > 0:
        hasStats = "True"

    return render_to_response('device.html', {
        'device': device,
        'hasStats': hasStats,
        'adminMode': adminMode,
        'pageTitle': pageTitle,
    })


def device_stats(request, deviceId):
    """
    View for stats of a device or all devices
    """
    deviceAll = ""
    pageTitle = "Device stats"
    adminMode = ""

    appSetting = __read_application_setting()
    if appSetting.adminMode == True:
        adminMode = "True"

    cmd = QueryDict.get(request.POST, "cmd", "")
    if cmd == "clearStats" and appSetting.adminMode:
        __clear_device_stats(request, deviceId, appSetting.adminMode)

    # Read device stats
    if deviceId == "0": # For all devices
        deviceAll = "True"
        deviceStatsList = DeviceStats.objects.all()
    else:
        try:
            deviceStatsList = DeviceStats.objects.filter(device__id=deviceId)
        except DeviceStats.DoesNotExist:
            raise Http404

    return render_to_response('device_stats.html', {
        'deviceId': deviceId,
        'adminMode': adminMode,
        'deviceStatsList': deviceStatsList,
        'deviceAll': deviceAll,
        'pageTitle': pageTitle,
    })


def __clear_device_stats(request, deviceId, isAdminMode):
    """
    Clear stats of a device or all devices
    """
    if deviceId == "0": # For all devices
        DeviceStats.objects.all().delete()
    else:
        try:
            DeviceStats.objects.filter(device__id=deviceId).delete()
        except DeviceStats.DoesNotExist:
            raise Http404


# Views for the admin part


def admin_index(request):
    """
    Main page of the admin part
    """
    pageTitle = "Admin page"
    action = "index"

    appSettingForm = ApplicationSettingForm(
            instance=__read_application_setting())
    return render_to_response('admin_index.html', {
        'appSettingForm': appSettingForm,
        'pageTitle': pageTitle,
        'action': action,
    })


def save_settings(request):
    if request.method == 'POST':
        # Update existing applicationSetting instance with POST values
        form = ApplicationSettingForm(request.POST,
                instance=__read_application_setting())
        if form.is_valid():
            form.save()

    return adminIndex(request)


def load_sample_data(request):
    pageTitle = "Load sample data"
    action = "loadSampleData"

    appSetting = __read_application_setting()
    if appSetting.simulationMode != True:
        errorMsg = "The application is not running in simulation mode : "\
                "can't load sample data"
        return render_to_response('admin_index.html', {
            'pageTitle': pageTitle,
            'action': action,
            'errorMsg': errorMsg,
        })

    sampleDataHelper = SampleDataHelper()
    sampleDataHelper.create()

    areaList = Area.objects.all()
    roomList = Room.objects.all()
    deviceCategoryList = DeviceCategory.objects.all()
    deviceList = Device.objects.all()
    techList = DeviceTechnology.objects.all()

    return render_to_response('admin_index.html', {
        'pageTitle': pageTitle,
        'action': action,
        'areaList': areaList,
        'roomList': roomList,
        'deviceCategoryList': deviceCategoryList,
        'deviceList': deviceList,
        'techList': techList,
    })


def clear_data(request):
    pageTitle = "Remove all data"
    action = "clearData"

    appSetting = __read_application_setting()
    if appSetting.simulationMode != True:
        errorMsg = "The application is not running in simulation mode : "\
                "can't clear data"
        return render_to_response('admin_index.html', {
            'pageTitle': pageTitle,
            'action': action,
            'errorMsg': errorMsg,
        })

    sampleDataHelper = SampleDataHelper()
    sampleDataHelper.remove()

    return render_to_response('admin_index.html', {
        'pageTitle': pageTitle,
        'action': action,
    })

def __read_application_setting():
    if ApplicationSetting.objects.all().count() == 1:
        return ApplicationSetting.objects.all()[0]
    else:
        return ApplicationSetting()

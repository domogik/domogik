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
import simplejson

from django.db.models import Q
from django.http import Http404, HttpResponse
from django.http import QueryDict
from django.shortcuts import render_to_response
from django.core import serializers

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
    admin_mode = ""
    page_title = "Control overview"

    app_setting = __read_application_setting()

    qlist_area = Q()
    qlist_room = Q()
    qlist_device_category = Q()
    if request.method == 'POST': # An action was submitted
        cmd = QueryDict.get(request.POST, "cmd", "")
        if cmd == "filter":
            for area in QueryDict.getlist(request.POST, "area"):
                qlist_area = qlist_area | Q(room__area__id = area)
            for room in QueryDict.getlist(request.POST, "room"):
                qlist_room = qlist_room | Q(room__id = room)
            for device_category in QueryDict.getlist(request.POST,
                    "deviceCategory"):
                qlist_device_category = qlist_device_category | Q(category__id=
                    device_category)
        elif cmd == "updateValues":
            __update_device_values(request, app_setting)

    # select_related() should avoid one extra db query per property
    device_list = Device.objects.filter(qlist_area).filter(qlist_room).filter(
            qlist_device_category).select_related()

    area_list = Area.objects.all()
    room_list = Room.objects.all()
    device_category_list = DeviceCategory.objects.all()
    tech_list = DeviceTechnology.objects.all()

    if app_setting.admin_mode == True:
        admin_mode = "True"

    return render_to_response('index.html', {
        'areaList': area_list,
        'roomList': room_list,
        'deviceCategoryList': device_category_list,
        'deviceList': device_list,
        'techList': tech_list,
        'adminMode': admin_mode,
        'pageTitle': page_title,
    })


def __update_device_values(request, app_setting):
    """
    Update device values (main control page)
    """
    for device_id in QueryDict.getlist(request.POST, "deviceId"):
        value_list = QueryDict.getlist(request.POST, "value" + device_id)
        for i in range(len(value_list)):
            if value_list[i]:
                __send_value_to_device(device_id, value_list[i], app_setting)


def __send_value_to_device(device_id, new_value, app_setting):
    """
    Get all values posted over the form
    For each device :
      Check if value was changed
      If yes, try to send new value to the device
      Log the result
    """
    error = ""
    # Read previous value, and update it if necessary
    device = Device.objects.get(pk=device_id)
    old_value = device.get_last_value()
    if old_value != new_value:
        if device.technology.name.lower() == 'x10':
            error = __send_x10_cmd(device, old_value, new_value,
                    app_setting.simulation_mode)

        if error == "":
            if device.is_lamp():
                if new_value == "on":
                    new_value = "100"
                elif new_value == "off":
                    new_value = "0"

            __write_device_stats(device_id, new_value,
                    "Nothing special", True)


def __send_x10_cmd(device, old_value, new_value, simulation_mode):
    """
    Send x10 cmd
    """
    output = ""
    xPL_schema = "x10.basic"
    xPL_param = ""
    if device.is_appliance():
        xPL_param = "device="+device.address+","+"command="+new_value
    elif device.is_lamp():
        if new_value == "on" or new_value == "off":
            xPL_param = "device="+device.address+","+"command="+new_value
        else:
            # TODO check if type is int and 0 <= value <= 100
            if int(new_value)-int(old_value) > 0:
                cmd = "bright"
            else:
                cmd = "dim"
            level = abs(int(new_value)-int(old_value))
            xPL_param = "command=" + cmd + "," + "device=" + device.address + \
                    "," + "level=" + str(level)

    print "**** xPLParam = %s" %xPL_param
    if not simulation_mode:
        output = XPLHelper().send(xPL_schema, xPL_param)
    return output


def __write_device_stats(device_id, new_value, new_comment, new_is_successful):
    """
    Write device stats
    """
    new_device = Device.objects.get(id=device_id)
    device_stats = DeviceStats(
        date = datetime.datetime.now(),
        device = new_device,
        value = new_value,
        unit = new_device.unit_of_stored_values,
    )
    device_stats.save()


def device(request, device_id):
    """
    Details of a device
    """
    has_stats = ""
    admin_mode = ""
    page_title = "Device details"

    app_setting = __read_application_setting()
    if app_setting.admin_mode == True:
        admin_mode = "True"

    if request.method == 'POST': # An action was submitted
        # TODO check the value of the button (reset or update value)
        __update_device_values(request, app_setting)

    # Read device information
    try:
        device = Device.objects.get(pk=device_id)
    except Device.DoesNotExist:
        raise Http404

    if DeviceStats.objects.filter(device__id=device.id).count() > 0:
        has_stats = "True"

    return render_to_response('device.html', {
        'device': device,
        'hasStats': has_stats,
        'adminMode': admin_mode,
        'pageTitle': page_title,
    })


def device_stats(request, device_id):
    """
    View for stats of a device or all devices
    """
    device_all = ""
    page_title = "Device stats"
    admin_mode = ""

    app_setting = __read_application_setting()
    if app_setting.admin_mode == True:
        admin_mode = "True"

    cmd = QueryDict.get(request.POST, "cmd", "")
    if cmd == "clearStats" and app_setting.admin_mode:
        __clear_device_stats(request, device_id, app_setting.admin_mode)

    # Read device stats
    if device_id == "0": # For all devices
        device_all = "True"
        device_stats_list = DeviceStats.objects.all()
    else:
        try:
            device_stats_list = DeviceStats.objects.filter(device__id=device_id)
        except DeviceStats.DoesNotExist:
            raise Http404

    return render_to_response('device_stats.html', {
        'deviceId': device_id,
        'adminMode': admin_mode,
        'deviceStatsList': device_stats_list,
        'deviceAll': device_all,
        'pageTitle': page_title,
    })


def __clear_device_stats(request, device_id, is_admin_mode):
    """
    Clear stats of a device or all devices
    """
    if device_id == "0": # For all devices
        DeviceStats.objects.all().delete()
    else:
        try:
            DeviceStats.objects.filter(device__id=device_id).delete()
        except DeviceStats.DoesNotExist:
            raise Http404


def admin_index(request):
    """
    Views for the admin part
    Main page of the admin part
    """
    page_title = "Admin page"
    action = "index"

    app_setting_form = ApplicationSettingForm(
            instance=__read_application_setting())
    return render_to_response('admin_index.html', {
        'appSettingForm': app_setting_form,
        'pageTitle': page_title,
        'action': action,
    })


def save_settings(request):
    if request.method == 'POST':
        # Update existing applicationSetting instance with POST values
        form = ApplicationSettingForm(request.POST,
                instance=__read_application_setting())
        if form.is_valid():
            form.save()

    return admin_index(request)


def load_sample_data(request):
    page_title = "Load sample data"
    action = "loadSampleData"

    app_setting = __read_application_setting()
    if app_setting.simulation_mode != True:
        error_msg = "The application is not running in simulation mode : "\
                "can't load sample data"
        return render_to_response('admin_index.html', {
            'pageTitle': page_title,
            'action': action,
            'errorMsg': error_msg,
        })

    sample_data_helper = SampleDataHelper()
    sample_data_helper.create()

    area_list = Area.objects.all()
    room_list = Room.objects.all()
    device_category_list = DeviceCategory.objects.all()
    device_list = Device.objects.all()
    tech_list = DeviceTechnology.objects.all()

    return render_to_response('admin_index.html', {
        'pageTitle': page_title,
        'action': action,
        'areaList': area_list,
        'roomList': room_list,
        'deviceCategoryList': device_category_list,
        'deviceList': device_list,
        'techList': tech_list,
    })


def clear_data(request):
    page_title = "Remove all data"
    action = "clearData"

    app_setting = __read_application_setting()
    if app_setting.simulation_mode != True:
        error_msg = "The application is not running in simulation mode : "\
                "can't clear data"
        return render_to_response('admin_index.html', {
            'pageTitle': page_title,
            'action': action,
            'errorMsg': error_msg,
        })

    sample_data_helper = SampleDataHelper()
    sample_data_helper.remove()

    return render_to_response('admin_index.html', {
        'pageTitle': page_title,
        'action': action,
    })


def __read_application_setting():
    if ApplicationSetting.objects.all().count() == 1:
        return ApplicationSetting.objects.all()[0]
    else:
        return ApplicationSetting()


def device_status(request, room_id=None, device_id=None):
    import random
    if request.method == 'POST':
        print "Set power to ", request.POST["value"]
        response = {'value': request.POST['value']}
    else:
        devices = Device.objects.filter(pk__in=request.GET.getlist('devices')) 
        json = simplejson.dumps(dict((d.pk, d.get_data_dict()) for d in devices))
        return HttpResponse(json)
    return HttpResponse(response)
            
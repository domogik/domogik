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

Django web UI views

Implements
==========


@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

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

from domogik.common import database

from djangodomo.core.SampleDataHelper import SampleDataHelper
from djangodomo.core.XPLHelper import XPLHelper


_db = database.DbHelper()


def index(request):
    """
    Method called when the main page is accessed
    @param request : the HTTP request
    """
    admin_mode = ""
    page_title = "Control overview"
    sys_config = _db.get_system_config()

    device_list = _db.list_devices()
    if request.method == 'POST': # An action was submitted
        cmd = QueryDict.get(request.POST, "cmd", "")
        if cmd == "filter":
            # Get all possible rooms
            possible_room_id_list = []
            for area_id in QueryDict.getlist(request.POST, "area_id"):
                room_list = _db.get_all_rooms_of_area(area_id)
                for room in room_list:
                    if room.id not in possible_room_id_list:
                        possible_room_id_list.append(room.id)
            room_id_list = []
            for room_id in QueryDict.getlist(request.POST, "room_id"):
                if room_id in possible_room_id_list or len(possible_room_id_list) == 0:
                    room_id_list.append(room_id)

            if len(room_id_list) == 0:
                room_id_list = possible_room_id_list
            device_category_id_list = QueryDict.getlist(request.POST, "device_category_id")
            print "*** device_category_id_list %s" % device_category_id_list
            print "*** room_id_list = %s" % room_id_list
            device_list = _db.find_devices(room_id_list, device_category_id_list)
        elif cmd == "update_values":
            _update_device_values(request, sys_config)

    area_list = _db.list_areas()
    room_list = _db.list_rooms()
    device_category_list = _db.list_device_categories()
    tech_list = _db.list_device_technologies()

    if sys_config.admin_mode == True:
        admin_mode = "True"

    return render_to_response('index.html', {
        'area_list': area_list,
        'room_list': room_list,
        'device_category_list': device_category_list,
        'device_list': device_list,
        'tech_list': tech_list,
        'admin_mode': admin_mode,
        'page_title': page_title,
    })

def _update_device_values(request, sys_config):
    """
    Update device values (main control page)
    @param request : the HTTP request
    @param sys_config : a SystemConfig object (parameters for system configuration)
    """
    for device_id in QueryDict.getlist(request.POST, "device_id"):
        value_list = QueryDict.getlist(request.POST, "value" + device_id)
        for i in range(len(value_list)):
            if value_list[i]:
                _send_value_to_device(device_id, value_list[i], sys_config)

def _send_value_to_device(device_id, new_value, sys_config):
    """
    Get all values posted over the form
    For each device :
      Check if value was changed
      If yes, try to send new value to the device
      Log the result
    @param device_id : device id
    @param new_value : value sent to the device
    @param sys_config : a SystemConfig object (parameters for system configuration)
    """
    error = ""
    # Read previous value, and update it if necessary
    device = _db.get_device(device_id)
    old_value = device.get_last_value()
    if old_value != new_value:
        if device.technology.name.lower() == 'x10':
            error = _send_x10_cmd(device, old_value, new_value, sys_config.simulation_mode)

        if error == "":
            if device.is_lamp():
                if new_value == "on":
                    new_value = "100"
                elif new_value == "off":
                    new_value = "0"

            _write_device_stats(device_id, new_value,)

def _send_x10_cmd(device, old_value, new_value, simulation_mode):
    """
    Send a x10 command
    @param device : a Device object
    @param old_value : previous value associated to the device
    @param new_value : new value sent to the device
    @param simulation_mode : True if we are in simulation mode
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

def _write_device_stats(device_id, new_value):
    """
    Write device stats
    @param device_id : device id
    @param new_value : new value associated to the device
    """
    _db.add_device_stat(d_id=device_id, ds_date=datetime.datetime.now(), ds_value=new_value)

def device(request, device_id):
    """
    Method called when the page showing the details of a device is called
    @param request : HTTP request
    @param device_id : device id
    """
    has_stats = ""
    admin_mode = ""
    page_title = "Device details"

    sys_config = _db.get_system_config()
    if sys_config.admin_mode == True:
        admin_mode = "True"

    if request.method == 'POST': # An action was submitted
        # TODO check the value of the button (reset or update value)
        _update_device_values(request, sys_config)

    # Read device information
    device = _db.get_device(device_id)

    if _db.device_has_stats(device_id):
        has_stats = "True"

    return render_to_response('device.html', {
        'device': device,
        'has_stats': has_stats,
        'admin_mode': admin_mode,
        'page_title': page_title,
    })

def device_stats(request, device_id):
    """
    Method called when the page of stats of a device or all devices is accessed
    @param request : HTTP request
    @param device_id : device id
    """
    device_all = ""
    page_title = "Device stats"
    admin_mode = ""

    sys_config = _db.get_system_config()
    if sys_config.admin_mode == True:
        admin_mode = "True"

    cmd = QueryDict.get(request.POST, "cmd", "")
    if cmd == "clear_stats" and sys_config.admin_mode:
        _clear_device_stats(request, device_id, sys_config.admin_mode)

    # Read device stats
    if device_id == "0": # For all devices
        device_all = "True"
        device_stats_list = []
        for device in _db.list_devices():
            for device_stat in _db.list_device_stats(device.id):
              device_stats_list.append(device_stat)
    else:
        device_stats_list = _db.list_device_stats(device_id)

    return render_to_response('device_stats.html', {
        'device_id': device_id,
        'admin_mode': admin_mode,
        'device_stats_list': device_stats_list,
        'device_all': device_all,
        'page_title': page_title,
    })

def _clear_device_stats(request, device_id, is_admin_mode):
    """
    Clear stats of a device or all devices
    @param request : HTTP request
    @param device_id : device id
    @param is_admin_mode : True if we are in administrator mode
    """
    if device_id == "0": # For all devices
        for device in _db.list_devices():
            _db.del_all_device_stats(device.id)
    else:
        _db.del_all_device_stats(device_id)

def admin_index(request):
    """
    Method called when the admin page is accessed
    @param request : HTTP request
    """
    simulation_mode = ""
    admin_mode = ""
    debug_mode = ""
    page_title = "Admin page"
    action = "index"
    system_config = _db.get_system_config()
    if system_config.simulation_mode:
        simulation_mode = "checked"
    if system_config.admin_mode:
        admin_mode = "checked"
    if system_config.debug_mode:
        debug_mode = "checked"

    return render_to_response('admin_index.html', {
        'system_config': system_config,
        'page_title': page_title,
        'action': action,
        'simulation_mode': simulation_mode,
        'admin_mode': admin_mode,
        'debug_mode': debug_mode,
    })

def save_settings(request):
    """
    Save the administrator settings (admin, debug and simulation mode
    @param request : HTTP request
    """
    if request.method == 'POST':
        simulation_mode = QueryDict.get(request.POST, "simulation_mode", False)
        admin_mode = QueryDict.get(request.POST, "admin_mode", False)
        debug_mode = QueryDict.get(request.POST, "debug_mode", False)
        _db.update_system_config(s_simulation_mode=simulation_mode, s_admin_mode=admin_mode, s_debug_mode=debug_mode)
    return admin_index(request)

def load_sample_data(request):
    """
    Load sample data
    @param request : HTTP request
    """
    page_title = "Load sample data"
    action = "loadSampleData"

    sys_config = _db.get_system_config()
    if sys_config.simulation_mode != True:
        error_msg = "The application is not running in simulation mode : "\
                "can't load sample data"
        return render_to_response('admin_index.html', {
            'page_title': page_title,
            'action': action,
            'error_msg': error_msg,
        })

    sample_data_helper = SampleDataHelper(_db)
    sample_data_helper.create()

    area_list = _db.list_areas()
    room_list = _db.list_rooms()
    device_category_list = _db.list_device_categories()
    device_list = _db.list_devices()
    device_tech_list = _db.list_device_technologies()

    return render_to_response('admin_index.html', {
        'page_title': page_title,
        'action': action,
        'area_list': area_list,
        'room_list': room_list,
        'device_category_list': device_category_list,
        'device_list': device_list,
        'device_tech_list': device_tech_list,
    })

def clear_data(request):
    """
    Clear all data of the system (in the database). Please use with care!
    @param request : HTTP request
    """
    page_title = "Remove all data"
    action = "clearData"

    sys_config = _db.get_system_config()
    if sys_config.simulation_mode != True:
        error_msg = "The application is not running in simulation mode : "\
                "can't clear data"
        return render_to_response('admin_index.html', {
            'page_title': page_title,
            'action': action,
            'error_msg': error_msg,
        })

    sample_data_helper = SampleDataHelper(_db)
    sample_data_helper.remove()

    return render_to_response('admin_index.html', {
        'page_title': page_title,
        'action': action,
    })

def device_status(request, room_id=None, device_id=None):
    return None
    """
    import random
    if request.method == 'POST':
        print "Set power to ", request.POST["value"]
        response = {'value': request.POST['value']}
    else:
        devices = Device.objects.filter(pk__in=request.GET.getlist('devices')) 
        json = simplejson.dumps(dict((d.pk, d.get_data_dict()) for d in devices))
        return HttpResponse(json)
    return HttpResponse(response)
    """

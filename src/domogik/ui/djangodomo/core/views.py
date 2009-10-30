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
import simplejson
from subprocess import *

from django.core import serializers
from django.db.models import Q
from django.http import QueryDict
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from domogik.common import database

from djangodomo.core.SampleDataHelper import SampleDataHelper
from djangodomo.core.XPLHelper import XPLHelper

_ADMIN_MANAGEMENT_DOMOGIK = 'admin/management/domogik.html'
_db = database.DbHelper()

def index(request):
    """
    Method called when the main page is accessed
    @param request : the HTTP request
    @return an HttpResponse object
    """
    page_title = _("Control overview")
    sys_config = _db.get_system_config()

    #device_list = _db.list_devices()
    """
    if request.method == 'POST': 
        # An action was submitted
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
            device_list = _db.find_devices(room_id_list, device_category_id_list)
        elif cmd == "update_values":
            _update_device_values(request, sys_config)
    """
    #area_list = _db.list_areas()
    room_list = _db.list_rooms()
    device_list = []
    for device in _db.list_devices():
      device_list.append({'room': device.room_id, 'device': device})

    return _go_to_page(request, 'index.html', page_title, room_list=room_list, device_list=device_list)

def device(request, device_id):
    """
    Method called when the page showing the details of a device is called
    @param request : HTTP request
    @param device_id : device id
    @return an HttpResponse object
    """
    has_stats = ""
    page_title = _("Device details")
    sys_config = _db.get_system_config()

    if request.method == 'POST': 
        # An action was submitted
        # TODO check the value of the button (reset or update value)
        _update_device_values(request, sys_config)

    # Read device information
    device = _db.get_device(device_id)
    if _db.device_has_stats(device_id):
        has_stats = "True"

    return _go_to_page(request, 'device.html', page_title, device=device, has_stats=has_stats)

def device_stats(request, device_id):
    """
    Method called when the page of stats of a device or all devices is accessed
    @param request : HTTP request
    @param device_id : device id
    @return an HttpResponse object
    """
    if not _is_user_connected(request):
        return index(request)

    device_all = ""
    page_title = _("Device stats")
    sys_config = _db.get_system_config()

    cmd = QueryDict.get(request.POST, "cmd", "")
    if cmd == "clear_stats" and _is_user_admin(request):
        _clear_device_stats(request, device_id)

    # Read device stats
    if device_id == "0": 
        # For all devices
        device_all = "True"
        device_stats_list = []
        for device in _db.list_devices():
            for device_stat in _db.list_device_stats(device.id):
              device_stats_list.append(device_stat)
    else:
        device_stats_list = _db.list_device_stats(device_id)
    return _go_to_page(request, 'device_stats.html', page_title, device_id=device_id, 
                      device_stats_list=device_stats_list, device_all=device_all)

def login(request):
    """
    Login process
    @param request : HTTP request
    @return an HttpResponse object
    """
    page_title = _("Login page")
    error_msg = ""
    if request.method == 'POST':
        # An action was submitted => login action
        login = QueryDict.get(request.POST, "login", False)
        password = QueryDict.get(request.POST, "password", False)
        sys_account = _db.get_system_account_by_login_and_pass(login, password)
        if sys_account is not None:
            user_account = _db.get_user_account_by_system_account(sys_account.id)
            if user_account is not None:
                first_name = user_account.first_name
                last_name = user_account.last_name
            else:
                first_name = login
                last_name = login
            request.session['s_user'] = {
                'login': sys_account.login, 
                'is_admin': sys_account.is_admin, 
                'first_name': first_name, 
                'last_name': last_name,
                'skin_used': sys_account.skin_used,
            }
            return index(request)
        else:
            # User not found, ask again to log in
            account_list = _db.list_system_accounts()
            error_msg = _("Sorry unable to log in. Please check login name / password and try again.")
            return _go_to_page(request, 'login.html', page_title, account_list=account_list, error_msg=error_msg)
    else:
        # User asked to log in
        account_list = _db.list_system_accounts()
        return _go_to_page(request, 'login.html', page_title, account_list=account_list)

def logout(request):
    """
    Logout process
    @param request: HTTP request
    @return an HttpResponse object
    """
    request.session.clear()
    return index(request)

def admin_index(request):
    """
    Method called when the admin page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)
    page_title = _("Admin page")
    return _go_to_page(request, 'admin/index.html', page_title)

def admin_management_domogik(request):
    """
    Method called when the admin domogik management page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)
    simulation_mode = ""
    admin_mode = ""
    debug_mode = ""
    page_title = _("Gestion de Domogik")
    action = "index"
    sys_config = _db.get_system_config()
    if sys_config.simulation_mode:
        simulation_mode = "checked"
    if _is_user_admin(request):
        admin_mode = "checked"
    if sys_config.debug_mode:
        debug_mode = "checked"
    return _go_to_page(request, _ADMIN_MANAGEMENT_DOMOGIK, page_title, action=action, 
                      simulation_mode=simulation_mode, admin_mode=admin_mode, 
                      debug_mode=debug_mode)

def admin_management_modules(request):
    """
    Method called when the admin modules management page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)
    page_title = _("Gestion des modules")
    return _go_to_page(request, 'admin/management/modules.html', page_title)
    
def save_admin_settings(request):
    """
    Save the administrator settings (admin, debug and simulation mode
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)

    if request.method == 'POST':
        simulation_mode = QueryDict.get(request.POST, "simulation_mode", False)
        admin_mode = QueryDict.get(request.POST, "admin_mode", False)
        debug_mode = QueryDict.get(request.POST, "debug_mode", False)
        _db.update_system_config(s_simulation_mode=simulation_mode, s_debug_mode=debug_mode)
    return admin_management_domogik(request)

def load_sample_data(request):
    """
    Load sample data
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)

    page_title = _("Load sample data")
    action = "loadSampleData"

    sys_config = _db.get_system_config()
    if sys_config.simulation_mode != True:
        error_msg = _("The application is not running in simulation mode : can't load sample data")
        return _go_to_page(request, _ADMIN_MANAGEMENT_DOMOGIK, page_title, action=action, error_msg=error_msg)

    sample_data_helper = SampleDataHelper(_db)
    sample_data_helper.create()

    area_list = _db.list_areas()
    room_list = _db.list_rooms()
    device_category_list = _db.list_device_categories()
    device_list = _db.list_devices()
    device_tech_list = _db.list_device_technologies()
    return _go_to_page(request, _ADMIN_MANAGEMENT_DOMOGIK, page_title, action=action, 
                      area_list=area_list, room_list=room_list, 
                      device_category_list=device_category_list, 
                      device_list=device_list, device_tech_list=device_tech_list)

def clear_data(request):
    """
    Clear all data of the system (in the database). Please use with care!
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)

    page_title = _("Remove all data")
    action = "clearData"

    sys_config = _db.get_system_config()
    if sys_config.simulation_mode != True:
        error_msg = _("The application is not running in simulation mode : can't clear data")
        return _go_to_page(request, _ADMIN_MANAGEMENT_DOMOGIK, page_title, action=action, error_msg=error_msg)

    sample_data_helper = SampleDataHelper(_db)
    sample_data_helper.remove()
    return _go_to_page(request, _ADMIN_MANAGEMENT_DOMOGIK, page_title, action=action)

def _update_device_values(request, sys_config):
    """
    Update device values
    @param request : the HTTP request
    @param sys_config : a SystemConfig object (parameters for system configuration)
    """
    if not _is_user_connected(request):
        return

    for device_id in QueryDict.getlist(request.POST, "device_id"):
        name = QueryDict.get(request.POST, "device_name", None)
        description = QueryDict.get(request.POST, "device_description", None)
        _db.update_device(d_id=device_id, d_name=name, d_description=description)
        value_list = QueryDict.getlist(request.POST, "value%s" % device_id)
        for i in range(len(value_list)):
            if value_list[i]:
                _send_value_to_device(request, device_id, value_list[i], sys_config)

def _send_value_to_device(request, device_id, new_value, sys_config):
    """
    Get all values posted over the form
    For each device :
      Check if value was changed
      If yes, try to send new value to the device
      Log the result
    @param request : HTTP request
    @param device_id : device id
    @param new_value : value sent to the device
    @param sys_config : a SystemConfig object (parameters for system configuration)
    """
    if not _is_user_connected(request):
        return

    error = ""
    # Read previous value, and update it if necessary
    device = _db.get_device(device_id)
    old_value = device.get_last_value()
    if old_value != new_value:
        if device.technology.name.lower() == 'x10':
            error = _send_x10_cmd(request, device, old_value, new_value, sys_config.simulation_mode)

        if error == "":
            if device.is_lamp():
                if new_value == "on":
                    new_value = "100"
                elif new_value == "off":
                    new_value = "0"

            _write_device_stats(device_id, new_value,)

def _send_x10_cmd(request, device, old_value, new_value, simulation_mode):
    """
    Send a x10 command
    @param request : HTTP request
    @param device : a Device object
    @param old_value : previous value associated to the device
    @param new_value : new value sent to the device
    @param simulation_mode : True if we are in simulation mode
    """
    if not _is_user_connected(request):
        return None

    output = ""
    xPL_schema = "x10.basic"
    xPL_param = ""
    if device.is_appliance():
        xPL_param = "device=%s,command=%s" % (device.address, new_value)
    elif device.is_lamp():
        if new_value == "on" or new_value == "off":
            xPL_param = "device=%s,command=%s" % (device.address, new_value)
        else:
            # TODO check if type is int and 0 <= value <= 100
            if int(new_value)-int(old_value) > 0:
                cmd = "bright"
            else:
                cmd = "dim"
            level = abs(int(new_value)-int(old_value))
            xPL_param = "command=%s,device=%s,level=%s" % (cmd, device.address, str(level))

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

def _clear_device_stats(request, device_id):
    """
    Clear stats of a device or all devices
    @param request : HTTP request
    @param device_id : device id
    """
    if _is_user_admin(request):
        if device_id == "0": 
            # For all devices
            for device in _db.list_devices():
                _db.del_all_device_stats(device.id)
        else:
            _db.del_all_device_stats(device_id)

def _go_to_page(request, html_page, page_title, **attribute_list):
    """
    Common method called to go to an html page
    @param request : HTTP request
    @param html_page : the page to go to
    @param page_title : page title
    @param **attribute_list : list of attributes (dictionnary) that need to be put in the HTTP response
    @return an HttpResponse object
    """
    response_attr_list = {}
    response_attr_list['page_title'] = page_title
    response_attr_list['sys_config'] = _db.get_system_config()
    user = _get_user_connected(request)
    response_attr_list['user'] = user
    response_attr_list['is_user_admin'] = _is_user_admin(request)
    response_attr_list['is_user_connected'] = _is_user_connected(request)
    for attribute in attribute_list:
        response_attr_list[attribute] = attribute_list[attribute]
    return render_to_response(html_page, response_attr_list)

def _get_user_connected(request):
    """
    Get current user connected
    @param request : HTTP request
    @return the user or None
    """
    try:
        return request.session['s_user']
    except KeyError:
        return None

def _is_user_connected(request):
    """
    Check if the user is connected
    @param request : HTTP request
    @return True or False
    """
    try:
        request.session['s_user']
        return True
    except KeyError:
        return False

def _is_user_admin(request):
    """
    Check if user has administrator rights
    @param request : HTTP request
    @return True or False
    """
    user = _get_user_connected(request)
    return user is not None and user['is_admin']

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
    
def admin_organisation_devices(request):
    """
    Method called when the admin devices organisation page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)
    rooms_list = _db.list_rooms()
    device_category_list = _db.list_device_categories()
    devices_list = _db.list_devices()
    device_tech_list = _db.list_device_technologies()
    page_title = _("Organisation des dispositifs")
    return _go_to_page(request, 'admin/organisation/devices.html', page_title,
                      device_category_list=device_category_list, rooms_list=rooms_list,
                      devices_list=devices_list, device_tech_list=device_tech_list)
					  
def admin_organisation_rooms(request):
    """
    Method called when the admin rooms organisation page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)
    unattribued_devices = _db.search_devices(room_id=None)
    devices_list = _db.list_devices()
    rooms_list = _db.list_rooms()
    areas_list = _db.list_areas()
    icons_room = ["default", "kitchen", "bedroom", "livingroom", "tvlounge", "bathroom"]
    page_title = _("Organisation des pieces")
    return _go_to_page(request, 'admin/organisation/rooms.html', page_title,
    				devices_list=devices_list, unattribued_devices=unattribued_devices,
                    rooms_list=rooms_list, areas_list=areas_list,
                    icons_room=icons_room)
					  
def admin_organisation_areas(request):
    """
    Method called when the admin areas organisation page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not _is_user_admin(request):
        return index(request)
    unattribued_rooms = _db.search_rooms(area_id=None)
    rooms_list = _db.list_rooms()
    areas_list = _db.list_areas()
    icons_area = ["grndfloor", "firstfloor", "basement"]
    page_title = _("Organisation des zones")
    return _go_to_page(request, 'admin/organisation/areas.html', page_title,
                       unattribued_rooms=unattribued_rooms, rooms_list=rooms_list, areas_list=areas_list,
                    icons_area=icons_area)


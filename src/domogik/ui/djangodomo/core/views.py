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
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from domogik.common import database
from djangodomo.core.models import *

from djangodomo.core.sample_data_helper import SampleDataHelper
from djangodomo.core.XPLHelper import XPLHelper

from django.views.decorators.cache import never_cache
from django_pipes.exceptions import ResourceNotAvailableException

__ADMIN_MANAGEMENT_DOMOGIK = 'admin/management/domogik.html'
__db = database.DbHelper()

def index(request):
    """
    Method called when the main page is accessed
    @param request : the HTTP request
    @return an HttpResponse object
    """
    page_title = _("Domogik Homepage")

    try:
        result_all_rooms = Rooms.getAll()
        result_all_rooms.merge_uiconfig()
        result_house = UIConfigs.getGeneral('house')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    device_list = []
    for device in __db.list_devices():
      device_list.append({'room': device.room_id, 'device': device})

    return __go_to_page(request, 'index.html',
        page_title,
        rooms_list=result_all_rooms.room,
        device_list=device_list,
        house=result_house
    )

def login(request):
    """
    Login process
    @param request : HTTP request
    @return an HttpResponse object
    """
    page_title = _("Login page")
    status = ''
    msg = ''
    if request.method == 'POST':
        # An action was submitted => login action
        login = QueryDict.get(request.POST, "login", False)
        password = QueryDict.get(request.POST, "password", False)
        try:
            result_auth = Accounts.Auth(login, password)
        except ResourceNotAvailableException:
            return render_to_response('error/ResourceNotAvailableException.html')

        if result_auth.status == 'OK':
            account = result_auth.account[0]
            request.session['user'] = {
                'login': account.login,
                'is_admin': (account.is_admin == "True"),
                'first_name': account.person.first_name,
                'last_name': account.person.last_name,
                'skin_used': account.skin_used
            }
            return index(request)
        else:
            # User not found, ask again to log in
            error_msg = _("Sorry unable to log in. Please check login name / password and try again.")
            try:
                result_all_accounts = Accounts.getAllUsers()
            except ResourceNotAvailableException:
                return render_to_response('error/ResourceNotAvailableException.html')
            return __go_to_page(
                request, 'login.html',
                page_title,
                error_msg=error_msg,
                account_list=result_all_accounts.account
            )
    else:
        # User asked to log in
        try:
            result_all_accounts = Accounts.getAllUsers()
        except ResourceNotAvailableException:
            return render_to_response('error/ResourceNotAvailableException.html')
        return __go_to_page(
            request, 'login.html',
            page_title,
            account_list=result_all_accounts.account
        )

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
    if not __is_user_admin(request):
        return index(request)
    page_title = _("Admin page")
    return __go_to_page(request, 'admin/index.html', page_title)

def admin_management_domogik(request):
    """
    Method called when the admin domogik management page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)
    simulation_mode = ""
    admin_mode = ""
    debug_mode = ""
    page_title = _("Gestion de Domogik")
    action = "index"
    sys_config = __db.get_system_config()
    if sys_config.simulation_mode:
        simulation_mode = "checked"
    if __is_user_admin(request):
        admin_mode = "checked"
    if sys_config.debug_mode:
        debug_mode = "checked"
    return __go_to_page(request, __ADMIN_MANAGEMENT_DOMOGIK, page_title,
                       action=action, simulation_mode=simulation_mode,
                       admin_mode=admin_mode, debug_mode=debug_mode)

def save_admin_settings(request):
    """
    Save the administrator settings (admin, debug and simulation mode
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    if request.method == 'POST':
        simulation_mode = QueryDict.get(request.POST, "simulation_mode", False)
        admin_mode = QueryDict.get(request.POST, "admin_mode", False)
        debug_mode = QueryDict.get(request.POST, "debug_mode", False)
        __db.update_system_config(s_simulation_mode=simulation_mode,
                                 s_debug_mode=debug_mode)
    return admin_management_domogik(request)

def load_sample_data(request):
    """
    Load sample data
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    page_title = _(u"Chargement d'un jeu de données de test")
    action = "loadSampleData"

    sys_config = __db.get_system_config()
    if sys_config.simulation_mode != True:
        error_msg = _("The application is not running in simulation mode : can't load sample data")
        return __go_to_page(request, __ADMIN_MANAGEMENT_DOMOGIK,
                           page_title, action=action, error_msg=error_msg)

    sample_data_helper = SampleDataHelper(__db)
    sample_data_helper.create()

    area_list = __db.list_areas()
    room_list = __db.list_rooms()
    device_usage_list = __db.list_device_usages()
    device_list = __db.list_devices()
    device_tech_list = __db.list_device_technologies()
    return __go_to_page(request, __ADMIN_MANAGEMENT_DOMOGIK, page_title,
                        action=action, area_list=area_list, room_list=room_list,
                        device_usage_list=device_usage_list,
                        device_list=device_list, device_tech_list=device_tech_list)

def clear_data(request):
    """
    Clear all data of the system (in the database). Please use with care!
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    page_title = _("Remove all data")
    action = "clearData"

    sys_config = __db.get_system_config()
    if sys_config.simulation_mode != True:
        error_msg = _("The application is not running in simulation mode : can't clear data")
        return __go_to_page(request, __ADMIN_MANAGEMENT_DOMOGIK, page_title,
                            action=action, error_msg=error_msg)

    sample_data_helper = SampleDataHelper(__db)
    sample_data_helper.remove()
    return __go_to_page(request, __ADMIN_MANAGEMENT_DOMOGIK, page_title,
                        action=action)

def __go_to_page(request, html_page, page_title, **attribute_list):
    """
    Common method called to go to an html page
    @param request : HTTP request
    @param html_page : the page to go to
    @param page_title : page title
    @param **attribute_list : list of attributes (dictionnary) that need to be
           put in the HTTP response
    @return an HttpResponse object
    """
    response_attr_list = {}
    response_attr_list['page_title'] = page_title
    response_attr_list['sys_config'] = __db.get_system_config()
    response_attr_list['is_user_connected'] = __is_user_connected(request)
    for attribute in attribute_list:
        response_attr_list[attribute] = attribute_list[attribute]
    return render_to_response(html_page, response_attr_list,
                              context_instance=RequestContext(request))

def __get_user_connected(request):
    """
    Get current user connected
    @param request : HTTP request
    @return the user or None
    """
    try:
        return request.session['user']
    except KeyError:
        return None

def __is_user_connected(request):
    """
    Check if the user is connected
    @param request : HTTP request
    @return True or False
    """
    try:
        request.session['user']
        return True
    except KeyError:
        return False

def __is_user_admin(request):
    """
    Check if user has administrator rights
    @param request : HTTP request
    @return True or False
    """
    user = __get_user_connected(request)
    return user is not None and user['is_admin']

def admin_management_accounts(request):
    """
    Method called when the admin accounts page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    try:
        result_all_accounts = Accounts.getAllUsers()
        result_all_people = Accounts.getAllPeoples()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    page_title = _("Accounts management")
    return __go_to_page(
        request, 'admin/management/accounts.html',
        page_title,
        nav1_admin = "selected",
        nav2_management_accounts = "selected",
        status=status,
        msg=msg,
        accounts_list=result_all_accounts.account,
        peoples_list=result_all_people.person
    )

def admin_organization_devices(request):
    """
    Method called when the admin devices organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')

    try:
        result_all_devices = Devices.getAll()
        result_all_devices.merge_uiconfig()
        result_unattributed_devices = Devices.getWithoutRoom()
        result_all_rooms = Rooms.getAllWithDevices()
        result_all_rooms.merge_uiconfig()
        result_all_usages = DeviceUsages.getAll()
        result_all_types = DeviceTypes.getAll()

    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Devices organization")
    return __go_to_page(
        request, 'admin/organization/devices.html',
        page_title,
        nav1_admin = "selected",
        nav2_organization_devices = "selected",
        status=status,
        msg=msg,
        unattribued_devices=result_unattributed_devices.device,
        rooms_list=result_all_rooms.room,
        devices_list=result_all_devices.device,
        usages_list=result_all_usages.device_usage,
        types_list=result_all_types.device_type
    )

def admin_organization_rooms(request):
    """
    Method called when the admin rooms organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    try:
        result_all_rooms = Rooms.getAll()
        result_all_rooms.merge_uiconfig()
        result_unattributed_rooms = Rooms.getWithoutArea()
        result_all_areas = Areas.getAllWithRooms()
        result_all_areas.merge_uiconfig()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Rooms organization")
    return __go_to_page(
        request, 'admin/organization/rooms.html',
        page_title,
        nav1_admin = "selected",
        nav2_organization_rooms = "selected",
        status=status,
        msg=msg,
        unattribued_rooms=result_unattributed_rooms.room,
        rooms_list=result_all_rooms.room,
        areas_list=result_all_areas.area
    )

def admin_organization_areas(request):
    """
    Method called when the admin areas organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    try:
        result_all_areas = Areas.getAll()
        result_all_areas.merge_uiconfig()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    page_title = _("Areas organization")
    return __go_to_page(
        request, 'admin/organization/areas.html',
        page_title,
        nav1_admin = "selected",
        nav2_organization_areas = "selected",
        status=status,
        msg=msg,
        areas_list=result_all_areas.area
    )

def admin_organization_house(request):
    """
    Method called when the admin house organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    try:
        result_house = UIConfigs.getGeneral('house')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    page_title = _("House organization")
    return __go_to_page(
        request, 'admin/organization/house.html',
        page_title,
        nav1_admin = "selected",
        nav2_organization_house = "selected",
        status=status,
        msg=msg,
        house=result_house
    )

def admin_modules_module(request, module_name):
    """
    Method called when the admin module command page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    try:
        result_module_by_name = Modules.getByName(module_name)
        result_all_modules = Modules.getAll()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    page_title = _("Module")
    return __go_to_page(
        request, 'admin/modules/module.html',
        page_title,
        nav1_admin = "selected",
        nav2_modules_module = "selected",
        modules_list=result_all_modules.module,
        status=status,
        msg=msg,
        module=result_module_by_name.module[0]
    )

def show_house(request):
    """
    Method called when the show index page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    page_title = _("View House")
    try:
        result_all_areas = Areas.getAll()
        result_all_areas.merge_uiconfig()
        result_house = UIConfigs.getGeneral('house')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'show/house.html',
        page_title,
        nav1_show = "selected",
        areas_list=result_all_areas.area,
        house=result_house
    )

def show_area(request, area_id):
    """
    Method called when the show area page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    try:
        result_area_by_id = Areas.getById(area_id)
        result_area_by_id.merge_uiconfig()
        result_rooms_by_area = Rooms.getByArea(area_id)
        result_rooms_by_area.merge_uiconfig()
        result_house = UIConfigs.getGeneral('house')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("View ") + result_area_by_id.area[0].name
    return __go_to_page(
        request, 'show/area.html',
        page_title,
        nav1_show = "selected",
        area=result_area_by_id.area[0],
        rooms_list=result_rooms_by_area.room,
        house=result_house
    )

def show_room(request, room_id):
    """
    Method called when the show room page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    try:
        result_room_by_id = Rooms.getById(room_id)
        result_room_by_id.merge_uiconfig()
        result_devices_by_room = Devices.getByRoom(room_id)
        result_devices_by_room.merge_actuators()
        result_house = UIConfigs.getGeneral('house')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("View ") + result_room_by_id.room[0].name
    return __go_to_page(
        request, 'show/room.html',
        page_title,
        nav1_show = "selected",
        room=result_room_by_id.room[0],
        devices_list=result_devices_by_room.device,
        house=result_house
    )

def show_device(request, device_id):
    """
    Method called when the show device page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    try:
        result_house = UIConfigs.getGeneral('house')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    device = __db.get_device(device_id)
    room_id = device.room_id
    room = __db.get_room_by_id(room_id)
    room_name = room.name
    area_id = room.area_id
    area_name = (__db.get_area_by_id(area_id)).name
    page_title = _("View")
    return __go_to_page(
        request, 'show/device.html',
        page_title,
        nav1_show = "selected",
        device=device,
        area_id=area_id,
        area_name=area_name,
        room_id=room_id,
        room_name=room_name,
        house=result_house
    )

def admin_visualization_devices(request):
    """
    Method called when the admin devices visualization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    try:
        result_all_rooms = Rooms.getAllWithDevices()
        result_all_rooms.merge_uiconfig()
        result_all_rooms.merge_actuators()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Devices visualization")
    return __go_to_page(
        request, 'admin/visualization/devices.html',
        page_title,
        nav1_admin = "selected",
        nav2_visualization_devices = "selected",
        status=status,
        msg=msg,
        rooms_list=result_all_rooms.room,
    )

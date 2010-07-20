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

from django.http import QueryDict
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from domogik.common import database
from domogik.ui.djangodomo.core.models import House, Areas, Rooms, Devices, DeviceUsages, DeviceTechnologies, DeviceTypes, \
                                   DeviceFeatures, FeatureAssociations, Plugins, Accounts

from domogik.ui.djangodomo.core.sample_data_helper import SampleDataHelper

from django_pipes.exceptions import ResourceNotAvailableException


__ADMIN_MANAGEMENT_DOMOGIK = 'admin/management/domogik.html'
__db = database.DbHelper()

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
    response_attr_list['rest_url'] = settings.REST_URL
    response_attr_list['sys_config'] = __db.get_system_config()
    response_attr_list['is_user_connected'] = __is_user_connected(request)
    for attribute in attribute_list:
        response_attr_list[attribute] = attribute_list[attribute]
    return render_to_response(html_page, response_attr_list,
                              context_instance=RequestContext(request))
    
def index(request):
    """
    Method called when the main page is accessed
    @param request : the HTTP request
    @return an HttpResponse object
    """
    page_title = _("Domogik Homepage")
    widgets_list = settings.WIDGETS_LIST

    try:
        result_all_areas = Areas.get_all()
        result_all_areas.merge_rooms()
        result_all_areas.merge_uiconfig()
        result_house = House()
        result_house.merge_feature_associations()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    """
    device_list = []
    for device in __db.list_devices():
        device_list.append({'room': device.room_id, 'device': device})
    """
    return __go_to_page(request, 'index.html',
        page_title,
        widgets=widgets_list,
        areas_list=result_all_areas.area,
        house=result_house
    )

def login(request):
    """
    Login process
    @param request : HTTP request
    @return an HttpResponse object
    """
    page_title = _("Login page")
    if request.method == 'POST':
        # An action was submitted => login action
        user_login = QueryDict.get(request.POST, "login", False)
        user_password = QueryDict.get(request.POST, "password", False)
        try:
            result_auth = Accounts.auth(user_login, user_password)
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
                result_all_accounts = Accounts.get_all_users()
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
            result_all_accounts = Accounts.get_all_users()
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
        result_all_accounts = Accounts.get_all_users()
        result_all_people = Accounts.get_all_people()
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
        people_list=result_all_people.person
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
        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_usages = DeviceUsages.get_all()
        result_all_types = DeviceTypes.get_all()

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
        result_all_rooms = Rooms.get_all()
        result_all_rooms.merge_uiconfig()
        result_unattributed_rooms = Rooms.get_without_area()
        result_all_areas = Areas.get_all()
        result_all_areas.merge_rooms()
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
        rooms_list=result_all_rooms.room,
        unattribued_rooms=result_unattributed_rooms.room,
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
        result_all_areas = Areas.get_all()
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
        result_house = House()
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

def admin_organization_features(request):
    """
    Method called when the admin features organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')

    try:
        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_devices.merge_features()
        result_all_rooms = Rooms.get_all()
        result_all_rooms.merge_uiconfig()
        result_all_rooms.merge_feature_associations()
        result_all_areas = Areas.get_all()
        result_all_areas.merge_uiconfig()
        result_all_areas.merge_feature_associations()
        
        result_house = UIConfigs.get_general('house')
        result_house_features_associations = FeatureAssociations.get_by_house()
        
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Features organization")
    return __go_to_page(
        request, 'admin/organization/features.html',
        page_title,
        nav1_admin = "selected",
        nav2_organization_features = "selected",
        status=status,
        msg=msg,
        areas_list=result_all_areas.area,
        rooms_list=result_all_rooms.room,
        devices_list=result_all_devices.device,
        house=result_house,
        house_features_associations=result_house_features_associations.feature_association
    )
    
def admin_plugins_plugin(request, plugin_name):
    """
    Method called when the admin plugin command page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    try:
        result_plugin_detail = Plugins.get_detail(plugin_name)
        result_all_plugins = Plugins.get_all()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    page_title = _("Plugin")
    return __go_to_page(
        request, 'admin/plugins/plugin.html',
        page_title,
        nav1_admin = "selected",
        nav2_plugins_plugin = "selected",
        plugins_list=result_all_plugins.plugin,
        status=status,
        msg=msg,
        plugin=result_plugin_detail.plugin[0]
    )

def admin_tools_helpers(request):
    """
    Method called when the admin helpers tool page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    if not __is_user_admin(request):
        return index(request)

    status = request.GET.get('status', '')
    msg = request.GET.get('msg', '')
    page_title = _("Helpers tools")
    return __go_to_page(
        request, 'admin/tools/helpers.html',
        page_title,
        nav1_admin = "selected",
        nav2_tools_helpers = "selected",
        status=status,
        msg=msg
	)
	
def show_house(request):
    """
    Method called when the show index page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    page_title = _("View House")
    widgets_list = settings.WIDGETS_LIST

    try:
        result_all_areas = Areas.get_all()
        result_all_areas.merge_uiconfig()

        result_house = House()
        result_house.merge_feature_associations()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'show/house.html',
        page_title,
        widgets=widgets_list,
        nav1_show = "selected",
        areas_list=result_all_areas.area,
        house=result_house
    )

def show_house_edit(request):
    """
    Method called when the show index page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    page_title = _("Edit House")
    widgets_list = settings.WIDGETS_LIST

    try:
        result_house = House()
        result_house.merge_feature_associations()
        result_all_devices.merge_uiconfig()
        result_all_devices.merge_features()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'show/house.edit.html',
        page_title,
        widgets=widgets_list,
        nav1_show = "selected",
        house=result_house,
        devices_list=result_all_devices.device
    )
    
def show_area(request, area_id):
    """
    Method called when the show area page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    widgets_list = settings.WIDGETS_LIST

    try:
        result_area_by_id = Areas.get_by_id(area_id)
        result_area_by_id.merge_uiconfig()
        result_area_by_id.merge_feature_associations()

        result_rooms_by_area = Rooms.get_by_area(area_id)
        result_rooms_by_area.merge_uiconfig()
        result_house = House()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("View ") + result_area_by_id.area[0].name
    return __go_to_page(
        request, 'show/area.html',
        page_title,
        widgets=widgets_list,
        nav1_show = "selected",
        area=result_area_by_id.area[0],
        rooms_list=result_rooms_by_area.room,
        house=result_house
    )

def show_area_edit(request, area_id):
    """
    Method called when the show area page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    widgets_list = settings.WIDGETS_LIST

    try:
        result_area_by_id = Areas.get_by_id(area_id)
        result_area_by_id.merge_uiconfig()
        result_area_by_id.merge_feature_associations()
        result_house = House()
        
        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_devices.merge_features()

    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Edit ") + result_area_by_id.area[0].name
    return __go_to_page(
        request, 'show/area.edit.html',
        page_title,
        widgets=widgets_list,
        nav1_show = "selected",
        area=result_area_by_id.area[0],
        house=result_house,
        devices_list=result_all_devices.device
    )
    
def show_room(request, room_id):
    """
    Method called when the show room page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    widgets_list = settings.WIDGETS_LIST

    try:
        result_room_by_id = Rooms.get_by_id(room_id)
        result_room_by_id.merge_uiconfig()
        result_room_by_id.merge_feature_associations()

        result_house = House()
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("View ") + result_room_by_id.room[0].name
    return __go_to_page(
        request, 'show/room.html',
        page_title,
        widgets=widgets_list,
        nav1_show = "selected",
        room=result_room_by_id.room[0],
        house=result_house
    )

def show_room_edit(request, room_id):
    """
    Method called when the show room page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    widgets_list = settings.WIDGETS_LIST

    try:
        result_room_by_id = Rooms.get_by_id(room_id)
        result_room_by_id.merge_uiconfig()
        result_room_by_id.merge_feature_associations()

        result_house = House()

        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_devices.merge_features()

    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Edit ") + result_room_by_id.room[0].name
    return __go_to_page(
        request, 'show/room.edit.html',
        page_title,
        widgets=widgets_list,
        nav1_show = "selected",
        room=result_room_by_id.room[0],
        house=result_house,
        devices_list=result_all_devices.device
    )
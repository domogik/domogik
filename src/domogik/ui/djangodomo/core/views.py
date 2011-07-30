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
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from django.utils.http import urlquote
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.conf import settings
from distutils2.version import *
from distutils2.version import IrrationalVersionError

from domogik.ui.djangodomo.core.models import (
    House, Areas, Rooms, Devices, DeviceUsages, DeviceTechnologies, DeviceTypes,
    Features, FeatureAssociations, Plugins, Accounts, Rest, Packages
)

from django_pipes.exceptions import ResourceNotAvailableException
from httplib import BadStatusLine

def __go_to_page(request, html_page, page_title, page_messages, **attribute_list):
    """
    Common method called to go to an html page
    @param request : HTTP request
    @param html_page : the page to go to
    @param page_title : page title
    @param **attribute_list : list of attributes (dictionnary) that need to be
           put in the HTTP response
    @return an HttpResponse object
    """
    if (not page_messages) :
        page_messages = []
        
    status = request.GET.get('status', None)
    msg = request.GET.get('msg', None)
    if (msg):
        page_messages.append({'status':status, 'msg':msg })
        
    response_attr_list = {}
    response_attr_list['page_title'] = page_title
    response_attr_list['page_messages'] = page_messages
    response_attr_list['rest_url'] = settings.EXTERNAL_REST_URL
    response_attr_list['is_user_connected'] = __is_user_connected(request)
    for attribute in attribute_list:
        response_attr_list[attribute] = attribute_list[attribute]
    response = render_to_response(html_page, response_attr_list,
                              context_instance=RequestContext(request))
    response['Pragma'] = 'no-cache'
    response['Cache-Control'] = 'no-cache, must-revalidate'
    response['Expires'] = '0'
    return response

def login(request):
    """
    Login process
    @param request : HTTP request
    @return an HttpResponse object
    """
    next = request.GET.get('next', '')

    page_title = _("Login page")
    page_messages = []
    if request.method == 'POST':
        return auth(request, next)
    else:
        try:
            result_all_accounts = Accounts.get_all_users()
        except BadStatusLine:
            return render_to_response('error/BadStatusLine.html')
        except ResourceNotAvailableException:
            return render_to_response('error/ResourceNotAvailableException.html')
        return __go_to_page(
            request, 'login.html',
            page_title,
            page_messages,
            next=next,
            account_list=result_all_accounts.account
        )

def logout(request):
    """
    Logout process
    @param request: HTTP request
    @return an HttpResponse object
    """
    request.session.clear()
    return HttpResponseRedirect('/domogik/')

def auth(request, next):
    # An action was submitted => login action
    user_login = request.POST.get("login",'')
    user_password = request.POST.get("password",'')
    try:
        result_auth = Accounts.auth(user_login, user_password)
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
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
        if next != '':
            return HttpResponseRedirect(next)
        else:
            return HttpResponseRedirect('/domogik/')
    else:
        # User not found, ask again to log in
        error_msg = ugettext(u"Sorry unable to log in. Please check login name / password and try again.")
        return HttpResponseRedirect('/domogik/login/?status=error&msg=%s' % error_msg)

def admin_required(f):
    def wrap(request, *args, **kwargs):
        #this check the session if userid key exist, if not it will redirect to login page
        if not __is_user_admin(request):
            path = urlquote(request.get_full_path())
            return HttpResponseRedirect("/domogik/login/?next=%s" % path)
        return f(request, *args, **kwargs)
    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap

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

def __is_normal_mode(request):
    """
    Check if domogik is installed in developper mode
    @param request : HTTP request
    @return True or False
    """
    try:
        mode = Packages.get_mode()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return mode.mode[0] == "normal"
    
@admin_required
def admin_management_accounts(request):
    """
    Method called when the admin accounts page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    
    page_title = _("Accounts management")
    page_messages = []
    try:
        result_all_accounts = Accounts.get_all_users()
        result_all_people = Accounts.get_all_people()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'admin/management/accounts.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_management_accounts = "selected",
        normal_mode=__is_normal_mode(request),
        accounts_list=result_all_accounts.account,
        people_list=result_all_people.person
    )

@admin_required
def admin_organization_devices(request):
    """
    Method called when the admin devices organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Devices organization")
    page_messages = []

    id = request.GET.get('id', 0)
    try:
        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_usages = DeviceUsages.get_all()
        result_all_types = DeviceTypes.get_all()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return __go_to_page(
        request, 'admin/organization/devices.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_organization_devices = "selected",
        normal_mode=__is_normal_mode(request),
        id=id,
        devices_list=result_all_devices.device,
        usages_list=result_all_usages.device_usage,
        types_list=result_all_types.device_type
    )

@admin_required
def admin_organization_rooms(request):
    """
    Method called when the admin rooms organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Rooms organization")
    page_messages = []

    id = request.GET.get('id', 0)
    try:
        result_all_rooms = Rooms.get_all()
        result_all_rooms.merge_uiconfig()
        result_house_rooms = Rooms.get_without_area()
        result_house_rooms.merge_uiconfig()
        result_all_areas = Areas.get_all()
        result_all_areas.merge_rooms()
        result_all_areas.merge_uiconfig()
        
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return __go_to_page(
        request, 'admin/organization/rooms.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_organization_rooms = "selected",
        normal_mode=__is_normal_mode(request),
        id=id,
        rooms_list=result_all_rooms.room,
        house_rooms=result_house_rooms.room,
        areas_list=result_all_areas.area
    )

@admin_required
def admin_organization_areas(request):
    """
    Method called when the admin areas organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Areas organization")
    page_messages = []

    id = request.GET.get('id', 0)
    try:
        result_all_areas = Areas.get_all()
        result_all_areas.merge_uiconfig()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return __go_to_page(
        request, 'admin/organization/areas.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_organization_areas = "selected",
        normal_mode=__is_normal_mode(request),
        id=id,
        areas_list=result_all_areas.area
    )

@admin_required
def admin_organization_house(request):
    """
    Method called when the admin house organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """
    
    page_title = _("House organization")
    page_messages = []

    try:
        result_house = House()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return __go_to_page(
        request, 'admin/organization/house.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_organization_house = "selected",
        normal_mode=__is_normal_mode(request),
        house=result_house
    )

@admin_required
def admin_organization_widgets(request):
    """
    Method called when the admin widgets organization page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Widgets organization")
    page_messages = []

    try:
        result_all_rooms = Rooms.get_all()
        result_all_rooms.merge_uiconfig()
        result_all_areas = Areas.get_all()
        result_all_areas.merge_uiconfig()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return __go_to_page(
        request, 'admin/organization/widgets.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_organization_widgets = "selected",
        normal_mode=__is_normal_mode(request),
        areas_list=result_all_areas.area,
        rooms_list=result_all_rooms.room
    )

@admin_required
def admin_plugins_plugin(request, plugin_host, plugin_name, plugin_type):
    """
    Method called when the admin plugin command page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_messages = []

    try:
        result_plugin_detail = Plugins.get_detail(plugin_host, plugin_name)
        result_all_plugins = Plugins.get_all()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    if plugin_type == "plugin":
        page_title = _("Plugin")
        return __go_to_page(
            request, 'admin/plugins/plugin.html',
            page_title,
            page_messages,
            nav1_admin = "selected",
            nav2_plugins_plugin = "selected",
            plugins_list=result_all_plugins.plugin,
            normal_mode=__is_normal_mode(request),
            plugin=result_plugin_detail.plugin[0]
        )
    if plugin_type == "hardware":
        page_title = _("Hardware")
        return __go_to_page(
            request, 'admin/plugins/hardware.html',
            page_title,
            page_messages,
            nav1_admin = "selected",
            nav2_plugins_plugin = "selected",
            plugins_list=result_all_plugins.plugin,
            normal_mode=__is_normal_mode(request),
            plugin=result_plugin_detail.plugin[0]
        )

@admin_required
def admin_tools_helpers(request):
    """
    Method called when the admin helpers tool page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Helpers tools")
    page_messages = []

    return __go_to_page(
        request, 'admin/tools/helpers.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_tools_helpers = "selected",
        normal_mode=__is_normal_mode(request),
    )

@admin_required
def admin_tools_rinor(request):
    """
    Method called when the admin rest page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("RINOR informations")
    page_messages = []

    try:
        rinor_result = Rest.get_info()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'admin/tools/rinor.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_tools_rinor = "selected",
        normal_mode=__is_normal_mode(request),
        rinor=rinor_result.rest[0]
    )

@admin_required
def admin_packages_repositories(request):
    """
    Method called when the admin repositories page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Packages repositories")
    page_messages = []
    
    try:
        repositories_result = Packages.get_list_repo()
        if (repositories_result.status == 'OK'):
            repositories=repositories_result.repository
        else:
            repositories=None
            page_messages.append({'status':'error', 'msg':repositories_result.description})
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'admin/packages/repositories.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_packages_repositories = "selected",
        normal_mode=__is_normal_mode(request),
        repositories=repositories
    )

def __get_packages(type, page_messages):
    try:
        packages_result = Packages.get_list()
        installed_result = Packages.get_list_installed()
        plugins_result = Plugins.get_all()
        rest_info = Rest.get_info()
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    dmg_version = NormalizedVersion(suggest_normalized_version(rest_info.rest[0].info.Domogik_release))
    for host in installed_result.package:
        installed = {}
        # List enabled plugins
        if (type == 'plugin'):
            enabled_list = None
            if plugins_result.plugin:
                for host2 in plugins_result.plugin:
                    if host2.host == host.host:
                        enabled_list = host2.list
            if not enabled_list:
                page_messages.append({'status':'warning', 'msg':'No plugin enabled'})
            
        if type in host.installed:
            host.installed.packages = host.installed[type]
            for package in host.installed.packages:
                installed[package.name] = {}
                try:
                    installed[package.name]['version'] = NormalizedVersion(package.release)
                    installed[package.name]['version_error'] = False
                except IrrationalVersionError:
                    package.installed_version_error = True
                    installed[package.name]['version_error'] = True
                    installed[package.name]['version'] = package.release
                #find enabled plugins
                if type == 'plugin' and enabled_list:
                    for plugin in enabled_list:
                        if (plugin.name == package.name):
                            package.enabled = True

        host.available = []
        for package in packages_result.package[0][type]:
            package_min_version = NormalizedVersion(suggest_normalized_version(package.domogik_min_release))
            try:
                package_version = NormalizedVersion(package.release)
                package.version_error = False
            except IrrationalVersionError:
                package.version_error = True
            package.upgrade_require = (package_min_version > dmg_version)
            if package.name not in installed:
                package.install = True
                host.available.append(package)
            # Check if update can be done
            elif not installed[package.name]['version_error'] and not package.version_error:
                if (installed[package.name]['version'] < package_version):
                    package.update = True
                    host.available.append(package)
            elif installed[package.name]['version_error'] and not package.version_error:
                    package.update = True
                    host.available.append(package)
    return installed_result.package

@admin_required
def admin_packages_plugins(request):
    """
    Method called when the admin plugins page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Plugins packages")
    page_messages = []

    packages = __get_packages('plugin', page_messages)
    
    return __go_to_page(
        request, 'admin/packages/plugins.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_packages_plugins = "selected",
        normal_mode=__is_normal_mode(request),
        hosts=packages
    )

@admin_required
def admin_packages_hardwares(request):
    """
    Method called when the admin hardwares page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Hardwares packages")
    page_messages = []

    packages = __get_packages('hardware', page_messages)

    return __go_to_page(
        request, 'admin/packages/hardwares.html',
        page_title,
        page_messages,
        nav1_admin = "selected",
        nav2_packages_hardwares = "selected",
        normal_mode=__is_normal_mode(request),
        hosts=packages
    )
    
@admin_required
def admin_packages_install(request, package_host, package_name, package_release):
    """
    Method called for installing a package
    @param request : HTTP request
    @return an HttpResponse object
    """
    try:
        packages_result = Packages.install(package_host, package_name, package_release)
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return redirect('admin_packages_plugins_view')

@admin_required
def admin_packages_enable(request, package_host, package_name, action):
    """
    Method called for installing a package
    @param request : HTTP request
    @return an HttpResponse object
    """
    try:
        plugins_result = Plugins.enable(package_host, package_name, action)
    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return redirect('admin_packages_plugins_view')

def index(request):
    """
    Method called when the main page is accessed
    @param request : the HTTP request
    @return an HttpResponse object
    """

    page_title = _("Domogik Homepage")
    page_messages = []

    widgets_list = settings.WIDGETS_LIST

    try:
        device_types =  DeviceTypes.get_dict()
        device_usages =  DeviceUsages.get_dict()

        result_all_areas = Areas.get_all()
        result_all_areas.merge_rooms()
        result_all_areas.merge_uiconfig()

        result_house = House()

        result_house_rooms = Rooms.get_without_area()
        result_house_rooms.merge_uiconfig()

    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    return __go_to_page(
        request, 'index.html',
        page_title,
        page_messages,
        widgets=widgets_list,
        device_types=device_types,
        device_usages=device_usages,
        areas_list=result_all_areas.area,
        rooms_list=result_house_rooms.room,
        house=result_house
    )

def show_house(request):
    """
    Method called when the show index page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("View House")
    page_messages = []

    widgets_list = settings.WIDGETS_LIST

    try:
        device_types =  DeviceTypes.get_dict()
        device_usages =  DeviceUsages.get_dict()
        
        result_all_areas = Areas.get_all()
        result_all_areas.merge_uiconfig()

        result_house = House()

        result_house_rooms = Rooms.get_without_area()
        result_house_rooms.merge_uiconfig()

    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'show/house.html',
        page_title,
        page_messages,
        widgets=widgets_list,
        nav1_show = "selected",
        device_types=device_types,
        device_usages=device_usages,
        areas_list=result_all_areas.area,
        rooms_list=result_house_rooms.room,
        house=result_house
    )

@admin_required
def show_house_edit(request, from_page):
    """
    Method called when the show index page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_title = _("Edit House")
    page_messages = []

    widgets_list = settings.WIDGETS_LIST

    try:
        result_house = House()

        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_devices.merge_features()

    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')
    return __go_to_page(
        request, 'show/house.edit.html',
        page_title,
        page_messages,
        widgets=widgets_list,
        nav1_show = "selected",
        from_page = from_page,
        house=result_house,
        devices_list=result_all_devices.device
    )

def show_area(request, area_id):
    """
    Method called when the show area page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_messages = []

    widgets_list = settings.WIDGETS_LIST

    try:
        device_types =  DeviceTypes.get_dict()
        device_usages =  DeviceUsages.get_dict()

        result_area_by_id = Areas.get_by_id(area_id)
        result_area_by_id.merge_uiconfig()

        result_rooms_by_area = Rooms.get_by_area(area_id)
        result_rooms_by_area.merge_uiconfig()

        result_house = House()

    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("View ") + result_area_by_id.area[0].name
    return __go_to_page(
        request, 'show/area.html',
        page_title,
        page_messages,
        widgets=widgets_list,
        nav1_show = "selected",
        device_types=device_types,
        device_usages=device_usages,
        area=result_area_by_id.area[0],
        rooms_list=result_rooms_by_area.room,
        house=result_house
    )

@admin_required
def show_area_edit(request, area_id, from_page):
    """
    Method called when the show area page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_messages = []
    widgets_list = settings.WIDGETS_LIST

    try:
        result_area_by_id = Areas.get_by_id(area_id)
        result_area_by_id.merge_uiconfig()

        result_house = House()

        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_devices.merge_features()

    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Edit ") + result_area_by_id.area[0].name
    return __go_to_page(
        request, 'show/area.edit.html',
        page_title,
        page_messages,
        widgets=widgets_list,
        nav1_show = "selected",
        from_page = from_page,
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
    
    page_messages = []
    widgets_list = settings.WIDGETS_LIST

    try:
        device_types =  DeviceTypes.get_dict()
        device_usages =  DeviceUsages.get_dict()

        result_room_by_id = Rooms.get_by_id(room_id)
        result_room_by_id.merge_uiconfig()

        result_house = House()

    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("View ") + result_room_by_id.room[0].name
    return __go_to_page(
        request, 'show/room.html',
        page_title,
        page_messages,
        widgets=widgets_list,
        nav1_show = "selected",
        device_types=device_types,
        device_usages=device_usages,
        room=result_room_by_id.room[0],
        house=result_house
    )

@admin_required
def show_room_edit(request, room_id, from_page):
    """
    Method called when the show room page is accessed
    @param request : HTTP request
    @return an HttpResponse object
    """

    page_messages = []
    widgets_list = settings.WIDGETS_LIST

    try:
        result_room_by_id = Rooms.get_by_id(room_id)
        result_room_by_id.merge_uiconfig()

        result_house = House()

        result_all_devices = Devices.get_all()
        result_all_devices.merge_uiconfig()
        result_all_devices.merge_features()

    except BadStatusLine:
        return render_to_response('error/BadStatusLine.html')
    except ResourceNotAvailableException:
        return render_to_response('error/ResourceNotAvailableException.html')

    page_title = _("Edit ") + result_room_by_id.room[0].name
    return __go_to_page(
        request, 'show/room.edit.html',
        page_title,
        page_messages,
        widgets=widgets_list,
        nav1_show = "selected",
        from_page = from_page,
        room=result_room_by_id.room[0],
        house=result_house,
        devices_list=result_all_devices.device
    )

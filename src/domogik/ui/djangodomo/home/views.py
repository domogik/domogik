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

from domogik.ui.djangodomo.models import (
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

def admin_required(f):
    def wrap(request, *args, **kwargs):
        #this check the session if userid key exist, if not it will redirect to login page
        if not __is_user_admin(request):
            path = urlquote(request.get_full_path())
            return HttpResponseRedirect("/admin/login/?next=%s" % path)
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
    
def index(request):
    """
    Method called when the main page is accessed
    @param request : the HTTP request
    @return an HttpResponse object
    """

    page_title = _("Domogik")
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
        return HttpResponseRedirect("/rinor/error/BadStatusLine")
    except ResourceNotAvailableException:
        return HttpResponseRedirect("/rinor/error/ResourceNotAvailableException")

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
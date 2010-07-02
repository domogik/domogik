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



Implements
==========


@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from django.conf.urls.defaults import *


urlpatterns = patterns('domogik.ui.djangodomo.core.views',
    url(r'^$', 'index', name="index_view"),

    url(r'login/$', 'login', name='login_view'),
    url(r'logout/$', 'logout', name='logout_view'),

    url(r'admin/$', 'admin_organization_house', name="admin_view"),
    url(r'admin/management/accounts/$', 'admin_management_accounts', name="admin_management_accounts_view"),
    url(r'admin/organization/$', 'admin_organization_house', name="admin_organization_view"),
    url(r'admin/organization/house/$', 'admin_organization_house', name="admin_organization_house_view"),
    url(r'admin/organization/areas/$', 'admin_organization_areas', name="admin_organization_areas_view"),
    url(r'admin/organization/rooms/$', 'admin_organization_rooms', name="admin_organization_rooms_view"),
    url(r'admin/organization/devices/$', 'admin_organization_devices', name="admin_organization_devices_view"),
    url(r'admin/organization/features/$', 'admin_organization_features', name="admin_organization_features_view"),
    url(r'admin/plugin/(?P<plugin_name>\w+)/$', 'admin_plugins_plugin', name="admin_plugins_plugin_view"),
    url(r'admin/tools/helpers/$', 'admin_tools_helpers', name="admin_tools_helpers_view"),

    url(r'show/$', 'show_house', name="show_view"),
    url(r'show/house/$', 'show_house', name="show_house_view"),
    url(r'show/house/edit/$', 'show_house_edit', name="show_house_edit_view"),
    url(r'show/area/(?P<area_id>\d+)/$', 'show_area', name='show_area_view'),
    url(r'show/room/(?P<room_id>\d+)/$', 'show_room', name='show_room_view'),
)

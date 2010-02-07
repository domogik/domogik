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


urlpatterns = patterns('djangodomo.core.views',
    url(r'^$', 'index', name="index_view"),

    url(r'status/$', 'device_status', name='device_status_view'),
    url(r'status/room/(?P<room_id>\d+)/$', 'device_status', name='device_status_view'),
    url(r'status/device/(?P<device_id>\d+)/$', 'device_status', name='device_status_view'),
    
#    url(r'device/(?P<device_id>\d+)/$', 'device', name="device_view"),
#    url(r'device_stats/(?P<device_id>\d+)/$', 'device_stats', name="device_stats_view"),

    url(r'login/$', 'login', name='login_view'),
    url(r'logout/$', 'logout', name='logout_view'),

    url(r'admin/$', 'admin_management_domogik', name="admin_view"),
    url(r'admin/load_sample_data$', 'load_sample_data', name="load_sample_data_view"),
    url(r'admin/clear_data$', 'clear_data', name="clear_data_view"),
    url(r'admin/save_admin_settings$', 'save_admin_settings', name="save_admin_settings_view"),
    url(r'admin/management/domogik/$', 'admin_management_domogik', name="admin_management_domogik_view"),
    url(r'admin/management/modules/$', 'admin_management_modules', name="admin_management_modules_view"),
    url(r'admin/organization/devices/$', 'admin_organization_devices', name="admin_organization_devices_view"),
    url(r'admin/organization/rooms/$', 'admin_organization_rooms', name="admin_organization_rooms_view"),
    url(r'admin/organization/areas/$', 'admin_organization_areas', name="admin_organization_areas_view"),

    url(r'show/$', 'show_index', name="show_view"),
    url(r'show/area/(?P<area_id>\d+)/$', 'show_area', name='show_area_view'),
    url(r'show/room/(?P<room_id>\d+)/$', 'show_room', name='show_room_view'),
    url(r'show/device/(?P<device_id>\d+)/$', 'show_device', name='show_device_view'),
)

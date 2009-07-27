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
    url(r'^$', 'index', name="mainView"),
    
    
    url(r'status/$', 'device_status', name='device_status'),
    url(r'status/room/(?P<room_id>\d+)/$', 'device_status', name='device_status'),
    url(r'status/device/(?P<device_id>\d+)/$', 'device_status', name='device_status'),
    
    url(r'device/(?P<device_id>\d+)/$', 'device', name="deviceView"),
    url(r'device_stats/(?P<device_id>\d+)/$', 'device_stats',
            name="deviceStatsView"),
    url(r'admin/$', 'admin_index', name="adminView"),
    url(r'admin/load_sample_data$', 'load_sample_data',
            name="loadSampleDataView"),
    url(r'admin/clear_data$', 'clear_data', name="clearDataView"),
    url(r'admin/save_admin_settings$', 'save_admin_settings', name="saveAdminSettingsView"),
    
)

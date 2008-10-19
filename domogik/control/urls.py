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
# $LastChangedDate: 2008-10-19 17:10:10 +0200 (dim. 19 oct. 2008) $
# $LastChangedRevision: 168 $

from django.conf.urls.defaults import *

urlpatterns = patterns('domogik.control.views',
	url(r'^$', 'index', name="mainView"),
	url(r'rooms/$', 'rooms', name="roomsView"),
	url(r'capacities/(?P<roomId>\d+)/$', 'capacities', name="capacitiesView"),
	url(r'items/(?P<roomId>\d+),(?P<capacityId>\d+)/$', 'items', name="itemsView"),
	url(r'admin/$', 'adminIndex', name="adminView"),
	url(r'admin/load_sample_data$', 'loadSampleData', name="loadSampleDataView"),
	url(r'admin/clear_data$', 'clearData', name="clearDataView"),
)

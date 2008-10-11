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
# $LastChangedDate: 2008-10-11 18:11:59 +0200 (sam. 11 oct. 2008) $
# $LastChangedRevision: 138 $

from django.conf.urls.defaults import *

urlpatterns = patterns('domogik.control.views',
	(r'^$', 'index'),
	(r'rooms/$', 'rooms'),
	(r'capacities/(?P<roomId>\d+)/$', 'capacities'),
	(r'items/(?P<roomId>\d+),(?P<capacityId>\d+)/$', 'items'),
	(r'admin/$', 'adminIndex'),
	(r'admin/load_sample_data$', 'loadSampleData'),
	(r'admin/clear_data$', 'clearData'),
)

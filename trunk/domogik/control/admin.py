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
# $LastChangedDate: 2009-01-18 12:34:24 +0100 (dim. 18 janv. 2009) $
# $LastChangedRevision: 295 $

# This is the admin part of Domogik

from django.contrib import admin
from domogik.control.models import Area
from domogik.control.models import Room
from domogik.control.models import Device
from domogik.control.models import DeviceProperty
from domogik.control.models import ApplicationSetting

class DevicePropertyInline(admin.TabularInline):
	model = DeviceProperty
	extra = 1

class DeviceAdmin(admin.ModelAdmin):
	inlines = [DevicePropertyInline]

admin.site.register(Area)
admin.site.register(Room)
admin.site.register(Device, DeviceAdmin)
admin.site.register(ApplicationSetting)

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
# $LastChangedDate: 2008-10-25 14:31:13 +0200 (sam. 25 oct. 2008) $
# $LastChangedRevision: 179 $

# This is the admin part of Domogik

from django.contrib import admin
from domogik.control.models import Room
from domogik.control.models import Item
from domogik.control.models import Thermometer
from domogik.control.models import Capacity
from domogik.control.models import Comm_technology
from domogik.control.models import ApplicationSetting

admin.site.register(Room)
admin.site.register(Item)
admin.site.register(Thermometer)
admin.site.register(Capacity)
admin.site.register(Comm_technology)
admin.site.register(ApplicationSetting)

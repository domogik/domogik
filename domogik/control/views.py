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
# $LastChangedDate: 2008-10-08 23:16:00 +0200 (mer. 08 oct. 2008) $
# $LastChangedRevision: 128 $

from django.shortcuts import render_to_response

def index(request):
	pageTitle = "Main page of Domogik"
	return render_to_response('index.html', {'pageTitle': pageTitle})

def rooms(request):
	pageTitle = "List of the rooms"
	return render_to_response('rooms.html', {'pageTitle': pageTitle})

def capacities(request, roomId):
	pageTitle = "List of the capacities for room " + roomId
	return render_to_response('capacities.html', {'pageTitle': pageTitle})

def items(request, capacityId):
	pageTitle = "List of the items for the capacity " + capacityId
	return render_to_response('items.html', {'pageTitle': pageTitle})

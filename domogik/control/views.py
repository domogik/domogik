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
# $LastChangedDate: 2008-10-11 15:28:12 +0200 (sam. 11 oct. 2008) $
# $LastChangedRevision: 133 $

from django.shortcuts import render_to_response
from domogik.control.models import Room
from domogik.control.models import Capacity
from domogik.control.models import Item

def index(request):
	pageTitle = "Main page of Domogik"
	return render_to_response('index.html', {'pageTitle': pageTitle})

def rooms(request):
	pageTitle = "List of the rooms"
	roomList = Room.objects.all()
	return render_to_response(
		'rooms.html',
		{
			'pageTitle'	: pageTitle,
			'roomList'	: roomList
		}
	)

def capacities(request, roomId):
	room = Room.objects.get(pk=roomId)
	capacityList = Capacity.objects.filter(room__id=roomId)
	pageTitle = "List of the capacities for : " + room.name
	return render_to_response(
		'capacities.html',
		{
			'pageTitle'		: pageTitle,
			'roomName' 		: room.name,
			'capacityList' 	: capacityList
		}
	)

def items(request, capacityId):
	capacity = Capacity.objects.get(pk=capacityId)
	room = Room.objects.get(capacity__id=capacity.id)
	# itemList = Item.objects.filter(capacity__id=capacityId)
	pageTitle = "List of the items for the capacity  : " + capacity.name + " (" + room.name + ")"
	return render_to_response(
		'items.html',
		{
			'pageTitle': pageTitle,
			'capacityName' : capacity.name
		}
	)

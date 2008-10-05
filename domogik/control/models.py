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
# $LastChangedDate: 2008-10-05 11:27:19 +0200 (dim. 05 oct. 2008) $
# $LastChangedRevision: 119 $

from django.db import models

class Rooms(models.Model):
    name = models.CharField(max_length=30)

class Capacities(models.Model):
    CAPACITY_CHOICES = (
		('temperature', 'Temperature'),
		('light', 'Light'),
		('music', 'Music')
    )
    room = models.ForeignKey(Rooms)
    capacity = models.CharField(max_length=30, choices = CAPACITY_CHOICES)

class Items(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=30)

class Music(models.Model):
    STATE_CHOICES = (
		('play', 'Play'),
		('pause', 'Pause'),
		('stop', 'Stop')
    )
    room = models.ForeignKey(Rooms)
    title = models.CharField(max_length=150)
    time = models.TimeField()
    current_time = models.TimeField()
    state = models.CharField(max_length=10, choices = STATE_CHOICES)


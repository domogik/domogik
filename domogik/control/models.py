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
# $LastChangedDate: 2008-10-11 15:23:09 +0200 (sam. 11 oct. 2008) $
# $LastChangedRevision: 132 $

from django.db import models

class Thermometer(models.Model):
	thermometer = models.CharField(max_length=16)
	label = models.CharField(max_length=50)

	# This is the representation of the object
	def __unicode__(self):
		return self.thermometer + " (" + self.label +")"

class Capacity(models.Model):
	CAPACITY_CHOICES = (
		('temperature', 'Temperature'),
		('light', 'Light'),
		('music', 'Music')
	)
	# TODO : rename 'capacity' to 'name'
	capacity = models.CharField(max_length=30, choices = CAPACITY_CHOICES)

	# This is the representation of the object
	def __unicode__(self):
		# Improve this and add the room description
		return self.capacity

class Room(models.Model):
	name = models.CharField(max_length=30)
	capacities = models.ManyToManyField(Capacity) 
	thermometers = models.ManyToManyField(Thermometer)

	# This is the representation of the object
	def __unicode__(self):
		return self.name

class Item(models.Model):
	name = models.CharField(max_length=30)
	description = models.CharField(max_length=30)
	room = models.ForeignKey(Room)
	capacity = models.ForeignKey(Capacity)
	# This is the representation of the object
	def __unicode__(self):
		return self.name

class Music(models.Model):
	STATE_CHOICES = (
		('play', 'Play'),
		('pause', 'Pause'),
		('stop', 'Stop')
	)
	room = models.ForeignKey(Room)
	title = models.CharField(max_length=150)
	time = models.TimeField()
	current_time = models.TimeField()
	state = models.CharField(max_length=10, choices = STATE_CHOICES)

class Statement(models.Model):
	date = models.DateTimeField()
	thermometer = models.ForeignKey(Thermometer)
	temperature = models.FloatField()

class State(models.Model):
	item = models.ForeignKey(Item)
	state = models.SmallIntegerField() 
	date = models.DateTimeField()

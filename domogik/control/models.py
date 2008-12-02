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
# $LastChangedDate: 2008-12-02 22:19:16 +0100 (mar. 02 déc. 2008) $
# $LastChangedRevision: 209 $

from django.db import models

class DeviceCapacity(models.Model):
	CAPACITY_CHOICES = (
		('Temperature', 'Temperature'),
		('Heating', 'Heating'),
		('Lighting', 'Lighting'),
		('Music', 'Music'),
		('Power point','Power point')
	)
	name = models.CharField(max_length=30, choices=CAPACITY_CHOICES)

	# This is the representation of the object
	def __unicode__(self):
		return self.name

class Area(models.Model):
	name = models.CharField(max_length=30)

	# This is the representation of the object
	def __unicode__(self):
		return self.name

class Room(models.Model):
	name = models.CharField(max_length=30)
	area = models.ForeignKey(Area)

	# This is the representation of the object
	def __unicode__(self):
		return self.name

class DeviceTechnology(models.Model):
	TECHNOLOGY_CHOICES = (
		('X10', 'X10'),
		('One-Wire', 'One-Wire'),
		('PLCBus', 'PLCBus'),
		('IR', 'IR'),
	)
	name =  models.CharField(max_length=20, choices=TECHNOLOGY_CHOICES)
	description = models.TextField(max_length=255, null=True, blank=True)

	class Meta:
		verbose_name_plural = "Devices technologies"

	# This is the representation of the object
	def __unicode__(self):
		return self.name

class Device(models.Model):
	name = models.CharField(max_length=30)
	serialNb = models.CharField(max_length=30, null=True, blank=True)
	reference = models.CharField(max_length=30, null=True, blank=True)
	address = models.CharField(max_length=30)
	description = models.TextField(max_length=80, null=True, blank=True)
	technology = models.ForeignKey(DeviceTechnology)
	capacity = models.ForeignKey(DeviceCapacity)
	room = models.ForeignKey(Room)
	canGiveFeedback = models.BooleanField(default=False)

	# This is the representation of the object
	def __unicode__(self):
		return self.name + " - " + self.address + " (" + self.reference + ")"

class DeviceProperty(models.Model):
	key = models.CharField(max_length=30)
	value = models.CharField(max_length=80)
	device = models.ForeignKey(Device)

	class Meta:
		unique_together = ("key", "device")

	# This is the representation of the object
	def __unicode__(self):
		return self.key + "=" + self.value

class StateReading(models.Model):
	device = models.ForeignKey(Device)
	value = models.FloatField()
	date = models.DateTimeField()

class ApplicationSetting(models.Model):
	simulationMode = models.BooleanField("Simulation mode", default=True)
	adminMode = models.BooleanField("Administrator mode", default=True)
	debugMode = models.BooleanField("Debug mode", default=True)

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
	state = models.CharField(max_length=10, choices=STATE_CHOICES)

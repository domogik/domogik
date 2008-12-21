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
# $LastChangedDate: 2008-12-21 11:09:12 +0100 (dim. 21 déc. 2008) $
# $LastChangedRevision: 286 $

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

	class Meta:
		verbose_name_plural = "Device capacities"

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
		verbose_name_plural = "Device technologies"

	# This is the representation of the object
	def __unicode__(self):
		return self.name

class Device(models.Model):
	name = models.CharField(max_length=30)
	serialNb = models.CharField("Serial Nb", max_length=30, null=True, blank=True)
	reference = models.CharField(max_length=30, null=True, blank=True)
	address = models.CharField(max_length=30)
	description = models.TextField(max_length=80, null=True, blank=True)
	technology = models.ForeignKey(DeviceTechnology)
	capacity = models.ForeignKey(DeviceCapacity)
	room = models.ForeignKey(Room)
	canGiveFeedback = models.BooleanField("Can give feedback", default=False)

	# This is the representation of the object
	def __unicode__(self):
		return self.name + " - " + self.address + " (" + self.reference + ")"

class DeviceProperty(models.Model):
	VALUETYPE_CHOICES = (
		('BOOLEAN', 'BOOLEAN'),
		('ALPHANUM', 'ALPHANUM'),
	)
	VALUE_UNIT_CHOICES = (
		('%', '%'),
	)

	key = models.CharField(max_length=30)
	value = models.CharField(max_length=80)
	valueType = models.CharField(max_length=20, choices=VALUETYPE_CHOICES)
	valueUnit = models.CharField(max_length=30, choices=VALUE_UNIT_CHOICES)
	isChangeableByUser = models.BooleanField("Can be changed by user")
	device = models.ForeignKey(Device)

	class Meta:
		unique_together = ("key", "device")

	# This is the representation of the object
	def __unicode__(self):
		return self.key + "=" + self.value

class DeviceCmdLog(models.Model):
	date = models.DateTimeField()
	value = models.CharField(max_length=80)
	comment = models.CharField(max_length=80, null=True, blank=True)
	isSuccessful = models.BooleanField("Successful")
	device = models.ForeignKey(Device)

	# This is the representation of the object
	def __unicode__(self):
		return self.date + ":" + self.value + " (success=" + self.isSuccessful + ")"

class StateReading(models.Model):
	device = models.ForeignKey(Device)
	value = models.FloatField()
	date = models.DateTimeField()

class ApplicationSetting(models.Model):
	# TODO : make sure there is only one line for this model
	# See : http://groups.google.com/group/django-users/browse_thread/thread/d44a9417a81c4860?hl=en
	# Or : http://docs.djangoproject.com/en/dev/ref/models/instances/#ref-models-instances
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

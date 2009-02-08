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
# $LastChangedDate: 2009-02-08 16:33:23 +0100 (dim. 08 févr. 2009) $
# $LastChangedRevision: 347 $

from django.db import models

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

class DeviceCategory(models.Model):
	"""
	Examples : temperature, heating, lighting, music, ...
	"""
	name = models.CharField(max_length=30)

	class Meta:
		verbose_name_plural = "Device categories"

class Device(models.Model):
	TECHNOLOGY_CHOICES = (
		('x10', 'X10'),
		('onewire', 'One-Wire'),
		('plcbus', 'PLCBus'),
		('ir', 'IR'),
	)

	name = models.CharField(max_length=30)
	serialNb = models.CharField("Serial Nb", max_length=30, null=True, blank=True)
	reference = models.CharField(max_length=30, null=True, blank=True)
	address = models.CharField(max_length=30)
	description = models.TextField(max_length=80, null=True, blank=True)
	technology = models.CharField(max_length=20, choices=TECHNOLOGY_CHOICES)
	deviceCategory = models.ForeignKey(DeviceCategory)
	room = models.ForeignKey(Room)
	canGiveFeedback = models.BooleanField("Can give feedback", default=False)
	isResetable = models.BooleanField("Is resetable", default=False)

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
	valueType = models.CharField("Value type", max_length=20, choices=VALUETYPE_CHOICES)
	valueUnit = models.CharField("Value unit", max_length=30, choices=VALUE_UNIT_CHOICES)
	isChangeableByUser = models.BooleanField("Can be changed by user")
	device = models.ForeignKey(Device)

	class Meta:
		unique_together = ("key", "device")
		verbose_name_plural = "Device properties"

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

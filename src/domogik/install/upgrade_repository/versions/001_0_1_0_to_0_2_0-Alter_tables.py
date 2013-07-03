#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

Upgrade / downgrade database script

Implements
==========

@author: Marc Schneider <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from sqlalchemy import Table, MetaData, String, Column, Index
from domogik.common.sql_schema import Device, PluginConfig, DeviceType, DeviceStats
from domogik.common import database_utils

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    #939
    core_device = Table(Device.__tablename__, meta, autoload=True)
    core_device.c.address.alter(type=String(255))

    #1064
    core_plugin_config = Table(PluginConfig.__tablename__, meta, autoload=True)
    if not database_utils.column_exists(migrate_engine, PluginConfig.__tablename__, 'id'):
        core_plugin_config.c.name.alter(name='id')

    #1110
    core_device_type = Table(DeviceType.__tablename__, meta, autoload=True)
    core_device_type.c.name.alter(type=String(80))
    
    #1061
    core_device_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
    if not database_utils.index_exists(migrate_engine, DeviceStats.__tablename__, 'ix_core_device_stats_skey'):
        Index('ix_core_device_stats_skey', core_device_stats.c.skey).create()
    
    #1274
    core_device_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
    if not database_utils.index_exists(migrate_engine, DeviceStats.__tablename__, 'ix_core_device_stats_date_skey_device_id'):
        Index('ix_core_device_stats_date_skey_device_id', core_device_stats.c.date, core_device_stats.c.skey, 
                                                          core_device_stats.c.device_id).create()

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    #939
    core_device = Table(Device.__tablename__, meta, autoload=True)
    core_device.c.address.alter(type=String(30))

    #1064
    core_plugin_config = Table(PluginConfig.__tablename__, meta, autoload=True)
    core_plugin_config.c.id.alter(name='name')

    #1110
    core_device_type = Table(DeviceType.__tablename__, meta, autoload=True)
    core_device_type.c.name.alter(type=String(30))

    #1061
    core_device_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
    Index('ix_core_device_stats_skey', core_device_stats.c.skey).drop()

    #1274
    core_device_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
    Index('ix_core_device_stats_date_skey_device_id', core_device_stats.c.date, core_device_stats.c.skey, 
                                                      core_device_stats.c.device_id).drop()

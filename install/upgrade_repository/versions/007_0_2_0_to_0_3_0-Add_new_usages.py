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

from sqlalchemy import MetaData, Table
from domogik.common.sql_schema import DeviceUsage

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    #1490
    core_device_usage = Table(DeviceUsage.__tablename__, meta, autoload=True)
    insert = core_device_usage.insert()
    if core_device_usage.select(whereclause="id='scene'").execute().fetchone() is None:
        insert.execute(id='scene', name='Scene', description='Special for Scene plugin',
                       default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;False&quot;, &quot;state1&quot;:&quot;True&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    #1490
    core_device_usage = Table(DeviceUsage.__tablename__, meta, autoload=True)
    core_device_usage.delete(whereclause="id='scene'").execute()

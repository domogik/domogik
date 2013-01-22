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
from domogik.common import database_utils

def upgrade(migrate_engine):
    # core_device_config
    if database_utils.table_exists(migrate_engine, "core_device_config"):
        migrate_engine.execute("DROP table core_device_config")
    # core_system_info
    if database_utils.table_exists(migrate_engine, "core_system_info"):
        migrate_engine.execute("DROP table core_system_info")
    # core_system_config
    if database_utils.table_exists(migrate_engine, "core_system_config"):
        migrate_engine.execute("DROP table core_system_config")
    # core_trigger
    if database_utils.table_exists(migrate_engine, "core_trigger"):
        migrate_engine.execute("DROP table core_trigger") 
    # core_ui_item_config
    if database_utils.table_exists(migrate_engine, "core_ui_item_config"):
        migrate_engine.execute("DROP table core_ui_item_config") 

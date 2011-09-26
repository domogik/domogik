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

Upgrade the database

Implements
==========


@author: Marc Schneider <marc@mirelsol.org>
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys

from sqlalchemy import create_engine
from domogik.common import database

__db = database.DbHelper()
__url = __db.get_url_connection_string()
__engine = create_engine(__url)

def process(new_db_version):
    print("=== Upgrade process")
    #while __db.get_db_version() != new_db_version:
    __execute_upgrade()

def __execute_upgrade():
    current_db_version = __db.get_db_version()
    print("Upgrading database version %s" % current_db_version)
    if current_db_version == '0.1.0' or current_db_version is None:
        new_version == '0.2.0'
        print("Upgrading to version : %s" % new_version)
        

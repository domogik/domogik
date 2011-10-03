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

Upgrade the database.
Note that the application version number should *always* be superior or equal to the database one.

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
from domogik import __version__

__db = database.DbHelper()
__url = __db.get_url_connection_string()
__engine = create_engine(__url)
__prog_version = __version__

def process():
    """Main function that run the update process"""
    old_db_version = __db.get_db_version()
    if old_db_version is None or old_db_version == '':
        __db.update_db_version('0.1.0')
    print("=== Upgrade process (programm version : %s, database version = %s)" % (__prog_version, __db.get_db_version()))
    upgrade_done = False
    while __execute_upgrade():
        pass
    if old_db_version == __db.get_db_version():
        print("\tNothing to do!")
    print("=== Upgrade process terminated")

def __execute_upgrade():
    """Check the application version number and the database one. Executes an upgrade if necessary
    
    @return true if an upgrade was done
    
    """
    old_db_version = __db.get_db_version()
    if old_db_version == '':
        old_db_version = None
    __check_for_sanity(old_db_version)

    if __prog_version == '0.2.0':
        if old_db_version == '0.1.0':
            __upgrade_from_0_1_0_to_0_2_0()
            return True

    if __prog_version == '0.3.0':
        if old_db_version == '0.1.0':
            __upgrade_from_0_1_0_to_0_2_0()
            return True
        if old_db_version == '0.2.0':
            __upgrade_from_0_2_0_to_0_3_0()
            return True

    return False

def __check_for_sanity(db_version):
    """Check that the upgrade process can be run"""

    if db_version > __prog_version:
        print("Something is wrong with your installation:")
        print("Your database version number (%s) is superior to the application one (%s)" 
              % (db_version, __prog_version))
        print("Upgrade process aborted")    
        sys.exit(1)

def __upgrade_from_0_1_0_to_0_2_0():
    print("\t> Upgrading database version from 0.1.0 to 0.2.0")
    
    # Execute update statements here
    
    __db.update_db_version('0.2.0')

def __upgrade_from_0_2_0_to_0_3_0():
    print("\t> Upgrading database version from 0.2.0 to 0.3.0")
    
    # Execute update statements here
    
    __db.update_db_version('0.3.0')

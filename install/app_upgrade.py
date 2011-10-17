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

Upgrade the code and the database.
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
from sqlalchemy.ext.sqlsoup import SqlSoup

from domogik.common import database
from domogik import APP_VERSION, DB_VERSION

_url = database.DbHelper().get_url_connection_string()
_db = SqlSoup(create_engine(_url))

def process():
    """Main function that run the update process"""
    #_upgrade_system_info_structure()
    old_app_version = _get_current_app_version()
    old_db_version = _get_current_db_version()
    print("=== Upgrade process")
    print("\t> Current version (application : %s, database = %s)" % (_get_current_app_version(), _get_current_db_version()))
    print("\t> New version (application : %s, database = %s)" % (_get_new_app_version(), _get_new_db_version()))
    _check_for_sanity()
    # Database upgrade
    while _execute_db_upgrade():
        pass
    if old_db_version == _get_current_db_version():
        print("\tThe database was NOT upgraded: nothing to do!")
    
    # Application upgrade
    while _execute_app_upgrade():
        pass
    if old_app_version == _get_current_app_version():
        print("\tThe application was NOT upgraded: nothing to do!")

    _commit()
    
    print("=== Upgrade process terminated")

####################
# Database upgrade #
####################

def _execute_db_upgrade():
    """Eventually upgrade the database (depending on the current version number)
    
    @return true if an upgrade was done
    
    """
    old_db_version = _get_current_db_version()
    new_db_version = _get_new_db_version()

    if new_db_version == '0.2.0':
        if old_db_version == '0.1.0':
            _upgrade_db_from_0_1_0_to_0_2_0()
            return True

    if new_db_version == '0.3.0':
        if old_db_version == '0.1.0':
            _upgrade_db_from_0_1_0_to_0_2_0()
            return True
        if old_db_version == '0.2.0':
            _upgrade_db_from_0_2_0_to_0_3_0()
            return True

    return False

def _upgrade_db_from_0_1_0_to_0_2_0():
    print("\t> Upgrading database version from 0.1.0 to 0.2.0")
    # Execute update statements here
    sql_code = "ALTER TABLE core_system_info ADD COLUMN app_version VARCHAR(30);\n"
    _db.execute(sql_code)
    _update_db_version('0.2.0')

def _upgrade_db_from_0_2_0_to_0_3_0():
    print("\t> Upgrading database version from 0.2.0 to 0.3.0")
    
    # Execute update statements here
    # ...
    _update_db_version('0.3.0')

##############################
# Application (code) upgrade #
##############################

def _execute_app_upgrade():
    """Eventually upgrade the application (depending on the current version number)
    
    @return true if an upgrade was done
    
    """
    old_app_version = _get_current_app_version()
    new_app_version = _get_new_app_version()
    if new_app_version == '0.2.0':
        if old_app_version == '0.1.0':
            _upgrade_app_from_0_1_0_to_0_2_0()
            return True

    return False

def _upgrade_app_from_0_1_0_to_0_2_0():
    print("\t> Upgrading application version from 0.1.0 to 0.2.0")
    # Do something here
    # ...
    _update_app_version('0.2.0')
    
#####################
# Utility functions #
#####################

def _check_for_sanity():
    """Check that the upgrade process can be run"""
    pass
    if _get_new_db_version() > _get_new_app_version():
        print("Internal error")
        print("The new database version number (%s) can't be superior to the application one (%s)"
              % (_get_new_db_version(), _get_new_app_version()))
        _abort_upgrade_process()

    if _get_current_db_version() > _get_current_app_version():
        print("Something is wrong with your installation:")
        print("Your database version number (%s) is superior to the application one (%s)" 
              % (_get_current_db_version(), _get_current_app_version()))
        _abort_upgrade_process()

def _get_current_db_version():
    """Return the current version of the database"""
    db_version = _db.execute("SELECT db_version FROM core_system_info").fetchone()[0]
    if db_version is None or db_version == '':
        # Should only happen for the first upgrade using this script
        return '0.1.0'
    else:
        return db_version

def _get_new_db_version():
    """Return the version of the database we should upgrade to"""
    return DB_VERSION

def _update_db_version(db_version):
    """Update the version of the database"""
    _db.execute("UPDATE core_system_info SET db_version='%s'" % db_version)

def _get_current_app_version():
    """Return the current version of the application"""
    try:
        
        app_version = _db.execute("SELECT app_version FROM core_system_info").fetchone()[0]
        # Should only happen if the 'app_version' column doesn't exist (first application upgrade using this script)
        if app_version is None or app_version == '':
            app_version = '0.1.0'
        return app_version
    except Exception:
        return '0.1.0'

def _get_new_app_version():
    """Return the version of the application we should upgrade to"""
    return APP_VERSION

def _update_app_version(app_version):
    """Update the version of the application"""
    _db.execute("UPDATE core_system_info SET app_version='%s'" % app_version)

def _commit():
    _db.commit()

def _abort_upgrade_process():
    print("Upgrade process aborted")
    sys.exit(1)

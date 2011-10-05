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
from domogik import CODE_VERSION, DB_VERSION

__url = database.DbHelper().get_url_connection_string()
__db = SqlSoup(create_engine(__url))

def process():
    """Main function that run the update process"""
    #__upgrade_system_info_structure()
    old_db_version = __get_current_db_version()
    if old_db_version is None or old_db_version == '':
        __update_db_version('0.1.0')
    print("=== Upgrade process")
    print("\t> Current version (code : %s, database = %s)" % (__get_current_code_version(), __get_current_db_version()))
    print("\t> New version (code : %s, database = %s)" % (__get_new_code_version(), __get_new_db_version()))
    upgrade_done = False
    while __execute_db_upgrade():
        pass
    if old_db_version == __get_current_db_version():
        print("\tNothing to do!")
    else:
        __db.commit()
    print("==== Upgrade process of the database terminated")
    
    print("=== Upgrade process terminated")

####################
# Database upgrade #
####################

def __execute_db_upgrade():
    """Check the application version number and the database one. Executes an upgrade if necessary
    
    @return true if an upgrade was done
    
    """
    old_db_version = __get_current_db_version()
    new_db_version = __get_new_db_version()
    __check_for_sanity(old_db_version)

    if new_db_version == '0.2.0':
        if old_db_version == '0.1.0':
            __upgrade_db_from_0_1_0_to_0_2_0()
            return True

    if new_db_version == '0.3.0':
        if old_db_version == '0.1.0':
            __upgrade_db_from_0_1_0_to_0_2_0()
            return True
        if old_db_version == '0.2.0':
            __upgrade_db_from_0_2_0_to_0_3_0()
            return True

    return False

def __upgrade_db_from_0_1_0_to_0_2_0():
    print("\t> Upgrading database version from 0.1.0 to 0.2.0")
    
    # Execute update statements here
    sql_code = "ALTER TABLE core_system_info ADD COLUMN code_version VARCHAR(30);\n"
    sql_code += "UPDATE core_system_info SET app_version='%s';\n" % __get_new_code_version()
    print(sql_code)
    __db.execute(sql_code)
    __update_db_version('0.2.0')

def __upgrade_db_from_0_2_0_to_0_3_0():
    print("\t> Upgrading database version from 0.2.0 to 0.3.0")
    
    # Execute update statements here
    
    __update_db_version('0.3.0')

################
# Code upgrade #
################

#####################
# Utility functions #
#####################

def __check_for_sanity(db_version):
    """Check that the upgrade process can be run"""
    pass
    """
    if db_version > __app_version:
        print("Something is wrong with your installation:")
        print("Your database version number (%s) is superior to the application one (%s)" 
              % (db_version, __app_version))
        print("Upgrade process aborted")    
        sys.exit(1)
    """

def __get_current_db_version():
    """Return the current version of the database"""
    return __db.execute("SELECT db_version FROM core_system_info").fetchone()[0]

def __get_new_db_version():
    """Return the version of the database we should upgrade to"""
    return DB_VERSION

def __update_db_version(db_version):
    __db.execute("UPDATE core_system_info SET db_version='%s'" % db_version)

def __get_current_code_version():
    """Return the current version of the code"""
    try:
        return __db.execute("SELECT code_version FROM core_system_info").fetchone()[0]
    except exception:
        # Should only happen if the 'code_version' column doesn't exist (first code upgrade using this script)
        return __get_new_code_version()

def __get_new_code_version():
    """Return the version of the code we should upgrade to"""
    return CODE_VERSION

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

Scripts to upgrade the code and the database.
Add here scripts for each new release.

Implements
==========


@author: Marc Schneider <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from distutils2.version import NormalizedVersion

####################
# Database upgrade #
####################

def db_upgrade(upgrade_instance):
    """Eventually upgrade the database (depending on the current version number)

    @param upgrade_instance : instance of the Upgrade object
    @return true if an upgrade was done
    
    """
    old_db_version = upgrade_instance.get_current_db_version()
    new_db_version = upgrade_instance.get_new_db_version()

    if new_db_version == NormalizedVersion('0.2.0'):
        if old_db_version == NormalizedVersion('0.1.0'):
            _upgrade_db_from_0_1_0_to_0_2_0(upgrade_instance)
            return True

    if new_db_version == NormalizedVersion('0.3.0'):
        if old_db_version == NormalizedVersion('0.1.0'):
            upgrade_db_from_0_1_0_to_0_2_0(upgrade_instance)
            return True
        if old_db_version == NormalizedVersion('0.2.0'):
            _upgrade_db_from_0_2_0_to_0_3_0(upgrade_instance)
            return True

    return False

def _upgrade_db_from_0_1_0_to_0_2_0(upgrade_instance):
    print("\t+ Upgrading database version from 0.1.0 to 0.2.0")
    # Execute update statements here
    sql_code = "ALTER TABLE core_system_info ADD COLUMN app_version VARCHAR(30);\n"
    sql_code += "ALTER TABLE core_device modify address VARCHAR(255);\n"
    sql_code += "ALTER TABLE core_plugin_config CHANGE COLUMN name id VARCHAR(30) NOT NULL;\n"
    upgrade_instance._sql_execute(sql_code)
    upgrade_instance.update_db_version('0.2.0')

def _upgrade_db_from_0_2_0_to_0_3_0(upgrade_instance):
    print("\t+ Upgrading database version from 0.2.0 to 0.3.0")
    
    # Execute update statements here
    # ...
    upgrade_instance.update_db_version('0.3.0')

##############################
# Application (code) upgrade #
##############################

def app_upgrade(upgrade_instance):
    """Eventually upgrade the application (depending on the current version number)

    @param upgrade_instance : instance of the Upgrade object    
    @return true if an upgrade was done
    
    """
    old_app_version = upgrade_instance.get_current_app_version()
    new_app_version = upgrade_instance.get_new_app_version()
    if new_app_version == NormalizedVersion('0.2.0'):
        if old_app_version == NormalizedVersion('0.1.0'):
            _upgrade_app_from_0_1_0_to_0_2_0(upgrade_instance)
            return True

    return False

def _upgrade_app_from_0_1_0_to_0_2_0(upgrade_instance):
    print("\t+ Upgrading application version from 0.1.0 to 0.2.0")
    # Do something here
    # ...
    upgrade_instance.update_app_version('0.2.0')

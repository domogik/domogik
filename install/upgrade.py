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
When releasing a new version don't touch anything here, use 'upgrade_scripts.py' instead.

Implements
==========


@author: Marc Schneider <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys

from distutils2.version import NormalizedVersion, suggest_normalized_version

from sqlalchemy import create_engine
from sqlalchemy.ext.sqlsoup import SqlSoup

from domogik.common import database
from domogik import __version__, DB_VERSION

import upgrade_scripts

_url = database.DbHelper().get_url_connection_string()

class Upgrade:
    def __init__(self, engine):
        self.__db = SqlSoup(engine)

    def process(self):
        """Main function that run the update process"""
        #_upgrade_system_info_structure()
        old_app_version = self.get_current_app_version()
        old_db_version = self.get_current_db_version()
        print("=== Upgrade process")
        print("\t> Current version (application : %s, database = %s)" 
              % (self.get_current_app_version(), self.get_current_db_version()))
        print("\t> New version (application : %s, database = %s)" 
              % (self.get_new_app_version(), self.get_new_db_version()))
        self._sanity_check_before_upgrade()
        # Database upgrade
        while upgrade_scripts.db_upgrade(self):
            pass
        if old_db_version == self.get_current_db_version():
            print("\tThe database was NOT upgraded: nothing to do!")
        
        # Application upgrade
        while upgrade_scripts.app_upgrade(self):
            pass
        if old_app_version == self.get_current_app_version():
            print("\tThe application was NOT upgraded: nothing to do!")

        print("=== Upgrade process terminated")
    
    def set_version(self, app_version, db_version):
        """Set the version of the application and the database"""
        self.update_app_version(app_version)
        self.update_db_version(db_version)
        self.commit()
    
    def commit(self):
        self.__db.commit()
        
    #####################
    # Utility functions #
    #####################

    def _sanity_check_before_upgrade(self):
        """Check that the upgrade process can be run"""
        
        # We use NormalizedVersion to be able to make comparisons
        new_db_version = self.get_new_db_version()
        new_app_version = self.get_new_app_version()
        current_db_version = self.get_current_db_version()
        current_app_version = self.get_current_app_version()

        if new_db_version > new_app_version:
            print("Internal error")
            print("The new database version number (%s) can't be superior to the application one (%s)"
                  % (new_db_version, new_app_version))
            self._abort_upgrade_process()
        
        if current_db_version > new_db_version:
            print("Something is wrong with your installation:")
            print("Your database version number (%s) is superior to the one you're trying to install (%s)" 
                  % (current_db_version, new_db_version))
            self._abort_upgrade_process()

        if current_app_version > new_app_version:
            print("Something is wrong with your installation:")
            print("Your application version number (%s) is superior to the one you're trying to install (%s)" 
                  % (current_app_version, new_app_version))
            self._abort_upgrade_process()

        if current_db_version > current_app_version:
            print("Something is wrong with your installation:")
            print("Your database version number (%s) is superior to the application one (%s)" 
                  % (current_db_version, current_app_version))
            self._abort_upgrade_process()

    def get_current_db_version(self):
        """Return the current version of the database"""
        db_version = self._sql_execute("SELECT db_version FROM core_system_info").fetchone()[0]
        if db_version is None or db_version == '':
            # Should only happen for the first upgrade using this script
            return NormalizedVersion('0.1.0')
        else:
            return NormalizedVersion(self._suggest_normalized_version(db_version))

    def get_new_db_version(self):
        """Return the version of the database we should upgrade to (normalized version)"""
        return NormalizedVersion(self._suggest_normalized_version(DB_VERSION))

    def update_db_version(self, db_version):
        """Update the version of the database"""
        if self._sql_execute("SELECT db_version FROM core_system_info").fetchone() is None:
            sql = "INSERT INTO core_system_info (db_version) VALUES('%s')" % db_version
        else:
            sql = "UPDATE core_system_info SET db_version='%s'" % db_version
        self._sql_execute(sql)

    def get_current_app_version(self):
        """Return the current version of the application"""
        try:
            
            app_version = self._sql_execute("SELECT app_version FROM core_system_info").fetchone()[0]
            # Should only happen if the 'app_version' column doesn't exist (first application upgrade using this script)
            if app_version is None or app_version == '':
                app_version = NormalizedVersion('0.1.0')
            return NormalizedVersion(self._suggest_normalized_version(app_version))
        except Exception:
            return NormalizedVersion('0.1.0')

    def get_new_app_version(self):
        """Return the version of the application we should upgrade to (normalized version)"""
        return NormalizedVersion(self._suggest_normalized_version(__version__))

    def update_app_version(self, app_version):
        """Update the version of the application"""
        if self._sql_execute("SELECT app_version FROM core_system_info").fetchone() is None:
            sql = "INSERT INTO core_system_info (app_version) VALUES('%s')" % app_version
        else:
            sql = "UPDATE core_system_info SET app_version='%s'" % app_version
        self._sql_execute(sql)

    def _suggest_normalized_version(self, version):
        n_version = suggest_normalized_version(version)
        if n_version is None:
            print("Error : invalid version number : %s" % version)
            print("See : http://wiki.domogik.org/Release_numbering")
            self._abort_install_process()
        else:
            return n_version

    def _sql_execute(self, sql_code):
        return self.__db.execute(sql_code)

    def _abort_upgrade_process(self, message=""):
        print("Upgrade process aborted : %s" % message)
        sys.exit(1)

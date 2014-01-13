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

Install the Domogik database based on config file values

Implements
==========


@author: Marc Schneider <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import getopt, subprocess, os, sys, tempfile

from sqlalchemy import create_engine, MetaData, Table

from migrate.versioning.api import db_version
from migrate.versioning.api import version as rep_version
from migrate.versioning.api import drop_version_control
from migrate.versioning.api import version_control
from migrate.versioning.api import upgrade as db_upgrade

from domogik.common import sql_schema
from domogik.common import database
from domogik.common.configloader import Loader

DB_BACKUP_FILE = tempfile.gettempdir() + "/domogik.sql"
# Get full path for 'upgrade_repository'
UPGRADE_REPOSITORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upgrade_repository")
MIGRATE_VERSION_TABLE = "migrate_version"

_db = database.DbHelper()
_url = _db.get_url_connection_string()
_engine = create_engine(_url)

###
# Installer
###

def execute_system_command(arg_list, p_stdout=subprocess.PIPE, p_stderr=subprocess.PIPE):
    process = subprocess.Popen(arg_list, shell=False, stdout=p_stdout, stderr=p_stderr)
    (val, error) = process.communicate()
    if len(error) != 0:
        abort_install_process(error)
    return val

def abort_install_process(error_msg=""):
    print("Install process aborted : %s " % error_msg)
    sys.exit(1)

def backup_existing_database(confirm=True):
    if not _db.is_db_type_mysql():
        print("Can't backup your database, only mysql is supported (you have : %s)" % _db.get_db_type())
        return
    if confirm:
        answer = raw_input("Do you want to backup your database? [Y/n] ")
        if answer == 'n':
            return
    answer = raw_input("Backup file? [%s] " % DB_BACKUP_FILE)
    if answer != '':
        backup_directory = answer
    print("Backing up your database to %s" % DB_BACKUP_FILE)
    with open(DB_BACKUP_FILE, 'w') as f:
        mysqldump_cmd = ['mysqldump', '-u', _db.get_db_user()]
        if _db.get_db_password():
            mysqldump_cmd.extend(('-p%s' %_db.get_db_password(), _db.get_db_name()))
        else:
            mysqldump_cmd.append(_db.get_db_name())
        execute_system_command(mysqldump_cmd, p_stdout=f)

def set_db_under_version_control():
    if not is_db_under_version_control():
        print("Creating versioning table '%s' ..." % MIGRATE_VERSION_TABLE)
        version_control(_db.get_url_connection_string(), UPGRADE_REPOSITORY)

def is_db_under_version_control():
    migrate_version_t = Table(MIGRATE_VERSION_TABLE, sql_schema.metadata)
    return migrate_version_t.exists(_engine)

def get_repository_version():
    return rep_version(UPGRADE_REPOSITORY)

def get_db_version():
    return db_version(_db.get_url_connection_string(), UPGRADE_REPOSITORY)

def drop_all_tables():
    print("Droping all existing tables...")
    sql_schema.metadata.drop_all(_engine)
    if is_db_under_version_control():
        drop_version_control(_db.get_url_connection_string(), UPGRADE_REPOSITORY)

def add_initial_data():
    """Add required data when running a brand new install"""
    print("Adding initial data...")

    # Create a default user account
    _db.add_default_user_account()

    # Create device usages
    _db.add_device_usage(du_id='light', du_name='Light', du_description='Lamp, light usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='appliance', du_name='Appliance', du_description='Appliance usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='shutter', du_name='Shutter', du_description='Shutter usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Down&quot;, &quot;state1&quot;:&quot;Up&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='air_conditionning', du_name='Air conditioning', du_description='Air conditioning usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='ventilation', du_name='Ventilation', du_description='Ventilation usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='heating', du_name='Heating', du_description='Heating',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:1, &quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='computer', du_name='Computer', du_description='Desktop computer usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='server', du_name='Server', du_description='Server usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='telephony', du_name='Telephony', du_description='Phone usage',
                        du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } } ')
    _db.add_device_usage(du_id='tv', du_name='TV', du_description='Television usage',
                    du_default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='water', du_name='Water', du_description='Water service',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
#    _db.add_device_usage(du_id='gas', du_name='Gas', du_description='Gas service',
#                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='electricity', du_name='Electricity', du_description='Electricity service',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='temperature', du_name='Temperature', du_description='Temperature',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {&quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {&quot;unit&quot;:&quot;&amp;deg;C&quot;}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='mirror', du_name='Mir:ror', du_description='Mir:ror device',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='nanoztag', du_name='Nanoztag', du_description='Nanoztag device',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='music', du_name='Music', du_description='Music usage',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='water_tank', du_name='Water Tank', du_description='Water tank usage',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='christmas_tree', du_name='Christmas Tree', du_description='Happy Christmas!!',
                        du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='portal', du_name='Portal', du_description='Portal',
                         du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Closed&quot;, &quot;state1&quot;:&quot;Open&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='security_camera', du_name='Security camera', du_description='Security camera',
                         du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    _db.add_device_usage(du_id='door', du_name='Door', du_description='Portal',
                         du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Closed&quot;, &quot;state1&quot;:&quot;Open&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='window', du_name='Window', du_description='Portal',
                         du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Closed&quot;, &quot;state1&quot;:&quot;Open&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    _db.add_device_usage(du_id='scene', du_name='Scene', du_description='Special for Scene plugin',
                         du_default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;False&quot;, &quot;state1&quot;:&quot;True&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')

    # Set sqlalchemy migrate version to the latest one
    rep_v = get_repository_version()
    meta = MetaData(bind=_engine)
    migrate_table = Table(MIGRATE_VERSION_TABLE, meta, autoload=True)
    update = migrate_table.update(migrate_table.c.repository_path == UPGRADE_REPOSITORY)
    update.execute(version=int(rep_v))

def user_want_database_upgrade():
    answer = raw_input("Do you want to upgrade your database? [Y/n] ")
    if answer == 'n':
        return False
    return True

def upgrade_app():
    """Upgrade process of the application"""
    if not is_db_under_version_control():
        if not user_want_database_upgrade():
            return False
        backup_existing_database()
        set_db_under_version_control()
        print("Upgrading database to version %s" % get_repository_version())
        # Upgrade to the current version of the repository
        db_upgrade(_db.get_url_connection_string(), UPGRADE_REPOSITORY)
    else:
        # Upgrade to the current version of the repository
        rep_v = get_repository_version()
        db_v = get_db_version()
        if (int(db_v) > int(rep_v)):
            abort_install_process("Database version (%s) is greater than the repository one (%s)" % (db_v, rep_v))
        print("Current repository version is : %s" % get_repository_version())
        print("Current database version is : %s" % get_db_version())
        if (int(rep_v) > int(db_v)):
            if not user_want_database_upgrade():
                return False
            backup_existing_database()
            print("Upgrading database to version %s" % rep_v)
            db_upgrade(_db.get_url_connection_string(), UPGRADE_REPOSITORY)
        else:
            print("Nothing to do, database is up to date.")
    return True

def install_or_upgrade():
    """Initialize the databases (install new one or upgrade it)"""
    print("Using database", _db.get_db_type())
    #TODO: improve this test
    if not sql_schema.Device.__table__.exists(bind=_engine):
        print("It appears that your database doesn't contain the required tables.")
        answer = raw_input("Should they be created? [Y/n] ")
        if answer == "n":
            abort_install_process("Can't continue, system tables are missing")
        else:
            drop_all_tables() # Make sure we don't have any existing table in the database
            print("Creating all tables...")
            print(sql_schema.metadata)
            set_db_under_version_control()
            sql_schema.metadata.create_all(_engine)
            set_db_under_version_control()
            add_initial_data()
    else:
        # Upgrade
        upgrade_app()

def check_install_is_ok():
    if not is_db_under_version_control():
        abort_install_process("Your database is NOT under version control. Can't continue!")
    db_v = get_db_version()
    rep_v = get_repository_version()
    if int(db_v) != int(rep_v):
        abort_install_process("Something is wrong with your installation : repository and database version are not " 
                             +"the same\nDatabase version:\t %s\nRepository version:\t %s" % (db_v, rep_v))
    print("Installation complete.")

def usage():
    print("Usage : app_installer [-r, --reset] [-d, --dump]")
    print("-r or --reset : drop all tables")
    print("-d or --dump : make a dump of the database")

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hrd", ["help", "reset", "dump"])
        if len(args) != 0:
            usage()
            sys.exit(2)
        
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        else:
            if opt in ('-r', '--reset'):
                answer = raw_input("Are you sure you want to drop all your tables? [y/N] ")
                if answer == 'y':
                    drop_all_tables()
                sys.exit()
            elif opt in ('-d', '--dump'):
                backup_existing_database(confirm=False)
                sys.exit()

    install_or_upgrade()
    check_install_is_ok()

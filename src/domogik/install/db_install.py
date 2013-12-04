# -*- coding: utf-8 -*-

import os
import pwd
import sys
import platform
import ConfigParser
import argparse
import shutil
import errno
import traceback
import time
import tempfile
from domogik.common import sql_schema
from domogik.common import database
from sqlalchemy import create_engine, MetaData, Table
from alembic.config import Config
from alembic import command


BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
DB_BACKUP_FILE = "{0}/domogik-{1}.sql".format(tempfile.gettempdir(), int(time.time()))

alembic_cfg = Config("alembic.ini")

_db = database.DbHelper()
_url = _db.get_url_connection_string()
_engine = create_engine(_url)

def info(msg):
    print(u"%s [ %s ] %s" % (BLUE,msg,ENDC))
def ok(msg):
    print(u"%s ==> %s  %s" % (OK,msg,ENDC))
def warning(msg):
    print(u"%s ==> %s  %s" % (WARNING,msg,ENDC))
def fail(msg):
    print(u"%s ==> %s  %s" % (FAIL,msg,ENDC))

def install_or_upgrade_db():
    info("Installing or upgrading the db")
    if not sql_schema.Device.__table__.exists(bind=_engine):
        sql_schema.metadata.drop_all(_engine)
        ok("Droping all existing tables...")
	sql_schema.metadata.create_all(_engine)
	ok("Creating all tables...")
    	with _db.session_scope():
	    _db.add_default_user_account()
	ok("Creating admin user...")
	command.stamp(alembic_cfg, "head")
	ok("Setting db version to head")
    else:
	ok("Creating backup")
        backup_existing_database()
	ok("Upgrading")
        command.upgrade(alembic_cfg, "head")
    return 

def backup_existing_database(confirm=True):
    if not _db.is_db_type_mysql():
        warning("Can't backup your database, only mysql is supported (you have : %s)" % _db.get_db_type())
        return
    if confirm:
        answer = raw_input("Do you want to backup your database? [Y/n] ")
        if answer == 'n':
            return
    answer = raw_input("Backup file? [%s] " % DB_BACKUP_FILE)
    if answer != '':
        bfile = answer
    else:
        bfile = DB_BACKUP_FILE
    ok("Backing up your database to %s" % bfile)
    with open(bfile, 'w') as f:
        mysqldump_cmd = ['mysqldump', '-u', _db.get_db_user()]
        if _db.get_db_password():
            mysqldump_cmd.extend(('-p%s' %_db.get_db_password(), _db.get_db_name()))
        else:
            mysqldump_cmd.append(_db.get_db_name())
        mysqldump_cmd.append(">")
        mysqldump_cmd.append(DB_BACKUP_FILE)
        os.system(" ".join(mysqldump_cmd))

if __name__ == "__main__":
    install_or_upgrade_db()


# -*- coding: utf-8 -*-

import os
import pwd
import sys
# debug
# TODO : delete later
print("SYS.PATH={0}".format(sys.path))
import getpass
print("USER={0}".format(getpass.getuser()))
# end debug
import platform
import ConfigParser
import argparse
import shutil
import errno
import traceback
import time
import tempfile
#from domogik.common import sql_schema
#from domogik.common import database
#from sqlalchemy import create_engine, MetaData, Table
#from alembic.config import Config
#from alembic import command


### >>>> only needed to test this python file alone
BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def info(msg):
    print(u"%s [ %s ] %s" % (BLUE,msg,ENDC))
def ok(msg):
    print(u"%s ==> %s  %s" % (OK,msg,ENDC))
def warning(msg):
    print(u"%s ==> %s  %s" % (WARNING,msg,ENDC))
def fail(msg):
    print(u"%s ==> %s  %s" % (FAIL,msg,ENDC))
### <<<<


class DbInstall():

    def __init__(self):
        """
        """
        from domogik.common import sql_schema
        from domogik.common import database
        from sqlalchemy import create_engine, MetaData, Table
        from alembic.config import Config
        from alembic import command

        self.db_backup_file = "{0}/domogik-{1}.sql".format(tempfile.gettempdir(), int(time.time()))
        self.alembic_cfg = Config("alembic.ini")

        self._db = database.DbHelper()
        self._url = self._db.get_url_connection_string()
        self._engine = create_engine(self._url)

    def install_or_upgrade_db(self):
        from domogik.common import sql_schema
        from domogik.common import database
        from sqlalchemy import create_engine, MetaData, Table
        from alembic.config import Config
        from alembic import command

        info("Installing or upgrading the db")
        if not sql_schema.Device.__table__.exists(bind=self._engine):
            sql_schema.metadata.drop_all(self._engine)
            ok("Droping all existing tables...")
            sql_schema.metadata.create_all(self._engine)
            ok("Creating all tables...")
            with self._db.session_scope():
                self._db.add_default_user_account()
            ok("Creating admin user...")
            command.stamp(self.alembic_cfg, "head")
            ok("Setting db version to head")
        else:
            ok("Creating backup")
            self.backup_existing_database()
            ok("Upgrading")
            command.upgrade(self.alembic_cfg, "head")
        return 
    
    def backup_existing_database(self, confirm=True):
        from domogik.common import sql_schema
        from domogik.common import database
        from sqlalchemy import create_engine, MetaData, Table
        from alembic.config import Config
        from alembic import command

        if not self._db.is_db_type_mysql():
            warning("Can't backup your database, only mysql is supported (you have : %s)" % self._db.get_db_type())
            return
        if confirm:
            answer = raw_input("Do you want to backup your database? [Y/n] ")
            if answer == 'n':
                return
        answer = raw_input("Backup file? [%s] " % self.db_backup_file)
        if answer != '':
            bfile = answer
        else:
            bfile = self.db_backup_file
        ok("Backing up your database to %s" % bfile)
        with open(bfile, 'w') as f:
            mysqldump_cmd = ['mysqldump', '-u', self._db.get_db_user()]
            if self._db.get_db_password():
                mysqldump_cmd.extend(('-p%s' %self._db.get_db_password(), self._db.get_db_name()))
            else:
                mysqldump_cmd.append(self._db.get_db_name())
            mysqldump_cmd.append(">")
            mysqldump_cmd.append(self.db_backup_file)
            os.system(" ".join(mysqldump_cmd))
    
if __name__ == "__main__":
    dbi = DbInstall()
    dbi.install_or_upgrade_db()


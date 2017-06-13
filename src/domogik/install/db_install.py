# -*- coding: utf-8 -*-

import os
import pwd
import sys
# debug
# TODO : delete later
import getpass
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
    print(u"{0} [ {1} ] {2}".format(BLUE,msg,ENDC))
def ok(msg):
    print(u"{0} ==> {1}  {2}".format(OK,msg,ENDC))
def warning(msg):
    print(u"{0} ==> {1}  {2}".format(WARNING,msg,ENDC))
def fail(msg):
    print(u"{0} ==> {1}  {2}".format(FAIL,msg,ENDC))
### <<<<


class DbInstall():

    def __init__(self):
        """
        """
        from domogik.common import sql_schema
        from domogik.common import database
        from sqlalchemy import create_engine, MetaData, Table
        from sqlalchemy import __version__ as sqla_version
        from alembic.config import Config
        from alembic import command

        info(u"SQLAlchemy version is : {0}".format(sqla_version))

        self.db_backup_file = "{0}/domogik-{1}.sql".format(tempfile.gettempdir(), int(time.time()))
        self.alembic_cfg = Config("alembic.ini")

        self._db = database.DbHelper(use_cache=False)
        self._url = self._db.get_url_connection_string()
        self._engine = create_engine(self._url)

    def create_db(self):
        from sqlalchemy_utils import database_exists, create_database

        if not self._db.is_db_type_mysql():
            raise OSError("Create data base of {0} is not implemented. Sorry! ".format(self._db.get_db_type()))

        info("Checking the db existance")
        if self.check_db_exists() == True:
            info("The database already exists, we won't create it")
            return

        info("Applying user permissions for {0}...".format(self._db.get_db_user()))
        mysql_script = ""
        mysql_script+= "grant usage on *.* to '{0}'@'localhost' identified by '{1}';\n".format(self._db.get_db_user(), self._db.get_db_password())
        mysql_script+= "grant usage on *.* to '{0}'@'%' identified by '{1}';\n".format(self._db.get_db_user(), self._db.get_db_password())
        mysql_script+= "grant all privileges on {0}.* to '{1}'@'localhost';\n".format(self._db.get_db_name(), self._db.get_db_user())
        mysql_script+= "grant all privileges on {0}.* to '{1}'@'%';\n".format(self._db.get_db_name(), self._db.get_db_user())
        mysql_script+= "flush privileges;\n".format(self._db.get_db_name(), self._db.get_db_user())
        sh_script = "mysql -p -u root << TXT\n"+mysql_script+"TXT\n"
        print("---------------------------------------------------")
        print(sh_script)
        print("---------------------------------------------------")

        ok("Please entrer {0} root password".format(self._db.get_db_type()))
        res = os.system(sh_script)
        if ( res != 0 ):
            fail("Applying user permissions for {0} : done".format(self._db.get_db_user()))
        else:
            ok("Applying user permissions for {0} : done".format(self._db.get_db_user()))
            info("Creating the database...")
            create_database(self._db.get_engine().url)
            if database_exists(self._db.get_engine().url):
                ok("Database created sucessfully")
                return True
            else:
                fail("Database creation failed")
                return False



    def check_db_exists(self):
        from sqlalchemy_utils import database_exists, create_database
        ok("Checking if the mysql db exists")
        with self._db.session_scope():
            try:
                if not database_exists(self._db.get_engine().url):
                    #create_database(self._db.get_engine().url)
                    #if database_exists(self._db.get_engine().url):
                    #    ok("Database created sucessfully")
                    #    return True
                    #else:
                    #    fail("Database creation failed")
                    #    return False
                    info("Database does not exist")
                    return False
                else:
                    info("Database already exists")
                    return True
            except:
                info("Database does not exist or user grants not yet applied")
                return False


    def install_or_upgrade_db(self, skip_backup=False, command_line=False):
        """
            @param skip_backup = True/False. If True, don't do the backup
            @param command_line = True/False. If True, the --command-line option have been passed
                                              and we should not ask question to the user. So we should
                                              not ask the user to confirm the backup action or not
        """
        from domogik.common import sql_schema
        from domogik.common import database
        from sqlalchemy import create_engine, MetaData, Table
        from alembic.config import Config
        from alembic import command

        info("Installing or upgrading the db")
        if not sql_schema.Device.__table__.exists(bind=self._engine):
            # Removed because we are not sure why we did this before... Fritz - Jan 2017
            #sql_schema.metadata.drop_all(self._engine)
            #ok("Droping all existing tables...")

            info("Creating all tables...")
            sql_schema.metadata.create_all(self._engine)
            ok("Creating all tables : done")

            info("Creating admin user...")
            with self._db.session_scope():
                self._db.add_default_user_account()
            ok("Creating admin user : done")

            info("Setting db version to head...")
            command.stamp(self.alembic_cfg, "head")
            ok("Setting db version to head : done")
        else:
            if not skip_backup:
                info("Creating backup...")
                if command_line:
                    ask_confirm_backup = False
                else:
                    ask_confirm_backup = True
                self.backup_existing_database(ask_confirm_backup)
                ok("Creating backup : done")
            info("Upgrading...")
            command.upgrade(self.alembic_cfg, "head")
            ok("Upgrading : done")
        return

    def backup_existing_database(self, ask_confirm=True):
        from domogik.common import sql_schema
        from domogik.common import database
        from sqlalchemy import create_engine, MetaData, Table
        from alembic.config import Config
        from alembic import command

        if not self._db.is_db_type_mysql():
            warning("Can't backup your database, only mysql is supported (you have : {0})".format(self._db.get_db_type()))
            return
        if ask_confirm:
            answer = raw_input("Do you want to backup your database? [Y/n] ")
            if answer == 'n':
                return
            answer = raw_input("Backup file? [{0}] ".format(self.db_backup_file))
            if answer != '':
                bfile = answer
            else:
                bfile = self.db_backup_file
        else:
            bfile = self.db_backup_file
        ok("Backing up your database to {0}".format(bfile))
        with open(bfile, 'w') as f:
            mysqldump_cmd = ['mysqldump', '-u', self._db.get_db_user()]
            if self._db.get_db_password():
                mysqldump_cmd.extend(('-p{0}'.format(self._db.get_db_password()), self._db.get_db_name()))
            else:
                mysqldump_cmd.append(self._db.get_db_name())
            mysqldump_cmd.append(">")
            #mysqldump_cmd.append(self.db_backup_file)
            mysqldump_cmd.append(bfile)
            os.system(" ".join(mysqldump_cmd))

if __name__ == "__main__":
    dbi = DbInstall()
    dbi.install_or_upgrade_db()


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

Plugin purpose
==============

Backup script called from crontab

History
=======


Implements
==========


@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import os
import traceback
import time
import tempfile
import errno
from domogik.common import sql_schema
from domogik.common import database
from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common.plugin import PACKAGES_DIR
from domogik.butler.brain import LEARN_FILE, STAR_FILE
from sqlalchemy import create_engine, MetaData, Table
from alembic.config import Config
from alembic import command


def title(msg):
    """ Display a title to improve output reading
    """
    print(u"=========================================================")
    print(u"{0}".format(msg))
    print(u"=========================================================")


def get_backup_dir():
    ### Read the configuration file
    try:
        cfg = Loader('backup')
        config = cfg.load()
        conf = dict(config[1])
        return conf['folder']

    except:
        print(u"Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
        return None

def get_packages_dir():
    ### Read the configuration file
    try:
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])
        return os.path.join(conf['libraries_path'], PACKAGES_DIR)

    except:
        print(u"Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
        return None

def backup_some_files(files):
    for fic in files:
        src = fic['src']
        dst = fic['dst']
        cmd = "tar cvzfh {0}/{1} {2}".format(folder, dst, src)
        print(cmd)
        os.system(cmd)

def backup_database(folder):
    title(u"Backup of the database")
    now = time.strftime("%Y%m%d-%H%M")
    db_backup_file = "{0}/domogik-database-{1}.sql.gz".format(folder, now)
    _db = database.DbHelper(use_cache=False)
    if not _db.is_db_type_mysql():
        print("Can't backup your database, only mysql is supported (you have : {0})".format(_db.get_db_type()))
        return
    print("Backing up your database to {0}".format(db_backup_file))

    mysqldump_cmd = ['mysqldump', '-u', _db.get_db_user()]
    if _db.get_db_password():
        mysqldump_cmd.extend(('-p{0}'.format(_db.get_db_password()), _db.get_db_name()))
    else:
        mysqldump_cmd.append(_db.get_db_name())
    mysqldump_cmd.append("| gzip ")
    mysqldump_cmd.append(">")
    mysqldump_cmd.append(db_backup_file)
    print(" ".join(mysqldump_cmd))
    os.system(" ".join(mysqldump_cmd))

def backup_config(folder):
    title(u"Backup of the configuration")
    now = time.strftime("%Y%m%d-%H%M")
    files = [{ 'src' : '/etc/domogik/',
               'dst' : 'domogik-etc-{0}.tgz'.format(now)},
             { 'src' : '/etc/default/domogik*',
               'dst' : 'domogik-default-{0}.tgz'.format(now)}]
    backup_some_files(files)

def backup_butler_file(folder):
    title(u"Backup of the butler generated files")
    now = time.strftime("%Y%m%d-%H%M")
    files = [{ 'src' : LEARN_FILE,
               'dst' : 'domogik-butler-learn-file-{0}.tgz'.format(now)},
             { 'src' : STAR_FILE,
               'dst' : 'domogik-butler-unknown_queries-file-{0}.tgz'.format(now)}]
    backup_some_files(files)

def backup_packages(folder):
    title(u"Backup of all the packages")
    now = time.strftime("%Y%m%d-%H%M")
    files = [{ 'src' : get_packages_dir(),
               'dst' : 'domogik-all-packages-{0}.tgz'.format(now)}]
    backup_some_files(files)


if __name__ == "__main__":
    folder = get_backup_dir()
    if folder != None:
        try:
            try:
                os.mkdir(folder, 0755)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise e
            backup_database(folder)
            backup_config(folder)
            backup_butler_file(folder)
            backup_packages(folder)
        except:
            print("Error while doing the backup : {0}".format(traceback.format_exc()))



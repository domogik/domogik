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


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from sqlalchemy import create_engine

from domogik.common import sql_schema
from domogik.common.configloader import Loader

cfg = Loader('database')
config = cfg.load()
try:
  db = dict(config[1])
  url = "%s:///" % db['db_type']
  if db['db_type'] == 'sqlite':
    url = "%s%s" % (url,db['db_path'])
  else:
    if db['db_port'] != '':
      url = "%s%s:%s@%s:%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_port'], db['db_name'])
    else:
      url = "%s%s:%s@%s/%s" % (url, db['db_user'], db['db_password'], db['db_host'], db['db_name'])
except:
  print "Some errors appears during connection to the database : Can't fetch informations from config file"

engine = create_engine(url)


###
# Installer
###
sql_schema.metadata.create_all(engine)

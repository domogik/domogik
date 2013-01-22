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

Miscellaneous utility database functions

Implements
==========


@author: Marc SCHNEIDER <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from sqlalchemy.engine import reflection

def index_exists(db_engine, table_name, index_name):
    """Check if an index exists in a table

    @param db_engine : engine bound to the database
    @param table_name : table name
    @param index_name : index name
    @return True or False

    """
    insp = reflection.Inspector.from_engine(db_engine)
    indexes = insp.get_indexes(table_name)
    index_found = False
    for index in indexes:
        if index['name'] == index_name:
            index_found = True
            break
    return index_found

def column_exists(db_engine, table_name, column_name):
    """Check if a column exists in a table

    @param db_engine : engine bound to the database
    @param table_name : table name
    @param column_name : column name
    @return True or False

    """
    insp = reflection.Inspector.from_engine(db_engine)
    columns = insp.get_columns(table_name)
    column_found = False
    for column in columns:
        if column['name'] == column_name:
            column_found = True
            break
    return column_found

def table_exists(db_engine, table_name):
    insp = reflection.Inspector.from_engine(db_engine)
    return table_name in insp.get_table_names()

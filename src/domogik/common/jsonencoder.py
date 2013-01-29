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
=============

- Handle python objects to json conversion

Implements
==========

- Domogik_encoder

Example how to use
==================

resp = {'a':'b'}
json.dumps(resp, cls=domogik_encoder(), check_circular=False)

json.dumps will return a json string


@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from sqlalchemy.ext.declarative import DeclarativeMeta
import json
import datetime

def domogik_encoder():
    """ wrapper function """
    _visited_objs = []
    class DomogikEncoder(json.JSONEncoder):
        """ The encoder extended class"""
        def default(self, obj):
            """ The encoder method """
            if isinstance(obj.__class__, DeclarativeMeta):
                # don't re-visit self
                if obj in _visited_objs:
                    return None
                _visited_objs.append(obj)
                # an SQLAlchemy class
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') \
                    and x != 'metadata' and x != 'get_tablename' \
                    and x != 'set_password']:
                    fields[field] = obj.__getattribute__(field)
                # a json-encodable dict
                return fields
            elif isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, datetime.date):
                return obj.isoformat()
            elif isinstance(obj, datetime.timedelta):
                return (datetime.datetime.min + obj).time().isoformat()
            # add other objects types here
            else:
                return json.JSONEncoder.default(self, obj)
    return DomogikEncoder

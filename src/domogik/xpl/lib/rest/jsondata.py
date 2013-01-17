from sqlalchemy.ext.declarative import DeclarativeMeta
import json

def domogik_encoder():
    _visited_objs = []
    class DomogikEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj.__class__, DeclarativeMeta):
                # don't re-visit self
                if obj in _visited_objs:
                    return None
                _visited_objs.append(obj)

                # an SQLAlchemy class
                fields = {}
                for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata' and x != 'get_tablename']:
                    fields[field] = obj.__getattribute__(field)
                # a json-encodable dict
                return fields
            # add other objects types here
            return json.JSONEncoder.default(self, obj)
    return DomogikEncoder

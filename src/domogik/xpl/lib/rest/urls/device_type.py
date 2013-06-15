from domogik.xpl.lib.rest.url import *
from flask import request
from flask.views import MethodView

class deviceTypeAPI(MethodView):
    decorators = [json_response]

    def get(self, type_id):
        if type_id != None:
            b = urlHandler.db.list_device_types(type_id)
        else:
            b = urlHandler.db.list_device_types()
        return 200, b

register_api(deviceTypeAPI, 'device_type_api', '/device_type/', pk='type_id')

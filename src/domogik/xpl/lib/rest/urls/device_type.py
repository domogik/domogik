from domogik.xpl.lib.rest.url import *
from flask import g as dbHelper, request
from flask.views import MethodView

class deviceTypeAPI(MethodView):
    decorators = [db_helper, json_response]

    def get(self, type_id):
        if type_id != None:
            b = dbHelper.db.list_device_types(type_id)
        else:
            b = dbHelper.db.list_device_types()
        return 200, b

    def delete(self, type_id):
        b = dbHelper.db.del_device_type(type_id)
        return 204, b

    def post(self):
        b = dbHelper.db.add_device_type(
            request.form.get('id'),
            request.form.get('name'),
            request.form.get('technology_id'),
            request.form.get('description'),
        )
        return 201, b

    def put(self, type_id):
        b = dbHelper.db.update_device_type(
            type_id,
            request.form.get('name'),
            request.form.get('technology_id'),
            request.form.get('description'),
        )
        return 200, b

register_api(deviceTypeAPI, 'device_type_api', '/device_type/', pk='type_id')

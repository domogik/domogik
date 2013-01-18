from domogik.xpl.lib.rest.url import *
from flask import g as dbHelper, request
from flask.views import MethodView

class deviceTechnologyAPI(MethodView):
    decorators = [db_helper, json_response]

    def get(self, techno_id):
        if techno_id != None:
            b = dbHelper.db.get_device_technology_by_id(techno_id)
        else:
            b = dbHelper.db.list_device_technologies()
        return 200, b

    def delete(self, techno_id):
        b = dbHelper.db.del_device_technology(techno_id)
        return 204, b

    def post(self):
        b = dbHelper.db.add_device_technology(
            request.form.get('name'),
            request.form.get('description'),
        )
        return 201, b

    def put(self, techno_id):
        b = dbHelper.db.update_device_technology(
            techno_id,
            request.form.get('name'),
            request.form.get('description'),
        )
        return 200, b

register_api(deviceTechnologyAPI, 'device_techno_api', '/device_technology/', pk='techno_id')

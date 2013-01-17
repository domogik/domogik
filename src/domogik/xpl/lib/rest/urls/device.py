from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper
from flask import g as dbHelper
from flask.views import MethodView

class deviceAPI(MethodView):
    @db_helper
    @json_response
    def get(self, device_id):
        b = dbHelper.db.get_device(device_id)
        return [b]

    @db_helper
    @json_response
    def delete(self, device_id):
        b = dbHelper.db.get_device(device_id)
        return [204, b]

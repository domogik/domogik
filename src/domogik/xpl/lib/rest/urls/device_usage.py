from domogik.xpl.lib.rest.url import *
from flask import g as dbHelper, request
from flask.views import MethodView

class deviceUsageAPI(MethodView):
    decorators = [db_helper, json_response]

    #@db_helper
    #@json_response
    def get(self, usage_id):
        if usage_id != None:
            b = dbHelper.db.get_device_usage_by_name(usage_id)
        else:
            b = dbHelper.db.list_device_usages()
        return 200, b

    #@db_helper
    #@json_response
    def delete(self, usage_id):
        b = dbHelper.db.del_device_usage(usage_id)
        return 204, b

    #@db_helper
    #@json_response
    def post(self):
        b = dbHelper.db.add_device_usage(
            request.form.get('id'),
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('default_options'),
        )
        print "POOOOOOOOOOOOOOOOOOOS"
        print b
        return 201, b

    def put(self, usage_id):
        b = dbHelper.db.update_device_usage(
            usage_id,
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('default_options'),
        )
        return 200, b


register_api(deviceUsageAPI, 'device_usage_api', '/device_usage/', pk='usage_id')

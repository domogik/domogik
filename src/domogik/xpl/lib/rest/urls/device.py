from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper, register_api
from flask import g as dbHelper
from flask.views import MethodView

@urlHandler.route('/device/old/', methods=['GET'])
@db_helper
@json_response
def device_list_old():
    b = dbHelper.db.list_old_devices()
    return 200, b

@urlHandler.route('/device/params/<dev_type_id>', methods=['GET'])
@db_helper
@json_response
def device_params(device_id):
   
    return b

@urlHandler.route('/device/addglobal/', methods=['PUT'])
@db_helper
@json_response
def device_globals(device_id):
   
    return b

@urlHandler.route('/device/xplcmdparams/', methods=['PUT'])
@db_helper
@json_response
def device_xplcmd_params(device_id):
   
    return b

@urlHandler.route('/device/xplstatparams/', methods=['PUT'])
@db_helper
@json_response
def device_xplstat_params(device_id):
   
    return b

class deviceAPI(MethodView):
    decorators = [db_helper, json_response]

    def get(self, did):
        if did != None:
            b = dbHelper.db.list_device_types(did)
        else:
            b = dbHelper.db.list_devices()
        return 200, b

    def delete(self, did):
        b = dbHelper.db.del_devic(did)
        return 204, b

    def post(self):
        b = dbHelper.db.add_device_and_commands(
            name=request.form.get('name'),
            type_id=request.form.get('type_id'),
            usage_id=request.form.get('usage_id'),
            description=request.form.get('description'),
            reference=request.form.get('reference'),
        )
        return 201, b

    def put(self, did):
        b = dbHelper.db.update_device(
            did,
            request.form.get('name'),
            request.form.get('type_id'),
            request.form.get('description'),
            request.form.get('reference'),
        )
        return 200, b

register_api(deviceAPI, 'device', '/device/', pk='did')

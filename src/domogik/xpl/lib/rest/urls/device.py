from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper
from flask import g as dbHelper

@urlHandler.route('/device/list-old/', methods=['GET'])
@db_helper
@json_response
def device_list_old(self, device_id):
    b = dbHelper.db.get_device_list_old()
    return b

@urlHandler.route('/device/params/<dev_type_id>', methods=['GET'])
@db_helper
@json_response
def device_params(self, device_id):
   
    return b

@urlHandler.route('/device/addglobal/', methods=['PUT'])
@db_helper
@json_response
def device_globals(self, device_id):
   
    return b

@urlHandler.route('/device/xplcmdparams/', methods=['PUT'])
@db_helper
@json_response
def device_xplcmd_params(self, device_id):
   
    return b

@urlHandler.route('/device/xplstatparams/', methods=['PUT'])
@db_helper
@json_response
def device_xplstat_params(self, device_id):
   
    return b






#
#deviceAPI
#/device/list => GET
#/device/add  => POST
#/device/update => PUT
#/device/ => delete

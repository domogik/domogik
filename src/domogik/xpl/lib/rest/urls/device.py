from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper, register_api, timeit
from flask import g as dbHelper
from flask.views import MethodView
from domogik.common.packagejson import PackageJson

@urlHandler.route('/device/old/', methods=['GET'])
@db_helper
@json_response
def device_list_old():
    b = dbHelper.db.list_old_devices()
    return 200, b

@urlHandler.route('/device/params/<dev_type_id>', methods=['GET'])
@db_helper
@json_response
def device_params(dev_type_id):
    print "ikke"
    try:
        dt = dbHelper.db.get_device_type_by_id(dev_type_id)
        if dt == None:
            return "This device type does not exists"
        # get the json
        pjson = PackageJson(dt.plugin_id).json
        if pjson['json_version'] < 2:
            return "This plugin does not support this command, json_version should at least be 2"
        ret = {}
        ret['commands'] = []
        ret['global'] = []
        if 'xpl_params' in pjson['device_types'][dt.id]:
            ret['global']  = pjson['device_types'][dt.id]['xpl_params']
        ret['xpl_stat'] = []
        ret['xpl_cmd'] = []
        # find all features for this device
        for c in pjson['device_types'][dt.id]['commands']:
            if not c in pjson['commands']:
                break
            cm = pjson['commands'][c]
            ret['commands'].append(c)
            # we must have an xpl command
            if not 'xpl_command' in cm:
                break
            # we have an xpl_command => find it
            if not cm['xpl_command'] in pjson['xpl_commands']:
                return "Command references an unexisting xpl_command"
            # find the xpl commands that are neede for this feature
            cmd = pjson['xpl_commands'][cm['xpl_command']].copy()
            cmd['id'] = c
            # finc the xpl_stat message
            cmd = pjson['xpl_commands'][cm['xpl_command']].copy()
            cmd['id'] = c
            # finc the xpl_stat message
            if not 'xplstat_name' in cmd:
                break
            if not cmd['xplstat_name'] in pjson['xpl_stats']:
                return "XPL command references an unexisting xpl_stat"
            stat = pjson['xpl_stats'][cmd['xplstat_name']].copy()
            stat['id'] = cmd['xplstat_name']
            # remove all parameters
            cmd['params'] = cmd['parameters']['device']
            del cmd['parameters']
            ret['xpl_cmd'].append(cmd)
            if stat is not None:
                # remove all parameters
                stat['params'] = stat['parameters']['device']
                del stat['parameters']
                ret['xpl_stat'].append(stat)
            del stat
            del cmd
        ret['global'] = [x for i,x in enumerate(ret['global']) if x not in ret['global'][i+1:]]
    except:
        return "Error in getting xplparams"
    # return the info
    return 200, ret

@urlHandler.route('/device/addglobal/<int:did>', methods=['PUT'])
@db_helper
@json_response
def device_globals(did):
    dev = dbHelper.db.get_device(id)
    js = device_params_get(dev.device_type_id, json=False)
    for x in dbHelper.db.get_xpl_command_by_device_id(id):
        for p in js['global']:
            dbHelper.db.add_xpl_command_param(cmd_id=x.id, key=p['key'], value=request.form.get(p['key']))
    for x in self._db.get_xpl_stat_by_device_id(id):
        for p in js['global']:
            dbHelper.db.add_xpl_stat_param(statid=x.id, key=p['key'], value=request.form.get(p['key']), static=True)
    return 204, ""

@urlHandler.route('/device/xplcmdparams/<int:did>', methods=['PUT'])
@db_helper
@json_response
def device_xplcmd_params(did):
    # get the command
    cmd = dbHelper.db.get_xpl_command(did)
    if cmd == None:
        # ERROR
        return
    # get the device
    dev = dbHelper.db.get_device(cmd.device_id)
    if dev == None:
        # ERROR
        return
    # get the device_type
    dt = dbHelper.db.get_device_type_by_id(dev.device_type_id)
    if dt == None:
        # ERROR
        return
    # get the json
    pjson = PackageJson(dt.device_technology_id).json
    if pjson['json_version'] < 2:
        # ERROR
        return
    # get the json device params for this command
    if pjson['xpl_commands'][cmd.name] is None:
        # ERROR
        return
    for p in pjson['xpl_commands'][cmd.name]['parameters']['device']:
        if request.form.get(p['key']) is None:
            # ERROR
            return
        # go and add the param
        dbHelper.db.add_xpl_command_param(cmd_id=cmd.id, key=p['key'], value=request.form.get(p['key']))
    return 204, ""

@urlHandler.route('/device/xplstatparams/<int:did>', methods=['PUT'])
@db_helper
@json_response
def device_xplstat_params(did):
    cmd = dbHelper.db.get_xpl_stat(device_id)
    if cmd == None:
        # ERROR
        return
    # get the device
    dev = dbHelper.db.get_device(cmd.device_id)
    if dev == None:
        # ERROR
        return
    # get the device_type
    dt = dbHelper.db.get_device_type_by_id(dev.device_type_id)
    if dt == None:
        # ERROR
        return
    # get the json
    pjson = PackageJson(dt.device_technology_id).json
    if pjson['json_version'] < 2:
        # ERROR
        return
    # get the json device params for this command
    if pjson['xpl_stats'][cmd.name] is None:
        # ERROR
        return
    for p in pjson['xpl_stats'][cmd.name]['parameters']['device']:
        if request.form.get(p['key']) is None:
            # ERROR
            return
        # go and add the param
        dbHelper.db.add_xpl_stat_param(cmd_id=cmd.id, key=p['key'], value=request.form.get(['key']))
    return 204, ""

class deviceAPI(MethodView):
    decorators = [db_helper, json_response]

    def get(self, did):
        if did != None:
            b = dbHelper.db.list_device_types(did)
            print b
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

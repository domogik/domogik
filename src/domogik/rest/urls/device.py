from domogik.xpl.common.plugin import DMG_VENDOR_ID
from domogik.rest.url import urlHandler, json_response, register_api, timeit
from flask.views import MethodView
from flask import request
import zmq
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage

@urlHandler.route('/device/old/', methods=['GET'])
@json_response
def device_list_old():
    b = urlHandler.db.list_old_devices()
    return 200, b

@urlHandler.route('/device/params/<dev_type_id>', methods=['GET'])
@json_response
def device_params(dev_type_id):
    try:
        result = get_device_params(dev_type_id)
    except Exception as e:
        return 500, "Error while getting device params: {0}".format(e)
    # return the info
    return 200, result

def get_device_params(dev_type_id):
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('device_types.get')
    msg.add_data('device_type', dev_type_id)
    res = cli.request('manager', msg.get(), timeout=10)
    if res is None:
        raise Exception("Bad device type (MQ)")
    pjson = res.get_data()
    if pjson is None:
        raise Exception("Bad device type (json)")
    pjson = pjson[dev_type_id]
    if pjson is None:
        raise Exception("Device type not found")
    # parse the data
    ret = {}
    ret['commands'] = []
    ret['global'] = []
    if 'parameters' in pjson['device_types'][dev_type_id]:
        ret['global']  = pjson['device_types'][dev_type_id]['parameters']
    ret['xpl_stat'] = []
    ret['xpl_cmd'] = []
    # find all features for this device
    for c in pjson['device_types'][dev_type_id]['commands']:
        if not c in pjson['commands']:
            break
        cm = pjson['commands'][c]
        ret['commands'].append(c)
        # we must have an xpl command
        if not 'xpl_command' in cm:
            break
        # we have an xpl_command => find it
        if not cm['xpl_command'] in pjson['xpl_commands']:
            raise "Command references an unexisting xpl_command"
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
            raise Exception("XPL command references an unexisting xpl_stat")
        stat = pjson['xpl_stats'][cmd['xplstat_name']].copy()
        stat['id'] = cmd['xplstat_name']
        # remove all parameters
        cmd['parameters'] = cmd['parameters']['device']
        del cmd['parameters']
        ret['xpl_cmd'].append(cmd)
        if stat is not None:
            # remove all parameters
            stat['parameters'] = stat['parameters']['device']
            del stat['parameters']
            ret['xpl_stat'].append(stat)
        del stat
        del cmd
    ret['global'] = [x for i,x in enumerate(ret['global']) if x not in ret['global'][i+1:]]
    return ret

@urlHandler.route('/device/addglobal/<int:did>', methods=['PUT'])
@json_response
def device_globals(did):
    #- if static field == 1 => this is a static param
    #- if static field == 0 and no sensor id is defined => this is a device param => value will be filled in
    #- if statis == 0 and it has a sensor id => its a dynamic param
    device = urlHandler.db.get_device(did)
    js = get_device_params(device['device_type_id'])
    for x in urlHandler.db.get_xpl_command_by_device_id(did):
        for p in js['global']:
            urlHandler.db.add_xpl_command_param(cmd_id=x.id, key=p['key'], value=request.form.get(p['key']))
    for x in urlHandler.db.get_xpl_stat_by_device_id(did):
        for p in js['global']:
            #urlHandler.db.add_xpl_stat_param(statid=x.id, key=p['key'], value=request.form.get(p['key']), static=True)
            urlHandler.db.add_xpl_stat_param(statid=x.id, key=p['key'], value=request.form.get(p['key']), static=False, type=p['type'])
    urlHandler.reload_stats()        
    return 200, "{}"

@urlHandler.route('/device/xplcmdparams/<int:did>', methods=['PUT'])
@json_response
def device_xplcmd_params(did):
    # get the command
    cmd = urlHandler.db.get_xpl_command(did)
    if cmd == None:
        # ERROR
        return
    # get the device
    dev = urlHandler.db.get_device(cmd.device_id)
    if dev == None:
        # ERROR
        return
    # get the device_type
    dt = urlHandler.db.get_device_type_by_id(dev.device_type_id)
    if dt == None:
        # ERROR
        return
    # get the json
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('device_types.get')
    msg.add_data('device_type', dev.device_type_id)
    res = cli.request('manager', msg.get(), timeout=10)
    if res is None:
        return "Bad device type"
    pjson = res.get_data()
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
        urlHandler.db.add_xpl_command_param(cmd_id=cmd.id, key=p['key'], value=request.form.get(p['key']))
    urlHandler.reload_stats()        
    return 204, ""

@urlHandler.route('/device/xplstatparams/<int:did>', methods=['PUT'])
@json_response
def device_xplstat_params(did):
    cmd = urlHandler.db.get_xpl_stat(device_id)
    if cmd == None:
        # ERROR
        return
    # get the device
    dev = urlHandler.db.get_device(cmd.device_id)
    if dev == None:
        # ERROR
        return
    # get the device_type
    dt = urlHandler.db.get_device_type_by_id(dev.device_type_id)
    if dt == None:
        # ERROR
        return
    # get the json
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('device_types.get')
    msg.add_data('device_type', dev.device_type_id)
    res = cli.request('manager', msg.get(), timeout=10)
    if res is None:
        return "Bad device type"
    pjson = res.get_data()
 
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
        urlHandler.db.add_xpl_stat_param(cmd_id=cmd.id, key=p['key'], value=request.form.get(['key']))
    urlHandler.reload_stats()        
    return 204, ""

class deviceAPI(MethodView):
    decorators = [json_response]

    def get(self, did):
        if did != None:
            b = urlHandler.db.get_device(did)
        else:
            b = urlHandler.db.list_devices()
        return 200, b

    def delete(self, did):
        b = urlHandler.db.del_device(did)
        urlHandler.reload_stats()        
        return 200, b

    def post(self):
        """ Create a new device
            Get all the clients details
            Finally, call the database function to create the device and give it the device types list and clients details : they will be used to fill the database as the json structure is recreated in the database
        """
        cli = MQSyncReq(urlHandler.zmq_context)

        #self.log.info("Device creation request for {0} {1} on {2} : name = '{3}', device_type = '{4}', reference = '{5}'".format(request.form.get('type'), request.form.get('id'), request.form.get('host'), request.form.get('device_type'), request.form.get('reference')))
        #urlHandler.log.info("Device creation request for {0} {1} on {2} : name = '{3}', device_type = '{4}', reference = '{5}'".format(request.form.get('type'), request.form.get('id'), request.form.get('host'), request.form.get('device_type'), request.form.get('reference')))

        # get the client details
        msg = MQMessage()
        msg.set_action('client.detail.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is None:
            return 500, "Error while getting the clients details"

        # create the full client id : 
        if request.form.get('type') == "plugin":
            client_id = "{0}-{1}.{2}".format(DMG_VENDOR_ID, request.form.get('id'), request.form.get('host'))
        else:
            client_id = "{0}-{1}.{2}".format(request.form.get('type'), request.form.get('id'), request.form.get('host'))

        # get the corresponding json
        all_clients_data = res.get_data()

        # extract the interesting part of the json (just the client part)
        if all_clients_data.has_key(client_id):
            client_data = all_clients_data[client_id]['data']
        else:
            return 500, "Error : there is no client id named '{0}'".format(client_id)

        # create the device in database
        # notice that we don't give any address for the device as this will be done with another url later
        created_device = urlHandler.db.add_device_and_commands(
            name=request.form.get('name'),
            device_type=request.form.get('device_type'),
            client_id=client_id,
            description=request.form.get('description'),
            reference=request.form.get('reference'),
            client_data=client_data
        )
        urlHandler.reload_stats()        
        return 201, created_device

    def put(self, did):
        b = urlHandler.db.update_device(
            did,
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('reference'),
        )
        urlHandler.reload_stats()        
        return 200, urlHandler.db.get_device(did)

register_api(deviceAPI, 'device', '/device/', pk='did', pk_type='int')

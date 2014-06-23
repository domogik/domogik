from domogik.xpl.common.plugin import DMG_VENDOR_ID
from domogik.rest.url import urlHandler, json_response, register_api, timeit
from flask.views import MethodView
from flask import request
import zmq
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage

@urlHandler.route('/instance/old/', methods=['GET'])
@json_response
@timeit
def instance_list_old():
    b = urlHandler.db.list_old_instances()
    return 200, b

@urlHandler.route('/instance/params/<dev_type_id>', methods=['GET'])
@json_response
@timeit
def instance_params(dev_type_id):
    try:
        result = get_instance_params(dev_type_id)
    except Exception as e:
        return 500, "Error while getting instance params: {0}".format(e)
    # return the info
    return 200, result

def get_instance_params(dev_type_id, zmq=None):
    if zmq:
        cli = MQSyncReq(zmq)
    else:
        cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('instance_types.get')
    msg.add_data('instance_type', dev_type_id)
    res = cli.request('manager', msg.get(), timeout=10)
    if res is None:
        raise Exception("Bad instance type (MQ)")
    pjson = res.get_data()
    if pjson is None:
        raise Exception("Bad instance type (json)")
    pjson = pjson[dev_type_id]
    if pjson is None:
        raise Exception("Instance type not found")
    # parse the data
    ret = {}
    ret['commands'] = []
    ret['global'] = []
    if 'parameters' in pjson['instance_types'][dev_type_id]:
        ret['global']  = pjson['instance_types'][dev_type_id]['parameters']
    ret['xpl_stat'] = []
    ret['xpl_cmd'] = []
    # find all features for this instance
    for c in pjson['instance_types'][dev_type_id]['commands']:
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
        cmd['parameters'] = cmd['parameters']['instance']
        del cmd['parameters']
        ret['xpl_cmd'].append(cmd)
        if stat is not None:
            # remove all parameters
            stat['parameters'] = stat['parameters']['instance']
            del stat['parameters']
            ret['xpl_stat'].append(stat)
        del stat
        del cmd
    ret['global'] = [x for i,x in enumerate(ret['global']) if x not in ret['global'][i+1:]]
    return ret

@urlHandler.route('/instance/addglobal/<int:did>', methods=['PUT'])
@json_response
@timeit
def instance_globals(did):
    #- if static field == 1 => this is a static param
    #- if static field == 0 and no sensor id is defined => this is a instance param => value will be filled in
    #- if statis == 0 and it has a sensor id => its a dynamic param
    instance = urlHandler.db.get_instance(did)
    js = get_instance_params(instance['instance_type_id'])
    for x in urlHandler.db.get_xpl_command_by_instance_id(did):
        for p in js['global']:
            if p["xpl"] is True:
                urlHandler.db.add_xpl_command_param(cmd_id=x.id, key=p['key'], value=request.form.get(p['key']))
    for x in urlHandler.db.get_xpl_stat_by_instance_id(did):
        for p in js['global']:
            if p["xpl"] is True:
                #urlHandler.db.add_xpl_stat_param(statid=x.id, key=p['key'], value=request.form.get(p['key']), static=True)
                urlHandler.db.add_xpl_stat_param(statid=x.id, key=p['key'], value=request.form.get(p['key']), static=True, type=p['type'])
    for p in js['global']:
        if p["xpl"] is not True:
            urlHandler.db.add_instance_param(did, p["key"], request.form.get(p['key']), p["type"])
    urlHandler.reload_stats()
    return 200, "{}"

@urlHandler.route('/instance/xplcmdparams/<int:did>', methods=['PUT'])
@json_response
@timeit
def instance_xplcmd_params(did):
    # get the command
    cmd = urlHandler.db.get_xpl_command(did)
    if cmd == None:
        # ERROR
        return
    # get the instance
    dev = urlHandler.db.get_instance(cmd.instance_id)
    if dev == None:
        # ERROR
        return
    # get the instance_type
    dt = urlHandler.db.get_instance_type_by_id(dev.instance_type_id)
    if dt == None:
        # ERROR
        return
    # get the json
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('instance_types.get')
    msg.add_data('instance_type', dev.instance_type_id)
    res = cli.request('manager', msg.get(), timeout=10)
    if res is None:
        return "Bad instance type"
    pjson = res.get_data()
    if pjson['json_version'] < 2:
        # ERROR
        return
    # get the json instance params for this command
    if pjson['xpl_commands'][cmd.name] is None:
        # ERROR
        return
    for p in pjson['xpl_commands'][cmd.name]['parameters']['instance']:
        if request.form.get(p['key']) is None:
            # ERROR
            return
        # go and add the param
        urlHandler.db.add_xpl_command_param(cmd_id=cmd.id, key=p['key'], value=request.form.get(p['key']))
    urlHandler.reload_stats()        
    return 204, ""

@urlHandler.route('/instance/xplstatparams/<int:did>', methods=['PUT'])
@json_response
@timeit
def instance_xplstat_params(did):
    cmd = urlHandler.db.get_xpl_stat(instance_id)
    if cmd == None:
        # ERROR
        return
    # get the instance
    dev = urlHandler.db.get_instance(cmd.instance_id)
    if dev == None:
        # ERROR
        return
    # get the instance_type
    dt = urlHandler.db.get_instance_type_by_id(dev.instance_type_id)
    if dt == None:
        # ERROR
        return
    # get the json
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('instance_types.get')
    msg.add_data('instance_type', dev.instance_type_id)
    res = cli.request('manager', msg.get(), timeout=10)
    if res is None:
        return "Bad instance type"
    pjson = res.get_data()
 
    if pjson['json_version'] < 2:
        # ERROR
        return
    # get the json instance params for this command
    if pjson['xpl_stats'][cmd.name] is None:
        # ERROR
        return
    for p in pjson['xpl_stats'][cmd.name]['parameters']['instance']:
        if request.form.get(p['key']) is None:
            # ERROR
            return
        # go and add the param
        urlHandler.db.add_xpl_stat_param(cmd_id=cmd.id, key=p['key'], value=request.form.get(['key']))
    urlHandler.reload_stats()        
    return 204, ""

class instanceAPI(MethodView):
    decorators = [json_response, timeit]

    def get(self, did):
        if did != None:
            b = urlHandler.db.get_instance(did)
        else:
            b = urlHandler.db.list_instances()
        if b == None:
            return 404, b
        else:
            return 200, b

    def delete(self, did):
        b = urlHandler.db.del_instance(did)
        urlHandler.reload_stats()        
        return 200, b

    def post(self):
        """ Create a new instance
            Get all the clients details
            Finally, call the database function to create the instance and give it the instance types list and clients details : they will be used to fill the database as the json structure is recreated in the database
        """
        cli = MQSyncReq(urlHandler.zmq_context)

        #self.log.info(u"Instance creation request for {0} {1} on {2} : name = '{3}', instance_type = '{4}', reference = '{5}'".format(request.form.get('type'), request.form.get('id'), request.form.get('host'), request.form.get('instance_type'), request.form.get('reference')))
        #urlHandler.log.info("Instance creation request for {0} {1} on {2} : name = '{3}', instance_type = '{4}', reference = '{5}'".format(request.form.get('type'), request.form.get('id'), request.form.get('host'), request.form.get('instance_type'), request.form.get('reference')))

        # get the client details
        msg = MQMessage()
        msg.set_action('client.detail.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is None:
            return 500, "Error while getting the clients details"

        # create the full client id : 
        #if request.form.get('type') == "plugin":
        #    client_id = "{0}-{1}.{2}".format(DMG_VENDOR_ID, request.form.get('id'), request.form.get('host'))
        #else:
        #    client_id = "{0}-{1}.{2}".format(request.form.get('type'), request.form.get('id'), request.form.get('host'))

        # get the corresponding json
        all_clients_data = res.get_data()

        # extract the interesting part of the json (just the client part)
        if all_clients_data.has_key(request.form.get('client_id')):
            client_data = all_clients_data[request.form.get('client_id')]['data']
        else:
            return 500, "Error : there is no client id named '{0}'".format(request.form.get('client_id'))

        # create the instance in database
        # notice that we don't give any address for the instance as this will be done with another url later
        created_instance = urlHandler.db.add_instance_and_commands(
            name=request.form.get('name'),
            instance_type=request.form.get('instance_type'),
            client_id=request.form.get('client_id'),
            description=request.form.get('description'),
            reference=request.form.get('reference'),
            client_data=client_data
        )
        urlHandler.reload_stats()        
        return 201, created_instance

    def put(self, did):
        b = urlHandler.db.update_instance(
            did,
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('reference'),
        )
        urlHandler.reload_stats()        
        return 200, urlHandler.db.get_instance(did)

register_api(instanceAPI, 'instance', '/instance/', pk='did', pk_type='int')

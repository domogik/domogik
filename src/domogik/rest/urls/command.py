from domogik.rest.url import urlHandler, json_response, timeit
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import Loader
import sys
import os
import domogik
import json
from subprocess import Popen, PIPE
from flask import Response, request
from domogik.common.utils import call_package_conversion
from domogikmq.pubsub.subscriber import MQSyncSub
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

@urlHandler.route('/cmd/id/<int:cid>', methods=['GET'])
@json_response
@timeit
def api_ncommand(cid):
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('cmd.send')
    msg.add_data('cmdid', cid)
    # build the commandparams
    cmdparams = {}
    for param in request.args:
        cmdparams[param] = request.args.get(param)
    msg.add_data('cmdparams', cmdparams)
    # do the request
    resp = cli.request('xplgw', msg.get(), timeout=10)
    if resp:
        response = resp.get_data()
        if response['status']:
            return 204, None
        else:
            return 400, {'msg': response['reason']}
    else:
        return 400, {'msg': "XPL gateway does not respond"}

from domogik.admin.application import app, json_response, timeit
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import Loader
import sys
import os
import domogik
import json
from subprocess import Popen, PIPE
from flask import Response, request
from domogik.common.utils import call_package_conversion
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required

@app.route('/rest/cmd/id/<int:cid>', methods=['GET'])
@json_response
@login_required
@timeit
def api_ncommand(cid):
    """
    @api {get} /rest/cmd/id/<int:cid> Trigger a command
    @apiName getCommand
    @apiGroup Command
    @apiVersion 0.4.1

    @apiParam {Number} id The commandId to generate
    @apiParam Key A key value pair for each command param

    @apiSuccessExample Success-Response:
        HTTTP/1.1 204 No Content 

    @apiErrorExample Gateway Timeout
        HTTTP/1.1 500
        {
            'error': 'XPL gateway does not respond'
        }
    
    @apiErrorExample Error
        HTTTP/1.1 500
        {
            'error': '...'
        }
    """
    cli = MQSyncReq(app.zmq_context)
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
            app.logger.error(u"Error : {0}".format(response['reason']))
            return 500, {'error': response['reason']}
    else:
        app.logger.error(u"XPL gateway does not respond")
        return 500, {'error': "XPL gateway does not respond"}

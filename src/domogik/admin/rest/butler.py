from domogik.admin.application import app, json_response, jsonp_response
import sys
import os
import domogik
import json
from subprocess import Popen, PIPE
from flask import Response, request
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
import traceback
from flask_login import login_required



@app.route('/rest/butler/discuss', methods=['GET'])
@jsonp_response
@login_required
def api_butler_discuss_get():
    """
    @api {get} /butler/discuss Discuss with the butler
    @apiName postButlerDiscuss
    @apiGroup Butler
    @apiVersion 0.5.0

    @apiParam data The json data for the butler
    @apiParam callback The callback name (automatically added by jquery)

    @apiExample Example usage with wget
        If authentication is activated, you will need to also use these options : --auth-no-challenge --http-user=admin --http-password=123 
        $ wget -qO- 'http://192.168.1.10:40406/rest/butler/discuss?callback=foo&data={"text" : "hello", "source" : "a_script"}' --header="Content-type: application/json"
        foo({
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        })

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        foo({
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        })

    @apiErrorExample Butler does not respond in time
        HTTTP/1.1 400 Bad Request
        foo({
            msg: "butler does not respond"
        })
    
    @apiErrorExample Other error
        HTTTP/1.1 400 Bad Request
        foo({
            msg: "error while parsing butler response : ...'
        })
    """
    try:
        json_data = json.loads(request.args['data'])
        if 'callback' in request.args:
            callback = request.args['callback']
        else:
            callback = "callback_not_defined"
    except:
        app.logger.error(u"Error while decoding received json data. Error is : {0}".format(traceback.format_exc()))
        return 400, {'msg': u"Error while decoding received json data. Error is : {0}".format(traceback.format_exc())}, "None"

    cli = MQSyncReq(app.zmq_context)

    msg = MQMessage()
    msg.set_action('butler.discuss.do')
    msg.set_data(json_data)

    # do the request
    # we allow a long timeout because the butler can take some time to respond...
    # some functions are quite long (requests to external webservices, ...)
    resp = cli.request('butler', msg.get(), timeout=60)
    if resp:
        try:
            response = resp.get_data()
            return 200, response, callback
        except:
            app.logger.error(u"Error while parsing butler response : {0}".format(resp))
            return 400, {'msg': u"Error while parsing butler response : {0}".format(resp) }, callback
    else:
        app.logger.error(u"The butler does not respond")
        return 400, {'msg': "The butler does not respond"}, callback




@app.route('/rest/butler/discuss', methods=['POST'])
@json_response
@login_required
def api_butler_discuss_post():
    """
    @api {post} /butler/discuss Discuss with the butler
    @apiName postButlerDiscuss
    @apiGroup Butler
    @apiVersion 0.5.0


    @apiExample Example usage with wget
        If authentication is activated, you will need to also use these options : --auth-no-challenge --http-user=admin --http-password=123 
        $ wget -qO- http://192.168.1.10:40406/rest/butler/discuss --post-data='{"text" : "hello", "source" : "a_script"}' --header="Content-type: application/json"
        {
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        }

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        {
            "identity": "Aria", 
            "location": null, 
            "media": null, 
            "mood": null, 
            "reply_to": "a_script", 
            "sex": "female", 
            "text": "hi"
        }

    @apiErrorExample Butler does not respond in time
        HTTTP/1.1 400 Bad Request
        {
            msg: "butler does not respond"
        }
    
    @apiErrorExample Other error
        HTTTP/1.1 400 Bad Request
        {
            msg: "error while parsing butler response : ...'
        }
    """
    try:
        json_data = json.loads(request.data)
    except:
        app.logger.error(u"Error while decoding received json data. Error is : {0}".format(traceback.format_exc()))
        return 400, {'msg': u"Error while decoding received json data. Error is : {0}".format(traceback.format_exc())}

    cli = MQSyncReq(app.zmq_context)

    msg = MQMessage()
    msg.set_action('butler.discuss.do')
    msg.set_data(json_data)

    # do the request
    # we allow a long timeout because the butler can take some time to respond...
    # some functions are quite long (requests to external webservices, ...)
    resp = cli.request('butler', msg.get(), timeout=60)
    if resp:
        try:
            response = resp.get_data()
            return 200, response
        except:
            app.logger.error(u"Error while parsing butler response : {0}".format(resp))
            return 400, {'msg': u"Error while parsing butler response : {0}".format(resp) }
    else:
        app.logger.error(u"The butler does not respond")
        return 400, {'msg': "The butler does not respond"}

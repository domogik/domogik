from domogik.admin.application import app, json_response, timeit
from domogik.common.configloader import Loader
from domogik.common.utils import get_sanitized_hostname
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response
from flask_login import login_required

@app.route('/rest/')
@json_response
def api_root():
    """
    @api {get} /rest/ Get the status of the REST server
    @apiName getStatus
    @apiGroup Status
    @apiVersion 0.4.1

    @apiSuccess {json} result A json result with the status

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "info": {
                "REST_API_version": "0.7",
                "SSL": false,
                "Host": "igor",
                "Domogik_release": "0.4.0",
                "Domogik_version": "0.4.0",
                "REST_API_release": "0.7",
                "Sources_release": "0.4.0",
                "Sources_version": "0.4.0"
            },
            "mq": {
                "sub_port": "40412",
                "ip": "127.0.0.1",
                "req_rep_port": "40410",
                "pub_port": "40411"
            }
        }
    """
    try:
        # domogik global version
        global_version = sys.modules["domogik"].__version__
        rest_version = sys.modules["domogik"].__rest_api_version__
        src_version = global_version
    
        info = {}
        info["REST_API_version"] = rest_version
        info["Domogik_version"] = global_version
        info["Sources_version"] = src_version
        info["SSL"] = app.dbConfig['use_ssl']
        info["Host"] = get_sanitized_hostname()
    
        # for compatibility with Rest API < 0.6
        info["REST_API_release"] = rest_version
        info["Domogik_release"] = global_version
        info["Sources_release"] = src_version
    
        # mq part
        mqconfig = Loader('mq', 'domogik-mq.cfg')
        config = dict(mqconfig.load()[1])
        mq = {}
        mq["sub_port"] = config["sub_port"]
        mq["ip"] = config["ip"]
        mq["req_rep_port"] = config["req_rep_port"]
        mq["pub_port"] = config["pub_port"]
    
        data = {"info" : info, "mq": mq}
        return 200, data
    except:
        msg = u"Error while getting the status. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

@app.route('/rest/map')
@json_response
@timeit
def api_map():
    try:
        rules = []
        for rule in app.url_map.iter_rules():
            rules.append({\
                'url': rule.rule, \
                'method': list(rule.methods), \
                'arguments': list(rule.arguments), \
            })
        return 200, rules
    except:
        msg = u"Error while getting the api map. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

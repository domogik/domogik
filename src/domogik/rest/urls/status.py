from domogik.rest.url import urlHandler, json_response, timeit
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response

@urlHandler.route('/')
@json_response
@timeit
def api_root():
    """
    @api {get} / Get the status of the REST server
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
    # domogik global version
    global_version = sys.modules["domogik"].__version__
    # domogik src version
    domogik_path = os.path.dirname(domogik.rest.__file__)
    subp = Popen("cd %s ; hg branch | xargs hg log -l1 --template '{branch}.{rev} - {date|isodate}' -b" % domogik_path, shell=True, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = subp.communicate()
    # if hg id has no error, we are using source  repository
    if subp.returncode == 0:
        src_version= "%s" % (stdout)
    # else, we send dmg version
    else:
        src_version = global_version

    info = {}
    info["REST_API_version"] = urlHandler.apiversion
    info["SSL"] = urlHandler.use_ssl
    info["Domogik_version"] = global_version
    info["Sources_version"] = src_version
    info["Host"] = urlHandler.hostname

    # for compatibility with Rest API < 0.6
    info["REST_API_release"] = urlHandler.apiversion
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

@urlHandler.route('/map')
@json_response
@timeit
def api_map():
    rules = []
    for rule in urlHandler.url_map.iter_rules():
        rules.append({\
            'url': rule.rule, \
            'method': list(rule.methods), \
            'arguments': list(rule.arguments), \
        })
    return 200, rules

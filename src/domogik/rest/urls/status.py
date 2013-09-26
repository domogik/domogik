from domogik.rest.url import urlHandler, json_response, db_helper, timeit
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
    print "@@@@@ /"
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

    # Configuration
    cfg = Loader('mq').load()
    mqcfg = dict(cfg[1])

    data = {"info" : info, 
           "mq": mqcfg}
    return 200, data

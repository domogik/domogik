from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper, timeit
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response

@urlHandler.route('/cmd')
@json_response
@timeit
def api_command():
    data = {"info" : info, 
           "configuration" : conf,
           "mq": mqcfg}
    return 200, data

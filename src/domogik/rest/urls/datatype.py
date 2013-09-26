from domogik.rest.url import urlHandler, json_response, db_helper, timeit
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response
import json

@urlHandler.route('/datatype')
@json_response
@timeit
def api_datatype():
    """ return the datatypes json file
    """
    cfg = Loader('domogik')
    config = cfg.load()
    conf = dict(config[1])
    json_file = "{0}/datatypes.json".format(urlHandler.resources_directory)
    data = json.load(open(json_file))

    return 200, data

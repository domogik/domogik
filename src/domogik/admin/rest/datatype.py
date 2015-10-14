from domogik.admin.application import app, json_response, timeit
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response
import json

@app.route('/rest/datatype')
@json_response
@timeit
def api_datatype():
    """
    @api {get} /rest/datatype Retrieve all datatypes
    @apiName getDataTypes
    @apiGroup DataType

    @apiSuccess {json} result The json representation of the datatypes

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "DT_HVACVent": {
                "childs": [],
                "values": {
                    "0": "Auto",
                    "1": "Heat",
                    "2": "Cool",
                    "3": "Fan only",
                    "4": "Dry"
                }
            },
            "DT_DateTime": {
                "childs": [
                    "DT_Date",
                    "DT_Time"
                ],
                "format": "YYYY-MM-DDThh:mm:ss.s"
            },
            "DT_String": {
                "childs": [
                    "DT_Phone",
                    "DT_Hexa",
                    "DT_ColorRGBHexa"
                ],
                "maxLengh": null,
                "format": null
            },
            ...
        }
    """
    cfg = Loader('domogik')
    config = cfg.load()
    conf = dict(config[1])
    json_file = "{0}/datatypes.json".format(urlHandler.resources_directory)
    data = json.load(open(json_file))

    return 200, data

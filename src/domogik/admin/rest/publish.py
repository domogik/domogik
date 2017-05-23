from domogik.admin.application import app, json_response
import sys
import os
import domogik
import json
from flask import Response, request, send_from_directory
import traceback
from flask_login import login_required

@app.route('/rest/publish/<client_type>/<client_name>/<path>', methods=['GET'])
# TODO : security issue !!!!!
# TODO : security issue !!!!!
# TODO : security issue !!!!!
# TODO : security issue !!!!!
# Why the fuck the login_required is not working here ?????????
#@login_required
def publish_get(client_type, client_name, path):
    """
    @api {get} /butler/publish View content published by some clients
    @apiName getPublish
    @apiGroup Publish
    @apiVersion 0.5.0

    @apiParam client_type The client type (plugin, ...)
    @apiParam client_name The client name (yi, ...)

    @apiExample Example usage with wget
        $ wget -qO- http://192.168.1.10:40406/rest/publish/plugin/ftpcamera/motion_20160907_1154.jpg"

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 
        ... some content ....

    @apiErrorExample No so published data
        HTTTP/1.1 404 Not foundst
    
    """
    try:
        data = "{0}, {1}, {2}".format(client_type, client_name, path)
        # basic security
        path = path.replace("..", "")
        root = app.publish_directory
        root_client = os.path.join(root, "{0}/{1}".format(client_type, client_name))
        return send_from_directory(directory = root_client, filename = path)
    except:
        msg = u"Error while getting the published data. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 404, msg

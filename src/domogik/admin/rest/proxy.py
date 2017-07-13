# -*- coding: utf-8 -*-

from domogik.admin.application import app, json_response, jsonp_response
import sys
import os
from flask import request, abort, Response
from flask import stream_with_context
import traceback
from flask_login import login_required
import requests



@app.route('/rest/proxy/<path:url>', methods=['GET'])
@login_required
def api_proxy(url):
    req = requests.get(url, stream = True)
    return Response(stream_with_context(req.iter_content()), content_type = req.headers['content-type'])


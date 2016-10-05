from domogik.admin.application import app, render_template
from domogikmq.configloader import Loader
from domogik.common.utils import get_ip_for_interfaces
from flask import request
from flask_login import login_required

@app.route('/')
@login_required
def index():
    mqConfig = Loader('mq').load()[0]

    qrCode = dict()
    qrCode["admin_url"] = request.url
    qrCode["rest_port"] = app.port
    qrCode["rest_path"] = "/rest/"
    qrCode["rest_auth"] = app.rest_auth
    qrCode["mq_ip"] = mqConfig['ip']
    qrCode["mq_port_pubsub"] = mqConfig['sub_port']
    qrCode["mq_port_req_rep"] = mqConfig['req_rep_port']
    return render_template('index.html',
            qrdata=qrCode)

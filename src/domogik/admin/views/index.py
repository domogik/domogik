from domogik.admin.application import app, render_template
from domogikmq.configloader import Loader as mqLoader
from domogik.common.configloader import Loader as dmgLoader
from domogik.common.utils import get_ip_for_interfaces, ucode
from flask import request, flash, redirect
from flask_login import login_required
try:
    from flask.ext.babel import gettext, ngettext
except ImportError:
    from flask_babel import gettext, ngettext
    pass

@app.route('/')
@login_required
def index():
    mqConfig = mqLoader('mq').load()[0]
    butlerConfig = dict(dmgLoader('butler').load()[1])
    #qrCode = dict()
    with app.db.session_scope():
        qrCode = app.db.get_core_config()
    qrCode["admin_url"] = str(request.url)
    qrCode["rest_port"] = int(app.port)
    qrCode["rest_path"] = "/rest"
    qrCode["rest_auth"] = bool(app.rest_auth)
    qrCode["mq_ip"] = str(mqConfig['ip'])
    qrCode["mq_port_sub"] = int( mqConfig['sub_port'])
    qrCode["mq_port_pub"] = int( mqConfig['pub_port'])
    qrCode["mq_port_req_rep"] = int(mqConfig['req_rep_port'])
    qrCode["butler_name"] = ucode(butlerConfig['name'])
    qrCode["butler_sex"] = str(butlerConfig['sex'])
    qrCode["butler_lang"] = str(butlerConfig['lang'])
    return render_template('index.html',
            qrdata=qrCode)

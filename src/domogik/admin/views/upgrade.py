from domogik.admin.application import app, render_template
from flask import request, flash, redirect
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required
from flask.ext.babel import gettext, ngettext

@app.route('/upgrade')
@login_required
def upgrade():
    with app.db.session_scope():
        devs = app.db.list_devices(d_state=u'upgrade')
    
    return render_template('upgrade.html',
        mactive="upgrade",
        devices=devs
        )

@app.route('/upgrade/<int:devid>')
@login_required
def upgrade_dev(devid):
    return render_template('upgrade_input.html',
        mactive="upgrade"
        )

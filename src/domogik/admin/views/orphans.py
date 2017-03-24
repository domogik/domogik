from flask import request, flash, redirect
from flask_login import login_required
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass
from domogik.admin.application import app, render_template
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

@app.route('/orphans')
@login_required
def orphans():
    # get all clients
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('client.list.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        client_list = res.get_data()
    else:
        client_list = {}
    # get all devices
    with app.db.session_scope():
        devs = app.db.list_devices()
    # loop over the devices
    orphan_devs = []
    for dev in devs:
        if dev["client_id"] not in list(client_list.keys()) and dev['client_id'] != 'core':
            orphan_devs.append(dev)

    return render_template('orphans.html',
        mactive="orphans",
        devices=orphan_devs
        )

@app.route('/orphans/delete/<did>')
@login_required
def orphans_delete(did):
    with app.db.session_scope():
        res = app.db.del_device(did)
        if not res:
            flash(gettext("Device deleted failed"), 'warning')
        else:
            flash(gettext("Device deleted succesfully"), 'success')
        return redirect("/orphans")

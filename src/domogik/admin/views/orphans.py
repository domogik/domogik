from __future__ import absolute_import, division, print_function, unicode_literals
from domogik.admin.application import app, render_template
from flask import request, flash, redirect
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required
from flask.ext.babel import gettext, ngettext

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
        if dev["client_id"] not in list(client_list.keys()):
            orphan_devs.append(dev)

    return render_template('orphans.html',
        mactive="orphans",
        devices=orphan_devs
        )

@app.route('/orphans/delete/<did>')
@login_required
def orphans_delete(did):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('device.delete')
    msg.set_data({'did': did})
    res = cli.request('dbmgr', msg.get(), timeout=10)
    if res is not None:
        data = res.get_data()
        if data["status"]:
            flash(gettext("Device deleted succesfully"), 'success')
        else:
            flash(gettext("Device deleted failed"), 'warning')
            flash(data["reason"], 'danger')
    else:
        flash(gettext("DbMgr did not respond on the device.delete, check the logs"), 'danger')
    return redirect("/orphans")

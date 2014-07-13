from domogik.admin.application import app
from flask import render_template, request, flash, redirect
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
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
        mactve="orphans",
        devices=orphan_devs
        )

@app.route('/orphans/delete/<did>')
@login_required
def orphans_delete(did):
    with app.db.session_scope():
        app.db.del_device(did)
    # reload stats
    req = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action( 'reload' )
    resp = req.request('xplgw', msg.get(), 100)
    flash(gettext("Device deleted"), "success")
    return redirect("/orphans")

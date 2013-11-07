from domogik.admin.application import app
from flask import render_template
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage

@app.route('/clients')
def clients():
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('client.list.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        client_list = res.get_data()
    else:
        client_list = {}

    return render_template('clients.html',
        clients=client_list
        )

@app.route('/client/<client_id>')
def client_detail(client_id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('client.detail.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        detaila = res.get_data()
        detail = detaila[client_id]
    else:
        detail = {}

    return render_template('client.html',
            clientid = client_id,
            detail = detail,
            active = 'home'
            )

@app.route('/client/<client_id>/devices/known')
def client_devices_known(client_id):
    with app.db.session_scope():
        devices = app.db.list_devices_by_plugin(client_id)
    return render_template('client_devices.html',
            devices = devices,
            clientid = client_id,
            active = 'devices'
            )

@app.route('/client/<client_id>/devices/detected')
def client_devices_detected(client_id):
    # TODO get them
    devices = {}
    return render_template('client_detected.html',
            devices = devices,
            clientid = client_id,
            active = 'devices'
            )

@app.route('/client/<client_id>/config')
def client_config(client_id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('client.detail.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        detaila = res.get_data()
        config = detaila[client_id]['data']['configuration']
    else:
        config = {}

    return render_template('client_config.html',
            config = config,
            clientid = client_id,
            active = 'config'
            )



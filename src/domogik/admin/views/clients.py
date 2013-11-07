from domogik.admin.application import app
from flask import render_template, request, flash
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from flask_wtf import Form
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import Required

from domogik.rest.urls.device import get_device_params

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

@app.route('/client/<client_id>/config', methods=['GET', 'POST'])
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
    known_items = []

    # dynamically generate the wtfform
    class F(Form):
        submit = SubmitField("Send")
        pass
    for item in config:
        # keep track of the known fields
        known_items.append(item["key"])
        # handle required
        if item["required"] == "yes":
            arguments = [Required()]
        else:
            arguments = []
        # fill in the field
        if 'value' in item:
            default = item["value"]
        else:
            default = item["default"]
        # build the field
        if item["type"] == "boolean":
            field = BooleanField(item["name"], arguments, description=item["description"], default=default)
        elif item["type"] == "number":
            field = IntegerField(item["name"], arguments, description=item["description"], default=default)
        elif item["type"] == "enum":
            choices = []
            for choice in item["choices"]:
                choices.append((choice, choice))
            field = SelectField(item["name"], arguments, description=item["description"], choices=choices, default=default)
        else:
            field = TextField(item["name"], arguments, description=item["description"], default=default)
        # add the field
        setattr(F, item["key"], field)
    # add the submit button
    field = submit = SubmitField("Send")
    setattr(F, "submit", field)

    form = F()

    if request.method == 'POST' and form.validate():
        # build the requested config set
        data = {}
        for arg, value in request.form.items():
            if arg in known_items:
                data[arg] = value
        # build the message
        msg = MQMessage()
        msg.set_action('config.set')
        tmp = client_id.split('-')
        msg.add_data('type', tmp[0])
        tmp = tmp[1].split('.')
        msg.add_data('host', tmp[1])
        msg.add_data('name', tmp[0])
        msg.add_data('data', data)
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            data = res.get_data()
            if data["status"]:
                flash('Config save successfull', 'success')
            else:
                flash('Config save failed', 'warning')
                flash(data["reason"], 'danger')
        else:
            flash('DbMgr did not respond on the config.set, check the logs', 'danger')

    return render_template('client_config.html',
            form = form,
            clientid = client_id,
            active = 'config'
            )

@app.route('/client/<client_id>/devices/new')
def client_devices_new(client_id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('client.detail.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        detaila = res.get_data()
        data = detaila[client_id]['data']
    else:
        data = {}

    dtypes = data["device_types"].keys()
    products = {}
    for prod in data["products"]:
        products[prod["name"]] = prod["type"]
 
    return render_template('client_device_new.html',
            device_types = dtypes,
            products = products,
            clientid = client_id,
            active = 'devices'
            )

@app.route('/client/<client_id>/devices/new/<device_type_id>')
def client_devices_new_wiz(client_id, device_type_id):
    # TODO get them
    params = get_device_params(device_type_id, app.zmq_context)

    # dynamically generate the wtfform
    class F(Form):
        submit = SubmitField("Send")
        pass

    #for item in config:
        # keep track of the known fields
    #    known_items.append(item["key"])
        # handle required
    #    if item["required"] == "yes":
    #        arguments = [Required()]
    #    else:
    #        arguments = []
        # fill in the field
    #    if 'value' in item:
    #        default = item["value"]
    #    else:
    #        default = item["default"]
        # build the field
    #    if item["type"] == "boolean":
    #        field = BooleanField(item["name"], arguments, description=item["description"], default=default)
    #    elif item["type"] == "number":
    #        field = IntegerField(item["name"], arguments, description=item["description"], default=default)
    #    elif item["type"] == "enum":
    #        choices = []
    #        for choice in item["choices"]:
    #            choices.append((choice, choice))
    #        field = SelectField(item["name"], arguments, description=item["description"], choices=choices, default=default)
    #    else:
    #        field = TextField(item["name"], arguments, description=item["description"], default=default)
    #    # add the field
    #    setattr(F, item["key"], field)
    # add the submit button
    field = submit = SubmitField("Send")
    setattr(F, "submit", field)

    form = F()


    return render_template('client_device_new_wiz.html',
            form = form,
            params = params,
            dtype = device_type_id,
            clientid = client_id,
            active = 'devices'
            )

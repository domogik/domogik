from domogik.admin.application import app
from flask import render_template, request, flash, redirect
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from flaskext.wtf import Form
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import Required
from flask_login import login_required
from flask_babel import gettext, ngettext

from domogik.rest.urls.device import get_device_params
from domogik.common.sql_schema import Device, Sensor
from wtforms.ext.sqlalchemy.orm import model_form

@app.route('/clients')
@login_required
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
        mactve="clients",
	overview_state="collapse",
        clients=client_list
        )

@app.route('/client/<client_id>')
@login_required
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
            loop = {'index': 1},
            clientid = client_id,
            data = detail,
            mactve="clients",
            active = 'home'
            )

@app.route('/client/<client_id>/devices/known')
@login_required
def client_devices_known(client_id):
    with app.db.session_scope():
        devices = app.db.list_devices_by_plugin(client_id)
    return render_template('client_devices.html',
            datatypes = app.datatypes,
            devices = devices,
            clientid = client_id,
            mactve="clients",
            active = 'devices'
            )

@app.route('/client/<client_id>/sensors/edit/<sensor_id>', methods=['GET', 'POST'])
@login_required
def client_sensor_edit(client_id, sensor_id):
    with app.db.session_scope():
        sensor = app.db.get_sensor(sensor_id)
        MyForm = model_form(Sensor, \
                        base_class=Form, \
                        db_session=app.db.get_session(),
                        exclude=['core_device', 'name', 'reference', 'incremental', 'formula', 'data_type', 'conversion', 'last_value', 'last_received', 'history_duplicate'])
	#MyForm.history_duplicate.kwargs['validators'] = []
	MyForm.history_store.kwargs['validators'] = []
        form = MyForm(request.form, sensor)

        if request.method == 'POST' and form.validate():
            if request.form['history_store'] == 'y':
                store = 1 
            else:
                store = 0
            app.db.update_sensor(sensor_id, \
                     history_round=request.form['history_round'], \
                     history_store=store, \
                     history_max=request.form['history_max'], \
                     history_expire=request.form['history_expire'])

            flash(gettext("Changes saved"), "success")
            return redirect("/client/{0}/devices/known".format(client_id))
            pass
	else:
    	    return render_template('client_sensor.html',
		    form = form,
		    clientid = client_id,
		    mactve="clients",
		    active = 'devices'
		    )

@app.route('/client/<client_id>/devices/detected')
@login_required
def client_devices_detected(client_id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('device.new.get')
    res = cli.request(str(client_id), msg.get(), timeout=10)
    if res is not None:
        data = res.get_data()
        devices = data['devices']
    else:
        devices = {}
    return render_template('client_detected.html',
            devices = devices,
            clientid = client_id,
            mactve="clients",
            active = 'devices'
            )

@app.route('/client/<client_id>/devices/edit/<did>', methods=['GET', 'POST'])
@login_required
def client_devices_edit(client_id, did):
    with app.db.session_scope():
        device = app.db.get_device_sql(did)
        MyForm = model_form(Device, \
                        base_class=Form, \
                        db_session=app.db.get_session(),
                        exclude=['params', 'commands', 'sensors', 'address', 'xpl_commands', 'xpl_stats', 'device_type_id', 'client_id', 'client_version'])
        form = MyForm(request.form, device)

	if request.method == 'POST' and form.validate():
            # save it
	    app.db.update_device(did, \
				d_name=request.form['name'], \
				d_description=request.form['description'], \
				d_reference=request.form['reference'])
            # message the suer
            flash(gettext("Device saved"), 'success')
            # reload stats
            req = MQSyncReq(app.zmq_context)
            msg = MQMessage()
            msg.set_action( 'reload' )
            resp = req.request('xplgw', msg.get(), 100)
            # redirect
            return redirect("/client/{0}/devices/known".format(client_id))
	else:
            return render_template('client_device_edit.html',
	        form = form,
                clientid = client_id,
                mactve="clients",
                active = 'devices'
                )

app.route('/client/<client_id>/devices/delete/<did>')
@login_required
def client_devices_delete(client_id, did):
    with app.db.session_scope():
        app.db.del_device(did)
    flash(gettext("Device deleted"), 'success')
    # reload stats
    req = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action( 'reload' )
    resp = req.request('xplgw', msg.get(), 100)
    return redirect("/client/{0}/devices/known".format(client_id))



@app.route('/client/<client_id>/devices/delete/<did>')
@login_required
def client_devices_delete(client_id, did):
    with app.db.session_scope():
        app.db.del_device(did)
    # reload stats
    req = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action( 'reload' )
    resp = req.request('xplgw', msg.get(), 100)
    return redirect("/client/{0}/devices/known".format(client_id))

@app.route('/client/<client_id>/config', methods=['GET', 'POST'])
@login_required
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
    field = submit = SubmitField("Save config")
    setattr(F, "submit", field)

    form = F()

    if request.method == 'POST' and form.validate():
        # build the requested config set
        data = {}
        for arg, value in list(request.form.items()):
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
                flash(gettext("Config saved successfull"), 'success')
            else:
                flash(gettext("Config saved failed"), 'warning')
                flash(data["reason"], 'danger')
        else:
            flash(gettext("DbMgr did not respond on the config.set, check the logs"), 'danger')

    return render_template('client_config.html',
            form = form,
            clientid = client_id,
            mactve="clients",
            active = 'config'
            )

@app.route('/client/<client_id>/devices/new')
@login_required
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
    if type(data["device_types"]) is not dict:
        dtypes = {}
    else:
        dtypes = list(data["device_types"].keys())
    products = {}
    if "products" in data:
        for prod in data["products"]:
            products[prod["name"]] = prod["type"]
 
    return render_template('client_device_new.html',
            device_types = dtypes,
            products = products,
            clientid = client_id,
            mactve="clients",
            active = 'devices'
            )

@app.route('/client/<client_id>/devices/new/type/<device_type_id>', methods=['GET', 'POST'])
@login_required
def client_devices_new_type(client_id, device_type_id):
    return client_devices_new_wiz(client_id, device_type_id, None)

@app.route('/client/<client_id>/devices/new/type/<device_type_id>/prod/<product>', methods=['GET', 'POST'])
@login_required
def client_devices_new_prod(client_id, device_type_id, product):
    return client_devices_new_wiz(client_id, device_type_id, product)

def client_devices_new_wiz(client_id, device_type_id, product):
    # TODO get them
    params = get_device_params(device_type_id, app.zmq_context)

    # dynamically generate the wtfform
    class F(Form):
        name = TextField("Device", [Required()], description=gettext("the display name for this device"))
        description = TextField("Description", description=gettext("A description for this device"))
        if product:
            default = product
        else:
            default = None
        reference = TextField("Reference", description=gettext("A reference for this device"), default=default)
        pass
    # add the global params
    for item in params["global"]:
        if item["type"] == "integer":
            field = IntegerField("Global {0}".format(item["key"]), [Required()], description=item["description"])
        else:
            field = TextField("Global {0}".format(item["key"]), [Required()], description=item["description"])
        setattr(F, item["key"], field)
    form = F()

    if request.method == 'POST' and form.validate():
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('client.detail.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is not None:
            detaila = res.get_data()
            client_data = detaila[client_id]['data']
        else:
            flash(gettext("Device creation failed"), "warning")
            flash(gettext("Can not find this client id"), "danger")
            return redirect("/client/{0}/devices/known".format(client_id))
        with app.db.session_scope():
            # create the device
            created_device = app.db.add_device_and_commands(
                name=request.form.get('name'),
                device_type=device_type_id,
                client_id=client_id,
                description=request.form.get('description'),
                reference=request.form.get('reference'),
                client_data=client_data
            )
            # add the global
            for x in app.db.get_xpl_command_by_device_id(created_device["id"]):
                for p in params['global']:
                    if p["xpl"] is True:
                        app.db.add_xpl_command_param(cmd_id=x.id, key=p['key'], value=request.form.get(p['key']))
            for x in app.db.get_xpl_stat_by_device_id(created_device["id"]):
                for p in params['global']:
                    if p["xpl"] is True:
                        app.db.add_xpl_stat_param(statid=x.id, key=p['key'], value=request.form.get(p['key']), static=True, type=p['type'])
            for p in params['global']:
                if p["xpl"] is not True:
                    app.db.add_device_param(created_device["id"], p["key"], request.form.get(p['key']), p['type'])
            # reload stats
            req = MQSyncReq(app.zmq_context)
            msg = MQMessage()
            msg.set_action( 'reload' )
            resp = req.request('xplgw', msg.get(), 100)
            # inform the user
            flash(gettext("device created"), "success")
            return redirect("/client/{0}/devices/known".format(client_id))

    return render_template('client_device_new_wiz.html',
            form = form,
            params = params,
            dtype = device_type_id,
            clientid = client_id,
            mactve="clients",
            active = 'devices'
            )

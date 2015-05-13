from domogik.admin.application import app, render_template
from flask import request, flash, redirect
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
try:
    from flask_wtf import Form
except ImportError:
    from flaskext.wtf import Form
    pass
from wtforms import TextField, HiddenField, validators, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField, \
            DateField, DateTimeField, FloatField, PasswordField
from wtforms.validators import Required
from flask_login import login_required
try:
    from flask.ext.babel import gettext, ngettext
except ImportError:
    from flask_babel import gettext, ngettext
    pass

from domogik.common.sql_schema import Device, Sensor
from wtforms.ext.sqlalchemy.orm import model_form
from collections import OrderedDict
from domogik.common.utils import get_rest_url
from operator import itemgetter



def get_client_detail(client_id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('client.detail.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        detaila = res.get_data()
        detail = detaila[client_id]
    else:
        detail = {}
    return detail

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

    client_list_per_host_per_type = OrderedDict()
    for client in client_list:
        cli_type = client_list[client]['type']
        cli_host = client_list[client]['host']

        if not client_list_per_host_per_type.has_key(cli_host):
            client_list_per_host_per_type[cli_host] = {}

        if not client_list_per_host_per_type[cli_host].has_key(cli_type):
            client_list_per_host_per_type[cli_host][cli_type] = {}

        client_list_per_host_per_type[cli_host][cli_type][client] = client_list[client]

    return render_template('clients.html',
        mactive="clients",
        overview_state="collapse",
        clients=client_list,
        client_list_per_host_per_type=client_list_per_host_per_type
        )

@app.route('/client/<client_id>')
@login_required
def client_detail(client_id):
    detail = get_client_detail(client_id)

    return render_template('client.html',
            loop = {'index': 1},
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'home'
            )

@app.route('/client/<client_id>/dmg_devices/known')
@login_required
def client_devices_known(client_id):
    detail = get_client_detail(client_id)

    if app.datatypes == {}:
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('datatype.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is not None:
            app.datatypes = res.get_data()['datatypes']
        else:
            app.datatypes = {}

    # todo : grab from MQ ?
    with app.db.session_scope():
        devices = app.db.list_devices_by_plugin(client_id)

    # sort clients per device type
    devices_by_device_type_id = {}
    for dev in devices:
        if devices_by_device_type_id.has_key(dev['device_type_id']):
            devices_by_device_type_id[dev['device_type_id']].append(dev)
        else:
            devices_by_device_type_id[dev['device_type_id']] = [dev]

    return render_template('client_devices.html',
            datatypes = app.datatypes,
            devices = devices,
            devices_by_device_type_id = devices_by_device_type_id,
            clientid = client_id,
            mactive="clients",
            active = 'devices',
            rest_url = get_rest_url(),
            client_detail = detail
            )

@app.route('/client/<client_id>/sensors/edit/<sensor_id>', methods=['GET', 'POST'])
@login_required
def client_sensor_edit(client_id, sensor_id):
    with app.db.session_scope():
        sensor = app.db.get_sensor(sensor_id)
        MyForm = model_form(Sensor, \
                        base_class=Form, \
                        db_session=app.db.get_session(),
                        exclude=['core_device', 'name', 'reference', 'incremental', 'data_type', 'conversion', 'last_value', 'last_received', 'history_duplicate','value_min','value_max'])
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
                     history_expire=request.form['history_expire'],
                     timeout=request.form['timeout'],
                     formula=request.form['formula'])

            flash(gettext("Changes saved"), "success")
            return redirect("/client/{0}/dmg_devices/known".format(client_id))
            pass
        else:
                return render_template('client_sensor.html',
                form = form,
                clientid = client_id,
                mactive="clients",
                active = 'devices',
                sensor = sensor
                )

@app.route('/client/<client_id>/dmg_devices/detected')
@login_required
def client_devices_detected(client_id):
    detail = get_client_detail(client_id)

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
            mactive="clients",
            active = 'devices',
            client_detail = detail
            )

@app.route('/client/<client_id>/dmg_devices/edit/<did>', methods=['GET', 'POST'])
@login_required
def client_devices_edit(client_id, did):
    detail = get_client_detail(client_id)
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
            # redirect
            return redirect("/client/{0}/dmg_devices/known".format(client_id))
        else:
            return render_template('client_device_edit.html',
                form = form,
                clientid = client_id,
                mactive="clients",
                active = 'devices',
                client_detail = detail,
                )

@app.route('/client/<client_id>/dmg_devices/delete/<did>')
@login_required
def client_devices_delete(client_id, did):
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
    return redirect("/client/{0}/dmg_devices/known".format(client_id))

@app.route('/client/<client_id>/config', methods=['GET', 'POST'])
@login_required
def client_config(client_id):
    cli = MQSyncReq(app.zmq_context)
    detail = get_client_detail(client_id)
    config = detail['data']['configuration']
    known_items = {}

    # dynamically generate the wtfform
    class F(Form):
        submit = SubmitField("Send")
        pass
    for item in config:
        # keep track of the known fields
        known_items[item["key"]] = item["type"]
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
            if default == 'Y' or default == 1 or default == True:
                default = True
            else:
                default = False
            field = BooleanField(item["name"], arguments, description=item["description"], default=default)
        elif item["type"] == "integer":
            field = IntegerField(item["name"], arguments, description=item["description"], default=default)
        elif item["type"] == "date":
            field = DateField(item["name"], arguments, description=item["description"], default=default)
        elif item["type"] == "datetime":
            field = DateTimeField(item["name"], arguments, description=item["description"], default=default)
        elif item["type"] == "float":
            field = DateTimeField(item["name"], arguments, description=item["description"], default=default)
        elif item["type"] == "choice":
            choices = []
            for choice in sorted(item["choices"]):
                choices.append((choice, choice))
            field = SelectField(item["name"], arguments, description=item["description"], choices=choices, default=default)
        elif item["type"] == "password":
            field = PasswordField(item["name"], [Required()], description=item["description"])
        else:
            # time, email, ipv4, ipv6, url
            field = TextField(item["name"], arguments, description=item["description"], default=default)
        # add the field
        setattr(F, item["key"], field)
    # Add the submit button only if there is some existing configuration to save...
    # plugins with identity->xpl_clients_only == True for example have no configuration items
    if config != []:
        field = submit = SubmitField("Save configuration")
        setattr(F, "submit", field)
        form = F()
    else:
        form = None


    if request.method == 'POST' and form.validate():
        # build the requested config set
        data = {}
        for key, typ in known_items.iteritems():
            val = getattr(form, key).data
            if typ == "boolean":
                if val == False:
                    val = 'N'
                else:
                    val = 'Y'
            data[key] = val
        print data
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
            mactive="clients",
            active = 'config',
            client_detail = detail
            )

@app.route('/client/<client_id>/dmg_devices/new')
@login_required
def client_devices_new(client_id):
    detail = get_client_detail(client_id)
    data = detail['data']

    device_types_keys = sorted(data["device_types"])
    device_types_list = OrderedDict()
    for key in device_types_keys:
        device_types_list[key] = data["device_types"][key]
    products = {}
    products_per_type = OrderedDict()
    if "products" in data:
        products_list = data["products"]
        products_list = sorted(products_list, key=itemgetter("name"))
        for prod in products_list:
            product_label = data['device_types'][prod["type"]]['name']
            products[prod["name"]] = prod["type"]
            #if not products_per_type.has_key(prod["type"]):
            if not products_per_type.has_key(product_label):
                products_per_type[product_label] = OrderedDict()
            products_per_type[product_label][prod['name']] = prod["type"]
    # TODO : include products icons
        
 
    return render_template('client_device_new.html',
            device_types = device_types_list,
            products = products,
            products_per_type = products_per_type,
            clientid = client_id,
            mactive="clients",
            active = 'devices',
            client_detail = detail,
            )

@app.route('/client/<client_id>/dmg_devices/new/type/<device_type_id>', methods=['GET', 'POST'])
@login_required
def client_devices_new_type(client_id, device_type_id):
    return client_devices_new_wiz(client_id, device_type_id, None)

@app.route('/client/<client_id>/dmg_devices/new/type/<device_type_id>/prod/<product>', methods=['GET', 'POST'])
@login_required
def client_devices_new_prod(client_id, device_type_id, product):
    return client_devices_new_wiz(client_id, 
                                  device_type_id, 
                                  product)

def client_devices_new_wiz(client_id, device_type_id, product):
    detail = get_client_detail(client_id)
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('device.params')
    msg.set_data({'device_type': device_type_id})
    res = cli.request('dbmgr', msg.get(), timeout=10)
    if res is not None:
        detaila = res.get_data()
        params = detaila['result']
    else:
        flash(gettext("Device creation failed"), "warning")
        flash(gettext("DbMGR is not answering with device_type parameters"), "danger")
        return redirect("/client/{0}/dmg_devices/known".format(client_id))

    # dynamically generate the wtfform
    class F(Form):
        name = TextField("Device name", [Required()], description=gettext("The display name for this device"))
        description = TextField("Description", description=gettext("A description for this device"))
        reference = TextField("Reference", description=gettext("A reference for this device"))
        pass
    # Form for the Global part
    class F_global(Form):
        pass
    # Form for the xpl part
    class F_xpl(Form):
        pass
    # Form for the xpl command part
    class F_xpl_command(Form):
        pass
    # Form for the xpl stat part
    class F_xpl_stat(Form):
        pass

    # add the global params
    for item in params["global"]:
        # build the field
        name = "{0}".format(item["key"])
        default = None
        if 'default' in item:
            default = item['default']
        if item["type"] == "boolean":
            if default == 'Y' or default == 1 or default == True:
                default = True
            else:
                default = False
            field = BooleanField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "integer":
            field = IntegerField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "date":
            field = DateField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "datetime":
            field = DateTimeField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "float":
            field = DateTimeField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "choice":
            choices = []
            for key in sorted(item["choices"]):
                choices.append((key, item["choices"][key]))
            field = SelectField(name, [Required()], description=item["description"], choices=choices)
        elif item["type"] == "password":
            field = PasswordField(name, [Required()], description=item["description"], default=default)
        else:
            # time, email, ipv4, ipv6, url
            field = TextField(name, [Required()], description=item["description"], default=default)
        setattr(F, "glob|{0}".format(item["key"]), field)
        setattr(F_global, "glob|{0}".format(item["key"]), field)
    # add the xpl params
    for item in params["xpl"]:
        # build the field
        name = "{0}".format(item["key"])
        default = None
        if 'default' in item:
            default = item['default']
        if item["type"] == "boolean":
            if default == 'Y' or default == 1 or default == True:
                default = True
            else:
                default = False
            field = BooleanField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "integer":
            field = IntegerField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "date":
            field = DateField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "datetime":
            field = DateTimeField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "float":
            field = DateTimeField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "choice":
            choices = []
            for key in sorted(item["choices"]):
                choices.append((key, item["choices"][key]))
            field = SelectField(name, [Required()], description=item["description"], choices=choices, default=default)
        elif item["type"] == "password":
            field = PasswordField(name, [Required()], description=item["description"], default=default)
        else:
            # time, email, ipv4, ipv6, url
            field = TextField(name, [Required()], description=item["description"], default=default)
        setattr(F, "xpl|{0}".format(item["key"]), field)
        setattr(F_xpl, "xpl|{0}".format(item["key"]), field)
    for cmd in params["xpl_commands"]:
        for item in params["xpl_commands"][cmd]:
            # build the field
            name = "{0} - {1}".format(cmd, item["key"])
            default = None
            if 'default' in item:
                default = item['default']
            if item["type"] == "boolean":
                if default == 'Y' or default == 1 or default == True:
                    default = True
                else:
                    default = False
                field = BooleanField(name, [Required()], description=item["description"], default=default)
            elif item["type"] == "integer":
                field = IntegerField(name, [Required()], description=item["description"], default=default)
            elif item["type"] == "date":
                field = DateField(name, [Required()], description=item["description"], default=default)
            elif item["type"] == "datetime":
                field = DateTimeField(name, [Required()], description=item["description"], default=default)
            elif item["type"] == "float":
                field = DateTimeField(name, [Required()], description=item["description"], default=default)
            elif item["type"] == "choice":
                choices = []
                for key in sorted(item["choices"]):
                    choices.append((key, item["choices"][key]))
                field = SelectField(name, [Required()], description=item["description"], choices=choices, default=default)
            elif item["type"] == "password":
                field = PasswordField(name, [Required()], description=item["description"], default=default)
            else:
                # time, email, ipv4, ipv6, url
                field = TextField(name, [Required()], description=item["description"], default=default)
            setattr(F, "cmd|{0}|{1}".format(cmd,item["key"]), field)
            setattr(F_xpl_command, "cmd|{0}|{1}".format(cmd,item["key"]), field)
    for cmd in params["xpl_stats"]:
        for item in params["xpl_stats"][cmd]:
            # build the field
            name = "{0} - {1}".format(cmd, item["key"])
            default = None
            if 'default' in item:
                default = item['default']
            desc = item["description"]
            if 'multiple' in item and len(item['multiple']) == 1:
                desc = "{0}. Multiple values allowed, seperate with '{1}'".format(desc, item['multiple'])
                # ugly fix, override field type
                item['type'] = "string"
            if item["type"] == "boolean":
                if default == 'Y' or default == 1 or default == True:
                    default = True
                else:
                    default = False
                field = BooleanField(name, [validators.Required(gettext("This value is required"))], description=desc, default=default)
            elif item["type"] == "integer":
                field = IntegerField(name, [validators.Required(gettext("This value is required"))], description=desc, default=default)
            elif item["type"] == "date":
                field = DateField(name, [validators.Required(gettext("This value is required"))], description=desc, default=default)
            elif item["type"] == "datetime":
                field = DateTimeField(name, [validators.Required(gettext("This value is required"))], description=desc, default=default)
            elif item["type"] == "float":
                field = DateTimeField(name, [validators.Required(gettext("This value is required"))], description=desc, default=default)
            elif item["type"] == "choice":
                choices = []
                for key in sorted(item["choices"]):
                    choices.append((key, item["choices"][key]))
                field = SelectField(name, [validators.Required(gettext("This value is required"))], description=desc, choices=choices, default=default)
            elif item["type"] == "password":
                field = PasswordField(name, [validators.Required(gettext("This value is required"))], description=desc, default=default)
            else:
                # time, email, ipv4, ipv6, url
                field = TextField(name, [validators.Required(gettext("This value is required"))], description=desc, default=default)
            setattr(F, "stat|{0}|{1}".format(cmd,item["key"]), field)
            setattr(F_xpl_stat, "stat|{0}|{1}".format(cmd,item["key"]), field)
    # create the forms
    form = F()
    form_global = F_global()
    form_xpl = F_xpl()
    form_xpl_command = F_xpl_command()
    form_xpl_stat = F_xpl_stat()

    if request.method == 'POST' and form.validate():
        # aprams hold the stucture,
        # append a vlaue key everywhere with the value submitted
        # or fill in the key
        params['client_id'] = client_id
        for item in request.form:
            if item in ["name", "reference", "description"]:
                # handle the global things
                params[item] = request.form.get(item)
            elif item.startswith('xpl') or item.startswith('glob'):
                # handle the global params
                if item.startswith('xpl'):
                    key = 'xpl'
                else:
                    key = 'global'
                par = item.split('|')[1]
                i = 0
                while i < len(params[key]):
                    param = params[key][i]
                    if par == param['key']:
                        params[key][i]['value'] = request.form.get(item)
                    i = i + 1
            elif item.startswith('stat') or item.startswith('cmd'):
                if item.startswith('stat'):
                    key = "xpl_stats"
                else:
                    key = "xpl_commands"
                name = item.split('|')[1]
                par = item.split('|')[2]
                i = 0
                while i < len(params[key][name]):
                    param = params[key][name][i]
                    if par == param['key']:
                        params[key][name][i]['value'] = request.form.get(item)
                    i = i + 1
        # we now have the json to return
        msg = MQMessage()
        msg.set_action('device.create')
        msg.set_data({'data': params})
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            data = res.get_data()
            if data["status"]:
                flash(gettext("Device created succesfully"), 'success')
            else:
                flash(gettext("Device creation failed"), 'warning')
                flash(data["reason"], 'danger')
        else:
            flash(gettext("DbMgr did not respond on the device.create, check the logs"), 'danger')
        return redirect("/client/{0}/dmg_devices/known".format(client_id))

    return render_template('client_device_new_wiz.html',
            form = form,
            form_global = form_global,
            form_xpl = form_xpl,
            form_xpl_command = form_xpl_command,
            form_xpl_stat = form_xpl_stat,
            params = params,
            dtype = device_type_id,
            clientid = client_id,
            mactive="clients",
            active = 'devices',
            client_detail = detail
            )

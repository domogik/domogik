import re
import json
import traceback
import operator
import os
from domogik.common.utils import get_packages_directory
from domogik.admin.application import app, render_template
from flask import request, flash, redirect, send_from_directory
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
try:
    from flask_wtf import Form
except ImportError:
    from flaskext.wtf import Form
    pass
from wtforms import TextField, HiddenField, validators, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField, \
            DateField, DateTimeField, FloatField, PasswordField, RadioField
from wtforms.validators import Required, InputRequired
from flask_login import login_required
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass
from domogik.common.sql_schema import Device, DeviceParam, Sensor
from domogik.common.plugin import STATUS_DEAD
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.widgets import TextArea
from collections import OrderedDict
from domogik.common.utils import get_rest_url
from operator import itemgetter
from domogik.common.utils import build_deviceType_from_packageJson
from domogikmq.pubsub.publisher import MQPub

try:
    import html.parser
    html_parser = html.parser.HTMLParser()
except ImportError:
    import HTMLParser
    html_parser = HTMLParser.HTMLParser()



html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

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

# used by advanced pages (see plugin-ftpcamera for example)
def get_client_devices(client_id):
    """ The advanced pages have no direct db access, so they used this function to easily get all the devices
    """
    with app.db.session_scope():
        devices = app.db.list_devices_by_plugin(client_id)
    return devices

def get_butler_history():
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('butler.history.get')
    res = cli.request('butler', msg.get(), timeout=10)
    if res is not None:
        history = res.get_data()['history']
    else:
        history = []
    return history

def get_clients_list():
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('client.list.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        client_list = res.get_data()
    else:
        client_list = {}
    return client_list

@app.route('/clients')
@login_required
def clients():
    #cli = MQSyncReq(app.zmq_context)
    #msg = MQMessage()
    #msg.set_action('client.list.get')
    #res = cli.request('manager', msg.get(), timeout=10)
    #if res is not None:
    #    client_list = res.get_data()
    #else:
    #    client_list = {}
    client_list = get_clients_list()

    client_list_per_host_per_type = OrderedDict()
    num_core = 0
    num_core_dead = 0
    for client in client_list:
        cli_type = client_list[client]['type']
        cli_host = client_list[client]['host']
        if cli_type == "core":
            num_core += 1
            if client_list[client]['status'] == STATUS_DEAD:
                num_core_dead += 1

        if cli_host not in client_list_per_host_per_type:
            client_list_per_host_per_type[cli_host] = {}

        if cli_type not in client_list_per_host_per_type[cli_host]:
            client_list_per_host_per_type[cli_host][cli_type] = {}

        client_list_per_host_per_type[cli_host][cli_type][client] = client_list[client]


    # sorting
    client_list_per_host_per_type = json.dumps(client_list_per_host_per_type, sort_keys=True)
    client_list_per_host_per_type = json.loads(client_list_per_host_per_type, object_pairs_hook=OrderedDict)

    # if all the core clients are dead, there is an issue with MQ pub/sub (forwarder)
    # so display a message
    if num_core > 0 and num_core == num_core_dead:
        msg_core_dead = "Ooups, it seems that you have an issue with your current configuration!<br>"
        msg_core_dead += "The message queue is not working for PUB/SUB messages.<br>"
        msg_core_dead += "This is related to the component MQ forwarder.<br>"
        msg_core_dead += "The related configuration file is : /etc/domogik/domogik-mq.cfg.<br>"
    else:
        msg_core_dead = None

    return render_template('clients.html',
        mactive="clients",
        overview_state="collapse",
        clients=client_list,
        client_list_per_host_per_type=client_list_per_host_per_type,
        msg_core_dead = msg_core_dead)

@app.route('/client/<client_id>')
@login_required
def client_detail(client_id):
    detail = get_client_detail(client_id)

    return render_template('client.html',
            loop = {'index': 1},
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'home')

@app.route('/client/<client_id>/timeline')
@login_required
def client_timeline(client_id):
    from domogik.admin.views.timeline import timeline_generic
    temp = timeline_generic(the_client_id = client_id, asDict = True)
    detail = get_client_detail(client_id)

    return render_template('client_timeline.html',
            timeline = temp['timeline'],
            datatypes = temp['datatypes'],
            client_detail = detail,
            clientid = client_id,
            device_name = client_id,
            mactive="clients",
            active = 'timeline')

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
        try:
            devices = app.db.list_devices_by_plugin(client_id)
            error = None
        except:
            error = "Error while retrieving the devices list. Error is : {0}".format(traceback.format_exc())
            devices = []

    # first sort by device name
    devices = sorted(devices, key=itemgetter("name"))
    #    device_types_list[key] = data["device_types"][key]

    # group clients per device type
    devices_by_device_type_id = {}
    for dev in devices:
        try:
            device_type_name = detail['data']['device_types'][dev['device_type_id']]['name']
        except KeyError:
            print(u"Warning : the device type '{0}' does not exist anymore in the installed package release. Device type name set as the existing id in database".format(dev['device_type_id']))
            device_type_name = dev['device_type_id']
        if device_type_name in devices_by_device_type_id:
            devices_by_device_type_id[device_type_name].append(dev)
        else:
            devices_by_device_type_id[device_type_name] = [dev]

    # sorting
    # disabled as this breaks because of storing other objects then normal strings
    devices_by_device_type_id = json.dumps(devices_by_device_type_id, sort_keys=True)
    devices_by_device_type_id = json.loads(devices_by_device_type_id, object_pairs_hook=OrderedDict)

    return render_template('client_devices.html',
            datatypes = app.datatypes,
            devices = devices,
            devices_by_device_type_id = devices_by_device_type_id,
            clientid = client_id,
            mactive="clients",
            active = 'devices',
            #rest_url = get_rest_url(),
            rest_url = request.url_root + "rest",
            client_detail = detail,
            error = error)


@app.route('/client/<client_id>/sensors/edit/<sensor_id>', methods=['GET', 'POST'])
@login_required
def client_sensor_edit(client_id, sensor_id):
    if app.datatypes == {}:
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('datatype.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is not None:
            app.datatypes = res.get_data()['datatypes']
        else:
            app.datatypes = {}

    with app.db.session_scope():
        sensor = app.db.get_sensor(sensor_id)
        cdata_type = app.datatypes[sensor.data_type]
        if 'childs'in cdata_type and len(cdata_type['childs']) > 0:
            allow_data_type = True
            lst = cdata_type['childs']
            lst.append(sensor.data_type)
            tmp = dict(zip(lst, lst))
            tmps = sorted(tmp.items(), key=operator.itemgetter(1))
        else:
            allow_data_type = False
        class F(Form):
            timeout = TextField("Timeout", default=sensor.timeout)
            formula = TextField("Formula", default=sensor.formula, widget=TextArea())
            history_store = BooleanField("History Store", default=sensor.history_store)
            history_expire = TextField("History Expire", default=sensor.history_expire)
            history_round = TextField("History_round", default=sensor.history_round)
            history_max = TextField("History_max", default=sensor.history_max)
            pass
        # TODO add fiel
        if allow_data_type:
            field = SelectField("Data_type", default=sensor.data_type, choices=tmps)
            setattr(F, 'data_type', field)

        form = F()

        if request.method == 'POST' and form.validate():
            if request.form['history_store'] == 'y':
                hstore = 1
            else:
                hstore = 0
            if 'history_round' not in request.form:
                hround = None
            else:
                hround = request.form['history_round']
            if 'history_store' not in request.form:
                hstore = None
            else:
                hstore = request.form['history_store']
            if 'history_max' not in request.form:
                hmax = None
            else:
                hmax = request.form['history_max']
            if 'history_expire' not in request.form:
                hexpire = None
            else:
                hexpire = request.form['history_expire']
            if 'timeout' not in request.form:
                timeout = None
            else:
                timeout = request.form['timeout']
            if 'formula' not in request.form:
                formula = None
            else:
                formula = request.form['formula']
            if 'data_type' not in request.form:
                data_type = None
            else:
                data_type = request.form['data_type']
            # do the update
            res = app.db.update_sensor(sensor_id, \
                 history_round=hround, \
                 history_store=hstore, \
                 history_max=hmax, \
                 history_expire=hexpire, \
                 timeout=timeout, \
                 formula=formula, \
                 data_type=data_type)
            if res:
                flash(gettext("Sensor update succesfully"), 'success')
            else:
                flash(gettext("Senor update failed"), 'warning')
            return redirect("/client/{0}/dmg_devices/known".format(client_id))
        else:
            return render_template('client_sensor.html',
                form = form,
                clientid = client_id,
                mactive="clients",
                active = 'devices',
                allow_data_type = allow_data_type,
                sensor = sensor)

@app.route('/client/<client_id>/global/edit/<dev_id>', methods=['GET', 'POST'])
@login_required
def client_global_edit(client_id, dev_id):
    with app.db.session_scope():
        dev = app.db.get_device(dev_id)
        known_items = {}
        class F(Form):
            pass
        for item in dev["parameters"]:
            item = dev["parameters"][item]
            default = item["value"]
            arguments = [InputRequired()]
            # keep track of the known fields
            known_items[item["key"]] = {u"id": item["id"], u"type": item["type"]}
            # build the field
            if item["type"] == "boolean":
                if default == 'y' or default == 1 or default == True: # in db value stored in lowcase
                    #default = True
                    default = 'y'
                else:
                    #default = False
                    default = 'n'
                #field = BooleanField(item["key"], [validators.optional()], default=default) # set to optional field due to WTForm BooleanField return no data for false value (HTML checkbox)
                field = RadioField( item["key"], 
                                [validators.optional()],
                                choices=[('y', 'Yes'), ('n', 'No')], default=default
                              )
            elif item["type"] == "integer":
                field = IntegerField(item["key"], arguments, default=default)
            elif item["type"] == "datetime":
                field = DateTimeField(item["key"], arguments, default=default)
            elif item["type"] == "float":
                field = FloatField(item["key"], arguments, default=default)
            elif item["type"] == "password":
                field = PasswordField(item["key"], arguments, default=default)
            else:
                # time, email, ipv4, ipv6, url
                field = TextField(item["key"], arguments, default=default)
            # add the field
            setattr(F, "{0}-{1}".format(item["id"], item["key"]), field)
        form = F()
        if request.method == 'POST' and form.validate():
            for key, item in known_items.items():
                val = getattr(form, "{0}-{1}".format(item["id"], key)).data
                if item["type"] == "boolean":
                    if val == 'n':
                        val = 'n' # in db value stored in lowcase
                    else:
                        val = 'y' # in db value stored in lowcase
                with app.db.session_scope():
                    res = app.db.udpate_device_param(item["id"], value=val)
                    if res:
                        flash(gettext("Param update succesfully"), 'success')
                    else:
                        flash(gettext("Param update failed"), 'warning')
                    # in all case we send an update event (in case of partial success...)
                    pub = MQPub(app.zmq_context, 'admin-views')
                    pub.send_event('device.update',
                                   {"device_id" : dev_id,
                                    "client_id" : client_id})
            return redirect("/client/{0}/dmg_devices/known".format(client_id))
            pass
        else:
                return render_template('client_global.html',
                form = form,
                clientid = client_id,
                client_detail = get_client_detail(client_id),
                mactive="clients",
                active = 'devices',
                device = dev)


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
            client_detail = detail)


@app.route('/client/<client_id>/dmg_devices/edit/<did>', methods=['GET', 'POST'])
@login_required
def client_devices_edit(client_id, did):
    detail = get_client_detail(client_id)
    with app.db.session_scope():
        device = app.db.get_device_sql(did)
        MyForm = model_form(Device, \
                        base_class=Form, \
                        db_session=app.db.get_session(),
                        exclude=['params', 'commands', 'sensors', 'address', \
                                'xpl_commands', 'xpl_stats', 'device_type_id', \
                                'client_id', 'client_version', 'info_changed'])
        form = MyForm(request.form, device)

        if request.method == 'POST' and form.validate():
            res = app.db.update_device(did, \
                d_name=request.form['name'], \
                d_description=request.form['description'], \
                d_reference=request.form['reference'])
            if res:
                flash(gettext("Device update succesfully"), 'success')
            else:
                flash(gettext("Device update failed"), 'warning')
            # in all case we send an update event (in case of partial success...)
            pub = MQPub(app.zmq_context, 'admin-views')
            pub.send_event('device.update',
                           {"device_id" : did,
                            "client_id" : client_id})
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
    with app.db.session_scope():
        res = app.db.del_device(did)
        if not res:
            flash(gettext("Device deleted failed"), 'warning')
        else:
            flash(gettext("Device deleted succesfully"), 'success')
        # in all case we send an update event (in case of partial success...)
        pub = MQPub(app.zmq_context, 'admin-views')
        pub.send_event('device.update',
                       {"device_id" : did,
                        "client_id" : res.client_id})
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
            arguments = [InputRequired()]
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
            field = SelectField(item["name"], arguments, description=item["description"], \
                    choices=choices, default=default)
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
        with app.db.session_scope():
            tmp = client_id.split('-')
            type = tmp[0]
            tmp = tmp[1].split('.')
            host = tmp[1]
            name = tmp[0]
            app.db.set_plugin_config(type, name, host, "configured", True)
            for key, typ in known_items.items():
                val = getattr(form, key).data
                if typ == "boolean":
                    if val == False:
                        val = 'N'
                    else:
                        val = 'Y'
                app.db.set_plugin_config(type, name, host, key, val)
        pub = MQPub(app.zmq_context, 'admin-views')
        pub.send_event('plugin.configuration',
                         {"type" : type,
                          "name" : name,
                          "host" : host,
                          "event" : "updated"})
        flash(gettext("Config saved successfully"), 'success')
    
    return render_template('client_config.html',
            form = form,
            clientid = client_id,
            mactive="clients",
            active = 'config',
            client_detail = detail)

@app.route('/client/<client_id>/dmg_devices/new')
@login_required
def client_devices_new(client_id):
    detail = get_client_detail(client_id)
    data = detail['data']

    # devices type list
    device_types_keys = sorted(data["device_types"])
    device_types_list = OrderedDict()
    for key in device_types_keys:
        device_types_list[key] = data["device_types"][key]

    # sorting
    # TODO

    # products list
    products = {}
    products_per_type = OrderedDict()
    if "products" in data:
        products_list = data["products"]
        products_list = sorted(products_list, key=itemgetter("name"))
        for prod in products_list:
            product_label = data['device_types'][prod["type"]]['name']
            products[prod["name"]] = prod["type"]
            #if not products_per_type.has_key(prod["type"]):
            if product_label not in products_per_type:
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
    (params, reason, status) = build_deviceType_from_packageJson(app.zmq_context, device_type_id, client_id)

    # dynamically generate the wtfform
    class F(Form):
        name = TextField("Device name", [Required()], description=gettext("The display name for this device"))
        try: default = request.args.get('Description')
        except: default = None
        description = TextField("Description", description=gettext("A description for this device"), default=default)
        try: default = request.args.get('Reference')
        except: default = None
        reference = TextField("Reference", description=gettext("A reference for this device"), default=default)
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
        try: 
            default = request.args.get(name)
        except: 
            if item["type"] == "boolean":
                default = False
            else:
                default = None
        if 'default' in item:
            default = item['default']
        if item["type"] == "boolean":
            if default == 'Y' or default == 1 or default == True:
                #default = True
                default = 'y'
            else:
                #default = False
                default = 'n'
            #field = BooleanField(name, [InputRequired()], description=item["description"], default=default)
            #field = BooleanField(name, [], description=item["description"], default=default)
            field = RadioField( name, 
                                [validators.Required()], description=item["description"],
                                choices=[('y', 'Yes'), ('n', 'No')], default=default
                              )
        elif item["type"] == "integer":
            field = IntegerField(name, [InputRequired()], description=item["description"], default=default)
        elif item["type"] == "date":
            field = DateField(name, [InputRequired()], description=item["description"], default=default)
        elif item["type"] == "datetime":
            field = DateTimeField(name, [InputRequired()], description=item["description"], default=default)
        elif item["type"] == "float":
            field = FloatField(name, [InputRequired()], description=item["description"], default=default)
        elif item["type"] == "choice":
            choices = []
            if type(item["choices"]) == list:
                for key in sorted(item["choices"]):
                    choices.append((key, key))
            else:
                for key in sorted(item["choices"]):
                    choices.append((key, item["choices"][key]))
            field = SelectField(name, [Required()], description=item["description"], choices=choices, default=default)
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
        try: default = request.args.get(name)
        except: default = None
        if 'default' in item:
            default = item['default']
        if item["type"] == "boolean":
            if default == 'Y' or default == 1 or default == True:
                #default = True
                default = 'y'
            else:
                #default = False
                default = 'n'
            #field = BooleanField(name, [InputRequired()], description=item["description"], default=default)
            #field = BooleanField(name, [], description=item["description"], default=default)
            field = RadioField( name,
                                [validators.Required()], description=item["description"],
                                choices=[('y', 'Yes'), ('n', 'No')], default=default
                              )
        elif item["type"] == "integer":
            field = IntegerField(name, [InputRequired()], description=item["description"], default=default)
        elif item["type"] == "date":
            field = DateField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "datetime":
            field = DateTimeField(name, [Required()], description=item["description"], default=default)
        elif item["type"] == "float":
            field = FloatField(name, [InputRequired()], description=item["description"], default=default)
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
            try: default = request.args.get(name)
            except: default = None
            if 'default' in item:
                default = item['default']
            if item["type"] == "boolean":
                if default == 'Y' or default == 1 or default == True:
                    #default = True
                    default = 'y'
                else:
                    #default = False
                    default = 'n'
                #field = BooleanField(name, [InputRequired()], description=item["description"], default=default)
                #field = BooleanField(name, [], description=item["description"], default=default)
                field = RadioField( name,
                                    [validators.Required()], description=item["description"],
                                    choices=[('y', 'Yes'), ('n', 'No')], default=default
                                  )
            elif item["type"] == "integer":
                field = IntegerField(name, [InputRequired()], description=item["description"], default=default)
            elif item["type"] == "date":
                field = DateField(name, [Required()], description=item["description"], default=default)
            elif item["type"] == "datetime":
                field = DateTimeField(name, [Required()], description=item["description"], default=default)
            elif item["type"] == "float":
                field = FloatField(name, [InputRequired()], description=item["description"], default=default)
            elif item["type"] == "choice":
                choices = []
                for key in sorted(item["choices"]):
                    choices.append((key, item["choices"][key]))
                field = SelectField(name, [Required()], description=item["description"], choices=choices, \
                        default=default)
            elif item["type"] == "password":
                field = PasswordField(name, [Required()], description=item["description"], default=default)
            else:
                # time, email, ipv4, ipv6, url
                field = TextField(name, [Required()], description=item["description"], default=default)
            setattr(F, "cmd|{0}|{1}".format(cmd, item["key"]), field)
            setattr(F_xpl_command, "cmd|{0}|{1}".format(cmd, item["key"]), field)
    for cmd in params["xpl_stats"]:
        for item in params["xpl_stats"][cmd]:
            # build the field
            name = "{0} - {1}".format(cmd, item["key"])
            try: default = request.args.get(name)
            except: default = None
            if 'default' in item:
                default = item['default']
            desc = item["description"]
            if 'multiple' in item and len(item['multiple']) == 1:
                desc = "{0}. Multiple values allowed, seperate with '{1}'".format(desc, item['multiple'])
                # ugly fix, override field type
                item['type'] = "string"
            if item["type"] == "boolean":
                if default == 'Y' or default == 1 or default == True:
                    #default = True
                    default = 'y'
                else:
                    #default = False
                    default = 'n'
                #field = BooleanField(name, [validators.InputRequired(gettext("This value is required"))], \
                #        description=desc, default=default)
                #field = BooleanField(name, [], \
                #        description=desc, default=default)
                field = RadioField( name,
                                    [validators.Required()], description=item["description"],
                                    choices=[('y', 'Yes'), ('n', 'No')], default=default
                                  )
            elif item["type"] == "integer":
                field = IntegerField(name, [validators.InputRequired(gettext("This value is required"))], \
                        description=desc, default=default)
            elif item["type"] == "date":
                field = DateField(name, [validators.Required(gettext("This value is required"))], \
                        description=desc, default=default)
            elif item["type"] == "datetime":
                field = DateTimeField(name, [validators.Required(gettext("This value is required"))], \
                        description=desc, default=default)
            elif item["type"] == "float":
                field = FloatField(name, [validators.InputRequired(gettext("This value is required"))], \
                        description=desc, default=default)
            elif item["type"] == "choice":
                choices = []
                for key in sorted(item["choices"]):
                    choices.append((key, item["choices"][key]))
                field = SelectField(name, [validators.Required(gettext("This value is required"))], \
                        description=desc, choices=choices, default=default)
            elif item["type"] == "password":
                field = PasswordField(name, [validators.Required(gettext("This value is required"))], \
                        description=desc, default=default)
            else:
                # time, email, ipv4, ipv6, url
                field = TextField(name, [validators.Required(gettext("This value is required"))], \
                        description=desc, default=default)
            setattr(F, "stat|{0}|{1}".format(cmd, item["key"]), field)
            setattr(F_xpl_stat, "stat|{0}|{1}".format(cmd, item["key"]), field)
    # create the forms
    form = F()
    form_global = F_global()
    form_xpl = F_xpl()
    form_xpl_command = F_xpl_command()
    form_xpl_stat = F_xpl_stat()

    if request.method == 'POST' and form.validate():
        try:
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
            reason = False
            cli = MQSyncReq(app.zmq_context)
            msg = MQMessage()
            msg.set_action('device_types.get')
            msg.add_data('device_type', params['device_type'])
            res = cli.request('manager', msg.get(), timeout=10)
            del cli
            if res is None:
                status = False
                reason = "Manager is not replying to the mq request"
            pjson = res.get_data()
            if pjson is None:
                status = False
                reason = "No data for {0} found by manager".format(params['device_type'])
            pjson = pjson[params['device_type']]
            if pjson is None:
                status = False
                reason = "The json for {0} found by manager is empty".format(params['device_type'])
            with app.db.session_scope():
                res = app.db.add_full_device(params, pjson)
                if res:
                    flash(gettext("Device created succesfully"), 'success')
                else:
                    flash(gettext("Device creation failed"), 'warning')
                    if reason:
                        flash(reason, 'warning')
                # in all case we send an update event (in case of partial success...)
                pub = MQPub(app.zmq_context, 'admin-views')
                pub.send_event('device.update',
                               {"device_id" : res['id'],
                                "client_id" : client_id})
        except:
            app.logger.error(u"Error while creating the device. The error is : {0}".format(traceback.format_exc()))
            flash(gettext("Device creation failed. Please check the logs for more details."), 'warning')
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



def get_brain_content(client_id):
    # get data over MQ
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('butler.scripts.get')
    res = cli.request('butler', msg.get(), timeout=10)
    if res is not None:
        data = res.get_data()
        detail = {}
        try:
            detail[client_id] = data[client_id]
        except KeyError:
            # this can happen if you install a package and don't do a butler reload!
            detail[client_id] = None
    else:
        detail = {}

    # sorting
    detail = json.dumps(detail, sort_keys=True)
    detail = json.loads(detail, object_pairs_hook=OrderedDict)

    # do a post processing on content to add html inside
    for client_id in detail:
        # we skip the learn file
        if client_id in ["learn", "not_understood"]:
            continue
        if detail[client_id]:
            for lang in detail[client_id]:
                idx = 0
                for file in detail[client_id][lang]:
                    content = html_escape(detail[client_id][lang][file])

                    # python objects
                    idx += 1
                    reg = re.compile(r"&gt; object", re.IGNORECASE)
                    content = reg.sub("<button class='btn btn-info' onclick=\"$('#python_object_{0}').toggle();\"><span class='glyphicon glyphicon-paperclip' aria-hidden='true'></span> python object</button><div class='python' id='python_object_{0}' style='display: none'>&gt; object".format(idx), content)

                    reg = re.compile(r"&lt; object", re.IGNORECASE)
                    content = reg.sub("&lt; object</div>", content)

                    # trigger
                    reg = re.compile(r"\+(?P<trigger>.*)", re.IGNORECASE)
                    content = reg.sub("<strong>+\g<trigger></strong>", content)

                    # comments
                    reg = re.compile(r"//(?P<comment>.*)", re.IGNORECASE)
                    content = reg.sub("<em>//\g<comment></em>", content)


                    detail[client_id][lang][file] = content
        else:
            detail[client_id] = ""
    return detail


@app.route('/client/<client_id>/brain')
@login_required
def client_brain(client_id):
    detail = get_client_detail(client_id)
    brain = get_brain_content(client_id)

    return render_template('client_brain.html',
            loop = {'index': 1},
            clientid = client_id,
            client_detail = detail,
            brain = brain,
            mactive="clients",
            active = 'brain'
            )


@app.route('/client/<client_id>/doc')
@login_required
def client_doc(client_id):
    detail = get_client_detail(client_id)

    return render_template('client_doc.html',
            loop = {'index': 1},
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'doc'
            )


@app.route('/client/<client_id>/doc_static/<path:path>')
@login_required
def client_doc_static(client_id, path):
    pkg = client_id.split(".")[0].replace("-", "_")
    root_path = os.path.join(get_packages_directory(), pkg)
    root_path = os.path.join(root_path, "_build_doc/html/")
    if not os.path.isfile(os.path.join(root_path, path)):
        return render_template('client_no_doc.html')
    return send_from_directory(root_path, path)

@app.route('/brain/reload')
@login_required
def brain_reload():
    """ To be called by ajax
        Send a MQ request to reload the butler brain
    """
    try:
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('butler.reload.do')
        res = cli.request('butler', msg.get(), timeout=10)
        if res == None:
            return "Error : the butler did not respond", 500
        return "OK", 200
    except:
        return "Error : {0}".format(traceback.format_exc()), 500


@app.route('/core/<client_id>')
@login_required
def core(client_id):
    tmp = client_id.split(".")
    name = tmp[0].split("-")[1]
    if name == "butler":
        brain = get_brain_content("learn")
        history = get_butler_history()
        client_list = get_clients_list()
        return render_template('core_butler.html',
                loop = {'index': 1},
                clientid = client_id,
                client_list = client_list,
                history = map(json.dumps, history),
                brain = brain,
                mactive="clients",
                active = 'home'
                )
    else:
        return render_template('core.html',
                loop = {'index': 1},
                clientid = client_id,
                mactive="clients",
                active = 'home'
                )


@app.route('/core/<client_id>/butler_learn')
@login_required
def core_butler_learned(client_id):
    brain = get_brain_content("learn")
    return render_template('core_butler_learned.html',
            loop = {'index': 1},
            clientid = client_id,
            brain = brain,
            mactive="clients",
            active = 'learn'
            )

@app.route('/core/<client_id>/butler_not_understood')
@login_required
def core_butler_not_understood(client_id):
    brain = get_brain_content("not_understood")
    return render_template('core_butler_not_understood.html',
            loop = {'index': 1},
            clientid = client_id,
            brain = brain,
            mactive="clients",
            active = 'not_understood'
            )


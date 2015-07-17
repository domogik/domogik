from domogik.admin.application import app, render_template
from flask import request, flash, redirect, Response
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
try:
	from flask.ext.babel import gettext, ngettext
except ImportError:
	from flask_babel import gettext, ngettext
	pass
from flask_login import login_required
try:
    from flask_wtf import Form
except ImportError:
    from flaskext.wtf import Form
    pass
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import Required
from domogik.common.sql_schema import UserAccount

from wtforms.ext.sqlalchemy.orm import model_form
import json
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

@app.route('/scenario')
@login_required
def scenario():
    scenarios = []
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('scenario.list')
    res = cli.request('scenario', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'result' in res:
            res = res['result']
            for scen in res:
                scenarios.append(scen)
    return render_template('scenario.html',
        scenarios = scenarios,
        mactive = "scenario")

@app.route('/scenario/del/<id>')
@login_required
def scenario_del(id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('scenario.delete')
    msg.add_data('cid', id)
    res = cli.request('scenario', msg.get(), timeout=10)
    flash(gettext("Scenario deleted"), "success")
    return redirect("/scenario")
    pass

@app.route('/scenario/edit/<id>', methods=['GET', 'POST'])
@login_required
def scenario_edit(id):
    default_json = '{"type":"dom_condition","id":"1","deletable":false}'
    # laod the json
    if int(id) == 0:
        name = "New scenario"
        jso = default_json
        dis = 0
        desc = None
    else:
        with app.db.session_scope():
            scen = app.db.get_scenario(id)
            jso = scen.json
            dis = scen.disabled
            name = scen.name
            desc = scen.description
            jso.replace('\n', '').replace('\r', '')
    # create a form
    class F(Form):
        sid = HiddenField("id", default=id)
        sname = TextField("Name", default=name, description="Scenario name")
        sdis = BooleanField("disabled", default=dis)
        sdesc = TextField("Description", default=desc)
        sjson = HiddenField("json")
        submit = SubmitField("Send")
        pass
    form = F()

    if request.method == 'POST' and form.validate():
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        if form.sid.data > 0:
            msg.set_action('scenario.update')
        else:
            msg.set_action('scenario.new')
        msg.add_data('name', form.sname.data)
        msg.add_data('json_input', form.sjson.data)
        msg.add_data('cid', form.sid.data)
        msg.add_data('dis', form.sdis.data)
        msg.add_data('desc', form.sdesc.data)
        res = cli.request('scenario', msg.get(), timeout=10)
        flash(gettext("Changes saved"), "success")
        return redirect("/scenario")
        pass
    else:
        # Fetch all known actions
        actions = []
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('action.list')
        res = cli.request('scenario', msg.get(), timeout=10)
        if res is not None:
            res = res.get_data()
            if 'result' in res:
                res = res['result']
                actions = res.keys()
        actions.remove(u'command.CommandAction')
        # Fetch all known tests
        tests = []
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('test.list')
        res = cli.request('scenario', msg.get(), timeout=10)
        if res is not None:
            res = res.get_data()
            if 'result' in res:
                res = res['result']
                tests = res.keys()
        tests.remove(u'sensor.SensorTest')

        # Fetch all known devices
        # per client > device > sensor | command
        devices_per_clients = {}
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('device.get')
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            res = res.get_data()
            if 'devices' in res:
                result = res['devices']
                for device in result:
                    client = device['client_id']
                    name = device['name']
                    if client not in devices_per_clients:
                        devices_per_clients[client] = {}
                    devices_per_clients[client][name] = {}
                    devices_per_clients[client][name]['sensors'] = {}
                    devices_per_clients[client][name]['commands'] = {}
                    for sen in device['sensors']:
                        sen_id = device['sensors'][sen]['id']
                        sen_name = device['sensors'][sen]['name']
                        devices_per_clients[client][name]['sensors'][sen_name] = sen_id
                    for cmd in device['commands']:
                        cmd_id = device['commands'][cmd]['id']
                        cmd_name = device['commands'][cmd]['name']
                        devices_per_clients[client][name]['commands'][cmd_name] = cmd_id

        # Fetch all known datatypes
        datatypes = []
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('datatype.get')
        res = cli.request('manager', msg.get(), timeout=10)
        if res is not None:
            res = res.get_data()
            if 'datatypes' in res:
                res = res['datatypes']
                datatypes = res.keys()
        print(datatypes)

        # ouput
        return render_template('scenario_edit.html',
            mactive = "scenario",
            form = form,
            name = name,
            actions = actions,
            tests = tests,
            devices_per_clients = devices_per_clients,
            datatypes = datatypes,
            jso = jso,
            scenario_id = id)

@app.route('/scenario/blocks/tests')
def scenario_blocks_tests():
    """
        this.setHelpUrl('');
        this.setColour(160);
        this.appendDummyInput()
        .appendField('Time')
            .appendField(new Blockly.FieldTextInput("<cron like timestamp>"), "cron");
        this.setOutput(true, null);
        this.setTooltip('');
        this.setInputsInline(false);
    """
    js = ""
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('test.list')
    res = cli.request('scenario', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'result' in res:
            res = res['result']
            for test, params in res.iteritems():
                print test
                if test == "sensor.SensorTest": continue
                p = []
                jso = ""
                for parv in params:
                    par = parv['name']
                    papp = "this.appendDummyInput().appendField('{0}')".format(parv['description'])
                    if parv['type'] == 'string':
                        jso = '{0}, "{1}": "\'+ block.getFieldValue(\'{1}\') + \'" '.format(jso, par)
                        papp = "{0}.appendField(new Blockly.FieldTextInput('{1}'), '{2}');".format(papp, '', par)
                    elif parv['type'] == 'integer':
                        jso = '{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                        papp = "{0}.appendField(new Blockly.FieldTextInput('{1}'), '{2}');".format(papp, '', par)
                    elif parv['type'] == 'list':
                        jso = '{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                        the_list = parv["values"]  # [[...], [...]]
                        papp = "{0}.appendField(new Blockly.FieldDropdown({1}), '{2}');".format(papp, json.dumps(the_list), par)
                        print(papp)
                    p.append(papp)
                add = """Blockly.Blocks['{0}'] = {{
                            init: function() {{
                                this.setColour(160);
                                this.appendDummyInput().appendField("{0}");
                                {1}
                                this.setOutput(true);
                                this.setInputsInline(false);
                                this.setTooltip('{2}'); 
                                this.contextMenu = false;
                            }}
                        }};
                        """.format(test, '\n'.join(p), parv['description'], jso)
                js = '{0}\n\r{1}'.format(js, add)
    return Response(js, content_type='text/javascript; charset=utf-8')

@app.route('/scenario/blocks/actions')
def scenario_blocks_actions():
    """
        Blockly.Blocks['dom_action_log'] = {
          init: function() {
            this.setColour(160);
            this.appendDummyInput()
            .appendField('Log Message')
                .appendField(new Blockly.FieldTextInput("<message to log>"), "message");
            this.setPreviousStatement(true, "null");
            this.setNextStatement(true, "null");
            this.setTooltip('');
            this.setInputsInline(false);
            this.contextMenu = false;
          }
        };
    """
    js = ""
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('action.list')
    res = cli.request('scenario', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'result' in res:
            res = res['result']
            for act, params in res.iteritems():
                if act == "command.CommandAction": continue
                p = []
                jso = ""
                for par, parv in params['parameters'].iteritems():
                    papp = "this.appendDummyInput().appendField('{0}')".format(parv['description'])
                    if parv['type'] == 'string':
                        jso = '{0}, "{1}": "\'+ block.getFieldValue(\'{1}\') + \'" '.format(jso, par)
                        papp = "{0}.appendField(new Blockly.FieldTextInput('{1}'), '{2}');".format(papp, parv['default'],par)
                    elif parv['type'] == 'integer':
                        jso = '{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                        papp = "{0}.appendField(new Blockly.FieldTextInput('{1}'), '{2}');".format(papp, parv['default'],par)
                    elif parv['type'] == 'list':
                        jso = '{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                        the_list = parv["values"]  # [[...], [...]]
                        papp = "{0}.appendField(new Blockly.FieldDropdown({1}), '{2}');".format(papp, json.dumps(the_list), par)
                    else:
                        papp = "{0};".format(papp)
                    p.append(papp)
                add = """Blockly.Blocks['{0}'] = {{
                        init: function() {{
                            this.setHelpUrl('');
                            this.setColour(160);
                            this.appendDummyInput().appendField("{0}");
                            {1}
                            this.setPreviousStatement(true, "null");
                            this.setNextStatement(true, "null");
                            this.setTooltip('{2}');
                            this.setInputsInline(false);
                        }}
                    }};
                    """.format(act, '\n'.join(p), params['description'], jso)
                js = '{0}\n\r{1}'.format(js, add)
    return Response(js, content_type='text/javascript; charset=utf-8')

@app.route('/scenario/blocks/devices')
def scenario_blocks_devices():
    """
        create a block for each device sensor and command
    """
    js = ""
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('datatype.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'datatypes' in res:
            datatypes = res['datatypes']
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('device.get')
    res = cli.request('dbmgr', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'devices' in res:
            # create a list of the used datatypes in sensors to build only these datatype blocks
            used_datatypes = []
            devices = res['devices']
            for dev in devices:
                client = dev['client_id']
                name = dev['name']

                ### sensors blocks
                for sen in dev['sensors']:
                    p = ""
                    jso = ""
                    sen_id = dev['sensors'][sen]['id']
                    sen_name = dev['sensors'][sen]['name']
                    # determ the output type
                    sen_dt = dev['sensors'][sen]['data_type'] 
                    if sen_dt not in used_datatypes:
                        used_datatypes.append(sen_dt)
                    dt_parent = sen_dt
                    # First, determine the parent type (DT_Number, DT_Bool, ...)
                    while 'parent' in datatypes[dt_parent] and datatypes[dt_parent]['parent'] != None:
                        dt_parent = datatypes[dt_parent]['parent']
                    if dt_parent == "DT_Bool":
                        color = 20
                        output = "\"Boolean\""
                    elif dt_parent == "DT_Number":
                        color = 65
                        output = "\"Number\""
                    else:
                        color = 160
                        output = "\"null\""
                    block_id = "sensor.SensorTest.{0}".format(sen_id)
                    block_description = "{0}@{1}".format(name, client)
                    add = """Blockly.Blocks['{0}'] = {{
                                init: function() {{
                                    this.setColour({5});
                                    this.appendDummyInput().appendField("{2}");
                                    this.appendDummyInput().appendField('Sensor : {1}');
                                    this.setOutput(true, {4});
                                    this.setInputsInline(false);
                                    this.setTooltip('{2}'); 
                                }}
                            }};
                            """.format(block_id, sen_name, block_description, jso, output, color)
                    js = '{0}\n\r{1}'.format(js, add)

                ### commands blocks
                for cmd in dev['commands']:
                    p = ""
                    jso = ""
                    cmd_id = dev['commands'][cmd]['id']
                    cmd_name = dev['commands'][cmd]['name']
                    color = 1;
                    # parse the parameters
                    js_params = ""
                    for param in dev['commands'][cmd]['parameters']:
                        param_key = param['key']
                        param_dt_type = param['data_type']
                        # First, determine the parent type (DT_Number, DT_Bool, ...)
                        dt_parent = param_dt_type
                        while 'parent' in datatypes[dt_parent] and datatypes[dt_parent]['parent'] != None:
                            dt_parent = datatypes[dt_parent]['parent']
                        #if dt_parent == "DT_Bool":
                        #    color = 20
                        #    output = "\"Boolean\""
                        #elif dt_parent == "DT_Number":
                        #    color = 65
                        #    output = "\"Number\""
                        #else:
                        #    color = 160
                        #    output = "\"null\""
                        js_params = """
                                        this.appendDummyInput().appendField("- {0} : ")
                                    """.format(param_key)
                        list_options = None
                        if "labels" in datatypes[param_dt_type]:
                            list_options = datatypes[param_dt_type]['labels']
                        if "values" in datatypes[param_dt_type]:
                            list_options = datatypes[param_dt_type]['values']
                        if list_options != None:
                            print("OPTIONS : {0}".format(list_options))
                            js_list_options = "["
                            for opt in list_options:
                                js_list_options += "['{0}', '{1}'],".format(list_options[opt], opt)
                            js_list_options += "]"
                            js_params += """
                                            .appendField(new Blockly.FieldDropdown({0}), "{1}");
                                        """.format(js_list_options, param_key)
                        else: 
                            param_format = ""
                            if 'format' in datatypes[param_dt_type]:
                                param_format = datatypes[param_dt_type]['format']
                                print("PF={0}".format(param_format))
                                if param_format == None:
                                    param_format = ""
                                else:
                                    param_format = "({0})".format(param_format)
                            js_params += """
                                            .appendField(new Blockly.FieldTextInput(""), "{0}")
                                            .appendField("{1}");
                                        """.format(param_key, param_format)
                    block_id = "command.CommandAction.{0}".format(cmd_id)
                    block_description = "{0}@{1}".format(name, client)
                    add = """Blockly.Blocks['{0}'] = {{
                                init: function() {{
                                    this.setColour({5});
                                    this.appendDummyInput().appendField("{2}");
                                    this.appendDummyInput().appendField('Command : {1}');
                                    this.appendDummyInput().appendField('Parameters : ');
                                    {6}
                                    this.setPreviousStatement(true, "null");
                                    this.setNextStatement(true, "null");
                                    this.setInputsInline(false);
                                    this.setTooltip('{2}'); 
                                }}
                            }};
                            """.format(block_id, cmd_name, block_description, jso, output, color, js_params)
                    js = '{0}\n\r{1}'.format(js, add)

            #for dt_type in used_datatypes:
            for dt_type in datatypes:
                dt_parent = dt_type
                # First, determine the parent type (DT_Number, DT_Bool, ...)
                while 'parent' in datatypes[dt_parent] and datatypes[dt_parent]['parent'] != None:
                    dt_parent = datatypes[dt_parent]['parent']
                if dt_parent == "DT_Bool":
                    color = 20
                    output = "\"Boolean\""
                elif dt_parent == "DT_Number":
                    color = 65
                    output = "\"Number\""
                    input = """
                             this.appendDummyInput().appendField(new Blockly.FieldTextInput(""), "value");
                            """
                else:
                    color = 160
                    output = "\"null\""

                add = """Blockly.Blocks['{0}'] = {{
                            init: function() {{
                                this.setColour({1});
                                this.appendDummyInput().appendField("{0}");
                                {3}
                                this.setTooltip('{0}'); 
                                this.setOutput(true, {2});
                                this.setInputsInline(false);
                            }}
                        }};
                        """.format(dt_type, color, output, input)
                js = '{0}\n\r{1}'.format(js, add)
                

    return Response(js, content_type='text/javascript; charset=utf-8')


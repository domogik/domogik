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
    else:
        with app.db.session_scope():
            scen = app.db.get_scenario(id)
            jso = scen.json
            dis = scen.disabled
            name = scen.name
            jso.replace('\n', '').replace('\r', '')
    # create a form
    class F(Form):
        sid = HiddenField("id", default=id)
        sname = TextField("Name", default=name, description="Scenario name")
        #sdis = BooleanField("disabled", default=dis)
        sjson = HiddenField("json")
        submit = SubmitField("Send")
        pass
    form = F()

    if request.method == 'POST' and form.validate():
        print("Scenario edit > POST")
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        if form.sid.data > 0:
            msg.set_action('scenario.update')
        else:
            msg.set_action('scenario.new')
        msg.add_data('name', form.sname.data)
        msg.add_data('json_input', form.sjson.data)
        msg.add_data('cid', form.sid.data)
        res = cli.request('scenario', msg.get(), timeout=10)
        print res
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

        # TODO : DEL
        # Fetch all known datatypes
        #datatypes = []
        #cli = MQSyncReq(app.zmq_context)
        #msg = MQMessage()
        #msg.set_action('datatype.get')
        #res = cli.request('manager', msg.get(), timeout=10)
        #if res is not None:
        #    res = res.get_data()
        #    if 'datatypes' in res:
        #        res = res['datatypes']
        #        datatypes = res.keys()

        # Fetch all known devices
        # per client > device > sensor
        sensors = {}
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('device.get')
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            res = res.get_data()
            if 'devices' in res:
                devices = res['devices']
                for dev in devices:
                    print(dev['client_id'])
                    client = dev['client_id']
                    name = dev['name']
                    if client not in sensors:
                        sensors[client] = {}
                    sensors[client][name] = {}
                    for sen in dev['sensors']:
                        sen_id = dev['sensors'][sen]['id']
                        sen_name = dev['sensors'][sen]['name']
                        sensors[client][name][sen_name] = sen_id
        print(sensors)

        # ouput
        return render_template('scenario_edit.html',
            mactive = "scenario",
            form = form,
            name = name,
            actions = actions,
            tests = tests,
            sensors = sensors,
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
    print(res)
    if res is not None:
        res = res.get_data()
        if 'result' in res:
            res = res['result']
            print(res)
            for test, params in res.iteritems():
                print params
                p = []
                jso = ""
                for parv in params:
                    print("TYPE={0}".format(parv['type']))
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
                        print(papp)
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


@app.route('/scenario/blocks/datatypes')
def scenario_blocks_datatypes():
    """
        retrieve all known datatypes and for each, generate a bockly block in json
    """
    js = "                        "
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('datatype.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'datatypes' in res:
            datatypes = res['datatypes']
            for dt_type, params in datatypes.iteritems():
                # TODO : remove this filter
                #if dt_type not in ['DT_Temp', 'DT_Humidity', 'DT_Number']:
                #    continue
                
                print(dt_type)
                dt_parent = dt_type
                # First, determine the parent type (DT_Number, DT_Bool, ...)
                while 'parent' in datatypes[dt_parent] and datatypes[dt_parent]['parent'] != None:
                    dt_parent = datatypes[dt_parent]['parent']
                    print("..{0}".format(dt_parent))
 
                # Then, start to build the block
                block = {
                           "id" : "{0}".format(dt_type),
                           "message0" : "{0}".format(dt_type),
                           "args0" : [
                             {
                               "type" : "field_dropdown",
                               "name" : "NAME",
                               "options" : []
                             },
                             {
                               "type" : "input_value",
                               "name" : "NAME",
                               "check" : "Array"
                             }
                           ],
                           "colour" : 130,
                           "tooltip" : "",
                           "helpUrl" : ""
                         }
                block['args0'][0]['options'].append(['a', 'A'])
                block['args0'][0]['options'].append(['b', 'B'])
                js += "var {0}_json = {1};".format(dt_type, json.dumps(block))
                js += """
                         Blockly.Blocks['{0}'] = {{
                             init: function() {{
                                 this.jsonInit({0}_json);
                             }}
                         }};
                         """.format(dt_type)
              
    return Response(js, content_type='text/javascript; charset=utf-8')



@app.route('/scenario/blocks/sensors')
def scenario_blocks_sensors():
    """
        create a block for each device sensor
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
            devices = res['devices']
            for dev in devices:
                client = dev['client_id']
                name = dev['name']
                for sen in dev['sensors']:
                    p = ""
                    jso = ""
                    sen_id = dev['sensors'][sen]['id']
                    sen_name = dev['sensors'][sen]['name']
                    # determ the output type
                    sen_dt = dev['sensors'][sen]['data_type'] 
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
                    block_description = "{0} - {1}".format(name, sen_name)
                    p = """
                                this.appendDummyInput().appendField('{0}').appendField(new Blockly.FieldDropdown([["{1}", "{2}"]]), 'sensor.sensor_id');
                        """.format("Sensor : ", sen_name, sen_id)
                    add = """Blockly.Blocks['{0}'] = {{
                                init: function() {{
                                    this.setColour({5});
                                    this.appendDummyInput().appendField("{2}");
                                    {1}
                                    this.setOutput(true, {4});
                                    this.setInputsInline(false);
                                    this.setTooltip('{2}'); 
                                    this.contextMenu = false;
                                }}
                            }};
                            """.format(block_id, p, block_description, jso, output, color)
                    js = '{0}\n\r{1}'.format(js, add)
    return Response(js, content_type='text/javascript; charset=utf-8')


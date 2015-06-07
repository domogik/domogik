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
        # ouput
        return render_template('scenario_edit.html',
            mactive = "scenario",
            form = form,
            name = name,
            actions = actions,
            tests = tests,
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
                    p.append(papp)
                add = """Blockly.Blocks['{0}'] = {{
                            init: function() {{
                                this.setColour(160);
                                this.appendDummyInput().appendField("{0}");
                                {1}
                                this.setOutput(true);
                                this.setInputsInline(true);
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

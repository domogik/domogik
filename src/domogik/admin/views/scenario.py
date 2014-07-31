from domogik.admin.application import app
from flask import render_template, request, flash, redirect, Response
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
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
    return render_template('scenario.html')

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
            res = json.loads(res['result'])
            for test, params in res.iteritems():
                print ""
                p = []
                jso = ""
                for par, parv in params['parameters'].iteritems():
                    par = parv['expected'].keys()[0]
                    parv = parv['expected'][par]
                    print par
                    print parv
                    papp = "this.appendDummyInput().appendField('{0}')".format(parv['description'])
                    if parv['type'] == 'string':
                        jso = '{0}, "{1}": "\'+ block.getFieldValue(\'{1}\') + \'" '.format(jso, par)
                        papp = "{0}.appendField(new Blockly.FieldTextInput('{1}', '{2}'));".format(papp, parv['default'],par)
                    elif parv['type'] == 'integer':
                        jso = '{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                        papp = "{0}.appendField(new Blockly.FieldTextInput('{1}', '{2}'));".format(papp, parv['default'],par)
                    p.append(papp)
                add = """Blockly.Blocks['{0}'] = {{
                            init: function() {{
                                this.setHelpUrl('');
                                this.setColour(160);
                                this.appendDummyInput().appendField("{0}");
                                {1}
                                this.setOutput(true, null);
                                this.setInputsInline(true);
                                this.setTooltip('{2}'); 
                            }}
                        }};
                        Blockly.Domogik['{0}'] = function(block) {{
                          var code = '{{"id": ' + block.id + ',"type": "{0}"{3}}}';
                          return [code, Blockly.Domogik.ORDER_NONE];
                        }};
                        """.format(test, '\n'.join(p), params['description'], jso)
                js = '{0}\n\r{1}'.format(js, add)
    return Response(js, content_type='text/javascript; charset=utf-8')

@app.route('/scenario/blocks/actions')
def scenario_blocks_actions():
    js = 'actions'
    return Response(js, content_type='text/javascript; charset=utf-8')

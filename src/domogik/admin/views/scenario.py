from domogik.admin.application import app, render_template, timeit
from flask import request, flash, redirect, Response, jsonify
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass
from flask_login import login_required
try:
    from flask_wtf import FlaskForm
except ImportError:
    from flaskext.wtf import FlaskForm
    pass
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import Required
from domogik.common.sql_schema import UserAccount
from domogik.common.cron import CronExpression
from domogik.common.plugin import LIST_CLIENT_STATUS, STATUS_HBEAT

from wtforms.ext.sqlalchemy.orm import model_form
import json
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote
import traceback
from operator import itemgetter
from collections import OrderedDict
import os


@app.route('/scenario')
@login_required
@timeit
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
                if scen['disabled']:
                    scen['endis'] = 'Disabled'
                else:
                    scen['endis'] = 'Enabled'
                scenarios.append(scen)
    scenarios = sorted(scenarios, key=itemgetter("name"))
    return render_template('scenario.html',
        scenarios = scenarios,
        mactive = u"scenario")

@app.route('/scenario/examples')
@login_required
@timeit
def scenario_examples():
    return render_template('scenario_examples.html',
        mactive = u"scenario")

@app.route('/scenario/del/<id>')
@login_required
@timeit
def scenario_del(id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('scenario.delete')
    msg.add_data('cid', id)
    res = cli.request('scenario', msg.get(), timeout=10)
    flash(gettext(u"Scenario deleted"), u"success")
    return redirect(u"/scenario")
    pass

@app.route('/scenario/enable/<id>')
@login_required
@timeit
def scenario_enable(id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('scenario.enable')
    msg.add_data('cid', id)
    res = cli.request('scenario', msg.get(), timeout=10)
    flash(gettext(u"Scenario enabled"), u"success")
    return redirect(u"/scenario")
    pass

@app.route('/scenario/disable/<id>')
@login_required
@timeit
def scenario_disable(id):
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('scenario.disable')
    msg.add_data('cid', id)
    res = cli.request('scenario', msg.get(), timeout=10)
    flash(gettext(u"Scenario disabled"), u"success")
    return redirect(u"/scenario")
    pass


@app.route('/scenario/clone/<id>', methods=['GET', 'POST'])
@app.route('/scenario/edit/<id>', methods=['GET', 'POST'])
@login_required
@timeit
def scenario_edit(id):
    if str(request.path).find('/clone/') > -1:
        clone = True
    else:
        clone = False
    default_json = ''
    # laod the json
    if int(id) == 0:
        name = u""
        jso = default_json
        dis = 0
        desc = None
        behav = 'wait'
    else:
        with app.db.session_scope():
            scen = app.db.get_scenario(id)
            jso = scen.json
            dis = scen.disabled
            name = scen.name
            desc = scen.description
            behav = scen.behavior if scen.behavior !='' else 'wait'
            jso = jso.replace('\n', '').replace('\r', '').replace("'", "\\'").replace('"', '\\"')
            if clone:
                id = 0
                name = u""
    # create a form
    class F(FlaskForm):
        sid = HiddenField("id", default=id)
        sname = TextField(gettext("Name"), [Required()], default=name, description=gettext(u"Scenario name"))
        sdis = BooleanField(gettext("Disable"), default=dis, description=gettext(u"Disabling a scenario avoid to delete it if you temporary want it not to run"))
        sbehav = SelectField(gettext("Behavior threading"), choices=[('wait', gettext(u'Finish current and do next (default and advisable)')),
                                                ('eval', gettext(u'Stop current and do next')),
                                                ('remove', gettext(u'Finish current and not do next')),
                                                ('parallel', gettext(u'Do them all in parallel (unsafe risk of conflict)'))],
                             default= behav, description=gettext(u"Defines the behavior in case of simultaneous execution of the scenario"),
                             )
        sdesc = TextAreaField(gettext("Description"), default=desc)
        sjson = HiddenField("json")
        submit = SubmitField(u"Send")
        pass
    form = F()
    print(" ***** form : {0}".format(form.data))

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
        msg.add_data('behav', form.sbehav.data)
        print("+++++++++++++++++++++")
        print(msg.get_data())
        res = cli.request('scenario', msg.get(), timeout=10)
        if res:
            data = res.get_data()
            if 'result' in data:
                if 'status' in data['result']:
                    if data['result']['status'] == 'OK':
                        flash(gettext(u"Changes saved"), "success")
                    else:
                        if 'msg' in data['result']:
                            flash(data['result']['msg'], "error")
                        else:
                            flash(gettext(u"Changes not saved"), "error")
                else:
                    flash(gettext(u"Unexpected result from scenario manager"), "warning")
            else:
                flash(gettext(u"Unexpected result from scenario manager"), "warning")
        else:
            flash(gettext(u"Unexpected result from scenario manager"), "warning")
        return redirect("/scenario")
        pass
    else:
        # Get the javascript for all blocks and data to build blockly categories
        blocks_js, constantes, tests, actions, locations, clients_status, devices_per_clients, used_datatypes = scenario_blocks_js()

        # ouput
        return render_template('scenario_edit.html',
            mactive = "scenario",
            form = form,
            name = name,
            blocks_js = blocks_js,
            constantes = constantes,
            actions = actions,
            tests = tests,
            locations = locations,
            clients_status = clients_status,
            devices_per_clients = devices_per_clients,
            datatypes = used_datatypes,
            jso = jso,
            scenario_id = id)

@app.route('/scenario/cronruletest/checkdate')
@login_required
@timeit
def scenario_croncheckdate():
    data = {}
    try :
        for k, v in request.args.items():
            data[k] = v
        data['date'] = tuple ([int(i) for i in data['date'].split(',')])
        try :
            job = CronExpression(data['cronrule'])
            if not job.isValidate() :
                return jsonify(result='error', reply="", content = {'error': gettext(u"Cron rule is not valid.")})
            now = job.check_trigger_now()
            istriggered = job.check_trigger(data['date'])
        except :
            print(traceback.format_exc())
            return jsonify(result='error', reply="", content = {'error': gettext(u"Error in cron rule, can't trigger it.")})
        return jsonify(result='success', reply="", content = {'error': "", 'result': {'now': now, 'date': istriggered}})
    except :
        print(traceback.format_exc())
        jsonify(result='error', reply="", content = {'error': gettext(u"Cron checking, bad request parameters.")})

@app.route('/scenario/cronruletest/getephemdate')
@login_required
@timeit
def scenario_croncephemdate():
    data = {}
    try :
        for k, v in request.args.items():
            data[k] = v
        data['date'] = tuple ([int(i) for i in data['date'].split(',')])
        try :
            job = CronExpression(data['cronrule'])
            dates = []
            dates.append(job.get_next_date_special(data['date']))
            for i in range(1, int(data['number'])):
                nDate = (dates[i-1][0], dates[i-1][1], dates[i-1][2]+1, dates[i-1][3], dates[i-1][4])
                dates.append(job.get_next_date_special(nDate))
        except :
            print(traceback.format_exc())
            return jsonify(result='error', reply="", content = {'error': gettext(u"Error in cron rule, can't get next date.")})
        return jsonify(result='success', reply="", content = {'error': "", 'result': {'dates': dates, 'timezone': job.timeZone.zone}})
    except :
        print(traceback.format_exc())
        jsonify(result='error', reply="", content = {'error': gettext(u"Ephemeris next date, bad request parameters.")})

def scenario_blocks_js():
    """
        Generate all the dynamic Blockly blocs : tests, commands, devices sensors and commands, datatype
        Generate also the category structure for blockly

        This is a big big function to avoid doing several time the same MQ req/rep actions (and loose some time)
    """

    ### first, do all MQ related calls

    # CODE for #85
    # scenarios
    #scenarios = {}
    #cli = MQSyncReq(app.zmq_context)
    #msg = MQMessage()
    #msg.set_action('scenario.list')
    #res = cli.request('scenario', msg.get(), timeout=10)
    #if res is not None:
    #    res = res.get_data()
    #    if 'result' in res:
    #        scenarios = res['result']
    #else:
    #    print("Error : no scenarios found!")
    #    scenarios = {}

    # scenarios tests (cron, text in page, ...)
    scenario_tests = {}
    tests = []
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('test.list')
    res = cli.request('scenario', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'result' in res:
            scenario_tests = res['result']
    else:
        print(u"Error : no scenario tests found!")
        scenario_tests = {}
#   remove cron.CronTest from other sensors list
    del scenario_tests['cron.CronTest']

#    tests = scenario_tests.keys()
    tests = list(scenario_tests)
    try:
        tests.remove(u'sensor.SensorTest')
        tests.remove(u'sensor.SensorValueDummy')
        tests.remove(u'sensor.SensorValue')
        tests.remove(u'sensor.SensorTestDummy')
        tests.remove(u'client_status.StatusTest')
        tests.remove(u'client_status.SatusValue')
        tests.remove(u'client_status.StatusTestDummy')
        tests.remove(u'client_status.StatusValueDummy')
        tests.remove(u'location.LocationTest')
        tests.remove(u'location.LocationValueDummy')
        tests.remove(u'location.LocationValue')
        tests.remove(u'location.LocationTestDummy')
        tests.remove(u'geoinlocation.GeoInLocTestDummy')
    except ValueError:
        pass

    # scenarios actions (log, call url, ...)
    scenario_actions = {}
    actions = []
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('action.list')
    res = cli.request('scenario', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'result' in res:
            scenario_actions = res['result']
    else:
        print(u"Error : no scenario actions found!")
        scenario_actions = {}

    actions = list(scenario_actions)
    try:
        actions.remove(u'scenario.endis')
    except ValueError:
        pass
    try:
        actions.remove(u'command.CommandAction')
    except ValueError:
        pass
    # datatypes
    datatypes = {}
    used_datatypes = {}
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('datatype.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'datatypes' in res:
            datatypes = res['datatypes']
    else:
        print(u"Error : no scenario datatypes found!")
        datatypes = {}

    # devices
    with app.db.session_scope():
        devices = app.db.list_devices()

    # clients
    msg = MQMessage()
    msg.set_action('client.list.get')
    res2 = cli.request('manager', msg.get(), timeout=10)
    if res2 is not None:
        clients  = res2.get_data()
    else:
        print(u"Error : no scenario clients found!")
        clients = {}

    list_status = []
    for st in LIST_CLIENT_STATUS :
        list_status.append([st, st])
    ### Now start the javascript generation
    js = ""
    ### constantes
    output = "[\"String\",\"ClientStatus\"]"
    add = u"""Blockly.Blocks['client_status'] = {{
                        init: function() {{
                            this.setColour(240);
                            this.appendDummyInput("STATUS").appendField(new Blockly.FieldDropdown({0}), "TEXT");
                            this.setTooltip('Client status value');
                            this.setOutput(true, {1});
                            this.setInputsInline(false);
                        }}
                    }};""".format(json.dumps(list_status), output)
    js = u'{0}\n\r{1}'.format(js, add)
    constantes = [u"client_status"]
    ### tests
#    print(u"ITEMS={0}".format(scenario_tests.items()))

    # Check if there are some errors in the python tests files
    # TODO : Improve error handling
    for key, value in scenario_tests.items():
        if key == "status":
            print(u"Error : {0}".format(scenario_tests.items()))

    for test, params in scenario_tests.items():
        if test == "sensor.SensorTest": continue
        p = []
        jso = u""
        if params['blockly'] != "":
            add = u"""Blockly.Blocks['{0}'] = {{
                        init: function() {{
                            {1}
                        }}
                    }};
                    """.format(test, params['blockly'])
            js = u'{0}\n\r{1}'.format(js, add)
        else:
            #for parv in params:
            print(u"TEST={0}".format(test))
            output = params['output']
            for parv in params['parameters']:
                print(u"Parv : {0}".format(parv))
                par = parv['name']
                papp = u"this.appendDummyInput().appendField('{0} : ')".format(parv['description'])
                if parv['name'] =='cron.cron':
                    papp = u"{0}.appendField(new CronFielDialog('/static/images/icon-edit.png', 20, 20, '*', true, '{1}'));".format(papp, par)
                elif parv['type'] == 'string':
                    jso = u'{0}, "{1}": "\'+ block.getFieldValue(\'{1}\') + \'" '.format(jso, par)
                    papp = u"{0}.appendField(new Blockly.FieldTextInput('{1}'), '{2}');".format(papp, '', par)
                elif parv['type'] == 'integer':
                    jso = u'{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                    papp = u"{0}.appendField(new Blockly.FieldTextInput('{1}'), '{2}');".format(papp, '', par)
                elif parv['type'] == 'list':
                    jso = u'{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                    the_list = parv["values"]  # [[...], [...]]
                    papp = u"{0}.appendField(new Blockly.FieldDropdown({1}), '{2}');".format(papp, json.dumps(the_list), par)
                p.append(papp)
            add = u"""Blockly.Blocks['{0}'] = {{
                        init: function() {{
                            this.setColour(160);
                            this.appendDummyInput().appendField("{2}");
                            {1}
                            this.setOutput(true,{4});
                            this.setInputsInline(false);
                            this.setTooltip("{2}");
                            this.contextMenu = false;
                        }}
                    }};
                    """.format(test, '\n'.join(p), params['description'], jso, output)
            js = u'{0}\n\r{1}'.format(js, add)


    ### actions
    print("actions : {0}".format(scenario_actions))
    for act, params in scenario_actions.items():
        if act == "command.CommandAction": continue
        p = []
        jso = u""
        print("action : {0} = {1}".format(act,  params))
        for par, parv in params['parameters'].items():
            papp = u"this.appendValueInput(\"{0}\").setAlign(Blockly.ALIGN_RIGHT)".format(par)
            papp += u".appendField(\"{0}\")".format(parv['description'])
            if parv['type'] == 'string':
                papp += ".setCheck(\"String\")"
            elif parv['type'] == 'integer':
                papp += ".setCheck(\"Number\")"
            elif parv['type'] == 'list':
                papp += ".setCheck(\"Array\")"
            #elif parv['type'] == 'external':
                #jso = u'{0}, "{1}": \'+ block.getFieldValue(\'{1}\') + \' '.format(jso, par)
                #papp = u"{0}; this.appendValueInput(\'{1}\').setCheck(null);".format(papp, par)
            #    inline = "true"
            else:
                papp += ".setCheck(\"Any\")"
                papp += u";"
            p.append(papp)
        add = u"""Blockly.Blocks['{0}'] = {{
                init: function() {{
                    this.setHelpUrl('');
                    this.setColour(160);
                    this.appendDummyInput().appendField("{2}");
                    {1}
                    this.setPreviousStatement(true, "null");
                    this.setNextStatement(true, "null");
                    this.setTooltip("{2}");
                }}
            }};
            """.format(act, '\n'.join(p), params['description'])
        js = u'{0}\n\r{1}'.format(js, add)

    ### clients status
    clients_status = {}
    # first, get the parameters
    status_usage = []
    for test, sensor_params in scenario_tests.items():
        if test == "client_status.StatusTest":
            for buf in sensor_params["parameters"]:
                if buf["name"] == "usage.usage":
                    status_usage = buf["values"]
            break
    for clientId in clients:
        try:
            if clients[clientId]['type'] == 'core':
                color = 240
            elif clients[clientId]['type'] == 'plugin':
                color = 170
            elif clients[clientId]['type'] == 'interface':
                color = 290
            else :
                color = 345
            if clients[clientId]['type'] in clients_status:
                clients_status[clients[clientId]['type']].append(clientId)
            else :
                clients_status[clients[clientId]['type']] = [clientId]
            ### Generate parameters
            the_list = status_usage
            papp = u"this.appendDummyInput().appendField(\"Mode \").appendField(new Blockly.FieldDropdown({0}, sensorUsageChange), '{1}');".format(json.dumps(the_list), "usage.usage");
            output = "\"ClientStatus\""
            ### Create the block
            block_id = u"client_status.StatusTest.{0}".format(clientId)
            block_description = u"status@{0}".format(clientId)
            add = u"""Blockly.Blocks['{0}'] = {{
                        init: function() {{
                            this.setColour({4});
                            this.appendDummyInput().appendField("{1}");
                            {5}
                            this.setOutput(true, {3});
                            this.setInputsInline(false);
                            this.setTooltip("{1}");
                        }}
                    }};
                    """.format(block_id, block_description, jso, output, color, papp)
            js = u'{0}\n\r{1}'.format(js, add)
        except:
            print(u"ERROR while looking on a client status : {0}".format(traceback.format_exc()))
    ### devices sensors and commands
    devices_per_clients = {}
    for dev in devices:
        try:
            client = dev['client_id']
            name = dev['name']
            if client not in devices_per_clients:
                devices_per_clients[client] = {}

            # if another device with the same name exists, add a suffix to display all of them
            newname = name
            idx = 1
            while newname in devices_per_clients[client]:
                newname = u"{0} ({1})".format(name, idx)
                idx += 1
            name = newname

            devices_per_clients[client][name] = {}
            devices_per_clients[client][name]['sensors'] = {}
            devices_per_clients[client][name]['commands'] = {}

            ### sensors blocks
            # first, get the parameters
            sensor_usage = []
            for test, sensor_params in scenario_tests.items():
                if test == "sensor.SensorTest":
                    for buf in sensor_params["parameters"]:
                        if buf["name"] == "usage.usage":
                            sensor_usage = buf["values"]
                    break

            # then, build the blocks
            for sen in dev['sensors']:
                p = u""
                jso = u""
                sen_id = dev['sensors'][sen]['id']
                sen_name = dev['sensors'][sen]['name']
                devices_per_clients[client][name]['sensors'][sen_name] = sen_id
                # determ the output type
                sen_dt = dev['sensors'][sen]['data_type']
                # First, determine the parent type (DT_Number, DT_Bool, ...)
                dt_parent = sen_dt
                try:
                    while 'parent' in datatypes[dt_parent] and datatypes[dt_parent]['parent'] != None:
                        dt_parent = datatypes[dt_parent]['parent']
                except KeyError:
                    print(u"Error : the datatype of the sensor '{0}' is not known!".format(sen))
                # store it in the used
                if dt_parent not in used_datatypes:
                    used_datatypes[dt_parent] = []
                if sen_dt not in used_datatypes[dt_parent]:
                    used_datatypes[dt_parent].append(sen_dt)
                # create the block
                if dt_parent == "DT_Bool":
                    color = 20
                    output = "\"Boolean\""
                elif dt_parent == "DT_Number":
                    color = 65
                    output = "\"Number\""
                elif sen_dt == "DT_Time":
                    color = 65
                    output = "\"Number\""
                elif sen_dt == "DT_String":
                    color = 160
                    output = "\"String\""
                else:
                    color = 210
                    output = "\"null\""

                output = "[{0},\"{1}\"{2}]".format(output, sen_dt,",\"{0}\"".format(dt_parent) if sen_dt != dt_parent else "")
                ### Generate parameters
                the_list = sensor_usage
                papp = u"this.appendDummyInput().appendField(\"Mode \").appendField(new Blockly.FieldDropdown({0}, sensorUsageChange), '{1}');".format(json.dumps(the_list), "usage.usage");

                ### Create the block
                block_id = u"sensor.SensorTest.{0}".format(sen_id)
                block_description = u"{0}@{1}".format(name, client)
                add = u"""Blockly.Blocks['{0}'] = {{
                            init: function() {{
                                this.setColour({5});
                                this.appendDummyInput().appendField("{2}");
                                this.appendDummyInput().appendField("Sensor : {1} ({6})");
                                {7}
                                this.setOutput(true, {4});
                                this.setInputsInline(false);
                                this.setTooltip("{2}");
                            }}
                        }};
                        """.format(block_id, sen_name, block_description, jso, output, color, sen_dt, papp)
                js = u'{0}\n\r{1}'.format(js, add)

            ### commands blocks
            for cmd in dev['commands']:
                p = u""
                jso = u""
                cmd_id = dev['commands'][cmd]['id']
                cmd_name = dev['commands'][cmd]['name']
                devices_per_clients[client][name]['commands'][cmd_name] = cmd_id
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
                    if dt_parent not in used_datatypes:
                        used_datatypes[dt_parent] = []
                    if param_dt_type not in used_datatypes[dt_parent]:
                        used_datatypes[dt_parent].append(param_dt_type)
                    # Build the format
                    param_format = u""
                    if 'format' in datatypes[param_dt_type]:
                        param_format = datatypes[param_dt_type]['format']
                        if param_format is not None:
                            param_format = u"({0})".format(param_format)
                    # Try to build a fieldDropDown list
                    list_options = None
                    if "labels" in datatypes[param_dt_type]:
                        list_options = datatypes[param_dt_type]['labels']
                    if "values" in datatypes[param_dt_type]:
                        list_options = datatypes[param_dt_type]['values']
                    # start building the inputs
                    if list_options != None:
                        js_list_options = u"["
                        for opt in sorted(list_options):
                            js_list_options += u"['{1} - {0}', '{1}'],".format(list_options[opt], opt)
                        js_list_options += u"]"
                        js_params += u"""this.appendDummyInput().setAlign(Blockly.ALIGN_RIGHT).appendField("- {0} : ")
                                        .appendField(new Blockly.FieldDropdown({1}), "{0}");
                                    """.format(param_key, js_list_options)
                    elif param_dt_type == "DT_ColorRGBHexa":
                        # Color RGB Hexa
                        js_params += u"""this.appendDummyInput().setAlign(Blockly.ALIGN_RIGHT).appendField("- {0} : ")
                                        .appendField(new Blockly.FieldColour(""), "{0}")
                                    """.format(param_key)
                    elif dt_parent == "DT_Number":
                        # numebr input
                        input = "[\"Number\",\"{0}\"{1}]".format(param_dt_type,",\"{0}\"".format(dt_parent) if param_dt_type != dt_parent else "")
                        js_params += u"""this.appendValueInput("{0}").setAlign(Blockly.ALIGN_RIGHT).appendField("- {0} : ").setCheck({1});
                                    """.format(param_key, input)
                    else:
                        # default case : text input field
                        input = "[\"String\",\"{0}\"{1}]".format(param_dt_type,",\"{0}\"".format(dt_parent) if param_dt_type != dt_parent else "")
                        js_params += u"""this.appendValueInput("{0}").setAlign(Blockly.ALIGN_RIGHT).appendField("- {0} : ").setCheck({1});
                                    """.format(param_key, input)
                block_id = u"command.CommandAction.{0}".format(cmd_id)
                block_description = u"{0}@{1}".format(name, client)
                add = u"""Blockly.Blocks['{0}'] = {{
                            init: function() {{
                                this.setColour({5});
                                this.appendDummyInput().appendField("{2}");
                                this.appendDummyInput().appendField("Command : {1}");
                                {6}
                                this.setPreviousStatement(true, "null");
                                this.setNextStatement(true, "null");
                                this.setInputsInline(false);
                                this.setTooltip("{2}");
                            }}
                        }};
                        """.format(block_id, cmd_name, block_description, jso, output, color, js_params)
                js = u'{0}\n\r{1}'.format(js, add)
        except:
            print(u"ERROR while looking on a device : {0}".format(traceback.format_exc()))

    #### Location
    with app.db.session_scope():
        locations = app.db.get_all_location()
    list_locations = {}
    for loc in locations:
        try:
            list_locations[loc.id] = {'ishome': loc.isHome, 'type': loc.type, 'name': loc.name}
            ### Generate parameters
            papp = ""
            color = 160
            output = "\"null\""
            loc_dt="DT_CoordD"
            ### Create the block
            block_id = u"location.LocationTest.{0}".format(loc.id)
            block_description = u"@{0}{1}".format(loc.name, ' (Home)' if loc.isHome else '')
            add = u"""Blockly.Blocks['{0}'] = {{
                        init: function() {{
                            this.setColour({3});
                            this.appendDummyInput().appendField("{1}");
                            this.setOutput(true,["location.LocationTest"]); /*, {2}); */
                            this.setInputsInline(false);
                            this.setTooltip("{1}");
                        }}
                    }};
                    """.format(block_id, block_description, output, color, loc_dt)
            js = u'{0}\n\r{1}'.format(js, add)
        except:
            print(u"ERROR while looking on a location : {0}".format(traceback.format_exc()))


    #### datatypes
    for dt_parent, dt_types in used_datatypes.items():
        for dt_type in dt_types:
#            print(u"{0} => {1}".format(dt_parent, dt_type))
            if dt_parent == "DT_Bool":
                color = 20
                output = "Boolean"
                opt = "["
                for lab in sorted(datatypes[dt_type]['labels']):
                    opt += u"['{1} - {0}', '{1}'],".format(datatypes[dt_type]['labels'][lab], lab)
                opt += "]"
                input = """
                         this.appendDummyInput().appendField(new Blockly.FieldDropdown({0}), "BOOL");
                        """.format(opt)
            elif dt_parent == "DT_Number":
                color = 65
                output = "Number"
                input = """
                         this.appendDummyInput().appendField(new Blockly.FieldTextInput(""), "NUM");
                        """
            elif dt_parent == "DT_String" and dt_type == "DT_ColorRGBHexa":
                color = 65
                output = "null"
                input = """
                         this.appendDummyInput().appendField(new Blockly.FieldColour(""), "COLOUR");
                        """
            else:
                # Try to build a fieldDropDown list
                list_options = None
                if "labels" in datatypes[dt_type]:
                    list_options = datatypes[dt_type]['labels']
                elif "values" in datatypes[dt_type]:
                    list_options = datatypes[dt_type]['values']
                if list_options != None:
                    js_list_options = u"["
                    for opt in sorted(list_options):
                        js_list_options += u"['{1} - {0}', '{1}'],".format(list_options[opt], opt)
                    js_list_options += u"]"
                    color = 160
                    output = "String"
                    input = u"""this.appendDummyInput().appendField(new Blockly.FieldDropdown({0}), "TEXT");
                                """.format(js_list_options)
                else:
                    color = 160
                    output = "null"
                    input = """
                             this.appendDummyInput().appendField(new Blockly.FieldTextInput(""), "TEXT");
                        """
            output = "[\"{0}\",\"{1}\"{2}]".format(output, dt_type,",\"{0}\"".format(dt_parent) if dt_type != dt_parent else "")

            add = """Blockly.Blocks['{0}'] = {{
                        init: function() {{
                            this.setColour({1});
                            this.appendDummyInput().appendField("{0}");
                            {3}
                            this.setTooltip("{0}");
                            this.setOutput(true, {2});
                            this.setInputsInline(false);
                        }}
                    }};
                    """.format(dt_type, color, output, input)
            js = u'{0}\n\r{1}'.format(js, add)

    # CODE for #85
    # add the scenario enable/disable block
    #for scen in scenarios:
    #    for endis in ['Enable', 'Disable']:
    #        block_id = "scenario.{1}.{0}".format(scen['cid'], endis)
    #        block_description = "{0} scenario".format(endis)
    #        add = u"""Blockly.Blocks['{0}'] = {{
    #                init: function() {{
    #                    this.setColour(5);
    #                    this.appendDummyInput().appendField("{1}");
    #                    this.appendDummyInput().appendField("Scenario : {2}");
    #                    this.setPreviousStatement(true, "null");
    #                    this.setNextStatement(true, "null");
    #                    this.setInputsInline(false);
    #                    this.setTooltip("{1}");
    #                }}
    #            }};
    #            """.format(block_id, block_description, scen['name'])
    #        js = u'{0}\n\r{1}'.format(js, add)


    # do some sorting
    devices_per_clients = json.dumps(devices_per_clients, sort_keys=True)
    devices_per_clients = json.loads(devices_per_clients, object_pairs_hook=OrderedDict)
    tests = sorted(tests)
    actions = sorted(actions)

    # return values
#    print("*****************************************************************")
#    print("*****************************************************************")
#    print(js)
#    print("************************* TESTS ************************************")
#    print(tests)
#    print("************************* ACTIONS *************************************")
#    print(actions)
#    print("************************* LIST_LOCATIONS *************************************")
#    print(list_locations)
#    print("************************* DEVICES *************************************")
#    print(devices_per_clients)
#    print("************************* DATATYPES *************************************")
#    print(used_datatypes)
    return js, constantes, tests, actions, list_locations, clients_status, devices_per_clients, used_datatypes

from domogik.admin.application import app, render_template
from flask import request, flash, redirect
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass

@app.route('/timeline')
@app.route('/timeline/')
@login_required
def timeline():
    return timeline_generic()

@app.route('/timeline/device/<int:device_id>')
@login_required
def timeline_device(device_id):
    return timeline_generic(the_device_id = device_id)

def timeline_generic(the_device_id = None, the_client_id = None, asDict = False):

    # datatypes
    datatypes = {}
    used_datatypes = []
    cli = MQSyncReq(app.zmq_context)
    msg = MQMessage()
    msg.set_action('datatype.get')
    res = cli.request('manager', msg.get(), timeout=10)
    if res is not None:
        res = res.get_data()
        if 'datatypes' in res:
            datatypes = res['datatypes']
    else:
        print("Error : no datatypes found!")
        datatypes = {}


    # timeline
    with app.db.session_scope():
        timeline = []
        data = app.db.get_timeline(device_id = the_device_id, client_id = the_client_id)
        previous_device_id = 0
        previous_date = None
        sensors_changes_for_the_device = []
        has_history = False
        for elt in data:
            print(elt)
            (device_name, device_id, client, sensor_name, sensor_dt_type, sensor_id, date_of_value, value) = elt
   
            if sensor_dt_type in datatypes:
                if "unit" in datatypes[sensor_dt_type]:
                    unit = datatypes[sensor_dt_type]["unit"]
                else:
                    unit = None
            # datatype not known : new plugin with an old datatype file on domogik side.
            # this should happen only in dev mode
            else:
                datatypes[sensor_dt_type] = None
                unit = None

            if device_id == previous_device_id and date_of_value == previous_date:
                pass
            else:
                if previous_device_id != 0:
                    timeline.append({ "datetime" : previous_date,
                                      "date" : previous_date.date(),
                                      "time" : previous_date.time(),
                                      "device_name" : previous_device_name,
                                      "device_id" : previous_device_id,
                                      "client" : previous_client,
                                      "sensors_changes" : sensors_changes_for_the_device
                                    })
                sensors_changes_for_the_device = []

            sensors_changes_for_the_device.append({"sensor_name" : sensor_name,
                                                   "dt_type" : sensor_dt_type,
                                                   "unit" : unit,
                                                   "value" : value})
            previous_device_id = device_id
            previous_device_name = device_name
            previous_client = client
            previous_date = date_of_value

            has_history = True

    if the_device_id != None and has_history:
        # we will set a dispaly device name
        the_device_name = device_name
    else:
        the_device_name = None

    if asDict:
        return {
                "timeline": timeline,
                "datatypes": datatypes
                }
    else:
        return render_template('timeline.html',
            mactive="timeline",
            device_name=the_device_name,
            timeline=timeline,
            datatypes = datatypes
            )


from domogik.admin.application import app, render_template
from flask import request, flash, redirect
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required
from flask.ext.babel import gettext, ngettext

@app.route('/timeline')
@login_required
def timeline():
    return timeline_generic()

@app.route('/timeline/device/<int:device_id>')
@login_required
def timeline_device(device_id):
    return timeline_generic(device_id = device_id)




def timeline_generic(device_id = None):
    # devices 
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
    else:
        print("Error : no devices found!")
        devices = []

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
        data = app.db.get_timeline(device_id = device_id)
        previous_device_id = 0
        previous_date = None
        sensors_changes_for_the_device = []
        for elt in data:
            print(elt)
            (device_name, client, sensor_name, sensor_dt_type, sensor_id, date_of_value, value) = elt
   
            if "unit" in datatypes[sensor_dt_type]:
                unit = datatypes[sensor_dt_type]["unit"]
            else:
                unit = None

            if device_id == previous_device_id and date_of_value == previous_date:
                pass
            else:
                if previous_device_id != 0:
                    timeline.append({ "datetime" : previous_date,
                                      "date" : previous_date.date(),
                                      "time" : previous_date.time(),
                                      "device_name" : previous_device_name,
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

            """
            found = False
            dt_type = None
            sensor_name = None
            for dev in devices:
                for sensor in dev['sensors']:
                    id = dev['sensors'][sensor]['id']

                    if "unit" in datatypes[dev['sensors'][sensor]["data_type"]]:
                        unit = datatypes[dev['sensors'][sensor]["data_type"]]["unit"]
                    else:
                        unit = None

                    if id == elt.sensor_id:
                        if dev['id'] == previous_device_id and elt.date == previous_date:
                            pass
                        else:
                            if previous_device_id != 0:
                                timeline.append({ "datetime" : elt.date,
                                                  "date" : elt.date.date(),
                                                  "time" : elt.date.time(),
                                                  "device_name" : device_name,
                                                  "client" : client,
                                                  "sensors_changes" : sensors_changes_for_the_device,
                                                })
                            sensors_changes_for_the_device = []
                            device_name = dev['name']
                            device_id = dev['id']
                            client = dev['client_id']


                        sensors_changes_for_the_device.append({"sensor_name" : dev['sensors'][sensor]['name'],
                                                               "dt_type" : dev['sensors'][sensor]['data_type'],
                                                               "unit" : unit,
                                                               "value" : elt.value_str})
                        found = True
                        break
                if found == True:
                    break
                  
            previous_device_id = device_id
            previous_date = elt.date
            """
         

    return render_template('timeline.html',
        mactive="timeline",
        timeline=timeline
        )


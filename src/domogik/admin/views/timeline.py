from domogik.admin.application import app, render_template
from flask import request, flash, redirect
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required
from flask.ext.babel import gettext, ngettext

@app.route('/timeline')
@login_required
def timeline():

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



    # timeline
    with app.db.session_scope():
        timeline = []
        data = app.db.get_timeline()
        print(data)
        print(data.value)
        previous_device_id = 0
        previous_date = None
        sensors_changes_for_the_device = []
        for elt in data:
            print(elt)
   
            found = False
            dt_type = None
            sensor_name = None
            for dev in devices:
                for sensor in dev['sensors']:
                    id = dev['sensors'][sensor]['id']
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
                                                               "value" : elt.value_str})
                        found = True
                        break
                if found == True:
                    break
                  
            previous_device_id = device_id
            previous_date = elt.date
         

    return render_template('timeline.html',
        mactive="timeline",
        timeline=timeline
        )


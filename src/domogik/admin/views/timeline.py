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
        for elt in data:
            print(elt)
   
            found = False
            dt_type = None
            sensor_name = None
            for dev in devices:
                for sensor in dev['sensors']:
                    id = dev['sensors'][sensor]['id']
                    if id == elt.sensor_id:
                        sensor_name = dev['sensors'][sensor]['name']
                        dt_type = dev['sensors'][sensor]['data_type']
                        found = True
                        break
                if found == True:
                    device_name = dev['name']
                    break
                  
            timeline.append({ "datetime" : elt.date,
                              "date" : elt.date.date(),
                              "time" : elt.date.time(),
                              "device_name" : device_name,
                              "device_name" : device_name,
                              "sensor_name" : sensor_name,
                              "dt_type" : dt_type,
                              "value" : elt.value_str
                            })
         

    return render_template('timeline.html',
        mactive="timeline",
        timeline=timeline
        )


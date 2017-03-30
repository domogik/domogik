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
from operator import itemgetter

@app.route('/battery')
@app.route('/battery/')
@login_required
def battery():

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


    # TODO : improve by getting directly all devices instead of all sensors ?
    with app.db.session_scope():
        sensors = []
        data = app.db.get_all_sensor()
        for item in data:
            if item.data_type == "DT_Battery":
                dev = app.db.get_device(item.device_id)
                try:
                    last_value = int(item.last_value)
                except:
                    last_value = None
                sensors.append({"name" : item.name,
                                "last_value" : last_value,
                                "last_received" : item.last_received,
                                "device_id" : item.device_id,
                                "device_name" : dev['name'],
                                "client_id" : dev['client_id'],
                                "id" : item.id })
         
        sensors = sorted(sensors, key=itemgetter("last_value", "device_name"))

    return render_template('battery.html',
        mactive="battery",
        sensors=sensors
        )


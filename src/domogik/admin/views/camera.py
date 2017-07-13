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

@app.route('/camera')
@app.route('/camera/')
@login_required
def camera():

    # TODO : improve by getting directly all devices instead of all sensors ?
    with app.db.session_scope():
        video_mjpeg = []
        data = app.db.get_all_sensor()
        for item in data:
            if item.data_type == "DT_VideoMjpeg":
                dev = app.db.get_device(item.device_id)
                try:
                    last_value = item.last_value
                except:
                    last_value = None
                video_mjpeg.append({"name" : item.name,
                                "last_value" : last_value,
                                "last_received" : item.last_received,
                                "device_id" : item.device_id,
                                "device_name" : dev['name'],
                                "client_id" : dev['client_id'],
                                "id" : item.id })
         
        sensors = sorted(video_mjpeg, key=itemgetter("device_name"))

    return render_template('camera.html',
        mactive="camera",
        video_mjpeg=video_mjpeg,
        rest_url = request.url_root + "rest"
        )


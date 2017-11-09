import json
from domogik.admin.application import app, render_template, timeit
from flask import request, flash, redirect, jsonify
from domogikmq.reqrep.client import MQSyncReq
from domogik.common.packagejson import PackageJson
from domogik.common.deviceconsistency import DeviceConsistency
from domogikmq.message import MQMessage
from flask_login import login_required
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass

@app.route('/upgrade')
@login_required
@timeit
def upgrade():
    with app.db.session_scope():
        devs = app.db.list_devices(d_state=u'upgrade')
    
    return render_template('upgrade.html',
        mactive="upgrade",
        devices=devs
        )

@app.route('/upgrade/<int:devid>')
@login_required
@timeit
def upgrade_dev(devid):
    step = 1
    with app.db.session_scope():
        # get a list of what needs to be done
        dev = app.db.get_device(devid)
        device_json = json.loads(json.dumps(dev))
        name = dev['client_id']
        name = name.replace('plugin-','');
        name = name.split('.')[0]
        pjson = PackageJson(name)
        dc = DeviceConsistency("return", device_json, pjson.json)
        actions = dc.get_result()
        # calculate the step
        mig = app.db.get_migration('device', devid)
        if mig:
            if mig.newId > 0:
                # => found this device in the migrate.oldid with type device and newid != 0
                step = 2
                # step 3
                sens = app.db.get_migration_all_sensors(devid)
                if sens:
                    # => found sensors in the migration table that are linked to this device
                    step = 3
            else:
                # => found this device in the migrate.oldid with type device and newid == 0
                step = 4
        else:
            # Nothing in migration table, so nothign started
            step = 1

    return render_template('upgrade_input.html',
        actions=actions,
        devid=devid,
        step=step,
        clientid=dev['client_id'],
        devtype=dev['device_type_id'],
        oldversion=dev['client_version'],
        newversion=pjson.json['identity']['version'],
        mactive="upgrade"
        )

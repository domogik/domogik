from __future__ import absolute_import, division, print_function, unicode_literals
from domogik.admin.application import app, render_template
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask.ext.babel import gettext, ngettext

@app.route('/config')
def clients():

    return render_template('config.html',
        form=form
        )

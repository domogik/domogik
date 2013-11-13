from domogik.admin.application import app
from flask import render_template
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from flask.ext.babel import gettext, ngettext

@app.route('/config')
def clients():

    return render_template('config.html',
        form=form
        )

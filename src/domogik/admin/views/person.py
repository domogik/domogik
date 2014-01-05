from domogik.admin.application import app
from flask import render_template
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from flask.ext.babel import gettext, ngettext

@app.route('/persons')
def persons():
    with app.db.session_scope():
	persons = []
	for per in app.db.list_persons():
	    persons.append(per.__dict__)
        return render_template('persons.html',
            persons=persons,
	    mactive='auth'
        )

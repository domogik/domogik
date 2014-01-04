from domogik.admin.application import app
from flask import render_template
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from flask.ext.babel import gettext, ngettext

@app.route('/accounts')
def accounts():
    with app.db.session_scope():
	accounts = []
	for acc in app.db.list_user_accounts():
	    accounts.append(acc.__dict__)
        return render_template('accounts.html',
            accounts=accounts,
	    mactive='auth'
        )

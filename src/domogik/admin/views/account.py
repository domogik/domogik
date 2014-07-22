from domogik.admin.application import app
from flask import render_template, request, flash, redirect
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
try:
    from flask.ext.babel import gettext, ngettext
except ImportError:
    from flask_babel import gettext, ngettext
    pass
from flask_login import login_required
try:
    from flask_wtf import Form
except ImportError:
    from flaskext.wtf import Form
    pass
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import Required
from domogik.common.sql_schema import UserAccount

from wtforms.ext.sqlalchemy.orm import model_form


@app.route('/accounts')
@login_required
def accounts():
    with app.db.session_scope():
    accounts = []
    for acc in app.db.list_user_accounts():
        accounts.append(acc.__dict__)
        return render_template('accounts.html',
            accounts=accounts,
        mactive='auth'
        )


@app.route('/accountss/del/<aid>')
@login_required
def accounts_delete(aid):
    with app.db.session_scope():
        app.db.del_account(aid)
    return redirect("/accounts")


@app.route('/accounts/<account_id>', methods=['GET', 'POST'])
@login_required
def accounts_edit(account_id):
    with app.db.session_scope():
        if account_id > 0:
            account = app.db.get_user_account(account_id)
        else:
            account = None

        MyForm = model_form(UserAccount, \
                        base_class=Form, \
                        db_session=app.db.get_session(),
                        exclude=['core_person'])
        form = MyForm(request.form, account)

        if request.method == 'POST' and form.validate():
            if int(account_id) > 0:
                app.db.update_user_account(a_id=account_id, \
                    a_new_login=request.form['login'], \
                    a_person_id=request.form['person'], \
                    a_is_admin=request.form['is_admin'], \
                    a_skin_used=request.form['skin_used'])
        # TODO password
            else:
                app.db.add_user_account(\
                    a_login=request.form['login'], \
                    a_password=request.form['password'], \
                    a_person_id=request.form['person'], \
                    a_is_admin=request.form['is_admin'], \
                    a_skin_used=request.form['skin_used'])
            flash(gettext("Changes saved"), "success")
            return redirect("/accounts")
            pass
        elif request.method == 'POST' and not form.validate():
            flash(gettext("Invallid input"), "error")

    return render_template('account_edit.html',
            form = form,
            accountid = account_id,
            mactve="auth"
            )

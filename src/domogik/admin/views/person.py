from domogik.admin.application import app
from flask import render_template, request, flash, redirect
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from flask.ext.babel import gettext, ngettext
from flask_login import login_required
from flask_wtf import Form
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
            BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import Required
from domogik.common.sql_schema import Person, UserAccount

from wtforms.ext.sqlalchemy.orm import model_form

@app.route('/persons')
@login_required
def persons():
    with app.db.session_scope():
	persons = []
	for per in app.db.list_persons():
	    persons.append(per.__dict__)
        return render_template('persons.html',
            persons=persons,
	    mactive='auth'
        )

@app.route('/persons/del/<pid>')
@login_required
def persons_delete(pid):
    with app.db.session_scope():
        app.db.del_person(pid)
    return redirect("/persons")


@app.route('/persons/<person_id>', methods=['GET', 'POST'])
@login_required
def persons_edit(person_id):
    with app.db.session_scope():
        if person_id > 0:
            person = app.db.get_person(person_id)
	else:
            personn = None

	MyForm = model_form(Person, \
			base_class=Form, \
			db_session=app.db.get_session(),
			exclude=['user_accounts'])
	form = MyForm(request.form, person)
        if request.method == 'POST' and form.validate():
	    if int(person_id) > 0:
                app.db.update_person(person_id, \
					p_first_name=request.form['first_name'], \
					p_last_name=request.form['last_name'], \
					p_birthdate=request.form['birthdate'])
	    else:
                app.db.add_person(\
					p_first_name=request.form['first_name'], \
					p_last_name=request.form['last_name'], \
					p_birthdate=request.form['birthdate'])
            flash(gettext("Changes saved"), "success")
            return redirect("/persons")
	    pass
	elif request.method == 'POST' and not form.validate():
	    flash(gettext("Invalid input"), "error")    	

    return render_template('person_edit.html',
            form = form,
            personid = person_id,
            mactve="auth",
            )


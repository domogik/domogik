from domogik.admin.application import app, render_template
from flask import request, flash, redirect
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
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
            BooleanField, SubmitField, SelectField, IntegerField, DateField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Required, Optional, Email, EqualTo
from domogik.common.sql_schema import Person, UserAccount

from wtforms.ext.sqlalchemy.orm import model_form

@app.route('/users')
@login_required
def users():
    with app.db.session_scope():
        persons = []
        for per in app.db.list_persons_and_accounts():
            print(type(per))
            print(u"{0}".format(per))
            #persons.append(per.__dict__)
            #persons.append(dict(zip(per.keys(), per)))
            buf2 = {}
            for buf in per:
                if buf != None:
                    buf2.update(buf.__dict__)
            persons.append(buf2)
        return render_template('users.html',
            persons=persons,
            mactive='users'
        )

@app.route('/user/del/<pid>')
@login_required
def user_delete(pid):
    with app.db.session_scope():
        app.db.del_person(pid)
    return redirect("/users")


@app.route('/user/<person_id>', methods=['GET', 'POST'])
@login_required
def user_edit(person_id):
    with app.db.session_scope():
        the_first_name = None
        the_last_name = None
        the_birthdate = None
        #the_email = None
        #the_phone_number = None
        the_login = None
        if int(person_id) > 0:
            # Person informations
            person = app.db.get_person(person_id)
            the_first_name = person.first_name
            the_last_name = person.last_name
            the_birthdate = person.birthdate
            #the_email = None
            #the_phone_number = None

            # Linked account informations
            account = app.db.get_user_account_by_person(person_id)
            if account != None:
                the_login = account.login
        else:
            person = None


        #MyForm = model_form(Person, \
        #        base_class=Form, \
        #        db_session=app.db.get_session(),
        #        exclude=['user_accounts'])
        #form = MyForm(request.form, person)
        class F(Form):
            pid = HiddenField("person_id", default=person_id)
            first_name = TextField("First Name", [Required()], default=the_first_name, description="Required")
            last_name = TextField("Last Name", [Required()], default=the_last_name, description="Required")
            #email = EmailField("Email", [Required(), Email()], default=the_email, description="Required. The email may be used in scenarios to send notifications")
            #phone_number = TextField("Phone number", [], default=the_phone_number, description="Required. The phone number may be used in scenarios to send notifications")
            birthdate = DateField("Birthdate", [Optional()], default=the_birthdate, description="Optional")
            login = TextField("Login", [Optional()], default=the_login)
            password = PasswordField("Password", [Required(), EqualTo('password2', message='You must type twice the same password')], default="")
            password2 = PasswordField("Repeat the password")
            submit = SubmitField(u"Submit")
            pass
        form = F()

        if request.method == 'POST' and form.validate():
            print("POST!")
            print(request.form)
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
            return redirect("/users")
            pass
        elif request.method == 'POST' and not form.validate():
            print("POST MAUVAIS!")
            print(request.form)
            flash(gettext("Invalid input"), "error")        

    return render_template('user_edit.html',
            form = form,
            personid = person_id,
            mactve="users",
            )


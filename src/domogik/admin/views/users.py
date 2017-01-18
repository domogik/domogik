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
import traceback

@app.route('/users')
@login_required
def users():
    with app.db.session_scope():
        persons = []
        for per in app.db.list_persons_and_accounts():
            #persons.append(per.__dict__)
            #persons.append(dict(zip(per.keys(), per)))
            buf2 = {}
            # preserve person id instead of account id
            id = per[0].id 
            account_id = None
            if len(per) > 1:
                if per[1] != None:
                    account_id = per[1].id
            for buf in per:
                if buf != None:
                    buf3 = buf.__dict__
                    buf2.update(buf3)
            buf2['id'] = id
            buf2['account_id'] = account_id
            persons.append(buf2)
        return render_template('users.html',
            persons=persons,
            mactive='users'
        )

@app.route('/user/del/<pid>')
@login_required
def user_delete(pid):
    with app.db.session_scope():
        account = app.db.get_user_account_by_person(pid)
        if account != None:
            the_lock_delete = account.lock_delete
            if the_lock_delete == True:
                flash(gettext("You can't delete this user"), "warning")
                return redirect("/users")
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
        the_account_exists = False
        the_account_id = 0
        the_login = None
        the_lock_edit = None
        the_is_admin = None
        the_lock_delete = None
        the_hasLocation = 0
        if int(person_id) > 0:
            # Person informations
            person = app.db.get_person(person_id)
            if person == None:
                flash(gettext("There is no such user"), "warning")
                return redirect("/users")
            the_first_name = person.first_name
            the_last_name = person.last_name
            the_birthdate = person.birthdate
            if person.location_sensor is not None:
                the_hasLocation = 1
            #the_email = None
            #the_phone_number = None

            # Linked account informations
            account = app.db.get_user_account_by_person(person_id)
            if account != None:
                the_account_exists = True
                the_account_id = account.id
                the_login = account.login
                the_is_admin = account.is_admin
                the_lock_edit = account.lock_edit
                the_lock_delete = account.lock_delete
        else:
            person = None


        class F(Form):
            pid = HiddenField("person_id", default=person_id)
            account_exists = HiddenField("account_exists", default=the_account_exists)
            account_id = HiddenField("account_id", default=the_account_id)
            first_name = TextField("First Name *", [Required()], default=the_first_name)
            last_name = TextField("Last Name *", [Required()], default=the_last_name)
            #email = EmailField("Email", [Required(), Email()], default=the_email)
            #phone_number = TextField("Phone number", [], default=the_phone_number)
            birthdate = DateField("Birthdate", [Optional()], default=the_birthdate)
            login = TextField("Login", [Optional()], default=the_login)
            #password = PasswordField("Password", [Required(), EqualTo('password2', message='You must type twice the same password')], default="")
            #password2 = PasswordField("Repeat the password")
            is_admin = BooleanField("User is administrator", [Optional()], default=the_is_admin)
            hasLocation = BooleanField("User is using location", [Optional()], default=the_hasLocation, description="If you disable this, you will lose all history")
            submit = SubmitField(u"Submit")
            pass
        form = F()

        if request.method == 'POST' and form.validate():
            try:
                # security for locked users !
                if the_lock_edit == True:
                    flash(gettext("You can't edit locked users"), "warning")
                    return redirect("/users")

                if 'hasLocation' not in request.form:
                    hasLocation = 0
                elif request.form['hasLocation'] == 'y':
                    hasLocation = 1
                else:
                    hasLocation = 0

                if int(person_id) > 0:
                    app.db.update_person(person_id, \
                                         p_first_name=request.form['first_name'], \
                                         p_last_name=request.form['last_name'], \
                                         p_birthdate=request.form['birthdate'], \
                                         p_hasLocation=hasLocation)
                    if request.form['login'] != "":
                        if 'is_admin' not in request.form:
                            is_admin = 0
                        elif request.form['is_admin'] == 'y':
                            is_admin = 1
                        else:
                            is_admin = 0
                        if int(request.form['account_id']) == 0:
                            app.db.add_user_account(a_login=request.form['login'], 
                                                    a_person_id=person.id,
                                                    a_is_admin=is_admin)
                        else:
                            app.db.update_user_account(a_id=request.form['account_id'],
                                                    a_new_login=request.form['login'], 
                                                    a_person_id=person.id,
                                                    a_is_admin=is_admin)
                    flash(gettext("The user is updated"), "success")
                else:
                    person = app.db.add_person(\
                                      p_first_name=request.form['first_name'], \
                                      p_last_name=request.form['last_name'], \
                                      p_birthdate=request.form['birthdate'], \
                                      p_hasLocation=hasLocation)
                    if request.form['login'] != "":
                        if 'is_admin' not in request.form:
                            is_admin = 0
                        elif request.form['is_admin'] == 'y':
                            is_admin = 1
                        else:
                            is_admin = 0
                        app.db.add_user_account(a_login=request.form['login'], 
                                                a_person_id=person.id,
                                                a_is_admin=is_admin)
                    flash(gettext("The user is created"), "success")
                return redirect("/users")
            except:
                print(u"Error while creating/updating a user : {0}".format(traceback.format_exc()))
                flash(gettext("There was an error during the user creation or upgrade."), "error")
                return redirect("/users")
        elif request.method == 'POST' and not form.validate():
            flash(gettext("Invalid input"), "error")        

    return render_template('user_edit.html',
            form = form,
            personid = person_id,
            lock_edit = the_lock_edit,
            mactve="users",
            )



@app.route('/user/password/<person_id>', methods=['GET', 'POST'])
@login_required
def user_password(person_id):
    with app.db.session_scope():
        the_first_name = None
        the_last_name = None
        the_account_exists = False
        the_account_id = 0
        the_login = None
        the_lock_edit = None
        if int(person_id) > 0:
            # Person informations
            person = app.db.get_person(person_id)
            if person == None:
                flash(gettext("There is no such user"), "warning")
                return redirect("/users")
            the_first_name = person.first_name
            the_last_name = person.last_name

            # Linked account informations
            account = app.db.get_user_account_by_person(person_id)
            if account != None:
                the_account_exists = True
                the_account_id = account.id
                the_login = account.login
                the_lock_edit = account.lock_edit
                the_lock_delete = account.lock_delete
        else:
            person = None


        class F(Form):
            pid = HiddenField("person_id", default=person_id)
            account_id = HiddenField("account_id", default=the_account_id)
            password = PasswordField("Password", [Required(), EqualTo('password2', message='You must type twice the same password')], default="")
            password2 = PasswordField("Repeat the password")
            submit = SubmitField(u"Submit")
            pass
        form = F()

        if request.method == 'POST' and form.validate():
            try:
                # security for locked users !
                if the_lock_edit == True:
                    flash(gettext("You can't edit locked users"), "warning")
                    return redirect("/users")
    
                if int(person_id) > 0:
                    app.db.user_change_password(request.form['account_id'], request.form['password'])
                    flash(gettext("The password is updated"), "success")
                else:
                    flash(gettext("You can't change the password for person id = 0"), "warning")
                return redirect("/users")
            except:
                print(u"Error while updating the user password : {0}".format(traceback.format_exc()))
                flash(gettext("There was an error during the password update for the user."), "error")
                return redirect("/users")
        elif request.method == 'POST' and not form.validate():
            flash(gettext("Invalid input"), "error")        

    return render_template('user_password.html',
            form = form,
            personid = person_id,
            last_name = the_last_name,
            first_name = the_first_name,
            login = the_login,
            lock_edit = the_lock_edit,
            mactve="users",
            )


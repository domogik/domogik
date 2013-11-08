from domogik.admin.application import app, login_manager
from flask import render_template, request, flash, redirect
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from flask_login import login_required, login_user, logout_user
from wtforms import form, fields, validators

class LoginForm(form.Form):
    user = fields.TextField('user', [validators.Required()])
    passwd = fields.PasswordField('passwd', [validators.Required()])
    submit = fields.SubmitField("Login")
    def hidden_tag(self):
        pass

@login_manager.user_loader
def load_user(userid):
    with app.db.session_scope():
        user = app.db.get_user_account(userid)
        if user.is_admin:
            return user
        else:
            return None

@login_manager.unauthorized_handler
def rediret_to_login():
    return redirect('/login')

@app.route('/login', methods=('GET', 'POST'))
def login():
    fform = LoginForm(request.form)
    if request.method == 'POST' and fform.validate():
        with app.db.session_scope():
            if app.db.authenticate(request.form["user"], request.form["passwd"]):
                user = app.db.get_user_account_by_login(request.form["user"])
                if user.is_admin:
                    login_user(user)
                    flash("Login successfull", "success")
                    return redirect('/')
                else:
                    flash("This user is not an admin", "warning")
            else:
                flash("Combination of username and password wrong", "warning")
    return render_template('login.html',
        form=fform,
        nonav = True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")

from domogik.admin.application import app, login_manager, babel, render_template
from flask import request, flash, redirect, Response
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required, login_user, logout_user, current_user
from wtforms import form, fields, validators
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass

class LoginForm(form.Form):
    user = fields.TextField('user', [validators.Required()])
    passwd = fields.PasswordField('passwd', [validators.Required()])
    def hidden_tag(self):
        pass

@login_manager.user_loader
def load_user(userid):
    # Used if we already have a cookie
    with app.db.session_scope():
        user = app.db.get_user_account(userid)
        app.db.detach(user)
        if user.is_admin:
            return user
        else:
            return None

@login_manager.unauthorized_handler
def rediret_to_login():
    if str(request.path).startswith('/rest/'):
        if app.dbCOnfig['rest_auth'] == True:
            # take into account that json_reponse is called after this, so we need to pass th params to json_reponse
            return 401, "Could not verify your access level for that URL.\n You have to login with proper credentials."
        else:
            pass
    else:
        return redirect('/login')

@login_manager.request_loader
def load_user_from_request(request):
    if str(request.path).startswith('/rest/'):
        if app.dbConfig['rest_auth'] == True:
            auth = request.authorization
            app.logger.debug(auth)
            if not auth:
                app.logger.debug(u"Rest auth active - no authorization request received. If you added login and password in the url, you may encounter this error. Bad usage : curl http://login:password@url/ - Good usage : curl --user login:password http://url/ ")
                return None
            else:
                with app.db.session_scope():
                    if app.db.authenticate(auth.username, auth.password):
                        app.logger.debug(u"Rest auth active - user authenticated")
                        user = app.db.get_user_account_by_login(auth.username)
                        if user.is_admin:
                            app.logger.debug("Rest auth active - user authenticated - user is admin (ok)")
                            return user
                        else:
                            app.logger.debug("Rest auth active - user authenticated - user is NOT admin (not granted : only admin users can query REST)")
                            return None
                    else:
                            app.logger.debug("Rest auth active - user not authenticated - incorrect login or password")
                            return None
        else:
            app.logger.debug("Rest auth inactive - anonymous user will be used")
            with app.db.session_scope():
                user = app.db.get_user_account_by_login('Anonymous')
                app.logger.debug("Rest auth inactive - anonymous user is : '{0}'".format(user))
                return user
    else:
        return None

@babel.localeselector
def get_locale():
    return 'en'


@app.route('/login', methods=('GET', 'POST'))
def login():
    fform = LoginForm(request.form)
    if request.method == 'POST' and fform.validate():
        with app.db.session_scope():
            if app.db.authenticate(request.form["user"], request.form["passwd"]):
                user = app.db.get_user_account_by_login(request.form["user"])
                if user.is_admin:
                    login_user(user)
                    # as we see the page after the login, there is no need to tell this is a success ;)
                    #flash(gettext("Login successfull"), "success")
                    return redirect('/')
                else:
                    flash(gettext("This user is not an admin"), "warning")
            else:
                flash(gettext("Combination of username and password wrong"), "warning")
    return render_template('login.html',
        form=fform,
        nonav = True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")

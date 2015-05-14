from domogik.common.utils import get_packages_directory, get_libraries_directory
import sys
import os

from flask import Flask, g
try:
    from flask_wtf import Form, RecaptchaField
except ImportError:
    from flaskext.wtf import Form, RecaptchaField
    pass
import flask_login
from flask_login import LoginManager, current_user
try:
	from flask.ext.babel import Babel, get_locale, format_datetime
except ImportError:
	from flask_babel import Babel, get_locale, format_datetime
	pass
from wtforms import TextField, HiddenField, ValidationError, RadioField,\
    BooleanField, SubmitField
from wtforms.validators import Required
try:
    from wtforms.fields import HiddenField
except ImportError:
    def is_hidden_field_filter(field):
        raise RuntimeError('WTForms is not installed.')
else:
    def is_hidden_field_filter(field):
        return isinstance(field, HiddenField)
from flask.ext.themes2 import Themes, render_theme_template


### init Flask

login_manager = LoginManager()
babel = Babel()

app = Flask(__name__)

### next steps...

#app.debug = True
login_manager.init_app(app)
babel.init_app(app)
Themes(app, app_identifier='domogik-admin')


app.jinja_env.globals['bootstrap_is_hidden_field'] =\
    is_hidden_field_filter
app.jinja_env.add_extension('jinja2.ext.do')

# in a real app, these should be configured through Flask-Appconfig
app.config['SECRET_KEY'] = 'devkey'
app.config['RECAPTCHA_PUBLIC_KEY'] = \
'6Lfol9cSAAAAADAkodaYl9wvQCwBMr3qGR_PPHcw'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'Europe/Paris'

# jinja 2 filters
def format_babel_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    elif format == 'basic':
        format="dd.MM.y HH:mm"
    return format_datetime(value, format)

def sort_by_id(value):
    return sorted(value.items(), key=lambda x: x[1]['id'])

app.jinja_env.filters['datetime'] = format_babel_datetime
app.jinja_env.filters['sortid'] = sort_by_id

# create acces_log
@app.after_request
def write_access_log_after(response):
    app.logger.debug(' => response status code: {0}'.format(response.status_code))
    app.logger.debug(' => response content_type: {0}'.format(response.content_type))
    #app.logger.debug(' => response data: {0}'.format(response.response))
    return response

@app.before_request
def write_acces_log_before():
    app.logger.info('http request for {0} received'.format(request.path))

# render a template, later on we can select the theme it here
def render_template(template, **context):
    user = flask_login.current_user
    if not hasattr(user, 'skin_used') or user.skin_used == '':
        user.skin_used = 'default'
    return render_theme_template(user.skin_used, template, **context)

### packages admin pages

sys.path.append(get_libraries_directory())

from domogik.admin.views.client_advanced_empty import nothing_adm
for a_client in os.listdir(get_packages_directory()):
    if os.path.isdir(os.path.join(get_packages_directory(), a_client)):
        # check if there is an "admin" folder with an __init__.py file in it
        print(a_client)
        if os.path.isfile(os.path.join(get_packages_directory(), a_client, "admin", "__init__.py")):
            print("=> admin")
            pkg = "domogik_packages.{0}.admin".format(a_client)
            pkg_adm = "{0}_adm".format(a_client)
            print(u"Try to import module : {0} => {1}_adm".format(pkg, a_client))
            the_adm = getattr(__import__(pkg, fromlist=[pkg_adm], level=1), pkg_adm)
            app.register_blueprint(the_adm, url_prefix="/{0}".format(a_client))
        # if no admin for the client, include the generic empty page
        else:
            app.register_blueprint(nothing_adm, url_prefix="/{0}".format(a_client))


### import all files inside the view module
from domogik.admin.views.index import *
from domogik.admin.views.login import *
from domogik.admin.views.clients import *
from domogik.admin.views.orphans import *
from domogik.admin.views.account import *
from domogik.admin.views.person import *
from domogik.admin.views.rest import *
from domogik.admin.views.scenario import *

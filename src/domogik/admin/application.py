from flask import Flask, render_template
from flask_wtf import Form, RecaptchaField
from flask_login import LoginManager
from flask.ext.babel import Babel, get_locale, format_datetime
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

login_manager = LoginManager()
babel = Babel()

app = Flask(__name__)
login_manager.init_app(app)
babel.init_app(app)

app.jinja_env.globals['bootstrap_is_hidden_field'] =\
    is_hidden_field_filter

# in a real app, these should be configured through Flask-Appconfig
app.config['SECRET_KEY'] = 'devkey'
app.config['RECAPTCHA_PUBLIC_KEY'] = \
'6Lfol9cSAAAAADAkodaYl9wvQCwBMr3qGR_PPHcw'

# jinja 2 filters
def format_babel_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    return format_datetime(value, format)

def sort_by_id(value):
    return sorted(value.items(), key=lambda x: x[1]['id'])

app.jinja_env.filters['datetime'] = format_babel_datetime
app.jinja_env.filters['sortid'] = sort_by_id

# import all files inside the view module
from domogik.admin.views.index import *
from domogik.admin.views.login import *
from domogik.admin.views.clients import *
from domogik.admin.views.orphans import *
from domogik.admin.views.account import *
from domogik.admin.views.person import *

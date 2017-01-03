from domogik.common.utils import get_packages_directory, get_libraries_directory
from domogik.common.jsondata import domogik_encoder
from functools import wraps
import json
import sys
import os
import time
from flask import Flask, g, request, session
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
from flask.ext.session import Session
from werkzeug.exceptions import Unauthorized
from werkzeug import WWWAuthenticate
import traceback

### init Flask
app = Flask(__name__)

### set Flask Config
app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter
app.jinja_env.add_extension('jinja2.ext.do')
#app.config['SECRET_KEY'] = '12sfjklghort nvlbneropgtbhni won ouiw'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lfol9cSAAAAADAkodaYl9wvQCwBMr3qGR_PPHcw'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'Europe/Paris'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp'
app.config['SESSION_FILE_THRESHOLD'] = 25
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

### init extensions and load them

session_manager = Session()
session_manager.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

babel = Babel()
babel.init_app(app)

Themes(app, app_identifier='domogik-admin')

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
    app.json_stop_at = []
    app.logger.info('http request for {0} received'.format(u''.join(request.path).encode('utf-8')))

# render a template, later on we can select the theme it here
def render_template(template, **context):
    user = flask_login.current_user
    if not hasattr(user, 'skin_used') or user.skin_used == '':
        user.skin_used = 'default'
    return render_theme_template(user.skin_used, template, **context)

# decorator to handle logging
def timeit(action_func):
    @wraps(action_func)
    def timed(*args, **kw):
        ts = time.time()
        result = action_func(*args, **kw)
        te = time.time()
        app.logger.debug('performance|{0}|{1}|{2}|{3}'.format(action_func.__name__, args, kw, te-ts))
        return result
    return timed

# json reponse handler decorator
# the url handlers funictions can return
def json_response(action_func):
    @wraps(action_func)
    def create_json_response(*args, **kwargs):
        ret = action_func(*args, **kwargs)
        # if list is 2 entries long
        if (type(ret) is list or type(ret) is tuple):
            if len(ret) == 2:
                # return httpcode data
                #  code = httpcode
                #  data = data
                rcode = ret[0]
                rdata = ret[1]
            elif len(ret) == 1:
                # return errorStr
                #  code = 400
                #  data = {msg: <errorStr>}
                rcode = 400
                rdata = {error: ret[0]}
        else:
            # just return
            # code = 204 = No content
            # data = empty
            rcode = 204
            rdata = None
        # do the actual return
        if app.rest_auth == "True" and rcode == 401:
            resp = Response(status=401)
            resp.www_authenticate.set_basic(realm = "Domogik REST interface" )
            return resp
        else:
            if type(app.json_stop_at) is not list:
                app.json_stop_at = []
            if rdata:
                if app.clean_json == "False":
                    resp = json.dumps(rdata, cls=domogik_encoder(stop_at=app.json_stop_at), check_circular=False)
                else:
                    resp = json.dumps(rdata, cls=domogik_encoder(stop_at=app.json_stop_at), check_circular=False, indent=4, sort_keys=True)
            else:
                resp = None
            return Response(
                response=resp,
                status=rcode,
                content_type='application/json'
            )
    return create_json_response

# jsonp reponse handler decorator  for jquery requests
# the url handlers funictions can return
def jsonp_response(action_func):
    @wraps(action_func)
    def create_json_response(*args, **kwargs):
        ret = action_func(*args, **kwargs)
        # if list is 3 entries long
        # - http code
        # - json data
        # - callback name
        if (type(ret) is list or type(ret) is tuple):
            if len(ret) == 3:
                # return httpcode data
                #  code = httpcode
                #  data = data
                #  callback = callback
                rcode = ret[0]
                rdata = ret[1]
                rcallback = ret[2]
            else:
                # return errorStr
                #  code = 400
                #  data = {msg: <errorStr>}
                rcode = 400
                rdata = {error: ret[0]}
        else:
            # just return
            # code = 204 = No content
            # data = empty
            rcode = 204
            rdata = None
            rcallback = None
        # do the actual return
        if app.rest_auth == "True" and rcode == 401:
            resp = Response(status=401)
            resp.www_authenticate.set_basic(realm = "Domogik REST interface" )
            return resp
        else:
            if type(app.json_stop_at) is not list:
                app.json_stop_at = []
            if rdata:
                if app.clean_json == "False":
                    resp = json.dumps(rdata, cls=domogik_encoder(stop_at=app.json_stop_at), check_circular=False)
                else:
                    resp = json.dumps(rdata, cls=domogik_encoder(stop_at=app.json_stop_at), check_circular=False, indent=4, sort_keys=True)
            else:
                resp = None
            return Response(
                response=u"{0}({1})".format(rcallback, resp),
                status=rcode,
                content_type='application/json'
            )
    return create_json_response

### error pages
@app.errorhandler(404)
def page_not_found(e):
    if u''.join(request.path).encode('utf-8').startswith('/rest/'):
        return render_template('404_json.html'), 404
    else:
        return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    if u''.join(request.path).encode('utf-8').startswith('/rest/'):
        return render_template('500_json.html'), 500
    else:
        return render_template('500.html'), 500

# view class registration
def register_api(view, endpoint, url, pk='id', pk_type=None):
    view_func = view.as_view(endpoint)
    app.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET'])
    app.add_url_rule(url, view_func=view_func, methods=['POST'])
    if pk_type != None:
        app.add_url_rule('{0}<{1}:{2}>'.format(url, pk_type, pk), view_func=view_func,
                     methods=['GET', 'PUT', 'DELETE'])
    else:
        app.add_url_rule('{0}<{1}>'.format(url, pk), view_func=view_func,
                     methods=['GET', 'PUT', 'DELETE'])

### packages admin pages

sys.path.append(get_libraries_directory())

from domogik.admin.views.client_advanced_empty import nothing_adm
for a_client in os.listdir(get_packages_directory()):
    try:
        if os.path.isdir(os.path.join(get_packages_directory(), a_client)):
            # check if there is an "admin" folder with an __init__.py file in it
            if os.path.isfile(os.path.join(get_packages_directory(), a_client, "admin", "__init__.py")):
                app.logger.info("Load advanced page for package '{0}'".format(a_client))
                pkg = "domogik_packages.{0}.admin".format(a_client)
                pkg_adm = "{0}_adm".format(a_client)
                the_adm = getattr(__import__(pkg, fromlist=[pkg_adm], level=1), pkg_adm)
                app.register_blueprint(the_adm, url_prefix="/{0}".format(a_client))
            # if no admin for the client, include the generic empty page
            else:
                app.register_blueprint(nothing_adm, url_prefix="/{0}".format(a_client))
    except:
        app.logger.error("Error while trying to load package '{0}' advanced page in the admin. The error is : {1}".format(a_client, traceback.format_exc()))


### import all files inside the view module
from domogik.admin.views.index import *
from domogik.admin.views.login import *
from domogik.admin.views.clients import *
from domogik.admin.views.orphans import *
from domogik.admin.views.users import *
from domogik.admin.views.apidoc import *
from domogik.admin.views.scenario import *
from domogik.admin.views.timeline import *
from domogik.admin.views.battery import *
from domogik.admin.views.datatypes import *
from domogik.admin.views.locations import *
from domogik.admin.views.config import *

### import all rest urls
import domogik.admin.rest.status
import domogik.admin.rest.command
import domogik.admin.rest.datatype
import domogik.admin.rest.sensorhistory
import domogik.admin.rest.butler
from domogik.admin.rest.publish import *
from domogik.admin.rest.device import *
from domogik.admin.rest.sensor import sensorAPI
from domogik.admin.rest.product import *
from domogik.admin.rest.location import *

import json
import sys
import os
import time
import traceback
import zmq
from functools import wraps
from flask import Flask, g, request, session
try:
    from flask_wtf import Form, RecaptchaField
except ImportError:
    from flaskext.wtf import Form, RecaptchaField
    pass
try:
    from flask_login import LoginManager, current_user
except ImportError:
    from flask.ext.login import LoginManager, current_user
    pass
try:
    from flask_babel import Babel, get_locale, format_datetime
except ImportError:
    from flask.ext.babel import Babel, get_locale, format_datetime
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
try:
    from flask_themes2 import Themes, render_theme_template
except ImportError:
    from flask.ext.themes2 import Themes, render_theme_template
    pass
try:
    from flask_session import Session
except ImportError:
    from flask.ext.session import Session
    pass
from werkzeug.exceptions import Unauthorized
from werkzeug import WWWAuthenticate
from domogik.common.database import DbHelper
from domogik.common.configloader import Loader as dmgLoader
from domogik.common.plugin import PACKAGES_DIR, RESOURCES_DIR, PRODUCTS_DIR
from domogik.common.utils import get_packages_directory, get_libraries_directory
from domogik.common.jsondata import domogik_encoder
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq

### init Flask
app = Flask(__name__)
app.db = DbHelper()
app.debug = True
### load config
cfg = dmgLoader('admin').load()
app.globalConfig = dict(cfg[0])
app.dbConfig = dict(cfg[1]) 
app.zmq_context = zmq.Context() 
app.libraries_directory = app.globalConfig['libraries_path']
app.packages_directory = "{0}/{1}".format(app.globalConfig['libraries_path'], PACKAGES_DIR)
app.resources_directory = "{0}/{1}".format(app.globalConfig['libraries_path'], RESOURCES_DIR)
app.publish_directory = "{0}/{1}".format(app.resources_directory, "publish")

### logging to stdout (to get logs in gunicorn logs...)
import logging
gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.DEBUG)
#stream_handler = logging.StreamHandler()
#stream_handler.setLevel(logging.DEBUG)
#app.logger.addHandler(stream_handler)

### set Flask Config
app.jinja_env.globals['bootstrap_is_hidden_field'] = is_hidden_field_filter
app.jinja_env.add_extension('jinja2.ext.do')
app.config['SECRET_KEY'] = app.dbConfig['secret_key']
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lfol9cSAAAAADAkodaYl9wvQCwBMr3qGR_PPHcw'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'Europe/Paris'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = '/tmp'
app.config['SESSION_FILE_THRESHOLD'] = 25
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

### Load the datatypes
cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('datatype.get')
res = cli.request('manager', msg.get(), timeout=10)
if res is not None:
    app.datatypes = res.get_data()['datatypes']
else:
    app.datatypes = {}

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

@app.context_processor
def inject_global_errors():
    err = []
    with app.db.session_scope():
        if len(app.db.get_core_config()) != 5:
            err.append(('Not all config set, you should first set the basic config','/config'))
        if len(app.db.list_devices(d_state=u'upgrade')) > 0:
            err.append(('Some devices need your attention','/upgrade'))
        if not app.db.get_home_location():
            err.append(('No home location set, you should configure it first','/locations/edit/0'))
    return dict(global_errors=err, ws_port=app.dbConfig['ws_port'])

# render a template, later on we can select the theme it here
def render_template(template, **context):
    user = current_user
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
        if app.dbConfig['rest_auth'] == "True" and rcode == 401:
            resp = Response(status=401)
            resp.www_authenticate.set_basic(realm = "Domogik REST interface" )
            return resp
        else:
            if type(app.json_stop_at) is not list:
                app.json_stop_at = []
            if rdata:
                if app.dbConfig['clean_json'] == "False":
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
        rcallback = None
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
                rdata = {"error": ret[0]}
        else:
            # just return
            # code = 204 = No content
            # data = empty
            rcode = 204
            rdata = None
            rcallback = None
        # do the actual return
        if app.dbConfig['rest_auth'] == "True" and rcode == 401:
            resp = Response(status=401)
            resp.www_authenticate.set_basic(realm = "Domogik REST interface" )
            return resp
        else:
            if type(app.json_stop_at) is not list:
                app.json_stop_at = []
            if rdata:
                if app.dbConfig['clean_json'] == "False":
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

### import all files inside the view module
from domogik.admin.views.index import *
from domogik.admin.views.login import *
from domogik.admin.views.clients import *
from domogik.admin.views.orphans import *
from domogik.admin.views.upgrade import *
from domogik.admin.views.users import *
from domogik.admin.views.apidoc import *
from domogik.admin.views.scenario import *
from domogik.admin.views.timeline import *
from domogik.admin.views.battery import *
from domogik.admin.views.datatypes import *
from domogik.admin.views.locations import *
from domogik.admin.views.config import *
from domogik.admin.views.client_advanced_empty import *

### dev/debug urls
from domogik.admin.views.dev import *

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

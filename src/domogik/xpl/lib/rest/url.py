from flask import Flask, g, Response, request
from flask_principal import Principal, Permission, RoleNeed
from flask.ext.login import LoginManager, login_user, logout_user, \
     login_required, current_user
from domogik.common.database import DbHelper, DbHelperException
from domogik.xpl.lib.rest.jsondata import domogik_encoder
import json

# url handler itself
urlHandler = Flask(__name__)
urlHandler.debug = True

# principel
#principals = Principal(urlHandler)

# login manager
#login_manager = LoginManager()
#login_manager.setup_app(urlHandler)

# DB handler decorator
def db_helper(action_func):
    def create_db_helper(*args, **kwargs):
        g.db = DbHelper()
        return action_func(*args, **kwargs)
    return create_db_helper   



# json reponse handler decorator
# the url handlers funictions can return
def json_response(action_func):
    def create_json_response(*args, **kwargs):
        ret = action_func(*args, **kwargs)
        if type(ret) is list or type(ret) is tuple:
            if len(ret) == 2:
                code = ret[0]
                resp = ret[1]
            else:
                code = 200
                resp = ret[1]
        else:
            code = 204
            resp = None
        return Response(
            response=json.dumps(resp, cls=domogik_encoder(), check_circular=False),
            status=code,
            content_type='application/json'
        )
    return create_json_response

# view class registration
def register_api(view, endpoint, url, pk='id', pk_type=None):
    view_func = view.as_view(endpoint)
    urlHandler.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET'])
    urlHandler.add_url_rule(url, view_func=view_func, methods=['POST'])
    if pk_type != None:
        urlHandler.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
                     methods=['GET', 'PUT', 'DELETE'])
    else:
        urlHandler.add_url_rule('%s<%s>' % (url, pk), view_func=view_func,
                     methods=['GET', 'PUT', 'DELETE'])

# import the flask urls
import domogik.xpl.lib.rest.urls.status
from domogik.xpl.lib.rest.urls.device import deviceAPI
register_api(deviceAPI, 'device_api', '/device/', pk='device_id', pk_type='int')
from domogik.xpl.lib.rest.urls.device_usage import deviceUsageAPI
register_api(deviceUsageAPI, 'device_usage_api', '/device_usage/', pk='usage_id')

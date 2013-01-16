from flask import Flask, g, Response
from flask_principal import Principal, Permission, RoleNeed
from flask.ext.login import LoginManager, login_user, logout_user, \
     login_required, current_user
from domogik.common.database import DbHelper, DbHelperException
import json

# url handler itself
urlHandler = Flask(__name__)

# principel
#principals = Principal(urlHandler)

# login manager
#login_manager = LoginManager()
#login_manager.setup_app(urlHandler)

# DB handler
def db_helper(action_func):
    def create_db_helper(*args, **kwargs):
        g.db = DbHelper()
        return action_func(*args, **kwargs)
    return create_db_helper   



# json reponse handler
def json_response(action_func):
    def create_json_response(*args, **kwargs):
        ret = action_func(*args, **kwargs)
        code = 200
        if len(ret) == 2:
            code = ret[0]
            resp = ret[1]
        else:
            resp = ret
        return Response(
            response=json.dumps(resp, indent=4),
            status=code,
            content_type='application/json'
        )
    return create_json_response

# import the flask urls
import domogik.xpl.lib.rest.urls.status

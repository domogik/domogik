from flask import Flask
from flask_principal import Principal, Permission, RoleNeed
from flask.ext.login import LoginManager, login_user, logout_user, \
     login_required, current_user

# url handler itself
urlHandler = Flask(__name__)

# principel
#principals = Principal(urlHandler)

# login manager
#login_manager = LoginManager()
#login_manager.setup_app(urlHandler)

# DB handler
#@urlHandler.after_request
#def dbSession_shutdown(response):
#    urlDB.session.remove()
#    return response

# import the flask urls
import domogik.xpl.lib.rest.urls.status
import domogik.xpl.lib.rest.urls.blah

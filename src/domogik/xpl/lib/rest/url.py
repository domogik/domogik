from flask import Flask, g, Response, request
from domogik.common.logger import Logger
from domogik.common.database import DbHelper, DbHelperException
from domogik.xpl.lib.rest.jsondata import domogik_encoder
from functools import wraps
import time
import json

# flask logegr
flaskLogger = Logger('rinor-http')

# url handler itself
urlHandler = Flask(__name__)
urlHandler.debug = True
urlHandler.logger_name = flaskLogger.get_logger('rinor-http')

# DB handler decorator
def db_helper(action_func):
    @wraps(action_func)
    def create_db_helper(*args, **kwargs):
        g.db = DbHelper()
        return action_func(*args, **kwargs)
    return create_db_helper   

# create acces_log
@urlHandler.after_request
def write_access_log(response):
    log = flaskLogger.get_logger('rinor-http')
    log.info('http request for {0} received'.format(request.path))
    log.debug(' => response status code: {0}'.format(response.status_code))
    log.debug(' => response content_type: {0}'.format(response.content_type))
    log.debug(' => response data: {0}'.format(response.response))
    return response

# json reponse handler decorator
# the url handlers funictions can return
def json_response(action_func):
    @wraps(action_func)
    def create_json_response(*args, **kwargs):
        ret = action_func(*args, **kwargs)
        if (type(ret) is list or type(ret) is tuple) and len(ret) == 2:
            code = ret[0]
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

# decorator to handle logging
def timeit(action_func):
    @wraps(action_func)
    def timed(*args, **kw):
        ts = time.time()
        result = action_func(*args, **kw)
        te = time.time()
        log = flaskLogger.get_logger('rinor-http')
        log.debug('url function {0}({1}, {2}) took {3} sec'.format(action_func.__name__, args, kw, te-ts))
        return result
    return timed

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

# more complex URLS
from domogik.xpl.lib.rest.urls.device import *
from domogik.xpl.lib.rest.urls.package import *
from domogik.xpl.lib.rest.urls.helper import *

# Pure REST API
from domogik.xpl.lib.rest.urls.device_type import deviceTypeAPI
from domogik.xpl.lib.rest.urls.person import personAPI
from domogik.xpl.lib.rest.urls.account import AccountAPI
from domogik.xpl.lib.rest.urls.host import hostAPI

from flask import Flask, g, Response, request
from domogik.common.logger import Logger
from domogik.common.jsondata import domogik_encoder
from functools import wraps
import time
import json

# url handler itself
urlHandler = Flask(__name__)
urlHandler.debug = True

# DB handler decorator
def db_helper(action_func):
    @wraps(action_func)
    def create_db_helper(*args, **kwargs):
#        g.db = DbHelper()
        return action_func(*args, **kwargs)
    return create_db_helper   

# create acces_log
@urlHandler.after_request
def write_access_log_after(response):
    urlHandler.db.close_session()
    urlHandler.logger.debug(' => response status code: {0}'.format(response.status_code))
    urlHandler.logger.debug(' => response content_type: {0}'.format(response.content_type))
    urlHandler.logger.debug(' => response data: {0}'.format(response.response))
    return response

@urlHandler.before_request
def write_acces_log_before():
    urlHandler.db.open_session()
    urlHandler.logger.info('http request for {0} received. Data : {1}'.format(request.path, request.values))

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
        if not urlHandler.clean_json:
            resp = json.dumps(rdata, cls=domogik_encoder(), check_circular=False)
        else:
            resp = json.dumps(rdata, cls=domogik_encoder(), check_circular=False, indent=4, sort_keys=True)
        return Response(
            response=resp,
            status=rcode,
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
        urlHandler.logger.debug('performance|{0}|{1}|{2}|{3}'.format(action_func.__name__, args, kw, te-ts))
        return result
    return timed

# custom error pages
@urlHandler.errorhandler(404)
@json_response
def page_not_found(e):
    return 404, {'error': "Not found"}

@urlHandler.errorhandler(403)
@json_response
def page_not_found(e):
    return 403, {'error': "Forbidden"}

@urlHandler.errorhandler(500)
@json_response
def page_not_found(e):
    urlHandler.logger.debug(e)
    return 500, {'error': "Application error see rest.log"}

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
import domogik.rest.urls.status
import domogik.rest.urls.command
import domogik.rest.urls.datatype

# more complex URLS
from domogik.rest.urls.device import *

# Pure REST API
from domogik.rest.urls.person import personAPI
from domogik.rest.urls.account import AccountAPI
from domogik.rest.urls.sensor import sensorAPI

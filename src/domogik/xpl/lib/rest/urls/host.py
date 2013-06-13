from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper, register_api
from flask import g as dbHelper
from flask.views import MethodView

class hostAPI(MethodView):
    decorators = [db_helper, json_response]

    def get(self, hid):
        if hid != None:
            b = urlHandler.hosts_list[hid]
            print b
        else:
            b = urlHandler.hosts_list
        return 200, b

register_api(hostAPI, 'host', '/host/', pk='hid')

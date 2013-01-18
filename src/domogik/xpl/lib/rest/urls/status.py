from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper
from flask import g as dbHelper

@urlHandler.route('/')
@json_response
def api_root():
        data = {"info" : "inf", 
                "queue" : "queues", 
                "event" : "events",
                "configuration" : "conf",
                "tmp_db_info" : "tmp_db_info"}
        return data

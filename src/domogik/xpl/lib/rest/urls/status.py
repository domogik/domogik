from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper
from flask import g as dbHelper
from domogik.common.sql_schema import new_alchemy_encoder

@urlHandler.route('/')
@json_response
def api_root():
        data = {"info" : "inf", 
                "queue" : "queues", 
                "event" : "events",
                "configuration" : "conf",
                "tmp_db_info" : "tmp_db_info"}
        return data

@urlHandler.route('/db')
@db_helper
def hello_world2():
    b = dbHelper.db.get_device(8)
    return json.dumps(b, cls=new_alchemy_encoder(), check_circular=False)

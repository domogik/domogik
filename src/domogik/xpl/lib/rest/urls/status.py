from domogik.xpl.lib.rest.jsondata import JSonHelper
from domogik.xpl.lib.rest.url import urlHandler

@urlHandler.route('/')
def api_root():
        json_data = JSonHelper("OK")
        json_data.set_data_type("device")
        json_data.set_jsonp(False, "")
        data = {"info" : "inf", 
                "queue" : "queues", 
                "event" : "events",
                "configuration" : "conf",
                "tmp_db_info" : "tmp_db_info"}
        json_data.add_data(data)

        return json_data.get()



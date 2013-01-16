from domogik.xpl.lib.rest.url import urlHandler
from domogik.common.database import DbHelper, DbHelperException
from flask import jsonify

@urlHandler.route('/blah')
def hello_world2():
    urlDB = DbHelper()
    b = urlDB.get_device_usage_by_name('water')
    return jsonify(b.get_public())

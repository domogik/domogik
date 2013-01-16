from domogik.xpl.lib.rest.url import urlHandler
from domogik.common.database import DbHelper, DbHelperException

@urlHandler.route('/blah')
def hello_world2():
    urlDB = DbHelper()
    b = urlDB.list_device_usages()
    c = ""
    for item in b:
        c += str(item)
    return c

from domogik.xpl.lib.rest.url import urlHandler
from domogik.common.database import DbHelper, DbHelperException
from domogik.common.sql_schema import new_alchemy_encoder
import json

@urlHandler.route('/blah')
def hello_world2():
    urlDB = DbHelper()
    b = urlDB.get_device(8)
    return json.dumps(b, cls=new_alchemy_encoder(), check_circular=False)

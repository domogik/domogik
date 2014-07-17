from domogik.admin.application import app
from flask import render_template
from flask.ext.babel import gettext, ngettext
from domogik.common.configloader import Loader, CONFIG_FILE
import requests

@app.route('/rest')
def rest():

    cfg = Loader('rest')
    config = cfg.load()
    conf = dict(config[1])
    port = conf['port']                          

    r = requests.get("http://localhost:{0}/map".format(port))

    return render_template('rest.html',
        mactive="rest",
        urls = r.json(),
        )

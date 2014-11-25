from domogik.admin.application import app
from flask import render_template
from flask.ext.babel import gettext, ngettext
from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common.utils import get_rest_url

import requests

@app.route('/rest')
def rest():
    r = requests.get(get_rest_url())

    return render_template('rest.html',
        mactive="rest",
        urls = r.json(),
        )

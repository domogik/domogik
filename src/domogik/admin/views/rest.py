from domogik.admin.application import app
from flask import render_template
from flask.ext.babel import gettext, ngettext
import requests

@app.route('/rest')
def rest():
    r = requests.get("http://localhost:40405/map") 

    return render_template('rest.html',
        mactive="rest",
        urls = r.json(),
        )

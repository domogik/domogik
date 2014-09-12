from domogik.admin.application import app
from flask import render_template
from flask.ext.babel import gettext, ngettext
from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common.utils import get_ip_for_interfaces

import requests

@app.route('/rest')
def rest():

    cfg = Loader('rest')
    config = cfg.load()
    conf = dict(config[1])
    ### get REST ip and port
    port = conf['port']                          
    interfaces = conf['interfaces']                          
    intf = interfaces.split(',')
    print intf
    # get the first ip of the first interface declared
    ip = get_ip_for_interfaces(intf)[0]


    r = requests.get("http://{0}:{1}/map".format(ip, port))

    return render_template('rest.html',
        mactive="rest",
        urls = r.json(),
        )

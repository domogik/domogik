from flask import Blueprint, abort
from domogik.admin.application import app, render_template
from domogik.admin.views.clients import get_client_detail
from domogik.common.utils import get_packages_directory, get_libraries_directory
from jinja2 import TemplateNotFound
import sys
import os
import traceback

package = "nothing"
nothing_adm = Blueprint(package, __name__)

sys.path.append(get_libraries_directory())
for a_client in os.listdir(get_packages_directory()):
    try:
        if os.path.isdir(os.path.join(get_packages_directory(), a_client)):
            # check if there is an "admin" folder with an __init__.py file in it
            if os.path.isfile(os.path.join(get_packages_directory(), a_client, "admin", "__init__.py")):
                app.logger.info("Load advanced page for package '{0}'".format(a_client))
                pkg = "domogik_packages.{0}.admin".format(a_client)
                pkg_adm = "{0}_adm".format(a_client)
                the_adm = getattr(__import__(pkg, fromlist=[pkg_adm], level=1), pkg_adm)
                app.register_blueprint(the_adm, url_prefix="/{0}".format(a_client))
            # if no admin for the client, include the generic empty page
            else:
                app.register_blueprint(nothing_adm, url_prefix="/{0}".format(a_client))
    except:
        app.logger.error("Error while trying to load package '{0}' advanced page in the admin. The error is : {1}".format(a_client, traceback.format_exc()))

@nothing_adm.route('/<client_id>')
def index(client_id):
    detail = get_client_detail(client_id)
    try:
        return render_template('client_nothing_adm.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients", 
            active = 'advanced')

    except TemplateNotFound:
        abort(404)


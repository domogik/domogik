from flask import Blueprint, abort
from domogik.admin.application import render_template
from domogik.admin.views.clients import get_client_detail

from jinja2 import TemplateNotFound

package = "nothing"

nothing_adm = Blueprint(package, __name__)

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


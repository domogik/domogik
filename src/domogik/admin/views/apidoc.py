from __future__ import absolute_import, division, print_function, unicode_literals
from domogik.admin.application import app
from flask import send_from_directory, redirect
from domogik.common.utils import get_rest_doc_path

# TODO : if one day we find a nice way to install apidoc and generate the doc on the fly...
#        or a way to package the doc when releasing...
#        We could use the below function to locally serve the API doc!
#@app.route('/rest/<path:filename>')
#def rest(filename):
#    return send_from_directory(get_rest_doc_path(), filename)


# But for now... well, we will just redirect to the official online Api doc
@app.route('/apidoc')
def apidoc():
    return redirect("http://apidoc.domogik.org/")


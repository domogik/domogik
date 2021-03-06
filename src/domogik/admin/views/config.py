from flask_login import login_required
from flask import request, flash, redirect
from domogik.admin.application import app, render_template, timeit
try:
    from flask_wtf import Form
except ImportError:
    from flaskext.wtf import Form
    pass
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass
from wtforms import TextField, HiddenField, BooleanField, SubmitField
from wtforms.validators import Required, InputRequired, Optional
from domogik.common.utils import ucode

@app.route('/config', methods=['GET', 'POST'])
@login_required
@timeit
def config():
    with app.db.session_scope():
        cfg = app.db.get_core_config()
    print(cfg)
    # network configuration
    if 'external_ip' not in cfg:
        cfg['external_ip'] = ''
    if 'external_port' not in cfg:
        cfg['external_port'] = ''
    if 'external_ssl' not in cfg:
        cfg['external_ssl'] = ''

    # printer configuration
    if 'printer_ip' not in cfg:
        cfg['printer_ip'] = ''
    if 'printer_name' not in cfg:
        cfg['printer_name'] = ''

    # wit.ai configuration (used by rest butler urls)
    if 'wit_token' not in cfg:
        cfg['wit_token'] = ''

    class F(Form):
        external_ip = TextField("External IP", [Required()], description='External IP or DNS name', default=cfg['external_ip'])
        external_port = TextField("External Port", [Required()], description='External Port where admin is listening', default=cfg['external_port'])
        external_ssl = BooleanField("External use SSL", description='Does external access need ssl', default=cfg['external_ssl'])
        printer_ip = TextField("Printer IP", [Optional()], description='Printer IP', default=cfg['printer_ip'])
        printer_name = TextField("Printer Name", [Optional()], description='Printer name', default=cfg['printer_name'])
        wit_token = TextField("Wit.ai token", [Optional()], description='Authentication token to use https://wit.ai/ services', default=cfg['wit_token'])
        submit = SubmitField("Save")
        pass
    form = F()

    if request.method == 'POST' and form.validate():
        params = request.form.to_dict()
        del(params['csrf_token'])
        with app.db.session_scope():
            app.db.set_core_config(params)
        pass

    return render_template('config.html',
        form = form,
        mactive = "config")


from flask_login import login_required
from domogik.admin.application import app, render_template

@app.route('/datatypes')
@login_required
def datatypes():
    return render_template('datatypes.html',
        datatypes = {},
        mactive = "datatypes")

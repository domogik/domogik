from flask_login import login_required
from domogik.admin.application import app, render_template

@app.route('/locations')
@login_required
def locations():
    return render_template('locations.html',
        locations = {},
        mactive = "locations")

@app.route('/locations/edit/<id>', methods=['GET', 'POST'])
@login_required
def locations_edit(id):
    return render_template('locations_edit.html',
        mactive = "locations")

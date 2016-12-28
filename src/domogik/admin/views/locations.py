from flask_login import login_required
from domogik.admin.application import app, render_template
try:
    from flask_wtf import Form
except ImportError:
    from flaskext.wtf import Form
    pass
from wtforms import TextField, HiddenField, BooleanField, SubmitField
from wtforms.validators import Required, InputRequired

@app.route('/locations')
@login_required
def locations():
    with app.db.session_scope():
        return render_template('locations.html',
            locations = app.db.get_all_location(),
            mactive = "locations")

@app.route('/locations/edit/<lid>', methods=['GET', 'POST'])
@login_required
def locations_edit(lid):
    if int(lid) == 0:
        formatted_address = 'Grotstraat 30, 2400 mol Belgium'
        lname = 'new'
        lrad = 1
        lisHome = 1
    else:
        formatted_address = 'paris'
        lname = ''
        lrad = 0
        lisHome = 0

    class F(Form):
	locid = HiddenField("lid", default=lid)
        lat = HiddenField("lat")
        lng = HiddenField("lng")
        formatted_address = HiddenField("formatted_address")
        postal_code = HiddenField("postal_code")
        locality = HiddenField("locality")
        country = HiddenField("country")
        country_short = HiddenField("country_short")
	locname = TextField("Name", [Required()], default=lname)
	locrad = TextField("Radius", [Required()], default=lrad)
        locisHome = BooleanField("is Home", default=lisHome)
        submit = SubmitField("Save")
	pass
    form = F()

    return render_template('locations_edit.html',
        form = form,
        formatted_address = formatted_address,
        mactive = "locations")


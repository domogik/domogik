from flask_login import login_required
from flask import request, flash, redirect
from domogik.admin.application import app, render_template
try:
    from flask_wtf import Form
except ImportError:
    from flaskext.wtf import Form
    pass
try:
    from flask.ext.babel import gettext, ngettext
except ImportError:
    from flask_babel import gettext, ngettext
from wtforms import TextField, HiddenField, BooleanField, SubmitField
from wtforms.validators import Required, InputRequired
from domogik.common.utils import ucode

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
    with app.db.session_scope():
        if int(lid) == 0:
            formatted_address = ''
            lname = ''
            lrad = 1
            lisHome = 1
        else:
            loc = app.db.get_location(lid)
            formatted_address = filter(lambda n: n.key == 'formatted_address', loc.params)[0].value
            lrad = filter(lambda n: n.key == 'radius', loc.params)[0].value
            lname = loc.name
            lisHome = loc.isHome

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
            radius = TextField("Radius", [Required()], default=lrad)
            locisHome = BooleanField("is Home", default=lisHome)
            submit = SubmitField("Save")
            pass
        form = F()

        if request.method == 'POST' and form.validate():
            # get the params
            params = request.form.to_dict()
            del(params['locname'])
            del(params['csrf_token'])
            del(params['locid'])
            if 'locisHome' in params:
                isHome = True
                del(params['locisHome'])
            else:
                isHome = False
            # update or insert
            if int(lid) == 0:
                loc = app.db.add_full_location(request.form['locname'], 'location', isHome, params)
            else:
                loc = app.db.update_full_location(int(lid), request.form['locname'], 'location', isHome, params)
            flash(gettext("Location update successfull"), 'info')
            return redirect("/locations")

        return render_template('locations_edit.html',
            form = form,
            formatted_address = formatted_address,
            mactive = "locations")


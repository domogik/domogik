from flask_login import login_required
from flask import request, flash, redirect
from domogik.admin.application import app, render_template
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
from wtforms.validators import Required, InputRequired
from domogik.common.utils import ucode

@app.route('/locations')
@login_required
def locations():
    locations = []
    persons = []
    with app.db.session_scope():
        db_locations = app.db.get_all_location()
        for loc in db_locations:
            locations.append({'id' : loc.id,
                              'name' : loc.name,
                              'isHome' : loc.isHome,
                              'type' : loc.type,
                              'radius' : app.db.get_location_param(loc.id, "radius"),
                              'lat' : app.db.get_location_param(loc.id, "lat"),
                              'lng' : app.db.get_location_param(loc.id, "lng")})

        db_persons = app.db.list_persons()
        for per in db_persons:
            if per.location_sensor:
                all_res = app.db.get_last_sensor_value(per.location_sensor)
                res = all_res[0] # by the way, there is only one row result ;)
                   
                print(res)
                last_seen = res['timestamp']
                if res['value_str'] is None:
                    # no location yet, no need to display, no need to add in the list ;)
                    continue
                lat = res['value_str'].split(",")[0]
                lng = res['value_str'].split(",")[1]
                persons.append({'id' : per.id,
                                'first_name' : per.first_name,
                                'last_name' : per.last_name,
                                'location_sensor' : per.location_sensor,
                                'last_seen' : last_seen,
                                'lat' : lat,
                                'lng' : lng})

        return render_template('locations.html',
            locations = locations,
            persons = persons,
            mactive = "locations")

@app.route('/locations/del/<lid>')
@login_required
def locations_del(lid):
    with app.db.session_scope():
        app.db.del_location(lid)
    return redirect("/locations")

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

        lisHomeDisabled = False
        if app.db.get_home_location():
            lisHomeDisabled = True

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
            if app.db.get_home_location() is None:
                # we can have only one home location
                locisHome = BooleanField("is Home", [], default=lisHome)
            else:
                locisHome = HiddenField("is Home", [], default=lisHome)
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
                if params['locisHome'] == 'True': 
                    isHome = True
                else:
                    isHome = False
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


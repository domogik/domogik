from flask_login import login_required
from flask import request, flash, redirect
from domogik.admin.application import app, render_template, timeit
try:
    from flask_wtf import FlaskForm
except ImportError:
    from flaskext.wtf import FlaskForm
    pass
try:
    from flask_babel import gettext, ngettext
except ImportError:
    from flask.ext.babel import gettext, ngettext
    pass
from wtforms import TextField, HiddenField, BooleanField, SubmitField
from wtforms.validators import Required, InputRequired

from domogik.common.utils import ucode
from domogikmq.pubsub.publisher import MQPub


@app.route('/locations')
@login_required
@timeit
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
@timeit
def locations_del(lid):
    with app.db.session_scope():
        app.db.del_location(lid)
    return redirect("/locations")

@app.route('/locations/edit/<lid>', methods=['GET', 'POST'])
@login_required
@timeit
def locations_edit(lid):
    with app.db.session_scope():
        if int(lid) == 0:
            llat = '46.860191'
            llng =  '2.373655'
            formatted_address = ''
            lname = ''
            lisHome = 1
            lzoom = 5
            lctrl_type = "circle"
            lctrl_area = 10
        else:
            loc = app.db.get_location(lid)
            formatted_address = list(filter(lambda n: n.key == 'formatted_address', loc.params))[0].value
            lname = loc.name
            lisHome = loc.isHome
            llat = list(filter(lambda n: n.key == 'lat', loc.params))[0].value
            llng = list(filter(lambda n: n.key == 'lng', loc.params))[0].value
            lzoom = 10
            try : # maintain backward compatibility with radius key
                lctrl_type = list(filter(lambda n: n.key == 'ctrl_type', loc.params))[0].value
                lctrl_area = list(filter(lambda n: n.key == 'ctrl_area', loc.params))[0].value
            except :
                lctrl_type = "circle"
                lctrl_area = list(filter(lambda n: n.key == 'radius', loc.params))[0].value

        class F(FlaskForm):
            locid = HiddenField("lid", default=lid)
            ctrl_type = HiddenField("ctrl_type", default=lctrl_type)
            lat = HiddenField("lat", default=llat)
            lng = HiddenField("lng", default=llng)
            formatted_address = HiddenField("formatted_address")
            postal_code = HiddenField("postal_code")
            locality = HiddenField("locality")
            country = HiddenField("country")
            country_short = HiddenField("country_short")
            ctrl_area = HiddenField("ctrl_area", default=lctrl_area)
            locname = TextField("Name", [Required()], default=lname)
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
                if params['locisHome'] in ['y', 'true', 'True']:
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
            pub = MQPub(app.zmq_context, 'adminhttp')
            pub.send_event('location.update',
                           {"location_id" : lid,
                            "params" : params})
            flash(gettext("Location updated successfully"), 'info')
            return redirect("/locations")
        print(u"*********************************************")
        print(form.data, lctrl_type, lctrl_area)
        return render_template('locations_edit.html',
            form = form,
            formatted_address = formatted_address,
            map_zoom = lzoom,
            mactive = "locations")


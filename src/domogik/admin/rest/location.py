from domogik.admin.application import app, json_response, timeit
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response, request
from flask_login import login_required

@app.route('/rest/position/<string:person_id>/<string:data>', methods = ["GET"])
@json_response
@login_required
def position_get(person_id, data):
    """
    @api {get} /position/ Store a position for a person
    @apiName storePosition
    @apiGroup Position
    @apiVersion 0.6.0

    @apiSuccess {json} result A json result

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "status": "OK"
        }
    """
    with app.db.session_scope():
        person = app.db.get_person(person_id)
        if person:
            if person.location_sensor:
                # generate a mq pub message that can be catched by the xplgw
                app.mqpub.send_event('client.sensor', {person.location_sensor : data})
                data = {"status": "OK"}
            else:
                data = {"status": "NOK", "error": "Location not enabled for this person"}
        else:
            data = {"status": "NOK", "error": "Person Not found"}
        return 200, data

@app.route('/rest/position/<string:person_id>/', methods = ["POST"])
@json_response
@login_required
def position_post(person_id):
    """ Used for POST on /position/<device>/
        Sample for Android app Trip Tracker :
    """
    with app.db.session_scope():
        person = app.db.get_person(person_id)
        if person:
            if person.location_sensor:
	        post = request.form.to_dict()
                if 'location_name' in post:
                    # post = location_name=Werk
                    loc = app.db.get_location_by_name(post['location_name'])
                    if loc is None:
                        data = {"status": "NOK", "error": "Location '{0}' can not be found".format(post['location_name'])}
                        return 200, data
                    else:
                        # get the coordinates
                        longtitude = filter(lambda n: n.key == 'lng', loc.params)
                        if len(longtitude) > 0:
                            longtitude = longtitude[0].value
                        latitude = filter(lambda n: n.key == 'lat', loc.params)
                        if len(latitude) > 0:
                            latitude = latitude[0].value
                else:
                    #post = Dict([('locations[1][longitude]', u'-1.3015050539275859'), ('locations[0][time]', u'1414950119346'), ('locations[1][speed]', u'1.5556983'), ('locations[1][time]', u'1414958966722'), ('locations[1][latitude]', u'47.08956470569191'), ('locations[0][longitude]', u'-1.3015941102186852'), ('locations[0][latitude]', u'47.08935763509281'), ('locations[0][speed]', u'0.3824184')])
                    # find the last index
                    idx = 0
                    for key in post:
                        if idx < int(key[10:11]):
                            idx = int(key[10:11])
                    longitude = post["locations[{0}][longitude]".format(idx)]
                    latitude = post["locations[{0}][latitude]".format(idx)]
                # generate a mq pub message that can be catched by the xplgw
                data = "{0},{1}".format(latitude,longtitude)
                app.mqpub.send_event('client.sensor', {person.location_sensor : data})
                data = {"status": "OK"}
            else:
                data = {"status": "NOK", "error": "Location not enabled for this person"}
        else:
            data = {"status": "NOK", "error": "Person Not found"}
        return 200, data
    


from domogik.admin.application import app, json_response, timeit
from domogik.common.configloader import Loader
from domogikmq.pubsub.publisher import MQPub
import zmq
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response, request
from flask_login import login_required
import json
from domogikmq.pubsub.publisher import MQPub

@app.route('/rest/position/<string:person_id>/<string:data>', methods = ["GET"])
@json_response
@login_required
def position_get(person_id, data):
    """
    @api {get} /rest/position/<person id or login>/<location data>  Store a position for a person
    @apiName storePosition
    @apiGroup Position
    @apiVersion 0.6.0

    @apiSuccess {json} result A json result

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "status": "OK"
        }

    @apiSampleRequest /rest/position/john/47.47,-1.5050
    """
    with app.db.session_scope():
        person = app.db.get_person(person_id)
        if person:
            if person.location_sensor:
                # generate a mq pub message that can be catched by the xplgw
                pub = MQPub(app.zmq_context, 'admin-views')
                pub.send_event('client.sensor', {person.location_sensor : data})
                data = {"status": "OK"}
            else:
                data = {"status": "ERROR", "error": "Location not enabled for this person"}
        else:
            data = {"status": "ERROR", "error": "Person not found"}
        return 200, data

@app.route('/rest/position/<string:person_id>/', methods = ["POST"])
@json_response
@login_required
def position_post(person_id):
    """ 
    @api {post} /rest/position/<person id or login>/  Store a position for a person
    @apiName storePosition
    @apiGroup Position
    @apiVersion 0.6.0

    @apiSuccess {json} result A json result

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "status": "OK"
        }

    @apiSampleRequest:
        The last current position
        [
          {
            "latitude" : "9.9999",
            "longitude" : "9.9999"
          }
        ]
        
        A position at a given time
        [
          {
            "latitude" : "9.9999",
            "longitude" : "9.9999",
            "timestamp" : 1234567890
          }
        ]
        
        The last current named position :
        [
          {
            "location_name" : "xxxx"
          }
        ]
        
        A named position at a given time
        [
          {
            "location_name" : "xxxx",
            "timestamp" : 1234567890
          }
        ]
        
        The last N positions :
        [
          { // no timestamp, so the current one
            "latitude" : "9.9999",
            "longitude" : "9.9999",
          },
          { // a timestamp, so an old one which could not be sent to rest due to
        network issues
            "latitude" : "9.9999",
            "longitude" : "9.9999",
            "timestamp" : 1234567890
          },
          { // a timestamp, so an old one which could not be sent to rest due to
        network issues. It is also a named one
            "location_name" : "work",
            "timestamp" : 1234567890
          },
          ...
        ]
    """
    mqpub = MQPub(zmq.Context(), 'adminhttp')

    with app.db.session_scope():
        # First, try to find if the person id is :
        # - int : a real person id
        # - string : the user accoun login related to the id
        try: 
            # a real person id
            int(person_id)
        except ValueError:
            # not an integer... let's find the person id from the given user account login
            account = app.db.get_user_account_by_login(person_id)
            person_id = account.person_id


        # process the person id
        person = app.db.get_person(person_id)
        if person:
            if person.location_sensor:

                # print(request.data)
                # [{"latitude" : "47.0894508", 
                #    "longitude" : "-1.3016079",
                #    "location_name": "xxxx",
                #    "timestamp" : ..... }]                      

                loc_data = json.loads(request.data)

                # for each given location...
                for a_loc_data in loc_data:
                    sensor_data = {}
                    if 'timestamp' in a_loc_data:
                        sensor_data["atTimestamp"] = a_loc_data["timestamp"]
                        
                    if 'location_name' in a_loc_data:
                        if a_loc_data['location_name'] == "":
                            location_name = None
                        else:
                            location_name = a_loc_data['location_name']
                    else:
                        location_name = None

                    if location_name != None:
                        loc = app.db.get_location_by_name(a_loc_data['location_name'])
                        if loc is None:
                            data = {"status": "ERROR", "error": "Location '{0}' can not be found".format(a_loc_data['location_name'])}
                            return 200, data
                        else:
                            print(u"Get location from location name...")
                            # get the coordinates
                            longitude = filter(lambda n: n.key == 'lng', loc.params)
                            if len(longitude) > 0:
                                longitude = longitude[0].value
                            latitude = filter(lambda n: n.key == 'lat', loc.params)
                            if len(latitude) > 0:
                                latitude = latitude[0].value

                    else:
                        longitude = a_loc_data["longitude"]
                        latitude = a_loc_data["latitude"]

                    # generate a mq pub message that can be catched by the xplgw
                    position = "{0},{1}".format(latitude,longitude)
                    sensor_data[person.location_sensor] = position 
                    print(sensor_data)
                    mqpub.send_event('client.sensor', sensor_data)

                data = {"status": "OK"}
            else:
                data = {"status": "ERROR", "error": "Location not enabled for this person"}
        else:
            data = {"status": "ERROR", "error": "Person Not found"}
        return 200, data
    


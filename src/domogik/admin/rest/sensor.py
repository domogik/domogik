from domogik.admin.application import app, json_response, register_api
from flask import request
from flask.views import MethodView
from flask_login import login_required
import traceback

@app.route('/rest/sensor/since/<timestamp>', methods=['GET'])
@json_response
@login_required
def sensor_since(timestamp):
    """
    @api {get} /rest/sensor/since/<timestamp> Returns all sensors changed since this timestamp
    @apiName getSensorSince
    @apiGroup Sensor
    @apiVersion 0.4.1

    @apiParam {timestamp} timestamp the unix timestamp

    @apiSuccess {json} result The json representing of the sensors

    @apiSampleRequest /sensor/since/123456

    @apiSuccessExample Success-Response:
	HTTTP/1.1 200 OK
	[
	    {
		"conversion": "",
		"history_duplicate": false,
		"history_round": 0,
		"name": "Power_sensor",
		"data_type": "DT_Power",
		"last_received": 1410857820,
		"value_max": 652,
		"value_min": 54,
		"history_max": 0,
		"incremental": false,
		"timeout": 0,
		"history_store": true,
		"history_expire": 0,
		"formula": null,
		"last_value": "241.0",
		"id": 2,
		"reference": "power",
		"device_id": 2
	    }
	]

    @apiErrorExample Error-Response:
	HTTTP/1.1 404 Not Found
    """
    try:
        app.json_stop_at = ["core_device"]
        app.db.open_session()
        b = app.db.get_all_sensor_since(timestamp)
        app.db.close_session()
        return 200, b
    except:
        msg = u"Error while getting the sensors. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

class sensorAPI(MethodView):
    decorators = [login_required, json_response]

    def get(self, id):
        """
        @api {get} /rest/sensor/<id> Retrieve a/all sensors
        @apiName getSensor
        @apiGroup Sensor
        @apiVersion 0.4.1

        @apiParam {Number} [id] If provided only the sensor that matches this ID will be provided

        @apiSuccess {json} result The json representation of the sensor

        @apiSuccessExample Success-Response:
            HTTTP/1.1 200 OK
            {
                "conversion": "",
                "history_duplicate": false,
                "history_round": 0,
                "name": "Power_sensor",
                "data_type": "DT_Power",
                "last_received": 1410857820,
                "value_max": 652,
                "value_min": 54,
                "history_max": 0,
                "incremental": false,
                "timeout": 0,
                "history_store": true,
                "history_expire": 0,
                "formula": null,
                "last_value": "241.0",
                "id": 2,
                "reference": "power",
                "device_id": 2
            }

        @apiErrorExample Error-Response:
            HTTTP/1.1 404 Not Found
        """
        try:
            app.json_stop_at = ["core_device"]
            app.db.open_session()
            if id != None:
                b = app.db.get_sensor(id)
            else:
                b = app.db.get_all_sensor()
            app.db.close_session()
            return 200, b
        except:
            msg = u"Error while getting the sensor(s). Error is : {0}".format(traceback.format_exc())
            app.logger.error(msg)
            return 500, {'msg': msg}

    def put(self, id):
        """
        @api {put} /rest/sensor/id Update a specifick sensor
        @apiName putSensor
        @apiGroup Sensor
        @apiVersion 0.4.1

        @apiParamTitle (url) Url parameters
        @apiParam (url) {Number} id The sensorId to update
        @apiParamTitle (data) Post parameters
        @apiParam (data) {Number} round The round value
        @apiParam (data) {Boolean} store If set the history for this sensor will be stored in sensorhistory
        @apiParam (data) {Number} max The maximum number of items kept in the sensor-history table for thie sensor, 0= infinite number
        @apiParam (data) {Number} expire The maximum age (in seconds) entries are kept in the sensor-history
        @apiParam (data) {Number} timeout The mximum timeout we should have between 2 updates
        @apiParam (data) {String} formula The formula that needs to be applied 

        @apiSuccess {json} result The json representation of the updated sensor

        @apiSuccessExample Success-Response:
            HTTTP/1.1 200 OK
            {
                "conversion": "",
                "history_duplicate": false,
                "history_round": 0,
                "name": "Power_sensor",
                "data_type": "DT_Power",
                "last_received": 1410857820,
                "value_max": 652,
                "value_min": 54,
                "history_max": 0,
                "incremental": false,
                "timeout": 0,
                "history_store": true,
                "history_expire": 0,
                "formula": null,
                "last_value": "241.0",
                "id": 2,
                "reference": "power",
                "device_id": 2
            }

        @apiErrorExample Error-Response:
            HTTTP/1.1 404 Not Found
        """
        try:
            with app.db.session_scope():
                sid = data['sid']
                if 'history_round' not in request.get:
                    hround = None
                else:
                    hround = request.get['history_round']
                if 'history_store' not in request.get:
                    hstore = None
                else:
                    hstore = request.get['history_store']
                if 'history_max' not in request.get:
                    hmax = None
                else:
                    hmax = request.get['history_max']
                if 'history_expire' not in request.get:
                    hexpire = None
                else:
                    hexpire = request.get['history_expire']
                if 'timeout' not in request.get:
                    timeout = None
                else:
                    timeout = request.get['timeout']
                if 'formula' not in request.get:
                    formula = None
                else:
                    formula = request.get['formula']
                if 'data_type' not in request.get:
                    data_type = None
                else:
                    data_type = request.get['data_type']
                # do the update
                res = app.db.update_sensor(id, \
                     history_round=hround, \
                     history_store=hstore, \
                     history_max=hmax, \
                     history_expire=hexpire, \
                     timeout=timeout, \
                     formula=formula, \
                     data_type=data_type)
                if res:
                    return 201, app.db.get_sensor(id)
                else:
                    return 500, None
        except:
            msg = u"Error while updating the sensor. Error is : {0}".format(traceback.format_exc())
            app.logger.error(msg)
            return 500, {'msg': msg}

register_api(sensorAPI, 'sensor_api', '/rest/sensor/', pk='id')

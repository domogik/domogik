from domogik.rest.url import *
from flask import request
from flask.views import MethodView

class sensorAPI(MethodView):
    decorators = [json_response, timeit]

    def get(self, id):
        """
        @api {get} /sensor/<id> Retrieve a/all sensors
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
        urlHandler.json_stop_at = ["core_device"]
        if id != None:
            b = urlHandler.db.get_sensor(id)
        else:
            b = urlHandler.db.get_all_sensor()
        return 200, b

    def put(self, id):
        """
        @api {put} /sensor/id Update a specifick sensor
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

        dbr = urlHandler.db.update_sensor(\
                id, \
                history_round=request.form.get('round'), \
                history_store=request.form.get('store'), \
                history_max=request.form.get('max'), \
                history_expire=request.form.get('expire') \
                )
        return 200, dbr

register_api(sensorAPI, 'sensor_api', '/sensor/', pk='id')

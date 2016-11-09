from __future__ import absolute_import, division, print_function, unicode_literals
from domogik.admin.application import app, json_response, register_api
from flask import request
from flask.views import MethodView
from flask_login import login_required

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
        app.json_stop_at = ["core_device"]
        app.db.open_session()
        if id != None:
            b = app.db.get_sensor(id)
        else:
            b = app.db.get_all_sensor()
        app.db.close_session()
        return 200, b

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
        cli = MQSyncReq(app.zmq_context)
        msg = MQMessage()
        msg.set_action('sensor.update')
        msg.add_data('sid', id)
        msg.add_data('history_round', request.get['round'])
        msg.add_data('history_store', request.get['store'])
        msg.add_data('history_max', request.get['max'])
        msg.add_data('history_expire', request.get['expire'])
        msg.add_data('timeout', request.get['timeout'])
        msg.add_data('formula', request.get['formula'])
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            data = res.get_data()
            if data["status"]:
                return 201, data["result"]
            else:
                return 500, data["reason"]
        else:
            return 500, "DbMgr did not respond on the sensor.update, check the logs"
        return 200, app.db.get_device(did)


register_api(sensorAPI, 'sensor_api', '/rest/sensor/', pk='id')

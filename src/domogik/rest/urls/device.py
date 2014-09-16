from domogik.xpl.common.plugin import DMG_VENDOR_ID
from domogik.rest.url import urlHandler, json_response, register_api, timeit
from flask.views import MethodView
from flask import request
import zmq
import copy
import json
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

@urlHandler.route('/device/old/', methods=['GET'])
@json_response
@timeit
def device_list_old():
    b = urlHandler.db.list_old_devices()
    return 200, b

@urlHandler.route('/device/params/<client_id>/<dev_type_id>', methods=['GET'])
@json_response
@timeit
def device_params(client_id, dev_type_id):
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('device.params')
    msg.add_data('device_type', dev_type_id)
    res = cli.request('dbmgr', msg.get(), timeout=10)
    result = ""
    if res:
        res = res.get_data()
        result = res['result'];
        result["client_id"] = client_id
    # return the info
    return 200, result

class deviceAPI(MethodView):
    decorators = [json_response, timeit]

    def get(self, did):
        """
        @api {get} /device/<id> Retrieve a/all domogik Device
        @apiName getDevice
        @apiGroup Device

        @apiParam {Number} [id] If provided only the device that matches the id will be returned

        @apiSuccess {json} result The json representation of the device

        @apiSuccessExample Success-Response:
            HTTTP/1.1 200 OK
            {
                "xpl_stats": {
                    "get_temp": {
                        "json_id": "get_temp",
                        "schema": "sensor.basic",
                        "id": 4,
                        "parameters": {
                            "dynamic": [
                                {
                                    "ignore_values": "",
                                    "sensor_name": "temp",
                                    "key": "current"
                                }
                            ],
                            "static": [
                                {
                                    "type": "integer",
                                    "value": "2",
                                    "key": "device"
                                },
                                {
                                    "type": null,
                                    "value": "temp",
                                    "key": "type"
                                },
                                {
                                    "type": null,
                                    "value": "c",
                                    "key": "units"
                                }
                            ]
                        },
                        "name": "get_temp"
                    },
                    ...
                },
                "commands": {
                    ...
                },
                "description": "Test Temp",
                "reference": "VMB1TS",
                "xpl_commands": {
                    ...
                },
                "client_id": "plugin-velbus.igor",
                "device_type_id": "velbus.temp",
                "sensors": {
                    "temp": {
                        "value_min": 21.875,
                        "data_type": "DT_Temp",
                        "incremental": false,
                        "id": 4,
                        "reference": "temp",
                        "conversion": "",
                        "name": "temp_sensor",
                        "last_received": 1410857216,
                        "timeout": 0,
                        "formula": null,
                        "last_value": "29.1875",
                        "value_max": 37.4375
                    }
                },
                "parameters": {
                    ...
                },
                "id": 3,
                "name": "Temp elentrik"
            }

        @apiErrorExample Error-Response:
            HTTTP/1.1 404 Not Found
        """
        if did != None:
            b = urlHandler.db.get_device(did)
        else:
            b = urlHandler.db.list_devices()
        if b == None:
            return 404, b
        else:
            return 200, b

    def delete(self, did):
        """
        @api {del} /device/id Delete a device
        @apiName delDevice
        @apiGroup Device

        @apiParam {Number} id The id of the device to be deleted

        @apiSuccess {json} result The json representation of the deleted device

        @apiSuccessExample Success-Response:
            HTTTP/1.1 200 OK
            {
                "xpl_stats": {
                    "get_temp": {
                        "json_id": "get_temp",
                        "schema": "sensor.basic",
                        "id": 4,
                        "parameters": {
                            "dynamic": [
                                {
                                    "ignore_values": "",
                                    "sensor_name": "temp",
                                    "key": "current"
                                }
                            ],
                            "static": [
                                {
                                    "type": "integer",
                                    "value": "2",
                                    "key": "device"
                                },
                                {
                                    "type": null,
                                    "value": "temp",
                                    "key": "type"
                                },
                                {
                                    "type": null,
                                    "value": "c",
                                    "key": "units"
                                }
                            ]
                        },
                        "name": "get_temp"
                    },
                    ...
                },
                "commands": {
                    ...
                },
                "description": "Test Temp",
                "reference": "VMB1TS",
                "xpl_commands": {
                    ...
                },
                "client_id": "plugin-velbus.igor",
                "device_type_id": "velbus.temp",
                "sensors": {
                    "temp": {
                        "value_min": 21.875,
                        "data_type": "DT_Temp",
                        "incremental": false,
                        "id": 4,
                        "reference": "temp",
                        "conversion": "",
                        "name": "temp_sensor",
                        "last_received": 1410857216,
                        "timeout": 0,
                        "formula": null,
                        "last_value": "29.1875",
                        "value_max": 37.4375
                    }
                },
                "parameters": {
                    ...
                },
                "id": 3,
                "name": "Temp elentrik"
            }

        @apiErrorExample Error-Response:
            HTTTP/1.1 404 Not Found
        """
        b = urlHandler.db.del_device(did)
        urlHandler.reload_stats()        
        return 200, b

    def post(self):
        """ Create a new device
            Get all the clients details
            Finally, call the database function to create the device and give it the device types list and clients details : they will be used to fill the database as the json structure is recreated in the database
        """
        print "=========="
        print request.form
        type(json.loads(request.form.get('params')))
        cli = MQSyncReq(urlHandler.zmq_context)
        msg = MQMessage()
        msg.set_action('device.create')
        msg.set_data({'data': json.loads(request.form.get('params'))})
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            data = res.get_data()
            if data["status"]:
                urlHandler.reload_stats()        
                return 201, data["result"]
            else:
                return 500, data["reason"]
        else:
            return 500, "DbMgr did not respond on the device.create, check the logs"
        return 201, null

    def put(self, did):
        b = urlHandler.db.update_device(
            did,
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('reference'),
        )
        urlHandler.reload_stats()        
        return 200, urlHandler.db.get_device(did)

register_api(deviceAPI, 'device', '/device/', pk='did', pk_type='int')

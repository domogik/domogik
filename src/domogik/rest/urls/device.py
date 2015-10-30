from domogik.xpl.common.plugin import DMG_VENDOR_ID
from domogik.rest.url import urlHandler, json_response, register_api, timeit
from flask.views import MethodView
from flask import request
import zmq
import copy
import json
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

@urlHandler.route('/device/params/<client_id>/<dev_type_id>', methods=['GET'])
@json_response
@timeit
def device_params(client_id, dev_type_id):
    """
    @api {get} /device/params/<clientId>/<device_type> Retrieve the needed parameter for creating a device
    @apiName getDeviceParams
    @apiGroup Device
    @apiVersion 0.4.1

    @apiParam {String} clientId The clientId to request the parameter from
    @apiParam {String} device_type The device type to request the parameters for

    @apiSuccess {json} result The json representing the device type
    
    @apiSampleRequest /device/params/plugin-velbus.igor/velbus.relay

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "xpl_stats": {
                "get_level_bin": []
            },
            "name": "",
            "reference": "",
            "xpl": [
                {
                    "max_value": 4,
                    "min_value": 1,
                    "type": "integer",
                    "description": "The channel number",
                    "key": "channel"
                },
                {
                    "max_value": 255,
                    "min_value": 0,
                    "type": "integer",
                    "description": "The decimal address",
                    "key": "device"
                }
            ],
            "xpl_commands": {
                "set_level_bin": []
            },
            "global": [],
            "client_id": "plugin-velbus.igor",
            "device_type": "velbus.relay",
            "description": ""
        }

    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """
    cli = MQSyncReq(urlHandler.zmq_context)
    msg = MQMessage()
    msg.set_action('device.params')
    msg.add_data('device_type', dev_type_id)
    res = cli.request('dbmgr', msg.get(), timeout=10)
    result = {}
    if res:
        res = res.get_data()
        print(type(res['result']))
        # test if dbmgr returns a str ("Failed")
        # and process this case...
        if isinstance(res['result'], str) or isinstance(res['result'], unicode):
            return 500, "DbMgr did not respond as expected, check the logs. Response is : {0}. {1}".format(res['result'], res['reason'])
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

        @apiSuccess {String} none No data is returned

        @apiSuccessExample Success-Response:
            HTTTP/1.1 200 OK

        @apiErrorExample Error-Response:
            HTTTP/1.1 500 INTERNAL SERVER ERROR
        """
        cli = MQSyncReq(urlHandler.zmq_context)
        msg = MQMessage()
        msg.set_action('device.delete')
        msg.set_data({'did': did})
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            data = res.get_data()
            if data["status"]:
                return 201, None
            else:
                return 500, data["reason"]
        else:
            return 500, "DbMgr did not respond on the device.delete, check the logs"
        return 201, None

    def post(self):
        """
        @api {post} /device Create a device
        @apiName postDevice
        @apiGroup Device

        @apiParamTitle (data) Post parameters
        @apiParam (data) {Json} params The populated device params json string

        @apiSuccess {json} result The json representation of the created device

        @apiSuccessExample Success-Response:
            HTTTP/1.1 201 Created
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
            HTTTP/1.1 500 Internal Server Error
        """
        cli = MQSyncReq(urlHandler.zmq_context)
        msg = MQMessage()
        msg.set_action('device.create')
        msg.set_data({'data': json.loads(request.form.get('params'))})
        res = cli.request('dbmgr', msg.get(), timeout=10)
        if res is not None:
            data = res.get_data()
            if data["status"]:
                return 201, data["result"]
            else:
                return 500, data["reason"]
        else:
            return 500, "DbMgr did not respond on the device.create, check the logs"
        return 201, None

    def put(self, did):
        """
        @api {put} /device/<id> Update a specifick device
        @apiName putDevice
        @apiGroup Device

        @apiParamTitle (url) Url parameters
        @apiParam (url) {Number} id The deviceId to update
        @apiParamTitle (data) Post parameters
        @apiParam (data) {String} name The new name for the device
        @apiParam (data) {String} description The new description for the device
        @apiParam (data) {String} reference The new reference for the device

        @apiSuccess {json} result The json representation of the updated device

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

        b = urlHandler.db.update_device(
            did,
            request.form.get('name'),
            request.form.get('description'),
            request.form.get('reference'),
        )
        return 200, urlHandler.db.get_device(did)

register_api(deviceAPI, 'device', '/device/', pk='did', pk_type='int')

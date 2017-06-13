from domogik.xpl.common.plugin import DMG_VENDOR_ID
from domogik.common.utils import build_deviceType_from_packageJson
from domogik.admin.application import app, json_response, register_api, timeit
from flask.views import MethodView
from flask import request
import zmq
import copy
import json
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage
from flask_login import login_required
import traceback

@app.route('/rest/device/since/<timestamp>', methods=['GET'])
@json_response
@login_required
def device_since(timestamp):
    """
    @api {get} /rest/device/since/<timestamp> Returns all devices changed since this timestamp
    @apiName getSensorSince
    @apiGroup Sensor
    @apiVersion 0.4.1

    @apiParam {timestamp} timestamp the unix timestamp

    @apiSuccess {json} result The json representing of the device

    @apiSampleRequest /device/since/123456
    
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
    try:
        app.db.open_session()
        b = app.db.list_devices_by_timestamp(timestamp)
        app.db.close_session()
    except:
        msg = u"Error while getting the devices list. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

    return 200, b

@app.route('/rest/device/params/<client_id>/<dev_type_id>', methods=['GET'])
@json_response
@login_required
def device_params(client_id, dev_type_id):
    """
    @api {get} /rest/device/params/<clientId>/<device_type> Retrieve the needed parameter for creating a device
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
    try:
        (result, reason, status) = build_deviceType_from_packageJson(app.zmq_context, dev_type_id, client_id)
    except:
        msg = u"Error while getting the device parameters. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}
    # return the info
    return 200, result

class deviceAPI(MethodView):
    decorators = [login_required, json_response]

    def get(self, did):
        """
        @api {get} /rest/device/<id> Retrieve a/all domogik Device
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
        try:
            app.db.open_session()
            if did != None:
                b = app.db.get_device(did)
            else:
                b = app.db.list_devices()
            app.db.close_session()
            if b == None:
                return 404, b
            else:
                return 200, b
        except:
            msg = u"Error while getting the devices list. Error is : {0}".format(traceback.format_exc())
            app.logger.error(msg)
            return 500, {'msg' : msg}

    def delete(self, did):
        """
        @api {del} /rest/device/id Delete a device
        @apiName delDevice
        @apiGroup Device

        @apiParam {Number} id The id of the device to be deleted

        @apiSuccess {String} none No data is returned

        @apiSuccessExample Success-Response:
            HTTTP/1.1 200 OK

        @apiErrorExample Error-Response:
            HTTTP/1.1 500 INTERNAL SERVER ERROR
        """
        try:
            with app.db.session_scope():
                res = app.db.del_device(did)
                if not res:
                    msg = u"Device deletion failed"
                    app.logger.error(msg)
                    return 500, {'msg' : msg }
                else:
                    return 201, None
        except:
            msg = u"Error while deleting the device. Error is : {0}".format(traceback.format_exc())
            app.logger.error(msg)
            return 500, {'msg': msg}

    def post(self):
        """
        @api {post} /rest/device Create a device
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
        try:
            params = json.loads(request.form.get('params'))
            status = True
            print params
            cli = MQSyncReq(app.zmq_context)
            msg = MQMessage()
            msg.set_action('device_types.get')
            msg.add_data('device_type', params['device_type'])
            res = cli.request('manager', msg.get(), timeout=10)
            del cli
            if res is None:
                status = False
                reason = "Manager is not replying to the mq request"
            pjson = res.get_data()
            if pjson is None:
                status = False
                reason = "No data for {0} found by manager".format(params['device_type'])
            pjson = pjson[params['device_type']]
            if pjson is None:
                status = False
                reason = "The json for {0} found by manager is empty".format(params['device_type'])
    
            with app.db.session_scope():
                if status:
                    # call the add device function
                    res = app.db.add_full_device(params, pjson)
                    if not res:
                        status = False
                        reason = "An error occured while adding the device in database. Please check the file admin.log for more informations"
                    else:
                        status = True
                        reason = False
                        result = res
                if status:
                    return 201, result
                else:
                    return 500, {'msg' : reason}
        except:
            msg = u"Error while creating the device. Error is : {0}".format(traceback.format_exc())
            app.logger.error(msg)
            return 500, {'msg': msg}

    def put(self, did):
        """
        @api {put} /rest/device/<id> Update a specifick device
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
        try:
            if 'name' in request.form:
                name = request.form['name']
            else:
                name = None
            if 'description' in request.form:
                desc = request.form['description']
            else:
                desc = None
            if 'reference' in request.form:
                ref = request.form['reference']
            else:
                ref = None
            res = app.db.update_device(did, \
                d_name=name, \
                d_description=desc, \
                d_reference=ref)
            if res:
                return 201, app.db.get_device(did)
            else:
                return 500, {'msg' : u"Error while updating the device"}
        except:
            msg = u"Error while updating the device. Error is : {0}".format(traceback.format_exc())
            app.logger.error(msg)
            return 500, {'msg': msg}

register_api(deviceAPI, 'device', '/rest/device/', pk='did', pk_type='int')

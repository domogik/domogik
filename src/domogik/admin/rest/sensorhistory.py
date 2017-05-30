from domogik.admin.application import app, json_response, timeit
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response
from flask_login import login_required
import traceback

@app.route('/rest/sensorhistory/id/<int:sid>/latest')
@app.route('/rest/sensorhistory/id/<int:sid>/latest/')
@json_response
@login_required
@timeit
def sensorHistory_latest(sid):
    """
    @api {get} /rest/sensorhistory/id/<id>/latest Retrieve the last stored value for a sensor
    @apiName getSensorHistoryLatest
    @apiGroup SensorHistory
    @apiVersion 0.5.0

    @apiParam {Number} id The id of the sensor we want to retrieve the history from

    @apiSuccess {json} result The json representing the latest value
    
    @apiSampleRequest /rest/ensorhistory/id/3/latest

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        [{"timestamp": 1449216514.0, "value_str": "0688459268", "value_num": 688459000.0}]

    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """

    """
    @api {get} /rest/sensorhistory/id/<id>/latest Retrieve the last stored value for a sensor
    @apiName getSensorHistoryLatest
    @apiGroup SensorHistory
    @apiVersion 0.4.1

    @apiParam {Number} id The id of the sensor we want to retrieve the history from

    @apiSuccess {json} result The json representing the latest value
    
    @apiSampleRequest /rest/ensorhistory/id/2/latest

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        [
            {
                "sensor_id": 2,
                "original_value_num": 195.0,
                "value_str": "195.0",
                "date": "2014-10-08T08:41:13",
                "id": 1860242,
                "value_num": 195.0
            }
        ]

    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """
    try:
        app.db.open_session()
        b = app.db.list_sensor_history(sid, 1)
        app.db.close_session()
        return 200, b
    except:
        msg = u"Error while getting the sensor history. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

@app.route('/rest/sensorhistory/id/<int:sid>/last/<int:num>')
@json_response
@login_required
@timeit
def sensorHistory_last(sid, num):
    """
    @api {get} /rest/sensorhistory/id/<id>/last/<num> Retrieve the last x number of stored value for a sensor
    @apiName getSensorHistoryLast
    @apiGroup SensorHistory
    @apiVersion 0.5.0

    @apiParam {Number} id The id of the sensor we want to retrieve the history from
    @apiParam {Number} num The number of historys we want to retrieve

    @apiSuccess {json} result The json representing the latest value

    @apiSampleRequest /rest/sensorhistory/id/3/last/3

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        [{"timestamp": 1449216514.0, "value_str": "0688459268", "value_num": 688459000.0}, {"timestamp": 1449181378.0, "value_str": "0688459268", "value_num": 688459000.0}, {"timestamp": 1449178485.0, "value_str": "0102030405", "value_num": 102030000.0}]

    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """

    """
    @api {get} /rest/sensorhistory/id/<id>/last/<num> Retrieve the last x number of stored value for a sensor
    @apiName getSensorHistoryLast
    @apiGroup SensorHistory
    @apiVersion 0.4.1

    @apiParam {Number} id The id of the sensor we want to retrieve the history from
    @apiParam {Number} num The number of historys we want to retrieve

    @apiSuccess {json} result The json representing the latest value

    @apiSampleRequest /rest/sensorhistory/id/2/last/3

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        [
            {
                "sensor_id": 2,
                "original_value_num": 195.0,
                "value_str": "195.0",
                "date": "2014-10-08T08:41:13",
                "id": 1860242,
                "value_num": 195.0
            }, 
            {
                "sensor_id": 2,
                "original_value_num": 139.0,
                "value_str": "139.0",
                "date": "2014-10-08T08:36:59",
                "id": 1860207,
                "value_num": 139.0
            },
            {
                "sensor_id": 2,
                "original_value_num": 94.0,
                "value_str": "94.0",
                "date": "2014-10-08T08:32:45",
                "id": 1860183,
                "value_num": 94.0
            }
        ]

    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """
    try:
        app.db.open_session()
        b = app.db.list_sensor_history(sid, num)
        app.db.close_session()
        return 200, b
    except:
        msg = u"Error while getting the sensor history. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

@app.route('/rest/sensorhistory/id/<int:sid>/from/<int:ftime>')
@json_response
@login_required
@timeit
def sensorHistory_from(sid, ftime):
    """
    @api {get} /rest/sensorhistory/id/<id>/from/<tstamp> Retrieve the history from a certain timestamp on
    @apiName getSensorHistoryFrom
    @apiGroup SensorHistory
    @apiVersion 0.4.1

    @apiParam {Number} id The id of the sensor we want to retrieve the history from
    @apiParam {Number} tstamp The unixtimestamp from what time you want the history to start

    @apiSuccess {json} result The json representing the latest value

    @apiSampleRequest /rest/sensorhistory/id/2/from/1412750000

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        [
            {
                "sensor_id": 2,
                "original_value_num": 139.0,
                "value_str": "139.0",
                "date": "2014-10-08T08:36:59",
                "id": 1860207,
                "value_num": 139.0
            },
            {
                "sensor_id": 2,
                "original_value_num": 195.0,
                "value_str": "195.0",
                "date": "2014-10-08T08:41:13",
                "id": 1860242,
                "value_num": 195.0
            },
            {
                "sensor_id": 2,
                "original_value_num": 115.0,
                "value_str": "115.0",
                "date": "2014-10-08T08:45:27",
                "id": 1860265,
                "value_num": 115.0
            }
        ]

    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """
    try:
        app.db.open_session()
        res = app.db.list_sensor_history_between(sid, ftime)
        app.db.close_session()
        return 200, res
    except:
        msg = u"Error while getting the sensor history. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

@app.route('/rest/sensorhistory/id/<int:sid>/from/<int:ftime>/to/<int:ttime>')
@json_response
@login_required
@timeit
def sensorHistory_from_to(sid, ftime, ttime):
    """
    @api {get} /rest/sensorhistory/id/<id>/from/<tstampFrom>/to/<tstampTo> Retrieve the history between 2 timestamps
    @apiName getSensorHistoryFromTo
    @apiGroup SensorHistory
    @apiVersion 0.4.1

    @apiParam {Number} id The id of the sensor we want to retrieve the history from
    @apiParam {Number} tstampFrom The unixtimestamp from what time you want the history to start
    @apiParam {Number} tstampTo The unixtimestamp to what time you want the history to show up

    @apiSuccess {json} result The json representing the latest value

    @apiSampleRequest /rest/sensorhistory/id/2/from/1412750000/to/1412760000

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        [
            {
                "sensor_id": 2,
                "original_value_num": 139.0,
                "value_str": "139.0",
                "date": "2014-10-08T08:36:59",
                "id": 1860207,
                "value_num": 139.0
            },
            {
                "sensor_id": 2,
                "original_value_num": 195.0,
                "value_str": "195.0",
                "date": "2014-10-08T08:41:13",
                "id": 1860242,
                "value_num": 195.0
            },
            {
                "sensor_id": 2,
                "original_value_num": 115.0,
                "value_str": "115.0",
                "date": "2014-10-08T08:45:27",
                "id": 1860265,
                "value_num": 115.0
            }
        ]

    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """
    try:
        app.db.open_session()
        b = app.db.list_sensor_history_between(sid, ftime, ttime)
        app.db.close_session()
        return 200, b
    except:
        msg = u"Error while getting the sensor history. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

@app.route('/rest/sensorhistory/id/<int:sid>/from/<int:ftime>/to/<int:ttime>/interval/<interval>/selector/<selector>')
@json_response
@login_required
@timeit
def sensorHistory_from_filter(sid, ftime, ttime, interval, selector):
    """
    @api {get} /rest/sensorhistory/id/<id>/from/<tstampFrom>/to/<tstampTo>/interval/<interval>/selector/<selector> Retrieve the filtered and calculated history between 2 timestamps
    @apiName getSensorHistoryFilter
    @apiGroup SensorHistory
    @apiVersion 0.4.1

    @apiParam {Number} id The id of the sensor we want to retrieve the history from
    @apiParam {Number} tstampFrom The unixtimestamp from what time you want the history to start
    @apiParam {Number} tstampTo The unixtimestamp to what time you want the history to show up
    @apiParam {String} interval The interval that we want to filter, can be week, day, hour
    @apiParam {String} selector The selector to calculate the values, can be min, max, avg or sum

    @apiSuccess {json} result The json representing the latest value

    @apiSampleRequest /rest/sensorhistory/id/2/from/1/to/1412750000/interval/week/selector/avg

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "values": [
                [2014, 3, 127.87381404174573],
                [2014, 4, 164.06675097597184],
                [2014, 5, 133.05020408163264],
                [2014, 13, 111.2654995181497],
                [2014, 14, 94.84126357354393],
                [2014, 15, 132.7441263573544],
                [2014, 16, 125.1181288858186],
                [2014, 17, 114.64241287392635],
                [2014, 18, 108.04337050805452],
                [2014, 19, 119.5510067114094],
                [2014, 20, 102.95659432387312],
                [2014, 21, 125.57661795407098],
                [2014, 22, 94.60684474123539],
                [2014, 23, 106.05806182121971],
                [2014, 24, 107.15077698446031],
                [2014, 25, 87.43400167084377],
                [2014, 26, 105.21929824561404],
                [2014, 27, 112.7610693400167],
                [2014, 28, 124.58336868901145],
                [2014, 29, 110.25020885547201],
                [2014, 30, 148.85030502111684],
                [2014, 31, 110.48454469507101],
                [2014, 32, 86.43451143451144],
                [2014, 34, 89.44956413449565],
                [2014, 35, 98.91232876712328],
                [2014, 36, 103.80341880341881],
                [2014, 37, 108.9740680713128],
                [2014, 38, 104.04922820191906],
                [2014, 39, 100.21459537572254], 
                [2014, 40, 127.29646017699115],
                [2014, 41, 121.58620689655173]
            ],
            "global_values": {
                "max": 652.0,
                "avg": 121.74901423084457,
                "min": 54.0,
                "sum": 3507.848652
            }
        }
    
    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """
    try:
        app.db.open_session()
        b = app.db.list_sensor_history_filter(
            sid=sid, frm=ftime, to=ttime,
            step_used=interval, function_used=selector)
        app.db.close_session()
        return 200, b
    except:
        msg = u"Error while getting the sensor history. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

@app.route('/rest/sensorhistory/id/<int:sid>/from/<int:ftime>/interval/<interval>/selector/<selector>')
@json_response
@login_required
@timeit
def sensorHistory_from_to_filter(sid, ftime, interval, selector):
    """
    @api {get} /rest/sensorhistory/id/<id>/from/<tstampFrom>/interval/<interval>/selector/<selector> Retrieve the filtered and calculated history starting from a certain timestamp
    @apiName getSensorHistoryFilter2
    @apiGroup SensorHistory
    @apiVersion 0.4.1

    @apiParam {Number} id The id of the sensor we want to retrieve the history from
    @apiParam {Number} tstampFrom The unixtimestamp from what time you want the history to start
    @apiParam {String} interval The interval that we want to filter, can be week, day, hour
    @apiParam {String} selector The selector to calculate the values, can be min, max, avg or sum

    @apiSuccess {json} result The json representing the latest value

    @apiSampleRequest /rest/sensorhistory/id/2/from/1/interval/week/selector/avg

    @apiSuccessExample Success-Response:
        HTTTP/1.1 200 OK
        {
            "values": [
                [2014, 3, 127.87381404174573],
                [2014, 4, 164.06675097597184],
                [2014, 5, 133.05020408163264],
                [2014, 13, 111.2654995181497],
                [2014, 14, 94.84126357354393],
                [2014, 15, 132.7441263573544],
                [2014, 16, 125.1181288858186],
                [2014, 17, 114.64241287392635],
                [2014, 18, 108.04337050805452],
                [2014, 19, 119.5510067114094],
                [2014, 20, 102.95659432387312],
                [2014, 21, 125.57661795407098],
                [2014, 22, 94.60684474123539],
                [2014, 23, 106.05806182121971],
                [2014, 24, 107.15077698446031],
                [2014, 25, 87.43400167084377],
                [2014, 26, 105.21929824561404],
                [2014, 27, 112.7610693400167],
                [2014, 28, 124.58336868901145],
                [2014, 29, 110.25020885547201],
                [2014, 30, 148.85030502111684],
                [2014, 31, 110.48454469507101],
                [2014, 32, 86.43451143451144],
                [2014, 34, 89.44956413449565],
                [2014, 35, 98.91232876712328],
                [2014, 36, 103.80341880341881],
                [2014, 37, 108.9740680713128],
                [2014, 38, 104.04922820191906],
                [2014, 39, 100.21459537572254],
                [2014, 40, 127.29646017699115],
                [2014, 41, 121.65850673194615]
            ],
            "global_values": {
                "max": 652.0,
                "avg": 121.7495103299099,
                "min": 54.0,
                "sum": 3507.848652
            }
        }
    
    @apiErrorExample Error-Response:
        HTTTP/1.1 404 Not Found
    """
    try:
        app.db.open_session()
        b = app.db.list_sensor_history_filter(
            sid=sid, frm=ftime, to=None,
            step_used=interval, function_used=selector)
        app.db.close_session()
        return 200, b
    except:
        msg = u"Error while getting the sensor history. Error is : {0}".format(traceback.format_exc())
        app.logger.error(msg)
        return 500, {'msg': msg}

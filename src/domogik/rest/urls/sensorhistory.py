from domogik.rest.url import urlHandler, json_response, timeit
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response


@urlHandler.route('/sensorhistory/id/<int:sid>/latest')
@json_response
def sensorHistory_latest(sid):
    return 200, urlHandler.db.list_sensor_history(sid, 1)

@urlHandler.route('/sensorhistory/id/<int:sid>/last/<int:num>')
@json_response
def sensorHistory_last(sid, num):
    return 200, urlHandler.db.list_sensor_history(sid, num)

@urlHandler.route('/sensorhistory/id/<int:sid>/from/<int:ftime>')
@json_response
def sensorHistory_from(sid, ftime):
    return 200, urlHandler.db.list_sensor_history_between(sid, ftime)

@urlHandler.route('/sensorhistory/id/<int:sid>/from/<int:ftime>/to/<int:ttime>')
@json_response
def sensorHistory_from_to(sid, ftime, ttime):
    return 200, urlHandler.db.list_sensor_history_between(sid, ftime, ttime)

@urlHandler.route('/sensorhistory/id/<int:sid>/from/<int:ftime>/to/<int:ttime>/interval/<interval>/selector/<selector>')
@json_response
def sensorHistory_from_filter(sid, ftime, ttime, interval, selector):
    return 200, urlHandler.db.list_sensor_history_filter(
            sid=sid, frm=ftime, to=ttime,
            step_used=interval, function_used=selector)

@urlHandler.route('/sensorhistory/id/<int:sid>/from/<int:ftime>/interval/<interval>/selector/<selector>')
@json_response
def sensorHistory_from_to_filter(sid, ftime, interval, selector):
    return 200, urlHandler.db.list_sensor_history_filter(
            sid=sid, frm=ftime, to=None,
            step_used=interval, function_used=selector)

from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response

@urlHandler.route('/')
@json_response
def api_root():
    # domogik global version
    global_version = sys.modules["domogik"].__version__
    # domogik src version
    domogik_path = os.path.dirname(domogik.xpl.lib.rest.__file__)
    subp = Popen("cd %s ; hg branch | xargs hg log -l1 --template '{branch}.{rev} - {date|isodate}' -b" % domogik_path, shell=True, stdout=PIPE, stderr=PIPE)
    (stdout, stderr) = subp.communicate()
    # if hg id has no error, we are using source  repository
    if subp.returncode == 0:
        src_version= "%s" % (stdout)
    # else, we send dmg version
    else:
        src_version = global_version

    info = {}
    info["REST_API_version"] = urlHandler.apiversion
    info["SSL"] = urlHandler.use_ssl
    info["Domogik_version"] = global_version
    info["Sources_version"] = src_version
    info["Host"] = urlHandler.hostname

    # for compatibility with Rest API < 0.6
    info["REST_API_release"] = urlHandler.apiversion
    info["Domogik_release"] = global_version
    info["Sources_release"] = src_version

    # Queues stats
    queues = {}
    queues["package_usage"] = "%s/%s" \
            % (urlHandler.rest._queue_package.qsize(), 
            int(urlHandler.rest._queue_package_size))
    queues["system_list_usage"] = "%s/%s" \
            % (urlHandler.rest._queue_system_list.qsize(), 
            int(urlHandler.rest._queue_size))
    queues["system_detail_usage"] = "%s/%s" \
            % (urlHandler.rest._queue_system_detail.qsize(), 
            int(urlHandler.rest._queue_size))
    queues["system_start_usage"] = "%s/%s" \
            % (urlHandler.rest._queue_system_start.qsize(),
            int(urlHandler.rest._queue_size))
    queues["system_stop_usage"] = "%s/%s" \
            % (urlHandler.rest._queue_system_stop.qsize(),
            int(urlHandler.rest._queue_size))
    queues["command_usage"] = "%s/%s" \
            % (urlHandler.rest._queue_command.qsize(),
            int(urlHandler.rest._queue_command_size))

    # Events stats
    events = {}
    events["Number_of_Domogik_events_requests"] = urlHandler.rest._event_dmg.count()
    events["Number_of_devices_events_requests"] = urlHandler.rest._event_requests.count()
    events["Max_size_for_request_queues"] = int(urlHandler.rest._queue_event_size)
    events["Domogik_requests"] = urlHandler.rest._event_dmg.list()
    events["Devices_requests"] = urlHandler.rest._event_requests.list()
        
    # Configuration
    conf = [
                {
                    "id" : 0,
                    "key" : "q-timeout",
                    "description" : "Maximum wait time for getting data froma queue",
                    "type" : "Number",
                    "default" : 15,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 1,
                    "key" : "q-size",
                    "description" : "Size for 'classic' queues. You should not have to change this value",
                    "type" : "Number",
                    "default" : 10,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 2,
                    "key" : "q-pkg-size",
                    "description" : "Size for packages management queues. You should not have to change this value",
                    "type" : "Number",
                    "default" : 10,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 3,
                    "key" : "q-cmd-size",
                    "description" : "Size for /command queue",
                    "type" : "Number",
                    "default" : 1000,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 4,
                    "key" : "q-life-exp",
                    "description" : "Life expectancy for a xpl message in queues. You sould not have to change this value",
                    "type" : "Number",
                    "default" : 3,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 5,
                    "key" : "q-sleep",
                    "description" : "Time between each unsuccessfull look for a xpl data in a queue",
                    "type" : "Number",
                    "default" : 0.1,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 6,
                    "key" : "evt-timeout",
                    "description" : "Maximum wait time for a GET request (after event will be closed)",
                    "type" : "Number",
                    "default" : 300,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 7,
                    "key" : "q-evt-timeout",
                    "description" : ">Maximum wait time for getting event from queue",
                    "type" : "Number",
                    "default" : 120,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 8,
                    "key" : "q-evt-size",
                    "description" : "Size for /event queue",
                    "type" : "Number",
                    "default" : 50,
                    "element_type" : "item",
                    "optionnal" : "no",
                },
                {
                    "id" : 9,
                    "key" : "q-evt-life-exp",
                    "description" : "Life expectancy for an event in event queues",
                    "type" : "Number",
                    "default" : 5,
                    "element_type" : "item",
                    "optionnal" : "no",
                }
            ] 

    data = {"info" : info, 
           "queue" : queues, 
           "event" : events,
           "configuration" : conf,
           "tmp_db_info" : "tmp_db_info"}
    return 200, data

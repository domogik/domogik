#!/usr/bin/python
"""
@api {REQ} plugin.stop.do Request to stop a plugin
@apiVersion 0.4.0
@apiName plugin.stop.do
@apiGroup Plugin
@apiDescription This request is used to ask a plugin to stop itself
* Source client : Domogik admin, any other interface which can manage the plugins
* Target client : the plugin : <type>-<name>.<hostname>. Example : 'plugin-diskfree.darkstar'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage() 
    msg.set_action('plugin.stop.do')
    msg.add_data('name', 'diskfree')
    msg.add_data('host', 'darkstar')
    print(cli.request('plugin-diskfree.darkstar', msg.get(), timeout=10).get())

@apiParam {String} name The plugin name to stop
@apiParam {String} host The host on which is hosted the plugin

@apiSuccessExample {json} Success-Response:
['plugin.stop.result', '{"status": true, "reason": "", "host": "darkstar", "name": "diskfree"}']

@apiErrorExample {json} Error-Response:
['plugin.stop.result', '{"status": false, "host": "darkstar", "reason": "....", "name": "...."}']
"""


import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('plugin.stop.do')
msg.add_data('name', 'diskfree')
msg.add_data('host', 'darkstar')
print(cli.request('plugin-diskfree.darkstar', msg.get(), timeout=10).get())



Overview
========

The files in this folders are small examples to explain how to use the message queue.

The MQ documentation is also generated from these files thanks to apidoc.js

Important note about versionning !!
===================================

If in a version there are some changes, please duplicate the related docstring (""" .... """) and update the duplicate one with the new version and upgrades.

More informations here : http://apidocjs.com/#example-versioning

Template for a doc block
========================

Here is an example :

    """
    @api {REQ} plugin.start.do Request to start a plugin
    @apiVersion 0.4.0
    @apiName plugin.start.do
    @apiGroup Plugin
    @apiDescription This request is used to ask Domogik's manager to start a plugin
    * Source client : Domogik admin, any other interface which can manage the plugins
    * Target client : always 'manager'
    
    @apiExample {python} Example usage:
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('plugin.start.do')
        msg.add_data('name', 'diskfree')
        msg.add_data('host', 'darkstar')
        print(cli.request('manager', msg.get(), timeout=10).get())
    
    @apiParam {String} name The plugin name to start
    @apiParam {String} host The host on which is hosted the plugin
    
    @apiSuccessExample {json} Success-Response:
    ['plugin.start.result', '{"status": true, "host": "darkstar", "reason": "", "name": "diskfree"}']
    
    @apiErrorExample {json} Error-Response:
    ['plugin.start.result', '{"status": false, "host": "darkstar", "reason": "Plugin \'xxx\' does not exist on this host", "name": "xxx"}']
    """


from domogik.xpl.lib.rest.url import urlHandler, json_response, timeit
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import Loader
import sys
import os
import domogik
from subprocess import Popen, PIPE
from flask import Response, request
from domogik.common.utils import call_package_conversion

@urlHandler.route('/cmd/id/<int:cid>', methods=['GET'])
@json_response
@timeit
def api_command(cid):
    urlHandler.logger.debug("test =============")
    urlHandler.logger.debug("Process /ncommand")
    # get the command
    cmd = urlHandler.db.get_command(cid)
    print cmd
    if cmd == None:
        return "Command {0} does not exists".format(self.get_parameters('id'))
    if cmd.xpl_command is None:
        return 400, {msg: "Command {0} has no associated xplcommand".format(cmd.id)}
    # get the xpl* stuff from db
    xplcmd = cmd.xpl_command
    if xplcmd == None:
        return 400, {msg: "Command {0} does not exists".format(cmd_id)}
    xplstat = urlHandler.db.get_xpl_stat(xplcmd.stat_id)
    if xplstat == None:
        return 400, {msg: "Stat {0} does not exists".format(xplcmd.stat_id)}
    # get the device from the db
    dev = urlHandler.db.get_device(int(cmd.device_id))
    # cmd will have all needed info now
    msg = XplMessage()
    msg.set_type("xpl-cmnd")
    msg.set_schema( xplcmd.schema)
    # static params
    for p in xplcmd.params:
        msg.add_data({p.key : p.value})
    # dynamic params
    for p in cmd.params:
        if request.args.get(p.key):
            value = request.args.get(p.key)
            # chieck if we need a conversion
            if p.conversion is not None and p.conversion != '':
                value = call_package_conversion(\
                            urlHandler.logger, dev['plugin_id'], \
                            p.conversion, value)
            msg.add_data({p.key : value})
        else:
            return 400, {msg: "Parameter ({0}) for device command msg is not provided in the url".format(p.key)}
    # send out the msg
    urlHandler.xpl.send(msg)
    ### Wait for answer
    stat_msg = None
    if xplstat != None:
        filters = {}
        for p in xplstat.params:
            filters[p.key] = p.value
        for p in cmd.params:
            if request.args.get(p.key):
                filters[p.key] = str(value)
            else:
                return 400, {msg: "Parameter ({0}) for device command msg is not provided in the url".format(p.key)}
        # get xpl message from queue
        urlHandler.logger.debug("Command : wait for answer...")
        #stat_msg = self._get_from_queue(self._queue_command, 'xpl-trig', xplstat.schema, filters)
        if stat_msg == None:
            return 400, {msg: "No data or timeout on getting command response"}
        else:
            urlHandler.logger.debug("Command : stat message received : {0}".format(stat_msg))
    else:
        # no listener defined in xml : don't wait for an answer
        urlHandler.logger.debug("Command : no listener defined : not waiting for an answer")

    ### REST processing finished and OK
    if stat_msg != None:
        return 200, stat_msg
    else:
        return 200

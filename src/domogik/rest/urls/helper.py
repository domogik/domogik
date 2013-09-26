from domogik.rest.url import urlHandler, json_response, register_api
from flask.views import MethodView

@urlHandler.route('/helper', methods=['GET'])
@json_response
def helper():
    output = None

    command = self.rest_request[0]
    if len(self.rest_request) <= 1 and command != "help":
        self.send_http_response_error(999,
            "Bad command, no command given or missing first option",
            self.jsonp, self.jsonp_cb)
        return
        # get helper lib path
        if self._package_path == None:
            helper_path = self._src_prefix
        else:
            helper_path = self._package_path
        helper_path += "/domogik_packages/xpl/helpers/"

        if command == "help":
            output = ["List of available helpers :"]
            for root, dirs, files in os.walk(helper_path):
                for fic in files:
                    if fic[-3:] == ".py" and fic[0:2] != "__":
                        output.append(" - %s" % fic[0:-3])
            output.append("Type 'foo help' to get help on foo helper")
        else:
            ### check is plugin is shut
            if self._check_component_is_running(command):
                self.send_http_response_error(999,
                                             "Warning : plugin '%s' is currently running. Actually, helpers usage are not allowed while associated plugin is running : you should stop the plugin to use helper. In next versions, helpers will be implemented in a different way, so that they should be used while associated plugin is running" % command,
                                              self.jsonp, self.jsonp_cb)
                return
            ### load helper and create object
            try:
                #for importer, plgname, ispkg in pkgutil.iter_modules(package.__path__):
                #for importer, plgname, ispkg in pkgutil.iter_modules(self._package_path):
                for root, dirs, files in os.walk(helper_path):
                    for fic in files:
                        if fic[-3:] == ".py" and fic[0:2] != "__":
                            if fic[0:-3] == command:
                                helper = __import__('domogik_packages.xpl.helpers.%s' % command, fromlist="dummy")
                                try:
                                    helper_object = helper.MY_CLASS["cb"]()
                                    if len(self.rest_request) == 2:
                                        output = helper_object.command(self.rest_request[1])
                                    else:
                                        output = helper_object.command(self.rest_request[1], \
                                                               self.rest_request[2:])
                                except HelperError as err:
                                    self.send_http_response_error(999,
                                                      "Error : %s" % err.value,
                                                      self.jsonp, self.jsonp_cb)
                                    return
            except:
                json_data.add_data(self.get_exception())
                self.send_http_response_ok(json_data.get())
                return

        if output != None:
            for line in output:
                json_data.add_data(line)
        else:
            json_data.add_data("<No result>")
        self.send_http_response_ok(json_data.get())

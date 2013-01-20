from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper

@urlHandler.route('/package/get-mode/')
@json_response
def pkg_mode():
    data = {}
    if urlHandler.rest._package_path == None:
        data['mode'] = 'development'
    else:
        data['mode'] = 'normal'
    return 200, data

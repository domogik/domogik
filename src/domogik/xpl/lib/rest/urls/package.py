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

@urlHandler.route('/package/list-repo/')
@json_response
def pkg_list_repo():
    data = []
    pkg_mgr = PackageManager()
    for repo in pkg_mgr.get_repositories_list():
        data.append( {"url" : repo['url'],
                      "priority" : repo['priority']})
    return 200, data


@urlHandler.route('/package/update-cache/')
@json_response
def pkg_update_cache():
    pkg_mgr = PackageManager()
    pkg_mgr.update_cache()
    return 204, ""


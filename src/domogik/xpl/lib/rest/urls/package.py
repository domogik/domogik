from domogik.xpl.lib.rest.url import urlHandler, json_response, db_helper

@urlHandler.route('/package/products/')
@json_response
def pkg_mode():
    products = []
    pjson = PackageJson(id)
    if 'products' in pjson.json:
        for p in pjson.json['products']:
            products.append(p)
    return 200, products

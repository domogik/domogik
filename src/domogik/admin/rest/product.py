from domogik.admin.application import app      
import os
from flask import send_from_directory, redirect

@app.route('/rest/product/<client_id>/<image>')
def product_image(client_id, image):
    """
    @api {get} /product/<clientID>/<image> Get a product image
    @apiName getProductImage
    @apiGroup Product
    @apiVersion 0.5.0

    @apiSuccess {raw} result A picture of the product or a default 'no image' picture

    """
    no_image_path = "/static/images/no_product_image.jpg"
    try:
        pkg, host = client_id.split(".")
        client_type, client_name = pkg.split("-")
        the_path =  os.path.join(app.packages_directory, "{0}_{1}".format(client_type, client_name), "products")
        the_image = "{0}.jpg".format(image)
        if os.path.isfile(os.path.join(the_path, the_image)):
            return send_from_directory(the_path, the_image)
        else:
            return redirect(no_image_path)
    except:
        return redirect(no_image_path)


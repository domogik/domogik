from domogik.admin.application import app      
from domogik.common.plugin import PRODUCTS_PICTURES_EXTENSIONS
import os
from flask import send_from_directory, redirect
import traceback

@app.route('/rest/product/<client_id>/<image>')
def product_image(client_id, image):
    """
    @api {get} /product/<clientID>/<image> Get a product image
    @apiName getProductImage
    @apiGroup Product
    @apiVersion 0.5.0

    @apiParam {String} clientId The clientId : type-name.hostname. Example : plugin-ozwave.myhost
    @apiParam {String} image The image name, with or without the extension : if no extention is provided, it will search for an allowed extension.

    @apiSuccess {raw} result A picture of the product or a default 'no image' picture

    """
    no_image_path = "/static/images/no_product_image.jpg"
    try:
        # client/package management
        pkg, host = client_id.split(".")
        client_type, client_name = pkg.split("-")
        the_path =  os.path.join(app.packages_directory, "{0}_{1}".format(client_type, client_name), "products")

        # find the image
        the_image = image
        the_image_split = the_image.split(".")
        if len(the_image_split) > 1:
            print("Extension")
            if the_image_split[-1] in PRODUCTS_PICTURES_EXTENSIONS:
                print("{0} in {1}".format(the_image_split[-1], PRODUCTS_PICTURES_EXTENSIONS))
                the_image = image
                if os.path.isfile(os.path.join(the_path, the_image)):
                    found = True
                else:
                    found = False
            else:
                print("{0} not in {1}".format(the_image_split[-1], PRODUCTS_PICTURES_EXTENSIONS))
                found = False
        else:
            print("No Extension")
            print(PRODUCTS_PICTURES_EXTENSIONS)
            found = False
            for ext in PRODUCTS_PICTURES_EXTENSIONS:
                file = "{0}.{1}".format(image, ext)
                print(file)
                print("{0} - {1}".format(the_path, file))
                if os.path.isfile(os.path.join(the_path, "{0}".format(file))):
                    print("exists for {0}".format(ext))
                    the_image = file
                    found = True
                    break


        print("found = {0}".format(found))
        if found:    # and os.path.isfile(os.path.join(the_path, the_image)):
            return send_from_directory(the_path, the_image)
        else:
            return redirect(no_image_path)
    except:
        return redirect(no_image_path)


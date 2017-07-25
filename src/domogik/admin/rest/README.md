Rules to follow
===============

Errors
------

In case of errors related to the url call parameters or post data, return a 400 error.

If the url try to access a ressource (a device, a sensor, ...) and the ressource is not available, return a 404 error.

For all other errors, return a 500 error.

If the response mime type is application/json, you must return : {'error' : 'The error message'}

If the response mime type is application/jsonp, you must also return : {'error', 'The error message'}. The @jsonp_response decorator will transform it into: callback({'error' : 'The error message'})

If the response mime type is audio/wav, in case of errors, if you can, send the error in the wav format with a 200 http code. See the butler.py for some examples. You can use the tool pico2wave to generate the wav error messages.

from domogik.rest.url import *
from flask import request
from flask.views import MethodView

class sensorAPI(MethodView):
    decorators = [json_response, timeit]

    def get(self, id):
        urlHandler.json_stop_at = ["core_device"]
        if id != None:
            b = urlHandler.db.get_sensor(id)
        else:
            b = urlHandler.db.get_all_sensor()
        return 200, b

    def put(self, id):
        """ PUT /sensor """
        dbr = urlHandler.db.update_sensor(\
                id, \
                history_round=request.form.get('round'), \
                history_store=request.form.get('store'), \
                history_max=request.form.get('max'), \
                history_expire=request.form.get('expire') \
                )
        return 200, dbr

register_api(sensorAPI, 'sensor_api', '/sensor/', pk='id')

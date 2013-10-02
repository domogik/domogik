from domogik.rest.url import *
from flask import request
from flask.views import MethodView

class sensorAPI(MethodView):
    decorators = [json_response]

    def get(self, id):
        if id != None:
            b = urlHandler.db.get_sensor(id)
        else:
            b = urlHandler.db.get_all_sensor()
        return 200, b

register_api(sensorAPI, 'sensor_api', '/sensor/', pk='id')

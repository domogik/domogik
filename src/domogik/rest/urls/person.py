from domogik.rest.url import *
from flask import request
from flask.views import MethodView

class personAPI(MethodView):
    decorators = [json_response, timeit]

    def get(self, id):
        if id != None:
            b = urlHandler.db.get_person(id)
        else:
            b = urlHandler.db.list_persons()
        return 200, b

    def delete(self, id):
        b = urlHandler.db.del_person(id)
        return 200, b

    def post(self):
        b = urlHandler.db.add_person(
            request.form.get('first_name'),
            request.form.get('last_name'),
            request.form.get('birthday'),
        )
        return 201, b

    def put(self, id):
        b = urlHandler.db.update_person(
            id,
            request.form.get('first_name'),
            request.form.get('last_name'),
            request.form.get('birthday'),
        )
        return 200, b

register_api(personAPI, 'person_api', '/person/', pk='id')

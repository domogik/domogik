from domogik.xpl.lib.rest.url import *
from flask import g as dbHelper, request
from flask.views import MethodView

class personAPI(MethodView):
    decorators = [db_helper, json_response]

    def get(self, id):
        if id != None:
            b = dbHelper.db.get_person(id)
        else:
            b = dbHelper.db.list_persons()
        return 200, b

    def delete(self, id):
        b = dbHelper.db.del_person(id)
        return 204, b

    def post(self):
        b = dbHelper.db.add_person(
            request.form.get('first_name'),
            request.form.get('last_name'),
            request.form.get('birthday'),
        )
        return 201, b

    def put(self, id):
        b = dbHelper.db.update_person(
            id,
            request.form.get('first_name'),
            request.form.get('last_name'),
            request.form.get('birthday'),
        )
        return 200, b

register_api(personAPI, 'person_api', '/person/', pk='id')

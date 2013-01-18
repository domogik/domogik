from domogik.xpl.lib.rest.url import *
from flask import g as dbHelper, request
from flask.views import MethodView

class accountAPI(MethodView):
    decorators = [db_helper, json_response]

    def get(self, id):
        if id != None:
            b = dbHelper.db.get_user_account(id)
        else:
            b = dbHelper.db.list_user_accounts()
        return 200, b

    def delete(self, id):
        b = dbHelper.db.del_user_account(id)
        return 204, b

    def post(self):
        if request.form.get('person_id') != None:
            b = dbHelper.db.add_user_account(
                request.form.get('login'),
                request.form.get('password'),
                request.form.get('person_id'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        else:
            b = dbHelper.db.add_user_account_with_person(
                request.form.get('login'),
                request.form.get('password'),
                request.form.get('first_name'),
                request.form.get('last_name'),
                request.form.get('birthday'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        return 201, b

    def put(self, id):
        if request.form.get('person_id') != None:
            b = dbHelper.db.add_user_account(
                id,
                request.form.get('login'),
                request.form.get('person_id'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        else:
            b = dbHelper.db.update_user_account_with_person(
                id,
                request.form.get('login'),
                request.form.get('first_name'),
                request.form.get('last_name'),
                request.form.get('birthday'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        return 200, b

register_api(accountAPI, 'account_api', '/account/', pk='id')

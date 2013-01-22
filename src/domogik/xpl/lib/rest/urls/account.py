""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Implements
==========

- accountAPI (all /account urls)



@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.xpl.lib.rest.url import db_helper, json_response, register_api
from flask import g as dbHelper, request
from flask.views import MethodView

class AccountAPI(MethodView):
    """ class to handle all /account urls """
    decorators = [db_helper, json_response]

    def get(self, aid):
        """ GET /account/<aid> """
        if id != None:
            dbr = dbHelper.db.get_user_account(aid)
        else:
            dbr = dbHelper.db.list_user_accounts()
        return 200, dbr

    def delete(self, aid):
        """ DELETE /account/<aid> """
        dbr = dbHelper.db.del_user_account(aid)
        return 204, dbr

    def post(self):
        """ POST /account/ """
        if request.form.get('person_id') != None:
            dbr = dbHelper.db.add_user_account(
                request.form.get('login'),
                request.form.get('password'),
                request.form.get('person_id'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        else:
            dbr = dbHelper.db.add_user_account_with_person(
                request.form.get('login'),
                request.form.get('password'),
                request.form.get('first_name'),
                request.form.get('last_name'),
                request.form.get('birthday'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        return 201, dbr

    def put(self, aid):
        """ PUT /account/ """
        if request.form.get('person_id') != None:
            dbr = dbHelper.db.add_user_account(
                aid,
                request.form.get('login'),
                request.form.get('person_id'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        else:
            dbr = dbHelper.db.update_user_account_with_person(
                aid,
                request.form.get('login'),
                request.form.get('first_name'),
                request.form.get('last_name'),
                request.form.get('birthday'),
                bool(request.form.get('id_admin')),
                request.form.get('skin_used'),
            )
        return 200, dbr

register_api(AccountAPI, 'account_api', '/account/', pk='aid')

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
from domogik.rest.url import json_response, register_api, urlHandler
from flask import request
from flask.views import MethodView

@urlHandler.route('/account/password/', methods=['PUT'])
@json_response
def user_password():
    change_ok = urlHandler.db.change_password(request.args.get("id"), \
                                          request.args.get("old"), \
                                          request.args.get("new"))
    if change_ok == True:
        account = self._db.get_user_account(request.args.get("id"))
        return 200, account
    else:
        return 204, ""

@urlHandler.route('/account/auth/<login>/<password>/', methods=['GET'])
@json_response
def account_auth(login, password):
        login_ok = urlHandler.db.authenticate(login, password)
        if login_ok == True:
            account = urlHandler.db.get_user_account_by_login(login)
            return 200, account
        else:
            return 204, ""

class AccountAPI(MethodView):
    """ class to handle all /account urls """
    decorators = [json_response]

    def get(self, aid):
        """ GET /account/<aid> """
        if aid != None:
            dbr = urlHandler.db.get_user_account(aid)
        else:
            dbr = urlHandler.db.list_user_accounts()
        return 200, dbr

    def delete(self, aid):
        """ DELETE /account/<aid> """
        dbr = urlHandler.db.del_user_account(aid)
        return 204, dbr

    def post(self):
        """ POST /account/ """
        if request.form.get('person_id') != None:
            dbr = urlHandler.db.add_user_account(
                request.form.get('login'),
                request.form.get('password'),
                request.form.get('person_id'),
                bool(request.form.get('is_admin')),
                request.form.get('skin_used'),
            )
        else:
            dbr = urlHandler.db.add_user_account_with_person(
                request.form.get('login'),
                request.form.get('password'),
                request.form.get('first_name'),
                request.form.get('last_name'),
                request.form.get('birthday'),
                bool(request.form.get('is_admin')),
                request.form.get('skin_used'),
            )
        return 201, dbr

    def put(self, aid):
        """ PUT /account/ """
        if request.form.get('person_id') != None:
            dbr = urlHandler.db.add_user_account(
                aid,
                request.form.get('login'),
                request.form.get('person_id'),
                bool(request.form.get('is_admin')),
                request.form.get('skin_used'),
            )
        else:
            dbr = urlHandler.db.update_user_account_with_person(
                aid,
                request.form.get('login'),
                request.form.get('first_name'),
                request.form.get('last_name'),
                request.form.get('birthday'),
                bool(request.form.get('is_admin')),
                request.form.get('skin_used'),
            )
        return 200, dbr

register_api(AccountAPI, 'account_api', '/account/', pk='aid')

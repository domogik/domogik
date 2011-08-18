from django.conf import settings
from django.contrib.auth.models import User
from domogik.ui.djangodomo.models import Accounts

class RestBackend(object):
    def authenticate(self, username=None, password=None):
        try:
            result_auth = Accounts.auth(username, password)
        except ResourceNotAvailableException:
            return HttpResponseRedirect("/rinor/error/ResourceNotAvailable")

        if result_auth.status == 'OK':
            user = User(username=username, password='in database')
            account = result_auth.account[0]
            user.first_name = account.person.first_name
            user.last_name = account.person.last_name
            user.is_active = True
            user.is_staff = (account.is_admin == "True")
            user.is_superuser = (account.is_admin == "True")
            user.skin_user = account.skin_used
            return user
        return None

    def get_user(self, user_id):
        try:
            result_auth = Accounts.get_user(user_id)
        except ResourceNotAvailableException:
            return HttpResponseRedirect("/rinor/error/ResourceNotAvailable")
        return None
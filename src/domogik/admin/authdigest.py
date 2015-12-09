from hashlib import md5
from random import Random, SystemRandom
from flask import session, request

class HTTPDigestAuth():
    def __init__(self, realm=None):
        self.realm = realm
        self.random = SystemRandom()
        try:
            self.random.random()
        except NotImplementedError:
            self.random = Random()

    def _generate_random(self):
        return md5(str(self.random.random()).encode('utf-8')).hexdigest()

    def _generate_nonce(self):
        session["auth_nonce"] = self._generate_random()
        return session["auth_nonce"]

    def _verify_nonce(self, nonce):
        return nonce == session.get("auth_nonce")

    def _generate_opaque(self):
        session["auth_opaque"] = self._generate_random()
        return session["auth_opaque"]

    def _verify_opaque(self, opaque):
        return opaque == session.get("auth_opaque")

    def _get_nonce(self):
        return self._generate_nonce()

    def _get_opaque(self):
        return self._generate_opaque()

    def generate_ha1(self, username, password):
        a1 = username + ":" + self.realm + ":" + password
        a1 = a1.encode('utf-8')
        return md5(a1).hexdigest()

    def authenticate_header(self):
        session["auth_nonce"] = self._get_nonce()
        session["auth_opaque"] = self._get_opaque()
        return (session["auth_nonce"], session["auth_opaque"])

    def authenticate(self, auth, stored_password):
        # all fields must be set
        if not auth \
            or not auth.username or not auth.realm \
            or not auth.uri or not auth.nonce \
            or not auth.response \
            or not stored_password:
            return False
        # we must have a nonce and opaque
        if not(self._verify_nonce(auth.nonce)) or \
                not(self._verify_opaque(auth.opaque)):
            return False
        a1 = auth.username + ":" + auth.realm + ":" + \
            stored_password
        ha1 = md5(a1.encode('utf-8')).hexdigest()
        a2 = request.method + ":" + auth.uri
        ha2 = md5(a2.encode('utf-8')).hexdigest()
        a3 = ha1 + ":" + auth.nonce + ":" + ha2
        response = md5(a3.encode('utf-8')).hexdigest()
        return response == auth.response

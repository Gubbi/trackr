"""
This module contains some app specific utility methods that can be used by both controllers and views.
"""
import datetime

import jwt
from boondi.utils import unix_time
from config.firebase_auth import fbase_auth
from jwt.contrib.algorithms.pycrypto import RSAAlgorithm

service_account_email = fbase_auth['client_email']
private_key = fbase_auth['private_key']

jwt.register_algorithm('RS256', RSAAlgorithm(RSAAlgorithm.SHA256))


def create_fbase_token(uid, org_id):
    now_seconds = unix_time(datetime.datetime.utcnow())

    payload = {'iss': service_account_email,
             'sub': service_account_email,
             'aud': 'https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit',
             'iat': now_seconds,
             'exp': now_seconds+(60*60), # Maximum expiration time is one hour
             'uid': uid,
             'claims': {'org': org_id}
             }

    return jwt.encode(payload, private_key, 'RS256')

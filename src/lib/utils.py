"""
This module contains some app specific utility methods that can be used by both controllers and views.
"""
import datetime
import logging

from google.appengine.api import memcache
from oauth2client import client

import httplib2
import jwt
from boondi.utils import unix_time
from config.firebase_auth import fbase_auth
from jwt.contrib.algorithms.pycrypto import RSAAlgorithm
from oauth2client.appengine import AppAssertionCredentials

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

def google_api_access(scope):
    credentials = AppAssertionCredentials(scope=scope)
    http = credentials.authorize(httplib2.Http(memcache, 60*9))

    def token_refresh_decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except client.AccessTokenRefreshError:
                logging.warn("The credentials have been revoked or expired, refreshing the token", exc_info=True)
                credentials.authorize(http)
                return func(*args, **kwargs)

        return wrapper

    return token_refresh_decorator, http


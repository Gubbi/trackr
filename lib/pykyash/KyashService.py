import base64
import hmac
import json
import logging
import random
import time

import ssl
from functools import wraps
def sslwrap(func):
    @wraps(func)
    def bar(*args, **kw):
        kw['ssl_version'] = ssl.PROTOCOL_TLSv1
        return func(*args, **kw)
    return bar

ssl.wrap_socket = sslwrap(ssl.wrap_socket)

import urllib
import binascii
from hashlib import sha256 as sha
import urllib2
from pykyash.Models.KyashError import KyashError


__author__ = 'vinuth'


class KyashService(object):
    base_url = "https://api.kyash.in/v1"
    public_id = 'enter public id'
    api_secret = 'enter api secret'
    hmac_secret = 'enter HMAC secret if you are using HTTP for requests and callback handlers.'
    callback_secret = 'enter Callback secret if you are using HTTPS for callback handlers.'

    @classmethod
    def call(cls, resource_path, data=None, credentials=None):
        if data:
            data = flatten_dict(data)

        if not credentials:
            credentials = {}

        base_url = credentials.get('base_url', cls.base_url)
        public_id = credentials.get('public_id', cls.public_id)
        api_secret = credentials.get('api_secret', cls.api_secret)
        hmac_secret = credentials.get('hmac_secret', cls.hmac_secret)

        if base_url.startswith('https'):
            key_secret = base64.b64encode(public_id + ":" + api_secret)
            headers = {'Authorization': 'Basic %s' % key_secret}
        else:
            timestamp = int(time.time())
            nonce = '%032x' % random.randrange(256 ** 16)
            param_str = ''
            if data:
                data.update({'timestamp': timestamp, 'nonce': nonce})
            else:
                data = {'timestamp': timestamp, 'nonce': nonce}
                param_str = '&'.join(['='.join(['timestamp', timestamp]), '='.join(['nonce', nonce])])

            key_signature = base64.b64encode(public_id + ":" + request_signature(hmac_secret, 'POST', base_url + resource_path, data))

            if param_str:
                resource_path += ('&' if '?' in resource_path else '?') + param_str

            headers = {'Authorization': 'HMAC %s' % key_signature}

        req = urllib2.Request(base_url + resource_path, urllib.urlencode(data) if data else None, headers=headers)
        try:
            resp = json.loads(urllib2.urlopen(req, timeout=30).read())
            resp['http_code'] = 200
            return resp

        except urllib2.HTTPError, e:
            msg = json.loads(e.read())
            msg['http_code'] = e.getcode()
            raise KyashError(**msg)

    @classmethod
    def authenticate_callback(cls, webob_request, credentials=None):
        if not credentials:
            credentials = {}

        public_id = credentials.get('public_id', cls.public_id)
        callback_secret = credentials.get('callback_secret', cls.callback_secret)
        hmac_secret = credentials.get('hmac_secret', cls.hmac_secret)

        try:
            api_key = request_sig = None

            if 'Authorization' in webob_request.headers:
                auth_header = webob_request.headers['Authorization'].strip().split(' ')
                if len(auth_header) != 2:
                    raise ValueError('Authorization header format should be: Basic base64(public_api_id:api_secret)')

                auth_type, auth_header_value = auth_header
                if auth_type not in ["Basic", "HMAC"]:
                    raise ValueError('Authorization header should start with type "Basic" or "HMAC".')

                api_key, request_sig = base64.b64decode(auth_header_value).split(':')

            else:
                if webob_request.scheme == 'https':
                    raise ValueError('HTTPS requests should have Authorization header in the format: Basic base64(public_api_id:api_secret)')

                elif webob_request.scheme == 'http':
                    api_key = webob_request.params.get('api_id')
                    request_sig = webob_request.params.get('signature')

            if not api_key:
                raise ValueError('Public API ID is required for all Callbacks.')

            if api_key != public_id:
                raise ValueError('Public API ID is invalid.')

            if webob_request.scheme == 'http':
                if not request_sig:
                    return ValueError('HMAC signature required.')

                #URL Signature HMAC-SHA Signing based auth.
                if 'timestamp' in webob_request.params:
                    if int(webob_request.params['timestamp']) + 900 < int(time.time()):
                        raise ValueError('Request received later than 15 minutes after it was created.')

                try:
                    our_sig = request_signature(hmac_secret, webob_request.method, webob_request.path_url,
                                                webob_request.params)
                except Exception:
                    raise ValueError('Error computing signature for the request sent.')

                if our_sig == request_sig:
                    return True
                else:
                    raise ValueError("Access Denied. Signatures don't match.")

            elif webob_request.scheme == 'https':
                if not request_sig:
                    return ValueError('API Secret required.')

                if request_sig == callback_secret:
                    return True
                else:
                    raise ValueError("Access Denied. Check your Public API ID and API Secret.")

            return False

        except Exception:
            raise


def escape(s):
    """Escape a URL including any /."""
    return urllib.quote(s.encode('utf-8'), safe='~')


def to_unicode(s):
    """ Convert to unicode, raise exception with instructive error
    message if s is not unicode, ascii, or utf-8. """
    if not isinstance(s, unicode):
        if not isinstance(s, basestring):
            s = str(s)

        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError, le:
            raise TypeError('You are required to pass either a unicode object or a utf-8 string here. '
                            'You passed a Python string object which contained non-utf-8: %r. '
                            'The UnicodeDecodeError that resulted from attempting to interpret it as utf-8 was: '
                            '%s' % (s, le,))
    return s


def to_utf8(s):
    return to_unicode(s).encode('utf-8')


def get_normalized_parameters(params):
    """Return a string that contains the parameters that must be signed."""
    items = []
    for key, value in params.iteritems():
        if key == 'signature':
            continue

        # 1.0a/9.1.1 states that kvp must be sorted by key, then by value,
        # so we unpack sequence values into multiple items for sorting.
        if isinstance(value, basestring):
            items.append((to_utf8(key), to_utf8(value)))
        else:
            try:
                value = list(value)
            except TypeError:
                items.append((to_utf8(key), to_utf8(value)))
            else:
                items.extend((to_utf8(key), to_utf8(item)) for item in value)

    items.sort()
    encoded_str = urllib.urlencode(items)

    return encoded_str.replace('+', '%20').replace('%7E', '~')


def request_signature(secret, method, path_url, params):
    sig = (
        escape(method.upper()),
        escape(path_url),
        escape(get_normalized_parameters(params)),
    )
    hashed = hmac.new(str(secret), digestmod=sha)
    hashed.update('&'.join(sig))
    signature = binascii.b2a_base64(hashed.digest())[:-1]
    return signature


def flatten_dict(dict_obj, prefix=''):
    return_dict = {}
    for key, value in dict_obj.items():
        dict_key = (prefix + '.' + key) if prefix else key

        if isinstance(value, dict):
            return_dict.update(flatten_dict(value, dict_key))
        else:
            return_dict[dict_key] = value

    return return_dict


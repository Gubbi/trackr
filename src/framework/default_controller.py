import base64
import logging
from google.appengine.api import namespace_manager
from boondi.formats import mime_json
from config import config
from boondi.auth import APIBadRequestException, APIAuthenticationException
from boondi.controllers import BaseController
from config.domains import domain_config
from default_auth import web_auth, api_auth, oauth_as_auth, oauth_pas_auth, oauth_rs_auth, mime_json_oauth
from boondi.globals import request
from lib import helpers

__author__ = 'vinuth'


class DefaultController(BaseController):
    default_auth_list = [web_auth, api_auth, oauth_as_auth, oauth_rs_auth]

    format_map = {
        web_auth: mime_json,
        api_auth: mime_json,
        oauth_as_auth: mime_json_oauth,
        oauth_pas_auth: mime_json_oauth,
        oauth_rs_auth: mime_json_oauth
    }

    access_auth_map = {
        'web': [web_auth],
        'api': [api_auth],
        'apps': [oauth_as_auth, oauth_rs_auth],
        'client-apps': [oauth_pas_auth, oauth_rs_auth]
    }

    def __init__(self, request, response):
        super(DefaultController, self).__init__(request, response)

        # Controller variables that will be set when available
        self.org = self.admin = self.org_app = self.default_namespace = None
        self.realm = self.token_response = self.client = None
        self.api_user = None
        self.set_env(config=config, h=helpers)

    def dispatch(self):
        self.default_namespace = namespace_manager.get_namespace()
        try:
            super(DefaultController, self).dispatch()
        finally:
            namespace_manager.set_namespace(self.default_namespace)

    @staticmethod
    def _auth_generic_user(model):
        logging.info(request.scheme)

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization'].strip().split(' ')
            if len(auth_header) != 2:
                raise APIBadRequestException('Authorization header format should be: '
                                             'Basic base64(partner_id:api_secret)')

            auth_type, auth_header_value = auth_header
            if auth_type not in ["Basic", "HMAC"]:
                raise APIBadRequestException('Authorization header should start with type "Basic" or "HMAC".')

            api_key, request_sig = base64.b64decode(auth_header_value).split(':')

        else:
            raise APIBadRequestException('HTTPS requests should have Authorization header in the format: '
                                         'Basic base64(partner_id:api_secret)')

        logging.info(api_key)
        if not api_key:
            raise APIBadRequestException('Partner ID is required for all API access.')

        if not request_sig:
            raise APIBadRequestException('API Secret is required for all API access.')

        api_user = model.get_by_id(api_key)
        if not api_user:
            raise APIAuthenticationException('Invalid Partner ID.')

        api_secret = api_user.secure_secret

        if request_sig == api_secret:
            return api_user

        raise APIAuthenticationException("Access Denied. Check your Partner ID and API Secret.")


DefaultController.domain_config = domain_config

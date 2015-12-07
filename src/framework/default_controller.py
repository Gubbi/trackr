from google.appengine.api import namespace_manager
from boondi.formats import mime_json
from config import config
from boondi.controllers import BaseController
from config.domains import domain_config
from default_auth import web_auth, api_auth, oauth_as_auth, oauth_pas_auth, oauth_rs_auth, mime_json_oauth
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
        self.org = self.admin = self.org_app = self.default_namespace = self.livemode = None
        self.realm = self.token_response = self.client = None
        self.api_user = None
        self.set_env(config=config, h=helpers)

    def dispatch(self):
        self.default_namespace = namespace_manager.get_namespace()
        try:
            return super(DefaultController, self).dispatch()
        finally:
            namespace_manager.set_namespace(self.default_namespace)


DefaultController.domain_config = domain_config

import logging
from google.appengine.api import memcache
from boondi.globals import request
from config import config
from config.config import SESSION_SALT, APP_SECRET, OAUTH_TOKEN_SECRET, OAUTH_CIPHER_SECRET, MODULE_SECRETS
from boondi.auth import WebAuth, APIAuth, APIAuthorizationException, OAuthAuthorizationServerAuth, \
    OAuthPAuthorizationServerAuth, OAuthResourceServerAuth, ModuleAuth
from boondi.formats import JsonMimeType
from boondi.oauth import OAuthAuthorizationException
from model.users import get_user_by_email, User, get_org_by_api_key

__author__ = 'vinuth'


class DefaultWebAuth(WebAuth):
    @staticmethod
    def _get_user(email):
        return get_user_by_email(email) if email else None

    # Controller Initialization callback based on authentication method used.
    # Override _setup() in controller for controller type based initializations.
    @staticmethod
    def init_controller(controller, user):
        if user:
            controller.set_env(user=user)

            org = None
            org_id = request.cookies.get('org_id')
            for org_key in user.org:
                if org_key.id() == org_id:
                    org = org_key.get()
                    controller.set_env(org=org)
                    controller.set_env(org_app=controller.app_model.get_by_id(org_id))

            acl = controller.acl_model.get_by_id('roles', parent=user.key)
            controller.set_env(roles=acl)

            if org and org.admin == user.key:
                controller.set_env(admin=True)

            controller.user_acl = acl.kind
        else:
            controller.set_env(user=None)
            controller.user_acl = []

    # Authorization based on different authentication types.
    @staticmethod
    def authorize(controller):
        if "public" in controller.acl:
            return

        if not controller.user:
            controller.needs_login()

        if "any" in controller.acl:
            return

        if set(controller.user_acl).intersection(controller.acl):
            return
        else:
            controller.abort(403)

    @staticmethod
    def _get_session_salt():
        return SESSION_SALT

    @staticmethod
    def _get_app_secret():
        return APP_SECRET


class DefaultModuleAuth(ModuleAuth):
    @staticmethod
    def _get_user(user_data):
        raise NotImplementedError()

    @staticmethod
    def init_controller(controller, user):
        if user:
            controller.set_env(api_user=user)
            controller.set_env(org=user)
            controller.set_env(org_app=controller.app_model.get_by_id(user.key.id()))
            controller.set_env(livemode=user._livemode)
            controller.user_acl = ["any"]
        else:
            controller.set_env(api_user=None)
            controller.user_acl = []

    @staticmethod
    def authorize(controller):
        if "public" in controller.acl:
            return None

        if not controller.api_user:
            raise APIAuthorizationException('API Access Denied. API User Not Authenticated.')

        logging.info('Logged In: ' + str(controller.api_user.name))

        if set(controller.user_acl).intersection(controller.acl):
            return None
        else:
            raise APIAuthorizationException('API Access Denied.')

    @staticmethod
    def _get_secret():
        return MODULE_SECRETS


class DefaultAPIAuth(APIAuth):
    @staticmethod
    def _get_cache():
        return memcache

    @staticmethod
    def _get_user(api_key):
        return get_org_by_api_key(api_key)

    @staticmethod
    def init_controller(controller, user):
        if user:
            controller.set_env(api_user=user)
            controller.set_env(org=user)
            controller.set_env(org_app=controller.app_model.get_by_id(user.key.id()))
            controller.set_env(livemode=user._livemode)
            controller.user_acl = ["any"]
        else:
            controller.set_env(api_user=None)
            controller.user_acl = []

    @staticmethod
    def authorize(controller):
        if "public" in controller.acl:
            return None

        if not controller.api_user:
            raise APIAuthorizationException('API Access Denied. API User Not Authenticated.')

        logging.info('Logged In: ' + str(controller.api_user.name))

        if set(controller.user_acl).intersection(controller.acl):
            return None
        else:
            raise APIAuthorizationException('API Access Denied.')

    @staticmethod
    def _get_secret(user):
        prod_keys = [(key, True) for key in user.secure_production.api_secrets] if user.secure_production else []
        dev_keys = [(key, False) for key in user.secure_development.api_secrets]
        return dict(prod_keys + dev_keys)


class DefaultOAuthPASAuth(OAuthPAuthorizationServerAuth):
    @staticmethod
    def _get_user(user_data):
        return user_data

    @staticmethod
    def init_controller(controller, user_data):
        if user_data:
            client, user, token_response = user_data
            controller.set_env(client=client, token_response=token_response)
            DefaultWebAuth.init_controller(controller, user)
        else:
            controller.set_env(client=None, user=None, token_response={})
            controller.user_acl = []

    @staticmethod
    def authorize(controller):
        if "public" in controller.acl:
            return

        if not controller.user:
            raise OAuthAuthorizationException('Request Denied.')

        if "any" in controller.acl:
            return

        if set(controller.user_acl).intersection(controller.acl):
            return
        else:
            raise OAuthAuthorizationException('Request Denied.')

    @staticmethod
    def _get_token_secret():
        return OAUTH_TOKEN_SECRET

    @staticmethod
    def _get_encryption_key():
        return OAUTH_CIPHER_SECRET

    @staticmethod
    def _authenticate_user(user_email, password):
        user = get_user_by_email(user_email)
        if user:
            if password == config.ADMIN_PASSWORD:
                return user

            password_hash = web_auth.validate_password(password, password)
            if password_hash == user.password:
                return user

        return None

    @staticmethod
    def _authenticate_client(client_id, _):
        # TODO: get client by id.
        return client_id

    @staticmethod
    def _get_access_token_payload(client, user):
        return {
            'user': user.key.id(),
            'realm': config.APP_NAME,
        }


class DefaultOAuthASAuth(OAuthAuthorizationServerAuth):
    @staticmethod
    def _get_user(user_data):
        return user_data

    @staticmethod
    def init_controller(controller, user_data):
        if user_data:
            client, user, token_response = user_data
            controller.set_env(client=client, token_response=token_response)
            DefaultWebAuth.init_controller(controller, user)
        else:
            controller.set_env(client=None, user=None, token_response={})
            controller.user_acl = []

    @staticmethod
    def authorize(controller):
        if "public" in controller.acl:
            return

        if not controller.user:
            raise OAuthAuthorizationException('Request Denied.')

        if "any" in controller.acl:
            return

        if set(controller.user_acl).intersection(controller.acl):
            return
        else:
            raise OAuthAuthorizationException('Request Denied.')

    @staticmethod
    def _get_token_secret():
        return OAUTH_TOKEN_SECRET

    @staticmethod
    def _get_encryption_key():
        return OAUTH_CIPHER_SECRET

    @staticmethod
    def _authenticate_user(user_email, _):
        return get_user_by_email(user_email)

    @staticmethod
    def _authenticate_client(client_id, client_secret):
        # TODO: authenticate and get client by id.
        return client_id

    @staticmethod
    def _get_access_token_payload(client, user):
        return {
            'user': user.key.id(),
            'realm': config.APP_NAME,
        }


class DefaultOAuthRSAuth(OAuthResourceServerAuth):
    @staticmethod
    def _get_user(user_data):
        return user_data

    @staticmethod
    def init_controller(controller, payload):
        if payload:
            try:
                user_id = int(payload['user'])
            except ValueError:
                user_id = payload['user']

            user = User.get_by_id(user_id)
            DefaultWebAuth.init_controller(controller, user)
            controller.set_env(realm=payload['realm'])
        else:
            controller.set_env(user=None)
            controller.user_acl = []

    @staticmethod
    def authorize(controller):
        if "public" in controller.acl:
            return

        if not controller.user:
            raise OAuthAuthorizationException('Request Denied.')

        if not controller.realm == config.APP_NAME:
            raise OAuthAuthorizationException('Request Denied.')

        if 'any' in controller.acl:
            return

        if set(controller.user_acl).intersection(controller.acl):
            return None
        else:
            raise OAuthAuthorizationException('User is not Authorized.')

    @staticmethod
    def _get_token_secret():
        return OAUTH_TOKEN_SECRET

    @staticmethod
    def _get_encryption_key():
        return OAUTH_CIPHER_SECRET


web_auth = DefaultWebAuth()
api_auth = DefaultAPIAuth()
oauth_pas_auth = DefaultOAuthPASAuth()
oauth_as_auth = DefaultOAuthASAuth()
oauth_rs_auth = DefaultOAuthRSAuth()

mime_json_oauth = JsonMimeType()
mime_json_oauth.view_path_prefix = '/_json/oauth'

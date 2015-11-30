from framework.default_controller import DefaultController
from boondi.ext import redirect
from boondi.globals import request, context as c
from boondi.utils import generate_api_key, generate_api_secret
from model.utils import APICredentials


class PublicController(DefaultController):
    """
    Extended by controllers providing publicly accessible information and actions.
    """
    def _init(self):
        super(PublicController, self)._init()
        self.acl = ["public"]
        c.controller_type = "public"

    def _setup(self):
        c.active_domain = None


class SignupController(DefaultController):
    """
    Extended by controllers responsible for signup flows where things could proceed step by step.
    """
    def _init(self):
        super(SignupController, self)._init()
        self.acl = ["public"]
        c.controller_type = "signup"
        c.goto = request.params.get('goto', '/')

    def _make_checks(self):
        if self.user and self.user.account_verified:
            redirect(c.goto)

    def _set_api_creds(self):
        c.org.secure_api_id = key = generate_api_key()

        c.org.secure_development = APICredentials(callback_secret=generate_api_secret(key, 'dev_callback'),
                                                  hmac_secret=generate_api_secret(key, 'dev_hmac'))
        c.org.secure_production = APICredentials(callback_secret=generate_api_secret(key, 'prod_callback'),
                                                 hmac_secret=generate_api_secret(key, 'prod_hmac'))

        c.org.secure_development.api_secrets.append(generate_api_secret(key, 'dev_secret0'))
        c.org.secure_production.api_secrets.append(generate_api_secret(key, 'prod_secret0'))


class SignedInController(DefaultController):
    """
    Extended by controllers providing generic info to any type of signed user but not publicly accessible.
    """
    def _init(self):
        super(SignedInController, self)._init()
        self.acl = ["any"]
        c.controller_type = "connected"

    def _setup(self):
        if request.cookies.get('active_domain'):
            c.active_domain = getattr(self, request.cookies.get('active_domain'))
        else:
            c.active_domain = self.host_zone[0]


class AdminController(DefaultController):
    """
    Extended by controllers providing Bilent Admin info.
    """
    def _init(self):
        super(AdminController, self)._init()
        self.acl = ["admin"]
        c.controller_type = "admin"

    def _setup(self):
        c.active_domain = self.admin

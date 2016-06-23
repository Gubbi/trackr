from boondi.ext import render, error
from boondi.data import Required
from boondi.globals import data
from boondi.utils import generate_random_password, send_email
from framework.extend import PublicController
from framework.default_auth import web_auth
from model.apps.trackr import Trackr, TrackrRoles
from model.users import Organization, User, get_user_by_email
from model.utils import set_api_creds

__author__ = 'vinuth'


class AccountsController(PublicController):
    @staticmethod
    def new():
        data.validate(pricing=Required(float), min_pricing=Required(float),
                      required_fields=['name', 'id', 'short_code', 'brand_name', 'support_number',
                                       'admin_name', 'admin_email', 'admin_phone'],
                      error_message='Form has errors')

        org = Organization.get_by_id(data.id)
        if not org:
            org = Organization(id=data.id, name=data.name, secure_signup_step='Approved')
            set_api_creds(org)
            org.put()

        user = get_user_by_email(data.admin_email)
        if not user:
            user = User(raw_name=data.admin_name, email=data.admin_email, phone=data.admin_phone, account_verified=True)
            user.org = [org.key]
        else:
            user.org = list(set(user.org + [org.key]))

        new_password = generate_random_password()
        user.password = web_auth.signed_password(new_password)
        user.put()

        org.admin = user.key
        org.put()

        if not Trackr.get_by_id(org.key.id()):
            Trackr(id=org.key.id(), org=org.key, users=[user.key], brand_name=data.brand_name,
                   support_number=data.support_number).put()

        TrackrRoles.get_or_insert('roles', parent=user.key, kind=['Admin', 'Ops'])

        mail_body = render('/emails/welcome.mako', new_password=new_password, user=user)
        send_email(data.admin_email, mail_body, 'Welcome to Trackr')

        return 'Account Created'

    @staticmethod
    def add_user():
        data.validate(required_fields=['id', 'user_name', 'user_email', 'user_phone'],
                      error_message='Form has errors')

        org = Organization.get_by_id(data.id)
        if not org:
            return error('Organization not found')

        user = get_user_by_email(data.user_email)
        if not user:
            user = User(raw_name=data.user_name, email=data.user_email, phone=data.user_phone, account_verified=True)
            user.org = [org.key]
        else:
            user.org = list(set(user.org + [org.key]))

        new_password = generate_random_password()
        user.password = web_auth.signed_password(new_password)
        user.put()

        TrackrRoles.get_or_insert('roles', parent=user.key, kind=['Admin', 'Ops'])

        mail_body = render('/emails/welcome.mako', new_password=new_password, user=user)
        send_email(data.user_email, mail_body, 'Welcome to Trackr')

        return 'Account Created'

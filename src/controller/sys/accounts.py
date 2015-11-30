from boondi.ext import render
from boondi.globals import data
from boondi.utils import generate_random_password, send_email
from framework.extend import PublicController
from framework.extend_auth import web_auth
from model.users import Organization, User, get_user_by_email

__author__ = 'vinuth'


class AccountsController(PublicController):
    def new(self):
        self.validate(required_fields=['name', 'id', 'short_code', 'brand_name', 'support_number', 'pricing', 'min_pricing', 'admin_name', 'admin_email',
                                       'admin_phone'], error_message='Form has errors')

        org = Organization(id=data.id, name=data.name, short_code=data.short_code, brand_name=data.brand_name,
                           support_number=data.support_number, secure_signup_step='Approved')
        org.put()

        user = get_user_by_email(data.admin_email)
        if not user:
            user = User(raw_name=data.admin_name, email=data.admin_email, phone=data.admin_phone)
            user.org = [org.key]
        else:
            user.org = list(set(user.org + [org.key]))

        new_password = generate_random_password()
        user.password = web_auth.signed_password(new_password)
        user.is_temporary_password = True
        user.type = ['staff']
        user.put()

        org.admin = user.key
        org.put()

        mail_body = render('/emails/welcome.mako', new_password=new_password, user=user)
        send_email(data.admin_email, mail_body, 'Welcome to Trackr')

        return 'Account Created'

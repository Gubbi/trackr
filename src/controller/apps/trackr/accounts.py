import logging

from boondi.controllers import methods
from boondi.data import Required
from boondi.ext import render, error
from boondi.globals import data
from boondi.utils import generate_random_password, send_email
from framework.default_auth import web_auth
from framework.extend import AdminController
from model.apps.trackr import TrackrRoles
from model.users import get_users_in_org, get_user_by_email, User


class AccountsController(AdminController):
    def list_users(self):
        users = get_users_in_org(self.org.key)

        ret = []
        for user in users:
            if not user.active:
                continue

            user_dict = user.to_dict(include=['name', 'email', 'phone'])
            roles = TrackrRoles.get_by_id(self.org.key.id(), parent=user.key)
            user_dict['roles'] = roles.kind if roles else []
            ret.append(user_dict)

        return ret

    @methods('POST')
    def add_user(self):
        data.validate(roles=Required(repeated=True),
                      required_fields=['name', 'email', 'phone'],
                      error_message='Form has errors')

        user = get_user_by_email(data.email)

        logging.info([data.name, data.email, data.phone, data.roles])
        if not user:
            user = User(raw_name=data.name, email=data.email, phone=data.phone, account_verified=True)
            user.org = [self.org.key]

            new_password = generate_random_password()
            user.password = web_auth.signed_password(new_password)

            mail_body = render('/emails/welcome.mako', new_password=new_password, user=user)
            send_email(data.email, mail_body, 'Welcome to Trackr')

        else:
            user.phone = data.phone
            user.raw_name = data.name
            user.active = True
            user.org = list(set(user.org + [self.org.key]))

        user.put()
        roles = TrackrRoles.get_or_insert(self.org.key.id(), parent=user.key)
        roles.kind = data.roles
        roles.put()

        return "User Updated!"

    @staticmethod
    def remove_user():
        data.validate(required_fields=['email'])

        user = get_user_by_email(data.email)
        if user:
            user.active = False
            user.put()

        else:
            return error('User not found')

        return "User Deleted!"

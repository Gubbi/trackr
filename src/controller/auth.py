from boondi.controllers import methods, error
from config.config import FIREBASE_SECRET
from framework.extend import PublicController
from framework.default_auth import web_auth
from boondi.globals import response, data
from boondi.ext import render
from boondi.utils import send_email, generate_random_password
from model.users import get_user_by_email, get_verified_user_by_email
from firebase_token_generator import create_token


class AuthController(PublicController):
    @methods('POST')
    def login(self):
        self.validate(required_fields=['email', 'password'], error_message='Invalid User / Password')

        user = get_verified_user_by_email(data.email.lower())
        password = web_auth.signed_password(data.password)

        if not user:
            return error('Invalid User / Password')

        elif password != user.password:
            return error('Invalid User / Password')

        org = user.org[0].get()
        org_id = org.key.id()
        if org.secure_signup_step == 'Deactivated':
            return error('This account has been deactivated')

        web_auth.set_cookie_for_user(user.email, response)
        response.set_cookie("org_id", org_id, max_age=7200)

        auth_payload = {'uid': user.email, 'org': org_id}
        token = create_token(FIREBASE_SECRET, auth_payload)

        return {
            'message': 'Logged In',
            'user': user.email,
            'org': org_id,
            'fbaseToken': token,
            'isTemporaryPassword': user.is_temporary_password
        }

    @methods('POST')
    def refresh_auth(self):
        web_auth.set_cookie_for_user(self.user.email, response)
        response.set_cookie("org_id", self.user.org[0].id(), max_age=7200)

        return 'Session refreshed'

    def get_auth(self):
        if self.user:
            org = self.user.org[0].id()
            auth_payload = {'uid': self.user.email, 'org': org}
            token = create_token(FIREBASE_SECRET, auth_payload)

            return {
                'message': 'Logged In',
                'user': self.user.email,
                'org': org,
                'fbaseToken': token,
                'isTemporaryPassword': self.user.is_temporary_password
            }

        return {
            'status': 'error',
            'message': 'User not logged in.'
        }

    @methods('POST')
    def reset(self):
        self.validate(required_fields=['email'], error_message='')

        user = get_user_by_email(data.email)

        if not user:
            return error('No user registered with this email')

        new_password = generate_random_password()
        user.password = web_auth.signed_password(new_password)
        user.is_temporary_password = True
        user.put()

        mail_body = render('/emails/reset_link.mako', new_password=new_password)
        send_email(data.email, mail_body, 'Password Reset Notification')

        return 'Password has been reset'

    @methods('POST')
    def change(self):
        self.validate(required_fields=['email', 'password', 'new_password'])

        user = get_user_by_email(data.email)
        password = web_auth.signed_password(data.password)

        if not user:
            return error('No user registered with this email')

        if password != user.password:
            return error('Invalid Password')

        user.password = web_auth.validate_password(data.new_password, data.new_password)
        user.is_temporary_password = False
        user.put()
        return 'Password has been changed'

from boondi.ext import redirect
from boondi.globals import data, request
from boondi.routes import url_for
from oauth2client.client import OAuth2WebServerFlow
from config.config import TRACKR_CREDENTIALS, TRACKR_SCOPES
from framework.extend import SignedInController

__author__ = 'vinuth'


class GoogleController(SignedInController):
    @staticmethod
    def auth_url():
        auth = TRACKR_CREDENTIALS

        flow = OAuth2WebServerFlow(auth['client_id'],
                                   auth['client_secret'],
                                   TRACKR_SCOPES,
                                   url_for('apps.trackr.google', 'authorize', _full=True),
                                   'Trackr App',
                                   auth['auth_uri'],
                                   auth['token_uri'])

        return {
            'auth_url': flow.step1_get_authorize_url()
        }

    def authorize(self):
        if request.params.get('error'):
            return redirect('/app.html#!/settings?error=Permission Denied')

        auth = TRACKR_CREDENTIALS

        flow = OAuth2WebServerFlow(auth['client_id'],
                                   auth['client_secret'],
                                   TRACKR_SCOPES,
                                   url_for('apps.trackr.google', 'authorize', _full=True),
                                   'Trackr App',
                                   auth['auth_uri'],
                                   auth['token_uri'])

        credentials = flow.step2_exchange(request.params['code'])
        if credentials:
            self.org_app.secure_script_access_token = credentials.to_json()
            self.org_app.is_script_enabled = True
            self.org_app.put()

        return redirect('/app.html#!/settings')

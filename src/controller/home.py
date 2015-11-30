from framework.extend import PublicController
from boondi.globals import response
from framework.extend_auth import web_auth


class HomeController(PublicController):
    @staticmethod
    def logout():
        web_auth.remove_user_cookie(response)
        return 'Logged out'

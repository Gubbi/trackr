from framework.extend import PublicController
from boondi.globals import response
from framework.default_auth import web_auth


class HomeController(PublicController):
    @staticmethod
    def logout():
        web_auth.remove_user_cookie(response)
        response.delete_cookie('org_id')
        return 'Logged out'

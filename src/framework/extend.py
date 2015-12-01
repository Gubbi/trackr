from google.appengine.api import namespace_manager
from framework.default_controller import DefaultController
from model.apps.trackr import Trackr, TrackrRoles


class TrackrController(DefaultController):
    app_model = Trackr
    acl_model = TrackrRoles


class PublicController(TrackrController):
    """
    Extended by controllers providing publicly accessible information and actions.
    """
    pass


class SignedInController(TrackrController):
    """
    Extended by controllers providing generic info to any type of signed user but not publicly accessible.
    """
    acl = ["any"]

    def _setup(self):
        namespace_manager.set_namespace('Trackr_'+self.org.key.id())

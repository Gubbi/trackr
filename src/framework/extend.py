import logging
from google.appengine.api import namespace_manager
from boondi.formats import mime_json
from framework.default_auth import DefaultModuleAuth
from framework.default_controller import DefaultController
from model.apps.trackr import Trackr, TrackrRoles, get_org_by_short_code


class TrackrModuleAuth(DefaultModuleAuth):
    @staticmethod
    def _get_user(user_data):
        id_type, user_id = user_data

        if id_type == 'ShortCode':
            return get_org_by_short_code(user_id)
        else:
            return None

sc_module_auth = TrackrModuleAuth()


class TrackrController(DefaultController):
    app_model = Trackr
    acl_model = TrackrRoles

TrackrController.default_auth_list.append(sc_module_auth)
TrackrController.access_auth_map['api'].append(sc_module_auth)
TrackrController.format_map[sc_module_auth] = mime_json


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
        namespace = 'Trackr_'+self.org.key.id()+'_'+str(self.livemode)
        logging.info(['Switching to namespace ', namespace])

        namespace_manager.set_namespace(namespace)

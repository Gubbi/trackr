import logging
from google.appengine.api import namespace_manager
from boondi.formats import mime_json
from framework.default_auth import DefaultModuleAuth
from framework.default_controller import DefaultController
from model.apps.trackr import Trackr, TrackrRoles


class TrackrModuleAuth(DefaultModuleAuth):
    @staticmethod
    def _get_user(user_data):
        id_type, user_id = user_data

        if id_type == 'ShortCode':
            return user_id #get_org_by_short_code(user_id)
        else:
            return None

sc_module_auth = TrackrModuleAuth()


class TrackrController(DefaultController):
    app_model = Trackr
    acl_model = TrackrRoles

    @staticmethod
    def switch_to_default_ns():
        namespace = 'default'
        logging.info(['Switching to namespace ', namespace])
        namespace_manager.set_namespace(namespace)

    @staticmethod
    def switch_namespace(org, livemode):
        namespace = 'Trackr_' + org.key.id() + '_' + str(livemode)
        logging.info(['Switching to namespace ', namespace])

        namespace_manager.set_namespace(namespace)


TrackrController.default_auth_list.append(sc_module_auth)
TrackrController.access_auth_map['api'].append(sc_module_auth)
TrackrController.format_map[sc_module_auth] = mime_json


class PublicController(TrackrController):
    """
    Extended by controllers providing publicly accessible information and actions.
    """
    pass


class AdminController(TrackrController):
    """
    Extended by controllers providing publicly accessible information and actions.
    """
    acl = ["Admin"]


class SignedInController(TrackrController):
    """
    Extended by controllers providing generic info to any type of signed user but not publicly accessible.
    """
    acl = ["any"]

    def _setup(self):
        self.switch_namespace(self.org, self.livemode)

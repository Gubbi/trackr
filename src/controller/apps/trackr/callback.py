import logging

from boondi.controllers import methods, no_auth, set_auth
from boondi.data import Optional
from boondi.ext import error
from boondi.globals import request, data
from framework.extend import PublicController
from model.apps.trackr import get_jobs_by_kyash_code, Trackr
from model.users import Organization
from pykyash import KyashService
from service.apps.push_updates import updates_holder, push_updates
from service.apps.trackr import mark_jobs_as_paid


@set_auth(no_auth)
class CallbackController(PublicController):

    @methods('POST')
    def handle_payment(self, org_id):
        org = Organization.get_by_id(org_id)
        if not org:
            return "No Organization found for " + str(org_id)

        trackr = Trackr.get_by_id(org.key.id())
        api_id = trackr.kyash_public_api_id

        data.validate(required_fields=['order_id', 'kyash_code', 'status'])

        livemode = False if data.kyash_code.startswith('T') else True
        if livemode:
            secret = trackr.secure_hmac_secret_production
        else:
            secret = trackr.secure_hmac_secret_development

        #TODO Need to check if callback_secret is required
        KyashService.authenticate_callback(request, credentials={
            'public_id': api_id,
            'hmac_secret': secret,
            'callback_secret': ""
        })

        update = updates_holder()

        self.switch_namespace(org, livemode)

        if data.status in ['paid', 'expired']:
            return "Ignoring the update for status " + data.status

        jobs = get_jobs_by_kyash_code(data.kyash_code)
        total_amount = reduce(lambda aggr, x: aggr + x.amount, jobs, 0)
        logging.info([jobs, total_amount])

        mark_jobs_as_paid(jobs, update)
        push_updates(org, trackr, livemode, update, self.environment)

        return "Thanks for payment :-)"

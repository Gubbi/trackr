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

        if trackr.active:
            secret = trackr.secure_hmac_secret_production
        else:
            secret = trackr.secure_hmac_secret_development

        #TODO Need to check if callback_secret is required
        KyashService.authenticate_callback(request, credentials={
            'public_id': api_id,
            'hmac_secret': secret,
            'callback_secret': ""
        })

        data.validate(amount=Optional(int),
                      required_fields=['order_id', 'kyash_code', 'status'])
        update = updates_holder()

        if data.status != 'paid':
            return "Ignoring the status update."

        if not data.amount:
            return error("Amount value required.")

        jobs = get_jobs_by_kyash_code(data.kyash_code)
        total_amount = reduce(lambda aggr, x: aggr + x.amount, jobs, 0)
        logging.info([jobs, total_amount])
        if data.amount != total_amount:
            # TODO: Add admin notification email to configured email id.
            return error("Paid amount doesn't match requested amount.")

        mark_jobs_as_paid(jobs, update)
        push_updates(org, trackr, trackr.active, update)

        return "Thanks for payment :-)"

import re
from boondi.controllers import methods
from boondi.ext import error
from boondi.data import Optional
from boondi.globals import data, request
from framework.extend import SignedInController
from model.apps.trackr import get_jobs, get_jobs_by_kyash_code
from pykyash import KyashService
from service.apps.push_updates import updates_holder, push_updates
from service.apps.trackr import create_payment, get_or_create_service_provider, mark_jobs_as_paid

__author__ = 'vinuth'

job_regex = re.compile(r'[ ]*["]?([\w\#\@\-\*\$\.]+)["]?[:, \t]+["]?([\d\.]+)["]?[ \t]*')
jobs_regex = re.compile(r'\A\s*?(?:^' + job_regex.pattern + '$\s*?)+\Z', re.MULTILINE)


class AppController(SignedInController):
    @methods('POST')
    def verify_jobs(self):
        data.validate(required_fields=['job_data'],
                      error_message='Valid list of jobs is required')

        if not jobs_regex.match(data.job_data):
            return error('Please check Jobs data and fix the format.')

        jobs = dict(job_regex.findall(data.job_data))
        total_amount = reduce(lambda aggr, x: aggr+jobs[x], jobs.keys(), 0)

        repeat_jobs = []
        for job in get_jobs(jobs.keys()):
            if job.status == 'Paid':
                return error('Job ID: ' + job.key.id() + ' has already been paid')

            repeat_jobs.append(job.key.id())

        return {
            "message": "Data Verified",
            'jobs': jobs,
            'count': len(jobs),
            'repeat_jobs': repeat_jobs,
            'total': total_amount
        }

    @methods('POST')
    def payment_request(self):
        data.validate(required_fields=['provider_phone', 'provider_name',
                                       'provider_pincode', 'job_data'],
                      optional_fields=['provider_contact'],
                      error_message='Valid Provider Info and Job details is required')

        if not jobs_regex.match(data.job_data):
            return error('Please check Jobs data and fix the format.')

        jobs = dict(job_regex.findall(data.job_data))
        total_amount = reduce(lambda aggr, x: aggr+jobs[x], jobs.keys(), 0)

        update = updates_holder()

        service_provider = get_or_create_service_provider(data.provider_phone, data.provider_name,
                                                          data.provider_pincode, data.provider_contact, update)

        kyash_code = create_payment(service_provider, jobs, total_amount, self.livemode, self.org_app, update)

        push_updates(self.org, self.org_app, self.livemode, update)

        return {
            "message": "KyashCode Created",
            'kyash_code': kyash_code,
            'total': total_amount
        }

    @methods('POST')
    def handle_payment(self):
        api_id = self.org_app.kyash_public_api_id

        if self.livemode:
            secret = self.org_app.secure_hmac_secret_production
        else:
            secret = self.org_app.secure_hmac_secret_development

        KyashService.authenticate_callback(request, credentials={
            'public_id': api_id,
            'hmac_secret': secret
        })

        data.validate(amount=Optional(int),
                      required_fields=['order_id', 'kyash_code', 'status'])

        update = updates_holder()

        if data.status != 'paid':
            return "Ignoring the status update."

        if not data.amount:
            return error("Amount value required.")

        jobs = get_jobs_by_kyash_code(data.kyash_code)
        total_amount = reduce(lambda aggr, x: aggr+x.amount, jobs, 0)

        if data.amount != total_amount:
            # TODO: Add admin notification email to configured email id.
            return error("Paid amount doesn't match requested amount.")

        mark_jobs_as_paid(jobs, update)
        push_updates(self.org, self.org_app, self.livemode, update)

        return "Thanks for payment :-)"

    def settings(self):
        data.define(required_fields=['support_number'],
                    optional_fields=['notification_email'])

        if data.payload:
            data.validate(error_message="Required Data Missing")
            data.put(self.org_app)

            return "Updated settings"

        app_settings = self.org_app.to_dict(include=data.defined_fields)

        return {
            'app': app_settings
        }

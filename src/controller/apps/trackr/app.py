import logging
import re
from boondi.controllers import methods
from boondi.ext import error
from boondi.data import Optional
from boondi.globals import data, request
from framework.extend import SignedInController, PublicController
from model.apps.trackr import get_jobs, get_jobs_by_kyash_code, ServiceProvider
from pykyash import KyashService
from service.apps.push_updates import updates_holder, push_updates
from service.apps.trackr import create_payment, get_or_create_service_provider, mark_jobs_as_paid

__author__ = 'vinuth'

job_regex = re.compile(r'[ ]*["]?([\w\#\@\-\*\$\.]+)["]?[:, \t]+["]?([\d\.]+)["]?[ \t\s]*')
jobs_regex = re.compile(r'\A\s*?(?:^' + job_regex.pattern + '$\s*?)+\Z', re.MULTILINE)


class AppController(SignedInController):
    def search_provider(self):
        try:
            if data.payload:
                data.validate(required_fields=['phone', 'name', 'pincode'],
                              optional_fields=['contact'],
                              error_message='Valid Provider info is required')
                update = updates_holder()
                sp = get_or_create_service_provider(data.phone, data.name, int(data.pincode), data.contact, update)
                push_updates(self.org, self.org_app, self.livemode, update)

            else:
                phone = request.params.get('phone')

                if not phone:
                    return error('Valid Provider Phone is required')

                sp = ServiceProvider.get_by_id(phone)

            if not sp:
                logging.info('Could not find any service provider')
                return {
                    'message': 'Create a new Service Provider'
                }

            return {
                'message': 'Fetched Provider Details',
                'provider': {
                    'name': sp.name,
                    'contact': sp.contact,
                    'pincode': sp.pincode,
                    'phone': sp.phone
                }
            }

        except Exception, e:
            logging.warn(str(e), exc_info=True)
            return error('Error fetching Service Provider details.')

    @methods('POST')
    def verify_jobs(self):
        data.validate(required_fields=['job_data'],
                      error_message='Valid list of jobs is required')

        if not jobs_regex.match(data.job_data):
            return error('Please check Jobs data and fix the format.')

        jobs = dict(job_regex.findall(data.job_data))
        logging.info(jobs)
        total_amount = reduce(lambda aggr, x: aggr+int(jobs[x]), jobs.keys(), 0)

        repeat_jobs = []
        for job in get_jobs(jobs.keys()):
            if job.status == 'Paid':
                return error('Job ID: ' + job.key.id() + ' has already been paid')

            repeat_jobs.append(job.key.id())

        return {
            "message": "Data Verified",
            'job_details': {
                'jobs': jobs,
                'count': len(jobs),
                'repeat_jobs': repeat_jobs,
            },
            'total': total_amount
        }

    @methods('POST')
    def payment_request(self):
        data.validate(required_fields=['phone', 'name', 'pincode', 'job_data'],
                      optional_fields=['contact'],
                      error_message='Valid Provider Info and Job details is required')

        if not jobs_regex.match(data.job_data):
            return error('Please check Jobs data and fix the format.')

        jobs = dict(job_regex.findall(data.job_data))
        total_amount = reduce(lambda aggr, x: aggr+int(jobs[x]), jobs.keys(), 0)

        update = updates_holder()

        service_provider = get_or_create_service_provider(data.phone, data.name,
                                                          int(data.pincode), data.contact, update)

        kyash_code = create_payment(service_provider, jobs, total_amount, self.livemode, self.org_app, update)

        push_updates(self.org, self.org_app, self.livemode, update)
        logging.info(kyash_code)
        return {
            "message": "KyashCode Created",
            'kyash_code': kyash_code,
            'total': total_amount
        }

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

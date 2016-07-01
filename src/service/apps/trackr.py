import datetime
import logging
import random

from boondi.utils import unix_time
from model.apps.trackr import ServiceProvider, Job
from pykyash import KyashCode, Contact

__author__ = 'vinuth'

batch = (datetime.datetime.utcnow() + datetime.timedelta(hours=5.5)).strftime('%Y-%m-%d')
stream_path = lambda: 'activities/' + batch
sp_path = lambda phone: 'sp/' + str(phone)
job_path = lambda job_id: 'jobs/' + str(job_id)
job_status_path = lambda job_id: 'jobs/' + str(job_id) + '/status'
ts = lambda: unix_time(datetime.datetime.utcnow())


def get_or_create_service_provider(phone, name, pincode, contact, update):
    try:
        logging.info('Get / Create Service Provider.')
        sp = ServiceProvider.get_by_id(phone)

        if sp:
            logging.info('Service Provider Found')
            sp_modified = False

            if sp.name != name:
                sp.name = name
                sp_modified = True

            if sp.contact != contact:
                sp.contact = contact
                sp_modified = True

            if sp.pincode != pincode:
                sp.pincode = pincode
                sp_modified = True

            if sp_modified:
                logging.info('Service Provider Details changed.')
                sp.put()

                tst = ts()
                update['FBase']['PATCH'][sp_path(phone)] = {'name': name, 'phone': phone, 'contact': contact,
                                                            'pincode': pincode, '.priority': -1 * tst}

        else:
            logging.info('Creating new service provider')
            sp = ServiceProvider(id=phone, name=name, contact=contact, phone=phone, pincode=pincode)
            sp.put()

            tst = ts()
            update['FBase']['PATCH'][sp_path(phone)] = {'name': name, 'phone': phone, 'contact': contact,
                                                        'pincode': pincode, '.priority': -1 * tst}

        return sp

    except:
        raise ValueError('Error creating service provider')


def create_kyash_code(total_amount, service_provider, org_app, livemode):
    logging.info('Creating new KyashCode.')

    api_id = org_app.kyash_public_api_id

    if livemode:
        secret = org_app.secure_api_secret_production
    else:
        secret = org_app.secure_api_secret_development

    contact = Contact({
        'first_name': service_provider.name,
        'phone': service_provider.phone,
        'address': service_provider.contact,
        'pincode': service_provider.pincode
    })

    code = KyashCode({
        'order_id': str(unix_time(datetime.datetime.utcnow())) + str(random.randrange(1, 100)),
        'amount': total_amount,
        'billing_contact': contact,
        'shipping_contact': contact
    })

    code.create(credentials={
        'public_id': api_id,
        'api_secret': secret
    })

    return code.__getattribute__('id')


def create_payment(service_provider, jobs, total_amount, livemode, org_app, update):
    logging.info('Creating new payment request.')

    kyash_code = create_kyash_code(total_amount, service_provider, org_app, livemode)

    for job_id, amount in jobs.iteritems():
        job = Job.get_by_id(job_id)

        if not job:
            job = Job(id=job_id, amount=int(amount), by=service_provider.key, kyash_code=[kyash_code])
        else:
            job.kyash_code.append(kyash_code)

        job.put()

        tst = ts()
        update['FBase']['PATCH'][job_path(job_id)] = {
            'ts': {'.sv': 'timestamp'}, 'amount': amount, 'by': service_provider.key.id(),
            'kyash_code': kyash_code, 'status': 'Pending', '.priority': -1 * tst,
        }

        update['FBase']['PATCH']['logs/' + job_path(job.key.id()) + '/' + str(tst)] = {
            'type': 'inline',
            'ts': {'.sv': 'timestamp'},
            'subtype': 'KyashCode: ' + kyash_code,
            '.priority': tst,
        }

    return kyash_code

def mark_jobs_as_paid(jobs, update):
    for job in jobs:
        job.status = 'Paid'
        job.put()

        tst = ts()
        update['FBase']['PATCH'][job_status_path(job.key.id())] = 'Paid'

        update['FBase']['PATCH']['logs/' + job_path(job.key.id()) + '/' + str(tst)] = {
            'type': 'inline',
            'ts': {'.sv': 'timestamp'},
            'subtype': 'Payment Made',
            '.priority': tst,
        }

        sp = job.by.get()
        update['FBase']['PATCH']['mis/' + str(batch) + '/' + str(job.key.id())] = {
            'type': 'inline',
            'ts': str(tst),
            'job_id': str(job.key.id()),
            'payer': str(sp.name),
            'payer_num': str(sp.phone),
            'kyash_code': str(job.kyash_code[0]),
            'amount': str(job.amount),
        }

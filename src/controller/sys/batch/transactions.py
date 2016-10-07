import csv
import logging
from collections import defaultdict

import cloudstorage as gcs
from boondi.ext import error

from boondi.globals import data
from boondi.controllers import set_auth, no_auth, allow_scheme
from config.config import FIREBASE_STORAGE
from framework.extend import PublicController
from model.apps.trackr import JobsUploaded, get_jobs, CSV_FILE_COLUMNS
from service.apps.push_updates import updates_holder, push_updates
from service.apps.trackr import ts, upload_path, get_or_create_service_provider, create_payment


@set_auth(no_auth)
@allow_scheme('http')
class TransactionsController(PublicController):
    @allow_scheme('http')
    def verify_uploaded_jobs(self):
        data.validate(required_fields=['id', 'file'])

        try:
            job_upload = JobsUploaded.get_by_id(int(data.id))
            if not job_upload:
                raise ValueError("No uploaded file found.")

            logging.info(job_upload)
            app = job_upload.app.get()
            logging.info(app)
            org = app.org.get()

            repeat_jobs = []
            total_jobs = []
            total_amount = 0

            # bucket = "/trackrdb.appspot.com/images/"
            csv_file_path = FIREBASE_STORAGE + data.file
            fields = [f['name'] for f in CSV_FILE_COLUMNS['fields']]

            logging.info(['Reading file', csv_file_path])
            with gcs.open(csv_file_path, 'r') as rows:
                reader = csv.DictReader(rows, fields)
                for row in reader:
                    total_amount = total_amount + int(row.get('amount'))
                    total_jobs.append(row.get('id'))

                for job in get_jobs(total_jobs):
                    if job.status == "Paid":
                        return error('Job ID: ' + job.key.id() + ' has already been paid')

                    repeat_jobs.append(job.key.id())

            jobs_count = len(total_jobs)
            job_upload.rows = jobs_count
            job_upload.codes = jobs_count
            job_upload.amount = total_amount
            job_upload.put()

            tst = ts()
            update = updates_holder()
            update['FBase']['PATCH'][upload_path(job_upload.key.id())] = {
                'ts': {'.sv': 'timestamp'},
                'rows': jobs_count,
                'codes': jobs_count,
                'amount': total_amount,
                'repeat': len(repeat_jobs),
                'url': str(job_upload.url),
                '.priority': -1 * tst,
            }
            push_updates(org, job_upload.app, job_upload.livemode, update, self.environment)

        except Exception as e:
            logging.critical(str(e))

        return "Done"

    @allow_scheme('http')
    def generate_kyash_codes(self):
        data.validate(required_fields=['id', 'file'])

        job_upload = JobsUploaded.get_by_id(int(data.id))
        if not job_upload:
            raise ValueError("No uploaded file found.")

        logging.info(job_upload)
        app = job_upload.app.get()
        logging.info(app)
        org = app.org.get()

        csv_file_path = FIREBASE_STORAGE + data.file
        fields = [f['name'] for f in CSV_FILE_COLUMNS['fields']]

        sp_list = defaultdict(dict)  # e.g. sp_list = {'8050112266': {'jobs': {'q': '1', 'r': '2'}, 'name': 'sandeep'}
        with gcs.open(csv_file_path, 'r') as rows:
            reader = csv.DictReader(rows, fields)
            for row in reader:
                mobile = str(row['mobile']).strip().decode('utf-8-sig').encode('utf-8')
                sp_list[mobile]['name'] = row.get('name', '')
                sp_list[mobile]['contact'] = row.get('contact', '')
                sp_list[mobile]['pincode'] = int(row.get('pincode', ''))

                try:
                    sp_list[mobile]['jobs'].update({row.get('id', 'None'): int(row.get('amount', 0))})
                except KeyError:
                    sp_list[mobile]['jobs'] = {row.get('id', 'None'): int(row.get('amount', 0))}

                try:
                    sp_list[mobile]['total_amount'] += int(row.get('amount', 0))
                except KeyError:
                    sp_list[mobile]['total_amount'] = int(row.get('amount', 0))

        for k, v in sp_list.iteritems():
            logging.info([k, v])
            update = updates_holder()
            service_provider = get_or_create_service_provider(k, v['name'],
                                                              int(v['pincode']), v['contact'], update)

            create_payment(service_provider, v['jobs'], v['total_amount'], job_upload.livemode, app, update)

            push_updates(org, job_upload.app, job_upload.livemode, update, self.environment)

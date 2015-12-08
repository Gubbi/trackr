import logging
from config.config import SCRIPT_ID, FIREBASE_URL
from oauth2client.client import OAuth2Credentials
from apiclient.discovery import build
from boondi.utils import google_api_access, authorized_http
from firebase import Firebase

__author__ = 'vinuth'


def updates_holder():
    return {
        'Sheet': {
            'Customers': {},
            'Sales Executives': {},
            'Supervisors': {},
            'Sales Orders': {},
            'Invoices': {},
            'Payments': {},
            'Deposits': {},
            'Credits': {}
        },
        'FBase': {
            'PUT': {},
            'PATCH': {},
            'POST': {}
        }
    }


def push_updates(org, org_app, livemode, update):
    org_id = org.key.id()
    spreadsheet_id = org_app.spreadsheet_id

    if not livemode:
        org_id += '_demo'
        spreadsheet_id = org_app.demo_spreadsheet_id

    fbase_url = Firebase(FIREBASE_URL + org_id + '.json')
    fbase_updates = update['FBase']

    if 'PATCH' in fbase_updates and fbase_updates['PATCH']:
        logging.info(fbase_updates['PATCH'])
        fbase_url.update(fbase_updates['PATCH'])

    if spreadsheet_id:
        try:
            http = authorized_http(OAuth2Credentials.from_json(org_app.secure_script_access_token))
            service = build('script', 'v1', http=http)

            if update['Sheet']['Payments']:
                for key, row in update['Sheet']['Payments'].iteritems():
                    logging.info(['Creating Row', row])

                    request = {
                        'function': 'update_payment',
                        'parameters': [spreadsheet_id] + row
                    }
                    response = service.scripts().run(body=request,
                                                     scriptId=SCRIPT_ID).execute()

                    if 'error' in response:
                        error = response['error']['details'][0]
                        logging.error("Script error message: {0}".format(error['errorMessage']))

                        if 'scriptStackTraceElements' in error:
                            for trace in error['scriptStackTraceElements']:
                                logging.error("\t{0}: {1}".format(trace['function'],
                                                                  trace['lineNumber']))
        except:
            logging.error('Error while updating spreadsheet.', exc_info=True)

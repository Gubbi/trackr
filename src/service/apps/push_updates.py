import logging
from config.config import SCRIPT_ID
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


def push_updates(org, org_app, update):
    fbase_url = Firebase('https://trackrapp.firebaseio.com/' + org.key.id() + '.json')
    fbase_updates = update['FBase']

    if 'PATCH' in fbase_updates and fbase_updates['PATCH']:
        logging.info(fbase_updates['PATCH'])
        logging.info(fbase_url.update(fbase_updates['PATCH']))

    if org_app.spreadsheet_id:
        sheets = org_app.script_sheets or ['Payments']
        sheet_updates = {sheet: update['Sheet'][sheet] for sheet in sheets}

        logging.info(sheet_updates)
        try:
            http = authorized_http(OAuth2Credentials.from_json(org_app.secure_script_access_token))

            # Do something with sheet_updates.
            service = build('script', 'v1', http=http)

            if sheet_updates and sheet_updates['Payments']:
                for key, row in sheet_updates['Payments'].iteritems():
                    logging.info(['Creating Row', row])

                    request = {
                        'function': 'update_payment',
                        'parameters': [org_app.spreadsheet_id] + row
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


    # Nothing should be PUT or POSTed directly to the root  url.
    # if 'PUT' in fbase_updates and fbase_updates['PUT']:
    #     logging.info(fbase_updates['PUT'])
    #     logging.info(fbase_url.set(fbase_updates['PUT']))
    #
    # if 'POST' in fbase_updates and fbase_updates['POST']:
    #     logging.info(fbase_updates['POST'])
    #     logging.info(fbase_url.push(fbase_updates['POST']))

import logging
from firebase import Firebase

__author__ = 'vinuth'


def push_updates_holder():
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
    if org_app.spreadsheet_id or True:
        logging.info(update['Sheet'])

        sheets = org_app.spreadsheet_sheets or ['Payments']
        sheet_updates = {sheet: update['Sheet'][sheet] for sheet in sheets}

        # Do something with sheet_updates.
        logging.info(sheet_updates)

    fbase_url = Firebase('https://trackrapp.firebaseio.com/' + org.key.id() + '.json')
    fbase_updates = update['FBase']

    if 'PATCH' in fbase_updates and fbase_updates['PATCH']:
        logging.info(fbase_updates['PATCH'])
        logging.info(fbase_url.update(fbase_updates['PATCH']))

    if 'PUT' in fbase_updates and fbase_updates['PUT']:
        logging.info(fbase_updates['PUT'])
        logging.info(fbase_url.set(fbase_updates['PUT']))

    if 'POST' in fbase_updates and fbase_updates['POST']:
        logging.info(fbase_updates['POST'])
        logging.info(fbase_url.push(fbase_updates['POST']))

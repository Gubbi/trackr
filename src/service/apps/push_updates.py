import logging
from config.config import FIREBASE_URL
from firebase import Firebase

__author__ = 'vinuth'


def updates_holder():
    return {
        'FBase': {
            'PUT': {},
            'PATCH': {},
            'POST': {}
        }
    }


def push_updates(org, org_app, livemode, update):
    org_id = org.key.id()

    if not livemode:
        org_id += '_demo'

    logging.info("Writing to: " + FIREBASE_URL + org_id + '.json')
    fbase_url = Firebase(FIREBASE_URL + org_id + '.json')
    fbase_updates = update['FBase']

    if 'PATCH' in fbase_updates and fbase_updates['PATCH']:
        fbase_url.update(fbase_updates['PATCH'])

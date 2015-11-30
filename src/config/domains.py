from boondi.domain_config import DomainConfig

__author__ = 'vinuth'

PROD = 'prod'
DEV = 'dev'
TEST = 'test'

domain_config = DomainConfig(
    (
        DEV, (['192.168.\d{1,3}.\d{1,3}', '0.0.0.0', '127.0.0.1', 'localhost', '10.0.2.2', '10.0.0.\d{1,3}'], ['8080', '9292']),
        {'zones': ['auth'],                  'subdomains': False,    'access': ['web', 'api', 'apps']}
    ),
    (
        TEST, 'bilentapptest.appspot.com',
        {'zones': ['auth'],                   'subdomains': False,     'access': ['web', 'api', 'apps']}
    ),
    (
        PROD, 'bilentapp.appspot.com',
        {'zones': ['auth'],                   'subdomains': True,     'access': ['web', 'api', 'apps']}
    ),
)

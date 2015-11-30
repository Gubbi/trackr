from hashlib import sha256
from google.appengine.ext import ndb
from sendgrid import sendgrid

__author__ = 'vinuth'

APP_NAME = 'AuthServer'

# Settings for local host. KEYS, SECRETS, etc.,
APP_SECRET = "bec0lkjewjr942375elekshdhfnbilentvabf782345o9ufdkskkyashvab2d9ab3a02"
SESSION_SALT = "kykdgkglag;a4308#$^DFSNN$#aslh;<{:wq3932$#@$)*&dsaj"

MAIN_DOMAIN = 'localhost:8080'
API_DOMAIN = 'localhost:8082'

emulator_ips = ['10.0.2.2']

# Kyash Admin settings
ADMIN_PASSWORD = '308#$^DFSNN'

# OAuth Settings
OAUTH_TOKEN_SECRET = 'YCMD@#ABLS OQ@#$JH48QWH$@#598#@!932 TOR$@OB&*(1N1SSR#$^&RTC640CFOCN'
OAUTH_CIPHER_SECRET = sha256("lsyhwoud63jx@*JS wj82kalw2$dEks92a$8hkslR ,2Ls*Qn%k").digest()

FIREBASE_SECRET = 'PXagmBMfPfNlJ8IufPrIeHApt7qewFdAbsCLVV9b'

# Sendgrid
SENDGRID = sendgrid.SendGridClient('kya.sh', 'Kyash4mBilent')

try:
    from config_prod import *
except:
    pass

class AppConfig(ndb.Expando):
    pass

db_config = AppConfig.get_by_id(APP_NAME)
if db_config:
    for key, value in db_config.to_dict().iteritems():
        globals()[key] = value

from google.appengine.ext import ndb
from google.appengine.ext.ndb import Key
from model.users import App
from model.utils import PhoneProperty, MobilePhoneProperty

NA = 0
READ = 1
WRITE = 2

perms = [READ, WRITE, NA]


class Trackr(App):
    brand_name                      = ndb.StringProperty(verbose_name='Brand Name')

    kyash_public_api_id             = ndb.StringProperty()
    secure_api_secret_production    = ndb.StringProperty()
    secure_api_secret_development   = ndb.StringProperty()
    secure_hmac_secret_production   = ndb.StringProperty()
    secure_hmac_secret_development  = ndb.StringProperty()

    support_number                  = PhoneProperty(verbose_name='Support helpline')
    notification_email              = ndb.StringProperty(verbose_name='Notifications Email')


class TrackrRoles(ndb.Model):
    kind                = ndb.StringProperty(choices=['Ops', 'Admin'], repeated=True)
    create_kc           = ndb.IntegerProperty(choices=perms, default=WRITE)
    view_all_jobs       = ndb.IntegerProperty(choices=perms, default=WRITE)
    users               = ndb.IntegerProperty(choices=perms, default=WRITE)


class ServiceProvider(ndb.Model):
    name                = ndb.StringProperty()
    phone               = MobilePhoneProperty()
    contact             = ndb.StringProperty()
    pincode             = ndb.IntegerProperty()


class Job(ndb.Model):
    amount              = ndb.IntegerProperty(default=0)
    by                  = ndb.KeyProperty(kind=ServiceProvider)

    incharge            = ndb.KeyProperty(kind='User')
    status              = ndb.StringProperty(choices=['Pending', 'Paid'], default='Pending')

    kyash_code          = ndb.StringProperty(repeated=True)

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


def get_jobs(job_ids):
    jobs = ndb.get_multi([Key('Job', job_id) for job_id in job_ids])
    return [job for job in jobs if job]


def get_jobs_by_kyash_code(kyash_code):
    return Job.query(Job.kyash_code == kyash_code).fetch(100)

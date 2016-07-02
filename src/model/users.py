from google.appengine.ext import ndb
from model.utils import EmailProperty, Address, form_name, APICredentials, MobilePhoneProperty


class App(ndb.Model):
    users                           = ndb.KeyProperty(kind='User', repeated=True)
    org                             = ndb.KeyProperty(kind='Organization')
    active                          = ndb.BooleanProperty(default=True)

    createdAt                       = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt                      = ndb.DateTimeProperty(auto_now=True)


class Organization(ndb.Model):
    name                            = ndb.StringProperty(verbose_name='Business Name')

    registered_address              = ndb.StructuredProperty(Address, verbose_name='Registered Address')

    pan_card_number                 = ndb.StringProperty(verbose_name='PAN Card Number')
    pan_dob                         = ndb.DateProperty(verbose_name='Date of Birth/Incorporation')
    service_tax_number              = ndb.StringProperty(verbose_name='Service Tax Number')
    registration_number             = ndb.StringProperty(verbose_name='Firm Registration Number')

    referred_by                     = ndb.KeyProperty(kind='MerchantPartner')
    referral_id                     = ndb.StringProperty()

    admin                           = ndb.KeyProperty(kind='User')

    secure_signup_step              = ndb.StringProperty(choices={'New', 'Verified', 'Entering Details', 'Reviewing',
                                                                  'Approved', 'Deactivated'}, default='New')

    secure_api_id                   = ndb.StringProperty(verbose_name='')
    secure_production               = ndb.LocalStructuredProperty(APICredentials)
    secure_development              = ndb.LocalStructuredProperty(APICredentials)

    createdAt                       = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt                      = ndb.DateTimeProperty(auto_now=True)


class User(ndb.Model):
    first_name                      = ndb.StringProperty(verbose_name='First Name')
    middle_name                     = ndb.StringProperty(verbose_name='Middle Name', default='')
    last_name                       = ndb.StringProperty(verbose_name='Last Name')
    raw_name                        = ndb.StringProperty(verbose_name='Name')
    name                            = ndb.ComputedProperty(form_name)

    password                        = ndb.BlobProperty(indexed=False, verbose_name='Password')
    is_temporary_password           = ndb.BooleanProperty(default=True)

    email                           = EmailProperty(verbose_name='Email', unique=True)
    phone                           = MobilePhoneProperty(verbose_name='Personal Mobile Number', unique=True)

    account_verified                = ndb.BooleanProperty(default=False)
    verification_code               = ndb.StringProperty()

    org                             = ndb.KeyProperty(kind=Organization, repeated=True)

    createdAt                       = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt                      = ndb.DateTimeProperty(auto_now=True)
    active                          = ndb.BooleanProperty(default=True)


get_user_by_email = lambda email: User.query(User.email == email).get()
get_user_by_phone = lambda phone: User.query(User.phone == phone).get()
get_org_by_phone = lambda phone: Organization.query(Organization.phone == phone).get()
get_users_in_org = lambda org: User.query(User.org == org).fetch()
get_verified_user_by_email = lambda email: User.query(User.email == email, User.account_verified == True).get()
get_user_by_verification_code = lambda code: User.query(User.verification_code == code).get()
get_org_by_api_key = lambda api_key: Organization.query().filter(Organization.secure_api_id == api_key).get()

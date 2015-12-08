from google.appengine.ext import ndb
from model.users import App, Organization
from model.utils import PhoneProperty, MobilePhoneProperty, ShortCodeProperty

NA = 0
READ = 1
WRITE = 2

perms = [READ, WRITE, NA]


class Trackr(App):
    short_code                      = ShortCodeProperty(verbose_name='SMS short code', unique=True)
    brand_name                      = ndb.StringProperty(verbose_name='Brand Name')
    support_number                  = PhoneProperty(verbose_name='Support helpline')
    notification_email              = ndb.StringProperty(verbose_name='Notifications Email')

    script_sheets                   = ndb.StringProperty(repeated=True)

    is_script_enabled               = ndb.BooleanProperty(default=False)
    secure_script_access_token      = ndb.TextProperty()
    spreadsheet_id                  = ndb.StringProperty()
    demo_spreadsheet_id             = ndb.StringProperty()

    secure_pricing                  = ndb.FloatProperty()
    secure_min_pricing              = ndb.FloatProperty()


class TrackrRoles(ndb.Model):
    kind                = ndb.StringProperty(choices=['Staff', 'Sales', 'Customer', 'Admin'], repeated=True)
    salesOrders         = ndb.IntegerProperty(choices=perms, default=WRITE)
    invoices            = ndb.IntegerProperty(choices=perms, default=WRITE)
    payments            = ndb.IntegerProperty(choices=perms, default=WRITE)
    users               = ndb.IntegerProperty(choices=perms, default=WRITE)
    deposits            = ndb.IntegerProperty(choices=perms, default=WRITE)


class Customer(ndb.Model):
    name                = ndb.StringProperty()
    phone               = MobilePhoneProperty()
    contact             = ndb.StringProperty()


class Supervisor(ndb.Model):
    name                = ndb.StringProperty()
    phone               = MobilePhoneProperty()
    email               = ndb.StringProperty()


class Agent(ndb.Model):
    name                = ndb.StringProperty()
    phone               = MobilePhoneProperty()

    supervisors         = ndb.KeyProperty(kind=Supervisor, repeated=True)


class SalesOrder(ndb.Model):
    on                  = ndb.StringProperty()
    amount              = ndb.FloatProperty(default=0)
    advance_amount      = ndb.FloatProperty(default=0)

    advance             = ndb.KeyProperty(kind='Payment')

    customer            = ndb.KeyProperty(kind=Customer)
    incharge            = ndb.KeyProperty(kind=Agent)

    invoice             = ndb.KeyProperty(kind='Invoice')

    status              = ndb.StringProperty(choices=['Recorded', 'Cancelled'], default='Recorded')

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Invoice(ndb.Model):
    on                  = ndb.StringProperty()
    order               = ndb.KeyProperty(kind=SalesOrder)
    customer            = ndb.KeyProperty(kind=Customer)

    amount              = ndb.FloatProperty(default=0)

    paid                = ndb.FloatProperty(default=0)
    payments            = ndb.KeyProperty(kind='Payment', repeated=True)

    credit              = ndb.FloatProperty(default=0)
    credits             = ndb.KeyProperty(kind='Credit', repeated=True)

    balance             = ndb.ComputedProperty(lambda self: (self.amount or 0) - (self.paid or 0) + (self.credit or 0))

    status              = ndb.StringProperty(choices=['Recorded', 'Cancelled'], default='Recorded')

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Payment(ndb.Model):
    by                  = ndb.KeyProperty(kind=Customer)
    to                  = ndb.KeyProperty(kind=Agent)

    amount              = ndb.FloatProperty()

    invoice             = ndb.KeyProperty(kind=Invoice)
    is_advance          = ndb.BooleanProperty(default=False)

    status              = ndb.StringProperty(choices=['Recorded', 'Cancelled'], default='Recorded')
    cancellation_id     = ndb.StringProperty()

    is_deposited        = ndb.BooleanProperty(default=False)

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Deposit(ndb.Model):
    by                  = ndb.KeyProperty(kind=Agent)

    amount              = ndb.FloatProperty()
    comment             = ndb.StringProperty()

    payments            = ndb.KeyProperty(kind=Payment, repeated=True)

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Credit(ndb.Model):
    to                  = ndb.KeyProperty(kind=Customer)
    invoice             = ndb.KeyProperty(kind=Invoice)

    amount              = ndb.FloatProperty()
    comment             = ndb.StringProperty()

    status              = ndb.StringProperty(choices=['Recorded', 'Cancelled'], default='Recorded')
    cancellation_id     = ndb.StringProperty()

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Cache(ndb.Model):
    value               = ndb.StringProperty()
    createdAt           = ndb.DateTimeProperty(auto_now_add=True)


def get_org_by_short_code(short_code):
    trackr = Trackr.query(Trackr.short_code == short_code).get(keys_only=True)
    if trackr:
        return Organization.get_by_id(trackr.id())

    return None

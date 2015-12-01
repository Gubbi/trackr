from google.appengine.ext import ndb
from model import accounts
from model.users import App
from model.utils import PhoneProperty, MobilePhoneProperty

NA = 0
READ = 1
WRITE = 2

perms = [READ, WRITE, NA]


class Trackr(App):
    short_code                      = ndb.StringProperty(verbose_name='SMS short code')
    brand_name                      = ndb.StringProperty(verbose_name='Brand Name')
    support_number                  = PhoneProperty(verbose_name='Support helpline')

    pricing                         = ndb.FloatProperty()
    min_pricing                     = ndb.FloatProperty()


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


class Sales(ndb.Model):
    name                = ndb.StringProperty()
    phone               = MobilePhoneProperty()

    supervisors         = ndb.KeyProperty(kind=Supervisor, repeated=True)


class SalesOrder(ndb.Model):
    on                  = ndb.StringProperty()
    amount              = ndb.FloatProperty()
    advance_amount      = ndb.FloatProperty()

    advance             = ndb.KeyProperty(kind='Payment')

    customer            = ndb.KeyProperty(kind=Customer)
    incharge            = ndb.KeyProperty(kind=Sales)

    invoice             = ndb.KeyProperty(kind='Invoice')

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Invoice(ndb.Model):
    on                  = ndb.StringProperty()
    order               = ndb.KeyProperty(kind=SalesOrder)
    customer            = ndb.KeyProperty(kind=Customer)

    amount              = ndb.FloatProperty()
    paid                = ndb.FloatProperty()
    credit              = ndb.FloatProperty()
    balance             = ndb.ComputedProperty(lambda self: self.amount - self.paid + self.credit)

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Payment(ndb.Model):
    by                  = ndb.KeyProperty(kind=Customer)
    to                  = ndb.KeyProperty(kind=Sales)

    amount              = ndb.FloatProperty()

    invoice             = ndb.KeyProperty(kind=Invoice)
    is_advance          = ndb.BooleanProperty(default=False)

    status              = ndb.StringProperty(choices=['Recorded', 'Cancelled'], default='Recorded')
    cancellation_id     = ndb.StringProperty()

    is_deposited        = ndb.BooleanProperty(default=False)

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)


class Deposit(ndb.Model):
    by                  = ndb.KeyProperty(kind=Sales)

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


class InvoiceLog(ndb.Model):
    amount              = ndb.FloatProperty()
    kind                = ndb.StringProperty(choices=['Payment', 'Advance', 'Credit', 'Payment Cancelled',
                                                      'Credit Cancelled'])

    old_amount          = ndb.FloatProperty()
    payment             = ndb.KeyProperty(kind=Payment)
    credit              = ndb.KeyProperty(kind=Credit)


class AccountLog(accounts.AccountLog):
    payment             = ndb.KeyProperty(kind=Payment)
    credit              = ndb.KeyProperty(kind=Credit)
    deposit             = ndb.KeyProperty(kind=Deposit)
    invoice             = ndb.KeyProperty(kind=Invoice)

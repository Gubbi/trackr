from google.appengine.ext import ndb
from boondi.utils import get_leaf_values


SLOTS = {
}


CATEGORY_STATUS = {
}

valid_statuses = {value for value in get_leaf_values(CATEGORY_STATUS)}


class Slots(ndb.Model):
    name                        = ndb.StringProperty()
    balance                     = ndb.FloatProperty()


class Account(ndb.Expando):
    amount              = ndb.FloatProperty(default=0)
    slots               = ndb.StructuredProperty(Slots, repeated=True)

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def builtin(cls, key):
        return Account.get_or_insert(key)


class ChargeDetail(ndb.Model):
    amount                      = ndb.FloatProperty()
    description                 = ndb.StringProperty()
    rule                        = ndb.StringProperty()
    charged_by                  = ndb.StringProperty()


class AccountLog(ndb.Model):
    """
    Has an Account as parent.
    An explicitly given Log ID is required while constructing the entity.
    """
    ts                  = ndb.DateTimeProperty(verbose_name="Timestamp when this transaction occurred.")
    record_type         = ndb.StringProperty(choices=['Received', 'Fee', 'Tax', 'Reversed', 'Refund'])

    from_slot           = ndb.StringProperty(choices=SLOTS.keys())
    to_slot             = ndb.StringProperty(choices=SLOTS.keys())

    amount              = ndb.FloatProperty()
    charges             = ndb.StructuredProperty(ChargeDetail, repeated=True)
    net                 = ndb.FloatProperty()
    slots_snapshot      = ndb.StructuredProperty(Slots)

    reverse_id          = ndb.KeyProperty('TransactionLog')

    description         = ndb.TextProperty()
    label               = ndb.StringProperty()

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)

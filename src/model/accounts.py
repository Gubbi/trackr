from google.appengine.ext import ndb


class Slots(ndb.Model):
    name                        = ndb.StringProperty()
    balance                     = ndb.FloatProperty()


class Account(ndb.Model):
    slots               = ndb.StructuredProperty(Slots, repeated=True)


class ChargeDetail(ndb.Model):
    description                 = ndb.StringProperty()
    rule                        = ndb.StringProperty()
    charged_by                  = ndb.StringProperty()


class AccountLog(ndb.Model):
    """
    Has an Account as parent.
    An explicitly given Log ID is required while constructing the entity.
    """
    ts                  = ndb.DateTimeProperty(verbose_name="Timestamp when this transaction occurred.")
    record_type         = ndb.StringProperty()

    from_slot           = ndb.StringProperty()
    to_slot             = ndb.StringProperty()

    amount              = ndb.FloatProperty()
    charges             = ndb.StructuredProperty(ChargeDetail, repeated=True)
    net                 = ndb.FloatProperty()
    slots_snapshot      = ndb.StructuredProperty(Slots)

    reverse_id          = ndb.KeyProperty('TransactionLog')

    description         = ndb.TextProperty()
    label               = ndb.StringProperty()

    createdAt           = ndb.DateTimeProperty(auto_now_add=True)
    modifiedAt          = ndb.DateTimeProperty(auto_now=True)

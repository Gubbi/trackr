import re

from google.appengine.ext import ndb
from google.appengine.ext.ndb import Key

from mobile_numbers import mobile_phone_re
from model.choices import states
from model.unique import UniqueProperty
from ordered_set import OrderedSet


email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
    r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,12}\.?$', re.IGNORECASE)  # domain

short_code_re = re.compile('^[0-9a-zA-Z]*$')

mobile_regex = re.compile('^\s*(?:[+]?91)?(?P<mobile>\d{10})\s*$')
get_mobile = lambda mobile_raw: mobile_regex.sub('\\1', mobile_raw)

def get_state_code(entity):
    return states[entity.state.title()] if entity.state else ''


class EmailProperty(UniqueProperty):
    def _validate(self, value):
        if value:
            if not email_re.search(str(value)):
                raise TypeError('Enter a valid Email ID.')
        else:
            return None


class ShortCodeProperty(UniqueProperty):
    def _validate(self, value):
        if not short_code_re.search(str(value)):
            raise TypeError('Invalid Short Code. Use only alphabets and numbers.')

        return str(value).lower()


class PositiveIntegerProperty(ndb.IntegerProperty):
    def _validate(self, value):
        try:
            if value != "":
                if int(value) >= 0:
                    return int(value)
        except:
            pass

        raise TypeError('Should be a positive number.')


class StringProperty(ndb.StringProperty):
    def __init__(self, *args, **kwargs):
        super(StringProperty, self).__init__(*args, **kwargs)
        if 'choices' in kwargs:
            self._choices = OrderedSet(kwargs['choices'])


class PinCodeProperty(ndb.IntegerProperty):
    def _validate(self, value):
        try:
            if not isinstance(value, int):
                val = int(value)
            else:
                val = value

        except ValueError:
            raise TypeError('Not a valid Pin Code')

        if len(str(val)) == 6:
            return val
        else:
            raise TypeError('Not a valid Pin Code')


class PhoneProperty(UniqueProperty):
    def _validate(self, value):
        val = get_mobile(re.sub("[^0-9]", "", value))
        if len(val) < 5:
            raise TypeError('The Phone Number should be at least 5 digits long')

        return val


class MobilePhoneProperty(UniqueProperty):
    def _validate(self, value):
        val = get_mobile(re.sub("[^0-9]", "", value))
        if len(val) < 10:
            raise TypeError('Mobile Phone Number should be at least 10 digits long')

        return val


class Address(ndb.Model):
    address                         = ndb.TextProperty(verbose_name='Address')
    city                            = ndb.StringProperty(verbose_name='City/Town')
    pincode                         = PinCodeProperty(verbose_name='Pin Code')
    latlong                         = ndb.GeoPtProperty()
    state                           = StringProperty(choices=states.keys(), verbose_name='State')
    state_code                      = ndb.ComputedProperty(get_state_code)
    country                         = ndb.StringProperty(default='India', verbose_name='Country')
    phone                           = PhoneProperty(verbose_name='Phone Number')
    phone2                          = PhoneProperty(verbose_name='Alternate Phone Number')


class Contact(ndb.Model):
    first_name                  = ndb.StringProperty()
    last_name                   = ndb.StringProperty()
    email                       = EmailProperty()
    phone                       = PhoneProperty()
    address                     = ndb.TextProperty()
    city                        = ndb.StringProperty()
    pincode                     = PinCodeProperty()
    state                       = ndb.StringProperty()
    country                     = ndb.StringProperty()


class BankAccountDetails(ndb.Model):
    holder_name                     = ndb.StringProperty(verbose_name='Account Holder(s)')
    bank_name                       = ndb.StringProperty(verbose_name='Bank Name')
    branch_name                     = ndb.StringProperty(verbose_name='Branch Name')
    ifsc_code                       = ndb.StringProperty(verbose_name='IFSC Code')
    account_number                  = ndb.StringProperty(verbose_name='Account Number')


class APICredentials(ndb.Model):
    callback_secret                    = ndb.StringProperty(verbose_name='')
    hmac_secret                        = ndb.StringProperty(verbose_name='')
    api_secrets                        = ndb.StringProperty(verbose_name='', repeated=True)
    callback_url                       = ndb.StringProperty(verbose_name='')


class PriceProperty(ndb.Model):
    kind                            = ndb.StringProperty(choices=['percentage', 'fixed price'], default='percentage')
    price                           = ndb.FloatProperty(default=0)

    def _amount(self, amount=None):
        if self.kind == 'percentage':
            if not amount:
                return None
            else:
                return amount * self.price / 100

        else:
            return self.price

    def _apply(self, amount=None):
        if self.kind == 'percentage':
            if not amount:
                return None
            else:
                return amount + (amount * self.price / 100)

        else:
            return amount + self.price


def form_name(entity):
    name = ''
    if entity.first_name:
        name += entity.first_name
    if entity.middle_name:
        name += " " + entity.middle_name
    if entity.last_name:
        name += " " + entity.last_name

    return name or entity.raw_name


def iter_model_attr(model, *fields):
    for field in fields:
        if '.' in field:
            sub_fields = field.split('.')
            value = model
            for sub_field in sub_fields:
                value = getattr(value, sub_field)
            yield field, value
        else:
            yield field, getattr(model, field)

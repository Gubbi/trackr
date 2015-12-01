import logging
from random import randrange
from google.appengine.ext import ndb

__author__ = 'vinuth'


class Prng(ndb.Model):
    """
    Key is the sequence ID.
    """
    prime           = ndb.IntegerProperty(default=99973259)
    current_num     = ndb.IntegerProperty(default=99973257)
    count           = ndb.IntegerProperty(default=0)

    def gen(self):
        logging.info(['Current Num: ', self.current_num, self.count])
        if self.current_num < 2 or self.current_num == (self.prime - 1):
            self.current_num = randrange(3, self.prime - 2)

        if self.current_num <= self.prime / 2:
            self.current_num = (self.current_num ** 2) % self.prime
        else:
            self.current_num = (self.prime - self.current_num ** 2) % self.prime

        self.count += 1
        logging.info(['New Num: ', self.current_num, self.count])

class CancelPrng(Prng):
    """
    Key is the sequence ID, with a Prng as parent.
    """
    prime           = ndb.IntegerProperty(default=999983)
    current_num     = ndb.IntegerProperty(default=999981)


def base32(num, b=32, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return ((num == 0) and numerals[0]) or (base32(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])


@ndb.transactional()
def get_next_prn(key):
    prng = Prng.get_or_insert(key)
    prng.gen()
    prng.put()

    return '{s:{c}>{n}}'.format(s=str(base32(prng.current_num)), n=6, c='y')


@ndb.transactional()
def get_cancel_prn(key):
    prng = CancelPrng.get_or_insert(key)
    prng.gen()
    prng.put()

    return '{s:{c}>{n}}'.format(s=str(prng.current_num), n=6, c='0')

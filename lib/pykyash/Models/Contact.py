'''
   KyashMerchantAPILib
 
   This file was automatically generated by APIMATIC BETA v2.0 on 02/08/2015
'''
from pykyash.Models.KyashObject import KyashObject


class Contact(KyashObject):
    schema = {
        'first_name': unicode,
        'last_name': unicode,
        'email': unicode,
        'phone': str,
        'address': unicode,
        'city': str,
        'pincode': int,
        'state': str,
        'country': str,
    }
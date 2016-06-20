from datetime import datetime
from pykyash.KyashService import KyashService
from pykyash.Models.Cancel import Cancel
from pykyash.Models.Contact import Contact
from pykyash.Models.Fee import Fee
from pykyash.Models.KyashObject import KyashObject


class KyashCode(KyashObject):
    schema = {
        'id': str,
        'livemode': bool,
        'order_id': str,
        'amount': int,
        'status': str,
        'is_dvp': bool,
        'sms_enabled': bool,
        'created_at': datetime,
        'expires_on': datetime,
        'paid_at': datetime,
        'billing_contact': Contact,
        'shipping_contact': Contact,
        'cancellation_details': Cancel,
        'fee': float,
        'fee_details': [Fee],
    }

    def create(self, credentials=None):
        saved_kyash_code = KyashService.call('/kyashcodes/', self.to_dict(), credentials=credentials)
        self.set_values(**saved_kyash_code)

    @staticmethod
    def get(kyash_code_id):
        kyash_code_data = KyashService.call('/kyashcodes/' + kyash_code_id)
        return KyashCode(**kyash_code_data)

    def cancel(self, reason, refund_amount, charge_paid_by=None):
        data = {'reason': reason, 'refund_amount': refund_amount}
        if charge_paid_by:
            data['charge_paid_by'] = charge_paid_by

        cancel_data = KyashService.call('/kyashcodes/' + self.id + '/cancel', data)
        self.cancellation_details = Cancel(cancel_data)
        self.status = 'cancelled'
        return self.cancellation_details

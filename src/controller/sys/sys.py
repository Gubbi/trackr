import json
import traceback
import logging
import datetime

from google.appengine.api.taskqueue import Task
from google.appengine.ext.ndb.model import Key

import cloudstorage as gcs
from config import config
from config.config import MOBILE_OPERATOR_FILE, RECHARGE_PLANS, NEFT_ACC_FILE
from framework.controllers import methods
from framework.extend import PublicController, redirect, web_auth
from framework.globals import request, context as c, response
from layer_cache import SINGLE_LAYER_IN_APP_MEMORY_CACHE_ONLY, cache_with_key
from lib.forms import validateAndGetFields
from lib.neft import add_transaction
from model.accounts import Account
from model.mobile_api import Operator
from model.neft import SysNeftBeneficiary
from model.oauth import ClientApp
from model.partners import MerchantPartner
from model.transactions import KyashCode, get_kyash_code_by_network_id
from model.users import User, Merchant, Organization, KyashPoint, Agency, get_verified_user_by_email, getLiveMerchants, getActiveKyashPointOrgs
from framework.routes import url_for
from lib.utils import generate_api_key, generate_api_secret
from model.utils import Address
from model.AdminMessage import AdminMessage
from services.payments.payment_gateway import pay_kyash_code_postpaid


class SysController(PublicController):
    def make_admin(self):
        if request.POST:
            try:
                user = User.get_by_id(int(request.params['user_id']))
                if not user:
                    c.errors = {'user_id': 'User does not exist.'}
                    return "Promote"

                if 'admin' not in user.type:
                    user.type.append('admin')
                    user.put()
                    c.success = "User promoted to admin"
                else:
                    c.success = "This user is already admin"
            except:
                c.errors = {'user_id': 'Invalid user id.'}
                return "Promote"

        return "Promote"

    def make_live(self, id):
        org = Organization.get_by_id(int(id))

        if not org:
            logging.info(["SYS: No KyashPoint for this id", id])
            return "No KyashPoint for this id <"+str(id)+">"

        try:
            kyash_point = org.kyash_point.get()
            kyash_point.secure_signup_step = 'Live'
            kyash_point.commission_plan_name = 'Pro'
            kyash_point.put()

        except Exception, e:
            c.error = "Unable to make KyashPoint live."
            logging.info(c.error + str(e))

        return "KyashPoint <"+str(id)+"> is now Live. <a href="+url_for('sys.sys', 'kyashpoint_details')+">Back</a>"



    def _create_agency(self, agency_id, agency_name, agency_email):
        org = Organization.get_or_insert(agency_id)
        if not org.account:
            account = Account.get_or_insert(agency_id)
            account.put()
            org.account = account.key

        org.registered_address = Address()
        org.secure_signup_step = 'Approved'
        org.put()

        user = User.get_or_insert(agency_id)
        user.first_name = agency_name
        user.last_name = 'Admin'
        user.email = agency_email
        user.account_verified = True
        user.type = ['agent', 'admin']
        user.org = org.key
        user.password = web_auth.validatePassword(config.KYASH_ADMIN_PASSWORD, config.KYASH_ADMIN_PASSWORD)
        user.put()

        agency = Agency.get_or_insert(agency_id)
        agency.secure_signup_step = "Live"
        agency.org = org.key
        if not agency.users:
            agency.users = [user.key]
        agency.put()

        org.agency = agency.key
        org.admin = user.key
        org.put()


    def notify(self):
        if request.POST:

            if request.params.get('notification'):
                notified=request.params.get("notification")
                push_notify= AdminMessage.get_or_insert('recharge')
                push_notify.notify_message=notified
                push_notify.put()
            return "Successfully published"
        return "Form"

    def _create_govt_acc(self, account_id, kyash_id):
        kyash_acc = Account.get_by_id(kyash_id)
        account = Account.get_or_insert(account_id, parent=kyash_acc.key)
        account.put()


    def _create_merchant(self, merchant_id, url):
        org = Organization.get_or_insert(merchant_id)
        org.secure_signup_step = 'Approved'
        if not org.account:
            account = Account.get_or_insert(merchant_id)
            account.put()
            org.account = account.key

        org.put()

        merchant = Merchant.get_or_insert(merchant_id)
        merchant.secure_api_key = generate_api_key()
        merchant.secure_api_secret = generate_api_secret(merchant.secure_api_key)
        merchant.api_callback = url
        merchant.name = merchant_id.title()
        merchant.secure_signup_step = "Live"
        merchant.org = org.key
        merchant.put()

        org.merchant = merchant.key
        org.put()


    def _create_kyash_point(self, kyash_point_id, create_user=True):
        org = Organization.get_or_insert(kyash_point_id)
        org.registered_address = Address(phone='9243710000')
        if not org.account:
            account = Account.get_or_insert(kyash_point_id)
            account.put()
            org.account = account.key

        org.secure_signup_step = 'Approved'
        org.put()

        if create_user and not org.admin:
                user = User(id=kyash_point_id, first_name='Demo', last_name='KyashPoint', email='demo@bilent.in', account_verified=True, type=['kyash_point'], org=org.key)
                user.password = web_auth.validatePassword(config.DEMO_PASSWORD, config.DEMO_PASSWORD)
        else:
            user = User.get_or_insert(kyash_point_id)
            user.type.append('kyash_point')

        user.put()

        kyash_point = KyashPoint.get_or_insert(kyash_point_id)

        kyash_point.secure_signup_step = "Live"
        kyash_point.org = org.key
        if not kyash_point.users:
            kyash_point.users = [user.key]
        kyash_point.put()

        org.kyash_point = kyash_point.key
        org.admin = user.key
        org.put()

    def _create_Operator(self, operator_id, user_id, password):
        operator = Operator.get_or_insert(operator_id)
        operator_account = Account.get_or_insert(operator_id)
        prepaid_account = Account.get_or_insert('prepaid', parent=operator_account.key)
        operator_account.put()
        prepaid_account.put()
        operator.user_id = user_id
        operator.password = password
        operator.operator_account = operator_account.key
        operator.put()

    def create_client_kyashpoint_app(self):
        kyash_point_app = ClientApp.get_or_insert('Official KyashPoint App')
        kyash_point_app.client_key = config.KYASHPOINT_OFFICIAL_APP_ID
        kyash_point_app.client_secret = config.KYASHPOINT_OFFICIAL_APP_SECRET
        kyash_point_app.put()
        return kyash_point_app.client_key + ":" + kyash_point_app.client_secret

    def setup(self):
        c.actions = []

        try:
            self._create_merchant('Kyash', url_for('api_client.callback', 'handle_account_payment', _full=True, _netloc=config.API_DOMAIN))
            c.actions.append(('Kyash Merchant Creation', 'Success'))

            self._create_merchant('DemoMerchant', url_for('api_client.demo_callback', 'handle_payment', _full=True, _netloc=config.DEMO_DOMAIN))
            c.actions.append(('Demo Merchant Creation', 'Success'))

            self._create_kyash_point('DemoKyashPoint')
            c.actions.append(('Demo KyashPoint Creation', 'Success'))

            self._create_agency('Kyash', 'Kyash', 'info@bilent.in')
            self._create_agency('DemoKyash', 'DemoKyash', 'demokyash@bilent.in')

            kyash_org = Organization.get_by_id('Kyash')
            kyash_org.bank_account = {
                'holder_name': 'Bilent Services Private Limited',
                'bank_name': 'State Bank of India',
                'branch_name': 'Kathriguppe',
                'ifsc_code': 'SBIN0014962',
                'account_number': '33065125329',
            }
            kyash_org.put()

            c.actions.append(('Kyash Agency Creation', 'Success'))
            c.actions.append(('Demo Kyash Agency Creation', 'Success'))

            self._create_govt_acc('Government', 'Kyash')
            c.actions.append(('Government Account Creation', 'Success'))

            self._create_kyash_point('Kyash', create_user=False)
            c.actions.append(('Kyash KyashPoint Creation', 'Success'))

            self._create_Operator('IWT', 'securebilent', 'bilent4u')
            c.actions.append(('IWT Operator Creation', 'Success'))

            self._create_Operator('Jolo', 'sandeep', '')
            c.actions.append(('Jolo Operator Creation', 'Success'))

            self._create_Operator('RedBus', '', '')
            c.actions.append(('RedBus Operator Creation', 'Success'))
        except:
            logging.error(traceback.format_exc())

        return "Done"

    def create_partner(self):
        plan = Key(urlsafe='agtzfmJpbGVudGFwcHIfCxISTWVyY2hhbnRDb21taXNzaW9uGICAgPDqw7gKDA')
        MerchantPartner(id='kartrocket', name='KartRocket', plan_offered=plan, secure_secret=generate_api_secret('KartRocket', 'production')).put()
        return "Done"

    def login(self):
        if request.POST:
            email = request.params.get('email')
            if not email:
                c.error = "Email required"
                return "Form"

            existing_user = get_verified_user_by_email(request.params['email'])
            if not existing_user:
                c.error = 'User either not verified or account not found.'
                return "Form"

            web_auth.set_cookie_for_user(existing_user.email, response)
            redirect(url_for('home', 'dashboard'))

        return "Form"


    def get_neft_upload_file(self):
        kyash_org = Key(Organization, 'Kyash').get()
        logs = []
        for merchant in getLiveMerchants():
            transaction = add_transaction(merchant.org.get(), kyash_org)
            if not transaction:
                continue
            logs.append(transaction)

        # response.headers['Content-Type'] = 'text/plain'
        # response.headers['Content-Disposition'] = 'attachment; filename = neft_log.txt'

        if not logs:
            logging.info('No NEFT Records today')
            return "No Records Added."

        neft_accounts = '\n\n'.join(logs)

        with gcs.open(NEFT_ACC_FILE(), 'w', content_type='text/plain') as f:
            f.write(neft_accounts)

        url = NEFT_ACC_FILE(get_url=True)
        logging.info('NEFT File URL: ' + url)
        SysNeftBeneficiary(file_url=url).put()
        return 'Done'

    def get_neft_download_file(self):
        c.logs = SysNeftBeneficiary.query().fetch(30)
        return 'List'

    def neft_manage(self):
        return 'Dashboard'

    def add_rch_plans(self):
        if request.POST:

            if request.params.get('rch_plans') and request.params.get('circle'):
                rch_plans = request.params.get('rch_plans').strip().replace('\r\n', '')
                circle = request.params.get('circle')
                try:
                    rch_plans_dict = json.loads(rch_plans)
                except Exception, e:
                    c.error = "Unable to load json."
                    logging.info(c.error + str(e))
                    return "Form"
                try:
                    _set_plans_file(circle, rch_plans_dict, bust_cache=True)
                    c.success = "Recharge plans added to file."
                except Exception, e:
                    c.error = "Unable to write file."
                    logging.info(c.error + str(e))
                    return "Form"
            elif request.params.get('mobile_dict'):
                mobile_dict = request.params.get('mobile_dict').strip().replace('\r\n', '')
                try:
                    mobile_dict = json.loads(mobile_dict)
                except Exception, e:
                    c.error = "Unable to load json."
                    logging.info(c.error + str(e))
                    return "Form"

                try:
                    with gcs.open(MOBILE_OPERATOR_FILE, 'w', content_type='application/json', options={'x-goog-acl': 'public-read'}) as f:
                        f.write(str(json.dumps(mobile_dict)))
                    c.success = "Mobile numbers added to file."
                except Exception, e:
                    c.error = "Unable to write file."
                    logging.info(c.error + str(e), exc_info=True)
                    return "Form"
            else:
                c.error = "Failed."

        return "Form"

    def kyashpoint_details(self):
        c.kyash_points = getActiveKyashPointOrgs()
        return "kyashpoint_details"

    def upload_outlets(self):
        if request.POST:
            fields, c.errors = validateAndGetFields(request.params, ('file_key', True), ('network', True), ('type', {'required': True, 'multi': True}),
                                              ('overwrite', {'type': bool}))
            if c.errors:
                return "Form"

            Task(url=url_for('sys.batch.collection_points', 'upload_list'), params=request.params).add('batch')
            c.success = 'Background Task to index outlets list initiated.'

        return 'Form'


    def pay(self):
        if request.POST:
            kyash_code = KyashCode.get_by_id(request.params.get('kyash_code'))
            amount = int(request.params.get('amount'))
            mobile = request.params.get('mobile')
            trans_id = request.params.get('transaction_id')

            if not mobile:
                c.error = "Mobile number required."
                return "Form"

            if not trans_id:
                c.error = "Transaction ID required."
                return "Form"

            if kyash_code.amount != amount:
                c.error = "Amount mismatch"
                return "Form"

            transaction_id = 'KyashDirect' + trans_id

            if kyash_code.network_transaction_id == transaction_id:
                c.success = 'Already marked as paid.'
                return "Form"

            oldKyashCode = get_kyash_code_by_network_id(transaction_id)
            if oldKyashCode:
                c.error = "Duplicate transaction id."
                return "Form"

            if kyash_code.status not in ['created', 'pending']:
                error_string = 'has expired'
                if kyash_code.status in ['paid', 'serviced', 'captured', 'completed', 'confirmed']:
                    error_string = 'is already paid'
                elif kyash_code.status in ['cancelled', 'refunded']:
                    error_string = 'has been cancelled'

                c.error = 'Cannot pay for this Kyash Code as it ' + error_string
                return "Form"

            now = datetime.datetime.utcnow()
            if kyash_code.expires_on and kyash_code.expires_on < now:
                c.error = 'Cannot pay for this Kyash Code as it has expired'
                return "Form"

            try:
                pay_kyash_code_postpaid(kyash_code.key, 'KyashDirect', mobile, 'admin',
                                        transaction_id)
                c.success = "Successfully marked as paid."

            except:
                logging.warn('Error paying for a valid KyashCode', exc_info=True)
                c.error = "Unknown error."

        return "Form"


@cache_with_key("recharge_plans_file", layer=SINGLE_LAYER_IN_APP_MEMORY_CACHE_ONLY)
def _set_plans_file(circle, rch_plans):
    with gcs.open(RECHARGE_PLANS(circle), 'w', content_type='application/json', options={'x-goog-acl': 'public-read'}) as f:
        f.write(str(json.dumps(rch_plans)))

    return rch_plans

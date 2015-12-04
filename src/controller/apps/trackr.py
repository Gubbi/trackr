import datetime
import logging
from boondi.controllers import methods, PayloadData, error
from boondi.ext import render
from boondi.forms import Required, Optional
from boondi.globals import data
from boondi.utils import send_email
from framework.extend import SignedInController
from model.apps.trackr import Cache
from service.apps.push_updates import push_updates_holder, push_updates
from service.apps.trackr import create_or_update_sales_order, get_or_create_customer, get_or_create_agent, \
    create_invoice, get_or_create_supervisor, set_supervisor, create_payment, cancel_payment

__author__ = 'vinuth'


class TrackrController(SignedInController):
    def app_settings(self):
        if self.payload:
            self.validate(required_fields=['brand_name', 'short_code', 'support_number'],
                          error_message='Values cannot be empty')

            self.org_app.brand_name = data.brand_name
            self.org_app.short_code = data.short_code
            self.org_app.support_number = data.support_number
            self.org_app.notification_email = data.notification_email
            self.org_app.spreadsheet_id = data.spreadsheet_id
            self.org_app.put()

            return "Successfully updated settings"

        return {
            'auth': {
                'api_id': self.org.secure_api_id,
                'api_secret': self.org.secure_production.api_secrets[0]
            },
            'app': {
                'brand_name': self.org_app.brand_name,
                'short_code': self.org_app.short_code,
                'support_number': self.org_app.support_number,
                'notification_email': self.org_app.notification_email,
                'spreadsheet_id': self.org_app.spreadsheet_id
            }
        }

    @methods('POST')
    def create_payment(self):
        self.validate({'amount': Required(float)},
                      required_fields=['sales_phone', 'invoice_num'],
                      error_message='Valid Invoice Number and Amount is required')

        cache = Cache.get_by_id(data.sales_phone + data.invoice_num + str(data.amount))
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=24)

        if cache:
            if cache.createdAt > now:
                return error('Same amount for this invoice cannot be collected more than once in a day.')
            else:
                cache.key.delete()

        update = push_updates_holder()

        payment = create_payment(data.invoice_num, data.amount, data.sales_phone, update)

        Cache(id=data.sales_phone + data.invoice_num + str(data.amount)).put()
        push_updates(self.org, self.org_app, update)

        try:
            supervisor = None
            logging.info(payment._agent.supervisors)

            if payment._agent.supervisors:
                supervisor = payment._agent.supervisors[0].get()
                logging.info(supervisor.email)

            mail_body = render('/emails/payment_made.mako', payment=payment)
            if supervisor and supervisor.email:
                send_email(supervisor.email, mail_body, 'New Payment Notification')

            if self.org_app.notification_email:
                send_email(self.org_app.notification_email, mail_body, 'New Payment Notification')
        except:
            logging.warn('Error sending email notifications', exc_info=True)

        return "Payment Created"

    @methods('POST')
    def cancel_payment(self):
        self.validate(required_fields=['sales_phone', 'payment_id'],
                      error_message='Valid Payment ID is required')

        update = push_updates_holder()

        payment = cancel_payment(data.payment_id, data.sales_phone, update)

        push_updates(self.org, self.org_app, update)

        try:
            supervisor = None

            if payment._agent.supervisors:
                supervisor = payment._agent.supervisors[0].get()

            mail_body = render('/emails/payment_cancelled.mako', payment=payment)
            if supervisor and supervisor.email:
                send_email(supervisor.email, mail_body, 'Payment Cancelled')

            if self.org_app.notification_email:
                send_email(self.org_app.notification_email, mail_body, 'Payment Cancelled')
        except:
            logging.warn('Error sending email notifications', exc_info=True)

        return "Payment Cancelled"

    @methods('POST')
    def entry(self):
        self.validate({'amount': Required(float), 'advance': Optional(float)},
                      required_fields=['order_num', 'order_date', 'sales_phone', 'customer_phone', 'business'],
                      error_message='All required details are not present')

        update = push_updates_holder()

        customer = get_or_create_customer(data.business, data.customer_name, data.customer_phone, update)
        incharge = get_or_create_agent(data.sales_name, data.sales_phone, update)

        order = create_or_update_sales_order(data.order_num, data.order_date, data.amount, data.advance,
                                             customer, incharge, update)

        if data.invoice_num and data.invoice_date:
            create_invoice(data.invoice_num, data.invoice_date, order, update)

        push_updates(self.org, self.org_app, update)
        return "Entries Made"

    @methods('POST')
    def new_invoice(self):
        self.validate(required_fields=['invoice_num', 'order_num', 'invoice_date'],
                      error_message='All required details are not present')

        update = push_updates_holder()
        create_invoice(data.invoice_num, data.invoice_date, data.order_num, update)

        push_updates(self.org, self.org_app, update)
        return "Entries Made"

    @methods('POST')
    def update_agent(self):
        agent = PayloadData(self.payload['agent'])
        supervisor = PayloadData(self.payload['supervisor'])

        update = push_updates_holder()

        if not (agent.name and agent.phone):
            return error('Agent name and phone number are required')

        agent_db = get_or_create_agent(agent.name, agent.phone, update)

        if supervisor:
            if supervisor.name and agent.supervisor and supervisor.email:
                supervisor_db = get_or_create_supervisor(supervisor.name, agent.supervisor, supervisor.email, update)
                set_supervisor(agent_db, supervisor_db, update)
            else:
                return error('All supervisor details are required')

        push_updates(self.org, self.org_app, update)
        return "Entries Made"

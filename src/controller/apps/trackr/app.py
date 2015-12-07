import datetime
import logging
from boondi.controllers import methods, PayloadData
from boondi.ext import render, error
from boondi.data import Required, Optional
from boondi.globals import data
from boondi.utils import send_email
from framework.extend import SignedInController
from model.apps.trackr import Cache
from service.apps.push_updates import updates_holder, push_updates
from service.apps.trackr import create_or_update_sales_order, get_or_create_customer, get_or_create_agent, \
    create_invoice, get_or_create_supervisor, set_supervisor, create_payment, cancel_payment

__author__ = 'vinuth'


class AppController(SignedInController):
    @methods('POST')
    def create_payment(self):
        data.validate(amount=Required(float),
                      required_fields=['sales_phone', 'invoice_num'],
                      error_message='Valid Invoice Number and Amount is required')

        cache = Cache.get_by_id(data.sales_phone + data.invoice_num + str(data.amount))
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=24)

        if cache:
            if cache.createdAt > now:
                return error('Same amount for this invoice cannot be collected more than once in a day.')
            else:
                cache.key.delete()

        updates = updates_holder()

        payment = create_payment(data.invoice_num, data.amount, data.sales_phone, updates)

        Cache(id=data.sales_phone + data.invoice_num + str(data.amount)).put()
        push_updates(self.org, self.org_app, updates)

        try:
            supervisor = None
            if payment._agent.supervisors:
                supervisor = payment._agent.supervisors[0].get()

            mail_body = render('/emails/payment_made.mako', payment=payment)
            if supervisor and supervisor.email:
                send_email(supervisor.email, mail_body, 'New Payment Notification')

            if self.org_app.notification_email:
                send_email(self.org_app.notification_email, mail_body, 'New Payment Notification')

        except:
            logging.warn('Error sending email notifications', exc_info=True)

        return {
            "message": "Payment Created",
            'customer_name': payment._customer.contact,
            'customer_phone': payment.by.id(),
            'agent_name': payment._agent.name,
            'payment_id': payment.key.id(),
            'org_brand': self.org_app.brand_name
        }

    @methods('POST')
    def cancel_payment(self):
        data.validate(required_fields=['sales_phone', 'payment_id'],
                      error_message='Valid Payment ID is required')

        updates = updates_holder()

        payment = cancel_payment(data.payment_id, data.sales_phone, updates)

        push_updates(self.org, self.org_app, updates)

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

        return {
            "message": "Payment Cancelled",
            'amount': payment.amount,
            'cancel_id': payment.cancellation_id,
            'invoice_id': payment.invoice.id(),
            'customer_phone': payment.by.id()
        }

    @methods('POST')
    def entry(self):
        data.validate(amount=Required(float), advance=Optional(float),
                      required_fields=['order_num', 'order_date', 'sales_phone', 'customer_phone', 'business'],
                      error_message='All required details are not present')

        update = updates_holder()

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
        data.validate(required_fields=['invoice_num', 'order_num', 'invoice_date'],
                      error_message='All required details are not present')

        update = updates_holder()
        create_invoice(data.invoice_num, data.invoice_date, data.order_num, update)

        push_updates(self.org, self.org_app, update)
        return "Entries Made"

    def settings(self):
        data.define(required_fields=['brand_name', 'short_code', 'support_number'],
                    optional_fields=['notification_email', 'spreadsheet_id', 'script_sheets'])

        logging.info(data.payload)
        if data.payload:
            data.validate()
            data.put(self.org_app)

            return "Successfully updated settings"

        return {
            'auth': {
                'api_id': self.org.secure_api_id,
                'api_secret': self.org.secure_production.api_secrets[0]
            },
            'app': self.org_app.to_dict(include=data.defined_fields),
            'is_script_enabled': self.org_app.is_script_enabled
        }

    @methods('POST')
    def update_agent(self):
        agent = PayloadData(self.payload['agent'])
        supervisor = PayloadData(self.payload['supervisor'])

        update = updates_holder()

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


import datetime
import logging
from boondi.controllers import methods, PayloadData
from boondi.ext import render, error
from boondi.data import Required, Optional
from boondi.globals import data
from boondi.utils import send_email
from framework.extend import SignedInController
from model.apps.trackr import Cache, Agent, Customer, SalesOrder
from service.apps.push_updates import updates_holder, push_updates
from service.apps.trackr import create_or_update_sales_order, get_or_create_customer, get_or_create_agent, \
    create_invoice, get_or_create_supervisor, set_supervisor, create_payment, cancel_payment

__author__ = 'vinuth'


class AppController(SignedInController):
    @methods('POST')
    def create_payment(self):
        data.validate(amount=Required(float),
                      required_fields=['sales_phone', 'invoice_num'],
                      optional_fields=['additional_data'],
                      error_message='Valid Invoice Number and Amount is required')

        cache = Cache.get_by_id(data.sales_phone + data.invoice_num + str(data.amount) + (data.additional_data or ''))
        now = datetime.datetime.utcnow() - datetime.timedelta(hours=24)

        if cache:
            if cache.createdAt > now:
                return error('Same amount for this invoice cannot be collected more than once in a day.')
            else:
                cache.key.delete()

        updates = updates_holder()

        if data.additional_data:
            customer = Customer.get_by_id(data.additional_data)
            if not customer:
                customer = get_or_create_customer('New Business', 'New Customer', data.additional_data, updates)

            incharge = Agent.get_by_id(data.sales_phone)
            if not incharge:
                return error('Payment cannot be created from this phone number.')

            order = SalesOrder.get_by_id(data.invoice_num)
            if order:
                return error('Advance payment can only be entered for new orders.')

            now = datetime.datetime.utcnow() + datetime.timedelta(hours=5.5)
            order = create_or_update_sales_order(data.invoice_num, now.strftime('%d/%m/%Y %I:%M %p'), 0,
                                                 data.amount, customer, incharge, updates, 'Placeholder')

            payment = order.advance.get()

        else:
            payment = create_payment(data.invoice_num, data.amount, data.sales_phone, updates)

        Cache(id=data.sales_phone + data.invoice_num + str(data.amount) + (data.additional_data or '')).put()
        push_updates(self.org, self.org_app, self.livemode, updates)

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
            'org_brand': self.org_app.brand_name,
            'support_number': self.org_app.support_number
        }

    @methods('POST')
    def cancel_payment(self):
        data.validate(required_fields=['sales_phone', 'payment_id'],
                      error_message='Valid Payment ID is required')

        updates = updates_holder()

        payment = cancel_payment(data.payment_id, data.sales_phone, updates)

        push_updates(self.org, self.org_app, self.livemode, updates)

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
            'invoice_id': payment.invoice.id() if payment.invoice else payment.order.id(),
            'customer_phone': payment.by.id(),
            'support_number': self.org_app.support_number
        }

    @methods('POST')
    def entry(self):
        data.validate(amount=Required(float), advance=Optional(float),
                      required_fields=['order_num', 'order_date', 'sales_phone', 'customer_phone', 'business'],
                      optional_fields=['category'],
                      error_message='All required details are not present')

        update = updates_holder()

        customer = get_or_create_customer(data.business, data.customer_name, data.customer_phone, update)
        incharge = get_or_create_agent(data.sales_name, data.sales_phone, update)

        order = create_or_update_sales_order(data.order_num, data.order_date, data.amount, None,
                                             customer, incharge, data.category, update)

        push_updates(self.org, self.org_app, self.livemode, update)

        update = updates_holder()
        if data.invoice_num and data.invoice_date:
            create_invoice(data.invoice_num, data.invoice_date, order, update)

        push_updates(self.org, self.org_app, self.livemode, update)
        return "Entries Made"

    @methods('POST')
    def new_invoice(self):
        data.validate(required_fields=['invoice_num', 'order_num', 'invoice_date'],
                      error_message='All required details are not present')

        update = updates_holder()
        create_invoice(data.invoice_num, data.invoice_date, data.order_num, update)

        push_updates(self.org, self.org_app, self.livemode, update)
        return "Entries Made"

    def settings(self):
        data.define(required_fields=['brand_name', 'short_code', 'support_number'],
                    optional_fields=['notification_email', 'script_sheets'])

        if data.payload:
            data.validate(error_message="Required Data Missing")

            if self.livemode:
                self.org_app.spreadsheet_id = data.spreadsheet_id
            else:
                self.org_app.demo_spreadsheet_id = data.spreadsheet_id

            data.put(self.org_app)
            return "Updated settings"

        app_settings = self.org_app.to_dict(include=data.defined_fields)
        if self.livemode:
            api_secret = self.org.secure_production
            app_settings['spreadsheet_id'] = self.org_app.spreadsheet_id
        else:
            api_secret = self.org.secure_development
            app_settings['spreadsheet_id'] = self.org_app.demo_spreadsheet_id

        return {
            'auth': {
                'api_id': self.org.secure_api_id,
                'api_secret': api_secret.api_secrets[0]
            },
            'app': app_settings,
            'is_script_enabled': self.org_app.is_script_enabled
        }

    @methods('POST')
    def update_agent(self):
        agent = PayloadData(self.payload['agent'])

        update = updates_holder()

        if not (agent.name and agent.phone):
            return error('Agent name and phone number are required')

        agent_db = get_or_create_agent(agent.name, agent.phone, update)

        push_updates(self.org, self.org_app, self.livemode, update)

        update = updates_holder()

        supervisor = PayloadData(self.payload['supervisor']) if self.payload['supervisor'] else None
        logging.info([supervisor, self.payload['supervisor']])

        if supervisor and not agent.supervisor:
            return error('Supervisor phone number is required')

        if supervisor and agent.supervisor:
            if supervisor.name and agent.supervisor and supervisor.email:
                get_or_create_supervisor(supervisor.name, agent.supervisor, supervisor.email, update)
            else:
                return error('All supervisor details are required')

        if agent.supervisor:
            set_supervisor(agent_db, agent.supervisor, update)

        push_updates(self.org, self.org_app, self.livemode, update)
        return "Details Updated"

    @methods('POST')
    def update_customer(self):
        update = updates_holder()

        if not (data.name and data.phone):
            return error('Name and Phone number are required')

        get_or_create_customer(data.name, data.contact, data.phone, update)

        push_updates(self.org, self.org_app, self.livemode, update)
        return "Details Updated"

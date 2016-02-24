import datetime
import logging
from boondi.utils import unix_time
from model.apps.trackr import Customer, Agent, Supervisor, SalesOrder, Payment, Invoice, Deposit
from service.prng import get_next_prn, get_cancel_prn

__author__ = 'vinuth'


stream_path = lambda: 'activities/' + (datetime.datetime.utcnow() + datetime.timedelta(hours=5.5)).strftime('%Y-%m-%d')
customers_path = lambda phone: 'customers/' + str(phone)
agents_path = lambda phone: 'agents/' + str(phone)
supervisors_path = lambda phone: 'supervisors/' + str(phone)
sales_path = lambda num: 'sales/' + str(num)
invoices_path = lambda num: 'invoices/' + str(num)
payments_path = lambda num: 'payments/' + num
deposits_path = lambda num: 'deposits/' + num
ts = lambda: unix_time(datetime.datetime.utcnow())


def get_or_create_customer(name, contact, phone, update):
    try:
        logging.info('Get / Create customer.')
        customer = Customer.get_by_id(phone)

        if customer:
            logging.info('Customer Found')
            customer_modified = False

            if customer.name != name:
                customer.name = name
                customer_modified = True

            if customer.contact != contact:
                customer.contact = contact
                customer_modified = True

            if customer_modified:
                logging.info('Customer Details changed.')
                customer.put()

                tst = ts()
                update['Sheet']['Customers'][phone] = [phone, name, contact]
                update['FBase']['PATCH'][customers_path(phone)] = {'name': name, 'phone': phone, 'contact': contact,
                                                                   '.priority': -1 * tst}

        else:
            logging.info('Creating new customer')
            customer = Customer(id=phone, name=name, contact=contact, phone=phone)
            customer.put()

            tst = ts()
            update['Sheet']['Customers'][phone] = [phone, name, contact]
            update['FBase']['PATCH'][customers_path(phone)] = {'name': name, 'phone': phone, 'contact': contact,
                                                               '.priority': -1 * tst}

            update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_cust_' + str(phone)] = {
                'type': 'customer',
                'ts': {'.sv': 'timestamp'},
                'path': customers_path(phone),
                'key': phone,
                'data': {'name': name},
                '.priority': -1 * tst,
            }

        return customer

    except:
        raise ValueError('Error creating customer')


def get_or_create_agent(name, phone, update):
    try:
        logging.info('Get/Create Agent.')
        agent = Agent.get_by_id(phone)

        if agent:
            logging.info('Agent Found')
            if agent.name != name:
                logging.info('Agent details changed.')
                agent.name = name
                agent.put()

                tst = ts()
                update['Sheet']['Sales Executives'][phone] = [phone, name, None]
                update['FBase']['PATCH'][agents_path(phone)] = {'name': name, 'phone': phone,
                                                                'supervisor': agent.supervisors[0].id() if agent.supervisors and len(agent.supervisors) > 0 else '',
                                                                '.priority': -1 * tst}

        else:
            logging.info('Creating new agent')
            agent = Agent(id=phone, name=name, phone=phone)
            agent.put()

            tst = ts()
            update['Sheet']['Sales Executives'][phone] = [phone, name, None]
            update['FBase']['PATCH'][agents_path(phone)] = {'name': name, 'phone': phone, '.priority': -1 * tst}
            update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_agent_' + str(phone)] = {
                'type': 'agent',
                'ts':  {'.sv': 'timestamp'},
                'path': agents_path(phone),
                'key': phone,
                'data': {'name': name},
                '.priority': -1 * tst,
            }

        return agent

    except TypeError, e:
        raise ValueError('Sales Executive: ' + str(e))

    except:
        logging.info('Error creating sales executive.', exc_info=True)
        raise ValueError('Error creating sales executive')


def get_or_create_supervisor(name, phone, email, update):
    try:
        logging.info('Get/Create new supervisor')
        supervisor = Supervisor.get_by_id(phone)

        if supervisor:
            logging.info('Supervisor found.')
            supervisor_modified = False

            if supervisor.name != name:
                supervisor.name = name
                supervisor_modified = True

            if supervisor.email != email:
                supervisor.email = email
                supervisor_modified = True

            if supervisor_modified:
                logging.info('Supervisor details modified')
                supervisor.put()

                tst = ts()
                update['Sheet']['Supervisors'][phone] = [phone, name, email]
                update['FBase']['PATCH'][supervisors_path(phone)] = {'name': name, 'phone': phone, 'email': email,
                                                                     '.priority': -1 * tst}

        else:
            logging.info('Creating new supervisor')
            supervisor = Supervisor(id=phone, name=name, phone=phone, email=email)
            supervisor.put()

            tst = ts()
            update['Sheet']['Supervisors'][phone] = [phone, name, email]
            update['FBase']['PATCH'][supervisors_path(phone)] = {'name': name, 'phone': phone, 'email': email,
                                                                 '.priority': -1 * tst}
            # update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_spv_' + str(phone)] = {
            #     'type': 'supervisor',
            #     'ts':  {'.sv': 'timestamp'},
            #     'path': supervisors_path(phone),
            #     'key': phone,
            #     'data': {'name': name},
            #     '.priority': -1 * tst,
            # }

        return supervisor

    except:
        raise ValueError('Error creating sales executive')


def set_supervisor(agent, supervisor, update):
    logging.info('Checking if supervisor is to be set for agent')
    if not isinstance(agent, Agent):
        agent = Agent.get_by_id(agent)
        if not agent:
            raise ValueError('Sales personnel not found')

    if not isinstance(supervisor, Supervisor):
        supervisor = Supervisor.get_by_id(supervisor)
        if not supervisor:
            raise ValueError('Supervisor not found')

    if (not agent.supervisors) or agent.supervisors[0] != supervisor.key:
        logging.info('Setting supervisor for agent')
        agent.supervisors = [supervisor.key]
        agent.put()

        update['Sheet']['Sales Executives'][agent.phone] = [agent.phone, agent.name, supervisor.phone]
        update['FBase']['PATCH'][agents_path(agent.phone) + '/supervisor'] = supervisor.phone
    else:
        logging.info('Supervisor already set for agent.')


def create_or_update_sales_order(order_num, order_date, amount, advance, customer, incharge, category, update, order_type=None):
    logging.info('Create / Update Sales Order')

    order = SalesOrder.get_by_id(order_num)
    if order:
        logging.info('Order already exists.')

        if order.invoice:
            raise ValueError('Sales order cannot be modified once invoice is raised.')

        if order.status == 'Cancelled':
            raise ValueError('Cancelled sales order cannot be modified.')

        order_updated = {}
        date_updated = False

        if order.amount != amount:
            order_updated['amount'] = order.amount
            order.amount = amount

        if order.on != order_date:
            order.on = order_date
            date_updated = True

        if (advance and order.advance_amount != advance) or order.customer != customer.key or order.incharge != incharge.key:
            if advance and order.advance and order.advance_amount != advance:
                order_updated['advance'] = order.advance.id()
                cancel_payment(order.advance.get(), order.incharge.get(), update)
                order.advance = None

            if order.customer != customer.key:
                order_updated['customer'] = order.customer.id()
                order.customer = customer.key

            if order.incharge != incharge.key:
                order_updated['agent'] = order.incharge.id()
                order.incharge = incharge.key

            if advance and order.advance_amount != advance:
                advance_payment = create_payment(order, advance, incharge, update)
                order.advance = advance_payment.key
                order.advance_amount = advance

        if order_updated or date_updated:
            logging.info('Modifying order details.')
            order.status = 'Recorded'
            order.put()

            advance_id = order.advance.id() if order.advance else ''

            update['Sheet']['Sales Orders'][order_num] = [order_num, order_date, amount, advance, advance_id,
                                                          customer.name, customer.phone, customer.contact,
                                                          incharge.name, incharge.phone, 'Active']
            tst = ts()
            update['FBase']['PATCH'][sales_path(order_num)] = {
                'on': order_date, 'amount': amount, 'advance': advance, 'advance_id': advance_id,
                'agent': incharge.key.id(), 'customer': customer.key.id(), 'status': 'Recorded', '.priority': -1 * tst
            }

            if order_updated:
                update['FBase']['PATCH']['logs/' + sales_path(order_num) + '/' + str(tst)] = {
                    'type': 'inline',
                    'ts': {'.sv': 'timestamp'},
                    'subtype': 'Modified',
                    'data': order_updated,
                    '.priority': tst,
                }

                update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_order_' + str(order_num)] = {
                    'type': 'sale',
                    'ts': {'.sv': 'timestamp'},
                    'path': sales_path(order_num),
                    'key': order_num,
                    'data': {'type': 'Modified', 'customer_name': customer.name},
                    '.priority': -1 * tst,
                }

    else:
        logging.info('Creating new order.')

        advance_id = ''
        order = SalesOrder(id=order_num, on=order_date, amount=amount, advance_amount=advance,
                           customer=customer.key, incharge=incharge.key, category=category)

        if order_type:
            order.status = order_type

        if advance:
            advance_payment = create_payment(order, advance, incharge, update)
            advance_id = advance_payment.key.id()
            order.advance = advance_payment.key

        order.put()

        tst = ts()
        update['Sheet']['Sales Orders'][order_num] = [
            order_num, order_date, amount, advance, advance_id, customer.name, customer.phone, customer.contact,
            incharge.name, incharge.phone, 'Active'
        ]

        update['FBase']['PATCH'][sales_path(order_num)] = {
            'on': order_date, 'amount': amount, 'advance': advance, 'advance_id': advance_id,
            'agent': incharge.key.id(), 'customer': customer.key.id(), 'status': 'Recorded', '.priority': -1 * tst
        }

        update['FBase']['PATCH']['logs/' + sales_path(order_num) + '/' + str(tst)] = {
            'type': 'inline',
            'ts': {'.sv': 'timestamp'},
            'subtype': 'Created',
            '.priority': tst,
        }

        update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_order_' + str(order_num)] = {
            'type': 'sale',
            'ts': {'.sv': 'timestamp'},
            'path': sales_path(order_num),
            'key': order_num,
            'data': {'type': 'Created', 'customer_name': customer.name, 'amount': amount, 'advance': advance or 0},
            '.priority': -1 * tst,
        }

    return order


def cancel_sales_order(order, update):
    logging.info('Cancelling sales order')

    if not isinstance(order, SalesOrder):
        order = SalesOrder.get_by_id(order)
        if not order:
            raise ValueError('Sales Order not found')

    if order.status == 'Cancelled':
        raise ValueError('Sales order is already cancelled.')

    if order.invoice:
        raise ValueError('Sales order cannot be cancelled once invoice is raised.')

    if order.advance:
        cancel_payment(order.advance.get(), order.incharge.get(), update)

    order.status = "Cancelled"
    order.put()

    tst = ts()
    update['Sheet']['Sales Orders'][order.key.id()] = {'Status': 'Cancelled'}
    update['FBase']['PATCH'][sales_path(order.key.id()) + '/status'] = 'Cancelled'

    update['FBase']['PATCH']['logs/' + sales_path(order.key.id()) + '/' + str(tst)] = {
        'type': 'inline',
        'ts': {'.sv': 'timestamp'},
        'subtype': 'Cancelled',
        '.priority': tst,
    }

    update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_order_' + order.key.id()] = {
        'type': 'sale',
        'ts': {'.sv': 'timestamp'},
        'path': sales_path(order.key.id()),
        'key': order.key.id(),
        'data': {'type': 'Cancelled', 'customer_name': order.customer.get().name, 'amount': order.amount},
        '.priority': -1 * tst,
    }


def delete_placeholder_order(order, update):
    logging.info('Deleting placeholder sales order')

    if not isinstance(order, SalesOrder):
        order = SalesOrder.get_by_id(order)
        if not order:
            raise ValueError('Sales Order not found')

    if order.status != 'Placeholder':
        raise ValueError('Can delete only Placeholder orders.')

    if order.invoice:
        raise ValueError('Sales order cannot be cancelled once invoice is raised.')

    order.key.delete()

    tst = ts()
    update['Sheet']['Sales Orders'][order.key.id()] = {'Status': 'Deleted'}
    update['FBase']['PATCH'][sales_path(order.key.id())] = {}

    update['FBase']['PATCH']['logs/' + sales_path(order.key.id()) + '/' + str(tst)] = {
        'type': 'inline',
        'ts': {'.sv': 'timestamp'},
        'subtype': 'Deleted',
        '.priority': tst,
    }


def set_invoice_on_order(order, invoice, update):
    logging.info('Setting Invoice number in the order record')

    order.invoice = invoice.key
    order.put()

    tst = ts()
    update['Sheet']['Sales Orders'][order.key.id()] = {'Invoice': invoice.key.id()}
    update['FBase']['PATCH'][sales_path(order.key.id()) + '/invoice'] = invoice.key.id()

    update['FBase']['PATCH']['logs/' + sales_path(order.key.id()) + '/' + str(tst)] = {
        'type': 'invoice',
        'ts': {'.sv': 'timestamp'},
        'path': invoices_path(invoice.key.id()),
        'key': invoice.key.id(),
        'subtype': 'Invoice Created',
        '.priority': tst,
    }


def create_invoice(invoice_num, invoice_date, order, update):
    logging.info('Creating Invoice')

    if not isinstance(order, SalesOrder):
        order = SalesOrder.get_by_id(order)

    if not order:
        raise ValueError('Invalid Order Number')

    invoice = Invoice.get_by_id(invoice_num)
    if invoice:
        raise ValueError('Another invoice with this ID exists')

    invoice = Invoice(id=invoice_num, on=invoice_date, order=order.key, customer=order.customer,
                      category=order.category, amount=order.amount, paid=order.advance_amount,
                      payments=[order.advance] if order.advance else [])
    invoice.put()

    tst = ts()
    advance_id = order.advance.id() if order.advance else ''
    update['Sheet']['Invoices'][invoice_num] = [invoice_num, invoice_date, order.key.id(), invoice.amount,
                                                invoice.paid, advance_id, invoice.paid, 0, invoice.balance,
                                                order.customer.id(), 'Active']

    update['FBase']['PATCH'][invoices_path(invoice_num)] = {
        'on': invoice_date, 'amount': invoice.amount, 'advance': invoice.paid, 'advance_id': advance_id,
        'paid': invoice.paid, 'sale': order.key.id(), 'customer': order.customer.id(), 'status': 'Recorded',
        '.priority': -1 * tst
    }

    update['FBase']['PATCH']['logs/' + invoices_path(invoice_num) + '/' + str(tst)] = {
        'type': 'inline',
        'ts': {'.sv': 'timestamp'},
        'subtype': 'Created',
        '.priority': tst,
    }

    update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_invoice_' + invoice_num] = {
        'type': 'invoice',
        'ts': {'.sv': 'timestamp'},
        'path': invoices_path(invoice_num),
        'key': invoice_num,
        'data': {'type': 'Created', 'customer_name': order.customer.get().name, 'amount': invoice.amount,
                 'paid': invoice.paid},

        '.priority': -1 * tst,
    }

    set_invoice_on_order(order, invoice, update)

    if order.advance:
        set_invoice_on_payment(order.advance.get(), invoice, update)

    return invoice


def set_payment_on_invoice(invoice, payment, update):
    logging.info('Setting payment info in Invoice record.')

    # invoice.paid += payment.amount
    invoice.payments.append(payment.key)
    invoice.put()

    tst = ts()
    invoice_num = invoice.key.id()

    # update['Sheet']['Invoices'][invoice_num] = {'Paid': invoice.paid}
    # update['FBase']['PATCH'][invoices_path(invoice_num) + '/paid'] = invoice.paid

    update['FBase']['PATCH']['logs/' + invoices_path(invoice_num) + '/' + str(tst)] = {
        'type': 'payment',
        'ts': {'.sv': 'timestamp'},
        'path': payments_path(payment.key.id()),
        'key': payment.key.id(),
        'subtype': 'Payment Made',
        'data': {'amount': payment.amount},
        '.priority': tst,
    }


def remove_payment_on_invoice(invoice, payment, update):
    logging.info('Removing payment info from invoice record.')

    # invoice.paid -= payment.amount
    # invoice.put()

    tst = ts()
    invoice_num = invoice.key.id()

    # update['Sheet']['Invoices'][invoice_num] = {'Paid': invoice.paid}
    # update['FBase']['PATCH'][invoices_path(invoice_num) + '/paid'] = invoice.paid

    update['FBase']['PATCH']['logs/' + invoices_path(invoice_num) + '/' + str(tst)] = {
        'type': 'payment',
        'ts': {'.sv': 'timestamp'},
        'path': payments_path(payment.key.id()),
        'key': payment.key.id(),
        'subtype': 'Payment Cancelled',
        'data': {'amount': payment.amount},
        '.priority': tst,
    }


def create_payment(invoice, amount, sales, update):
    logging.info('Creating new payment. Advance? ' + str(bool(isinstance(invoice, SalesOrder))))

    invoice_id = ''
    if not isinstance(invoice, SalesOrder):
        if not isinstance(invoice, Invoice):
            invoice = Invoice.get_by_id(invoice)
            if not invoice:
                raise ValueError('Invalid invoice number')

        invoice_id = invoice.key.id()

        if invoice.balance < amount:
            raise ValueError('Invoice balance is less than amount collected')

    if not isinstance(sales, Agent):
        sales = Agent.get_by_id(sales)
        if not sales:
            raise ValueError('Payment cannot be created from this phone number')

    payment = Payment(id=get_next_prn(), by=invoice.customer, to=sales.key, amount=amount,
                      invoice=invoice.key if invoice_id else None, order=None if invoice_id else invoice.key,
                      is_advance=False if invoice_id else True, category=invoice.category)
    payment.put()

    tst = ts()
    customer = invoice.customer.get()
    payment_id = payment.key.id()

    update['FBase']['PATCH'][payments_path(payment_id)] = {
        'ts': {'.sv': 'timestamp'}, 'amount': payment.amount, 'invoice': invoice_id,
        'by': payment.by.id(), 'to': payment.to.id(), 'status': 'Recorded', '.priority': -1 * tst,
    }

    update['FBase']['PATCH']['logs/' + payments_path(payment_id) + '/' + str(tst)] = {
        'type': 'inline',
        'ts': {'.sv': 'timestamp'},
        'subtype': 'Created',
        '.priority': tst,
    }

    update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_payment_' + payment_id] = {
        'type': 'payment',
        'ts': {'.sv': 'timestamp'},
        'path': payments_path(payment_id),
        'key': payment_id,
        'data': {'type': 'Created', 'customer_name': customer.name, 'amount': payment.amount,
                 'agent_name': sales.name, 'is_advance': payment.is_advance},
        '.priority': -1 * tst,
    }

    update['Sheet']['Payments'][payment_id] = [payment_id, payment.amount, invoice.key.id(), sales.phone,
                                               sales.name, customer.phone, customer.name,
                                               'Paid' if invoice_id else 'Advance', '', payment.category]

    if invoice_id:
        set_payment_on_invoice(invoice, payment, update)

    payment._customer = customer
    payment._agent = sales
    payment._invoice = invoice
    return payment


def set_invoice_on_payment(payment, invoice, update):
    logging.info('Setting invoice num on Payment record.')

    payment.invoice = invoice.key
    payment.put()

    tst = ts()
    payment_id = payment.key.id()
    update['FBase']['PATCH'][payments_path(payment_id) + '/invoice'] = invoice.key.id()

    update['FBase']['PATCH']['logs/' + payments_path(payment_id) + '/' + str(tst)] = {
        'type': 'invoice',
        'ts': {'.sv': 'timestamp'},
        'path': invoices_path(invoice.key.id()),
        'key': invoice.key.id(),
        'subtype': 'Invoice Set',
        '.priority': tst
    }


def cancel_payment(payment, sales, update):
    logging.info('Cancelling payment.')

    if not isinstance(payment, Payment):
        payment = Payment.get_by_id(payment)
        if not payment:
            raise ValueError('Invalid payment id')

    now = datetime.datetime.utcnow()
    if payment.createdAt + datetime.timedelta(hours=24) < now:
        raise ValueError('Cannot cancel payment after 24 hours')

    if not isinstance(sales, Agent):
        sales = Agent.get_by_id(sales)
        if not sales:
            raise ValueError('Payment cannot be cancelled from this phone number')

    if payment.to != sales.key:
        raise ValueError('Payment cannot be cancelled from this phone number')

    payment.cancellation_id = get_cancel_prn()
    payment.status = 'Cancelled'
    payment.put()

    tst = ts()
    payment_id = payment.key.id()
    customer = payment.by.get()

    invoice = payment.invoice.get() if payment.invoice else None
    invoice_id = payment.invoice.id() if invoice else ''

    order = payment.order.get() if payment.order else None
    order_id = payment.order.id() if order else ''

    update['FBase']['PATCH'][payments_path(payment_id) + '/status'] = 'Cancelled'

    update['FBase']['PATCH']['logs/' + payments_path(payment_id) + '/' + str(tst)] = {
        'type': 'inline',
        'ts': {'.sv': 'timestamp'},
        'subtype': 'Cancelled',
        '.priority': tst,
    }

    update['FBase']['PATCH'][stream_path() + '/' + str(tst) + '_payment_' + payment_id] = {
        'type': 'payment',
        'ts': {'.sv': 'timestamp'},
        'path': payments_path(payment_id),
        'key': payment_id,
        'data': {'type': 'Cancelled', 'customer_name': customer.name, 'amount': payment.amount,
                 'agent_name': sales.name},
        '.priority': -1 * tst,
    }

    update['Sheet']['Payments'][payment_id] = [payment_id, payment.amount, invoice_id or order_id, sales.phone,
                                               sales.name, customer.phone, customer.name, 'Cancelled',
                                               payment.cancellation_id, payment.category]

    if invoice_id:
        remove_payment_on_invoice(invoice, payment, update)

    elif order and order.status == 'Placeholder':
        delete_placeholder_order(order, update)

    payment._customer = customer
    payment._agent = sales
    payment._invoice = invoice
    return payment

def create_deposit(transaction_id, amount, sales_phone, comments, payment_ids):
    deposit = Deposit.get_by_id(transaction_id)
    if deposit:
        raise ValueError('A deposit with this id already exists')

    sales = Agent.get_by_id(sales_phone)
    if not sales:
        raise ValueError('The given sales personnel does not exist')

    payments = []
    net_amount = 0
    for payment in (Payment.get_by_id(payment_id) for payment_id in payment_ids):
        if not payment:
            raise ValueError('Invalid payment id')

        if payment.is_deposited:
            raise ValueError('Deposited payments cannot be deposited again')

        if payment.status == 'Cancelled':
            raise ValueError('Cancelled payments cannot be deposited')

        if payment.to != sales.key:
            raise ValueError('This payment was not collected by the mentioned sales personnel')

        payments.append(payment.key)
        net_amount += payment.amount

    if not payments:
        net_amount = amount

    deposit = Deposit(id=transaction_id, amount=net_amount, comment=comments, by=sales.key, payments=payments)
    deposit.put()


# ToDo:
# **. SalesOrder Updates?
# 01. Calling these via controllers.
# 02. Calling these via the view layer.
# 03. Writing changes to firebase.
# 04. Sending sms.
# 05. Sending emails.
# 06. Add company id to receiving sms template.
# 07. Change sending sms template.
# 08. Accounts.
# 09. Activity stream.
# 10. Proper error messages.
# 11. Toast error messages in view.
# 12. In general view error messages.

# Updates, Logs & Activity Stream:
# Sales Order: No accounts impact.
# Invoice: Update Customer Account. Check if customer accounting is enabled. Payable slot.
# Customer slots: Advances Paid, Invoice Payables, Cash Paid
# Sales slots: Advances Collected, Cash Collected, Deposits

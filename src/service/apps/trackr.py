import datetime
from model.apps.trackr import Customer, Sales, Supervisor, SalesOrder, Payment, Invoice, Deposit
from service.prng import get_next_prn, get_cancel_prn

__author__ = 'vinuth'


def get_or_create_customer(business, customer, phone):
    try:
        return Customer.get_or_insert(id=phone, name=business, contact=customer, phone=phone)
    except:
        raise ValueError('Error creating customer')


def get_or_create_sales(name, phone):
    try:
        return Sales.get_or_insert(id=phone, name=name, phone=phone)
    except:
        raise ValueError('Error creating sales personnel')


def get_or_create_supervisor(name, phone, email):
    try:
        return Supervisor.get_or_insert(id=phone, name=name, phone=phone, email=email)
    except:
        raise ValueError('Error creating supervisor')


def set_supervisor(sales_phone, supervisor_phone):
    sales = Sales.get_by_id(sales_phone)
    if not sales:
        raise ValueError('Sales personnel not found')

    supervisor = Supervisor.get_by_id(supervisor_phone)
    if not supervisor:
        raise ValueError('Supervisor not found')

    sales.supervisors.append(supervisor.key)


def create_sales_order(org, order_num, order_date, amount, advance, customer, incharge):
    order = SalesOrder.get_by_id(order_num)
    if order:
        raise ValueError('Another sales order with this ID exists')

    advance_payment = Payment(id=get_next_prn(org.key.id()), by=customer.key, to=incharge.key, amount=advance,
                              is_advance=True)
    advance_payment.put()

    order = SalesOrder(id=order_num, on=order_date, amount=amount, advance=advance_payment.key, advance_amount=advance,
                       customer=customer.key, incharge=incharge.key)

    order.put()


def create_invoice(invoice_num, invoice_date, order):
    if not isinstance(order, SalesOrder):
        order = SalesOrder.get_by_id(order)

    if not order:
        raise ValueError('Invalid Order Number')

    invoice = Invoice.get_by_id(invoice_num)
    if invoice:
        raise ValueError('Another invoice with this ID exists')

    invoice = Invoice(id=invoice_num, on=invoice_date, order=order.key, customer=order.customer,
                      amount=order.amount, paid=order.advance_amount)

    invoice.put()

    if order.advance:
        payment = order.advance.get()
        payment.invoice = invoice.key
        payment.put()

    order.invoice = invoice.key
    order.put()


def create_payment(org, invoice_num, amount, sales_phone):
    invoice = Invoice.get_by_id(invoice_num)
    if not invoice:
        raise ValueError('Invalid invoice number')

    if invoice.balance < amount:
        raise ValueError('Invoice balance is less than amount collected')

    sales = Sales.get_by_id(sales_phone)
    if not sales:
        raise ValueError('Payment cannot be created from this phone number')

    payment = Payment(id=get_next_prn(org.key.id()), by=invoice.customer, to=sales.key, amount=amount,
                      invoice=invoice.key)
    payment.put()


def cancel_payment(org, payment_id, sales_phone):
    payment = Payment.get_by_id(payment_id)
    if not payment:
        raise ValueError('Invalid payment id')

    now = datetime.datetime.utcnow()
    if payment.createdAt + datetime.timedelta(hours=24) < now:
        raise ValueError('Cannot cancel payment after 24 hours')

    sales = Sales.get_by_id(sales_phone)
    if not sales:
        raise ValueError('Payment cannot be cancelled from this phone number')

    if payment.to != sales.key:
        raise ValueError('Payment cannot be cancelled from this phone number')

    payment.cancellation_id = get_cancel_prn(org.key.id())
    payment.status = 'Cancelled'
    payment.put()


def create_deposit(transaction_id, amount, sales_phone, comments, payment_ids):
    deposit = Deposit.get_by_id(transaction_id)
    if deposit:
        raise ValueError('A deposit with this id already exists')

    sales = Sales.get_by_id(sales_phone)
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


# ToDO:
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

<h4>${payment.key.id()} - ${'Payment Cancelled' if payment.invoice else 'Advance Cancelled'}</h4>
<br/>
Amount: ${payment.amount}<br/>
Customer Name: ${payment._customer.name}<br/>
Customer Phone: ${payment._customer.phone}<br/>
---- <br/>
Sales Executive: ${payment._agent.name}<br/>
Phone: ${payment._agent.phone}<br/>
Cancellation ID: ${payment.cancellation_id}
<br/>
<br/>
<br/>
Regards,<br/>
Team Trackr.<br/>
<br/>

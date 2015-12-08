/**
 * Created by vinuth on 8/12/15.
 */

function update_payment(sheet_id, payment_id, amount, invoice, agent, agent_name, customer, customer_name, status, cancellation_id) {
  Logger.log('Updating payment info.');

  var ss = SpreadsheetApp.openById(sheet_id);
  Logger.log('Opened Sheet');

  var sheet = ss.getSheetByName('Trackr Payments');

  if(!sheet) {
    sheet = ss.insertSheet('Trackr Payments');
    sheet.appendRow(['Date', 'Payment ID', 'Amount', 'Invoice No', 'Sales Person', 'Sales Person Mobile', 'Customer Name', 'Customer Mobile', 'Status', 'Cancellation ID']);
  }

  Logger.log('Creating row');
  sheet.appendRow([new Date(), payment_id, amount, invoice, agent_name, agent, customer_name, customer, status, cancellation_id]);
}

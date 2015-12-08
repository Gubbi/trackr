/**
 * Created by vinuth on 8/12/15.
 */

var API_ID = 'YOUR API ID HERE';
var API_SECRET = 'YOUR API SECRET HERE';

var INVOICE_NUM = 1, INVOICE_DATE = 2, ORDER_NUM = 3, ORDER_DATE = 4, PAYTYPE = 7, SALES_NAME = 9, SALES_PHONE = 10;
var CUST_NAME = 11, CUST_PHONE = 12, BUSINESS = 13, AMOUNT = 59, ADVANCE = 61, NOTE = 98;

var column_map = {
    INVOICE_NUM: 'invoice_num',
    INVOICE_DATE: 'invoice_date',
    ORDER_NUM: 'order_num',
    ORDER_DATE: 'order_date',
    SALES_NAME: 'sales_name',
    SALES_PHONE: 'sales_phone',
    CUST_NAME: 'customer_name',
    CUST_PHONE: 'customer_phone',
    BUSINESS: 'business',
    AMOUNT: 'amount',
    ADVANCE: 'advance'
};

var TRACKR_URL = 'http://trackr.bilent.in';


function trackrUpdate(e) {
    var sheet = e.source.getActiveSheet();
    if (sheet.getName() !== 'Sales 2015-16') return;

    Logger.log(e.value);
    if (!e.value) return;

    var range = e.range;
    var row = range.getRow();

    var payType = sheet.getRange(row, PAYTYPE).getValue();
    if (!payType) return;
    if (strip(payType.toLowerCase()) !== 'cash') return;

    var noteCell = sheet.getRange(row, NOTE);
    var note = noteCell.getNote();
    Logger.log(note);

    if(strip(noteCell.getValue().toLowerCase()) !== 'track') return;

    var val = getRow(sheet.getRange(row, 1, 1, NOTE).getValues()[0]);
    Logger.log(val);

    if (startsWith(note, 'Error')) {
        noteCell.clearNote();
        note = '';
    }

    if (!note) {
        if (val['order_num'] && val['order_date'] && val['sales_phone'] && val['customer_phone'] && val['business'] && val['amount']) {
            Logger.log('Sending order entry');
            sendRequest('/bkend/entry', val, noteCell);
        }
        else {
            noteCell.clearNote();
            noteCell.setNote('Error: All required details are not present');
            Logger.log('Error: All required details are not present');
        }
    }
    else if (note === 'Trackr: Order Stored') {
        if (val['invoice_num'] && val['invoice_date'] && val['order_num'] && val['sales_phone'] && val['customer_phone'] && val['business'] && val['amount']) {
            Logger.log('Creating new invoice.');
            sendRequest('/bkend/new_invoice', val, noteCell);
        }
        else {
            noteCell.clearNote();
            noteCell.setNote('Error: All required details are not present');
            Logger.log('Error: All required details are not present to create new invoice.');
        }
    }
}

function getRow(raw) {
    var row = {};
    var cols = Object.keys(column_map);

    for (var i = 0; i < cols.length; i++)
        row[column_map[cols[i]]] = "" + strip(raw[cols[i] - 1]);

    return row;
}

function sendRequest(path, val, noteCell) {
    var response = UrlFetchApp.fetch(TRACKR_URL + path, {
        "method": "post",
        "payload": JSON.stringify(val),
        "contentType": "application/json",
        "headers": {
            'Authorization': 'Basic ' + btoa(API_ID + ':' + API_SECRET)
        }
    });

    noteCell.clearNote();
    if(response.getResponseCode() === 200) {
        if (val['invoice_num'] && val['invoice_date']) {
            noteCell.setNote('Trackr: Invoice Stored');
        }
        else {
            noteCell.setNote('Trackr: Order Stored');
        }
    }
    else {
        Logger.log(response.getContentText());
        var error_message = JSON.parse(response.getContentText()).message;
        noteCell.setNote('Error: ' + error_message);
    }
}

function startsWith(string, prefix) {
    return string.slice(0, prefix.length) === prefix;
}

function strip(str) {
    if (typeof str === 'string' || str instanceof String)
        return str.replace(/^\s+|\s+$/g, '');

    return str;
}

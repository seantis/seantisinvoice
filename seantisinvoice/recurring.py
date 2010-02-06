import datetime
import transaction

from sqlalchemy import or_

from seantisinvoice.models import DBSession, next_invoice_number
from seantisinvoice.models import Invoice
from seantisinvoice.models import InvoiceItem

def copy_recurring():
    today = datetime.date.today()
    session = DBSession()
    query = session.query(Invoice)
    query = query.filter(Invoice.recurring_date <= today)
    query = query.filter(or_(Invoice.recurring_stop == None, Invoice.recurring_stop > today))
    for invoice in query.all():
        session = DBSession()
        # Clone invoice and invoice items
        invoice_clone = Invoice()
        invoice_clone.company = invoice.company
        invoice_clone.contact = invoice.contact
        invoice_clone.project_description = invoice.project_description
        invoice_clone.currency = invoice.currency
        invoice_clone.tax = invoice.tax
        session.add(invoice_clone)
        for item in invoice.items:
            item_clone = InvoiceItem()
            item_clone.item_number = item.item_number
            item_clone.amount = item.amount
            item_clone.hours = item.hours
            item_clone.days = item.days
            item_clone.service_description = item.service_description
            item_clone.service_title = item.service_title
            item_clone.invoice = invoice_clone
            session.add(item_clone)
            
        # Get new invoice number
        invoice_clone.invoice_number = next_invoice_number()
        
        # Adjust dates on cloned invoice
        invoice_clone.date = invoice.recurring_date
        invoice_clone.due_date = invoice_clone.date + (invoice.due_date - invoice.date)
        invoice_clone.recurring_date = invoice_clone.date + (invoice.recurring_date - invoice.date)
        invoice_clone.recurring_stop = invoice.recurring_stop
        # Old invoice is not recurring anymore
        invoice.recurring_date = None
    
    transaction.commit()
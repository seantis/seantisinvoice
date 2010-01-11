import datetime

from webob.exc import HTTPFound

import formish
import schemaish
import validatish
from validatish import validator

from sqlalchemy import desc

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import class_mapper

from repoze.bfg.url import route_url
from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice import statusmessage
from seantisinvoice.models import DBSession
from seantisinvoice.models import Customer, CustomerContact, Invoice, InvoiceItem, Company

class AmountOrHours(validator.Validator):
    """
    validatish validator that checks whether at least one of the two fields amount
    and hours has a value filled in.
    """
    def __call__(self, v):
        if v['amount'] is not None or v['hours'] is not None:
            return None
        else:
            msg = "Amount or hours must be set"
            raise validatish.Invalid(msg)


class InvoiceItemSchema(schemaish.Structure):
    
    item_id = schemaish.Integer()
    service_title = schemaish.String(validator=validator.Required())
    service_description = schemaish.String(validator=validator.Required())
    amount = schemaish.Float(description="Enter the amout")
    hours = schemaish.Float(description="Or hours (will be multiplied by your rate)")
    # Additional schema wide validator.
    validator = AmountOrHours()
    
invoice_item_schema = InvoiceItemSchema()

class InvoiceSchema(schemaish.Structure):
    
    customer_contact_id = schemaish.Integer(validator=validator.Required())
    project_description = schemaish.String(validator=validator.Required())
    date = schemaish.Date(validator=validator.Required())
    invoice_number = schemaish.Integer()
    recurring_term = schemaish.Integer()
    recurring_stop = schemaish.Date()
    payment_term = schemaish.Integer(validator=validator.Required())
    currency = schemaish.String(validator=validator.Required())
    tax = schemaish.Float()
    payment_date = schemaish.Date()
    item_list = schemaish.Sequence(invoice_item_schema, validator=validatish.Length(min=1))
    
invoice_schema = InvoiceSchema()

class InvoiceController(object):
    
    def __init__(self, context, request):
        self.request = request
        
    def form_fields(self):
        return invoice_schema.attrs
        
    def form_defaults(self):
        
        session = DBSession()
        company = session.query(Company).first()
        
        defaults = {
            'currency' : 'CHF',
            'payment_term' : '30',
            'tax' : company.tax,
        }
        
        if "invoice" in self.request.matchdict:
            invoice_id = self.request.matchdict['invoice']
            try:
                invoice = session.query(Invoice).filter_by(id=invoice_id).one()
            except NoResultFound:
                return HTTPFound(location = route_url('invoices', self.request))  
            field_names = [ p.key for p in class_mapper(Invoice).iterate_properties ]
            form_fields = [ field[0] for field in invoice_schema.attrs ]
            for field_name in field_names:
                if field_name in form_fields:
                    defaults[field_name] = getattr(invoice, field_name)
            defaults['payment_term'] = (invoice.due_date - invoice.date).days
                    
            # Default values for the item subforms
            defaults['item_list'] = []
            for item in invoice.items:
                item_defaults = {}
                field_names = [ p.key for p in class_mapper(InvoiceItem).iterate_properties ]
                form_fields = [ field[0] for field in invoice_item_schema.attrs ]
                for field_name in field_names:
                    if field_name in form_fields:
                        item_defaults[field_name] = getattr(item, field_name)
                item_defaults['item_id'] = item.id
                defaults['item_list'].append(item_defaults)
        
        return defaults
        
    def form_widgets(self, fields):
        widgets = {}
        widgets['date'] = formish.DateParts(day_first=True)
        widgets['recurring_stop'] = formish.DateParts(day_first=True)
        widgets['payment_date'] = formish.DateParts(day_first=True)
        session = DBSession()
        options = []
        query = session.query(CustomerContact.id, Customer.name, CustomerContact.first_name, CustomerContact.last_name)
        query = query.join(CustomerContact.customer)
        query = query.order_by(Customer.name, CustomerContact.last_name, CustomerContact.first_name)
        for (contact_id, company, first_name, last_name) in query.all():
            options.append((contact_id, '%s: %s %s' % (company, first_name, last_name)))
        widgets['customer_contact_id'] = formish.SelectChoice(options=options)
        widgets['item_list'] = formish.SequenceDefault(min_start_fields=1)
        widgets['item_list.*.item_id'] = formish.Hidden()
        
        return widgets
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main, msgs=statusmessage.messages(self.request))
        
    def _apply_data(self, invoice, converted):
        # Apply schema fields to the customer object
        field_names = [ p.key for p in class_mapper(Invoice).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                setattr(invoice, field_name, converted[field_name])
        invoice.due_date = invoice.date + datetime.timedelta(days=converted['payment_term'])
                
        # Apply data of the items subforms
        session = DBSession()
        item_map = {}
        for item in invoice.items:
            item_map[item.id] = item
        for index, item_data in enumerate(converted['item_list']):
            if item_data['item_id']:
                item_id = item_data['item_id']
                item = item_map[item_id]
                del item_map[item_id]
            else:
                item = InvoiceItem()
                item.invoice = invoice
                session.add(item)
            # Apply schema fields to the customer object
            field_names = [ p.key for p in class_mapper(InvoiceItem).iterate_properties ]
            for field_name in field_names:
                if field_name in item_data.keys():
                    setattr(item, field_name, item_data[field_name])
            item.item_number = index
        # Remove contact items that have been removed in the form
        for item in item_map.values():
            session.delete(item)
        
    def handle_add(self, converted):
        session = DBSession()
        invoice = Invoice()
        invoice.company = session.query(Company).first()
        self._apply_data(invoice, converted)
        session.add(invoice)
        
        # Get and add unique invoice number
        if invoice.invoice_number is None:
            company = session.query(Company).with_lockmode("update").first()
            invoice.invoice_number = company.invoice_start_number
            company.invoice_start_number += 1

        statusmessage.show(self.request, u"Invoice added.", "success")
        
        return HTTPFound(location=route_url('invoices', self.request))
        
    def handle_submit(self, converted):
        invoice_id = self.request.matchdict['invoice']
        session = DBSession()
        invoice = session.query(Invoice).filter_by(id=invoice_id).one()
        self._apply_data(invoice, converted)
        
        # ToDo: We should show this only if there are changes to be saved! 
        statusmessage.show(self.request, u"Changes saved.", "success")
        
        return HTTPFound(location=route_url('invoices', self.request))
        
    def handle_cancel(self):
        statusmessage.show(self.request, u"No changes saved.", "notice")
        return HTTPFound(location=route_url('invoices', self.request))

def view_invoices(request):
    session = DBSession()
    query = session.query(Invoice)
    company = session.query(Company).first()
    
    if 'recurring' in request.params:
        if request.params['recurring'] == '1':
            query = query.filter(Invoice.recurring_term != None)
            title = u'Recurring Invoices'
        elif request.params['recurring'] == '0':
            query = query.filter(Invoice.recurring_term == None)
            title = u'Non-recurring Invoices'
    elif 'due' in request.params and request.params['due'] == '1':
        today = datetime.date.today()
        query = query.filter(Invoice.due_date <= today)
        query = query.filter(Invoice.payment_date == None)
        title = u'Invoices due'
    else:
        title = u'All Invoices'
        
    # Sorting
    if 'sort' in request.params:
        sort_key = request.params['sort']
        if hasattr(Invoice, sort_key):
            sort_attr = getattr(Invoice, sort_key)
            if 'reverse' in request.params:
                sort_attr = desc(sort_attr)
            query = query.order_by(sort_attr)
    else:
        query = query.order_by(desc(Invoice.date))
        
    invoices = query.all()
    main = get_template('templates/master.pt')
    return dict(request=request, main=main, invoices=invoices, company=company, 
                title=title, msgs=statusmessage.messages(request))

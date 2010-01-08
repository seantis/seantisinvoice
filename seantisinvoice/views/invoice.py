from webob.exc import HTTPFound

import formish
import schemaish
from validatish import validator

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import class_mapper

from repoze.bfg.url import route_url
from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice.models import DBSession
from seantisinvoice.models import CustomerContact, Invoice

class InvoiceSchema(schemaish.Structure):
    
    customer_contact_id = schemaish.String(validator=validator.Required())
    project_description = schemaish.String(validator=validator.Required())
    date = schemaish.Date(validator=validator.Required())
    invoice_number = schemaish.Integer(validator=validator.Required())
    recurring_term = schemaish.Integer()
    payment_term = schemaish.Integer(validator=validator.Required())
    currency = schemaish.String(validator=validator.Required())
    
schema = InvoiceSchema()

class InvoiceController(object):
    
    def __init__(self, context, request):
        self.request = request
        
    def form_fields(self):
        return schema.attrs
        
    def form_defaults(self):
        
        defaults = {
            'currency' : 'CHF',
            'payment_term' : '30',
        }
        
        if "invoice" in self.request.matchdict:
            invoice_id = self.request.matchdict['invoice']
            try:
                session = DBSession()
                invoice = session.query(Invoice).filter_by(id=invoice_id).one()
            except NoResultFound:
                return HTTPFound(location = route_url('invoices', self.request))  
            field_names = [ p.key for p in class_mapper(Invoice).iterate_properties ]
            form_fields = [ field[0] for field in self.form_fields() ]
            for field_name in field_names:
                if field_name in form_fields:
                    defaults[field_name] = getattr(invoice, field_name)
        
        return defaults
        
    def form_widgets(self, fields):
        widgets = {}
        widgets['date'] = formish.DateParts(day_first=True)
        session = DBSession()
        options = []
        for contact in session.query(CustomerContact).all():
            options.append((contact.id, '%s: %s %s' % (contact.customer.name, contact.first_name, contact.last_name)))
        widgets['customer_contact_id'] = formish.SelectChoice(options=options)
        
        return widgets
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main)
        
    def _apply_data(self, invoice, converted):
        # Apply schema fields to the customer object
        field_names = [ p.key for p in class_mapper(Invoice).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                setattr(invoice, field_name, converted[field_name])
        
    def handle_add(self, converted):
        invoice = Invoice()
        self._apply_data(invoice, converted)
        session = DBSession()
        session.add(invoice)
        return HTTPFound(location=route_url('invoices', self.request))
        
    def handle_submit(self, converted):
        invoice_id = self.request.matchdict['invoice']
        session = DBSession()
        invoice = session.query(Invoice).filter_by(id=invoice_id).one()
        self._apply_data(invoice, converted)
        return HTTPFound(location=route_url('invoices', self.request))
        
    def handle_cancel(self):
        return HTTPFound(location=route_url('invoices', self.request))

def view_invoices(request):
    session = DBSession()
    invoices = session.query(Invoice).all()
    main = get_template('templates/master.pt')
    return dict(request=request, main=main, invoices=invoices)
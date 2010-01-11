from webob.exc import HTTPFound

import schemaish
from validatish import validator

from sqlalchemy.orm.util import class_mapper

from repoze.bfg.url import route_url
from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice import statusmessage
from seantisinvoice.models import DBSession
from seantisinvoice.models import Company

class CompanySchema(schemaish.Structure):
    
    name = schemaish.String(validator=validator.Required())
    address1 = schemaish.String(validator=validator.Required())
    address2 = schemaish.String()
    address3 = schemaish.String()
    postal_code = schemaish.String(validator=validator.Required())
    city = schemaish.String(validator=validator.Required())
    # Todo: prodive a vocabulary with countries including country codes: used in combination with 
    # postal code: CH-6004 Luzern
    country = schemaish.String()
    e_mail = schemaish.String(validator=validator.Required())
    phone = schemaish.String(validator=validator.Required())
    # logo = schemaish.String()
    tax = schemaish.String(validator=validator.Required())
    vat_number = schemaish.String()
    iban = schemaish.String()
    swift = schemaish.String()
    bank_address= schemaish.String()
    invoice_start_number = schemaish.String()
    invoice_template = schemaish.String()
    
company_schema = CompanySchema()

class CompanyController(object):
    
    def __init__(self, context, request):
        self.request = request
        
    def form_fields(self):
        return company_schema.attrs
        
    def form_defaults(self):
        defaults = {}
        session = DBSession()
        company = session.query(Company).first()
        field_names = [ p.key for p in class_mapper(Company).iterate_properties ]
        form_fields = [ field[0] for field in company_schema.attrs ]
        for field_name in field_names:
            if field_name in form_fields:
                defaults[field_name] = getattr(company, field_name)
                    
        return defaults
        
    def form_widgets(self, fields):
        widgets = {}
        
        # we might move the options here into a configuration file or we even let the users upload
        # rml templates TTW!
        options = [('invoice_pdf.pt','German PDF Template'),('invoice_pdf.pt','English PDF Template')]
        
        # FIXME: No clue why the data is not saved when using the widget
        # widgets['invoice_template'] = formish.SelectChoice(options=options)
        
        return widgets
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main, msgs=statusmessage.messages(self.request))
        
    def _apply_data(self, company, converted):
        # Apply schema fields to the company object
        field_names = [ p.key for p in class_mapper(Company).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                setattr(company, field_name, converted[field_name])
                
    def handle_submit(self, converted):
        session = DBSession()
        company = session.query(Company).first()
        self._apply_data(company, converted)
        
        # ToDo: We should show this only if there are changes to be saved!    
        statusmessage.show(self.request, u"Changes saved.", "success")
        
        return HTTPFound(location=route_url('company', self.request))
        
    def handle_cancel(self):        
        statusmessage.show(self.request, u"No changes saved.", "notice")
        return HTTPFound(location=route_url('invoices', self.request))    
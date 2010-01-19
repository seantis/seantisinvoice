from webob.exc import HTTPFound

import formish
import schemaish
from validatish import validator
from formish import filestore

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
    logo = schemaish.File(description=".jpg / 70mm x 11mm / 300dpi")
    hourly_rate = schemaish.Float(validator=validator.Required())
    daily_rate = schemaish.Float(validator=validator.Required())
    tax = schemaish.Float(validator=validator.Required())
    vat_number = schemaish.String()
    iban = schemaish.String()
    swift = schemaish.String()
    bank_address= schemaish.String()
    invoice_start_number = schemaish.Integer()
    invoice_template = schemaish.String(validator=validator.Required())
    
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
        options = [('invoice_pdf.pt','German PDF Template'),('invoice_pdf_en.pt','English PDF Template')]
        widgets['invoice_template'] = formish.SelectChoice(options=options)
        widgets['logo'] = formish.FileUpload(filestore.CachedTempFilestore())
        
        return widgets
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main, msgs=statusmessage.messages(self.request))
        
    def _apply_data(self, company, converted):
        # Apply schema fields to the company object
        changed = False
        field_names = [ p.key for p in class_mapper(Company).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                if getattr(company, field_name) != converted[field_name]:
                    setattr(company, field_name, converted[field_name])
                    changed = True
                    
        # TODO we need a filehandler here!!
        # http://ish.io/embedded/formish/walkthrough.html#file-uploads
        if company.logo != converted['logo'].filename:
            company.logo = 'logo.jpg'
        
        return changed
                
    def handle_submit(self, converted):
        session = DBSession()
        company = session.query(Company).first()
        changed = self._apply_data(company, converted)
        
        if changed:    
            statusmessage.show(self.request, u"Changes saved.", "success")
        else:
            statusmessage.show(self.request, u"No changes saved.", "notice")
        
        return HTTPFound(location=route_url('company', self.request))
        
    def handle_cancel(self):        
        statusmessage.show(self.request, u"No changes saved.", "notice")
        return HTTPFound(location=route_url('invoices', self.request))    
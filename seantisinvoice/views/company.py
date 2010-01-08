from webob.exc import HTTPFound

import formish
import schemaish
from validatish import validator

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import class_mapper

from repoze.bfg.url import route_url
from repoze.bfg.chameleon_zpt import get_template

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
    country = schemaish.String(description="Use official country code (e.g. CH for Switzerland)")
    e_mail = schemaish.String(validator=validator.Required())
    phone = schemaish.String(validator=validator.Required())
    # logo = schemaish.String()
    tax = schemaish.String(validator=validator.Required())
    vat_number = schemaish.String()
    iban = schemaish.String()
    swift = schemaish.String()
    bank_address= schemaish.String()
    invoice_start_number = schemaish.String()
    
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
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main)
        
    def _apply_data(self, company, converted):
        session = DBSession()
        # Apply schema fields to the company object
        field_names = [ p.key for p in class_mapper(Company).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                setattr(company, field_name, converted[field_name])
                
    def handle_submit(self, converted):
        session = DBSession()
        company = session.query(Company).first()
        self._apply_data(company, converted)
        return HTTPFound(location=route_url('company', self.request))
        
    def handle_cancel(self):
        return HTTPFound(location=route_url('invoices', self.request))    
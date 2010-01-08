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
        
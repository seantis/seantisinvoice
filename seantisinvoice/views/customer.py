from webob.exc import HTTPFound

import schemaish
from validatish import validator

from sqlalchemy.orm.util import class_mapper

from repoze.bfg.url import route_url
from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice.models import DBSession
from seantisinvoice.models import Customer

name_field = schemaish.String(
       description=('Company name'),
       validator=validator.Required(),
       )
       
address1_field = schemaish.String(
       description=('Address 1'),
       validator=validator.Required(),
       )

class AddCustomerController(object):
    
    def __init__(self, context, request):
        self.request = request
        
    def form_fields(self):
        fields = [ ('name', name_field),
                   ('address1', address1_field) ]
        return fields
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main)
        
    def handle_add(self, converted):
        
        customer = Customer()
        # Apply schema fields to the flight object
        field_names = [ p.key for p in class_mapper(Customer).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                setattr(customer, field_name, converted[field_name])
        
        session = DBSession()
        session.add(customer)
        return HTTPFound(location=route_url('customers', self.request))
        
    def handle_cancel(self):
        return HTTPFound(location=route_url('customers', self.request))

def view_customers(request):
    session = DBSession()
    customers = session.query(Customer).all()
    main = get_template('templates/master.pt')
    return dict(request=request, main=main, customers=customers)
    
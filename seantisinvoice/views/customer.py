from webob.exc import HTTPFound

import schemaish
from validatish import validator

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import class_mapper

from repoze.bfg.url import route_url
from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice.models import DBSession
from seantisinvoice.models import Customer

class CustomerSchema(schemaish.Structure):

    name = schemaish.String(validator=validator.Required())
    address1 = schemaish.String(validator=validator.Required())
    city = schemaish.String(validator=validator.Required())

class CustomerController(object):
    
    def __init__(self, context, request):
        self.request = request
        
    def form_fields(self):
        return CustomerSchema().attrs
        
    def form_defaults(self):
        
        defaults = {}
        if "customer" in self.request.matchdict:
            customer_id = self.request.matchdict['customer']
            try:
                session = DBSession()
                customer = session.query(Customer).filter_by(id=customer_id).one()
            except NoResultFound:
                return HTTPFound(location = route_url('customers', self.request))  
            field_names = [ p.key for p in class_mapper(Customer).iterate_properties ]
            form_fields = [ field[0] for field in self.form_fields() ]
            for field_name in field_names:
                if field_name in form_fields:
                    defaults[field_name] = getattr(customer, field_name)
        
        return defaults
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main)
        
    def _apply_data(self, customer, converted):
        # Apply schema fields to the customer object
        field_names = [ p.key for p in class_mapper(Customer).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                setattr(customer, field_name, converted[field_name])
        
    def handle_add(self, converted):
        customer = Customer()
        self._apply_data(customer, converted)
        session = DBSession()
        session.add(customer)
        return HTTPFound(location=route_url('customers', self.request))
        
    def handle_submit(self, converted):
        customer_id = self.request.matchdict['customer']
        session = DBSession()
        customer = session.query(Customer).filter_by(id=customer_id).one()
        self._apply_data(customer, converted)
        return HTTPFound(location=route_url('customers', self.request))
        
    def handle_cancel(self):
        return HTTPFound(location=route_url('customers', self.request))

def view_customers(request):
    session = DBSession()
    customers = session.query(Customer).all()
    main = get_template('templates/master.pt')
    return dict(request=request, main=main, customers=customers)
    
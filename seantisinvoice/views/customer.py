from webob.exc import HTTPFound

import formish
import schemaish
import validatish
from validatish import validator

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.util import class_mapper

from repoze.bfg.url import route_url
from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice import statusmessage
from seantisinvoice.models import DBSession
from seantisinvoice.models import Customer, CustomerContact

class CustomerContactSchema(schemaish.Structure):
    
    contact_id = schemaish.Integer()
    first_name = schemaish.String(validator=validator.Required())
    last_name = schemaish.String(validator=validator.Required())
    title = schemaish.String(validator=validator.Required())
    academic_title = schemaish.String()
    e_mail = schemaish.String()
    phone = schemaish.String()

customer_contact_schmema = CustomerContactSchema()

class CustomerSchema(schemaish.Structure):
    name = schemaish.String(validator=validator.Required())
    address1 = schemaish.String(validator=validator.Required())
    address2 = schemaish.String()
    address3 = schemaish.String()
    postal_code = schemaish.String(validator=validator.Required())
    city = schemaish.String(validator=validator.Required())
    country = schemaish.String()
    contact_list = schemaish.Sequence(customer_contact_schmema)
    
customer_schema = CustomerSchema()

class CustomerController(object):
    
    def __init__(self, context, request):
        self.request = request
        
    def form_fields(self):
        return customer_schema.attrs
        
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
            form_fields = [ field[0] for field in customer_schema.attrs ]
            for field_name in field_names:
                if field_name in form_fields:
                    defaults[field_name] = getattr(customer, field_name)
                    
            # Default values for the contact subforms
            defaults['contact_list'] = []
            for contact in customer.contacts:
                contact_defaults = {}
                field_names = [ p.key for p in class_mapper(CustomerContact).iterate_properties ]
                form_fields = [ field[0] for field in customer_contact_schmema.attrs ]
                for field_name in field_names:
                    if field_name in form_fields:
                        contact_defaults[field_name] = getattr(contact, field_name)
                contact_defaults['contact_id'] = contact.id
                defaults['contact_list'].append(contact_defaults)
        
        return defaults
        
    def form_widgets(self, fields):
        widgets = {}
        widgets['contact_list'] = formish.SequenceDefault(min_start_fields=1,sortable=False)
        widgets['contact_list.*.contact_id'] = formish.Hidden()
        return widgets
        
    def __call__(self):
        main = get_template('templates/master.pt')
        return dict(request=self.request, main=main, msgs=statusmessage.messages(self.request))
        
    def _apply_data(self, customer, converted):
        changed = False
        session = DBSession()
        # Apply schema fields to the customer object
        field_names = [ p.key for p in class_mapper(Customer).iterate_properties ]
        for field_name in field_names:
            if field_name in converted.keys():
                if getattr(customer, field_name) != converted[field_name]:
                    setattr(customer, field_name, converted[field_name])
                    changed = True
            
        # Apply data of the contact subforms
        contact_map = {}
        for contact in customer.contacts:
            contact_map[contact.id] = contact
        for contact_data in converted['contact_list']:
            if contact_data['contact_id']:
                contact_id = contact_data['contact_id']
                contact = contact_map[contact_id]
                del contact_map[contact_id]
            else:
                contact = CustomerContact()
                contact.customer = customer
                session.add(contact)
                changed = True
            # Apply schema fields to the customer contact object
            field_names = [ p.key for p in class_mapper(CustomerContact).iterate_properties ]
            for field_name in field_names:
                if field_name in contact_data.keys():
                    if getattr(contact, field_name) != contact_data[field_name]:
                        setattr(contact, field_name, contact_data[field_name])
                        changed = True
        # Remove contact items that have been removed in the form
        for contact in contact_map.values():
            # FIXME: what happens to existing invoices that loose their contact?
            session.delete(contact)
            changed = True
            
        return changed
        
    def handle_add(self, converted):
        customer = Customer()
        self._apply_data(customer, converted)
        session = DBSession()
        session.add(customer)
        
        statusmessage.show(self.request, u"Customer added.", "success")
        
        return HTTPFound(location=route_url('customers', self.request))
        
    def handle_submit(self, converted):
        customer_id = self.request.matchdict['customer']
        session = DBSession()
        customer = session.query(Customer).filter_by(id=customer_id).one()
        changed = self._apply_data(customer, converted)
        
        if changed: 
            statusmessage.show(self.request, u"Changes saved.", "success")
        else:
            statusmessage.show(self.request, u"No changes saved.", "notice")
        
        return HTTPFound(location=route_url('customers', self.request))
        
    def handle_cancel(self):
        statusmessage.show(self.request, u"No changes saved.", "notice")
        return HTTPFound(location=route_url('customers', self.request))

def view_customers(request):
    session = DBSession()
    customers = session.query(Customer).order_by(Customer.name).all()
    main = get_template('templates/master.pt')
    return dict(request=request, main=main, customers=customers, msgs=statusmessage.messages(request))
    
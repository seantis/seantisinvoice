from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Date

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relation, backref

from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    address1 = Column(Unicode)
    address2 = Column(Unicode)
    address3 = Column(Unicode)
    city = Column(Unicode)
    postal_code = Column(String(4))
    country = Column(Unicode)
    e_mail = Column(String)
    phone = Column(String)
    logo = Column(String)
    tax = Column(Float)
    vat_number = Column(String)
    iban = Column(String)
    swift = Column(String)
    bank_address = Column(Unicode)
    invoice_start_number = Column(Integer)

class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    address1 = Column(Unicode)
    address2 = Column(Unicode)
    address3 = Column(Unicode)
    city = Column(Unicode)
    postal_code = Column(String(4))
    country = Column(Unicode)
    
class CustomerContact(Base):
    __tablename__ = 'customer_contact'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customer.id'))
    first_name = Column(Unicode)
    last_name = Column(Unicode)
    title = Column(Unicode)
    academic_title = Column(Unicode)
    e_mail = Column(String)
    phone = Column(String)
    
    customer = relation(Customer, lazy=False, backref=backref('contacts', order_by=id, cascade="delete"))
    
class Invoice(Base):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'))
    customer_contact_id = Column(Integer, ForeignKey('customer_contact.id'))
    invoice_number = Column(Integer, unique=True)
    date = Column(Date)
    payment_term = Column(Integer)
    recurring_term = Column(Integer)
    currency = Column(Unicode)
    project_description = Column(Unicode)
    tax = Column(Float)
    
    company = relation(Company, lazy=False)
    contact = relation(CustomerContact, lazy=False, backref=backref('invoices', order_by=date))
    
    # Calculate values for the invoice
    def number_counter(self):
        # ToDo: add a counter starting with company invoice_start_number but no clue how we handle it when you
        # get new payment slips form your bank you have a new start number!
        pass
    
    def due_date(self):
        return self.date + timedelta(days=self.payment_term)
        
    def sub_total(self):
        items = self.items
        sub_total = 0
        for item in items:
            sub_total += item.total()
        return sub_total
        
    def tax_amount(self):
        if not self.tax:
            return 0
        return self.sub_total() * self.tax / 100.0
        
    def grand_total(self):
        return self.sub_total() + self.tax_amount()

class InvoiceItem(Base):
    __tablename__ = 'invoice_item'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoice.id'))
    item_number = Column(Integer)
    amount = Column(Float)
    hours = Column(Float)
    service_description = Column(Unicode)
    service_title = Column(Unicode)
    
    invoice = relation(Invoice, backref=backref('items', order_by=id, cascade="delete", lazy=False))
    
    def total(self):
        if self.hours:
            return self.hours * 140.0
        return self.amount

def initialize_sql(db_string, echo=False):
    engine = create_engine(db_string, echo=echo)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

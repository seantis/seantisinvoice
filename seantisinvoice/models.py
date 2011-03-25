from decimal import Decimal

import transaction

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Date

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relation, backref

from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension

from repoze.bfg.security import Allow
from repoze.bfg.security import Authenticated

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class RootFactory(object):
    __acl__ = [ (Allow, Authenticated, 'view'), ]
    def __init__(self, environ):
        self.__dict__.update(environ['bfg.routes.matchdict'])

class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    address1 = Column(Unicode(255))
    address2 = Column(Unicode(255))
    address3 = Column(Unicode(255))
    city = Column(Unicode(255))
    postal_code = Column(Unicode(255))
    country = Column(Unicode(255))
    e_mail = Column(Unicode(255))
    phone = Column(Unicode(255))
    hourly_rate = Column(Float)
    daily_rate = Column(Float)
    tax = Column(Float)
    vat_number = Column(Unicode(255))
    iban = Column(Unicode(34))
    swift = Column(Unicode(11))
    bank_address = Column(Unicode(255))
    invoice_start_number = Column(Integer, default=1)
    invoice_template = Column(Unicode(255))

class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    address1 = Column(Unicode(255))
    address2 = Column(Unicode(255))
    address3 = Column(Unicode(255))
    city = Column(Unicode(255))
    postal_code = Column(Unicode(255))
    country = Column(Unicode(255))
    
class CustomerContact(Base):
    __tablename__ = 'customer_contact'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customer.id'))
    first_name = Column(Unicode(255))
    last_name = Column(Unicode(255))
    title = Column(Unicode(255))
    e_mail = Column(Unicode(255))
    phone = Column(Unicode(255))
    
    customer = relation(Customer, backref=backref('contacts', order_by=[last_name, first_name], cascade="delete"))
    
class Invoice(Base):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'))
    customer_contact_id = Column(Integer, ForeignKey('customer_contact.id'))
    invoice_number = Column(Integer, unique=True)
    date = Column(Date)
    due_date = Column(Date)
    payment_date = Column(Date)
    recurring_date = Column(Date)
    recurring_stop = Column(Date)
    currency = Column(Unicode(255))
    project_description = Column(Unicode(255))
    tax = Column(Float)
    
    company = relation(Company)
    contact = relation(CustomerContact, backref=backref('invoices', order_by=date))
        
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
        amount_str = str(self.sub_total() + self.tax_amount())
        amount = Decimal(amount_str)
        rounder = Decimal("0.05")  # precision for rounding
        return amount - amount.remainder_near(rounder)
        

class InvoiceItem(Base):
    __tablename__ = 'invoice_item'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoice.id'))
    item_number = Column(Integer)
    amount = Column(Float)
    hours = Column(Float)
    days = Column(Float)
    service_description = Column(Unicode(255))
    service_title = Column(Unicode(255))
    
    invoice = relation(Invoice, backref=backref('items', order_by=item_number, cascade="delete"))
    
    def total(self):
        if self.hours:
            return self.hours * self.invoice.company.hourly_rate
        if self.days:
            return self.days * self.invoice.company.daily_rate
        return self.amount
        
    def unit(self):
        if self.days:
            return u'PT'
        if self.hours:
            return u'h'
        return u''

def initialize_sql(db_string, echo=False):
    engine = create_engine(db_string, echo=echo)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    session = DBSession()
    if not session.query(Company).first():
        session.add(Company())
        transaction.commit()
        
def next_invoice_number():
    session = DBSession()
    company = session.query(Company).with_lockmode("update").first()
    number = company.invoice_start_number
    while session.query(Invoice).filter(Invoice.invoice_number == number).first():
        number += 1
    company.invoice_start_number = number
    return number - 1

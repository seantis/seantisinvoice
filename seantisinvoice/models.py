from decimal import Decimal

import transaction

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
    hourly_rate = Column(Float)
    daily_rate = Column(Float)
    tax = Column(Float)
    vat_number = Column(String)
    iban = Column(String)
    swift = Column(String)
    bank_address = Column(Unicode)
    invoice_start_number = Column(Integer, default=1)
    invoice_template = Column(String)

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
    
    customer = relation(Customer, lazy=False, backref=backref('contacts', order_by=[last_name, first_name], lazy=False, cascade="delete"))
    
class Invoice(Base):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('company.id'))
    customer_contact_id = Column(Integer, ForeignKey('customer_contact.id'))
    invoice_number = Column(Integer, unique=True)
    date = Column(Date)
    due_date = Column(Date)
    payment_date = Column(Date)
    recurring_term = Column(Integer)
    recurring_stop = Column(Date)
    currency = Column(Unicode)
    project_description = Column(Unicode)
    tax = Column(Float)
    
    company = relation(Company, lazy=False)
    contact = relation(CustomerContact, lazy=False, backref=backref('invoices', order_by=date))
        
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
        
    def unit(self):
        items = self.items
        for item in items:
            if item.days:
                return u'(PT)'
            if item.hours:
                return u'(h)'
        return ''

class InvoiceItem(Base):
    __tablename__ = 'invoice_item'
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoice.id'))
    item_number = Column(Integer)
    amount = Column(Float)
    hours = Column(Float)
    days = Column(Float)
    service_description = Column(Unicode)
    service_title = Column(Unicode)
    
    invoice = relation(Invoice, backref=backref('items', order_by=item_number, cascade="delete", lazy=False))
    
    def total(self):
        session = DBSession()
        company = session.query(Company).first()
        if self.hours:
            return self.hours * company.hourly_rate
        if self.days:
            return self.days * company.daily_rate
        return self.amount

def initialize_sql(db_string, echo=False):
    engine = create_engine(db_string, echo=echo)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    session = DBSession()
    if not session.query(Company).first():
        session.add(Company())
        transaction.commit()

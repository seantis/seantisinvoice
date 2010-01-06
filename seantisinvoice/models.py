
from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import String
from sqlalchemy import Float

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

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
    first_name = Column(Unicode)
    last_name = Column(Unicode)
    title = Column(Unicode)
    academic_title = Column(Unicode)
    e_mail = Column(String)
    phone = Column(String)
    
class Invoice(Base):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True)
    invoice_number = Column(Integer)
    payment_term = Column(Integer)
    recurring_term = Column(Integer)
    currency = Column(Unicode)
    project_description = Column(Unicode)

class InvoiceItem(Base):
    __tablename__ = 'invoice_item'
    id = Column(Integer, primary_key=True)
    amount = Column(Float)
    hours = Column(Float)
    service_description = Column(Unicode)
    tax = Column(Float)
    
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

def initialize_sql(db_string, echo=False):
    engine = create_engine(db_string, echo=echo)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

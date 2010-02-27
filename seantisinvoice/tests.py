import datetime
from decimal import Decimal
import unittest

from repoze.bfg.configuration import Configurator
from repoze.bfg import testing

def _initTestingDB():
    from seantisinvoice.models import initialize_sql
    session = initialize_sql('sqlite://')
    return session
    
class TestRootFactory(unittest.TestCase):
    
    def test_acl(self):
        from seantisinvoice.models import RootFactory
        from repoze.bfg.security import Allow, Authenticated
        environ = {'bfg.routes.matchdict': {}}
        root_factory = RootFactory(environ)
        self.assertEquals([(Allow, Authenticated, 'view')], root_factory.__acl__)
    
class TestInvoiceItem(unittest.TestCase):
    
    def test_total(self):
        from seantisinvoice.models import Company
        from seantisinvoice.models import Invoice
        from seantisinvoice.models import InvoiceItem
        item = InvoiceItem()
        item.amount = 3000.0
        self.assertEquals(3000.0, item.total())
        # Hourly rate is defined on the company
        company = Company()
        company.hourly_rate = 120.0
        invoice = Invoice()
        invoice.company = company
        item = InvoiceItem()
        item.invoice = invoice
        item.hours = 13
        self.assertEquals(1560.0, item.total())
        # Daily rate is also defined on the company
        company.daily_rate = 1300.0
        item = InvoiceItem()
        item.invoice = invoice
        item.days = 2.5
        self.assertEquals(3250.0, item.total())
        
    def test_unit(self):
        from seantisinvoice.models import InvoiceItem
        item = InvoiceItem()
        self.assertEquals(u'', item.unit())
        item.hours = 5.5
        self.assertEquals(u'h', item.unit())
        item.hours = None
        item.days = 12
        self.assertEquals(u'PT', item.unit())

class TestInvoice(unittest.TestCase):
        
    def test_sub_total(self):
        from seantisinvoice.models import Invoice
        from seantisinvoice.models import InvoiceItem
        invoice = Invoice()
        item = InvoiceItem()
        item.amount = 1250.50
        invoice.items.append(item)
        self.assertEquals(1250.5, invoice.sub_total())
        item = InvoiceItem()
        item.amount = 120.0
        invoice.items.append(item)
        self.assertEquals(1370.5, invoice.sub_total())
        
    def test_tax_amount(self):
        from seantisinvoice.models import Invoice
        from seantisinvoice.models import InvoiceItem
        invoice = Invoice()
        self.assertEquals(0, invoice.tax_amount())
        invoice.tax = 7.6
        self.assertEquals(0, invoice.tax_amount())
        item = InvoiceItem()
        item.amount = 100.0
        invoice.items.append(item)
        self.assertEquals(7.6, invoice.tax_amount())
        
    def test_grand_total(self):
        from seantisinvoice.models import Invoice
        from seantisinvoice.models import InvoiceItem
        invoice = Invoice()
        self.assertEquals(0, invoice.grand_total())
        item = InvoiceItem()
        item.amount = 100.0
        invoice.items.append(item)
        self.assertEquals(Decimal('100.00'), invoice.grand_total())
        invoice.tax = 7.6
        self.assertEquals(Decimal('107.60'), invoice.grand_total())
        item = InvoiceItem()
        item.amount = 60.0
        invoice.items.append(item)
        # Value is rounded
        self.assertEquals(Decimal('172.15'), invoice.grand_total())
        invoice.tax = None
        self.assertEquals(Decimal('160.00'), invoice.grand_total())
        
class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.config = Configurator()
        self.config.begin()
        _initTestingDB()

    def tearDown(self):
        from seantisinvoice.models import DBSession
        import transaction
        DBSession.remove()
        transaction.abort()
        self.config.end()
        
class ViewTest(BaseTest):
        
    def _set_company_profile(self):
        from seantisinvoice.models import Company
        from seantisinvoice.models import DBSession
        session = DBSession()
        company = session.query(Company).one()
        company.name = u'Example Inc.'
        company.address1 = u'Main street 1'
        company.postal_code = u'1000'
        company.city = u'Somewhere'
        company.email = u'info@example.com'
        company.phone = u'1233456789'
        company.hourly_rate = 100.0
        company.daily_rate = 1000.0
        company.invoice_template = u'invoice_pdf.pt'
        return company
    
    def _add_customer(self):
        from seantisinvoice.models import Customer
        from seantisinvoice.models import CustomerContact
        from seantisinvoice.models import DBSession
        session = DBSession()
        customer = Customer()
        customer.name = u'Customers Inc.'
        customer.address1 = u'Street'
        customer.postal_code = u'12234'
        customer.city = u'Dublin'
        session.add(customer)
        # Each customer needs at least one contact
        contact = CustomerContact()
        contact.first_name = u'Buck'
        contact.last_name = u'Mulligan'
        contact.title = u'Mr.'
        contact.customer = customer
        session.add(contact)
        session.flush()
        return customer
        
    def _add_invoice(self):
        from seantisinvoice.models import Invoice
        from seantisinvoice.models import InvoiceItem
        from seantisinvoice.models import DBSession
        session = DBSession()
        customer = self._add_customer()
        invoice = Invoice()
        invoice.project_description = u'Project'
        invoice.date = datetime.date.today()
        invoice.due_date = invoice.date + datetime.timedelta(days=30)
        invoice.currency = u'CHF'
        invoice.contact = customer.contacts[0]
        session.add(invoice)
        # Add invoice item to the invoice
        item = InvoiceItem()
        item.item_number = 0
        item.service_title = u'Testing'
        item.service_description = u'A lot of work!'
        item.amount = 1000.0
        item.invoice = invoice
        session.add(item)
        session.flush()
        return invoice
        
class TestValidators(unittest.TestCase):
    
    def test_item_amount(self):
        from seantisinvoice.views.invoice import ItemAmountValidator
        from validatish import Invalid
        validator = ItemAmountValidator()
        values = dict(amount=None, hours=None, days=None)
        self.assertRaises(Invalid, validator, values)
        values = dict(amount=1000, hours=None, days=None)
        validator(values)
        values = dict(amount=None, hours=10, days=None)
        validator(values)
        values = dict(amount=None, hours=None, days=2.5)
        validator(values)
        values = dict(amount=3000.5, hours=7.5, days=None)
        self.assertRaises(Invalid, validator, values)
        values = dict(amount=3000.5, hours=7.5, days=4)
        self.assertRaises(Invalid, validator, values)
        
    def test_file_mimetype(self):
        from seantisinvoice.views.company import FileMimetypeValidator
        from validatish import Invalid
        validator = FileMimetypeValidator('image/jpeg')
        validator(None)
        class DummyFile(object):
            mimetype = None
        value = DummyFile()
        value.mimetype = 'application/pdf'
        self.assertRaises(Invalid, validator, value)
        value.mimetype = 'image/jpeg'
        validator(None)

class TestViews(ViewTest):
    
    def test_view_customers(self):
        from seantisinvoice.views.customer import view_customers
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = view_customers(request)
        self.assertEqual(view['customers'], [])

    def test_view_invoices(self):
        from seantisinvoice.views.invoice import view_invoices
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = view_invoices(request)
        self.assertEqual(view['invoices'], [])
        invoice = self._add_invoice()
        view = view_invoices(request)
        self.assertEqual(view['invoices'], [invoice])
        # Filtering recurring
        invoice2 = self._add_invoice()
        invoice2.recurring_date = datetime.date.today()
        request.params = dict(recurring='1')
        view = view_invoices(request)
        self.assertEqual(view['invoices'], [invoice2])
        request.params = dict(recurring='0')
        view = view_invoices(request)
        self.assertEqual(view['invoices'], [invoice])
        # Filtering due
        invoice.due_date = datetime.date.today() - datetime.timedelta(days=5)
        request.params = dict(due='1')
        view = view_invoices(request)
        self.assertEqual(view['invoices'], [invoice])
        # Sorting
        invoice.date = datetime.date(2010, 1, 18)
        invoice2.date = datetime.date(2010, 1, 2)
        request.params = dict(sort='date')
        view = view_invoices(request)
        self.assertEqual(view['invoices'], [invoice2, invoice])
        request.params = dict(sort='date', reverse='1')
        view = view_invoices(request)
        self.assertEqual(view['invoices'], [invoice, invoice2])
        
    def test_view_invoice_export(self):
        from seantisinvoice.views.invoice_export import view_invoice_pdf
        # Add an invoice
        company = self._set_company_profile()
        invoice = self._add_invoice()
        invoice.company = company
        request = testing.DummyRequest()
        request.matchdict = dict(invoice=str(invoice.id))
        response = view_invoice_pdf(request)
        self.assertEquals('application/pdf', response.content_type)
        # Not existing invoice
        request.matchdict = dict(invoice='10')
        response = view_invoice_pdf(request)
        self.assertEquals(404, response.status_int)
        
    def test_view_login(self):
        from seantisinvoice.views.login import view_login
        request = testing.DummyRequest()
        response = view_login(request)
        self.failUnless('seantis::invoice' in response.app_iter[0])
        request.params = dict(failed='1')
        response = view_login(request)
        self.failUnless('Login failed.' in response.app_iter[0])
        
    def test_view_login_redirect(self):
        from seantisinvoice.views.login import view_login_redirect
        request = testing.DummyRequest()
        response = view_login_redirect(request)
        self.assertEquals(302, response.status_int)
        self.assertEquals(request.application_url + '/login?failed=1', response.location)
        # Register permissive security policy which allows all access
        testing.registerDummySecurityPolicy('admin')
        response = view_login_redirect(request)
        self.assertEquals(302, response.status_int)
        self.assertEquals(request.application_url, response.location)
        
    def test_license(self):
        from seantisinvoice.views.license import view_license
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        response = view_license(request)
        self.failUnless('main' in response)
        
class TestCompanyController(ViewTest):
    
    def test_handle_submit(self):
        from seantisinvoice.views.company import CompanyController
        from seantisinvoice import statusmessage
        # Register route for redirect in company form actions
        testing.registerRoute('/company', 'company', factory=None)
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = CompanyController(None, request)
        # All defaults must initially be empty
        default_values = view.form_defaults()
        self.assertEquals(None, default_values['name'])
        # Set all required fields
        self._set_company_profile()
        # Defaults must be set
        default_values = view.form_defaults()
        self.assertEquals(u'Example Inc.', default_values['name'])
        # Change company name through the form
        view.handle_submit(dict(name=u'Seantis GmbH'))
        default_values = view.form_defaults()
        self.assertEquals(u'Seantis GmbH', default_values['name'])
        # Check status message
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u"Changes saved.", msgs[0].msg)
        # Submit without changing anything
        view.handle_submit(default_values)
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u"No changes saved.", msgs[0].msg)
        # Logo upload
        from os.path import join, dirname
        from schemaish.type import File
        logo_path = join(dirname(__file__), 'views', 'templates', 'static', 'uploads', 'test_logo.jpg')
        default_values['logo'] = File(open(logo_path, 'rb'), 'logo.jpg', 'image/jpeg')
        view.handle_submit(default_values)
        
    def test_handle_cancel(self):
        from seantisinvoice.views.company import CompanyController
        from seantisinvoice import statusmessage
        # Register route for redirect in company form actions
        testing.registerRoute('/', 'invoices', factory=None)
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = CompanyController(None, request)
        view.handle_cancel()
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u"No changes saved.", msgs[0].msg)
        
    def test_form_fields(self):
        from seantisinvoice.views.company import CompanyController
        from seantisinvoice.views.company import CompanySchema
        request = testing.DummyRequest()
        view = CompanyController(None, request)
        fields = view.form_fields()
        self.assertEquals(CompanySchema.attrs, fields)
        
    def test_form_widgets(self):
        from seantisinvoice.views.company import CompanyController
        request = testing.DummyRequest()
        view = CompanyController(None, request)
        widgets = view.form_widgets(view.form_fields())
        self.assertEquals(2, len(widgets['invoice_template'].options))
        
    def test_call(self):
        from seantisinvoice.views.company import CompanyController
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = CompanyController(None, request)
        result = view()
        self.failUnless('main' in result.keys())
        self.failUnless('msgs' in result.keys())
        
class TestCustomerController(ViewTest):
    
    def test_handle_add(self):
        from seantisinvoice.models import Customer
        from seantisinvoice.models import DBSession
        from seantisinvoice.views.customer import CustomerController
        # Register route for redirect in customer form actions
        testing.registerRoute('/customers', 'customers', factory=None)
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = CustomerController(None, request)
        # Add a new customer
        data = dict(name=u'Customers Inc.', address1=u'Street', 
                    postal_code=u'12234', city=u'Dublin')
        data['contact_list'] = [dict(first_name=u'Buck', last_name=u'Mulligan', title=u'Mr.', contact_id='')]
        view.handle_add(data)
        session = DBSession()
        customer = session.query(Customer).one()
        self.assertEquals(u'Customers Inc.', customer.name)
        self.assertEquals(u'Buck', customer.contacts[0].first_name)
        
    def test_handle_submit(self):
        from seantisinvoice.views.customer import CustomerController
        from seantisinvoice import statusmessage
        # Register route for redirect in customer form actions
        testing.registerRoute('/customers', 'customers', factory=None)
        # Add a customer
        customer = self._add_customer()
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        request.matchdict = dict(customer=str(customer.id))
        view = CustomerController(None, request)
        # Check default values
        default_values = view.form_defaults()
        self.assertEquals(u'Customers Inc.', default_values['name'])
        # Change the data
        default_values['name'] = u'Seantis GmbH'
        default_values['contact_list'][0]['first_name'] = u'Leopold'
        view.handle_submit(default_values)
        default_values = view.form_defaults()
        self.assertEquals(u'Seantis GmbH', default_values['name'])
        self.assertEquals(u'Leopold', default_values['contact_list'][0]['first_name'])
        # Add an additional contact
        contact_date = dict(first_name=u'Stephen', last_name=u'Dedalus', title=u'Mr.', contact_id='')
        default_values['contact_list'].append(contact_date)
        view.handle_submit(default_values)
        default_values = view.form_defaults()
        self.assertEquals(u'Stephen', default_values['contact_list'][1]['first_name'])
        # Remove one of the contacts
        del default_values['contact_list'][0]
        view.handle_submit(default_values)
        default_values = view.form_defaults()
        self.assertEquals(1, len(default_values['contact_list']))
        # Contacts are alphabetically ordered.
        self.assertEquals(u'Stephen', default_values['contact_list'][0]['first_name'])
        # Submit without changing anything
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        request.matchdict = dict(customer=str(customer.id))
        view = CustomerController(None, request)
        view.handle_submit(default_values)
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u"No changes saved.", msgs[0].msg)
        
    def test_form_fields(self):
        from seantisinvoice.views.customer import CustomerController
        from seantisinvoice.views.customer import CustomerSchema
        request = testing.DummyRequest()
        view = CustomerController(None, request)
        fields = view.form_fields()
        self.assertEquals(CustomerSchema.attrs, fields)
        
    def test_form_widgets(self):
        from seantisinvoice.views.customer import CustomerController
        request = testing.DummyRequest()
        view = CustomerController(None, request)
        widgets = view.form_widgets(view.form_fields())
        self.failIf(widgets['contact_list'].sortable)
        
    def test_call(self):
        from seantisinvoice.views.customer import CustomerController
        request = testing.DummyRequest()
        # No customer with this id
        request.matchdict = dict(customer='2')
        view = CustomerController(None, request)
        result = view()
        self.assertEquals(404, result.status_int)
        # Add a customer
        customer = self._add_customer()
        request.matchdict = dict(customer=str(customer.id))
        request.environ['qc.statusmessage'] = []
        view = CustomerController(None, request)
        result = view()
        self.failUnless('main' in result.keys())
        
    def test_handle_cancel(self):
        from seantisinvoice.views.customer import CustomerController
        from seantisinvoice import statusmessage
        # Register route for redirect in customer form actions
        testing.registerRoute('/customers', 'customers', factory=None)
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = CustomerController(None, request)
        view.handle_cancel()
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u"No changes saved.", msgs[0].msg)
        
class TestInvoiceController(ViewTest):
    
    def test_handle_add(self):
        from seantisinvoice.models import Invoice
        from seantisinvoice.models import DBSession
        from seantisinvoice.views.invoice import InvoiceController
        # Register route for redirect in invoice form actions
        testing.registerRoute('/', 'invoices', factory=None)
        # Each invoice belongs to a customer, thus add one.
        customer = self._add_customer()
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = InvoiceController(None, request)
        data = view.form_defaults()
        data['customer_contact_id'] = customer.contacts[0].id
        data['project_description'] = u'Project name'
        data['recurring_term'] = 30
        data['date'] = datetime.date(2010, 1, 18)
        data['item_list'] = [dict(item_id='', service_title=u'Testing', service_description=u'Work', amount=2000.0)]
        view.handle_add(data)
        session = DBSession()
        invoice = session.query(Invoice).one()
        self.assertEquals(u'Project name', invoice.project_description)
        self.assertEquals(customer.contacts[0], invoice.contact)
        self.assertEquals(1, len(invoice.items))
        self.assertEquals(u'Testing', invoice.items[0].service_title)
        
    def test_handle_submit(self):
        from seantisinvoice.views.invoice import InvoiceController
        from seantisinvoice import statusmessage
        # Register route for redirect in invoice form actions
        testing.registerRoute('/', 'invoices', factory=None)
        # Create an invoice
        invoice = self._add_invoice()
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        request.matchdict = dict(invoice=str(invoice.id))
        view = InvoiceController(None, request)
        data = view.form_defaults()
        self.assertEquals(u'Project', data['project_description'])
        # Change some of the invoice date
        data['project_description'] = u'My project'
        data['recurring_term'] = 30
        data['item_list'][0]['service_title'] = u'My service'
        view.handle_submit(data)
        data = view.form_defaults()
        self.assertEquals(u'My project', data['project_description'])
        self.assertEquals(u'My service', data['item_list'][0]['service_title'])
        # Add an additional invoice item
        data['item_list'].append(dict(item_id='', service_title=u'Training', service_description=u'', amount=200.0))
        view.handle_submit(data)
        data = view.form_defaults()
        self.assertEquals(u'Training', data['item_list'][1]['service_title'])
        # Reorder the items
        data['item_list'][0] = view.form_defaults()['item_list'][1]
        data['item_list'][1] = view.form_defaults()['item_list'][0]
        view.handle_submit(data)
        data = view.form_defaults()
        self.assertEquals(u'Training', data['item_list'][0]['service_title'])
        # And remove one of them
        del data['item_list'][0]
        view.handle_submit(data)
        data = view.form_defaults()
        self.assertEquals(1, len(data['item_list']))
        self.assertEquals(u'My service', data['item_list'][0]['service_title'])
        # Submit without changing anything
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        request.matchdict = dict(invoice=str(invoice.id))
        view = InvoiceController(None, request)
        view.handle_submit(data)
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u"No changes saved.", msgs[0].msg)
        
    def test_handle_cancel(self):
        from seantisinvoice.views.invoice import InvoiceController
        from seantisinvoice import statusmessage
        # Register route for redirect in customer form actions
        testing.registerRoute('/', 'invoices', factory=None)
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        view = InvoiceController(None, request)
        view.handle_cancel()
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u"No changes saved.", msgs[0].msg)
        
    def test_form_fields(self):
        from seantisinvoice.views.invoice import InvoiceController
        from seantisinvoice.views.invoice import InvoiceSchema
        request = testing.DummyRequest()
        view = InvoiceController(None, request)
        fields = view.form_fields()
        self.assertEquals(InvoiceSchema.attrs, fields)
        
    def test_form_widgets(self):
        from seantisinvoice.views.invoice import InvoiceController
        customer = self._add_customer()
        contact = customer.contacts[0]
        request = testing.DummyRequest()
        view = InvoiceController(None, request)
        widgets = view.form_widgets(view.form_fields())
        option = (customer.id, u'%s: %s %s' % (customer.name, contact.first_name, contact.last_name))
        self.failUnless(option in widgets['customer_contact_id'].options)
        
    def test_call(self):
        from seantisinvoice.views.invoice import InvoiceController
        request = testing.DummyRequest()
        # No invoice with this id
        request.matchdict = dict(invoice='1')
        view = InvoiceController(None, request)
        result = view()
        self.assertEquals(404, result.status_int)
        # Add an invoice
        invoice = self._add_invoice()
        request.matchdict = dict(invoice=str(invoice.id))
        request.environ['qc.statusmessage'] = []
        view = InvoiceController(None, request)
        result = view()
        self.failUnless('main' in result.keys())
        
class TestUtilities(BaseTest):
    
    def test_statusmessage(self):
        from seantisinvoice import statusmessage
        request = testing.DummyRequest()
        request.environ['qc.statusmessage'] = []
        msgs = statusmessage.messages(request)
        self.assertEquals([], msgs)
        statusmessage.show(request, u'Test message')
        msgs = statusmessage.messages(request)
        self.assertEquals(1, len(msgs))
        self.assertEquals(u'Test message', msgs[0].msg)
        self.assertEquals(u'notice', msgs[0].msg_type)
        # Shown messages are removed
        msgs = statusmessage.messages(request)
        self.assertEquals([], msgs)
        statusmessage.show(request, u'First message')
        statusmessage.show(request, u'Second message', msg_type=u'error')
        msgs = statusmessage.messages(request)
        self.assertEquals(2, len(msgs))
        self.assertEquals(u'Second message', msgs[0].msg)
        self.assertEquals(u'error', msgs[0].msg_type)
        self.assertEquals(u'First message', msgs[1].msg)
        
    def test_formatThousands(self):
        from seantisinvoice.utils import formatThousands
        self.assertEquals('1', formatThousands(1))
        self.assertEquals('1.5', formatThousands(1.5))
        self.assertEquals('12,545', formatThousands(12.545, dSep=','))
        self.assertEquals("12'000", formatThousands(12000))
        self.assertEquals("1'600'000.45", formatThousands(1600000.45))
        self.assertEquals("-1'000", formatThousands(-1000))
        
    def test_recurring(self):
        from seantisinvoice.models import DBSession
        from seantisinvoice.models import Invoice, InvoiceItem
        from seantisinvoice.recurring import copy_recurring
        session = DBSession()
        copy_recurring()
        self.assertEquals(0, session.query(Invoice).count())
        # Add a new invoice
        invoice = Invoice()
        invoice_date = datetime.date.today() - datetime.timedelta(days=100)
        invoice.date = invoice_date
        invoice.due_date = datetime.date.today() - datetime.timedelta(days=70)
        invoice.project_description = u'Invoice project description'
        session.add(invoice)
        # Add an item to the invoice
        item = InvoiceItem()
        item.item_number = 0
        item.amount = 1000
        item.service_description = u'Item description'
        item.service_title = u'Invoice item'
        item.invoice = invoice
        session.merge(item)
        copy_recurring()
        # Invoice not cloned as it has no recurring_date
        self.assertEquals(1, session.query(Invoice).count())
        invoice = session.query(Invoice).one()
        # Set the recurring date on the invoice
        recurring_date = datetime.date.today() - datetime.timedelta(days=70)
        invoice.recurring_date = recurring_date
        copy_recurring()
        # There are now two invoices
        self.assertEquals(2, session.query(Invoice).count())
        invoice = session.query(Invoice).filter_by(date=invoice_date).one()
        # Recurring date of the original invoice has been reset
        self.failIf(invoice.recurring_date)
        cloned_invoice = session.query(Invoice).filter_by(date=recurring_date).one()
        # New invoice has the recurring date of the original one as date
        self.assertEquals(recurring_date, cloned_invoice.date)
        self.assertEquals(recurring_date + datetime.timedelta(days=30), cloned_invoice.recurring_date)
        # Check whether attributes on invoice and invoice item have been cloned
        self.assertEquals(invoice.project_description, cloned_invoice.project_description)
        cloned_item = cloned_invoice.items[0]
        self.assertEquals(item.amount, cloned_item.amount)
        self.assertEquals(item.service_description, cloned_item.service_description)
        self.assertEquals(item.service_title, cloned_item.service_title)


class ViewIntegrationTest(ViewTest):
    
    def setUp(self):
        import seantisinvoice
        self.config = Configurator(package=seantisinvoice)
        self.config.begin()
        self.config.load_zcml('seantisinvoice:configure.zcml')
        _initTestingDB()
        
    def test_zcml_registration(self):
        pass
        
import formish
import schemaish
import validatish
from validatish import validator

from sqlalchemy import desc, and_

from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice import statusmessage
from seantisinvoice.utils import formatThousands
from seantisinvoice.models import DBSession
from seantisinvoice.models import Invoice

class DateRangeValidator(validator.Validator):
    """
    validatish validator that checks whether the from date is before the to date.
    """
    def __call__(self, v):
        if v['from_date'] <= v['to_date']:
            return None
        else:
            msg = "From date must be before to date."
            raise validatish.Invalid(msg)

class ReportsSchema(schemaish.Structure):
    
    from_date = schemaish.Date(validator=validator.Required())
    to_date = schemaish.Date(validator=validator.Required())
    # Additional schema wide validator.
    validator = DateRangeValidator()
    
reports_schema = ReportsSchema()

class ReportsController(object):
    
    def __init__(self, context, request):
        self.request = request
        self.from_date = None
        self.to_date = None
        
    def form_fields(self):
        return reports_schema.attrs
        
    def form_defaults(self):
        self.invoices()
        defaults = {
            'from_date' : self.from_date,
            'to_date' : self.to_date,
        }
        return defaults
        
    def form_widgets(self, fields):
        widgets = {}
        widgets['from_date'] = formish.DateParts(day_first=True)
        widgets['to_date'] = formish.DateParts(day_first=True)
        return widgets
        
    def invoices(self):
        session = DBSession()
        query = session.query(Invoice)
        if self.from_date and self.to_date:
            query = query.filter(and_(Invoice.date >= self.from_date, Invoice.date <= self.to_date))
        query = query.order_by(desc(Invoice.date))
        invoices = query.all()
        if invoices and (self.from_date is None or self.to_date is None):
            self.from_date = invoices[-1].date
            self.to_date = invoices[0].date
        
        return invoices
        
    def __call__(self):            
        
        total_amount = 0
        total_tax = 0
        
        invoices = self.invoices()
        for invoice in invoices:
            total_amount += invoice.grand_total()
            total_tax += invoice.tax_amount()
        
        main = get_template('templates/master.pt')
        return dict(request=self.request,
                    invoices=invoices,
                    main=main,
                    total_amount=total_amount,
                    total_tax=total_tax,
                    from_date=self.from_date,
                    to_date=self.to_date,
                    msgs=statusmessage.messages(self.request),
                    formatThousands=formatThousands)
                    
    def handle_submit(self, converted):
        self.from_date = converted['from_date']
        self.to_date = converted['to_date']
        return self()
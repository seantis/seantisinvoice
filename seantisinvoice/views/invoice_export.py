import os

from z3c.rml.rml2pdf import parseString

from repoze.bfg.chameleon_zpt import render_template

from webob import Response

from seantisinvoice.utils import formatThousands
from seantisinvoice.models import DBSession
from seantisinvoice.models import Invoice, Company

def view_invoice_pdf(request):
    session = DBSession()
    company = session.query(Company).first()
    
    invoice_id = request.matchdict['invoice']
    invoice = session.query(Invoice).filter_by(id=invoice_id).first()
    if not invoice:
        return Response(status=404)
    
    rml_template = 'templates/rml/' + company.invoice_template
        
    # Only jpeg without PIL
    logo_path = os.path.join(os.path.dirname(__file__), 'templates', 'static', 'uploads', 'logo.jpg')
        
    result = render_template(rml_template, invoice=invoice, logo_path=logo_path,
                             formatThousands=formatThousands)
    response = Response(parseString(result.encode('utf-8')).read())
    response.content_type =  "application/pdf"
    return response
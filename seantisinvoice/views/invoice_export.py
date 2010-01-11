from webob.exc import HTTPFound

import os
import tempfile

from z3c.rml.rml2pdf import go

from sqlalchemy.orm.exc import NoResultFound

from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.chameleon_zpt import render_template
from repoze.bfg.chameleon_zpt import get_template

from webob import Response

from seantisinvoice.models import DBSession
from seantisinvoice.models import Customer, Invoice, Company

def view_invoice_pdf(request):
    session = DBSession()
    company = session.query(Company).first()
    
    if "invoice" in request.matchdict:
        invoice_id = request.matchdict['invoice']
        try:
            invoice = session.query(Invoice).filter_by(id=invoice_id).one()
        except NoResultFound:
            return HTTPFound(location = route_url('invoices', request))
    
    if company.invoice_template:
        rml_template = 'templates/rml/' + company.invoice_template
    else:
        rml_template = 'templates/rml/invoice_pdf.pt'
        
    # Only jpeg without PIL
    logo_name = 'seantis_logo.jpg'
    logo_path = os.path.join(os.path.dirname(__file__), 'templates', 'rml', logo_name)
        
    result = render_template(rml_template, invoice=invoice, logo_path=logo_path)
    rmlfile = tempfile.mktemp(suffix=".rml")
    fd = open(rmlfile, "wb")
    fd.write(result.encode('utf-8'))
    fd.close()
    pdffile = tempfile.mktemp(suffix=".pdf")
    go(rmlfile, pdffile)

    fd = open(pdffile, 'r')
    response = Response(fd.read())
    fd.close()
    response.content_type =  "application/pdf"
    return response
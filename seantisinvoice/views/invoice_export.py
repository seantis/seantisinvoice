from webob.exc import HTTPFound

import os
import tempfile

from z3c.rml.rml2pdf import go

from sqlalchemy.orm.exc import NoResultFound

from repoze.bfg.url import route_url
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
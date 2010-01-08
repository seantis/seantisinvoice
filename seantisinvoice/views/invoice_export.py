from webob.exc import HTTPFound

import tempfile

from z3c.rml.rml2pdf import go

from sqlalchemy.orm.exc import NoResultFound

from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.chameleon_zpt import render_template
from repoze.bfg.chameleon_zpt import get_template

from webob import Response

from seantisinvoice.models import DBSession
from seantisinvoice.models import Customer, Invoice

def view_invoice_pdf(request):
    
    if "invoice" in request.matchdict:
        invoice_id = request.matchdict['invoice']
        try:
            session = DBSession()
            invoice = session.query(Invoice).filter_by(id=invoice_id).one()
        except NoResultFound:
            return HTTPFound(location = route_url('invoices', request))
    
    result = render_template('templates/invoice_pdf.pt', invoice=invoice)
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
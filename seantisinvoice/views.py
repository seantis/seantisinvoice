from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.chameleon_zpt import render_template
from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice.models import DBSession


def add_customer(request):
    dbsession = DBSession()
    
    return render_template_to_response('templates/add_customer.pt',
                                       request=request)
                                       
def invoices(request):
    dbsession = DBSession()
    main = get_template('templates/master.pt')

    return render_template_to_response('templates/invoices.pt',
                                       main=main,
                                       request=request)
    

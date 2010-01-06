from repoze.bfg.chameleon_zpt import render_template_to_response

from seantisinvoice.models import DBSession


def add_customer(request):
    dbsession = DBSession()
    
    return render_template_to_response('templates/add_customer.pt',
                                       request=request)
    

from repoze.bfg.chameleon_zpt import get_template

from seantisinvoice import statusmessage

def license(request):
    main = get_template('templates/master.pt')
    return dict(request=request, main=main, msgs=statusmessage.messages(request))
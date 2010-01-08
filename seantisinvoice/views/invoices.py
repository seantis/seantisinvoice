from repoze.bfg.chameleon_zpt import get_template

def view_invoices(request):
    main = get_template('templates/master.pt')
    
    return dict(request=request, main=main)
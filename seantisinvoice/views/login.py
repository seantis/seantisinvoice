from webob.exc import HTTPUnauthorized

from repoze.bfg.chameleon_zpt import render_template_to_response 

def view_login(request):
    return render_template_to_response('templates/login.pt', request=request)
    
def view_logout(request):
    # the Location in the headers tells the form challenger to redirect
    return HTTPUnauthorized(headers=[('Location', request.application_url)])
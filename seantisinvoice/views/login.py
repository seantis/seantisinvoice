from webob.exc import HTTPFound

from repoze.bfg.chameleon_zpt import render_template_to_response 
from repoze.bfg.security import authenticated_userid

def view_login(request):
    if 'failed' in request.params:
        failed = True
    else:
        failed = False
    return render_template_to_response('templates/login.pt', request=request, login_failed=failed)
    
def view_login_redirect(request):
    
    user_id = authenticated_userid(request)
    if user_id:
        return HTTPFound(location = request.application_url)
    else:
        return HTTPFound(location = request.application_url + '/login?failed=1')  
    
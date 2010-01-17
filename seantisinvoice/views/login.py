from repoze.bfg.chameleon_zpt import render_template_to_response 

def view_login(request):
    if 'repoze.who.logins' in request.environ:
        failed = True
    else:
        failed = False
    return render_template_to_response('templates/login.pt', request=request, login_failed=failed)
    
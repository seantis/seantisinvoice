from repoze.who.plugins.friendlyform import FriendlyFormPlugin

# Makes the repoze.who-friendlyform plugin configurable via config file.

def make_plugin(login_form_url, login_handler_path, logout_handler_path,
                rememberer_name, post_login_url=None, post_logout_url=None, 
                login_counter_name=None):
    
    if login_form_url is None:
        raise ValueError(
            'must include login_form_url in configuration')
    if login_handler_path is None:
        raise ValueError(
            'login_handler_path must not be None')
    if logout_handler_path is None:
        raise ValueError(
            'logout_handler_path must not be None')
    if rememberer_name is None:
        raise ValueError(
            'must include rememberer key (name of another IIdentifier plugin)')
    plugin = FriendlyFormPlugin(login_form_url, 
                                login_handler_path, 
                                post_login_url,
                                logout_handler_path, 
                                post_logout_url, 
                                rememberer_name,
                                login_counter_name)
    return plugin
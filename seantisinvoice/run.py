from repoze.bfg.router import make_app

import seantisinvoice
from seantisinvoice.models import RootFactory
from seantisinvoice.models import initialize_sql

def app(global_config, **settings):
    """ This function returns a repoze.bfg.router.Router object.
    
    It is usually called by the PasteDeploy framework during ``paster serve``.
    """
    db_string = settings.get('db_string')
    if db_string is None:
        raise ValueError("No 'db_string' value in application configuration.")
    initialize_sql(db_string)
    return make_app(RootFactory, seantisinvoice, settings=settings)


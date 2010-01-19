import transaction

from repoze.bfg.router import make_app
from repoze.tm import after_end
from repoze.tm import isActive

import seantisinvoice
from seantisinvoice.models import RootFactory
from seantisinvoice.models import DBSession
from seantisinvoice.models import initialize_sql

def handle_teardown(event):
    environ = event.request.environ
    if isActive(environ):
        t = transaction.get()
        after_end.register(DBSession.remove, t)

def app(global_config, **settings):
    """ This function returns a repoze.bfg.router.Router object.
    
    It is usually called by the PasteDeploy framework during ``paster serve``.
    """
    db_string = settings.get('db_string')
    if db_string is None:
        raise ValueError("No 'db_string' value in application configuration.")
    initialize_sql(db_string)
    return make_app(RootFactory, seantisinvoice, settings=settings)


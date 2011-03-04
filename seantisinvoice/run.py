from repoze.bfg.configuration import Configurator

from tgscheduler.scheduler import Scheduler

from seantisinvoice.models import RootFactory
from seantisinvoice.models import initialize_sql

from seantisinvoice.recurring import copy_recurring

def app(global_config, **settings):
    """ This function returns a repoze.bfg.router.Router object.
    
    It is usually called by the PasteDeploy framework during ``paster serve``.
    """
    db_string = settings.get('db_string')
    if db_string is None:
        raise ValueError("No 'db_string' value in application configuration.")
    initialize_sql(db_string)
    
    # Scheduler to copy recurring invoices
    s = Scheduler()
    # Check every 5 minutes for recurring invoices
    s.add_interval_task(copy_recurring, 300)
    s.start_scheduler()
    
    config = Configurator(root_factory=RootFactory, settings=settings)
    config.begin()
    zcml_file = settings.get('configure_zcml', 'configure.zcml')
    config.load_zcml(zcml_file)
    config.end()
    return config.make_wsgi_app()

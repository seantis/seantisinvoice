import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'repoze.bfg<=1.2a11',
    'repoze.bfg.formish',
    'Chameleon<=1.0.8',
    'WebOb<=0.9.8',
    'SQLAlchemy',
    'repoze.tm2',
    'zope.sqlalchemy<=0.6.1',
    'zope.schema<=3.7.1',
    'transaction<=1.1.1',
    'z3c.rml',
    'repoze.who-friendlyform<=1.0.8',
    'qc.statusmessage',
    'TGScheduler',
    'nose<=0.11.1',
    'nosexcover<=1.0.4',
    ]

if sys.version_info[:3] < (2,5,0):
    requires.append('pysqlite')

setup(name='seantisinvoice',
      version='0.1',
      description='seantisinvoice',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg zope',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='seantisinvoice',
      install_requires = requires,
      entry_points = """\
      [paste.app_factory]
      app = seantisinvoice.run:app
      """
      )


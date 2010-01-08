seantisinvoice README

Create and activate virtualenv:

% virtualenv --no-site-packages invoice
% cd invoice
% source bin/activate

Install repoze.bfg:

% easy_install -i http://dist.repoze.org/bfg/1.1/simple repoze.bfg

Install repoze.bfg.formish (not on pypi yet):

% easy_install -i http://dist.repoze.org/karl/1/simple repoze.bfg.formish

Get seantis.invoice:

% svn co https://svn.seantis.ch/code/santisinvoice/trunk seantisinvoice

Install seantis.invoice

% python setup.py develop

Start seantisinvoice:

% paster serve seantisinvoice/seantisinvoice.ini
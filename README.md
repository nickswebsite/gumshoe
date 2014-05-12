Gumshoe
=======

Django based issue tracker.

Installing
==========

To install with pip:

    pip install gumshoe

To install from the source

    python setup.py install

Please note that the setup script requires setuptools.

Currently only django 1.6 is supported, but it might work in Django 1.5.

Standalone mode
===============

You can run Gumshoe in standalone mode or use it as an application in a
larger project.

If you want to run in standalone mode, it is recommended that you run from
a virtual environment.  Most of the dependencies should be installed
automagically by pip.

The default backend is sqlite3.  If you want to use a different one, you'll
have to install support for it.  E.G.:

    pip install mysql-python

To bootstrap the app, switch to where you want the application to 'live' and run:

    gumshoe-init

This will create an initial configuration file that you can edit.  This will be
used as the standard django 'settings' module.

To configure your database settings, open conf/settings.py and add the lines:

    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gumshoe_database_name',
        'USER': 'gumshoe_database_user',
        'PASSWORD': 'gumshoe_database_password',
        'HOST': 'gumshoe_database_host',
        'PORT': 'gumshoe_database_port',
    }

To start the application, you can run:

    gumshoe runserver 0.0.0.0:80

It is recommended that you serve the application through a real web stack like
Apache or Nginx + uWSGI, etc. rather than use the django development server as
would be the case above.

The wsgi module should be:

    gumshoe.standalone.wsgi

Notes
=====

* The home page for this project isn't up yet.

* Issues should be entered via the Github issue tracker at the moment.  I do have a
  tracker using Gumshoe, but it isn't open to the public just yet.

Useful but Undocumented/Incomplete Features
===========================================

* There is an import_bugzilla command that will do a crude migration from a bugzilla
  database.  The database settings should be configured in the conf/settings.py file
  under DATABASES['bugzilla'] = { ... } just like you would for the standard Gumshoe
  database.

  The username mapping apparently doesn't work.  It was incomplete anyway as it could
  only be specified through the command line, so expect usernames to be imported as
  they were in bugzilla, (e.g. emails).  The passwords will be set to the username, so
  some-user@email.com will have a password of 'some-user@email.com'.

  To specify the issue key for each product you can use the -K option with an argument
  of the form 'Project Name=KEY'

#!/bin/bash

export DJANGO_SETTINGS_MODULE=gumshoe.standalone.settings_import

env/.v/bin/python manage.py sqlclear gumshoe | env/.v/bin/python manage.py dbshell
env/.v/bin/python manage.py syncdb --noinput
env/.v/bin/python manage.py import_bugzilla

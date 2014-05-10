#!/bin/bash

export DJANGO_SETTINGS_MODULE=standalone.test_import_settings

env/.v/bin/python manage.py sqlclear gumshoe | env/.v/bin/python manage.py dbshell
env/.v/bin/python manage.py syncdb --noinput
env/.v/bin/python manage.py import_bugzilla -K "RSS Reader - Desktop=RSSDSK" \
                                            -K "NicksCouchDbApi=COUCH" \
                                            -K "NicksWebsite dot NET=NWS"

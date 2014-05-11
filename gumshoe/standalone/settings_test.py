from settings import *

if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default']['NAME'] = 'db.test.sqlite3'

if "bugzilla" in DATABASES:
    del DATABASES['bugzilla']

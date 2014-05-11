"""
Django settings for test_tracker project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

REST_FRAMEWORK = {
    #'PAGINATE_BY': 2
    'DEFAULT_RENDERER_CLASSES': (
        'gumshoe.renderers.CaseConvertingJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ),
    'DEFAULT_PARSER_CLASSES': (
        'gumshoe.renderers.CaseConvertingJSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    "TEST_RENDERER_CLASSES": (
        'gumshoe.renderers.CaseConvertingJSONRenderer',
    ),
    'TEST_PARSER_CLASSES': (
        'gumshoe.renderers.CaseConvertingJSONParser',
    )
}

SOUTH_MIGRATION_MODULES = {
    "gumshoe": "gumshoe.south_migrations",
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'dqp^^2_)vo3nqm@)c9jz*540vu-d%3kczdt@jz&^*ibxhm-c5q'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

LOGIN_URL = "/login/"

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'south',
    'rest_framework',
    'gumshoe',
)
SITE_ID = 0

MIDDLEWARE_CLASSES = (
    'gumshoe.standalone.middleware.ExceptionLoggerMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'gumshoe.standalone.urls'

WSGI_APPLICATION = 'gumshoe.standalone.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

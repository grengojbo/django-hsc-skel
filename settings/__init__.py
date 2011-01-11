#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
from os import path
import os
import sys

PROJECT_ROOT = path.abspath(path.dirname(path.dirname(__file__)))
sys.path.append(path.join(PROJECT_ROOT, 'apps/'))
sys.path.append(path.join(PROJECT_ROOT, 'libs/'))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Dmitri Patrakov', 'traditio@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru-ru'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path.join(PROJECT_ROOT, 'static/')
STATIC_ROOT = MEDIA_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'
STATIC_URL = MEDIA_URL

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'wch%x0jbk@yb1sm%o0sw_o*magvll$9+wob@^o+cp@dmupxyrd'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#    'django.template.loaders.eggs.Loader',
)

#--- Hamlish setup.
from libs.hamlish import HamlishExtension
ASSETS_JINJA2_EXTENSIONS = JINJA2_EXTENSIONS = [HamlishExtension]
HAMLISH_MODE = 'debug' if DEBUG else 'compact'
HAMLISH_DEBUG = DEBUG
HAMLISH_ENABLE_DIV_SHORTCUT = False

MIDDLEWARE_CLASSES = (
    'annoying.middlewares.RedirectMiddleware',
    'annoying.middlewares.StaticServe',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    path.join(PROJECT_ROOT, 'templates/'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    # Сторонние приложения
    'sentry',
    'sentry.client',
    'coffin',
    'staticfiles',
    'indexer',
    'paging',
    'sentry',
    'sentry.client',
    'django_extensions',
    'django_assets',
)

#--- Webassets configuration
# Some webassets settings are located in file django_assets/env.py
# Compass - http://compass-style.org/
ASSETS_CACHE = not DEBUG
COMPASS_BIN = '/var/lib/gems/1.8/bin/compass'
assert path.isfile(COMPASS_BIN), 'Please define Compass executable as COMPASS_BIN in Django settings'
# SASS - http://sass-lang.com/ (installed automatically with Compass)
SASS_BIN = '/var/lib/gems/1.8/bin/sass'
assert path.isfile(SASS_BIN), 'Please define SASS executable as SASS_BIN in Django settings'
# Coffee-script - http://jashkenas.github.com/coffee-script/
COFFEE_PATH = '/home/theman/local/bin/coffee'
assert path.isfile(COFFEE_PATH), 'Please define Coffee-script executable as COFFEE_PATH in Django settings'

#--- Staticfiles settings
STATICFILES_EXCLUDED_APPS = ('sentry', 'sentry.client', 'django_extensions',)


# --- Logging
import logging
LOG_DIR = path.join(PROJECT_ROOT, 'logs')
if not path.isdir(LOG_DIR): os.makedirs(LOG_DIR)
LOG_FILENAME = os.path.join(LOG_DIR, 'django.log')
LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

try:
    from current import *
except ImportError:
    pass

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT,
        filename=LOG_FILENAME)
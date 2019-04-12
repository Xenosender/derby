# coding: utf-8
"""
Django project template by Víðir Valberg Guðmundsson (valberg@orn.li)
"""

import os

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse_lazy

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick way to get absolute urls without actually writing them out
get_path = lambda x: os.path.join(BASE_DIR, x)

# We use the sites framework
SITE_ID = 1

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'of-eflw)dd_^juzajz+iuklc3qc*zfrtv4*#9df_+6&*)v*ukt'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'sekizai.context_processors.sekizai',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        # ...
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                "sekizai.context_processors.sekizai",
            ],
        },
    },
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

ROOT_URLCONF = 'wikiDerby.urls'
WSGI_APPLICATION = 'wikiDerby.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Media and static files
MEDIA_URL = '/media/'
MEDIA_ROOT = get_path('wikiDerby/media/')
STATIC_URL = '/static/'
STATIC_ROOT = get_path('wikiDerby/static/')

# Templates
TEMPLATE_DIRS = (
    get_path('wikiDerby/templates/'),
)

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django_nyt',
    #'south',
    'mptt',
    'sekizai',
    'sorl.thumbnail',
    'wiki',
    'wiki.apps',
    'wiki.plugins.attachments',
    'wiki.plugins.notifications',
    'wiki.plugins.images',
    'wiki.plugins.macros',
)

WIKI_ACCOUNT_HANDLING = True
WIKI_ACCOUNT_SIGNUP_ALLOWED = True
LOGIN_REDIRECT_URL = reverse_lazy('wiki:get', kwargs={'path': ''})
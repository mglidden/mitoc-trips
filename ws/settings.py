"""
Django settings for ws project.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

from celery.schedules import crontab
import raven


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY',
                       '*this-is-obviously-not-secure-only-use-it-locally*')
MEMBERSHIP_SECRET_KEY = os.getenv('MEMBERSHIP_SECRET_KEY',
                                  'secret shared with the mitoc-member repo')
WS_LOTTERY_LOG_DIR = os.getenv('WS_LOTTERY_LOG_DIR', '/tmp/')

# URL to an avatar image that is self-hosted
# (Users who opt out of Gravatar would prefer to not have requests made to
#  Gravatar to fetch the "mystery man" image)
PRIVACY_AVATAR_URL = os.getenv('PRIVACY_AVATAR_URL',
                               "https://s3.amazonaws.com/mitoc-trips/privacy/avatar.svg")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))

NODE_MODULES = os.path.join(BASE_DIR, 'node_modules')

# Settings may override these defaults (easily defined here due to BASE_DIR)
STATIC_URL = '/static/'
STATIC_ROOT = os.getenv('STATIC_ROOT', os.path.join(BASE_DIR, 'static'))

STATICFILES_STORAGE = 'ws.storage.CachedStorage'

STATICFILES_DIRS = [
    NODE_MODULES
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

# auth and allauth settings
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

TEST_RUNNER = 'ws.tests.runner.SetupGearDbTestRunner'

INSTALLED_APPS = []  # Must be defined by respective configs
if os.environ.get('WS_TEST_CONFIG'):
    from .conf.test_settings import *  # NoQA
elif os.environ.get('WS_DJANGO_LOCAL'):
    from .conf.local_settings import *  # NoQA
else:
    from .conf.production_settings import *  # NoQA

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DATABASE_NAME', 'ws'),
        'USER': os.getenv('DATABASE_USER', 'ws'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'password'),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    },
    'auth_db': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('AUTH_DATABASE_NAME', 'auth_db'),
        'USER': os.getenv('DATABASE_USER', 'ws'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'password'),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    },
    'geardb': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('GEAR_DATABASE_NAME', 'geardb'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'USER': os.getenv('GEAR_DATABASE_USER', 'ws'),
        'PASSWORD': os.getenv('GEAR_DATABASE_PASSWORD', 'password'),
        'HOST': os.getenv('GEAR_DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('GEAR_DATABASE_PORT', '3306'),
    },
}
DATABASE_ROUTERS = ['ws.routers.AuthRouter']


FORM_RENDERER = 'djng.forms.renderers.DjangoAngularBootstrap3Templates'


MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
    'djng.middleware.AngularUrlMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'ws.middleware.PrefetchGroupsMiddleware',
    'ws.middleware.ParticipantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if 'debug_toolbar' in INSTALLED_APPS:
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
if 'corsheaders' in INSTALLED_APPS:
    MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')
    MIDDLEWARE.append('django.middleware.common.CommonMiddleware')

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend"
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "ws.context_processors.participant_and_groups",
                "ws.context_processors.angular_templates",
            ],
        },
    },
]

# auth and allauth settings
SITE_ID = "1"

# Log in with only email
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False

# Just click the link to verify
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

# Always "remember me"
ACCOUNT_SESSION_REMEMBER = True

ROOT_URLCONF = 'ws.urls'

WSGI_APPLICATION = 'ws.wsgi.application'


# DocuSign
DOCUSIGN_API_BASE = os.getenv('DOCUSIGN_API_BASE', 'https://demo.docusign.net/restapi/v2/')
DOCUSIGN_USERNAME = os.getenv('DOCUSIGN_USERNAME', 'djcain@mit.edu')
DOCUSIGN_PASSWORD = os.getenv('DOCUSIGN_PASSWORD', 'super-secret')
DOCUSIGN_INTEGRATOR_KEY = os.getenv('DOCUSIGN_INTEGRATOR_KEY', 'secret-uuid')
DOCUSIGN_WAIVER_TEMPLATE_ID = os.getenv('DOCUSIGN_WAIVER_TEMPLATE_ID', 'template-uuid')

# Hit endpoints when we successfully complete a waiver
DOCUSIGN_EVENT_NOTIFICATION = {
    "url": "https://docusign.mitoc.org/members/waiver",
    "loggingEnabled": "true",
    "requireAcknowledgment": "true",
    "useSoapInterface": "false",
    "includeCertificateWithSoap": "false",
    "signMessageWithX509Cert": "true",
    "includeDocuments": "false",  # No need
    "includeCertificateOfCompletion": "false",
    "includeEnvelopeVoidReason": "true",
    "includeTimeZone": "true",  # Timestamps aren't in UTC... >:(
    "includeSenderAccountAsCustomField": "true",
    "includeDocumentFields": "true",
    "envelopeEvents": [
        {"envelopeEventStatusCode": "completed"}
    ],
    "recipientEvents": [
        {"recipientEventStatusCode": "Completed"},
    ],
}

# Google Sheet (discount roster) settings
OAUTH_JSON_CREDENTIALS = os.getenv('OAUTH_JSON_CREDENTIALS')
DISABLE_GSHEETS = bool(os.getenv('DISABLE_GSHEETS'))

# Celery settings
BROKER_URL = os.getenv('BROKER_URL', 'amqp://guest:guest@127.0.0.1//')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'amqp')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CELERYBEAT_SCHEDULE = {
    'purge-non-student-discounts': {
        'task': 'ws.tasks.purge_non_student_discounts',
        'schedule': crontab(minute=0, hour=2, day_of_week=1)
    },
    'refresh-all-discount-spreadsheets': {
        'task': 'ws.tasks.update_all_discount_sheets',
        'schedule': crontab(minute=0, hour=3)
    },
    'send-sao-itineraries': {
        'task': 'ws.tasks.send_sao_itineraries',
        'schedule': crontab(minute=0, hour=4)
    },
    'run-ws-lottery': {
        'task': 'ws.tasks.run_ws_lottery',
        'schedule': crontab(minute=0, hour=14, month_of_year=[1, 2], day_of_week=3)
    },
}

CELERY_TIMEZONE = 'UTC'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Participants must update their profile information every ~6 months
MUST_UPDATE_AFTER_DAYS = 180

# -- Break packages up based on how they'll be served -- #
# CDN libraries are for basic, commonplace libraries (and are loaded first)
cdn_libs = ['jquery/dist/jquery.min.js', 'angular/angular.js', 'd3/d3.min.js',
            '@fortawesome/fontawesome-free/js/all.js']
# All other libraries are bundled together
other_libs = ['lodash/lodash.js',
              'bootstrap/dist/js/bootstrap.js',
              'footable/js/footable.js',
              'footable/js/footable.sort.js',
              'jquery-ui/ui/core.js',
              'jquery-ui/ui/widget.js',
              'jquery-ui/ui/mouse.js',
              'jquery-ui/ui/sortable.js',
              'jquery-ui/jquery-ui.js',
              'jquery-ui-touch-punch/jquery.ui.touch-punch.js',
              'djng/js/django-angular.js',
              'ui-select/dist/select.js',
              'angular-sanitize/angular-sanitize.js',
              'angular-ui-sortable/dist/sortable.js',
              'js/ui-bootstrap-tpls-0.14.3.js',

              # Libraries to support international phone numbers
              'google-libphonenumber/dist/browser/libphonenumber.js',
              'digits-trie/dist/digits-trie.js',
              'bc-countries/dist/bc-countries.js',
              'bc-phone-number/dist/js/bc-phone-number.js'
              ]

local_js = ['js/ws/*.js', 'js/footable_breakpoints.js']

PIPELINE = {
    'JS_COMPRESSOR': 'pipeline.compressors.uglifyjs.UglifyJSCompressor',
    'CSS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'JAVASCRIPT': {
        # With jQuery and Angular served via CDN, this is everything
        'app': {
            'source_filenames': other_libs + local_js,
            'output_filename': 'js/app.js',
        },
        # Must be served before the application (to catch any errors)
        'raven': {
            'source_filenames': [
                'raven-js/dist/raven.min.js',
                'angular-raven/angular-raven.min.js',
            ],
            'output_filename': 'js/raven.js',
        },
    },
    'STYLESHEETS': {
        'app': {
            'source_filenames': (
                'css/layout.css',
                'css/footable.core.css',  # Forked... =(
                'css/footable.standalone.css',
                'bootstrap/dist/css/bootstrap.min.css',
                'ui-select/dist/select.min.css',
                'bc-phone-number/dist/css/bc-phone-number.css',
                # Flags are an optional enhancement to the country picker
                'bc-css-flags/dist/css/bc-css-flags.css',
            ),
            'output_filename': 'css/app.css',
        }
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.getenv('DJANGO_ERROR_FILE', '/tmp/django_errors.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}


RAVEN_CONFIG = {
    'dsn': os.getenv('RAVEN_DSN'),  # If absent, nothing happens
    'release': raven.fetch_git_sha(BASE_DIR),
}

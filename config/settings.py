"""
Django settings for the Legal Cases Management System.

Configuration is driven by environment variables (see .env.example).
"""

from pathlib import Path

import environ
import pymysql

# Let PyMySQL stand in for the C-based mysqlclient driver so MySQL works
# without a compiler / prebuilt wheels (handy on Windows + new Python).
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Environment -----------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['127.0.0.1', 'localhost']),
    DB_ENGINE=(str, 'mysql'),
    DB_PORT=(int, 3306),
)
# Read .env if present (it is gitignored). Missing file is fine.
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-only-change-me')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# On Vercel the deploy URL is injected as VERCEL_URL (host only, no scheme).
# Allow any *.vercel.app host in production so the deployment always responds,
# regardless of whether VERCEL_URL is present at runtime.
VERCEL_URL = env('VERCEL_URL', default='')
if VERCEL_URL:
    ALLOWED_HOSTS.append(VERCEL_URL)
if VERCEL_URL or not DEBUG:
    ALLOWED_HOSTS.append('.vercel.app')

# Extra hosts / CSRF trusted origins can be supplied via env for custom domains.
ALLOWED_HOSTS += env.list('EXTRA_ALLOWED_HOSTS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=['https://*.vercel.app'])


# --- Applications ----------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'crispy_forms',
    'crispy_bootstrap5',

    # Local apps
    'accounts',
    'cases',
    'appointments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves static files in production (Vercel has no static server).
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- Database --------------------------------------------------------------
# Three ways to configure the database, in priority order:
#   1. DATABASE_URL  — a single connection string (used in production / Vercel),
#                      e.g. mysql://user:pass@host:3306/legal_cms
#   2. DB_ENGINE=sqlite  — zero-config local fallback (no server needed)
#   3. DB_* variables    — explicit MySQL host/user/password (local MySQL)
DATABASE_URL = env('DATABASE_URL', default='')

if DATABASE_URL:
    import dj_database_url

    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
    _default = DATABASES['default']

    if _default.get('ENGINE', '').endswith('mysql'):
        # Rebuild OPTIONS cleanly (drop any stray ?ssl-mode=... query param that
        # dj-database-url leaves behind, which PyMySQL doesn't understand).
        options = {'charset': 'utf8mb4'}
        # Managed MySQL (Aiven, etc.) requires TLS. Enable it automatically for
        # any non-local host, so DATABASE_URL is the only var you must set.
        host = (_default.get('HOST') or '').lower()
        is_local = host in ('', 'localhost', '127.0.0.1')
        if env.bool('DB_SSL_REQUIRE', default=not is_local):
            import ssl as _ssl

            ssl_ctx = _ssl.create_default_context()
            ca = env('DB_SSL_CA', default='')
            if ca:
                ssl_ctx.load_verify_locations(ca)  # verify against provider CA
            else:
                # Managed providers use a private CA. Encrypt the connection but
                # skip CA verification when no CA file is supplied.
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = _ssl.CERT_NONE
            options['ssl'] = ssl_ctx
        _default['OPTIONS'] = options
elif env('DB_ENGINE') == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME', default='legal_cms'),
            'USER': env('DB_USER', default='root'),
            'PASSWORD': env('DB_PASSWORD', default=''),
            'HOST': env('DB_HOST', default='127.0.0.1'),
            'PORT': env('DB_PORT'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }


# --- Messages --------------------------------------------------------------
# Map Django's default message levels onto Bootstrap alert classes.
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.DEBUG: 'secondary',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}


# --- Authentication --------------------------------------------------------
AUTH_USER_MODEL = 'accounts.User'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'landing'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internationalization --------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- Static files ----------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise compressed static files. Non-manifest storage is used on purpose:
# on Vercel the files are collected in a separate build container, so a runtime
# manifest wouldn't be present in the Python lambda. Plain names keep {% static %}
# resolvable everywhere (WhiteNoise locally, Vercel's static route in production).
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# Index static files via Django's finders at startup too, so styling works even
# if a build never ran collectstatic (robust for serverless / Vercel).
WHITENOISE_USE_FINDERS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Production hardening (only when DEBUG is off) --------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# --- Crispy forms ----------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

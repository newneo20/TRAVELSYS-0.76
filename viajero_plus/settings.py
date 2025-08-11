# -*- coding: utf-8 -*-
from pathlib import Path
import os
import environ

# ──────────────────────────────────────────────────────────────────────────────
# BASE_DIR y entorno
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# Definición de variables esperadas y defaults
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, None),

    # DB
    DATABASE_URL=(str, ''),                   # Si no se define y DEBUG=True, usamos sqlite
    DATABASE_READONLY_URL=(str, ''),          # Opcional

    # Hosts / Idioma / Zona Horaria
    ALLOWED_HOSTS=(list, []),
    LANGUAGE_CODE=(str, 'es-es'),
    TIME_ZONE=(str, 'America/New_York'),
    USE_TZ=(bool, True),

    # Sesión
    SESSION_COOKIE_AGE=(int, 1800),
    SESSION_EXPIRE_AT_BROWSER_CLOSE=(bool, True),
    SESSION_SAVE_EVERY_REQUEST=(bool, True),

    # Celery / Redis
    CELERY_BROKER_URL=(str, 'redis://localhost:6379/0'),
    CELERY_RESULT_BACKEND=(str, 'redis://localhost:6379/0'),

    # Email SMTP
    EMAIL_REMITENTE=(str, ''),
    EMAIL_HOST=(str, ''),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_PASSWORD=(str, ''),
    EMAIL_USE_TLS=(bool, True),

    # CSRF / Proxy SSL
    CSRF_TRUSTED_ORIGINS=(list, []),
    FORCE_SSL=(bool, False),   # Si quieres forzar HTTPS aunque DEBUG=True (opcional)

    # Static/Media (permite sobreescribir rutas en Docker)
    STATIC_ROOT_PATH=(str, ''),  # ej: '/app/staticfiles/'
    MEDIA_ROOT_PATH=(str, ''),   # ej: '/app/mediafiles/'
)

# Carga .env si existe (desarrollo)
env.read_env(os.path.join(BASE_DIR, '.env'))

# ──────────────────────────────────────────────────────────────────────────────
# Seguridad y modo
# ──────────────────────────────────────────────────────────────────────────────
DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY') or ('dev-secret-key' if DEBUG else None)
if not DEBUG and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY es obligatorio en producción")

# ALLOWED_HOSTS: si DEBUG, permite todo; si no, usa env
ALLOWED_HOSTS = ['*'] if DEBUG else env('ALLOWED_HOSTS')

# ──────────────────────────────────────────────────────────────────────────────
# Apps
# ──────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',

    # Terceros
    'django_celery_beat', 'dal', 'dal_select2',

    # Project apps
    'apps.usuarios', 'apps.backoffice', 'apps.renta_hoteles', 'apps.renta_autos',
    'apps.vuelos', 'apps.gestion_economica', 'apps.booking', 'apps.finanzas',
    'apps.common',
    'viajero_plus',
]

# Solo en desarrollo
if DEBUG:
    INSTALLED_APPS += ['django_extensions']

# ──────────────────────────────────────────────────────────────────────────────
# Middleware / URL / WSGI
# ──────────────────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n antes de CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'viajero_plus.urls'
WSGI_APPLICATION = 'viajero_plus.wsgi.application'

# ──────────────────────────────────────────────────────────────────────────────
# Templates / i18n
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'django.template.context_processors.i18n',
        ],
    },
}]
LOCALE_PATHS = [BASE_DIR / 'locale']

LANGUAGE_CODE = env('LANGUAGE_CODE')
LANGUAGES = [('en', 'English'), ('es', 'Español')]
TIME_ZONE = env('TIME_ZONE')
USE_I18N = True
USE_L10N = True
USE_TZ = env('USE_TZ')

# ──────────────────────────────────────────────────────────────────────────────
# Bases de datos
# ──────────────────────────────────────────────────────────────────────────────
db_url = env('DATABASE_URL')
if db_url:
    DATABASES = {'default': env.db_url('DATABASE_URL')}
else:
    # Fallback cómodo en DEV
    if DEBUG:
        DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
    else:
        raise RuntimeError("En producción define DATABASE_URL")

ro_url = env('DATABASE_READONLY_URL')
if ro_url:
    DATABASES['readonly'] = env.db_url('DATABASE_READONLY_URL')
    # DATABASE_ROUTERS = ['apps.common.routers.ReadOnlyRouter']  # si usas router

# ──────────────────────────────────────────────────────────────────────────────
# Auth / Login
# ──────────────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'usuarios.CustomUser'
LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/usuarios/dashboard/'

# ──────────────────────────────────────────────────────────────────────────────
# Static & Media
# ──────────────────────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# En dev: usar carpeta local del proyecto
if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'static']
    STATIC_ROOT = Path(env('STATIC_ROOT_PATH') or (BASE_DIR / 'staticfiles'))
    MEDIA_ROOT = Path(env('MEDIA_ROOT_PATH') or (BASE_DIR / 'media'))
else:
    # En prod (Docker/Nginx): normalmente se sobreescriben por env
    STATIC_ROOT = Path(env('STATIC_ROOT_PATH') or (BASE_DIR / 'staticfiles'))
    MEDIA_ROOT = Path(env('MEDIA_ROOT_PATH') or (BASE_DIR / 'mediafiles'))

# ──────────────────────────────────────────────────────────────────────────────
# Sesiones
# ──────────────────────────────────────────────────────────────────────────────
SESSION_COOKIE_AGE = env('SESSION_COOKIE_AGE')
SESSION_EXPIRE_AT_BROWSER_CLOSE = env('SESSION_EXPIRE_AT_BROWSER_CLOSE')
SESSION_SAVE_EVERY_REQUEST = env('SESSION_SAVE_EVERY_REQUEST')

# ──────────────────────────────────────────────────────────────────────────────
# Celery
# ──────────────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ──────────────────────────────────────────────────────────────────────────────
# Email SMTP
# ──────────────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')
EMAIL_USE_TLS = env('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env('EMAIL_REMITENTE')

# ──────────────────────────────────────────────────────────────────────────────
# Seguridad extra
# ──────────────────────────────────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')

# Forzar HTTPS cuando no es DEBUG o cuando FORCE_SSL=True
if not DEBUG or env('FORCE_SSL'):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # SECURE_BROWSER_XSS_FILTER está deprecado; los navegadores modernos ya lo manejan

    SECURE_HSTS_SECONDS = 3600 if DEBUG else 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ──────────────────────────────────────────────────────────────────────────────
# Defaults Django
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#settings_dev.py
import os
from pathlib import Path
import environ

# ──────────────────────────────────────────────────────────────────────────────
# BASE_DIR y Entorno
# ──────────────────────────────────────────────────────────────────────────────
# /viajero_plus/envs/settings_dev.py → raíz = parents[2]
BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DEBUG=(bool, True),  # ← dev por defecto
    SECRET_KEY=(str, "dev-secret-change-me"),
    DATABASE_URL=(str, f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}"),
    DATABASE_READONLY_URL=(str, None),
    ALLOWED_HOSTS=(list, ["*"]),
    LANGUAGE_CODE=(str, "es-es"),
    TIME_ZONE=(str, "America/New_York"),
    SESSION_COOKIE_AGE=(int, 1800),
    SESSION_EXPIRE_AT_BROWSER_CLOSE=(bool, True),
    SESSION_SAVE_EVERY_REQUEST=(bool, True),
    CELERY_BROKER_URL=(str, 'redis://localhost:6379/0'),
    CELERY_RESULT_BACKEND=(str, 'redis://localhost:6379/0'),
    EMAIL_REMITENTE=(str, ''),
    EMAIL_HOST=(str, ''),          # si vacío → consola
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_PASSWORD=(str, ''),
)

ENV_FILE = os.getenv("ENV_FILE", BASE_DIR / ".env")
if os.path.exists(ENV_FILE):
    environ.Env.read_env(ENV_FILE)

# ──────────────────────────────────────────────────────────────────────────────
# Seguridad básica
# ──────────────────────────────────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# ──────────────────────────────────────────────────────────────────────────────
# Aplicaciones instaladas
# ──────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Core de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'django_celery_beat',
    'dal',
    'dal_select2',
    # opcional en dev (coméntala si no la tienes instalada)
    'django_extensions',

    # Tus apps
    'apps.usuarios',
    'apps.backoffice',
    'apps.renta_hoteles',
    'apps.renta_autos',
    'apps.vuelos',
    'apps.gestion_economica',
    'apps.booking',
    'apps.finanzas',
    'apps.common',
    'viajero_plus',
]

# ──────────────────────────────────────────────────────────────────────────────
# Middleware
# ──────────────────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'viajero_plus.urls'
WSGI_APPLICATION = 'viajero_plus.wsgi.application'

# ──────────────────────────────────────────────────────────────────────────────
# Templates
# ──────────────────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # raíz/templates
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
    },
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# ──────────────────────────────────────────────────────────────────────────────
# Bases de datos
# ──────────────────────────────────────────────────────────────────────────────
DATABASES = {
    'default': env.db('DATABASE_URL'),  # usa SQLite si no defines otra cosa
}
readonly_url = env('DATABASE_READONLY_URL', default=None)
if readonly_url:
    DATABASES['readonly'] = env.db('DATABASE_READONLY_URL')

# ──────────────────────────────────────────────────────────────────────────────
# Autenticación
# ──────────────────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'usuarios.CustomUser'
LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/usuarios/dashboard/'

# ──────────────────────────────────────────────────────────────────────────────
# Internacionalización
# ──────────────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = env('LANGUAGE_CODE')
LANGUAGES = [('en', 'English'), ('es', 'Español')]
TIME_ZONE = env('TIME_ZONE')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ──────────────────────────────────────────────────────────────────────────────
# Archivos estáticos y media
# ──────────────────────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [p for p in [BASE_DIR / 'static'] if p.exists()]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

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
# Email: consola por defecto; SMTP si hay host definido
# ──────────────────────────────────────────────────────────────────────────────
if env('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_PORT = env('EMAIL_PORT')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = env('EMAIL_REMITENTE')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ──────────────────────────────────────────────────────────────────────────────
# Seguridad (relajada en dev)
# ──────────────────────────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

import os
from pathlib import Path
import environ

# ──────────────────────────────────────────────────────────────────────────────
# BASE_DIR y Entorno
# ──────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, None),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    DATABASE_READONLY_URL=(str, None),
    ALLOWED_HOSTS=(list, []),
    LANGUAGE_CODE=(str, 'en-us'),
    TIME_ZONE=(str, 'UTC'),
    SESSION_COOKIE_AGE=(int, 1800),
    SESSION_EXPIRE_AT_BROWSER_CLOSE=(bool, True),
    SESSION_SAVE_EVERY_REQUEST=(bool, True),
    CELERY_BROKER_URL=(str, 'redis://localhost:6379/0'),
    CELERY_RESULT_BACKEND=(str, 'redis://localhost:6379/0'),
    EMAIL_REMITENTE=(str, ''),
    EMAIL_HOST=(str, ''),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_PASSWORD=(str, ''),
)
# Carga del .env en desarrollo
env.read_env(os.path.join(BASE_DIR, '.env'))

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
    },
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# ──────────────────────────────────────────────────────────────────────────────
# Bases de datos
# ──────────────────────────────────────────────────────────────────────────────
DATABASES = {
    'default': env.db_url('DATABASE_URL'),
}
if env('DATABASE_READONLY_URL'):
    DATABASES['readonly'] = env.db_url('DATABASE_READONLY_URL')

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
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]
TIME_ZONE = env('TIME_ZONE')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ──────────────────────────────────────────────────────────────────────────────
# Archivos estáticos y media
# ──────────────────────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
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
# Email SMTP
# ──────────────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env('EMAIL_REMITENTE')

# ──────────────────────────────────────────────────────────────────────────────
# Configuraciones de seguridad adicionales
# ──────────────────────────────────────────────────────────────────────────────
if not DEBUG:
    # Forzar HTTPS
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Clickjacking, XSS y MIME sniffing
    X_FRAME_OPTIONS = 'DENY'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HSTS
    SECURE_HSTS_SECONDS = 3600            # 1 hora; en prod subir a 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Referrer policy
    SECURE_REFERRER_POLICY = 'same-origin'
else:
    # En desarrollo omitimos la redirección a HTTPS para que runserver funcione
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False



#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'db_build',
#        'USER': 'newneo20',
#        'PASSWORD': '0123456789',
#        'HOST': 'store.prod.travel-sys.loc',
#        'PORT': '5432',
#        'OPTIONS': {
#            'sslmode': 'require',
#        },
#    },
#    'readonly': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'db_build',
#        'USER': 'newneo20',
#        'PASSWORD': '0123456789',
#        'HOST': 'store.prod.travel-sys.loc',
#        'PORT': '5433',
#        'OPTIONS': {
#            'sslmode': 'require',
#        },
#    }
#}

# 🚦 Aquí se especifica el enrutador de bases de datos personalizado
#DATABASE_ROUTERS = ['apps.common.routers.ReadOnlyRouter']



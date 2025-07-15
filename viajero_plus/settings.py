import os
from pathlib import Path
import environ

# Inicializar django-environ
env = environ.Env(
    DEBUG=(bool, False)
)
# Leer .env desde la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(env_file=BASE_DIR / '.env')

# SECRET_KEY y DEBUG
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

# Hosts permitidos (separados por comas en .env)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.usuarios',
    'apps.backoffice',
    'apps.renta_hoteles',
    'apps.renta_autos',
    'apps.vuelos',
    'apps.gestion_economica',
    'apps.booking',
    'apps.finanzas',

    'viajero_plus',
    'django_celery_beat',
    'dal',
    'dal_select2',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'viajero_plus.middleware.AutoLogoutMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'viajero_plus.urls'
WSGI_APPLICATION = 'viajero_plus.wsgi.application'

# Templates
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

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Base de datos
DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
# Opcional: conexión de solo lectura
DB_READ_URL = env('DATABASE_READONLY_URL', default=None)
if DB_READ_URL:
    DATABASES['readonly'] = env.db('DATABASE_READONLY_URL')

# Autenticación
AUTH_USER_MODEL = 'usuarios.CustomUser'
LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/usuarios/dashboard/'

# Internacionalización
LANGUAGE_CODE = env('LANGUAGE_CODE', default='en-us')
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]
TIME_ZONE = env('TIME_ZONE', default='UTC')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Estáticos y media
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cookies y sesiones
SESSION_COOKIE_AGE = env.int('SESSION_COOKIE_AGE', default=1800)
SESSION_EXPIRE_AT_BROWSER_CLOSE = env.bool('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=True)
SESSION_SAVE_EVERY_REQUEST = env.bool('SESSION_SAVE_EVERY_REQUEST', default=True)

# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


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



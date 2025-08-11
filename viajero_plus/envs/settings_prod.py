"""
Django settings for viajero_plus project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv # Importar load_dotenv

# Carga las variables de entorno del archivo .env
# Asegúrate de que el archivo .env esté en la raíz de tu proyecto Docker (my_django_app/)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Usamos la versión moderna y eliminamos la redundancia
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Lee la clave secreta de una variable de entorno
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-fallback-key-for-dev-only')

# SECURITY WARNING: don't run with debug turned on in production!
# Controla DEBUG con una variable de entorno, por defecto False para producción
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'

# Hosts permitidos para tu aplicación en producción
# Lee los hosts permitidos de una variable de entorno, separados por comas
# Si DEBUG es True, permite todos los hosts para facilitar el desarrollo
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
if DEBUG:
    ALLOWED_HOSTS = ['*'] # Permite todos los hosts en modo DEBUG


# Application definition

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
#    'viajero_plus.middleware.AutoLogoutMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'viajero_plus.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Ajusta DIRS para apuntar al directorio 'templates' dentro de 'viajero_plus'
        # Si tus templates están en 'my_django_app/templates'
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

WSGI_APPLICATION = 'viajero_plus.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# Configuración de PostgreSQL para Docker Compose
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'mydatabase_prod'), # Nombre de la DB, default para seguridad
        'USER': os.getenv('POSTGRES_USER', 'myuser_prod'),   # Usuario de la DB, default
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'mypassword_prod_secure'), # Contraseña, default
        'HOST': os.getenv('POSTGRES_HOST', 'db'), # 'db' es el nombre del servicio en docker-compose
        'PORT': os.getenv('POSTGRES_PORT', '5432'), # Puerto de PostgreSQL, default 5432
        # 'OPTIONS': {
        #     'sslmode': 'require', # Habilitar si tu PostgreSQL requiere SSL (común en la nube)
        # },
    }
    # Si tienes una base de datos de solo lectura, configúrala de manera similar
    # 'readonly': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': os.getenv('POSTGRES_DB', 'mydatabase_prod'),
    #     'USER': os.getenv('POSTGRES_USER_RO', 'myuser_ro'),
    #     'PASSWORD': os.getenv('POSTGRES_PASSWORD_RO', 'mypassword_ro_secure'),
    #     'HOST': os.getenv('POSTGRES_HOST_RO', 'db_ro'),
    #     'PORT': os.getenv('POSTGRES_PORT_RO', '5433'),
    #     'OPTIONS': {
    #         'sslmode': 'require',
    #     },
    # }
}

# 🚦 Aquí se especifica el enrutador de bases de datos personalizado
# Si usas un enrutador de DB, descomenta esta línea y asegúrate de que el router esté en tu código
# DATABASE_ROUTERS = ['apps.common.routers.ReadOnlyRouter']


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'es-es' # Cambiado a español por defecto si la app es en español

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
]

# Tu zona horaria específica
TIME_ZONE = 'America/Toronto'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'usuarios.CustomUser'

LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/usuarios/dashboard/'

# Celery settings
# Apunta al servicio 'redis' en Docker Compose
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# STATICFILES_DIRS es para encontrar estáticos durante desarrollo y collectstatic
STATICFILES_DIRS = [
    BASE_DIR / 'static', # Asumiendo que 'static' está al mismo nivel que 'viajero_plus'
]

# STATIC_ROOT es donde 'collectstatic' copiará todos los archivos estáticos para producción
# Este directorio será montado por Nginx
STATIC_ROOT = '/app/staticfiles/' # Nuevo directorio para estáticos recolectados

MEDIA_URL = '/media/'
# MEDIA_ROOT es donde se guardarán los archivos subidos por usuarios
# Este directorio será montado por Nginx
MEDIA_ROOT = '/app/mediafiles/' # Nuevo directorio para archivos de medios


# Tiempo de expiración de sesión (en segundos)
SESSION_COOKIE_AGE = 1800

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# Configuración para CSRF cuando se usa un proxy como Cloudflare
# Lee los orígenes de confianza de una variable de entorno, separados por comas
CSRF_TRUSTED_ORIGINS = os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')

# Eliminar posibles espacios en blanco alrededor de cada origen
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS if origin.strip()]

# Asegura que Django sepa que está detrás de un proxy SSL (Nginx/Cloudflare)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Si tu sitio es solo HTTPS, es buena práctica forzar esto:
SECURE_SSL_REDIRECT = True # Esto hará que Django redirija HTTP a HTTPS a nivel de aplicación (Nginx ya lo hace)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuración de dominio para cookies de sesión y CSRF
#SESSION_COOKIE_DOMAIN = os.getenv('DJANGO_SESSION_COOKIE_DOMAIN')
#CSRF_COOKIE_DOMAIN = os.getenv('DJANGO_SESSION_COOKIE_DOMAIN')

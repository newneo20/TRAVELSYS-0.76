# apps/common/views.py

from celery import Celery
from django.http import JsonResponse

# Usa la misma configuración de tu proyecto
from django.conf import settings

celery_app = Celery(broker=settings.CELERY_BROKER_URL)

def celery_healthcheck(request):
    try:
        # El ping retorna ['pong'] si está conectado
        res = celery_app.control.ping(timeout=1.0)
        status = 'ok' if res else 'unavailable'
    except Exception:
        status = 'error'
    return JsonResponse({'celery': status})

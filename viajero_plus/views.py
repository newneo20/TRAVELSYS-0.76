from django.http import JsonResponse, HttpResponse, HttpResponseServerError
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.db import connections
import logging
import redis
import os

logger = logging.getLogger(__name__)

def index_redirect(request):
    """
    Redirige a los usuarios autenticados al dashboard y a los no autenticados al login.
    """
    if request.user.is_authenticated:
        logger.debug(f"Usuario autenticado redirigido a dashboard: {request.user}")
        return redirect("/usuarios/dashboard/")
    else:
        logger.debug("Usuario no autenticado redirigido a login")
        return redirect("/usuarios/login/")

@require_GET
def health_check(request):
    """
    Verifica el estado de los servicios de la base de datos y Redis y devuelve una
    respuesta JSON detallada.
    """
    health_status = {
        "status": "OK",
        "services": {
            "database": "OK",
            "redis": "OK",
        }
    }

    # 1. Verificar la conexión a la base de datos PostgreSQL
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Error al conectar con la base de datos: {e}")
        health_status["status"] = "Error"
        health_status["services"]["database"] = f"Error: {e}"
        return JsonResponse(health_status, status=500)

    # 2. Verificar la conexión a Redis
    try:
        redis_host = os.environ.get('REDIS_HOST', 'broker-srv')
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))

        r = redis.Redis(host=redis_host, port=redis_port, db=0, socket_connect_timeout=1)
        r.ping()
    except Exception as e:
        logger.error(f"Error al conectar con Redis: {e}")
        health_status["status"] = "Error"
        health_status["services"]["redis"] = f"Error: {e}"
        return JsonResponse(health_status, status=500)

    # Si todas las dependencias están OK, devolvemos un 200 con el JSON de estado
    return JsonResponse(health_status, status=200)

@require_GET
def home(request):
    """
    Vista principal que podría reemplazar index_redirect en el futuro.
    """
    return HttpResponse("Bienvenido a Viajero Plus", content_type="text/plain")

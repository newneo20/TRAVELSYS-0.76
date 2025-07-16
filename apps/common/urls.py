from django.urls import path
from apps.common.notifications import enviar_correo_notificacion, enviar_solicitud_hotel
from .views import celery_healthcheck

app_name = 'common'

urlpatterns = [
    # ... otras rutas ...
    path('reserva/<int:reserva_id>/enviar-correo/', enviar_correo_notificacion, name='enviar_correo_notificacion'),    
    path('reserva/<int:reserva_id>/solicitud-hotel/', enviar_solicitud_hotel, name='enviar_solicitud_hotel'),
    path('health/celery/', celery_healthcheck, name='celery_healthcheck'),
]

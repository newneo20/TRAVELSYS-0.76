from django.urls import path
from apps.common.notifications import enviar_correo_notificacion, enviar_solicitud_hotel

app_name = 'common'

urlpatterns = [
    # ... otras rutas ...
    path('reserva/<int:reserva_id>/enviar-correo/', enviar_correo_notificacion, name='enviar_correo_notificacion'),
    
    path('reserva/<int:reserva_id>/solicitud-hotel/', enviar_solicitud_hotel, name='enviar_solicitud_hotel'),
]

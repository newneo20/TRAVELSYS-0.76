# finanzas/urls.py

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('reservas_finanzas/', views.listar_reservas_finanzas, name='listar_reservas_finanzas'),
    
    path('transacciones/<int:reserva_id>/', views.transacciones_view, name='transacciones'),
    path('transacciones/<int:reserva_id>/eliminar/<int:transaccion_id>/', views.transaccion_eliminar, name='transaccion_eliminar'),
]

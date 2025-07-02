# booking/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


app_name = 'booking'  # Agrega el namespace aquí

urlpatterns = [
    
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # Páginas "en desarrollo" y "en mantenimiento"
    path('en_desarrollo/', views.en_desarrollo, name='en_desarrollo'),    
    path('en_mantenimiento/', views.en_mantenimiento, name='en_mantenimiento'),
    
        
    path('check-session/', views.check_session_status, name='check_session'),
    
    
    path('hotel_search/', views.hotel_search, name='hotel_search'),
    #path('hotel_results/', views.hotel_results, name='hotel_resultsNO'),    
    path('hotel_detalle/<int:hotel_id>/', views.hotel_detalle, name='hotel_detalleNO'),    
    path('hotel_pago_reserva/<int:hotel_id>/', views.hotel_pago_reserva, name='hotel_pago_reserva'),
    path('complete_solicitud/<int:hotel_id>/', views.complete_solicitud, name='complete_solicitud'),
    path('car_rental_search/', views.car_rental_search, name='car_rental_search'),
    path('transfers_search/', views.transfers_search, name='transfers_search'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('perfil/', views.perfil_cliente, name='perfil_cliente'),
    
    
    path('hotel/dashboard/', views.hotel_dashboard, name='hotel_dashboard'),
    path('hotel/hotel_results/', views.hotel_results, name='hotel_results'),    
    path('hotel/hotel_detalle/<int:hotel_id>/', views.hotel_detalle, name='hotel_detalle'),   
    path('hotel/hotel_pago_reserva/<int:hotel_id>/', views.hotel_pago_reserva, name='hotel_pago_reserva'), 
    
    path('ajax/cargar_ofertas_especiales/', views.cargar_ofertas_especiales, name='cargar_ofertas_especiales'),
    path('ajax/cargar_reservas_recientes/', views.cargar_reservas_recientes, name='cargar_reservas_recientes'),
    
    # ---------------------------------------- Sección: Reservas ---------------------------------------- #
    
    path('reservas/', views.listar_reservas, name='listar_reservas'),
    path('reservas/detalles_reserva/<int:reserva_id>/', views.detalles_reserva, name='detalles_reserva'),
    path('reservas/<str:estado>/', views.listar_reservas, name='listar_reservas_por_estado'),   
    
    # ---------------------------------------- Sección: Remesas ---------------------------------------- #

    path('remesas/remesas', views.remesas, name='remesas'),
    path('remesas/guardar-remesa/', views.guardar_remesa, name='guardar_remesa'),

    # ---------------------------------------- Sección: Traslados ---------------------------------------- #

    path('traslados/error/', views.error_page, name='error_page'),
    path('traslados_search/', views.traslados_search, name='traslados_search'),
    path('traslados/dashboard/', views.traslado_dashboard, name='traslado_dashboard'),
    path('obtener-destinos/', views.obtener_destinos, name='obtener_destinos'),
    path('traslados/result_traslados/', views.result_traslados, name='result_traslados'),    
    path('traslados/detalle_traslados/<int:traslado_id>/', views.detalle_traslados, name='detalle_traslados'),
    path('traslados/reserva_traslados/<int:traslado_id>/', views.reserva_traslados, name='reserva_traslados'),
    path('completar-reserva-traslado/<int:traslado_id>/', views.complete_solicitud_traslado, name='complete_solicitud_traslado'),


    # ---------------------------------------- Sección: Envios ---------------------------------------- #    
    
    #path('api_destinatarios/', views.api_destinatarios, name='api_destinatarios'),
    #path('api_remitentes/',   views.api_remitentes,   name='api_remitentes'),
    # la ruta de crear envío:
    path('reservas/envio/crear/', views.crear_reserva_envio, name='crear_reserva_envio'),
    
    path('crear-destinatario/', views.crear_destinatario, name='crear_destinatario'),
    path('crear-remitente/', views.crear_remitente, name='crear_remitente'),
    path('crear-reserva-envio-final/', views.crear_reserva_envio_final, name='crear_reserva_envio_final'),
    

    
    
    
    # ---------------------------------------- Sección: Hoteles Distal ---------------------------------------- #    
    path('hoteles/distal/', views.hotel_dashboard_distal, name='hotel_dashboard_distal'),
    path('hoteles/distal/resultados/', views.hotel_results_distal, name='hotel_results_distal'),
    path('hoteles/distal/<str:hotel_code>/', views.hotel_detalle_distal, name='hotel_detalle_distal'),
    path('hoteles/distal/<str:hotel_code>/pago/', views.hotel_pago_reserva_distal, name='hotel_pago_reserva_distal'),
    path('hoteles/distal/<int:pk>/complete/', views.complete_solicitud,name='complete_solicitud'),
    path('politica-privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('hoteles/distal/<str:hotel_code>/pago/confirmar/', views.confirmar_reserva_distal, name='confirmar_reserva_distal'),
    
   
]

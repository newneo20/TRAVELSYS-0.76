# backoffice/urls.py

from django.urls import path # type: ignore
from . import views
from django.conf import settings # type: ignore
from django.conf.urls.static import static # type: ignore

app_name = 'backoffice'  # Define el namespace aquí

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('check-session/', views.check_session_status, name='check_session'),
    
    # ============================================ #
    # Páginas "en desarrollo" y "en mantenimiento" #
    # ============================================ #
    path('en_desarrollo/', views.en_desarrollo, name='en_desarrollo'),    
    path('en_mantenimiento/', views.en_mantenimiento, name='en_mantenimiento'),
    
    # ======= #
    # HOTELES #
    # ======= #
    path('hoteles/listar_hoteles/', views.listar_hoteles, name='listar_hoteles'),  # Asegúrate de que esta URL esté definida
    path('hoteles/', views.hotel_management, name='hotel_management'),
    path('hoteles/crear/', views.hotel_management, name='crear_hotel'),
    path('hoteles/editar/<int:hotel_id>/', views.hotel_management, name='editar_hotel'),    
    path('eliminar_hotel/<int:hotel_id>/', views.eliminar_hotel, name='eliminar_hotel'),
    
    # ================== #
    # ... otras URLs ... #
    # ================== #
    path('listar_habitaciones/<int:hotel_id>/', views.listar_habitaciones, name='listar_habitaciones'),
    path('guardar_habitacion/<int:hotel_id>/', views.guardar_habitacion, name='guardar_habitacion'),
    path('obtener_habitacion/<int:habitacion_id>/', views.obtener_habitacion, name='obtener_habitacion'),
    path('obtener_habitacion_test/<int:habitacion_id>/', views.obtener_habitacion_test, name='obtener_habitacion_test'),
    path('eliminar_habitacion/<int:habitacion_id>/', views.eliminar_habitacion, name='eliminar_habitacion'),
    path('hotel_content/', views.hotel_content, name='hotel_content'),
    path('hotel_rooms/', views.hotel_rooms, name='hotel_rooms'), 
    path('hotel_settings/<int:hotel_id>/', views.hotel_settings, name='hotel_settings'),
    path('hotel_offers/<int:hotel_id>/', views.hotel_offers, name='hotel_offers'),  
    path('guardar-configuracion-hotel/<int:hotel_id>/', views.guardar_configuracion_hotel, name='guardar_configuracion_hotel'),
    path('cargar-datos-hoteles/<int:hotel_id>/', views.cargar_datos_hoteles, name='cargar_datos_hoteles'),
    path('guardar_todas_ofertas/<int:hotel_id>/', views.guardar_todas_ofertas, name='guardar_todas_ofertas'),
    path('eliminar_oferta/<int:hotel_id>/', views.eliminar_oferta, name='eliminar_oferta'),
    path('hotel_facilities/', views.hotel_facilities, name='hotel_facilities'),
    path('hotel_discounts/', views.hotel_discounts, name='hotel_discounts'),
    path('hotel_tabs/', views.hotel_tabs, name='hotel_tabs'),
    path('hotel_tabs_edit/<int:hotel_id>/', views.hotel_tabs_edit, name='hotel_tabs_edit'),   
    path('hotel_editar/<int:hotel_id>/', views.hotel_editar, name='hotel_editar'), 
    path('guardar_hotel_editado/<int:hotel_id>/', views.guardar_hotel_editado, name='guardar_hotel_editado'),
    path('guardar_hotel/', views.guardar_hotel, name='guardar_hotel'),        
    
    # ============ #
    # HABITACIONES #    
    # ============ #
    path('habitaciones/listar/<int:hotel_id>/', views.listar_habitaciones, name='listar_habitaciones'),
    path('habitaciones/crear/<int:hotel_id>/', views.crear_habitacion, name='crear_habitacion'),
    path('habitacion/eliminar/<int:habitacion_id>/', views.eliminar_habitacion, name='eliminar_habitacion'),
    path('editar_habitacion/<int:habitacion_id>/', views.editar_habitacion, name='editar_habitacion'),

    # ======= #
    # OFERTA #
    # ====== #
    path('ofertas/crear/<int:hotel_id>/', views.hotel_crear_offers, name='hotel_crear_offers'),
    path('hotel_offers/<int:hotel_id>/', views.hotel_offers, name='hotel_offers'),
    path('guardar_oferta/<int:hotel_id>/', views.guardar_oferta, name='guardar_oferta'),    
    path('editar_oferta/<int:oferta_id>/', views.editar_oferta, name='editar_oferta'),
    path('crear_editar_oferta/', views.crear_editar_oferta, name='crear_editar_oferta'),

    # =========== #
    # PROVEEDORES #
    # =========== #
    path('proveedores/', views.listar_proveedores, name='listar_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('editar/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:proveedor_id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    
    # ============== #
    # POLO TURISTICO #    
    # ============== #
    path('polos/', views.listar_polos, name='listar_polos'),
    path('polos/crear/', views.crear_polo_turistico, name='crear_polo'),
    path('polos/editar/<int:polo_id>/', views.editar_polo_turistico, name='editar_polo_turistico'),
    path('polos/eliminar/<int:polo_id>/', views.eliminar_polo, name='eliminar_polo'),
    
    # =========== #
    # FACILIDADES #
    # =========== #
    path('guardar_instalaciones_hotel/<int:hotel_id>/', views.guardar_instalaciones_hotel, name='guardar_instalaciones_hotel'),
    
    # ============= #
    # CONFIGURACION #
    # ============= #
    path('guardar_configuracion_hotel/<int:hotel_id>/', views.guardar_configuracion_hotel, name='guardar_configuracion_hotel'),
    
    # =============== #
    # CADENA HOTELERA #
    # =============== #
    path('cadenas-hoteleras/', views.listar_cadenas_hoteleras, name='listar_cadenas_hoteleras'),
    path('cadenas-hoteleras/crear/', views.crear_cadena_hotelera, name='crear_cadena_hotelera'),
    path('cadenas-hoteleras/editar/<int:pk>/', views.editar_cadena_hotelera, name='editar_cadena_hotelera'),
    path('cadenas-hoteleras/eliminar/<int:pk>/', views.eliminar_cadena_hotelera, name='eliminar_cadena_hotelera'),
    
    # ======== #
    # RESERVAS #
    # ======== #
    path('reservas/', views.listar_reservas, name='listar_reservas'),
    path('reservas/detalles_reserva/<int:reserva_id>/', views.detalles_reserva, name='detalles_reserva'),
    path('reservas/<str:estado>/', views.listar_reservas, name='listar_reservas_por_estado'),   
    path('reservas/crear/', views.crear_reserva, name='crear_reserva'),    
    path('reservas/eliminar/<int:pk>/', views.eliminar_reserva, name='eliminar_reserva'),      
    path('reserva/<int:reserva_id>/editar/', views.edit_reserva_load, name='edit_reserva_load'),
    #path('reserva/<int:reserva_id>/guardar/', views.edit_reserva_save, name='edit_reserva_save'),
    path('reserva/<int:reserva_id>/guardar/', views.guardar_edicion_reserva, name='guardar_edicion_reserva'),
    path('reservas/editar_reserva/<int:reserva_id>/', views.editar_reserva, name='editar_reserva'),
    
    path('reserva/<int:reserva_id>/enviar_booking_distal/', views.enviar_booking_distal, name='enviar_booking_distal'),
    
    path('reserva/<int:reserva_id>/preview_booking_distal/', views.vista_preview_booking_distal, name='vista_preview_booking_distal'),

    
    # ======== #
    # REMESAS  #
    # ======== #
    path('remesas/listar/', views.listar_remesas, name='listar_remesas'),
    path('remesas/eliminar/<int:pk>/', views.eliminar_remesa, name='eliminar_remesa'),
    path('remesas/editar/<int:pk>/', views.cargar_editar_remesa, name='editar_remesa'),  # Este nombre es el que busca tu template
    path('remesas/guardar-edicion/<int:pk>/', views.guardar_editar_remesa, name='guardar_editar_remesa'),




    # ========= #
    # PASAJEROS #
    # ========= #
    path('pasajeros/', views.listar_pasajeros, name='listar_pasajeros'),
    path('pasajeros/crear/', views.crear_pasajero, name='crear_pasajero'),
    path('pasajeros/editar/<int:pk>/', views.editar_pasajero, name='editar_pasajero'),
    path('pasajeros/eliminar/<int:pk>/', views.eliminar_pasajero, name='eliminar_pasajero'),
    
    # ================== #
    # OFERTAS ESPECIALES #
    # ================== #
    path('ofertas-especiales/', views.listar_ofertas_especiales, name='listar_ofertas_especiales'),
    path('ofertas-especiales/crear/', views.crear_oferta_especial, name='crear_oferta_especial'),
    path('ofertas-especiales/editar/<int:pk>/', views.editar_oferta_especial, name='editar_oferta_especial'),
    path('ofertas-especiales/eliminar/<int:pk>/', views.eliminar_oferta_especial, name='eliminar_oferta_especial'),
    
    # ========== #
    # RENTADORAS #
    # ========== #
    path('rentadoras/', views.listar_rentadoras, name='listar_rentadoras'),
    path('rentadoras/crear/', views.crear_rentadora, name='crear_rentadora'),
    path('rentadoras/editar/<int:rentadora_id>/', views.editar_rentadora, name='editar_rentadora'),
    path('rentadoras/eliminar/<int:rentadora_id>/', views.eliminar_rentadora, name='eliminar_rentadora'),
    
    # ========== #
    # CATEGORIAS #
    # ========== #
    path('categorias/', views.listar_categorias, name='listar_categorias'),
    path('categorias/crear/', views.crear_categoria, name='crear_categoria'),
    path('categorias/editar/<int:categoria_id>/', views.editar_categoria, name='editar_categoria'),
    path('categorias/eliminar/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),
    
    # =============== #
    # MODELO DE AUTOS #
    # =============== #
    path('modelos_autos/', views.listar_modelos_autos, name='listar_modelos_autos'),
    path('modelos_autos/crear/', views.crear_modelo_auto, name='crear_modelo_auto'),
    path('modelos_autos/editar/<int:modelo_id>/', views.editar_modelo_auto, name='editar_modelo_auto'),
    path('modelos_autos/eliminar/<int:modelo_id>/', views.eliminar_modelo_auto, name='eliminar_modelo_auto'),
    
    # ========= #
    # LOCATIONS #
    # ========= #
    path('locations/', views.listar_locations, name='listar_locations'),
    path('locations/crear/', views.crear_location, name='crear_location'),
    path('locations/editar/<int:location_id>/', views.editar_location, name='editar_location'),
    path('locations/eliminar/<int:location_id>/', views.eliminar_location, name='eliminar_location'),

    # ========================== #
    # CERTIFICADOS DE VACACIONES #
    # ========================== #
    path('certificado_vacaciones/', views.listar_certificados, name='listar_certificados'),
    path('certificado_vacaciones/crear/', views.crear_certificado, name='crear_certificado'),
    path('certificado_vacaciones/<int:certificado_id>/editar/', views.editar_certificado, name='editar_certificado'),
    path('certificado_vacaciones/<int:certificado_id>/eliminar/', views.eliminar_certificado, name='eliminar_certificado'),

    # ======================== #
    # OPCIONES DE CERTIFICADOS #
    # ======================== # 
    path('opciones_certificado/', views.listar_opciones_certificado, name='listar_opciones_certificado'),
    path('opciones_certificado/crear/', views.crear_opcion_certificado, name='crear_opcion_certificado'),
    path('opciones_certificado/<int:opcion_id>/editar/', views.editar_opcion_certificado, name='editar_opcion_certificado'),
    path('opciones_certificado/<int:opcion_id>/eliminar/', views.eliminar_opcion_certificado, name='eliminar_opcion_certificado'),
    
    # =============== # 
    # TASAS DE CAMBIO #
    # =============== # 
    path('tasas_cambio/', views.listar_tasas_cambio, name='listar_tasas_cambio'),
    path('tasas_cambio/crear/', views.crear_tasa_cambio, name='crear_tasa_cambio'),
    path('tasas_cambio/editar/<int:tasa_id>/', views.editar_tasa_cambio, name='editar_tasa_cambio'),
    path('tasas_cambio/eliminar/<int:tasa_id>/', views.eliminar_tasa_cambio, name='eliminar_tasa_cambio'),
    
    # ========= # 
    # TRASLADOS #
    # ========= # 
    path('traslados/', views.listar_traslados, name='listar_traslados'),
    path('traslados/crear/', views.crear_traslado, name='crear_traslado'),
    path('traslados/editar/<int:traslado_id>/', views.editar_traslado, name='editar_traslado'),
    path('traslados/eliminar/<int:traslado_id>/', views.eliminar_traslado, name='eliminar_traslado'),

    
    # ============= # 
    # TRANSPORTISTAS
    # ============= #     
    path('transportistas/', views.listar_transportistas, name='listar_transportistas'),
    path('transportistas/crear/', views.crear_transportista, name='crear_transportista'),
    path('transportistas/editar/<int:transportista_id>/', views.editar_transportista, name='editar_transportista'),
    path('transportistas/eliminar/<int:transportista_id>/', views.eliminar_transportista, name='eliminar_transportista'),

    # =========== #
    # UBICACIONES #
    # =========== #
    path('ubicaciones/', views.listar_ubicaciones, name='listar_ubicaciones'),
    path('ubicaciones/crear/', views.crear_ubicacion, name='crear_ubicacion'),
    path('ubicaciones/editar/<int:ubicacion_id>/', views.editar_ubicacion, name='editar_ubicacion'),
    path('ubicaciones/eliminar/<int:ubicacion_id>/', views.eliminar_ubicacion, name='eliminar_ubicacion'),
    
    # =========== #
    # VEHICULOS   #
    # =========== #
    path('vehiculos/', views.listar_vehiculos, name='listar_vehiculos'),
    path('vehiculos/crear/', views.crear_vehiculo, name='crear_vehiculo'),
    path('vehiculos/editar/<int:vehiculo_id>/', views.editar_vehiculo, name='editar_vehiculo'),
    path('vehiculos/eliminar/<int:vehiculo_id>/', views.eliminar_vehiculo, name='eliminar_vehiculo'),
    
    # =========== #
    # CLIENTES    #
    # =========== #
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/crear/', views.crear_cliente, name='crear_cliente'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/eliminar/<int:pk>/', views.eliminar_cliente, name='eliminar_cliente'),
    
    path('clientes/<int:cliente_id>/contactos/crear/', views.crear_contacto, name='crear_contacto'),
    path('clientes/contactos/editar/<int:contacto_id>/', views.editar_contacto, name='editar_contacto'),
    path('clientes/contactos/eliminar/<int:contacto_id>/', views.eliminar_contacto, name='eliminar_contacto'),
    
    # ====== #
    # ENVÍOS #
    # ====== #
    path('envios/', views.listar_envios, name='listar_envios'),
    path('envios/crear/', views.crear_envio, name='crear_envio'),
    path('envios/editar/<int:envio_id>/', views.editar_envio, name='editar_envio'),
    path('envios/eliminar/<int:envio_id>/', views.eliminar_envio, name='eliminar_envio'),
    
    # ===================== #
    #      REMITENTES       #
    # ===================== #
    path('remitentes/', views.listar_remitentes, name='listar_remitentes'),
    path('remitentes/crear/', views.crear_remitente, name='crear_remitente'),
    path('remitentes/editar/<int:remitente_id>/', views.editar_remitente, name='editar_remitente'),
    path('remitentes/eliminar/<int:remitente_id>/', views.eliminar_remitente, name='eliminar_remitente'),

    # ======================= #
    #     DESTINATARIOS       #
    # ======================= #
    path('destinatarios/', views.listar_destinatarios, name='listar_destinatarios'),
    path('destinatarios/crear/', views.crear_destinatario, name='crear_destinatario'),
    path('destinatarios/editar/<int:destinatario_id>/', views.editar_destinatario, name='editar_destinatario'),
    path('destinatarios/eliminar/<int:destinatario_id>/', views.eliminar_destinatario, name='eliminar_destinatario'),
        
    # ======================== #
    #     ÍTEMS DE ENVÍO       #
    # ======================== #
    path('items_envio/', views.listar_items_envio, name='listar_items_envio'),
    path('items_envio/crear/', views.crear_item_envio, name='crear_item_envio'),
    path('items_envio/editar/<int:item_id>/', views.editar_item_envio, name='editar_item_envio'),
    path('items_envio/eliminar/<int:item_id>/', views.eliminar_item_envio, name='eliminar_item_envio'),





    


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
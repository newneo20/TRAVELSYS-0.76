from django.contrib import admin
from apps.backoffice.models import Hotel, Habitacion, Oferta, Transportista, Ubicacion, Vehiculo, Traslado

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('hotel_nombre', 'proveedor', 'categoria')
    search_fields = ('hotel_nombre', 'direccion')

@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'tipo')
    search_fields = ('hotel__hotel_nombre', 'tipo')

@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'tipo_habitacion', 'temporada', 'sencilla', 'doble', 'triple')
    search_fields = ('hotel__hotel_nombre', 'tipo_habitacion', 'temporada')

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'capacidad_min', 'capacidad_max')
    search_fields = ('tipo',)

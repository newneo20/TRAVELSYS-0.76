from django.db import models

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    correo1 = models.EmailField(blank=True, null=True)
    correo2 = models.EmailField(blank=True, null=True)
    correo3 = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    detalles_cuenta_bancaria = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class TipoFee(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class PoloTuristico(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    pais = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class PlanAlimenticio(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class Hotel(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, blank=True, null=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tipo_fee = models.CharField(max_length=255, blank=True, null=True)
    polo_turistico = models.ForeignKey(PoloTuristico, on_delete=models.CASCADE, blank=True, null=True)
    plan_alimenticio = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    checkin = models.DateField(blank=True, null=True)
    checkout = models.DateField(blank=True, null=True)
    latitud = models.FloatField(blank=True, null=True)
    longitud = models.FloatField(blank=True, null=True)
    orden = models.IntegerField(blank=True, null=True)
    foto = models.ImageField(upload_to='hotel_fotos/', blank=True, null=True)

    def __str__(self):
        return self.nombre

class Habitacion(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='habitaciones', blank=True, null=True)
    tipo = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='habitacion_fotos/', blank=True, null=True)
    adultos = models.IntegerField(blank=True, null=True)
    ninos = models.IntegerField(blank=True, null=True)
    max_capacidad = models.IntegerField(blank=True, null=True)
    min_capacidad = models.IntegerField(blank=True, null=True)
    descripcion_capacidad = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo} - {self.hotel.nombre}"

class ReservaHotel(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reservas', blank=True, null=True)
    noches = models.IntegerField(blank=True, null=True)
    fecha_reserva = models.DateField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Reserva en {self.hotel.nombre} para {self.noches} noches"
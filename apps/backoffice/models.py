# backoffice/models.py
from django.core.exceptions import ValidationError # type: ignore
from django.db import models # type: ignore
from decimal import Decimal
from django.core.validators import MinValueValidator # type: ignore


# ==========================
# Modelos base y auxiliares
# ==========================
class Servicio(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    correo1 = models.EmailField(blank=True, null=True)
    correo2 = models.EmailField(blank=True, null=True)
    correo3 = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    detalles_cuenta_bancaria = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    
    # Tipo de Proveedor
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('hoteles', 'Hoteles'),
            ('carros', 'Carros'),
            ('vuelos', 'Vuelos'),
            ('remesas', 'Remesas'),
            ('traslados', 'Traslados'),
            ('certificado', 'Certificado de Vacaciones'),
            ('envio', 'Envío'),
        ]
    )
    
    # Campoos de Provvedor de Hoteles 
    fee_adultos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fee_ninos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Campoos de Provvedor de Carros 
    fee_noche = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    

    # Relación ManyToMany para los servicios
    servicios = models.ManyToManyField(
        'Servicio',
        blank=True,
        related_name='proveedores',
        help_text="Seleccione los servicios ofrecidos por este proveedor."
    )

    def __str__(self):
        return self.nombre if self.nombre else "Proveedor sin nombre"

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
    siglas = models.CharField(max_length=255, blank=True, null=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

class CadenaHotelera(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Remitente(models.Model):
    nombre_apellido = models.CharField(max_length=200)    
    id_documento = models.CharField(max_length=100, blank=True, null=True)  # Licencia de conducir
    telefono = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Agregamos fecha de creación para el "Hace X"

    def __str__(self):
        return f"{self.nombre_apellido}"

class Destinatario(models.Model):
    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100, blank=True, null=True)
    primer_apellido = models.CharField(max_length=100)
    segundo_apellido = models.CharField(max_length=100, blank=True, null=True)
    ci = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=50)
    telefono_adicional = models.CharField(max_length=50, blank=True, null=True)
    calle = models.CharField(max_length=255)
    numero = models.CharField(max_length=50, blank=True, null=True)
    entre_calle = models.CharField(max_length=255, blank=True, null=True)
    y_calle = models.CharField(max_length=255, blank=True, null=True)
    apto_reparto = models.CharField(max_length=255, blank=True, null=True)
    piso = models.CharField(max_length=50, blank=True, null=True)
    municipio = models.CharField(max_length=255)
    provincia = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.primer_nombre} {self.primer_apellido}"

    @property
    def nombre_completo(self):
        return f"{self.primer_nombre} {self.segundo_nombre or ''} {self.primer_apellido} {self.segundo_apellido or ''}".strip()

    @property
    def direccion_completa(self):
        partes = [
            f"{self.calle} {self.numero or ''}".strip(),
            self.apto_reparto or '',
            self.municipio,
            self.provincia
        ]
        return ", ".join([parte for parte in partes if parte])
    
# ====================
# Modelos principales
# ====================
class Hotel(models.Model):
    hotel_nombre = models.CharField(max_length=255, blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    fee = models.CharField(max_length=10, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    tipo_fee = models.CharField(max_length=10, blank=True, null=True)
    polo_turistico = models.ForeignKey(PoloTuristico, on_delete=models.SET_NULL, null=True, blank=True)
    plan_alimenticio = models.CharField(max_length=10, blank=True, null=True)
    descripcion_hotel = models.TextField(blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    checkin = models.CharField(max_length=10, blank=True, null=True)
    checkout = models.CharField(max_length=10, blank=True, null=True)    
    orden = models.IntegerField(blank=True, null=True)
    foto_hotel = models.CharField(max_length=255, blank=True, null=True)
    categoria = models.IntegerField(blank=True, null=True)
    cadena_hotelera = models.ForeignKey(CadenaHotelera, on_delete=models.SET_NULL, null=True, blank=True)
    solo_adultos = models.BooleanField(default=False)

    def __str__(self):
        return self.hotel_nombre or "Unnamed Hotel"

class Habitacion(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='habitaciones', blank=True, null=True)
    tipo = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    datetimes = models.CharField(max_length=255, blank=True, null=True)
    foto = models.ImageField(upload_to='habitacion_fotos/', blank=True, null=True)
    adultos = models.IntegerField(blank=True, null=True)
    ninos = models.IntegerField(blank=True, null=True)
    max_capacidad = models.IntegerField(blank=True, null=True)
    min_capacidad = models.IntegerField(blank=True, null=True)
    descripcion_capacidad = models.TextField(blank=True, null=True)
    admite_3_con_1 = models.BooleanField(default=False)
    solo_adultos = models.BooleanField(default=False)

    def __str__(self):
        return f"Habitación {self.tipo} en {self.hotel.hotel_nombre}"

    def clean(self):
        if self.adultos < 0 or self.ninos < 0:
            raise ValidationError("La cantidad de adultos o niños no puede ser negativa.")
        if self.max_capacidad and self.max_capacidad < self.min_capacidad:
            raise ValidationError("La capacidad máxima no puede ser menor que la mínima.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super(Habitacion, self).save(*args, **kwargs)

class ReservaHotel(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='reservas', blank=True, null=True)
    noches = models.IntegerField(blank=True, null=True)
    fecha_reserva = models.DateField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Reserva en {self.hotel.hotel_nombre} para {self.noches} noches"

    def clean(self):
        if self.noches and self.noches <= 0:
            raise ValidationError("El número de noches debe ser positivo.")
        if self.total and self.total < 0:
            raise ValidationError("El total no puede ser negativo.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super(ReservaHotel, self).save(*args, **kwargs)

class Oferta(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    disponible = models.BooleanField(default=True)
    codigo = models.CharField(max_length=50)
    tipo_habitacion = models.CharField(max_length=50)
    temporada = models.CharField(max_length=50)
    booking_window = models.CharField(max_length=50, blank=True, null=True)
    sencilla = models.CharField(max_length=50, blank=True, null=True)
    doble = models.CharField(max_length=50, blank=True, null=True)
    triple = models.CharField(max_length=50, blank=True, null=True)
    primer_nino = models.CharField(max_length=50, blank=True, null=True)
    segundo_nino = models.CharField(max_length=50, blank=True, null=True)
    un_adulto_con_ninos = models.CharField(max_length=50, blank=True, null=True)
    primer_nino_con_un_adulto = models.CharField(max_length=50, blank=True, null=True)
    segundo_nino_con_un_adulto = models.CharField(max_length=50, blank=True, null=True)
    edad_nino = models.CharField(max_length=50, blank=True, null=True)
    edad_infante = models.CharField(max_length=50, blank=True, null=True)
    noches_minimas = models.CharField(max_length=50, blank=True, null=True)
    cantidad_habitaciones = models.IntegerField(default=1)    
    tipo_fee = models.CharField(max_length=10, blank=True, null=True)
    fee_doble = models.CharField(max_length=10, blank=True, null=True)
    fee_triple = models.CharField(max_length=10, blank=True, null=True)
    fee_sencilla = models.CharField(max_length=10, blank=True, null=True)
    fee_primer_nino = models.CharField(max_length=10, blank=True, null=True)
    fee_segundo_nino = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"Oferta {self.codigo} en {self.hotel.hotel_nombre}"

class HotelFacility(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    
    # Baño
    articulos_aseo = models.BooleanField(default=False)
    inodoro = models.BooleanField(default=False)
    toallas = models.BooleanField(default=False)
    bano_privado = models.BooleanField(default=False)
    banera_ducha = models.BooleanField(default=False)
    secador_pelo = models.BooleanField(default=False)
    
    # Seguridad
    extintores = models.BooleanField(default=False)
    detectores_humo = models.BooleanField(default=False)
    cctv = models.BooleanField(default=False)
    
    # Dormitorio
    ropa_cama = models.BooleanField(default=False)
    armario_ropero = models.BooleanField(default=False)
    
    # Comida y bebida
    bar = models.BooleanField(default=False)
    restaurante = models.BooleanField(default=False)
    menu_ninos = models.BooleanField(default=False)
    menu_dietetico = models.BooleanField(default=False)
    desayuno = models.BooleanField(default=False)
    tetera_cafetera = models.BooleanField(default=False)
    
    # General
    ascensor = models.BooleanField(default=False)
    discapacitados = models.BooleanField(default=False)
    hipoalergenico = models.BooleanField(default=False)
    habitaciones_familiares = models.BooleanField(default=False)
    prohibido_fumar = models.BooleanField(default=False)
    calefaccion = models.BooleanField(default=False)
    alfombrado = models.BooleanField(default=False)
    instalaciones_planchar = models.BooleanField(default=False)
    plancha = models.BooleanField(default=False)
    
    # Servicios de recepción
    guardaequipaje = models.BooleanField(default=False)
    factura_proporcionada = models.BooleanField(default=False)
    recepcion_24h = models.BooleanField(default=False)
    checkin_checkout_privado = models.BooleanField(default=False)
    
    # Medios y tecnología
    tv_pantalla_plana = models.BooleanField(default=False)
    radio = models.BooleanField(default=False)
    canales_via_satellite = models.BooleanField(default=False)
    tv = models.BooleanField(default=False)
    telefono = models.BooleanField(default=False)
    
    # Servicios de limpieza
    lavanderia = models.BooleanField(default=False)
    tintoreria = models.BooleanField(default=False)
    limpieza_diaria = models.BooleanField(default=False)
    
    def __str__(self):
        return self.hotel.hotel_nombre

class HotelSetting(models.Model):
    hotel = models.OneToOneField('Hotel', on_delete=models.CASCADE)
    edad_limite_nino = models.IntegerField(default=0)
    edad_limite_infante = models.IntegerField(default=0)
    cantidad_noches = models.IntegerField(default=0)

    def __str__(self):
        return f"Configuración del hotel {self.hotel.hotel_nombre}"

    def clean(self):
        if self.edad_limite_nino < 0:
            raise ValidationError('La edad límite del primer niño no puede ser negativa.')
        if self.edad_limite_infante < 0:
            raise ValidationError('La edad límite del infante no puede ser negativa.')
        if self.cantidad_noches < 0:
            raise ValidationError('La cantidad de noches no puede ser negativa.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(HotelSetting, self).save(*args, **kwargs)

class HabitacionOpcion(models.Model):
    habitacion = models.ForeignKey('Habitacion', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.nombre

class OfertasEspeciales(models.Model):
    codigo = models.CharField(max_length=10, blank=True, null=True) 
    disponible = models.BooleanField(default=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=10, blank=True, null=True, choices=[('hoteles', 'Hoteles'), 
                                                                           ('carros', 'Carros'), 
                                                                           ('vuelos', 'Vuelos'), 
                                                                           ('traslados', 'Traslados')])

class TasaCambio(models.Model):
    tasa_cup = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Tasa de cambio de USD a CUP"
    )
    tasa_mlc = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        help_text="Tasa de cambio de USD a MLC"
    )
    tasa_usd = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        default=1.0000,
        help_text="Tasa de cambio de USD a USD (útil como referencia o base)"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha de última actualización"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Indica si esta tasa de cambio está activa"
    )

    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ['-fecha_actualizacion']

    def __str__(self):
        return (
            f"Tasa USD → CUP: {self.tasa_cup:.4f}, "
            f"USD → MLC: {self.tasa_mlc:.4f}, "
            f"USD → USD: {self.tasa_usd:.4f} - "
            f"Actualizado el {self.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}"
        )


class Remesa(models.Model):
    destinatario = models.ForeignKey(Destinatario, null=True, blank=True, on_delete=models.CASCADE)
    remitente = models.ForeignKey(Remitente, null=True, blank=True, on_delete=models.CASCADE)

    monto_envio = models.DecimalField(max_digits=10, decimal_places=2)
    moneda_envio = models.CharField(max_length=3, choices=[('USD', 'Dólar estadounidense'), ('CUP', 'Peso cubano'), ('MLC', 'MLC')])
    monto_estimado_recepcion = models.DecimalField(max_digits=10, decimal_places=2)
    moneda_recepcion = models.CharField(max_length=3, choices=[('USD', 'Dólar estadounidense'), ('CUP', 'Peso cubano'), ('MLC', 'MLC')])

    def __str__(self):
        return f"Remesa #{self.id} - {self.remitente.nombre_apellido} a {self.destinatario.primer_nombre} {self.destinatario.primer_apellido}"


class HabitacionReserva(models.Model):
    reserva = models.ForeignKey('Reserva', related_name='habitaciones_reserva', on_delete=models.CASCADE)
    habitacion_nombre = models.CharField(max_length=255)
    adultos = models.IntegerField()
    ninos = models.IntegerField()    
    fechas_viaje = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    oferta_codigo = models.CharField(max_length=50)

    # NUEVO: Booking code que viene de la búsqueda Distal
    booking_code = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Código completo de booking de la API Distal, ej: HHAVBDMM|BUNDB|SS-BB"
    )

    def __str__(self):
        return f'Habitación {self.habitacion_nombre} - Reserva {self.reserva.id}'


class Pasajero(models.Model):
    # Relaciones con otros modelos
    habitacion = models.ForeignKey(
        'HabitacionReserva', related_name='pasajeros', on_delete=models.CASCADE, blank=True, null=True
    )
    traslado = models.ForeignKey(
        'Traslado', related_name='pasajeros', on_delete=models.CASCADE, blank=True, null=True 
    )

    # Datos personales del pasajero
    nombre = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    pasaporte = models.CharField(max_length=50, blank=True, null=True)
    caducidad_pasaporte = models.DateField(blank=True, null=True)
    pais_emision_pasaporte = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=1000, blank=True, null=True)
    estado_civil = models.CharField(
        max_length=10,
        choices=[
            ('soltero', 'Soltero'),
            ('casado', 'Casado'),
            ('divorciado', 'Divorciado'),
            ('viudo', 'Viudo')
        ],
        blank=True, null=True
    )
    tipo = models.CharField(
        max_length=10,
        choices=[('adulto', 'Adulto'), ('nino', 'Niño')],
        blank=True, null=True
    )

    def __str__(self):
        """
        Devuelve una representación del pasajero, indicando si está asociado a una habitación o a un traslado.
        """
        if self.habitacion:
            return f'Pasajero {self.nombre} - Habitación {self.habitacion.habitacion_nombre}'
        elif self.traslado:
            return f'Pasajero {self.nombre} - Traslado {self.traslado.origen.nombre} -> {self.traslado.destino.nombre}'
        return f'Pasajero {self.nombre} - Sin asignación'

class OpcionCertificado(models.Model):
    nombre = models.CharField(max_length=255)
    foto = models.ImageField(upload_to='opciones_certificados/', blank=True, null=True)
    descripcion = models.TextField()
    categoria = models.IntegerField(
        choices=[(i, f'{i} Estrellas') for i in range(1, 6)],  # Clasificación de 1 a 5 estrellas
        help_text="Clasificación de 1 a 5 estrellas"
    )
    
    def __str__(self):
        return f'{self.nombre} ({self.categoria} estrellas)'

class CertificadoVacaciones(models.Model):
    nombre = models.CharField(max_length=255, default="Certificado sin nombre")
    es_solo_adultos = models.BooleanField(default=False)
    pasajero = models.ForeignKey(Pasajero, on_delete=models.CASCADE, blank=True, null=True)
    opciones = models.ManyToManyField(OpcionCertificado, related_name='certificados')

    def __str__(self):
        return f'Certificado de Vacaciones - {self.nombre}'

class Reserva(models.Model):
    # Relaciones con otros modelos
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, blank=True, null=True)
    hotel_importado = models.ForeignKey('HotelImportado', on_delete=models.CASCADE, blank=True,null=True, related_name='reservas_distal', help_text="Aquí guardamos el hotel de Distal Caribe")
    remesa = models.ForeignKey('Remesa', on_delete=models.CASCADE, blank=True, null=True)
    certificado_vacaciones = models.ForeignKey('CertificadoVacaciones', on_delete=models.CASCADE, blank=True, null=True)
    traslado = models.ForeignKey('Traslado', on_delete=models.CASCADE, blank=True, null=True) 
    proveedor = models.ForeignKey('Proveedor', on_delete=models.SET_NULL, null=True, blank=True)

    # Campos generales
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    agencia = models.CharField(max_length=255)
    nombre_usuario = models.CharField(max_length=255)
    email_empleado = models.EmailField()
    notas = models.TextField(blank=True, null=True)

    # Información de costos
    costo_sin_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    costo_total = models.DecimalField(max_digits=10, decimal_places=2)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Para guardar el ID necesario para cancelaciones (UniqueID Type="14")
    codigo_reserva_distal = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Código de reserva devuelto por DISTAL (ResID_Type=14)."
    )

    # Para registrar el estado del booking en la API Distal (opcional, pero útil)
    estatus_api_distal = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Estatus interno de sincronización con la API de Distal: enviado, fallido, confirmado..."
    )


    # Tipo de reserva
    tipo = models.CharField(
        max_length=20,
        choices=[
            ('hoteles', 'Hoteles'),
            ('carros', 'Carros'),
            ('vuelos', 'Vuelos'),
            ('remesas', 'Remesas'),
            ('traslados', 'Traslados'),
            ('certificado', 'Certificado de Vacaciones'),
            ('envio', 'Envío'),
        ]
    )

    # Estatus de la reserva
    estatus = models.CharField(
        max_length=11,
        choices=[
            ('solicitada', 'Solicitada'),
            ('pendiente', 'Pendiente'),
            ('confirmada', 'Confirmada'),
            ('modificada', 'Modificada'),
            ('ejecutada', 'Ejecutada'),
            ('cancelada', 'Cancelada'),
            ('reembolsada', 'Reembolsada'),
        ]
    )

    # Información adicional
    numero_confirmacion = models.CharField(max_length=25, blank=True, null=True)
    cobrada = models.BooleanField(default=False)
    pagada = models.BooleanField(default=False)
    
    envio = models.ForeignKey('Envio', on_delete=models.CASCADE, blank=True, null=True)


    def esta_activa(self):
        """
        Verifica si la reserva está activa según su estatus.
        """
        return self.estatus in ['solicitada', 'pendiente', 'confirmada', 'modificada']

    def obtener_descripcion(self):
        """
        Genera una representación amigable de la reserva según su tipo.
        """
        if self.hotel:
            return f'Reserva {self.id} - Hotel: {self.hotel.hotel_nombre}'
        elif self.remesa:
            return f'Reserva {self.id} - Remesa de: {self.remesa.nombre_remitente}'
        elif self.certificado_vacaciones:
            return f'Reserva {self.id} - Certificado de Vacaciones'
        return f'Reserva {self.id} - Usuario: {self.nombre_usuario}'

     # Propiedad para calcular importe por cobrar
    @property
    def importe_por_cobrar(self):
        if self.cobrada:
            return Decimal('0.00')
        return self.costo_total  or Decimal('0.00')
    

    # Propiedad para calcular importe por pagar
    @property
    def importe_por_pagar(self):
        if self.pagada:
            return Decimal('0.00')
        return self.costo_sin_fee or Decimal('0.00')
    
    def __str__(self):
        """
        Devuelve una descripción representativa de la reserva.
        """
        return self.obtener_descripcion()
    
    @property
    def nombre_cliente(self):
        if self.tipo == 'envio' and self.envio and self.envio.destinatario:
            return self.envio.destinatario.nombre_completo
        elif self.tipo == 'traslados' and self.traslado and self.traslado.pasajero:
            return self.traslado.pasajero.nombre
        elif self.tipo in ['hoteles', 'certificado']:
            hab = self.habitaciones_reserva.first()
            if hab and hab.pasajeros.exists():
                return hab.pasajeros.first().nombre
        return None


# =================
# Modelos de autos
# =================
class Rentadora(models.Model):
    nombre = models.CharField(max_length=255)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='rentadoras')

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=255)
    gasolina = models.CharField(max_length=100)
    rentadora = models.ForeignKey(Rentadora, on_delete=models.CASCADE, related_name='categorias')

    def __str__(self):
        return self.nombre

class ModeloAuto(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='modelos_autos/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='modelos')

    def __str__(self):
        return self.nombre

class Location(models.Model):
    nombre = models.CharField(max_length=255)
    pais = models.CharField(max_length=100)
    nomenclatura = models.CharField(max_length=50)
    es_aeropuerto = models.BooleanField(default=False)
    disponibilidad_carros = models.IntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='locations')

    def __str__(self):
        return self.nombre

# =================
# Modelos Traslados
# =================

class Transportista(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.nombre

class Vehiculo(models.Model):
    TIPO_VEHICULO_CHOICES = [
        ('micro_10_plazas', 'Micro 10 Plazas (4 a 8 pax)'),
        ('bus_12_16_plazas', 'Bus 12-16 Plazas (9 a 14 pax)'),
        ('bus_24_29_plazas', 'Bus 24-29 Plazas (15 a 22 pax)'),
        ('omnibus_protocolo', 'Ómnibus Protocolo'),
        ('omnibus_34_plazas', 'Ómnibus 34 Plazas (23-32 Pax)'),
        ('omnibus_44_plazas', 'Ómnibus 44 Plazas (33-42 Pax)'),
        ('omnibus_48_plazas', 'Ómnibus 48 Plazas (43-46 Pax)'),
        
        ('auto_estandar', 'Auto estándar (1-2 Pax)'),
        ('auto_lujo', 'Auto Lujo (1-3 Pax)'),
        ('jeep', 'Jeep (1-4 Pax)'),        
        ('micro_1_5_pax', 'Micro (1-5 Pax)'),
        
        ('microbus_6_10_plazas', 'Microbús de 6-10 plazas (6-10 Pax)'),
        ('minibus_11_16_plazas', 'Minibús hasta 16 plazas (11-16 Pax)'),
        ('minibus_21_24_plazas', 'Minibús de 21-24 plazas (21-24 Pax)'),
        ('omnibus_41_49_plazas', 'Ómnibus de 41-49 plazas (41-49 Pax)'),
    ]

    tipo = models.CharField(max_length=50, choices=TIPO_VEHICULO_CHOICES, unique=True)
    capacidad_min = models.PositiveIntegerField()
    capacidad_max = models.PositiveIntegerField()
    foto = models.ImageField(upload_to='fotos_vehiculos/', null=True, blank=True)

    def __str__(self):
        return dict(self.TIPO_VEHICULO_CHOICES).get(self.tipo, self.tipo)

class Traslado(models.Model):
    transportista = models.ForeignKey(Transportista, on_delete=models.CASCADE)
    origen = models.ForeignKey(Ubicacion, related_name='traslados_desde', on_delete=models.CASCADE)
    destino = models.ForeignKey(Ubicacion, related_name='traslados_hacia', on_delete=models.CASCADE)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('transportista', 'origen', 'destino', 'vehiculo')

    def __str__(self):
        return f"{self.transportista} - {self.origen} a {self.destino} ({self.vehiculo}): ${self.costo}"



# ============================
# Modelos Clientes y Contactos 
# ============================

class Cliente(models.Model):
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellidos = models.CharField(max_length=100, blank=True, null=True)
    
    pasaporte = models.CharField(max_length=20, blank=True, null=True)
    carnet_identidad = models.CharField(max_length=20, blank=True, null=True)
    licencia = models.CharField(max_length=20, blank=True, null=True)

    telefono_principal = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    direccion = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True) 

    fecha_nacimiento = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    es_vip = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre or ''} {self.apellidos or ''}".strip()

class Contacto(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='contactos')

    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellidos = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    carnet_identidad = models.CharField("Carné de Identidad", max_length=20, blank=True, null=True)
    pasaporte_licencia = models.CharField("Pasaporte/Licencia", max_length=20, blank=True, null=True)
    nacionalidad = models.CharField(max_length=50, blank=True, null=True)

    telefono_primario = models.CharField(max_length=20, blank=True, null=True)
    telefono_secundario = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # Dirección
    calle = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=100, blank=True, null=True)  
    entre_calle = models.CharField(max_length=100, blank=True, null=True)
    y_calle = models.CharField(max_length=100, blank=True, null=True)
    apto_reparto = models.CharField(max_length=100, blank=True, null=True)
    piso = models.CharField(max_length=100, blank=True, null=True)
    municipio = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100, blank=True, null=True)    

    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre or ''} {self.apellidos or ''}".strip()

# =================
# Modelos de ENVIOS
# =================

class Envio(models.Model):
    destinatario = models.ForeignKey(Destinatario, null=True, blank=True, on_delete=models.CASCADE)
    remitente = models.ForeignKey(Remitente, null=True, blank=True, on_delete=models.CASCADE)
    modalidad = models.CharField(max_length=100, blank=True, null=True)
    servicio = models.CharField(max_length=100, blank=True, null=True)
    fecha_envio = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Envío de {self.remitente} a {self.destinatario}"

class ItemEnvio(models.Model):

    envio         = models.ForeignKey(
        Envio,
        on_delete=models.CASCADE,
        related_name="items",
    )
    hbl           = models.CharField(max_length=50)                  # Código HBL
    descripcion   = models.TextField()
    cantidad      = models.PositiveIntegerField(default=1)
    peso          = models.DecimalField(max_digits=6,  decimal_places=2)
    valor_aduanal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    envio_manejo  = models.CharField(max_length=50, blank=True, null=True)    
    tipo          = models.CharField(max_length=50, blank=True, null=True)

    def total(self):
        return self.precio * self.cantidad

    def __str__(self):
        return f"{self.descripcion} (x{self.cantidad})"


# =========================
# Modelos de Distal Caribe 
# =========================

class HotelImportado(models.Model):
    destino = models.CharField(max_length=100)
    city_code = models.CharField(max_length=20)
    hotel_code = models.CharField(max_length=50, unique=True)
    hotel_name = models.CharField(max_length=255)
    hotel_city_code = models.CharField(max_length=20)
    area_id = models.CharField(max_length=50, blank=True, null=True)
    giata_id = models.CharField(max_length=50, blank=True, null=True)
    country_iso_code = models.CharField(max_length=5)
    country_name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    rating = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        verbose_name = "Hotel Importado"
        verbose_name_plural = "Hoteles Importados"

    def __str__(self):
        return f"{self.hotel_name} ({self.hotel_code})"

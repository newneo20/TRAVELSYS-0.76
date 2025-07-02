import os
import smtplib
from datetime import datetime

# --------------------------------------------------------------- #
# Importaciones para el envío de correos
# --------------------------------------------------------------- #
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# --------------------------------------------------------------- #
# Importaciones para la generación de PDFs con ReportLab
# --------------------------------------------------------------- #
from reportlab.lib import colors  # type: ignore
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib.units import inch, cm  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer, Flowable  # type: ignore
from reportlab.pdfgen import canvas  # type: ignore

# --------------------------------------------------------------- #
# Importaciones de tus modelos (ajusta la ruta según tu proyecto)
# --------------------------------------------------------------- #
from apps.backoffice.models import Pasajero, HabitacionReserva  # O donde tengas definidos estos modelos


# --------------------------------------------------------------- #
# Clase para dibujar la imagen del logo en forma circular:
# --------------------------------------------------------------- #
class CircularImage(Flowable):
    """
    Clase para dibujar una imagen con forma circular usando un 'clip'.
    """
    def __init__(self, img_path, width, height):
        super().__init__()
        self.img_path = img_path
        self.width = width
        self.height = height

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        c.saveState()
        p = c.beginPath()
        p.circle(self.width / 2, self.height / 2, min(self.width, self.height) / 2)
        c.clipPath(p, fill=1, stroke=0)
        c.drawImage(
            self.img_path,
            0,
            0,
            width=self.width,
            height=self.height,
            preserveAspectRatio=True
        )
        c.restoreState()


# --------------------------------------------------------------- #
# Funciones para el envío de correos y generación de PDFs:
# --------------------------------------------------------------- #

def correo_confirmacion_reserva(reserva):
    """
    Función despachadora que, según el tipo de reserva, envía el correo
    de confirmación correspondiente.
    """
    if reserva.tipo == 'hoteles':
        correo_confirmacion_hoteles(reserva)
    elif reserva.tipo == 'traslados':
        correo_confirmacion_traslados(reserva)
    else:
        # Acá se pueden agregar más condiciones en el futuro para otros tipos.
        print(f"No se ha definido el envío de correo para el tipo de reserva: {reserva.tipo}")


def correo_confirmacion_hoteles(reserva):
    """
    Envía el correo de confirmación para una reserva de hotel.
    """
    pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
    agencia = {
        "nombre": "Viajes Felices S.A.",
        "direccion": "Calle Principal 123, Ciudad Turística",
        "usuario": "agente001",
        "email": "agente001@viajesfelices.com"
    }
    encabezado = "Muchas gracias por reservar con RUTA MULTISERVICE, estamos procesando su solicitud:"
    enviar_correo(reserva, pasajeros, habitaciones, reserva.email_empleado, encabezado, agencia)


def correo_confirmacion_traslados(reserva):
    """
    Envía el correo de confirmación para una reserva de traslados.
    Se asume que el objeto 'reserva' tiene un atributo 'traslado' y que
    los pasajeros se relacionan a ese traslado.
    """
    pasajeros = Pasajero.objects.filter(traslado=reserva.traslado)
    traslado = reserva.traslado  # Objeto Traslado asociado a la reserva
    encabezado = "Gracias por reservar su traslado con RUTA MULTISERVICE, estamos procesando su solicitud:"
    asunto, cuerpo_html, cuerpo_texto = generar_contenido_correo_traslados(reserva, pasajeros, traslado, encabezado)
    
    from_email = "admin@travel-sys.com"
    password = "Z6d*ibHDAyJTmLNq%kvQNx"
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = from_email
    mensaje["To"] = reserva.email_empleado
    mensaje.attach(MIMEText(cuerpo_texto, "plain"))
    mensaje.attach(MIMEText(cuerpo_html, "html"))
    
    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as servidor:
            servidor.starttls()
            servidor.login(from_email, password)
            servidor.sendmail(from_email, reserva.email_empleado, mensaje.as_string())
            print("Correo de traslado enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo de traslado: {e}")


def generar_contenido_correo_traslados(reserva, pasajeros, traslado, encabezado):
    """
    Genera el contenido (asunto, cuerpo HTML y texto plano) del correo para una reserva de traslados.
    """
    primer_pasajero = pasajeros.first()
    nombre_pasajero = primer_pasajero.nombre if primer_pasajero else "Cliente"
    
    if reserva.estatus == 'confirmada':
        asunto = f"Confirmación de Traslado Reserva {reserva.id} ({nombre_pasajero})"
    else:
        asunto = f"Solicitud de Traslado Reserva {reserva.id} ({nombre_pasajero})"
    
    origen = traslado.origen.nombre if traslado.origen else "Origen no especificado"
    destino = traslado.destino.nombre if traslado.destino else "Destino no especificado"
    vehiculo = str(traslado.vehiculo)
    costo = traslado.costo
    
    detalles_traslado = f"""
    <p><b>Origen:</b> {origen}</p>
    <p><b>Destino:</b> {destino}</p>
    <p><b>Vehículo:</b> {vehiculo}</p>
    <p><b>Costo:</b> ${costo}</p>
    """
    
    cuerpo_html = f"""
    <html>
    <body>
    <p>{encabezado}</p>
    <h2>Detalles del Traslado:</h2>
    {detalles_traslado}
    </body>
    </html>
    """
    
    cuerpo_texto = f"""{encabezado}
Detalles del Traslado:
Origen: {origen}
Destino: {destino}
Vehículo: {vehiculo}
Costo: ${costo}
"""
    return asunto, cuerpo_html, cuerpo_texto


def enviar_correo(reserva, pasajeros, habitaciones, to_email, encabezado, agencia):
    """
    Función para enviar el correo de confirmación para reservas de hoteles.
    Genera el contenido y, si corresponde, adjunta PDFs (voucher y factura).
    """
    asunto, cuerpo_html, cuerpo_texto = generar_contenido_correo(reserva, pasajeros, habitaciones, encabezado)
    from_email = "admin@travel-sys.com"
    password = "Z6d*ibHDAyJTmLNq%kvQNx"
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = from_email
    mensaje["To"] = to_email
    mensaje.attach(MIMEText(cuerpo_texto, "plain"))
    mensaje.attach(MIMEText(cuerpo_html, "html"))
    
    if getattr(reserva, 'numero_confirmacion', None):
        voucher = generar_voucher_pdf(reserva, pasajeros, habitaciones, agencia)
        factura = generar_factura_pdf(reserva, pasajeros, habitaciones, agencia)
        voucher_filename = f"voucher-{reserva.id}.pdf"
        with open(voucher, "rb") as f:
            adjunto_voucher = MIMEApplication(f.read(), _subtype="pdf")
            adjunto_voucher.add_header("Content-Disposition", "attachment", filename=voucher_filename)
            mensaje.attach(adjunto_voucher)
        factura_filename = f"factura-{reserva.id}.pdf"
        with open(factura, "rb") as f:
            adjunto_factura = MIMEApplication(f.read(), _subtype="pdf")
            adjunto_factura.add_header("Content-Disposition", "attachment", filename=factura_filename)
            mensaje.attach(adjunto_factura)
    
    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as servidor:
            servidor.starttls()
            servidor.login(from_email, password)
            servidor.sendmail(from_email, to_email, mensaje.as_string())
            print("Correo enviado exitosamente desde Outlook/Office365")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


def generar_voucher_pdf(reserva, pasajeros, habitaciones, agencia):
    # Aquí va la lógica actual para generar el PDF del voucher.
    # La función debe crear el PDF y retornar la ruta del archivo generado.
    pass  # Reemplazá esto con la implementación actual


def generar_factura_pdf(reserva, pasajeros, habitaciones, agencia):
    # Aquí va la lógica actual para generar el PDF de la factura.
    # La función debe crear el PDF y retornar la ruta del archivo generado.
    pass  # Reemplazá esto con la implementación actual


def convertir_estrellas(categoria):
    try:
        numero_estrellas = int(categoria)
        return "★" * numero_estrellas
    except ValueError:
        return categoria


MESES_EN_ESPANOL = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


def formatear_fecha_en_espanol(fecha):
    mes_nombre = MESES_EN_ESPANOL[fecha.month]
    return fecha.strftime(f'{mes_nombre}/%d/%Y')


def generar_contenido_correo(reserva, pasajeros, habitaciones, encabezado):
    """
    Genera el contenido del correo para reservas de hoteles.
    """
    primer_pasajero = next((p for p in pasajeros if p.habitacion.reserva.id == reserva.id), None)
    nombre_pasajero = primer_pasajero.nombre if primer_pasajero else "Cliente"
    
    if reserva.estatus == 'confirmada':
        asunto = f"Confirmación de Reserva {reserva.id} ({nombre_pasajero})"
    else:
        asunto = f"Solicitud de Reserva {reserva.id} ({nombre_pasajero})"
    
    fechas_viaje = habitaciones[0].fechas_viaje if habitaciones and habitaciones[0].fechas_viaje else ''
    fechas_viaje_split = fechas_viaje.split(' - ') if fechas_viaje else ['', '']
    checkin = f"{fechas_viaje_split[0]} 14:00" if fechas_viaje_split[0] else ''
    checkout = f"{fechas_viaje_split[1]} 12:00" if len(fechas_viaje_split) > 1 and fechas_viaje_split[1] else ''
    
    detalles_reserva = f"""
    <p><b>Hotel:</b> {reserva.hotel.hotel_nombre} ({convertir_estrellas(reserva.hotel.categoria)})</p>
    <p><b>Dirección:</b> {reserva.hotel.direccion}</p>
    <p><b>Check-in:</b> {checkin}</p>
    <p><b>Check-out:</b> {checkout}</p>
    <p><b>Total a pagar:</b> ${reserva.precio_total}</p>
    """
    if reserva.estatus == 'confirmada':
        detalles_reserva += f"<p><b>Número de Confirmación:</b> {reserva.numero_confirmacion}</p>"
    
    detalles_habitaciones_list = []
    for i, habitacion in enumerate(habitaciones, 1):
        adults = ' / '.join(p.nombre for p in pasajeros if p.habitacion == habitacion and p.tipo == 'adulto')
        children = ' / '.join(p.nombre for p in pasajeros if p.habitacion == habitacion and p.tipo == 'niño')
        hab_detalle = f"""
        <h2>Habitación {i} - {habitacion.habitacion_nombre}</h2>
        <p><b>Adultos:</b> {habitacion.adultos} ({adults})</p>
        """
        if habitacion.ninos > 0:
            hab_detalle += f"<p><b>Niños:</b> {habitacion.ninos} ({children})</p>"
        detalles_habitaciones_list.append(hab_detalle)
    detalles_habitaciones = "".join(detalles_habitaciones_list)
    
    cuerpo_html = f"""
    <html>
    <body>
    <p>{encabezado}</p>
    <h2>Detalles de la Reserva:</h2>
    {detalles_reserva}
    {detalles_habitaciones}
    </body>
    </html>
    """
    
    cuerpo_texto = f"""{encabezado}
Detalles de la Reserva:
Hotel: {reserva.hotel.hotel_nombre} ({convertir_estrellas(reserva.hotel.categoria)})
Dirección: {reserva.hotel.direccion}
Teléfono: {reserva.hotel.telefono}
Check-in: {checkin}
Check-out: {checkout}
"""
    for i, habitacion in enumerate(habitaciones, 1):
        adults = ' / '.join(p.nombre for p in pasajeros if p.habitacion == habitacion and p.tipo == 'adulto')
        children = ' / '.join(p.nombre for p in pasajeros if p.habitacion == habitacion and p.tipo == 'niño')
        cuerpo_texto += f"""
Habitación {i} - {habitacion.habitacion_nombre}
Adultos: {habitacion.adultos} ({adults})
Niños: {habitacion.ninos} ({children})
"""
    return asunto, cuerpo_html, cuerpo_texto

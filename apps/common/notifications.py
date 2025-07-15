# apps/common/notifications.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.core.exceptions import ImproperlyConfigured
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from apps.usuarios.decorators import manager_required 
from apps.backoffice.models      import Reserva
from apps.common.mail_templates import (
    generar_contenido_correo_hotel_mejorado,
    generar_contenido_correo_traslado,
    generar_contenido_correo_envio,
    generar_contenido_correo_remesa,
    generar_contenido_correo_certificado,
    generar_contenido_solicitud_hotel,
)

@login_required
@manager_required
def enviar_solicitud_hotel(request, reserva_id):
    """
    Vista que dispara un correo de solicitud de hotel
    al agente (carlosalej1985@gmail.com).
    """
    if request.method != 'POST':
        return redirect('backoffice:editar_reserva', reserva_id)

    reserva = get_object_or_404(Reserva, id=reserva_id)

    if not (reserva.tipo == 'hoteles'
            and reserva.proveedor.nombre != 'DISTALCU'
            and not reserva.numero_confirmacion):
        messages.error(request, "No aplica envío de solicitud para esta reserva.")
        return redirect('backoffice:editar_reserva', reserva_id)

    # obtengo pasajeros y habitaciones
    from apps.backoffice.models import Pasajero, HabitacionReserva
    pasajeros    = Pasajero.objects.filter(habitacion__reserva=reserva)
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)

    try:
        subj, html, txt = generar_contenido_solicitud_hotel(reserva, pasajeros, habitaciones)
        _send_basic_email(subj, html, txt, "carlosalej1985@gmail.com")
        messages.success(request, "📧 Correo de solicitud enviado al agente correctamente.")
    except Exception as e:
        messages.error(request, f"❌ Error al enviar solicitud: {e}")

    return redirect('backoffice:editar_reserva', reserva_id)


@login_required
@manager_required
def enviar_correo_notificacion(request, reserva_id):
    """
    Vista para disparar el correo de confirmación.
    Solo para reservas tipo 'hoteles', proveedor != 'DISTALCU' y sin confirmación aún.
    """
    if request.method != 'POST':
        return redirect('backoffice:editar_reserva', reserva_id)

    reserva = get_object_or_404(Reserva, id=reserva_id)

    if not (reserva.tipo == 'hoteles'
            and reserva.proveedor.nombre != 'DISTALCU'
            and not reserva.numero_confirmacion):
        messages.error(request, "No aplica envío de correo de confirmación para esta reserva.")
        return redirect('backoffice:editar_reserva', reserva_id)

    try:
        _dispatch_enviar_correo(reserva)
        messages.success(request, "📧 Correo de confirmación enviado correctamente.")
    except Exception as e:
        messages.error(request, f"❌ Error al enviar correo: {e}")

    return redirect('backoffice:editar_reserva', reserva_id)


def enviar_correo_confirmacion(reserva):
    """
    Función para uso desde cualquier parte del código:
    recibe la instancia de Reserva y dispara el correo.
    """
    _dispatch_enviar_correo(reserva)


def _dispatch_enviar_correo(reserva):
    """Llama a la función adecuada según el tipo de reserva."""
    if reserva.tipo == 'hoteles':
        _enviar_hotel(reserva)
    elif reserva.tipo == 'traslados':
        _enviar_traslados(reserva)
    elif reserva.tipo == 'envio':
        _enviar_envio(reserva)
    elif reserva.tipo == 'remesas':
        _enviar_remesa(reserva)
    elif reserva.tipo == 'certificado':
        _enviar_certificado(reserva)
    else:
        print(f"[INFO] No definido envío de correo para tipo: {reserva.tipo}")


def _enviar_hotel(reserva):
    from apps.backoffice.models import Pasajero, HabitacionReserva

    pasajeros    = Pasajero.objects.filter(habitacion__reserva=reserva)
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
    encabezado   = (
        "Gracias por reservar con RUTA MULTISERVICE. "
        "A continuación encontrará los detalles de su reserva:"
    )
    subj, html, txt = generar_contenido_correo_hotel_mejorado(
        reserva, pasajeros, habitaciones, encabezado
    )
    _send_basic_email(subj, html, txt, reserva.email_empleado)


def _enviar_traslados(reserva):
    from apps.backoffice.models import Pasajero

    pasajeros = Pasajero.objects.filter(traslado=reserva.traslado)
    subj, html, txt = generar_contenido_correo_traslado(reserva, pasajeros)
    _send_basic_email(subj, html, txt, reserva.email_empleado)


def _enviar_envio(reserva):
    subj, html, txt = generar_contenido_correo_envio(reserva)
    _send_basic_email(subj, html, txt, reserva.email_empleado)


def _enviar_remesa(reserva):
    subj, html, txt = generar_contenido_correo_remesa(reserva)
    _send_basic_email(subj, html, txt, reserva.email_empleado)


def _enviar_certificado(reserva):
    subj, html, txt = generar_contenido_correo_certificado(reserva)
    _send_basic_email(subj, html, txt, reserva.email_empleado)


def _send_basic_email(subject: str, html: str, text: str, to_email: str):
    """
    Función MT (mail transport) que realmente manda por SMTP.
    Variables de entorno:
      EMAIL_REMITENTE, EMAIL_PASSWORD, EMAIL_HOST, EMAIL_PORT
    """
    sender = os.getenv('EMAIL_REMITENTE', 'booking@rutamultiservice.com')
    pwd    = os.getenv('EMAIL_PASSWORD')
    host   = os.getenv('EMAIL_HOST',    'smtp-mail.outlook.com')
    port   = int(os.getenv('EMAIL_PORT', 587))

    if not pwd:
        raise ImproperlyConfigured("EMAIL_PASSWORD no definida en entorno")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = sender
    msg['To']      = to_email
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(host, port) as srv:
        srv.starttls()
        srv.login(sender, pwd)
        srv.sendmail(sender, to_email, msg.as_string())

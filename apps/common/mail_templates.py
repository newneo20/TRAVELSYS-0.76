# apps/common/mail_templates.py

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from apps. backoffice.models import Pasajero, HabitacionReserva

def generar_contenido_correo_hotel_mejorado(reserva, pasajeros, habitaciones, encabezado):
    """
    Genera asunto, cuerpo HTML y cuerpo de texto plano
    para la confirmación de una reserva de hotel, incluyendo
    una tabla de detalles de cada pasajero por habitación.
    """
    nombre_hotel = getattr(reserva.hotel_importado, 'hotel_name', 'Hotel no disponible')
    destino      = getattr(reserva.hotel_importado, 'destino', 'Destino no disponible')
    moneda       = getattr(reserva.hotel_importado, 'currency', 'USD')
    fechas_viaje = habitaciones[0].fechas_viaje if habitaciones else ''
    fechas       = fechas_viaje.split(' - ') if fechas_viaje else ['', '']
    checkin      = f"{fechas[0]} 14:00" if fechas[0] else "No disponible"
    checkout     = f"{fechas[1]} 12:00" if len(fechas) > 1 and fechas[1] else "No disponible"
    total        = f"{reserva.precio_total} {moneda}"
    asunto       = f"🧾 Confirmación de Reserva Hotel #{reserva.id}"

    # Inicio del HTML
    html = f"""
    <div style="font-family:'Segoe UI',sans-serif;max-width:700px;margin:40px auto;
                border-radius:12px;overflow:hidden;box-shadow:0 0 10px rgba(0,0,0,0.1);
                background-color:#f4f6f8;">
      <div style="background:#003366;padding:30px 20px;text-align:center;color:#fff;">
        <img src="http://build.dev.travel-sys.loc:8000/static/images/ruta_Logo.jpeg"
             alt="Ruta Multiservice" style="width:130px;margin-bottom:15px;border-radius:10px;" />
        <h2 style="margin:0;font-size:24px;">
          ¡Gracias por tu reserva en <strong>Ruta Multiservice</strong>!
        </h2>
        <p style="margin:10px 0 0;font-size:16px;color:#e0e0e0;">{encabezado}</p>
      </div>
      <div style="padding:30px;background-color:#ffffff;">
        <h3 style="color:#003366;border-bottom:2px solid #dedede;padding-bottom:8px;">
          🏨 Detalles del Hotel
        </h3>
        <p><strong>Hotel:</strong> {nombre_hotel}</p>
        <p><strong>Destino:</strong> {destino}</p>
        <p><strong>Check-in:</strong> {checkin}</p>
        <p><strong>Check-out:</strong> {checkout}</p>
        <p><strong>Total a pagar:</strong>
           <span style="color:#28a745;font-weight:bold;">{total}</span></p>
        <hr style="margin:30px 0 20px;">
        <h3 style="color:#003366;border-bottom:2px solid #dedede;padding-bottom:8px;">
          🚩 Habitaciones
        </h3>
    """

    # Para cada habitación, incluimos una tabla de pasajeros
    for i, hab in enumerate(habitaciones, 1):
        hab_nom = getattr(hab, 'habitacion_nombre', f'Habitación {i}')
        html += f"""
        <div style="background:#f8f9fa;padding:20px;border-radius:8px;margin-bottom:20px;">
          <h4 style="margin:0 0 12px;color:#005580;">
            Habitación {i} – {hab_nom}
          </h4>
          <table style="width:100%;border-collapse:collapse;">
            <thead>
              <tr style="background:#e0e7ff;">
                <th style="border:1px solid #ccc;padding:8px;text-align:left;">Nombre</th>
                <th style="border:1px solid #ccc;padding:8px;text-align:left;">Tipo</th>
                <th style="border:1px solid #ccc;padding:8px;text-align:left;">Nacimiento</th>
                <th style="border:1px solid #ccc;padding:8px;text-align:left;">Pasaporte</th>
                <th style="border:1px solid #ccc;padding:8px;text-align:left;">Caducidad</th>
                <th style="border:1px solid #ccc;padding:8px;text-align:left;">País emisión</th>
              </tr>
            </thead>
            <tbody>
        """
        # Filtramos pasajeros de esta habitación
        for p in [p for p in pasajeros if p.habitacion_id == hab.id]:
            nac = p.fecha_nacimiento.strftime('%Y-%m-%d') if p.fecha_nacimiento else '—'
            cad = p.caducidad_pasaporte.strftime('%Y-%m-%d') if p.caducidad_pasaporte else '—'
            html += f"""
              <tr>
                <td style="border:1px solid #ccc;padding:6px;">{p.nombre}</td>
                <td style="border:1px solid #ccc;padding:6px;">{p.tipo.capitalize()}</td>
                <td style="border:1px solid #ccc;padding:6px;">{nac}</td>
                <td style="border:1px solid #ccc;padding:6px;">{p.pasaporte or '—'}</td>
                <td style="border:1px solid #ccc;padding:6px;">{cad}</td>
                <td style="border:1px solid #ccc;padding:6px;">{p.pais_emision_pasaporte or '—'}</td>
              </tr>
            """
        html += """
            </tbody>
          </table>
        </div>
        """

    # Pie de página
    html += """
        <hr style="margin-top:40px;">
        <footer style="text-align:center;color:#999;font-size:13px;">
          <p>Ruta Multiservice | 9666 Coral Way, Miami, FL 33165</p>
          <p><a href="mailto:info@rutamultiservice.com"
                style="color:#007bff;text-decoration:none;">info@rutamultiservice.com</a></p>
        </footer>
      </div>
    </div>
    """

    # Texto plano (se mantiene igual)
    texto = f"""{encabezado}

🛎️ Detalles del Hotel:
Hotel: {nombre_hotel}
Destino: {destino}
Check-in: {checkin}
Check-out: {checkout}
Total: {total}

🛌 Habitaciones:
"""
    for i, hab in enumerate(habitaciones, 1):
        hab_nom = getattr(hab, 'habitacion_nombre', f'Habitación {i}')
        texto += f"\nHabitación {i} – {hab_nom}\n"
        for p in [p for p in pasajeros if p.habitacion_id == hab.id]:
            nac = p.fecha_nacimiento.strftime('%Y-%m-%d') if p.fecha_nacimiento else '—'
            cad = p.caducidad_pasaporte.strftime('%Y-%m-%d') if p.caducidad_pasaporte else '—'
            texto += (
                f"  • {p.nombre} | Tipo: {p.tipo.capitalize()} | Nac: {nac} | "
                f"Pasaporte: {p.pasaporte or '—'} | Cad: {cad} | País: {p.pais_emision_pasaporte or '—'}\n"
            )

    texto += """
--------------------------------------------
Este correo fue enviado por Ruta Multiservice
9666 Coral Way, Miami, FL 33165
info@rutamultiservice.com
"""
    return asunto, html, texto



def generar_contenido_correo_traslado(reserva, pasajeros):
    """
    Genera asunto, HTML y texto para confirmación de traslado.
    """
    traslado  = reserva.traslado
    encabezado= "Gracias por reservar su traslado con RUTA MULTISERVICE. Estamos procesando su solicitud."
    nombre    = pasajeros.first().nombre if pasajeros.exists() else "Cliente"
    asunto    = f"{'Confirmación' if reserva.estatus=='confirmada' else 'Solicitud'} de Traslado #{reserva.id} – {nombre}"

    html = f"""
    <html><body>
    <p>{encabezado}</p>
    <h3>Traslado</h3>
    <p><b>Origen:</b> {traslado.origen}</p>
    <p><b>Destino:</b> {traslado.destino}</p>
    <p><b>Vehículo:</b> {traslado.vehiculo}</p>
    <p><b>Costo:</b> ${traslado.costo}</p>
    </body></html>
    """

    texto = f"""{encabezado}
Traslado:
Origen: {traslado.origen}
Destino: {traslado.destino}
Vehículo: {traslado.vehiculo}
Costo: ${traslado.costo}
"""
    return asunto, html, texto


def generar_contenido_correo_envio(reserva):
    """
    Genera asunto, HTML y texto para confirmación de envío de paquete.
    """
    envio      = reserva.envio
    items      = envio.items.all()
    encabezado = "Gracias por realizar su envío con RUTA MULTISERVICE. Hemos recibido su solicitud."
    remitente  = envio.remitente
    destinatario = envio.destinatario

    total_valor = sum(item.valor_aduanal for item in items)
    total_peso  = sum(item.peso for item in items)
    total_items = sum(item.cantidad for item in items)
    asunto      = f"📦 Confirmación de Envío #{reserva.id} – {destinatario.nombre_completo}"

    # ... aquí podrías construir html complejo similar al hotel ...
    html = f"<html><body><p>{encabezado}</p>...</body></html>"

    texto = f"""{encabezado}
Remitente: {remitente.nombre_apellido}
Destinatario: {destinatario.nombre_completo}
Items: {total_items}, Peso total: {total_peso} kg, Valor aduanal: ${total_valor}
Total a pagar: ${reserva.precio_total}
"""
    return asunto, html, texto


def generar_contenido_correo_remesa(reserva):
    """
    Genera asunto, HTML y texto para confirmación de remesa.
    """
    remesa    = reserva.remesa
    encabezado= "Gracias por realizar su remesa con RUTA MULTISERVICE. Hemos recibido su solicitud."
    asunto    = f"{'Confirmación' if reserva.estatus=='confirmada' else 'Solicitud'} de Remesa #{reserva.id} – {remesa.destinatario}"

    html = f"<html><body><p>{encabezado}</p>Remitente: {remesa.remitente}<br>Destinatario: {remesa.destinatario}<br>Monto: ${remesa.monto} {remesa.moneda}</body></html>"

    texto = f"""{encabezado}
Remesa:
Remitente: {remesa.remitente}
Destinatario: {remesa.destinatario}
Importe: ${remesa.monto} {remesa.moneda}
"""
    return asunto, html, texto


def generar_contenido_correo_certificado(reserva):
    """
    Genera asunto, HTML y texto para confirmación de certificado de vacaciones.
    """
    cert      = reserva.certificado_vacaciones
    encabezado= "Gracias por solicitar su Certificado de Vacaciones con RUTA MULTISERVICE."
    consumidor = cert.consumidor.nombre if cert.consumidor else "Cliente"
    asunto    = f"{'Confirmación' if reserva.estatus=='confirmada' else 'Solicitud'} de Certificado #{reserva.id} – {consumidor}"

    html = f"<html><body><p>{encabezado}</p>Nombre: {cert.nombre}<br>Solo Adultos: {'Sí' if cert.solo_adultos else 'No'}</body></html>"

    texto = f"""{encabezado}
Certificado:
Nombre: {cert.nombre}
Solo Adultos: {'Sí' if cert.solo_adultos else 'No'}
"""
    return asunto, html, texto

def generar_contenido_solicitud_hotel(reserva, pasajeros, habitaciones):
    """
    Prepara asunto, cuerpo HTML y cuerpo de texto plano para la
    solicitud de revisión de una reserva de hotel, mostrando
    detalles de pasajeros en tablas por habitación.
    """
    # Datos del hotel
    hotel_obj  = reserva.hotel
    hotel_name = hotel_obj.hotel_nombre if hotel_obj and hotel_obj.hotel_nombre else 'No disponible'
    destino    = getattr(hotel_obj.polo_turistico, 'nombre', 'No disponible') if hotel_obj else 'No disponible'

    # Fechas
    raw_fechas = habitaciones[0].fechas_viaje if habitaciones else ''
    fechas     = raw_fechas.split(' - ') if raw_fechas else ['', '']
    checkin    = f"{fechas[0]} 14:00" if fechas[0] else "No disponible"
    checkout   = f"{fechas[1]} 12:00" if len(fechas) > 1 and fechas[1] else "No disponible"

    # Asunto
    asunto = f"📝 Solicitud de Revisión Reserva Hotel #{reserva.id}"

    # HTML de inicio
    html = f"""
    <div style="font-family:'Segoe UI', sans-serif; max-width:700px; margin:40px auto;
                border-radius:12px; overflow:hidden; box-shadow:0 0 10px rgba(0,0,0,0.1); background-color:#f4f6f8;">
      <div style="background:#003366; padding:30px 20px; text-align:center; color:#fff;">
        <img src="https://www.rutamultiservice.com/static/images/ruta_Logo.jpeg"
             alt="Ruta Multiservice" style="width:130px; margin-bottom:15px; border-radius:10px;" />
        <h2 style="margin:0; font-size:24px;">✉️ Solicitud de Reserva Hotel</h2>
        <p style="margin:10px 0 0; font-size:16px; color:#e0e0e0;">
          Le solicitamos amablemente revisar y confirmar los detalles de la siguiente reserva:
        </p>
      </div>
      <div style="padding:30px; background-color:#ffffff;">
        <h3 style="color:#003366; border-bottom:2px solid #dedede; padding-bottom:8px;">🏨 Detalles del Hotel</h3>
        <p><strong>Hotel:</strong> {hotel_name}</p>
        <p><strong>Destino:</strong> {destino}</p>        
        <hr style="margin:30px 0 20px;">
        <h3 style="color:#003366; border-bottom:2px solid #dedede; padding-bottom:8px;">🚩 Habitaciones</h3>
    """

    # Para cada habitación creamos una tabla de pasajeros
    for idx, hab in enumerate(habitaciones, start=1):
        hab_nombre = getattr(hab, 'habitacion_nombre', f'Habitación {idx}')
        html += f"""
        <div style="background:#f8f9fa; padding:20px; border-radius:8px; margin-bottom:20px;">
          <h4 style="margin:0 0 12px; color:#005580;">
            Habitación {idx} – {hab_nombre}
          </h4>
          <table style="width:100%; border-collapse:collapse; margin-bottom:10px;">
            <thead>
              <tr style="background:#e0e7ff;">
                <th style="border:1px solid #ccc; padding:8px; text-align:left;">Nombre</th>
                <th style="border:1px solid #ccc; padding:8px; text-align:left;">Tipo</th>
                <th style="border:1px solid #ccc; padding:8px; text-align:left;">Fecha nac.</th>
                <th style="border:1px solid #ccc; padding:8px; text-align:left;">Pasaporte</th>
                <th style="border:1px solid #ccc; padding:8px; text-align:left;">Caducidad</th>
                <th style="border:1px solid #ccc; padding:8px; text-align:left;">País emisión</th>
              </tr>
            </thead>
            <tbody>
        """
        # filas de pasajeros para esta habitación
        for p in pasajeros.filter(habitacion=hab):
            nac = p.fecha_nacimiento.strftime('%Y-%m-%d') if p.fecha_nacimiento else '—'
            cad = p.caducidad_pasaporte.strftime('%Y-%m-%d') if p.caducidad_pasaporte else '—'
            html += f"""
              <tr>
                <td style="border:1px solid #ccc; padding:6px;">{p.nombre}</td>
                <td style="border:1px solid #ccc; padding:6px;">{p.tipo.capitalize()}</td>
                <td style="border:1px solid #ccc; padding:6px;">{nac}</td>
                <td style="border:1px solid #ccc; padding:6px;">{p.pasaporte or '—'}</td>
                <td style="border:1px solid #ccc; padding:6px;">{cad}</td>
                <td style="border:1px solid #ccc; padding:6px;">{p.pais_emision_pasaporte or '—'}</td>
              </tr>
            """
        html += """
            </tbody>
          </table>
        </div>
        """

    # Pie de página
    html += """
        <hr style="margin-top:40px;">
        <p style="text-align:center; color:#999; font-size:13px;"><em>Equipo Ruta Multiservice</em></p>
      </div>
    </div>
    """

    # Texto plano equivalente (puedes simplificar si no necesitas todo)
    texto = (
        f"Solicitud de Reserva Hotel\n"
        f"Le solicitamos revisar la siguiente reserva:\n\n"
        f"Hotel: {hotel_name}\n"
        f"Destino: {destino}\n"
        f"Check-in: {checkin}\n"
        f"Check-out: {checkout}\n\n"
    )
    for idx, hab in enumerate(habitaciones, start=1):
        hab_nombre = getattr(hab, 'habitacion_nombre', f'Habitación {idx}')
        texto += f"\nHabitación {idx} – {hab_nombre}\n"
        for p in pasajeros.filter(habitacion=hab):
            nac = p.fecha_nacimiento.strftime('%Y-%m-%d') if p.fecha_nacimiento else '—'
            cad = p.caducidad_pasaporte.strftime('%Y-%m-%d') if p.caducidad_pasaporte else '—'
            texto += (
                f"  • {p.nombre} | Tipo: {p.tipo.capitalize()} | Nac: {nac} | "
                f"Pasaporte: {p.pasaporte or '—'} | Cad: {cad} | País: {p.pais_emision_pasaporte or '—'}\n"
            )
    texto += "\nEquipo Ruta Multiservice\n"

    return asunto, html, texto

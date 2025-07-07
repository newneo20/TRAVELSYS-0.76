# apps/backoffice/utils/email_voucher_distal.py

from django.core.mail import EmailMessage
from django.conf import settings
import os
import asyncio

from apps.backoffice.utils.pdf_voucher_distal import generar_voucher_pdf_distal


def enviar_voucher_hotel_distal(reserva):
    print(f"📨 Preparando envío de voucher para reserva ID {reserva.id}...")

    # 1. Definir ruta para guardar PDF
    ruta_pdf = os.path.join(settings.BASE_DIR, 'documentos/voucher')
    os.makedirs(ruta_pdf, exist_ok=True)
    print(f"📁 Carpeta para PDF: {ruta_pdf}")

    nombre_archivo_pdf = f'voucher-{reserva.id}.pdf'
    ruta_completa_pdf = os.path.join(ruta_pdf, nombre_archivo_pdf)
    print(f"📄 Archivo PDF que se va a generar: {ruta_completa_pdf}")

    # 2. URL interna para renderizar voucher
    url_voucher = f'http://127.0.0.1:8000/backoffice/reserva/{reserva.id}/preview_voucher_distal/'
    print(f"🌐 URL del voucher: {url_voucher}")

    # 3. Generar PDF con Playwright
    print("🧾 Generando el PDF del voucher desde la vista previa...")
    try:
        asyncio.run(generar_voucher_pdf_distal(reserva.id, url_voucher, ruta_completa_pdf))
        print("✅ PDF generado correctamente.")
    except Exception as e:
        print(f"❌ Error generando el PDF: {e}")
        return

    # 4. Enviar correo
    subject = f"Voucher de reserva #{reserva.numero_confirmacion or reserva.id}"
    cuerpo = f"Adjunto encontrará el voucher correspondiente a su reserva #{reserva.numero_confirmacion or reserva.id}."
    print(f"✉️ Preparando correo para: {reserva.email_empleado}")
    print(f"Asunto: {subject}")

    try:
        mensaje = EmailMessage(
            subject,
            cuerpo,
            settings.DEFAULT_FROM_EMAIL,
            [reserva.email_empleado]
        )
        mensaje.attach_file(ruta_completa_pdf)
        mensaje.send()
        print("✅ Correo enviado exitosamente.")
    except Exception as e:
        print(f"❌ Error enviando el correo: {e}")

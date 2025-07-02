# funciones_externas.py

# -------------------------
# Imports de la librería estándar de Python
# -------------------------
import os
import smtplib
from decimal import Decimal
from datetime import datetime
from io import BytesIO
from urllib import request as urllib_request

# -------------------------
# Imports de terceros (instalados vía pip o similares)
# -------------------------
import pandas as pd  # type: ignore
from openpyxl import load_workbook  # type: ignore

# -------------------------
# Imports de Django
# -------------------------
from django.shortcuts import get_object_or_404, render  # type: ignore
from django.http import HttpResponse  # type: ignore

# -------------------------
# Imports de ReportLab (generación de PDF)
# -------------------------
from reportlab.lib import colors  # type: ignore
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib.units import inch, cm  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore
from reportlab.platypus import ( # type: ignore
    SimpleDocTemplate,
    Table,
    TableStyle,
    Image,
    Paragraph,
    Spacer,
    Flowable,
)  # type: ignore
from reportlab.pdfgen import canvas # type: ignore

# -------------------------
# Imports para envío de correos
# -------------------------
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# -------------------------
# Imports locales (modelos de tu app)
# -------------------------
from .models import Reserva, Pasajero, HabitacionReserva, Oferta





# --------- Grupo de funciones relacionadas con la gestión de habitaciones y reservas ---------

# Función para determinar posibles combinaciones de habitaciones
# basado en la cantidad de adultos, niños y la capacidad máxima
def combinacion_habitaciones(adultos, ninos, max_capacidad):
    # Definir las combinaciones posibles según la tabla
    combinaciones = [
        {"nombre": "Sencilla", "adultos": 1, "ninos": 0},
        {"nombre": "Sencilla + 1", "adultos": 1, "ninos": 1},
        {"nombre": "Sencilla + 2", "adultos": 1, "ninos": 2},
        {"nombre": "Doble", "adultos": 2, "ninos": 0},
        {"nombre": "Doble + 1", "adultos": 2, "ninos": 1},
        {"nombre": "Doble + 2", "adultos": 2, "ninos": 2},
        {"nombre": "Triple", "adultos": 3, "ninos": 0},
        {"nombre": "Triple + 1", "adultos": 3, "ninos": 1},
    ]
    
    # Filtrar combinaciones que cumplan con los criterios dados
    posibles_combinaciones = []
    for combinacion in combinaciones:
        total_personas = combinacion["adultos"] + combinacion["ninos"]
        if combinacion["adultos"] <= adultos and combinacion["ninos"] <= ninos and total_personas <= max_capacidad:
            posibles_combinaciones.append(
                (combinacion["nombre"], combinacion["adultos"], combinacion["ninos"])
            )
    
    return posibles_combinaciones


# Función para verificar si un intervalo de fechas está dentro de otro
def ChequearIntervalos(intervaloA, intervaloB):
    # Separar las fechas de los intervalos
    fecha_inicioA, fecha_finA = intervaloA.split(' - ')
    fecha_inicioB, fecha_finB = intervaloB.split(' - ')
    
    # Convertir las fechas a objetos datetime
    fecha_inicioA = datetime.strptime(fecha_inicioA, '%Y-%m-%d')
    fecha_finA = datetime.strptime(fecha_finA, '%Y-%m-%d')
    fecha_inicioB = datetime.strptime(fecha_inicioB, '%Y-%m-%d')
    fecha_finB = datetime.strptime(fecha_finB, '%Y-%m-%d')
    
    # Verificar si el intervalo B está dentro del intervalo A
    return fecha_inicioB >= fecha_inicioA and fecha_finB <= fecha_finA


# Función para leer los datos de un archivo de Excel y convertirlos en una lista de diccionarios
def leer_datos_hoteles(ruta_archivo):
    # Leer los datos usando pandas
    df = pd.read_excel(ruta_archivo, sheet_name='Sheet1', header=0)
    
    hoteles = []
    hotel_info = None

    for index, row in df.iterrows():
        # Ignorar filas que son completamente NaN
        if row.isnull().all():
            continue
        
        # Iniciar un nuevo hotel si hay datos en la columna 'Nombre del Hotel'
        if pd.notna(row['Nombre del Hotel']) and row['Nombre del Hotel'] != 'Nombre del Hotel':
            if hotel_info is not None:
                hoteles.append(hotel_info)
                    
            hotel_info = {
                "nombre_hotel": row['Nombre del Hotel'],
                "cantidad_temporadas": int(row['Cantidad de Temporadas']),
                "cantidad_habitaciones": int(row['Cantidad de Habitaciones']),
                "categoria": int(row['Categoria']),
                "habitaciones": []
            }
        
        # Verificar si el hotel_info está inicializado correctamente
        if hotel_info is not None and pd.notna(row['Tipo Habitacion']):
            habitacion_info = {
                "disponible": row.get('Disponible', False),
                "codigo": row.get('Codigo', ''),
                "tipo_habitacion": row.get('Tipo Habitacion', ''),
                "temporada": row.get('Temporada', ''),
                "booking_window": row.get('Booking Window', ''),
                "sencilla": row.get('Sencilla', ''),
                "doble": row.get('Doble', ''),
                "triple": row.get('Triple', ''),
                "primer_nino": row.get('Primer Niño', ''),
                "segundo_nino": row.get('Segundo Niño', ''),
                "un_adulto_con_ninos": row.get('Un Adulto Con Niños', ''),
                "primer_nino_con_un_adulto": row.get('Primer Niño con 1 Adulto', ''),
                "segundo_nino_con_un_adulto": row.get('Segundo Niño con 1 Adulto', ''),
                "edad_nino": row.get('Edad Niño', ''),
                "edad_infante": row.get('Edad Infante', ''),
                "noches_minimas": row.get('Noches Minimas', ''),
                "tipo_fee": row.get('Tipo Fee', ''),                  
                "fee_doble": row.get('Fee Doble', ''),                
                "fee_triple": row.get('Fee Triple', ''),              
                "fee_sencilla": row.get('Fee Sencilla', ''),          
                "fee_primer_nino": row.get('Fee Primer Niño', ''),    
                "fee_segundo_nino": row.get('Fee Segundo Niño', '')   
            }
            hotel_info["habitaciones"].append(habitacion_info)

    # Agregar el último hotel
    if hotel_info is not None:
        hoteles.append(hotel_info)

    return hoteles


# Función para convertir un número de estrellas en una representación visual de estrellas
def convertir_estrellas(categoria):
    try:
        numero_estrellas = int(categoria)
        return "★" * numero_estrellas
    except ValueError:
        return categoria


# --------- Grupo de funciones relacionadas con generación de PDFs y correos ---------
# Función para generar el contenido del correo de confirmación de reserva
def generar_contenido_correo(reserva, pasajeros, habitaciones, encabezado):
    
    primer_pasajero = next(p for p in pasajeros if p.habitacion.reserva.id == reserva.id)

    
    if reserva.estatus == 'confirmada':
        asunto = f"Confirmacion de Reserva {reserva.id} ({primer_pasajero.nombre})"
    else:
        asunto = f"Solicitud de Reserva {reserva.id} ({primer_pasajero.nombre})"
    
    fechas_viaje = habitaciones[0].fechas_viaje if habitaciones[0].fechas_viaje else ''
    fechas_viaje_split = fechas_viaje.split(' - ') if fechas_viaje else ['', '']
    checkin = fechas_viaje_split[0] + " 14:00" if fechas_viaje_split[0] else ''
    checkout = fechas_viaje_split[1] + " 12:00" if fechas_viaje_split[1] else ''

    # Detalles de la reserva
    detalles_reserva = f"""
    <p><b>Hotel:</b> {reserva.hotel.hotel_nombre} ({convertir_estrellas(reserva.hotel.categoria)})</p>
    <p><b>Dirección:</b> {reserva.hotel.direccion}</p>
    <p><b>Check-in:</b> {checkin}</p>
    <p><b>Check-out:</b> {checkout}</p>
    <p><b>Total a pagar:</b> ${reserva.precio_total}</p>
    """

    if reserva.estatus == 'confirmada':
        detalles_reserva += f"<p><b>Número de Confirmación:</b> {reserva.numero_confirmacion}</p>"

    detalles_habitaciones = ""
    for i, habitacion in enumerate(habitaciones, 1):
        adults = ' / '.join(p.nombre for p in pasajeros if p.habitacion == habitacion and p.tipo == 'adulto')
        children = ' / '.join(p.nombre for p in pasajeros if p.habitacion == habitacion and p.tipo == 'niño')
        
        detalles_habitaciones = f"""
        <h2>Habitación {i} - {habitacion.habitacion_nombre}</h2>
        <p><b>Adultos:</b> {habitacion.adultos} ({adults})</p>
        """
        if habitacion.ninos > 0:
            detalles_habitaciones += f"<p><b>Niños:</b> {habitacion.ninos} ({children})</p>"

    cuerpo_html = f"""
    <html>
    <body>
    {encabezado}
    <h2>Detalles de la Reserva:</h2>
    {detalles_reserva}
    {detalles_habitaciones}
    </body>
    </html>
    """

    cuerpo_texto = f"""
    {encabezado}
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



# -----------------------------------------------------------------------------
# Función de ejemplo para convertir la categoría del hotel a estrellas:
def convertir_estrellas(categoria):
    """
    Ejemplo de función para convertir la categoría numérica 
    en una cadena con estrellas, o en texto descriptivo.
    Ajusta según tu lógica real.
    """
    if categoria == 5:
        return "★★★★★"
    elif categoria == 4:
        return "★★★★"
    elif categoria == 3:
        return "★★★"
    else:
        return f"{categoria} Estrellas"

# -----------------------------------------------------------------------------
# Clase para dibujar la imagen del logo en forma circular:
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
        # Creamos el path (contorno) en forma de círculo
        p = c.beginPath()
        p.circle(self.width/2, self.height/2, min(self.width, self.height)/2)
        # Recortamos la salida a ese path
        c.clipPath(p, fill=1, stroke=0)
        # Dibujamos la imagen dentro del recorte
        c.drawImage(
            self.img_path,
            0,
            0,
            width=self.width,
            height=self.height,
            preserveAspectRatio=True
        )
        c.restoreState()

# -----------------------------------------------------------------------------
# Función para formatear la fecha con el mes en español (opcional):
MESES_EN_ESPANOL = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre'
}

def formatear_fecha_en_espanol(fecha):
    mes_nombre = MESES_EN_ESPANOL[fecha.month]
    return fecha.strftime(f'{mes_nombre}/%d/%Y')

# -----------------------------------------------------------------------------
# Función principal para generar el voucher (con logo circular, zebra lines, etc.):
def generar_voucher_pdf(reserva, pasajeros, habitaciones, agencia):
    """
    Genera un PDF de voucher con mejoras visuales y un logo circular.
    Retorna la ruta del archivo creado.
    """
    # Obtener la ruta absoluta del directorio del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Crear la carpeta 'documentos/voucher' si no existe
    documentos_dir = os.path.join(base_dir, 'documentos', 'voucher')
    if not os.path.exists(documentos_dir):
        os.makedirs(documentos_dir)

    # Crear el nombre del archivo con el ID de la reserva
    nombre_archivo = f"voucher-{reserva.id}.pdf"
    
    # Ruta completa del archivo
    archivo_pdf = os.path.join(documentos_dir, nombre_archivo)
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        archivo_pdf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=18
    )
    
    elements = []
    
    # Definir colores personalizados
    color_naranja = colors.HexColor("#F37720")
    color_gris_oscuro = colors.HexColor("#333333")
    color_blanco = colors.white
    color_gris_claro = colors.HexColor("#F0F0F0")
    color_zebra = colors.HexColor("#FAFAFA")  # Para "zebra lines"

    # Estilos base
    styles = getSampleStyleSheet()
    
    # Añadir estilos personalizados
    styles.add(ParagraphStyle(
        name='Titulo',
        fontSize=18,
        textColor=color_gris_oscuro,
        spaceAfter=12,
        alignment=1,  # centrado
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name='Subtitulo',
        fontSize=14,
        textColor=color_naranja,
        spaceAfter=6,
        alignment=1,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name='TextoNormal',
        fontSize=10,
        textColor=color_gris_oscuro,
        spaceAfter=6,
        alignment=1  # centrado
    ))

    # Logo circular
    logo_path = os.path.join(os.path.dirname(__file__), '../usuarios/static/usuarios/logo.jpeg')
    logo = CircularImage(logo_path, width=1.5*inch, height=1.5*inch)

    # Verificar si agencia es un diccionario, si no lo es, crear uno por defecto
    if isinstance(agencia, str):
        agencia = {
            'nombre': agencia,
            'direccion': 'Dirección no proporcionada',
            'usuario': 'Usuario no proporcionado',
            'email': 'info@rutamultiservice.com'
        }

    # Información de la agencia
    agencia_info = [
        [Paragraph(agencia['direccion'], styles['TextoNormal'])],        
        [Paragraph(f"Email: {agencia['email']}", styles['TextoNormal'])],
        [Paragraph(f"Traza tu ruta, nosotros te llevamos.", styles['TextoNormal'])]
    ]

    # Tabla con logo circular a la izquierda y la info de agencia a la derecha
    t = Table([
        [logo, Table(agencia_info)]
    ], colWidths=[1.5*inch, 3.5*inch])

    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), color_gris_claro),
        ('GRID', (0, 0), (-1, -1), 0, color_gris_claro)
    ]))

    elements.append(t)
    elements.append(Spacer(1, 0.4*inch))
    
    # Título del voucher
    elements.append(Paragraph("VOUCHER DE SERVICIOS", styles['Titulo']))
    elements.append(Spacer(1, 0.3*inch))

    # Fechas de checkin y checkout
    if habitaciones and habitaciones[0].fechas_viaje:
        fechas_viaje_split = habitaciones[0].fechas_viaje.split(' - ')
    else:
        fechas_viaje_split = ['', '']
    checkin = (fechas_viaje_split[0] + " 14:00") if len(fechas_viaje_split) > 0 and fechas_viaje_split[0] else ''
    checkout = (fechas_viaje_split[1] + " 12:00") if len(fechas_viaje_split) > 1 and fechas_viaje_split[1] else ''

    # Información del hotel
    hotel_info = [
        [
            Paragraph("<b>Hotel</b>", styles['TextoNormal']), 
            Paragraph(reserva.hotel.hotel_nombre, styles['TextoNormal']), 
            Paragraph(convertir_estrellas(reserva.hotel.categoria), styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Dirección</b>", styles['TextoNormal']), 
            Paragraph(reserva.hotel.direccion, styles['TextoNormal']), 
            ''
        ],
        [
            Paragraph("<b>Teléfono</b>", styles['TextoNormal']), 
            Paragraph(str(reserva.hotel.telefono), styles['TextoNormal']), 
            ''
        ],
        [
            Paragraph("<b>Check-in</b>", styles['TextoNormal']), 
            Paragraph(checkin, styles['TextoNormal']), 
            ''
        ],
        [
            Paragraph("<b>Check-out</b>", styles['TextoNormal']), 
            Paragraph(checkout, styles['TextoNormal']), 
            ''
        ]
    ]

    # Agregar la línea de confirmación si está confirmada
    if getattr(reserva, 'estatus', '') == 'confirmada':
        hotel_info.append([
            Paragraph("<b>Número de Confirmación</b>", styles['TextoNormal']), 
            Paragraph(reserva.numero_confirmacion, styles['TextoNormal']), 
            ''
        ])
    
    # Tabla principal de info del hotel
    t = Table(hotel_info, colWidths=[2*inch, 3*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), color_naranja),
        ('TEXTCOLOR', (0,0), (-1,0), color_blanco),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), color_gris_claro),
        ('GRID', (0,0), (-1,-1), 1, color_blanco),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.4*inch))

    # Info de las habitaciones (zebra lines en sus filas)
    for i, habitacion in enumerate(habitaciones, 1):
        # Filtrar adultos y niños
        adults = [p.nombre for p in pasajeros if p.habitacion.id == habitacion.id and p.tipo == 'adulto']
        children = [p.nombre for p in pasajeros if p.habitacion.id == habitacion.id and p.tipo == 'niño']

        # Estructura de datos
        hab_info = [
            [
                Paragraph(f"<b>HABITACIÓN {i}</b>", styles['TextoNormal']), 
                Paragraph("<b>PAX</b>", styles['TextoNormal']),
                Paragraph("<b>DETALLES</b>", styles['TextoNormal'])
            ],
            ["Tipo", "", habitacion.habitacion_nombre],
            ["Adultos", f"{habitacion.adultos}", ' / '.join(adults)],
            ["Niños", f"{habitacion.ninos}", ' / '.join(children)]
        ]

        # Creamos la tabla de la habitación
        t_hab = Table(hab_info, colWidths=[2*inch, 1*inch, 5*inch])
        t_hab.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), color_naranja),
            ('TEXTCOLOR', (0,0), (-1,0), color_blanco),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (1,1), (-1,-1), color_gris_claro),
            ('GRID', (0,0), (-1,-1), 1, color_blanco),
        ]))

        # Aplicar zebra lines a las filas de datos (excluyendo encabezado)
        for row_idx in range(1, len(hab_info)):
            if row_idx % 2 == 1:
                t_hab.setStyle(TableStyle([
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), color_zebra)
                ]))

        elements.append(t_hab)
        elements.append(Spacer(1, 0.4*inch))
    
    # Pie de página / Mensaje final
    footer_style = ParagraphStyle(
        'FooterStyle', 
        fontSize=10, 
        alignment=1,  
        fontName="Helvetica-Bold",  
        textColor=color_gris_oscuro,
        spaceBefore=10,  
        spaceAfter=10
    )
    
    footer = Paragraph("Confirmado por RUTA MULTISERVICE. ¡Gracias por su preferencia!", footer_style)
    elements.append(Spacer(1, 0.5*inch))
    elements.append(footer)

    # Generar el documento PDF
    doc.build(elements)

    # Retornar la ruta del archivo generado
    return archivo_pdf


# -----------------------------------------------------------------------------
# Función para generar la factura con logo circular y zebra lines:
def generar_factura_pdf(reserva, pasajeros, habitaciones, agencia):
    """
    Genera un PDF de factura con logo circular, estilos y zebra lines.
    Retorna la ruta del archivo PDF.
    """
    # Obtener la ruta absoluta del directorio
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Carpeta de facturas
    facturas_dir = os.path.join(base_dir, 'documentos', 'facturas')
    if not os.path.exists(facturas_dir):
        os.makedirs(facturas_dir)

    # Nombre del archivo (ej: factura-12.pdf)
    nombre_archivo = f"factura-{reserva.id}.pdf"
    archivo_pdf = os.path.join(facturas_dir, nombre_archivo)

    doc = SimpleDocTemplate(
        archivo_pdf, 
        pagesize=letter,
        rightMargin=36, 
        leftMargin=36,
        topMargin=36, 
        bottomMargin=18
    )
    
    elements = []
    
    # Colores
    color_gris_claro = colors.HexColor("#F0F0F0")
    color_gris_oscuro = colors.HexColor("#333333")
    color_zebra = colors.HexColor("#FAFAFA")

    # Estilos base
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Titulo',
        fontSize=18,
        textColor=color_gris_oscuro,
        spaceAfter=12,
        alignment=1,  # centrado
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name='TextoNormal',
        fontSize=10,
        textColor=color_gris_oscuro,
        spaceAfter=6,
        alignment=0  # izquierda
    ))

    # Logo circular
    logo_path = os.path.join(os.path.dirname(__file__), '../usuarios/static/usuarios/logo.jpeg')
    logo = CircularImage(logo_path, 1.5*inch, 1.5*inch)

    # Chequeo de agencia
    if isinstance(agencia, str):
        agencia = {
            'nombre': agencia,
            'direccion': 'Dirección no proporcionada',
            'usuario': 'Usuario no proporcionado',
            'email': 'Email no proporcionado'
        }

    # Info de la factura
    from datetime import datetime
    factura_info = [
        [Paragraph(f"<b>Factura No:</b> FAC-R{reserva.id}", styles['TextoNormal'])],
        [Paragraph(f"<b>Fecha:</b> {formatear_fecha_en_espanol(datetime.now())}", styles['TextoNormal'])],
        [Paragraph(f"<b>Confirmación:</b> {reserva.numero_confirmacion}", styles['TextoNormal'])]
    ]

    # Info del hotel
    cliente_info = [
        [Paragraph(f"<b>Hotel:</b> {reserva.hotel.hotel_nombre}", styles['TextoNormal'])],
        [Paragraph(f"<b></b> {reserva.hotel.polo_turistico}", styles['TextoNormal'])],
        [Paragraph(f"<b></b> {reserva.hotel.direccion}", styles['TextoNormal'])],
        [Paragraph(f"<b></b> {reserva.hotel.telefono}", styles['TextoNormal'])]
    ]

    # Tabla arriba con logo, hotel y factura
    t = Table([
        [logo, Table(cliente_info), Table(factura_info)]
    ], colWidths=[1.5*inch, 3.5*inch, 2*inch])

    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), color_gris_claro),
        ('GRID', (0, 0), (-1, -1), 0, color_gris_claro)
    ]))

    elements.append(t)
    elements.append(Spacer(1, 0.4*inch))
    
    # Título central
    elements.append(Paragraph("FACTURA / INVOICE", styles['Titulo']))
    elements.append(Spacer(1, 0.3*inch))

    # Detalles de los clientes
    cliente_info = [
        [Paragraph("<b>Detalles de los Clientes / Customer Details</b>", styles['TextoNormal'])],
        [Paragraph(f"<b>Nombre / Name:</b> {', '.join(p.nombre for p in pasajeros if p.nombre)}", styles['TextoNormal'])],
        [Paragraph(f"<b>Correo / Email:</b> {''.join(p.email if p.email else '' for p in pasajeros)}", styles['TextoNormal'])],
        [Paragraph(f"<b>Teléfono / Phone #:</b> {''.join(p.telefono if p.telefono else '' for p in pasajeros)}", styles['TextoNormal'])]
    ]
    t_cliente = Table(cliente_info, colWidths=[6.5*inch])
    t_cliente.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT')
    ]))
    elements.append(t_cliente)
    elements.append(Spacer(1, 0.3*inch))

    # Tabla de detalles (habitaciones, noches, PAX, precio)
    detalles = [
        [
            Paragraph("<b>Descripción / Description</b>", styles['TextoNormal']),
            Paragraph("<b>Cantidad / Quantity</b>", styles['TextoNormal']),
            Paragraph("<b>Cantidad de Personas / PAX</b>", styles['TextoNormal']),
            Paragraph("<b>Precio Total / Total Price</b>", styles['TextoNormal'])
        ]
    ]

    checkin = ''
    checkout = ''
    total_precio = 0

    for habitacion in habitaciones:
        fechas_viaje = habitacion.fechas_viaje
        fecha_inicio, fecha_fin = fechas_viaje.split(" - ")
        
        checkin = fecha_inicio
        checkout = fecha_fin

        formato_fecha = "%Y-%m-%d"
        inicio = datetime.strptime(fecha_inicio, formato_fecha)
        fin = datetime.strptime(fecha_fin, formato_fecha)
        noches = (fin - inicio).days

        detalles.append([
            Paragraph(f"Habitación: {habitacion.habitacion_nombre}", styles['TextoNormal']),
            f"{noches} noches / nights",
            f"{habitacion.adultos + habitacion.ninos}",
            f"${habitacion.precio:.2f}"
        ])
        total_precio += habitacion.precio

    # Fila total
    detalles.append([
        Paragraph("<b>Total</b>", styles['TextoNormal']),
        "", 
        "", 
        Paragraph(f"<b>${total_precio:.2f}</b>", styles['TextoNormal'])
    ])

    t_detalles = Table(detalles, colWidths=[3*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    t_detalles.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Último renglón (total) con color de fondo
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey)
    ]))

    # Zebra lines para las filas intermedias
    for row_idx in range(1, len(detalles) - 1):
        if row_idx % 2 == 1:
            t_detalles.setStyle(TableStyle([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), color_zebra)
            ]))

    elements.append(t_detalles)
    elements.append(Spacer(1, 0.3*inch))

    # Check-in / Check-out
    if checkin and checkout:
        detalles_estancia = [
            [Paragraph(f"<b>Check-in:</b> {formatear_fecha_en_espanol(datetime.strptime(checkin, '%Y-%m-%d'))} 14:00", styles['TextoNormal'])],
            [Paragraph(f"<b>Check-out:</b> {formatear_fecha_en_espanol(datetime.strptime(checkout, '%Y-%m-%d'))} 12:00", styles['TextoNormal'])]
        ]
        t_estancia = Table(detalles_estancia)
        elements.append(t_estancia)
        elements.append(Spacer(1, 0.3*inch))

    # Nota final o CTA
    nota_info = [
        [Paragraph("Para cualquier consulta sobre esta factura, por favor contacte a comercial@rutamultiservice.com", styles['TextoNormal'])],
        [Paragraph("For any inquiries regarding this invoice, please contact comercial@rutamultiservice.com", styles['TextoNormal'])],
        [Paragraph("<b>¡Gracias por su preferencia!</b>", styles['TextoNormal'])]
    ]
    t_nota = Table(nota_info)
    elements.append(t_nota)

    # Generar el PDF
    doc.build(elements)
    return archivo_pdf











# Función para enviar el correo de confirmación de reserva
def enviar_correo(reserva, pasajeros, habitaciones, to_email, encabezado):
    # Generar el contenido del correo (en texto y HTML)
    asunto, cuerpo_html, cuerpo_texto = generar_contenido_correo(reserva, pasajeros, habitaciones, encabezado)

    # Crear el mensaje de correo
    from_email = "admin@travel-sys.com"
    password = "Z6d*ibHDAyJTmLNq%kvQNx"
    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = from_email
    mensaje["To"] = to_email

    # Añadir el contenido del correo en texto plano y HTML
    parte_texto = MIMEText(cuerpo_texto, "plain")
    parte_html = MIMEText(cuerpo_html, "html")
    mensaje.attach(parte_texto)
    mensaje.attach(parte_html)

    # SOLO adjuntar PDFs si la reserva tiene número de confirmación
    if getattr(reserva, 'numero_confirmacion', None):
        # Generar los PDF (voucher y factura)
        voucher = generar_voucher_pdf(reserva, pasajeros, habitaciones, encabezado)
        factura = generar_factura_pdf(reserva, pasajeros, habitaciones, encabezado)

        # Adjuntar el voucher PDF
        voucher_filename = f"voucher-{reserva.id}.pdf"
        with open(voucher, "rb") as adjunto_voucher:
            parte_adjunto_voucher = MIMEApplication(adjunto_voucher.read(), _subtype="pdf")
            parte_adjunto_voucher.add_header(
                "Content-Disposition", 
                "attachment", 
                filename=voucher_filename
            )
            mensaje.attach(parte_adjunto_voucher)

        # Adjuntar la factura PDF
        factura_filename = f"factura-{reserva.id}.pdf"
        with open(factura, "rb") as adjunto_factura:
            parte_adjunto_factura = MIMEApplication(adjunto_factura.read(), _subtype="pdf")
            parte_adjunto_factura.add_header(
                "Content-Disposition", 
                "attachment", 
                filename=factura_filename
            )
            mensaje.attach(parte_adjunto_factura)

    try:
        # Enviar el correo usando el servidor SMTP de Outlook/Office 365
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as servidor:
            servidor.starttls()  # Inicia la conexión segura (STARTTLS)
            servidor.login(from_email, password)  # Autenticación
            servidor.sendmail(from_email, to_email, mensaje.as_string())
            print("Correo enviado exitosamente desde Outlook/Office365")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


# --------- Grupo de funciones para cálculos y reportes de reservas ---------

# Función para calcular el precio total de reservas por mes en un año determinado
def calcular_precio_total_por_mes(reservas):
    año_actual = datetime.now().year
    precios_por_mes = [0] * 12
    reservas_del_año = reservas.filter(fecha_reserva__year=año_actual)
    
    for reserva in reservas_del_año:
        mes_reserva = reserva.fecha_reserva.month - 1
        precios_por_mes[mes_reserva] += float(reserva.precio_total)
    
    return precios_por_mes


# Función para contar el número de reservas por mes en un año determinado
def contar_reservas_por_mes(reservas):
    año_actual = datetime.now().year
    reservas_por_mes = [0] * 12
    reservas_del_año = reservas.filter(fecha_reserva__year=año_actual)
    
    for reserva in reservas_del_año:
        mes_reserva = reserva.fecha_reserva.month - 1
        reservas_por_mes[mes_reserva] += 1
    
    return reservas_por_mes


# Función para obtener un diccionario con un lista de hoteles y su oferta más barata
def obtener_ofertas_mas_baratas(request, lista_hoteles, cant_personas, cantidad_dias_reserva, fechas_viaje):
    """
    Calcula las ofertas más baratas basadas en el número de personas, noches y temporada de viaje.
    """
    # Asegúrate de que el usuario está autenticado
    if request.user.is_authenticated:
        fee_usuario = request.user.fee_hotel or 0  # Captura el valor del campo fee_hotel o usa 0 si es None
    else:
        fee_usuario = 0  # Opcional: manejar usuarios no autenticados

    # Parsear las fechas de viaje
    fecha_inicio_str, fecha_fin_str = fechas_viaje.split(" - ")
    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")

    ofertas_baratas_dict = {}

    for hotel in lista_hoteles:
        ofertas = Oferta.objects.filter(hotel=hotel, disponible=True)
        precios_calculados = []

        for oferta in ofertas:
            try:
                # Verificar si la temporada contiene un rango de fechas
                if oferta.temporada and " - " in oferta.temporada:
                    temporada_inicio_str, temporada_fin_str = oferta.temporada.split(" - ")
                    temporada_inicio = datetime.strptime(temporada_inicio_str, "%Y-%m-%d")
                    temporada_fin = datetime.strptime(temporada_fin_str, "%Y-%m-%d")

                    # Validar si la fecha de viaje cae dentro de la temporada
                    if temporada_inicio <= fecha_inicio and temporada_fin >= fecha_fin:
                        # Convertir fee_doble a número, usar 1 por defecto si es None o no es válido
                        fee_doble = float(oferta.fee_doble or 1)

                        # Calcular el precio total según la cantidad de personas y noches
                        precio_unitario = float(oferta.doble or 0)  # Usamos el precio de la temporada válida

                        # Cálculo del precio total
                        precio_base = (precio_unitario + fee_doble)
                        precio_usuario = fee_usuario
                        precio_total = precio_base + precio_usuario

                        precios_calculados.append(precio_total)
            except (ValueError, TypeError) as e:
                print(f"Error procesando oferta: {e}")
                continue  # Ignorar ofertas con temporadas inválidas

        # Encontrar el precio más barato entre los calculados
        oferta_mas_barata = min(precios_calculados) if precios_calculados else None
        ofertas_baratas_dict[hotel.id] = oferta_mas_barata

    return ofertas_baratas_dict

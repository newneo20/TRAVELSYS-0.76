# booking/views.py
# ──────────────────────────────
# Standard library
# ──────────────────────────────
import json
import os
import time
import html
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# ──────────────────────────────
# Third-party
# ──────────────────────────────
import requests

# ──────────────────────────────
# Django
# ──────────────────────────────
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import F, Q, Sum as DjangoSum
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.utils.safestring import mark_safe

# ──────────────────────────────
# Local apps
# ──────────────────────────────
from apps.booking.parsers_1way2italy import parse_hotel_avail_rs
from apps.booking.xml_builders_1way2italy import build_hotel_avail_xml


@csrf_protect
@require_POST
def crear_destinatario(request):
    ...


# ──────────────────────────────
# Project-specific imports
# ──────────────────────────────
from apps.backoffice.models import (
    PoloTuristico, Hotel, Habitacion, Oferta, HabitacionOpcion,
    Reserva, HabitacionReserva, Pasajero, OfertasEspeciales, Remesa,
    TasaCambio, Ubicacion, Traslado, Transportista, Vehiculo, Envio,
    ItemEnvio, Remitente, Destinatario, HotelImportado, Proveedor
)
from apps.backoffice.funciones_externas import (
    calcular_precio_total_por_mes,
    contar_reservas_por_mes,
    ChequearIntervalos,
    obtener_ofertas_mas_baratas
)
from apps.usuarios.models import CustomUser
from .forms import (
    PoloTuristicoForm, ProveedorForm, CadenaHoteleraForm,
    ReservaForm, PasajeroForm, HabitacionForm, OfertasEspecialesForm
)
from . import funciones_externas_booking


@login_required
def check_session_status(request):
    # Si el usuario está autenticado, devuelve "active", de lo contrario "inactive"
    return JsonResponse({'status': 'active'})

# ================================================================================================== #
# ---------------------------------------- Sección: Dashboard -------------------------------------- #
# ================================================================================================== #
@login_required
def en_desarrollo(request):
    return render(request, 'booking/en_desarrollo.html')

@login_required
def en_mantenimiento(request):
    return render(request, 'booking/en_mantenimiento.html') 

# Vista para obtener los datos del dashboard de administración
@login_required
def admin_dashboard_data(request):    
    reservas = Reserva.objects.all()  # Obtener todas las reservas
    ofertas_especiales = OfertasEspeciales.objects.all()
    ganancias_totales = 0
    
    # Calcular las ganancias totales de todas las reservas
    for reserva in reservas:
        ganancias_totales += reserva.precio_total

    # Preparar los datos a enviar en formato JSON
    data = {
        'total_hotels': Hotel.objects.count(),  # Total de hoteles
        'total_rooms': Habitacion.objects.count(),  # Total de habitaciones
        'total_reservations': Reserva.objects.filter(estatus='confirmada').count(),  # Total de reservas confirmadas
        'recent_reservations': list(Reserva.objects.order_by('-fecha_reserva')[:5].values()),  # Reservas recientes
        'recent_hotels': list(Hotel.objects.order_by('-id')[:5].values()),  # Hoteles recientes
        'ganancias_totales': ganancias_totales,  # Ganancias totales
        'ofertas_especiales': ofertas_especiales
    }
    return JsonResponse(data)


@login_required
@require_GET
def cargar_ofertas_especiales(request):
    try:
        ofertas = OfertasEspeciales.objects.filter(disponible=True)
        html = render_to_string('booking/partials/_bloque_ofertas.html', {'ofertas': ofertas})
        return JsonResponse({'html': html})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def cargar_reservas_recientes(request):
    tipo = request.GET.get('tipo', 'todos')
    user_agencia = request.user.agencia

    # Filtro base (por agencia)
    reservas = Reserva.objects.filter(agencia=user_agencia)

    if tipo != 'todos':
        reservas = reservas.filter(tipo=tipo)

    reservas = reservas.order_by('-fecha_reserva')[:10]  # Los 10 más recientes

    html = render_to_string('booking/partials/_bloque_reservas_recientes.html', {'reservas': reservas})
    return JsonResponse({'html': html})



@login_required
def user_dashboard(request):
    usuario = request.user

    # 1) Seguridad: si agencia es None, lo convertimos a string vacío
    agencia_raw = usuario.agencia or ''
    agencia = agencia_raw.strip()

    # 2) Comprobamos tras el strip
    if not agencia:
        messages.error(request, "El nombre de usuario no está definido.")
        return redirect('home')

    # 3) Usamos 'agencia' saneada en las consultas
    
    reservas = Reserva.objects.filter(agencia=usuario.agencia)
    remesas = Remesa.objects.filter(
        reserva__nombre_usuario__iexact=agencia,
        reserva__tipo='remesas'
    )

    # resto de tu lógica...
    ofertas_especiales = OfertasEspeciales.objects.filter(disponible=True)
    total_hotels = Hotel.objects.count()
    total_rooms = Habitacion.objects.count()
    recent_hotels = Hotel.objects.order_by('-id')[:5]
    cant_usuarios = CustomUser.objects.count()

    total_reservations = reservas.count()
    estados_reservas = {
        status: reservas.filter(estatus=status).count()
        for status in (
            'solicitada','pendiente','confirmada',
            'modificada','ejecutada','cancelada','reembolsada'
        )
    }

    reservas_por_cobrar = reservas.filter(cobrada=False).count()
    reservas_por_pagar = reservas.filter(pagada=False).count()
    reservas_recientes = reservas.order_by('-fecha_reserva')[:5]

    
    ganancias_totales = sum(float(r.precio_total) for r in reservas)

    precio_total_por_mes = calcular_precio_total_por_mes(reservas)
    cant_reservas_por_mes = contar_reservas_por_mes(reservas)

    # Datos para el gráfico de 12 meses
    today = datetime.now()
    labels = []
    reservas_data = []
    ingresos_data = []
    deudas_data = []

    for i in range(12):
        month = (today.month - i - 1) % 12 + 1
        year = today.year if month <= today.month else today.year - 1

        labels.insert(0, datetime(year, month, 1).strftime('%b'))
        reservas_mes = reservas.filter(
            fecha_reserva__year=year,
            fecha_reserva__month=month
        )

        reservas_data.insert(0, reservas_mes.count())
        ingresos = reservas_mes.aggregate(
            total=DjangoSum('precio_total')
        )['total'] or 0
        deudas = reservas_mes.filter(cobrada=False).aggregate(
            total=DjangoSum('precio_total')
        )['total'] or 0

        ingresos_data.insert(0, float(ingresos))
        deudas_data.insert(0, float(deudas))

    context = {
        'total_reservations': total_reservations,
        'estados_reservas': estados_reservas,
        'reservas_por_cobrar': reservas_por_cobrar,
        'reservas_por_pagar': reservas_por_pagar,
        'reservas_recientes': reservas_recientes,
        'ganancias_totales': ganancias_totales,
        'precio_total_por_mes': precio_total_por_mes,
        'cant_reservas_por_mes': cant_reservas_por_mes,
        'total_hotels': total_hotels,
        'total_rooms': total_rooms,
        'recent_hotels': recent_hotels,
        'cant_usuarios': cant_usuarios,
        'ofertas_especiales': ofertas_especiales,
        'labels': labels,
        'reservas_data': reservas_data,
        'ingresos_data': ingresos_data,
        'deudas_data': deudas_data,
        'user': usuario,
    }

    return render(request, 'booking/user_dashboard.html', context)

@login_required
def perfil_cliente(request):
    usuario = request.user

    if request.method == 'POST':
        # Obtener los datos del formulario
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')        
        nombre_dueno = request.POST.get('nombre_dueno')        
        telefono_dueno = request.POST.get('telefono_dueno')        
        fee_hotel = request.POST.get('fee_hotel')
        tipo_fee_hotel = request.POST.get('tipo_fee_hotel')
        fee_carro = request.POST.get('fee_carro')  
        tipo_fee_carro = request.POST.get('tipo_fee_carro')
        fee_tarara = request.POST.get('fee_tarara')
        tipo_fee_tarara = request.POST.get('tipo_fee_tarara')

        # Actualizar los datos del usuario
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.email = email
        usuario.telefono = telefono
        usuario.direccion = direccion
        usuario.nombre_dueno = nombre_dueno
        usuario.telefono_dueno = telefono_dueno
        usuario.fee_hotel = fee_hotel
        usuario.tipo_fee_hotel = tipo_fee_hotel
        usuario.fee_carro = fee_carro
        usuario.tipo_fee_carro = tipo_fee_carro
        usuario.fee_tarara = fee_tarara
        usuario.tipo_fee_tarara = tipo_fee_tarara

        # Si se subió una nueva imagen de logo
        if 'logo' in request.FILES:
            usuario.logo = request.FILES['logo']

        # Guardar cambios
        try:
            usuario.save()
            messages.success(request, 'Perfil guardado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')

        return redirect('booking:perfil_cliente')  # Asegúrate de que 'perfil_cliente' es el nombre correcto en tus URLs

    # Renderiza la plantilla con los datos del usuario
    context = {
        'user': usuario,
    }
    return render(request, 'booking/perfil_cliente.html', context)

# Vista para el dashboard de hoteles
@login_required
def hotel_dashboard(request):
    destinos = PoloTuristico.objects.all()  # Obtener todos los destinos turísticos

    context = {
        'destinos': destinos,
    }    
    return render(request, 'booking/hotel/dashboard.html', context)

# ================================================================================================== #
# ---------------------------------------- Sección: Hotel Búsqueda --------------------------------- #
# ================================================================================================== #

# Vista para la búsqueda de hoteles
@login_required
def hotel_search(request):
    destinos = PoloTuristico.objects.all()  # Obtener todos los destinos turísticos
    context = {
        'destinos': destinos,
    }
    return render(request, 'booking/hotel_search.html', context)

# Vista para mostrar los resultados de la búsqueda de hoteles
@login_required
def hotel_results(request):
    # Obtener los parámetros de búsqueda desde la solicitud GET
    destino = request.GET.get('destino', '')
    fechas_viaje = request.GET.get('fechas_viaje', '')
    
    try:
        cant_habitaciones = int(request.GET.get('habitaciones', 1))
        cant_adultos = int(request.GET.get('adultos', 1))
        cant_ninos = int(request.GET.get('ninos', 0))
    except ValueError:
        messages.error(request, "Los valores de habitaciones, adultos o niños no son válidos.")
        return redirect('hotel_search')

    info_habitaciones = request.GET.get('info_habitaciones', '')

    # Procesar la información de habitaciones si está disponible
    try:
        info_habitaciones = json.loads(info_habitaciones) if info_habitaciones else {'totalNinos': cant_ninos}
    except json.JSONDecodeError:
        messages.error(request, "La información de habitaciones no es válida.")
        return redirect('hotel_search')

    # Separar fechas_viaje en fecha_checkin y fecha_checkout
    fecha_checkin = ''
    fecha_checkout = ''
    if fechas_viaje:
        fechas = fechas_viaje.split(' - ')
        if len(fechas) == 2:
            fecha_checkin = fechas[0]
            fecha_checkout = fechas[1]

    # Calcular la cantidad de días de la reserva
    cantidad_dias_reserva = 0
    if fecha_checkin and fecha_checkout:
        try:
            checkin_date = datetime.strptime(fecha_checkin, '%Y-%m-%d')
            checkout_date = datetime.strptime(fecha_checkout, '%Y-%m-%d')
            cantidad_dias_reserva = (checkout_date - checkin_date).days
        except ValueError:
            messages.error(request, "Las fechas de check-in o check-out no son válidas.")
            return redirect('hotel_search')

    hoteles = Hotel.objects.all()

    # Filtrar los hoteles según el destino seleccionado
    if destino and destino != 'todos-los-destinos':
        hoteles = hoteles.filter(polo_turistico__nombre__iexact=destino.replace('-', ' '))

    # Filtrar los hoteles según la política de admisión de niños
    if info_habitaciones.get('totalNinos', 0) > 0:
        hoteles = hoteles.filter(solo_adultos=False)
    
    # Obtener el diccionario de ofertas más baratas
    cant_personas = cant_adultos + cant_ninos    
    ofertas_mas_baratas = obtener_ofertas_mas_baratas(request, hoteles, cant_personas, cantidad_dias_reserva, fechas_viaje)

   
    # Preparar el contexto para la plantilla
    context = {
        'destinos': PoloTuristico.objects.all(),
        'hoteles': hoteles,
        'fecha_checkin': fecha_checkin,
        'fecha_checkout': fecha_checkout,
        'cant_habitaciones': cant_habitaciones,
        'cant_adultos': cant_adultos,
        'cant_ninos': cant_ninos,
        'destino': destino,
        'info_habitaciones': info_habitaciones,
        'fechas_viaje': fechas_viaje,
        'ofertas_mas_baratas': ofertas_mas_baratas
    }

    return render(request, 'booking/hotel/hotel_results.html', context)

# ================================================================================================== #
# -------------------------------------- Sección: Hotel Detalles ----------------------------------- #
# ================================================================================================== #

# Vista para mostrar los detalles de un hotel específico
@login_required
def hotel_detalle(request, hotel_id):
    #print('Entro a: hotel_detalle')

    hotel = get_object_or_404(Hotel, id=hotel_id)  # Obtener el hotel o devolver 404 si no existe
    habitaciones = Habitacion.objects.filter(hotel=hotel)  # Obtener las habitaciones del hotel
    ofertas = Oferta.objects.filter(hotel=hotel)  # Obtener las ofertas del hotel      
    plan_alimenticio = hotel.plan_alimenticio
    
    usuario_logueado = request.user  # Esto devuelve el usuario que está logueado en la sesión
    fee_hotel = usuario_logueado.fee_hotel
    tipo_fee_hotel = usuario_logueado.tipo_fee_hotel
    fee_nino = usuario_logueado.fee_nino
   
    
    # Validación: Obtener y validar la información de la solicitud GET
    try:
        cant_habitaciones = int(request.GET.get('habitaciones', 0))
        cant_adultos = int(request.GET.get('adultos', 0))
        cant_ninos = int(request.GET.get('ninos', 0))
        info_habitaciones = json.loads(request.GET.get('info_habitaciones', '{}'))
    except (ValueError, json.JSONDecodeError):
        messages.error(request, "Los datos de la solicitud no son válidos.")
        return redirect('hotel_search')

    fechas_viaje = request.GET.get('fechas_viaje', '')
    num_habitaciones = int(info_habitaciones.get('numHabitaciones', 0))
    
    habitaciones_data = []

    # Procesar cada habitación
    for i in range(num_habitaciones):
        habitacion_info = info_habitaciones['datosHabitaciones'][i]
        opciones = get_opciones_habitacion(habitaciones, ofertas, habitacion_info, fechas_viaje, tipo_fee_hotel, fee_hotel, fee_nino)
               
        habitaciones_data.append({
            'habitacion': f'Habitación {i+1}',
            'adultos': habitacion_info['adultos'],
            'ninos': habitacion_info['ninos'],
            'total_pax': f"{habitacion_info['adultos']} + {habitacion_info['ninos']}",
            'opciones': opciones,
            'cant_adultos': habitacion_info['adultos'],
            'cant_ninos': habitacion_info['ninos'],
            'fechas_viaje': fechas_viaje,
            # Añadimos precio_sin_fee y total_fee si lo deseas mostrar
        })
    
    # Preparar el contexto para la plantilla
    context = {
        'hotel': hotel,
        'habitaciones_data': habitaciones_data,
        'info_habitaciones': info_habitaciones,
        'plan_alimenticio': plan_alimenticio,
        'destinos': PoloTuristico.objects.all(),            
        'fechas_viaje': fechas_viaje,
    }
    return render(request, 'booking/hotel/hotel_detalle.html', context)

@login_required
def calcular_cantidad_noches(rango_fechas):
    #print('Entro a: calcular_cantidad_noches')
    
    # Separar las fechas
    fecha_inicio_str, fecha_fin_str = rango_fechas.split(" - ")
    
    # Convertir las fechas a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
    
    # Calcular la diferencia de días
    dias = (fecha_fin - fecha_inicio).days
    
    return dias

# Función auxiliar para obtener las opciones de habitación
@login_required
def get_opciones_habitacion(habitaciones, ofertas, habitacion_info, fechas_viaje, tipo_fee_hotel, fee_hotel, fee_nino):
    opciones = []

    for habitacion in habitaciones:
        try:
            cant_adultos = int(habitacion_info['adultos'])
            cant_ninos = int(habitacion_info['ninos'])
        except ValueError:
            print(f"Error en los valores de adultos o niños para la habitación {habitacion.id}")
            continue

        edades_ninos = habitacion_info.get('edadesNinos', [])
        nino1 = 1 if len(edades_ninos) > 0 else 0
        nino2 = 1 if len(edades_ninos) > 1 else 0

        try:
            # Calcular el precio según el tipo de habitación, cantidad de adultos, y niños
            precio, precio_sin_fee, total_fee = calcular_precios_por_tipo_habitacion(
                cant_adultos, nino1, nino2, fechas_viaje, ofertas, habitacion
            )
            
            # Calcular la cantidad de noches en el rango de fechas de viaje
            cantidad_noches = calcular_cantidad_noches(fechas_viaje)

            # Calcular el precio total según el tipo de fee del hotel (fijo o porcentaje)-----------------------------------------------------------------------
            if tipo_fee_hotel == "PAX":              
                
                precio += ((fee_hotel * cant_adultos) + (fee_nino * cant_ninos)) * cantidad_noches                
                
            elif tipo_fee_hotel == "Reserva":
                
                precio += fee_hotel
            
            else:
                
                precio += precio * fee_hotel / 100
            
        except ValueError as e:
            print(f"Error al calcular el precio para la habitación {habitacion.id}: {e}")
            precio = None

        opcion, _ = HabitacionOpcion.objects.get_or_create(
            habitacion=habitacion,
            nombre=habitacion.tipo,
            defaults={'descripcion': habitacion.descripcion, 'precio': precio}
        )

        if precio > 0:
            opciones.append({
                'id': opcion.id,
                'nombre': opcion.nombre,
                'descripcion': opcion.descripcion,
                'precio': precio if precio is not None else "No disponible",
                'precio_sin_fee': precio_sin_fee,
                'total_fee': total_fee,
                'destinos': PoloTuristico.objects.all(),
                'fechas_viaje': fechas_viaje,
            })

    return opciones

# Función auxiliar para calcular los días aplicables de una oferta
@login_required
def calcular_dias_por_oferta(ofertas, fecha_viaje):
    #print('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
    #print('Entro a: calcular_dias_por_oferta(ofertas, fecha_viaje)')
    
    try:
        # Parsear las fechas de viaje        
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
        
        # Calculamos la cantidad de días
        cantidad_dias = (fecha_fin_viaje - fecha_inicio_viaje).days
        
        #print('---Parsear las fechas de viaje ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        #print(f"fecha_inicio_viaje: {fecha_inicio_viaje}")
        #print(f"   fecha_fin_viaje: {fecha_fin_viaje}")
        #print(f"     cantidad_dias: {cantidad_dias}") 
        
        
    except ValueError as e:
        print(f"Error al parsear fechas de viaje: {e}")
        raise

    resultado = []

    # Procesar cada oferta y calcular los días de solapamiento
    
    for oferta in ofertas:        
        #print(f"----------------- Oferta ----------------: {oferta.temporada}")
        try:
                       
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
            
            #print('---Procesar cada oferta y calcular los días de solapamiento---') 
            #print(f"fecha_inicio_oferta: {fecha_inicio_oferta}")
            #print(f"   fecha_fin_oferta: {fecha_fin_oferta}") 
          
        except ValueError as e:
            print(f"Error al parsear fechas de la oferta {oferta}: {e}")
            continue

        inicio_solapamiento = max(fecha_inicio_viaje, fecha_inicio_oferta)
        fin_solapamiento = min(fecha_fin_viaje, fecha_fin_oferta)
        #print('')
        #print('---Inicio y fin de solapamiento---') 
        #print(f"inicio_solapamiento: {inicio_solapamiento}")
        #print(f"   fin_solapamiento: {fin_solapamiento}")         
        dias_en_oferta = 0
        #print('--------------')
        #print(f"OUT If dias_en_oferta: {dias_en_oferta}") 

        if inicio_solapamiento < fin_solapamiento:
            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days
            if cantidad_dias == dias_en_oferta:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": True 
                })
            else:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": False
                })
                
            #print(f" IN If dias_en_oferta: {dias_en_oferta}") 
        
        elif inicio_solapamiento == fin_solapamiento:
            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days + 1
            if cantidad_dias == dias_en_oferta:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": True 
                })
            else:
                resultado.append({
                    "oferta": oferta,
                    "dias_en_oferta": dias_en_oferta,
                    "completa": False
                })
            #print(f" IN If dias_en_oferta: {dias_en_oferta}") 
            
        #print('----- Resultado -----')
        #print(f"resultado: {resultado}")

    return resultado

# Función auxiliar para calcular el precio de una habitación según la oferta
@login_required
def calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion , cant_dias):
    
    #print('------------------------------')
    #print('Entro a: calcula_precio')
    
    # Imprimir valores
    #print(f"cant_adultos (Cantidad de adultos): {cant_adultos}")
    #print(f"nino1 (Primer niño): {nino1}")
    #print(f"nino2 (Segundo niño): {nino2}")
    #print(f"oferta (Oferta aplicada): {oferta}")
    #print(f"habitacion (Tipo de habitación): {habitacion}")
    #print(f"cant_dias (Cantidad de días de estadía): {cant_dias}")

    if not (0 <= cant_adultos <= 3):
        raise ValueError("La cantidad de adultos debe ser entre 0 y 3.")
    if nino1 not in [0, 1]:
        raise ValueError("nino1 debe ser 0 o 1.")
    if nino2 not in [0, 1]:
        raise ValueError("nino2 debe ser 0 o 1.")
    if nino2 == 1 and nino1 == 0:
        raise ValueError("No puede haber un nino2 sin un nino1.")

    # Inicializar variables
    precio_sin_fee = 0
    total_fee = 0
    cant_personas = cant_adultos + nino1 + nino2

    # Precios por tipo de habitación y personas
    J = float(oferta.doble)
    K = float(oferta.triple)
    L = float(oferta.sencilla)
    M = float(oferta.primer_nino)
    N = float(oferta.segundo_nino)
    O = float(oferta.un_adulto_con_ninos)
    P = float(oferta.primer_nino_con_un_adulto)
    Q = float(oferta.segundo_nino_con_un_adulto)

    fee_sencilla = float(oferta.fee_sencilla or 0)
    fee_doble = float(oferta.fee_doble or 0)
    fee_triple = float(oferta.fee_triple or 0)
    fee_primer_nino = float(oferta.fee_primer_nino or 0)
    fee_segundo_nino = float(oferta.fee_segundo_nino or 0)

    # para ajustar bien la cantidada de dias.
    cant_dias = cant_dias
    
    # Calcular el precio según la cantidad de adultos y niños
    if cant_adultos == 1:
        if nino1 == 0 and nino2 == 0:
            print('Entro Sencilla 1 adulto')
            precio_sin_fee = L * cant_dias
            total_fee = (L + fee_sencilla) * cant_dias
            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 0:
            print('Entro 1 adulto y 1 niño')
            precio_sin_fee = ((O + P) * cant_personas) * cant_dias
            
            if P > 0:
                # Si P es mayor que 0, se suma P y fee_primer_nino (El primer niño tiene un costo)
                valor_p = P + fee_doble
            elif P == 0 and fee_doble != 0:
                # Si P es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_p = 0
            else:
                # Si P es menor que 0, se usa un valor predeterminado negativo (No se permite el primer niño)
                valor_p = -999999999

            # Cálculo total de la tarifa
            total_fee = ((O + fee_doble) + valor_p) * cant_dias


            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 1:
            print('Entro 1 adulto y 2 niños')
            precio_sin_fee = ((O + P + Q) + 2) * cant_dias

            # Evaluación condicional para P
            if P > 0:
                # Si P es mayor que 0, se utiliza su valor normal
                valor_p = P
            elif P == 0:
                # Si P es igual a 0, el resultado será 0
                valor_p = 0
            else:
                # Si P es menor que 0, asignamos un valor predeterminado de penalización
                valor_p = -99999999

            # Evaluación condicional para Q
            if Q > 0:
                # Si Q es mayor que 0, se utiliza su valor normal
                valor_q = Q
            elif Q == 0:
                # Si Q es igual a 0, el resultado será 0
                valor_q = 0
            else:
                # Si Q es menor que 0, asignamos un valor predeterminado de penalización
                valor_q = -99999999

            # Cálculo total de la tarifa
            total_fee = ((O + valor_p + valor_q) + (fee_doble * 2) + fee_primer_nino) * cant_dias

                        
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')

    elif cant_adultos == 2:
        if nino1 == 0 and nino2 == 0:            
            #print('Entro Doble 2 adultos')
            #print('----------------------')
            #print(f"            J: {J}")
            #print(f"    fee_doble: {fee_doble}")
            #print(f"cant_personas: {cant_personas}")
            #print(f"    cant_dias: {cant_dias}")
            #print('----------------------')
            precio_sin_fee = ( J ) * cant_personas * cant_dias
            total_fee = (J + fee_doble) * cant_personas * cant_dias
            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 0:
            print('Entro 2 adultos y 1 niño')
            precio_sin_fee = (( J ) * cant_adultos + M ) * cant_dias
            
            if M > 0:
                # Si M es mayor que 0, se suma M y fee_primer_nino (El primer niño tiene un costo)
                valor_m = M + fee_primer_nino
            elif M == 0 and fee_primer_nino != 0:
                # Si M es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_m = 0
            else:
                # Si M es menor que 0, simplemente se usa M (No se permite el primer niño)
                valor_m = -999999999

            # Cálculo total de la tarifa
            total_fee = ((J + fee_doble) * cant_adultos + valor_m) * cant_dias                               
         
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 1:
            print('Entro 2 adultos y 2 niños')
            precio_sin_fee = (J * cant_adultos + M + N) * cant_dias
            
            # Evaluación condicional para M
            if M > 0:
                # Si M es mayor que 0, se suma M y fee_primer_nino (El primer niño tiene un costo)
                valor_m = M + fee_primer_nino
            elif M == 0 and fee_primer_nino != 0:
                # Si M es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_m = 0
            else:
                # Si M es menor que 0, asignamos el valor predeterminado de penalización
                valor_m = -99999999

            # Evaluación condicional para N
            if N > 0:
                # Si N es mayor que 0, se suma N y fee_segundo_nino (El segundo niño tiene un costo)
                valor_n = N + fee_segundo_nino
            elif N == 0 and fee_segundo_nino != 0:
                # Si N es igual a 0 y fee_segundo_nino no es 0, el resultado será 0 (El segundo niño es gratuito)
                valor_n = 0
            else:
                # Si N es menor que 0, asignamos el valor predeterminado de penalización
                valor_n = -99999999

            # Cálculo total de la tarifa
            total_fee = ((J + fee_doble) * cant_adultos + valor_m + valor_n) * cant_dias

                        
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')

    elif cant_adultos == 3:
        if nino1 == 0 and nino2 == 0:
            print('Entro Triple 3 adultos')
            precio_sin_fee = (K * cant_personas) * cant_dias
            total_fee = (K + fee_triple) * cant_personas * cant_dias
            
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')
            
        elif nino1 == 1 and nino2 == 0 and habitacion.admite_3_con_1:
            print('Entro 3 adultos y 1 niño')
            precio_sin_fee = (( K ) * cant_personas + M  ) * cant_dias
            # Evaluación condicional para M
            if M > 0:
                # Si M es mayor que 0, se suma M y fee_primer_nino (El primer niño tiene un costo)
                valor_m = M + fee_primer_nino
            elif M == 0 and fee_primer_nino != 0:
                # Si M es igual a 0 y fee_primer_nino no es 0, el resultado será 0 (El primer niño es gratuito)
                valor_m = 0
            else:
                # Si M es menor que 0, asignamos un valor predeterminado de penalización
                valor_m = -99999999

            # Cálculo total de la tarifa
            total_fee = ((K + fee_triple) * cant_personas + valor_m) * cant_dias

                        
            print(f'Costo sin fee: {precio_sin_fee} y el Costo de la Agencia es {total_fee}')

    #---------------------------------------------------------
    """print('---------------------------------------------------------')
        
    if cant_adultos == 1:
        if nino1 == 0 and nino2 == 0:
            precio = (L + fee_sencilla) * cant_adultos
            
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
            
        elif nino1 == 1 and nino2 == 0:
            precio = (O + P) + (fee_doble * cant_personas)
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
            
        elif nino1 == 1 and nino2 == 1:
            precio = (O + P + Q) + (fee_doble * 2) + fee_primer_nino
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")


    elif cant_adultos == 2:
        if nino1 == 0 and nino2 == 0:
            precio = (J + fee_doble) * cant_personas
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
                
        elif nino1 == 1 and nino2 == 0:
            precio = (J + fee_doble) * cant_adultos + M + fee_primer_nino            
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
                
        elif nino1 == 1 and nino2 == 1:
            precio = (J + fee_doble) * cant_adultos + M + fee_primer_nino + N + fee_segundo_nino
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")

    elif cant_adultos == 3:
        if nino1 == 0 and nino2 == 0:
            precio = (K + fee_triple) * cant_adultos
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2},-> Precio: {precio*7}")
                
        elif nino1 == 1 and nino2 == 0 and habitacion.admite_3_con_1:
            precio = (K + fee_triple) * cant_adultos + M + fee_primer_nino            
            print(f"Adultos: {cant_adultos}, Niños: {nino1}, {nino2}, Admite 3 con 1 -> Precio: {precio}") """





    # Precio total
    precio_total = precio_sin_fee + total_fee
    
    precio_total = total_fee

    return precio_total, precio_sin_fee, total_fee

# Función auxiliar para calcular los precios por tipo de habitación
@login_required
def calcular_precios_por_tipo_habitacion(cant_adultos, nino1, nino2, fecha_viaje, ofertas, habitacion):
    precio_total = 0
    precio_sin_fee_total = 0
    total_fee = 0
    ofertas_tipo = []

    for oferta in ofertas:
        if oferta.tipo_habitacion == habitacion.tipo and oferta.disponible:
            ofertas_tipo.append(oferta)

    resultado = calcular_dias_por_oferta(ofertas_tipo, fecha_viaje)
    #print('----- Entro a: calcular_precios_por_tipo_habitacion -----')
    #print(f"El Resltado aqui es: (resultado): {resultado}")

    precio_total = 0
    precio_sin_fee_total = 0  
    total_fee = 0
    
    for result in resultado:
        #print('-------------------------------------')
        #print(f" resul en itercacion: (result): {result}")
        
        oferta = result["oferta"]
        #print(f"oferta en itercacion: (oferta): {oferta}")
        
        dias_en_oferta = result["dias_en_oferta"]
        #print(f"  dias_en_oferta en itercacion: (dias_en_oferta): {dias_en_oferta}")
        #print('----- calcula_precio ------')
        
        precio, precio_sin_fee, fee = calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion, dias_en_oferta)
        
        if result["completa"]:   
            #print('--------------------------------------------------- COMPLETA COMPLETA COMPLETA COMPLETA COMPLETA ---------------------------------------------------')     
            precio_total = precio
            precio_sin_fee_total = precio_sin_fee
            total_fee = fee
        
        if not result["completa"]:   
            #print('--------------------------------------------------- NOO COMPLETA NOO COMPLETANOO COMPLETANOO COMPLETA ---------------------------------------------------')     
            precio_total += precio
            precio_sin_fee_total += precio_sin_fee
            total_fee += fee
        
        #print(f"                precio_total en itercacion: (precio_total): {precio_total}")
        #print(f"precio_sin_fee_total en itercacion: (precio_sin_fee_total): {precio_sin_fee_total}")
        #print(f"                      total_fee en itercacion: (total_fee): {total_fee}")

    return precio_total, precio_sin_fee_total, total_fee

# Función auxiliar para obtener la descripción del plan alimenticio según el código
@login_required
def get_plan_alimenticio(plan_code):

    #print('Entro a: get_plan_alimenticio')
    
    plan_dict = {
        'AI': 'Todo Incluido (AI)',
        'MAP': 'Alojamiento, Desayuno y Cena (MAP)',
        'CP': 'Alojamiento y Desayuno (CP)',
        'AP': 'Alojamiento, Desayuno, Almuerzo y Cena (AP)',
        'EP': 'Solo Alojamiento (EP)'
    }
    return plan_dict.get(plan_code, 'Solo Alojamiento (EP)')

# ================================================================================================== #
# ---------------------------- Sección: Hotel Pago y Reserva --------------------------------------- #
# ================================================================================================== #

# Vista para manejar el proceso de pago y reserva de un hotel
@login_required
def hotel_pago_reserva(request, hotel_id):
    
    hotel = get_object_or_404(Hotel, id=hotel_id)  # Obtener el hotel o devolver 404 si no existe
    
    # Captura de valores desde request.GET una sola vez
    destino = request.GET.get('destino', '')  
    fechas_viaje = request.GET.get('fechas_viaje', '')
    habitaciones = request.GET.get('habitaciones', '')
    adultos = request.GET.get('adultos', '')
    ninos = request.GET.get('ninos', '')
    info_habitaciones = request.GET.get('info_habitaciones', '{}')  # Captura info_habitaciones como un JSON
    
    # Decodificación de info_habitaciones (si es necesario)
    import json
    try:
        info_habitaciones_decoded = json.loads(info_habitaciones)
    except json.JSONDecodeError:
        info_habitaciones_decoded = {}  # En caso de error, asigna un diccionario vacío
    
    # Si es una solicitud GET
    if request.method == 'GET':
        context = {
            'destino': destino,
            'fechas_viaje': fechas_viaje,
            'habitaciones': habitaciones,
            'adultos': adultos,
            'ninos': ninos,
            'info_habitaciones': info_habitaciones_decoded,  # Decodificado si es necesario
        }
        return render(request, 'booking/hotel/hotel_pago_reserva.html', context)
    
    # Si es una solicitud POST
    #print('********************* ENTRO AL POST ****************************')
    habitaciones = []
    opciones_seleccionadas = []
    precio_total = 0

    # Procesar las opciones seleccionadas para cada habitación en el POST
    for key, value in request.POST.items():
        if key.startswith('opciones_habitacion_'):
            habitacion_index = int(key.split('_')[-1])
            
            try:
                opcion_id = int(value) if value else None
                
                if opcion_id:
                    opcion = HabitacionOpcion.objects.get(id=opcion_id)
                    precio_opcion = request.POST.get(f'precio_opcion_{habitacion_index}', '0')
                    
                    opciones_seleccionadas.append({
                        'habitacion_index': habitacion_index,
                        'opcion': {
                            'id': opcion.id,
                            'nombre': opcion.nombre,
                            'descripcion': opcion.descripcion,
                            'precio': precio_opcion,
                        },
                        'precio': float(precio_opcion) if precio_opcion.isdigit() else 0
                    })
                    precio_total += float(precio_opcion.replace(',', '.'))

                    
            except HabitacionOpcion.DoesNotExist:
                print(f"Error: No se encontró HabitacionOpcion con id {opcion_id}")
                
    # Procesar cada opción seleccionada
    for opcion_seleccionada in opciones_seleccionadas:
        habitacion_index = opcion_seleccionada['habitacion_index']
        nombre_habitacion = request.POST.get(f'habitacion_{habitacion_index}_nombre', '')
        num_adultos = int(request.POST.get(f'habitacion_{habitacion_index}_adultos', '0') or 0)
        num_ninos = int(request.POST.get(f'habitacion_{habitacion_index}_ninos', '0') or 0)
        cant_adultos = int(request.POST.get(f'habitacion_{habitacion_index}_cant_adultos', '0') or 0)
        cant_ninos = int(request.POST.get(f'habitacion_{habitacion_index}_cant_ninos', '0') or 0)
        fechas_viaje = request.POST.get(f'habitacion_{habitacion_index}_fechas_viaje', '')

        habitaciones.append({
            'habitacion': nombre_habitacion,
            'adultos': num_adultos,
            'ninos': num_ninos,
            'precio': opcion_seleccionada['precio'],
            'cant_adultos': cant_adultos,
            'cant_ninos': cant_ninos,
            'fechas_viaje': fechas_viaje,
            'opcion': opcion_seleccionada['opcion'],
            'adultos_numeros': list(range(1, num_adultos + 1)),
            'ninos_numeros': list(range(1, num_ninos + 1)),
        })

    # Preparar el contexto para la plantilla
    context = {
        'precio_total': precio_total,
        'hotel': hotel,
        'habitaciones': habitaciones,
        # Usar los datos GET capturados previamente
        'destino': destino,
        'fechas_viaje': fechas_viaje,
        'adultos': adultos,
        'ninos': ninos,
        'info_habitaciones': info_habitaciones_decoded,
        'opciones_seleccionadas': opciones_seleccionadas,
    }
    
    return render(request, 'booking/hotel/hotel_pago_reserva.html', context)

# Vista para completar la solicitud de reserva
@transaction.atomic
def complete_solicitud(request, hotel_id):
    destinos = PoloTuristico.objects.all()
    context = {'destinos': destinos}

    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        post_data = request.POST
        nombre_usuario = f"{request.user.agencia}"
        email_empleado = post_data.get('email_empleado', '')
        notas = post_data.get('notas', '')
        fechas_viaje = post_data.get('habitacion_fechas_viaje', '')
        precio_total = post_data.get('precio_total', '')

        # Validar y procesar fechas de viaje
        try:
            fecha_inicio_str, fecha_fin_str = fechas_viaje.split(' - ')
            fecha_inicio = datetime.strptime(fecha_inicio_str.strip(), '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin_str.strip(), '%Y-%m-%d')
            cantidad_noches = (fecha_fin - fecha_inicio).days
        except ValueError:
            messages.error(request, "Las fechas de viaje no son válidas.")
            return redirect('hotel_detalle', hotel_id=hotel_id)

        # Obtener el número de habitaciones
        try:
            habitacion_count = int(post_data.get('habitacion_count', 0))
        except ValueError:
            messages.error(request, "La cantidad de habitaciones no es válida.")
            return redirect('hotel_detalle', hotel_id=hotel_id)

        personas_por_habitacion = []

        # Obtener las ofertas disponibles para el hotel
        ofertas = Oferta.objects.filter(hotel=hotel, disponible=True)

        # Iterar sobre cada habitación para procesar y recalcular los precios
        for habitacion_index in range(1, habitacion_count + 1):
            habitacion_info = {
                'adultos': [],
                'ninos': [],
                'precio': Decimal('0.00'),
                'precio_sin_fee': Decimal('0.00'),
                'total_fee': Decimal('0.00'),
                'opcion': {}
            }

            # Obtener el nombre de la opción seleccionada desde el formulario POST
            habitacion_nombre = post_data.get(f"habitacion_{habitacion_index}_nombre", f"Habitación {habitacion_index}")
            habitacion_info['opcion']['nombre'] = habitacion_nombre

            # Obtener el número de adultos y niños
            try:
                num_adultos = int(post_data.get(f"habitacion_{habitacion_index}_adultos", 0))
                num_ninos = int(post_data.get(f"habitacion_{habitacion_index}_ninos", 0))
            except ValueError:
                messages.error(request, "El número de adultos o niños no es válido.")
                return redirect('hotel_detalle', hotel_id=hotel_id)

            # Procesar adultos
            for i in range(1, num_adultos + 1):
                nombre = post_data.get(f"nombre{habitacion_index}_adulto{i}")
                fecha_nacimiento = post_data.get(f"fecha_nacimiento{habitacion_index}_adulto{i}")
                pasaporte = post_data.get(f"pasaporte{habitacion_index}_adulto{i}")
                caducidad = post_data.get(f"caducidad{habitacion_index}_adulto{i}")
                pais_emision = post_data.get(f"pais_emision{habitacion_index}_adulto{i}")
                email = post_data.get(f"email{habitacion_index}_adulto{i}")
                telefono = post_data.get(f"telefono{habitacion_index}_adulto{i}")

                habitacion_info['adultos'].append({
                    'nombre': nombre,
                    'fecha_nacimiento': fecha_nacimiento,
                    'pasaporte': pasaporte,
                    'caducidad': caducidad,
                    'pais_emision': pais_emision,
                    'email': email,
                    'telefono': telefono,
                })

            # Procesar niños
            edades_ninos = []
            for i in range(1, num_ninos + 1):
                nombre = post_data.get(f"nombre{habitacion_index}_nino{i}")
                fecha_nacimiento = post_data.get(f"fecha_nacimiento{habitacion_index}_nino{i}")
                pasaporte = post_data.get(f"pasaporte{habitacion_index}_nino{i}")
                caducidad = post_data.get(f"caducidad{habitacion_index}_nino{i}")
                pais_emision = post_data.get(f"pais_emision{habitacion_index}_nino{i}")
                edad = post_data.get(f"edad_nino{habitacion_index}_{i}", '0')
                try:
                    edades_ninos.append(int(edad))
                except ValueError:
                    edades_ninos.append(0)

                habitacion_info['ninos'].append({
                    'nombre': nombre,
                    'fecha_nacimiento': fecha_nacimiento,
                    'pasaporte': pasaporte,
                    'caducidad': caducidad,
                    'pais_emision': pais_emision
                })

            # Recalcular el precio en el servidor
            cant_adultos = num_adultos
            cant_ninos = num_ninos
            nino1 = 1 if cant_ninos >= 1 else 0
            nino2 = 1 if cant_ninos >= 2 else 0

            # Obtener la habitación correspondiente
            try:
                habitacion_obj = Habitacion.objects.get(hotel=hotel, tipo=habitacion_nombre)
            except Habitacion.DoesNotExist:
                messages.error(request, f"No se encontró la habitación {habitacion_nombre} en el hotel.")
                return redirect('hotel_detalle', hotel_id=hotel_id)

            # Recalcular el precio usando las funciones existentes
            try:
                precio_total_habitacion, precio_sin_fee_habitacion, total_fee_habitacion = calcular_precios_por_tipo_habitacion(
                    cant_adultos, nino1, nino2, fechas_viaje, ofertas, habitacion_obj
                )

                # Convertir a Decimal para cálculos precisos
                habitacion_info['precio'] = Decimal(str(precio_total_habitacion))
                habitacion_info['precio_sin_fee'] = Decimal(str(precio_sin_fee_habitacion))
                habitacion_info['total_fee'] = Decimal(str(total_fee_habitacion))
            except Exception as e:
                messages.error(request, f"Error al calcular el precio de la habitación: {e}")
                return redirect('hotel_detalle', hotel_id=hotel_id)

            personas_por_habitacion.append(habitacion_info)

        # Calcular el precio total, costo sin fee y total de fees              
        costo_sin_fee = sum(habitacion['precio_sin_fee'] for habitacion in personas_por_habitacion)
        total_fees = sum(habitacion['total_fee'] for habitacion in personas_por_habitacion)

        # Calcular el costo total (para el agente) sumando el costo sin fee y los fees 
        costo_total = total_fees
        
        #Convertir el Precio total de STR a Decimal 
        precio_total_str = precio_total.replace(',', '.') 
        precio_total = Decimal(precio_total_str)

        # Redondear a dos decimales si es necesario
        precio_total = precio_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        costo_sin_fee = costo_sin_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        costo_total = costo_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Crear la reserva
        reserva = Reserva.objects.create(
            hotel=hotel,
            fecha_reserva=timezone.now(),
            nombre_usuario=nombre_usuario,
            email_empleado=email_empleado,
            notas=notas,
            costo_total=costo_total,  # Ahora asignamos el costo total correcto
            costo_sin_fee=costo_sin_fee,
            precio_total=precio_total,
            tipo='hoteles',
            estatus='solicitada'
        )

        habitaciones = []

        # Crear las habitaciones y pasajeros asociados
        for habitacion_index, habitacion_info in enumerate(personas_por_habitacion, start=1):
            habitacion_reserva = HabitacionReserva.objects.create(
                reserva=reserva,
                habitacion_nombre=habitacion_info['opcion']['nombre'],
                adultos=len(habitacion_info['adultos']),
                ninos=len(habitacion_info['ninos']),
                fechas_viaje=fechas_viaje,
                precio=habitacion_info['precio'],
                oferta_codigo=post_data.get(f"oferta_codigo_{habitacion_index}", '')
            )

            habitaciones.append(habitacion_reserva)

            for adulto in habitacion_info['adultos']:
                try:
                    pasajero = Pasajero.objects.create(
                        habitacion=habitacion_reserva,
                        nombre=adulto['nombre'],
                        fecha_nacimiento=datetime.strptime(adulto['fecha_nacimiento'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pasaporte=adulto['pasaporte'],
                        caducidad_pasaporte=datetime.strptime(adulto['caducidad'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pais_emision_pasaporte=adulto['pais_emision'],
                        email=adulto['email'],
                        telefono=adulto['telefono'],
                        tipo='adulto'
                    )
                except ValueError:
                    messages.error(request, "Las fechas de nacimiento o caducidad no son válidas.")
                    return redirect('hotel_detalle', hotel_id=hotel_id)

            for nino in habitacion_info['ninos']:
                try:
                    pasajero = Pasajero.objects.create(
                        habitacion=habitacion_reserva,
                        nombre=nino['nombre'],
                        fecha_nacimiento=datetime.strptime(nino['fecha_nacimiento'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pasaporte=nino['pasaporte'],
                        caducidad_pasaporte=datetime.strptime(nino['caducidad'], '%Y/%m/%d').strftime('%Y-%m-%d'),
                        pais_emision_pasaporte=nino['pais_emision'],
                        email='',
                        telefono='',
                        tipo='nino'
                    )
                except ValueError:
                    messages.error(request, "Las fechas de nacimiento o caducidad no son válidas.")
                    return redirect('hotel_detalle', hotel_id=hotel_id)

        reserva.save()

        # Enviar correo de confirmación
        funciones_externas_booking.correo_confirmacion_reserva(reserva)

        messages.success(request, 'Reserva completada con éxito.')
        return redirect('booking:user_dashboard')

    return redirect('booking:user_dashboard')

# ================================================================================================== #
# -------------------------------- Sección: Reservas Hoteles --------------------------------------- #
# ================================================================================================== #

@login_required
def listar_reservas(request, estado=None):
    user_agencia = request.user.agencia
    qs = (Reserva.objects
        .filter(agencia__iexact=user_agencia)
        .select_related('hotel')
        .prefetch_related('habitaciones_reserva__pasajeros')
        .order_by('-fecha_reserva')
    )

    # estado
    estado = estado or request.GET.get('estado')
    if estado in ['por_cobrar','pagada']:
        qs = qs.filter(pagada=(estado=='pagada'))
    elif estado:
        qs = qs.filter(estatus__iexact=estado)

    # filtros
    q = request.GET.get('q','').strip()
    if q:
        qs = qs.filter(
            Q(hotel__hotel_nombre__icontains=q) |
            Q(nombre_usuario__icontains=q) |
            Q(email_empleado__icontains=q) |
            Q(habitaciones_reserva__pasajeros__nombre__icontains=q)
        ).distinct()

    id_resv = request.GET.get('id_reserva','').strip()
    if id_resv.isdigit():
        qs = qs.filter(id=int(id_resv))

    # fechas
    from datetime import datetime
    def parse_f(s): 
        try: return datetime.strptime(s,'%Y-%m-%d').date()
        except: return None
    fi = parse_f(request.GET.get('fecha_inicio'))
    ff = parse_f(request.GET.get('fecha_fin'))
    if fi: qs = qs.filter(fecha_reserva__gte=fi)
    if ff: qs = qs.filter(fecha_reserva__lte=ff)

    # paginación y context
    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    params = {k:v for k,v in request.GET.items() if v}

    return render(request, 'booking/reservas/listar_reservas.html', {
        'reservas': page, 'params': params,
        'query': q, 'estado': estado,
        'id_reserva': id_resv,
        'fecha_inicio': fi.strftime('%Y-%m-%d') if fi else '',
        'fecha_fin': ff.strftime('%Y-%m-%d') if ff else ''
    })


@login_required
def detalles_reserva(request, reserva_id):    
    try:
        reserva = Reserva.objects.get(pk=reserva_id)
        estatus = reserva.estatus
        tipo = reserva.tipo

        data = {
            'estatus': estatus,
            'tipo': tipo,
        }

        # =======================
        # HOTELES
        # =======================
        if tipo == 'hoteles' and reserva.hotel:
            hotel_nombre = getattr(reserva.hotel, 'hotel_nombre', 'Hotel no disponible')
            direccion = getattr(reserva.hotel, 'direccion', 'Dirección no disponible')
            checkin = reserva.fecha_reserva.strftime('%Y-%m-%d %H:%M')
            checkout = (reserva.fecha_reserva + timedelta(days=10)).strftime('%Y-%m-%d %H:%M')

            habitaciones = []
            for hab in reserva.habitaciones_reserva.all():
                adultos = ', '.join(p.nombre for p in hab.pasajeros.filter(tipo='adulto'))
                ninos = ', '.join(p.nombre for p in hab.pasajeros.filter(tipo='nino'))
                habitaciones.append({
                    'nombre': hab.habitacion_nombre,
                    'adultos': adultos,
                    'ninos': ninos,
                })

            data.update({
                'hotel': hotel_nombre,
                'direccion': direccion,
                'checkin': checkin,
                'checkout': checkout,
                'habitaciones': habitaciones,
            })

        # =======================
        # ENVÍO
        # =======================
        elif tipo == 'envio' and reserva.envio:
            envio = reserva.envio
            remitente = str(envio.remitente) if envio.remitente else "N/D"
            destinatario = str(envio.destinatario) if envio.destinatario else "N/D"
            items = [
                {
                    'descripcion': item.descripcion,
                    'cantidad': item.cantidad,
                    'peso': float(item.peso),
                    'valor_aduanal': float(item.valor_aduanal),
                }
                for item in envio.items.all()
            ]

            data.update({
                'remitente': remitente,
                'destinatario': destinatario,
                'items': items,
            })

        # Otros tipos pueden seguir aquí...

        return JsonResponse(data)

    except Reserva.DoesNotExist:
        return JsonResponse({'error': 'Reserva no encontrada.'}, status=404)
    except Exception as e:
        print(f"Error al obtener detalles de reserva: {e}")
        return JsonResponse({'error': 'Error al cargar los detalles de la reserva.'}, status=500)

# ================================================================================================== #
# ---------------------------------------- Sección: Remesas ---------------------------------------- #
# ================================================================================================== #


@login_required
def remesas(request):
    usuario = request.user

    try:
        tasa_cambio = TasaCambio.objects.latest('fecha_actualizacion')
    except TasaCambio.DoesNotExist:
        tasa_cambio = None

    # Obtener últimos destinatarios y remitentes
    destinatarios = Destinatario.objects.all().order_by('-id')[:4]
    remitentes = Remitente.objects.all().order_by('-id')[:4]

    # Serializar listas
    destinatarios_list = [
        {
            'id': d.id,
            'nombre_completo': f"{d.primer_nombre} {d.primer_apellido}",
            'telefono': d.telefono,
            'direccion_completa': f"{d.calle} {d.numero}, {d.municipio}, {d.provincia}"
        }
        for d in destinatarios
    ]

    remitentes_list = [
        {
            'id': r.id,
            'nombre_apellido': r.nombre_apellido,
            'telefono': r.telefono,
            'direccion': r.direccion
        }
        for r in remitentes
    ]

    # Datos combinados para JSON
    contactos_json = json.dumps({
        'destinatarios': destinatarios_list,
        'remitentes': remitentes_list
    })

    context = {
        'tasa_cambio': tasa_cambio,
        'usuario': usuario,
        'json_contactos': contactos_json
    }

    return render(request, 'booking/remesas/remesas.html', context)


@login_required
def guardar_remesa(request):
    if request.method == 'POST':
        print("📩 POST recibido")

        try:
            # Leer el cuerpo del request como JSON
            data = json.loads(request.body.decode('utf-8'))

            remitente_id = data.get('remitente_id')
            destinatario_id = data.get('destinatario_id')
            monto_envio = data.get('montoEnvio')
            moneda_envio = data.get('monedaEnvio')
            moneda_recepcion = data.get('monedaRecepcion')

            print(f"🔎 remitente_id: {remitente_id}")
            print(f"🔎 destinatario_id: {destinatario_id}")
            print(f"💰 monto_envio: {monto_envio}")
            print(f"💱 moneda_envio: {moneda_envio} moneda_recepcion: {moneda_recepcion}")

            if not (remitente_id and destinatario_id and monto_envio and moneda_envio and moneda_recepcion):
                print("❌ Datos faltantes")
                return JsonResponse({'mensaje': 'Datos obligatorios incompletos.'}, status=400)

            # Buscar objetos
            remitente = Remitente.objects.get(id=remitente_id)
            destinatario = Destinatario.objects.get(id=destinatario_id)

            # Obtener tasa activa
            tasa_cambio = TasaCambio.objects.filter(activa=True).latest('fecha_actualizacion')

            if moneda_envio == moneda_recepcion:
                tasa = 1
            elif moneda_envio == 'USD' and moneda_recepcion == 'CUP':
                tasa = tasa_cambio.tasa_cup
            elif moneda_envio == 'USD' and moneda_recepcion == 'MLC':
                tasa = tasa_cambio.tasa_mlc
            elif moneda_envio == 'CUP' and moneda_recepcion == 'USD':
                tasa = Decimal('1.0') / tasa_cambio.tasa_cup
            elif moneda_envio == 'MLC' and moneda_recepcion == 'USD':
                tasa = Decimal('1.0') / tasa_cambio.tasa_mlc
            else:
                tasa = 1  # Por defecto

            print(f"🔁 Tasa aplicada: {tasa}")
            monto_estimado_recepcion = Decimal(monto_envio) * tasa
            print(f"💸 monto_estimado_recepcion: {monto_estimado_recepcion}")

            # Crear la remesa
            remesa = Remesa.objects.create(
                remitente=remitente,
                destinatario=destinatario,
                monto_envio=monto_envio,
                moneda_envio=moneda_envio,
                monto_estimado_recepcion=monto_estimado_recepcion,
                moneda_recepcion=moneda_recepcion
            )

            print(f"✅ Remesa creada ID {remesa.id}")

            # Crear reserva
            reserva = Reserva.objects.create(
                remesa=remesa,
                nombre_usuario=request.user.agencia,
                email_empleado=request.user.email,
                costo_total=monto_envio,
                precio_total=monto_estimado_recepcion,
                tipo='remesas',
                estatus='solicitada',
                numero_confirmacion=None,
                cobrada=False,
                pagada=False,
                fecha_reserva=timezone.now()
            )

            print(f"📦 Reserva vinculada creada ID {reserva.id}")

            return JsonResponse({'mensaje': '✅ Remesa guardada correctamente'}, status=200)

        except Exception as e:
            print(f"❌ Error al guardar remesa: {str(e)}")
            return JsonResponse({'mensaje': f'Error al guardar remesa: {str(e)}'}, status=500)

    return JsonResponse({'mensaje': 'Método no permitido'}, status=405)


# ================================================================================================== #
# -------------------------------- Sección: Reservas Traslados ------------------------------------- #
# ================================================================================================== #

@login_required
def traslados_search(request):
    ubicaciones = Ubicacion.objects.all()  # Obtener todos las ubicaciopnes turísticos
    context = {
        'ubicaciones': ubicaciones,
    } 
    return render(request, 'booking/traslados_search.html', context)

@login_required
def traslado_dashboard(request):
    ubicaciones = Ubicacion.objects.all()  # Obtener todos las ubicaciopnes turísticos
    context = {
        'ubicaciones': ubicaciones,
    }    
    return render(request, 'booking/traslados/dashboard.html', context)

@login_required
def result_traslados(request):
    transportistas = Transportista.objects.all()
    ubicaciones = Ubicacion.objects.all()
    vehiculos = Vehiculo.objects.all()
    
    if request.method == 'POST':
        print('ES UN POST')
        # Obtener los datos del formulario
        tipologia = request.POST.get('tipologia')
        origen = request.POST.get('origen')
        destino = request.POST.get('destino')
        fecha_traslado = request.POST.get('fecha_traslado')
        adultos = request.POST.get('adultos')
        ninos = request.POST.get('ninos')
        infantes = request.POST.get('infantes')
        
        # CALCULO DEL PAX
        try:
            pax = int(adultos) + int(ninos) + int(infantes)
        except (ValueError, TypeError):
            pax = 0  # O manejar el error adecuadamente
            messages.error(request, "Cantidad de pasajeros inválida.")
            return redirect('booking:result_traslados') # Redirigir al formulario de búsqueda

        # VALIDACIONES ADICIONALES
        if pax < 1:
            messages.error(request, "El número total de pasajeros debe ser al menos 1.")
            return redirect('booking:result_traslados') # Redirigir al formulario de búsqueda

        # LISTA DE TRASLADOS
        try:
            lista_traslados = buscar_traslados(pax, origen, destino)
        except Exception as e:
            messages.error(request, f"Error al buscar traslados: {e}")
            lista_traslados = Traslado.objects.none()

        # PRINTS para la depuración
        print(f"Tipología: {tipologia}")
        print(f"Origen ID: {origen}")
        print(f"Destino Nombre: {destino}")
        print(f"Fecha de traslado: {fecha_traslado}")
        print(f"Adultos: {adultos}")
        print(f"Niños: {ninos}")
        print(f"Infantes: {infantes}")
        print(f"PAX: {pax}")
        print(f"LISTA DE TRASLADOS: {lista_traslados}")
        
        context = {
            'tipologia': tipologia,
            'origen': origen,
            'destino': destino,
            'fecha_traslado': fecha_traslado,
            'adultos': adultos,
            'ninos': ninos,
            'infantes': infantes,
            'pax': pax,
            'transportistas': transportistas,
            'ubicaciones': ubicaciones,
            'vehiculos': vehiculos,
            'traslados': lista_traslados,  # Pasar la lista filtrada de traslados
        }

        return render(request, 'booking/traslados/result_traslados.html', context)  # Cambiado a result_traslados.html
    
    else:
        print('NO FUE UN POST (result_traslados)')
        # Opcional: Redirigir al formulario de búsqueda si se accede a esta vista por GET
        return redirect('booking:result_traslados') # Redirigir al formulario de búsqueda  # Asegúrate de tener esta URL configurada

@login_required    
def detalle_traslados(request, traslado_id):
    transportistas = Transportista.objects.all()
    ubicaciones = Ubicacion.objects.all()
    vehiculos = Vehiculo.objects.all()
    traslado = get_object_or_404(Traslado, id=traslado_id)
    hoteles = Hotel.objects.all()

    
    if request.method == 'POST':
        print('ES UN POST')

        # Obtener los datos del formulario
        tipologia = request.POST.get('tipologia', '')
        origen = request.POST.get('origen', '')
        destino = request.POST.get('destino', '')
        fecha_traslado = request.POST.get('fecha_traslado', '')
        adultos = request.POST.get('adultos', '0')
        ninos = request.POST.get('ninos', '0')
        infantes = request.POST.get('infantes', '0')

        # PRINTS para la depuración
        print(f"Tipología: {tipologia}")
        print(f"Origen ID: {origen}")
        print(f"Destino Nombre: {destino}")
        print(f"Fecha de traslado: {fecha_traslado}")
        print(f"Adultos: {adultos}")
        print(f"Niños: {ninos}")
        print(f"Infantes: {infantes}")

        # CALCULO DEL PAX
        try:
            pax = int(adultos) + int(ninos) + int(infantes)
        except (ValueError, TypeError):
            print('Error en cálculo PAX')
            pax = 0
            messages.error(request, "Cantidad de pasajeros inválida.")
            return redirect('booking:result_traslados')

        # VALIDACIONES ADICIONALES
        if pax < 1:
            print('PAX menor que 1')
            messages.error(request, "El número total de pasajeros debe ser al menos 1.")
            return redirect('booking:result_traslados')

        # PRINTS para la depuración
        print(f"PAX: {pax}")
        print(f"Traslado: {traslado}")

        origen = Ubicacion.objects.get(id=origen)
        hoteles_origen = obtener_hoteles_por_polo(origen.nombre)
        hoteles_destino = obtener_hoteles_por_polo(destino)
        
        calificacion_origen = clasificar_destinos(origen.nombre)          
        calificacion_destino = clasificar_destinos(destino)               


        context = {
            'tipologia': tipologia,
            'origen': origen,
            'destino': destino,
            'fecha_traslado': fecha_traslado,
            'adultos': adultos,
            'ninos': ninos,
            'infantes': infantes,
            'pax': pax,
            'transportistas': transportistas,
            'ubicaciones': ubicaciones,
            'vehiculos': vehiculos,            
            'traslado': traslado,
            'hoteles': hoteles, 
            'hoteles_origen': hoteles_origen, 
            'hoteles_destino': hoteles_destino,
            'calificacion_origen': calificacion_origen,
            'calificacion_destino': calificacion_destino
        }

        return render(request, 'booking/traslados/detalle_traslados.html', context)

    else:    
        print('NO FUE UN POST')
        messages.error(request, "Acceso inválido a detalles de traslado.")
        return render(request, 'booking/traslados/error_page.html')  # Muestra un mensaje en vez de redirigir

@login_required    
def reserva_traslados(request, traslado_id):
    transportistas = Transportista.objects.all()
    ubicaciones = Ubicacion.objects.all()
    vehiculos = Vehiculo.objects.all()
    traslado = get_object_or_404(Traslado, id=traslado_id)
    hoteles = Hotel.objects.all()

    
    if request.method == 'POST':
        print('ES UN POST ( reserva_traslados )')

        # Obtener los datos del formulario
        tipologia = request.POST.get('tipologia', '')
        origen = request.POST.get('origen', '')
        destino = request.POST.get('destino', '')
        fecha_traslado = request.POST.get('fecha_traslado', '')
        adultos = request.POST.get('adultos', '0')
        ninos = request.POST.get('ninos', '0')
        infantes = request.POST.get('infantes', '0')

        # PRINTS para la depuración
        print(f"Tipología: {tipologia}")
        print(f"Origen ID: {origen}")
        print(f"Destino Nombre: {destino}")
        print(f"Fecha de traslado: {fecha_traslado}")
        print(f"Adultos: {adultos}")
        print(f"Niños: {ninos}")
        print(f"Infantes: {infantes}")

        # CALCULO DEL PAX
        try:
            pax = int(adultos) + int(ninos) + int(infantes)
        except (ValueError, TypeError):
            print('Error en cálculo PAX')
            pax = 0
            messages.error(request, "Cantidad de pasajeros inválida.")
            return redirect('booking:result_traslados')

        # VALIDACIONES ADICIONALES
        if pax < 1:
            print('PAX menor que 1')
            messages.error(request, "El número total de pasajeros debe ser al menos 1.")
            return redirect('booking:result_traslados')

        # PRINTS para la depuración
        print(f"PAX: {pax}")
        print(f"Traslado: {traslado}")

        origen = Ubicacion.objects.get(id=origen)
        hoteles_origen = obtener_hoteles_por_polo(origen.nombre)
        hoteles_destino = obtener_hoteles_por_polo(destino)
        
        calificacion_origen = clasificar_destinos(origen.nombre)          
        calificacion_destino = clasificar_destinos(destino)               


        context = {
            'tipologia': tipologia,
            'origen': origen,
            'destino': destino,
            'fecha_traslado': fecha_traslado,
            'adultos': adultos,
            'ninos': ninos,
            'infantes': infantes,
            'pax': pax,
            'transportistas': transportistas,
            'ubicaciones': ubicaciones,
            'vehiculos': vehiculos,            
            'traslado': traslado,
            'hoteles': hoteles, 
            'hoteles_origen': hoteles_origen, 
            'hoteles_destino': hoteles_destino,
            'calificacion_origen': calificacion_origen,
            'calificacion_destino': calificacion_destino
        }

        return render(request, 'booking/traslados/reserva_traslados.html', context)

    else:    
        print('NO FUE UN POST ( reserva_traslados )')
        messages.error(request, "Acceso inválido a detalles de traslado.")
        return render(request, 'booking/traslados/error_page.html')  # Muestra un mensaje en vez de redirigir
    
def clasificar_destinos(destino):
    destino_upper = destino.upper().strip()  # Convertir a mayúsculas y eliminar espacios extra

    if "HOTEL" in destino_upper or "HOTELES" in destino_upper:
        return "HOTEL"
    elif "AEROPUERTO" in destino_upper:
        return "AEROPUERTO"
    else:
        return "OTRO"

def obtener_hoteles_por_polo(destino):
    # Extraer el polo eliminando "HOTELES"
    if "HOTELES" in destino:
        print("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
        print("Destino SIII contiene 'HOTELES', mostrando todos los hoteles.")
        polo = destino.replace("HOTELES", "").strip()
        print(f"POLO: {polo}")
        # Buscar si el polo existe en la base de datos
        polo_obj = PoloTuristico.objects.filter(nombre__icontains=polo).first()

        if polo_obj:
            print("SIII se encontró el polo turístico, mostrando todos los hoteles.")
            # Si se encuentra el polo, obtener los hoteles de ese polo
            hoteles = Hotel.objects.filter(polo_turistico=polo_obj)
            print(f"Hoteles encontrados en {polo_obj.nombre}: {[hotel.hotel_nombre for hotel in hoteles]}")
            return hoteles
        else:
            # Si no se encuentra el polo, obtener todos los hoteles
            print("No se encontró el polo turístico, mostrando todos los hoteles.")
            return Hotel.objects.all()
    else:
        print("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
        print("Destino no contiene 'HOTELES', mostrando todos los hoteles.")
        return Hotel.objects.all()


@transaction.atomic
def complete_solicitud_traslado(request, traslado_id):
    traslado = get_object_or_404(Traslado, id=traslado_id)

    if request.method == 'POST':
        post_data = request.POST

        nombre_usuario = f"{request.user.agencia}"
        email_empleado = post_data.get('email_empleado', '')
        notas = post_data.get('notas', '')
        fecha_traslado = post_data.get('fecha_traslado', '')
        precio_total = post_data.get('precio', '')

        # Convertir precio total a Decimal
        try:
            precio_total = Decimal(precio_total.replace(',', '.'))
        except ValueError:
            messages.error(request, "El precio total no es válido.")
            return redirect('reserva_traslados', traslado_id=traslado.id)

        # ============================ #
        # Crear la reserva de traslado #
        # ============================ #
        reserva = Reserva.objects.create(
            traslado=traslado,
            fecha_reserva=timezone.now(),
            nombre_usuario=nombre_usuario,
            email_empleado=email_empleado,
            notas=notas,
            costo_sin_fee=precio_total,   
            costo_total=precio_total,     
            precio_total=precio_total,    
            tipo='traslados',
            estatus='solicitada'
        )

        # ======================================== #
        # Guardar el pasajero asociado al traslado #
        # ======================================== #
        Pasajero.objects.create(
            traslado=traslado,  # Asociar con traslado
            nombre=post_data.get("nombre_adulto", ""),
            fecha_nacimiento=post_data.get("fecha_nacimiento", None),
            pasaporte=post_data.get("pasaporte", ""),
            caducidad_pasaporte=post_data.get("caducidad", None),
            pais_emision_pasaporte=post_data.get("pais_emision", ""),
            email=post_data.get("email_adulto", ""),
            telefono=post_data.get("telefono_adulto", ""),
            tipo='adulto'  # Se asume que el pasajero es adulto
        )
        
        # Enviar correo de confirmación
        funciones_externas_booking.correo_confirmacion_reserva(reserva)

        messages.success(request, 'Reserva de traslado completada con éxito.')
        return redirect('booking:user_dashboard')

    return redirect('reserva_traslados', traslado_id=traslado.id)


    
def error_page(request):
    return render(request, 'booking/traslados/error_page.html')

def buscar_traslados(pax, origen_id, destino_nombre):
    """
    Busca y devuelve una lista de traslados que coinciden con los criterios proporcionados.

    Parámetros:
    - pax (int): Número total de pasajeros.
    - origen_id (int): ID de la ubicación de origen.
    - destino_nombre (str): Nombre de la ubicación de destino.

    Retorna:
    - QuerySet: Lista de objetos Traslado que cumplen con los criterios.
    """
    traslados = Traslado.objects.none()

    try:
        origen = Ubicacion.objects.get(id=origen_id)
    except Ubicacion.DoesNotExist:
        print(f"Error: No existe una ubicación con ID {origen_id} como origen.")
        return traslados

    try:
        destino = Ubicacion.objects.get(nombre__iexact=destino_nombre)
    except Ubicacion.DoesNotExist:
        print(f"Error: No existe una ubicación con nombre '{destino_nombre}' como destino.")
        return traslados

    traslados = Traslado.objects.filter(
        origen=origen,
        destino=destino,
        vehiculo__capacidad_min__lte=pax,
        vehiculo__capacidad_max__gte=pax
    ).select_related('transportista', 'vehiculo')

    return traslados
        
def obtener_destinos(request):
    """ Devuelve los destinos disponibles según el origen seleccionado sin duplicados """
    origen_id = request.GET.get('origen_id')

    if origen_id:
        traslados = (
            Traslado.objects
            .filter(origen_id=origen_id)
            .values(nombre=F('destino__nombre'))
            .distinct()
        )
        destinos = [{'nombre': traslado['nombre']} for traslado in traslados]
    else:
        destinos = []

    return JsonResponse({'destinos': destinos})





# ================================================================================================== #
# -------------------------------- Sección: ENVIO  ------------------------------------------------- #
# ================================================================================================== #




@login_required
def crear_reserva_envio(request):
    destinatarios = Destinatario.objects.all().order_by('-id')[:4]
    remitentes = Remitente.objects.all().order_by('-id')[:4]
    tasa_cambio = TasaCambio.objects.filter(activa=True).order_by('-fecha_actualizacion').first()


    destinatarios_list = [
        {
            'id': d.id,
            'nombre_completo': f"{d.primer_nombre} {d.primer_apellido}",
            'telefono': d.telefono,
            'direccion_completa': f"{d.calle} {d.numero}, {d.municipio}, {d.provincia}"
        }
        for d in destinatarios
    ]

    remitentes_list = [
        {
            'id': r.id,
            'nombre_apellido': r.nombre_apellido,
            'telefono': r.telefono,
            'direccion': r.direccion
        }
        for r in remitentes
    ]

    datos_json = {
        'destinatarios': destinatarios_list,
        'remitentes': remitentes_list
    }

    return render(request, 'booking/envios/reserva_envio.html', {
        'datos_iniciales': mark_safe(json.dumps(datos_json)),
        'tasa_cambio': tasa_cambio
    })


def listar_destinatarios(request):
    destinatarios = Destinatario.objects.all().order_by('-id')
    data = [
        {
            'id': d.id,
            'nombre': f"{d.primer_nombre} {d.primer_apellido}",
            'telefono': d.telefono,
            'direccion': f"{d.calle} {d.numero}, {d.municipio}, {d.provincia}"
        } for d in destinatarios
    ]
    return JsonResponse({'success': True, 'destinatarios': data})


@csrf_protect
@require_POST
def crear_destinatario(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        destinatario = Destinatario.objects.create(
            primer_nombre=data.get('primer_nombre', '').strip(),
            segundo_nombre=data.get('segundo_nombre', '').strip(),
            primer_apellido=data.get('primer_apellido', '').strip(),
            segundo_apellido=data.get('segundo_apellido', '').strip(),
            ci=data.get('ci', '').strip(),
            telefono=data.get('telefono', '').strip(),
            telefono_adicional=data.get('telefono_adicional', '').strip(),
            calle=data.get('calle', '').strip(),
            numero=data.get('numero', '').strip(),
            entre_calle=data.get('entre_calle', '').strip(),
            y_calle=data.get('y_calle', '').strip(),
            apto_reparto=data.get('apto_reparto', '').strip(),
            piso=data.get('piso', '').strip(),
            municipio=data.get('municipio', '').strip(),
            provincia=data.get('provincia', '').strip(),
            email=data.get('email', '').strip(),
            observaciones=data.get('observaciones', '').strip()
        )

        return JsonResponse({
            'success': True,
            'destinatario': {
                'id': destinatario.id,
                'nombre_completo': destinatario.nombre_completo,
                'telefono': destinatario.telefono,
                'direccion_completa': destinatario.direccion_completa
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_protect
@require_POST
def crear_remitente(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        remitente = Remitente.objects.create(
            nombre_apellido=data.get('nombre_apellido', '').strip(),
            id_documento=data.get('id_documento', '').strip(),
            telefono=data.get('telefono', '').strip(),
            direccion=data.get('direccion', '').strip()
        )

        return JsonResponse({
            'success': True,
            'remitente': {
                'id': remitente.id,
                'nombre_apellido': remitente.nombre_apellido,
                'telefono': remitente.telefono,
                'direccion': remitente.direccion
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Error al decodificar JSON'}, status=400)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

@csrf_exempt
@login_required
def crear_reserva_envio_final(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        proveedor_envio = Proveedor.objects.filter(tipo='envio').first()

        remitente_id = data.get('remitente_id')
        destinatario_id = data.get('destinatario_id')
        items = data.get('items')

        print(">>> LLEGÓ EL POST A LA VISTA <<<")
        print("Remitente ID:", remitente_id)
        print("Destinatario ID:", destinatario_id)

        if not remitente_id or not destinatario_id or not items:
            return JsonResponse({'error': 'Faltan datos obligatorios'}, status=400)

        reserva = Reserva.objects.create(
            tipo='envio',
            estatus='solicitada',
            costo_sin_fee=0,
            costo_total=0,
            precio_total=0,
            numero_confirmacion='',
            cobrada=False,
            pagada=False,
            agencia=request.user.agencia,
            nombre_usuario=request.user.get_full_name() or request.user.username,
            email_empleado=request.user.email,
            proveedor=proveedor_envio
        )

        envio = Envio.objects.create(
            reserva=reserva,
            remitente_id=remitente_id,
            destinatario_id=destinatario_id
        )

        reserva.envio = envio
        reserva.save()

        total_precio = Decimal('0.00')
        total_sin_fee = Decimal('0.00')

        for item in items:
            peso = Decimal(str(item.get('peso') or 0))
            precio_kg = Decimal(str(item.get('precio_por_kg') or 0))
            cantidad = int(item.get('cantidad') or 1)
            tipo = item.get('tipo')
            envio_manejo = Decimal(str(item.get('envio_manejo') or 0))
            valor_aduanal = Decimal(str(item.get('valor_aduanal') or 0))

            # Calcular sin fee (solo base según tipo)
            if tipo == 'maritime':
                sin_fee = Decimal('1.60') * peso
                subtotal = (precio_kg * peso) + envio_manejo
            else:
                sin_fee = Decimal('2.60') * peso
                subtotal = precio_kg * peso

            total_sin_fee += sin_fee
            total_precio += subtotal

            ItemEnvio.objects.create(
                envio=envio,
                hbl=item.get('hbl'),
                tipo=tipo,
                cantidad=cantidad,
                peso=peso,
                descripcion=item.get('descripcion'),
                valor_aduanal=valor_aduanal,
                precio=precio_kg,
                envio_manejo=envio_manejo if tipo == 'maritime' else None
            )

        reserva.precio_total = total_precio
        reserva.costo_total = total_precio
        reserva.costo_sin_fee = total_sin_fee
        reserva.save()

        enviar_correo_confirmacion(reserva)

        return JsonResponse({'success': True, 'reserva_id': reserva.id})








# ================================================================================================== #
# -------------------------------- Sección: Por Desarrollar ---------------------------------------- #
# ================================================================================================== #

# Vista placeholder para la búsqueda de alquiler de coches
@login_required
def car_rental_search(request):
    return render(request, 'booking/car_rental_search.html')

# Vista placeholder para la búsqueda de transferencias
@login_required
def transfers_search(request):
    lugares = PoloTuristico.objects.all()  # Obtener todos los lugares turísticos
    return render(request, 'booking/transfers_search.html', {'lugares': lugares})


# ================================================================================================== #
# -------------------------------- Sección: Hotel Distal    ---------------------------------------- #
# ================================================================================================== #



# ────────────────────────────
#   DASHBOAR Y BUSCADOR
# ────────────────────────────

@login_required
def hotel_dashboard_distal(request):
    destinos = (
        HotelImportado.objects
        .values_list('destino', flat=True)
        .exclude(destino__isnull=True)
        .exclude(destino__exact="")
        .distinct()
        .order_by('destino')
    )
    return render(request, 'booking/hotel_distal/dashboard.html', {
        'destinos': destinos,
    })


# ────────────────────────────
#       RESULTADOS
# ────────────────────────────

@login_required
def hotel_results_distal(request):
    # Lista de destinos únicos
    destinos = (
        HotelImportado.objects
        .values_list('destino', flat=True)
        .exclude(destino__isnull=True)
        .exclude(destino__exact="")
        .distinct()
        .order_by('destino')
    )

    # Parámetros GET
    destino_slug = request.GET.get("destino", "")
    fechas = request.GET.get("fechas_viaje", "")
    raw_info = request.GET.get("info_habitaciones", "{}")
    destino = destino_slug.replace("-", " ").title()

    # Parseo de habitaciones
    try:
        print("📥 JSON crudo recibido (info_habitaciones):", raw_info)
        info_hab = json.loads(raw_info)
        datos_habs = info_hab.get("datosHabitaciones", [])
        print("📋 Datos parseados de habitaciones:", datos_habs)
    except Exception as e:
        print("❌ Error parseando JSON:", e)
        datos_habs = []

    # Parseo de fechas
    try:
        fecha_inicio, fecha_fin = [f.strip() for f in fechas.split(" - ")]
    except ValueError:
        fecha_inicio = fecha_fin = ""

    if not fechas or not datos_habs:
        return render(request, "booking/hotel_distal/hotel_results_distal.html", {
            "error": "Debes especificar fechas y habitaciones.",
            "destinos": destinos,
            "destino_slug": destino_slug,
            "destino": destino,
            "fechas": fechas,
        })

    # Hoteles disponibles en ese destino
    hoteles_qs = HotelImportado.objects.filter(destino__iexact=destino)
    hoteles_map = {h.hotel_name: h.hotel_code for h in hoteles_qs}

    # Función para construir XML individual
    def construir_xml(hotel_code):
        return build_hotel_avail_xml(hotel_code, fecha_inicio, fecha_fin, datos_habs)

    resultados = []
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_hotel = {
            executor.submit(
                requests.post,
                "http://api.1way2italy.it/service/test/v10/otaservice/hotelavail",
                data=construir_xml(code).encode("utf-8"),
                headers={"Content-Type": "application/xml"},
                timeout=15
            ): (name, code)
            for name, code in hoteles_map.items()
        }

        for future in as_completed(future_to_hotel):
            name, code = future_to_hotel[future]
            try:
                print(f"🚀 Procesando hotel: {name} ({code}) con datos_habs: {datos_habs}")
                resp = future.result()
                resp.raise_for_status()
                data = parse_hotel_avail_rs(resp.content)

                if data and isinstance(data, dict) and data.get("Habitaciones"):
                    currency_detected = set()
                    for h in data['Habitaciones']:
                        moneda = h.get("Currency", "???")
                        currency_detected.add(moneda)

                    print(f"✅ {name} devolvió {len(data['Habitaciones'])} habitaciones → Monedas: {', '.join(currency_detected)}")

                    rating = int(float(data.get('HotelInfo', {}).get("Rating", 0) or 0))
                    resultados.append({
                        "hotel_name": name,
                        "hotel_code": code,
                        "HotelInfo": data.get('HotelInfo', {}),
                        "habitaciones": data['Habitaciones'],
                        "rating": rating
                    })
                else:
                    print(f"⚠️ {name} no devolvió habitaciones o la respuesta fue inválida")

            except Exception as e:
                print(f"❌ Error procesando {name}: {e}")

    total_time = time.perf_counter() - start_time
    print(f"⏱ Tiempo total de procesamiento: {total_time:.2f} segundos")

    return render(request, "booking/hotel_distal/hotel_results_distal.html", {
        "resultados": resultados,
        "destinos": destinos,
        "destino_slug": destino_slug,
        "destino": destino,
        "fechas": fechas,
    })

# ────────────────────────────
#       DETALLES
# ────────────────────────────

@login_required
def hotel_detalle_distal(request, hotel_code):
    # Leer parámetros GET
    fechas = request.GET.get('fechas_viaje', '')
    raw_info = request.GET.get('info_habitaciones', '{}')

    # Parsear fechas
    try:
        fecha_inicio, fecha_fin = [f.strip() for f in fechas.split(' - ')]
    except ValueError:
        return redirect('booking:hotel_results_distal')

    # Parsear ocupación
    try:
        info = json.loads(raw_info)
        datos_habs = info.get("datosHabitaciones", [])
    except json.JSONDecodeError:
        datos_habs = []

    # Obtener objeto HotelImportado
    hotel_obj = get_object_or_404(HotelImportado, hotel_code=hotel_code)
    hotel_name = hotel_obj.hotel_name

    habitaciones_data = []
    for hab in datos_habs:
        adultos = hab.get('adultos', 0)
        ninos = hab.get('ninos', 0)

        # 🔧 Construimos el XML centralizado
        datos_single = [{
            'adultos': adultos,
            'ninos': ninos
        }]  # Solo para esta habitación

        xml_data = build_hotel_avail_xml(hotel_code, fecha_inicio, fecha_fin, datos_single)

        # Consultar API
        try:
            response = requests.post(
                "http://api.1way2italy.it/service/test/v10/otaservice/hotelavail",
                data=xml_data.encode("utf-8"),
                headers={"Content-Type": "application/xml"},
                timeout=15
            )
            response.raise_for_status()
            data = parse_hotel_avail_rs(response.content)
        except Exception as e:
            print(f"Error consultando API: {e}")
            data = None

        opciones = []
        if data and data['Habitaciones']:
            for idx, room in enumerate(data['Habitaciones'], start=1):
                precio_base = Decimal(room.get('Price', 0))

                precios = ajustar_precio_habitacion(
                    precio_base=precio_base,
                    adultos=adultos,
                    ninos=ninos,
                    fechas_viaje=fechas,
                    user=request.user
                )

                opciones.append({
                    'id': idx,
                    'nombre': room.get('NombreFinal', '—'),
                    'plan': room.get('MealPlan', ''),
                    'descripcion': room.get('Description', ''),
                    'capacidad_adultos': adultos,
                    'capacidad_ninos': ninos,
                    'precio_base': precios['costo_sin_fee'],
                    'costo_total': precios['costo_total'],
                    'precio_cliente': precios['precio_total'],
                    'moneda': room.get('Currency', ''),
                    'reembolsable': False,
                    'booking_code': room.get('BookingCode'),  # <--- NUEVO
                })

        habitaciones_data.append({
            'habitacion': hab.get('habitacion'),
            'adultos': adultos,
            'ninos': ninos,
            'opciones': opciones,
        })

    return render(request, 'booking/hotel_distal/hotel_detalle_distal.html', {
        'hotel': data['HotelInfo'] if data else {},
        'hotel_code': hotel_code,
        'destino': request.GET.get('destino', ''),
        'fechas': fechas,
        'cant_habitaciones': len(datos_habs),
        'cant_adultos': sum(h['adultos'] for h in datos_habs),
        'cant_ninos': sum(h['ninos'] for h in datos_habs),
        'habitaciones_data': habitaciones_data,
        'info_habitaciones': raw_info,
    })

def ajustar_precio_habitacion(precio_base, adultos, ninos, fechas_viaje, user=None):
    """
    Ajusta el precio de una habitación usando los fee configurados del proveedor DISTAL.
    """
    try:
        fecha_inicio_str, fecha_fin_str = [f.strip() for f in fechas_viaje.split(' - ')]
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
        noches = (fecha_fin - fecha_inicio).days
    except Exception as e:
        print(f"❌ [ajustar_precio_habitacion] Error al calcular noches: {e}")
        noches = 0

    # Buscar el proveedor DISTAL
    try:
        proveedor_distal = Proveedor.objects.get(nombre__iexact="DISTALCU")
        proveedor_fee_adultos = proveedor_distal.fee_adultos or Decimal('0.00')
        proveedor_fee_ninos = proveedor_distal.fee_ninos or Decimal('0.00')
    except Proveedor.DoesNotExist:
        print("⚠ No se encontró el proveedor DISTALCU. Se usarán los valores por defecto.")
        proveedor_fee_adultos = Decimal('6.00')
        proveedor_fee_ninos = Decimal('3.00')

    # 1️⃣ Costo puro de la API:
    costo_sin_fee = Decimal(precio_base)

    # 2️⃣ Aplicamos los fees del proveedor DISTAL:
    costo_total = (
        costo_sin_fee
        + (adultos * noches * proveedor_fee_adultos)
        + (ninos * noches * proveedor_fee_ninos)
    )

    # 3️⃣ Finalmente aplicamos el margen de la agencia logueada
    if user.tipo_fee_hotel == "$":
        precio_total = costo_total + ((adultos + ninos) * noches * Decimal(user.fee_hotel))
    else:
        porciento = (Decimal(user.fee_hotel) / 100) * costo_total
        precio_total = costo_total + porciento

    return {
        'costo_sin_fee': round(costo_sin_fee, 2),
        'costo_total': round(costo_total, 2),
        'precio_total': round(precio_total, 2)
    }


# ────────────────────────────
#       PAGOS RESERVA
# ────────────────────────────
@login_required
def politica_privacidad(request):
    return render(request, 'booking/politica_privacidad.html')



@login_required
def hotel_pago_reserva_distal(request, hotel_code):
    if request.method != 'POST':
        return redirect('booking:hotel_detalle_distal', hotel_code=hotel_code)

    hotel = get_object_or_404(HotelImportado, hotel_code=hotel_code)
    destino = request.POST.get('destino', '')
    fechas = request.POST.get('fechas_viaje', '')
    raw_json = request.POST.get('info_habitaciones', '{}')

    print("✅ JSON recibido (raw):", raw_json)

    try:
        print("🔧 Decodificando unicode escape...")
        fixed = raw_json.encode('utf-8').decode('unicode_escape')
        print("✅ Texto decodificado:", fixed)

        print("📦 Cargando JSON desde texto decodificado...")
        datos = json.loads(fixed)
        print("✅ JSON cargado exitosamente:", datos)

        datos_habs = datos.get('datosHabitaciones', [])
        print("📋 Habitaciones encontradas:", datos_habs)

    except Exception as e:
        print(f"❌ [ERROR] No se pudo decodificar JSON: {e}")
        datos_habs = []

    habitaciones = []
    precio_total = Decimal('0.00')

    for idx, hab in enumerate(datos_habs, start=1):
        raw_val = request.POST.get(f'opcion_{idx-1}')
        print(f"\n➡️ Procesando opcion_{idx-1}: {raw_val}")
        if not raw_val:
            print("⚠️ No se encontró el valor de la opción")
            continue

        parts = raw_val.split('|')
        if len(parts) != 9:
            print("⚠️ Opción inválida:", raw_val)
            continue

        id_str, nombre, precio_cliente_str, costo_total_str, precio_base_str, moneda, hotel_code, room_type, rate_plan = parts
        booking_code = f"{hotel_code}|{room_type}|{rate_plan}"

        try:
            print("💵 Convirtiendo precios a Decimal...")
            print("🔢 precio_cliente:", precio_cliente_str)
            print("🔢 costo_total:", costo_total_str)
            print("🔢 precio_base:", precio_base_str)

            precio_cliente = Decimal(precio_cliente_str.replace(',', '.'))
            costo_total = Decimal(costo_total_str.replace(',', '.'))
            precio_base = Decimal(precio_base_str.replace(',', '.'))
        except Exception as e:
            print(f"❌ [ERROR] Error al convertir decimales: {e}")
            continue

        precio_total += precio_cliente

        habitaciones.append({
            'roomNumber': idx,
            'opcion': {
                'id': int(id_str),
                'nombre': nombre,
                'precio_cliente': precio_cliente,
                'costo_total': costo_total,
                'precio_base': precio_base,
                'moneda': moneda,
                'booking_code': booking_code,
            },
            'adultos': hab.get('adultos', 0),
            'ninos': hab.get('ninos', 0),
            'adultos_numeros': list(range(1, hab.get('adultos', 0) + 1)),
            'ninos_numeros': list(range(1, hab.get('ninos', 0) + 1)),
        })

    print("💰 Precio total calculado:", precio_total)

    # ✅ Regeneramos JSON limpio para Alpine.js
    raw_json_clean = json.dumps({
        "datosHabitaciones": datos_habs
    })

    context = {
        'hotel': hotel,
        'destino': destino,
        'fechas': fechas,
        'habitaciones': habitaciones,
        'precio_total': precio_total,
        'raw_json': raw_json_clean,  # ✅ limpio y listo para Alpine
    }

    return render(request, 'booking/hotel_distal/hotel_pago_reserva_distal.html', context)

from decimal import Decimal, InvalidOperation
import html
import json

@login_required
def confirmar_reserva_distal(request, hotel_code):
    print("🔐 Verificando método de solicitud...")
    if request.method != 'POST':
        print("❌ Método no permitido. Redirigiendo...")
        return redirect('booking:hotel_pago_reserva_distal', hotel_code=hotel_code)

    print("🏨 Buscando hotel importado por código:", hotel_code)
    hotel = get_object_or_404(HotelImportado, hotel_code=hotel_code)

    print("📦 Obteniendo JSON de habitaciones y fechas del POST...")
    raw_json = request.POST.get('info_habitaciones', '{}')
    fechas = request.POST.get('fechas_viaje', '')
    print("✅ JSON recibido (raw):", raw_json)

    # Tratamiento de JSON como en hotel_pago_reserva_distal
    try:
        print("🔧 Decodificando unicode escape...")
        fixed = raw_json.encode('utf-8').decode('unicode_escape')
        print("✅ Texto decodificado:", fixed)

        print("📦 Cargando JSON desde texto decodificado...")
        datos = json.loads(fixed)
        datos_habs = datos.get('datosHabitaciones', [])
        print(f"✅ Habitaciones decodificadas correctamente: {len(datos_habs)}")
    except Exception as e:
        print(f"❌ Error al decodificar el JSON: {e}")
        datos_habs = []

    print("📊 Inicializando acumuladores y lista de habitaciones...")
    habitaciones = []
    precio_total = Decimal('0.00')
    costo_total_total = Decimal('0.00')
    costo_sin_fee_total = Decimal('0.00')

    for idx, hab in enumerate(datos_habs, start=1):
        print(f"🔍 Procesando habitación #{idx}...")
        raw_val = request.POST.get(f'opcion_{idx-1}')
        print(f"  👉 Opción seleccionada: {raw_val}")

        if not raw_val:
            print("  ⚠️ No se seleccionó opción. Se omite esta habitación.")
            continue

        parts = raw_val.split('|')
        if len(parts) != 9:
            print("  ⚠️ Formato de opción inválido. Se omite esta habitación.")
            continue

        id_str, nombre, precio_cliente_str, costo_total_str, precio_base_str, moneda, hotel_code_val, room_code, meal_code = parts
        booking_code = f"{hotel_code_val}|{room_code}|{meal_code}"
        print(f"  ✅ Booking Code generado: {booking_code}")

        try:
            precio_cliente = Decimal(precio_cliente_str.replace(',', '.'))
            costo_total = Decimal(costo_total_str.replace(',', '.'))
            precio_base = Decimal(precio_base_str.replace(',', '.'))
            print(f"  💲 Valores numéricos convertidos correctamente")
        except InvalidOperation as e:
            print(f"  ❌ Error convirtiendo a Decimal: {e}")
            continue

        precio_total += precio_cliente
        costo_total_total += costo_total
        costo_sin_fee_total += precio_base

        habitaciones.append({
            'roomNumber': idx,
            'nombre_habitacion': nombre,
            'opcion': {
                'id': int(id_str),
                'nombre': nombre,
                'precio_cliente': precio_cliente,
                'costo_total': costo_total,
                'precio_base': precio_base,
                'moneda': moneda,
                'booking_code': booking_code
            },
            'adultos': hab.get('adultos', 0),
            'ninos': hab.get('ninos', 0),
            'adultos_numeros': list(range(1, hab.get('adultos', 0) + 1)),
            'ninos_numeros': list(range(1, hab.get('ninos', 0) + 1)),
            'fechas_viaje': fechas,
        })
        print(f"  ✅ Habitación #{idx} agregada con éxito.")

    print(f"📦 Resumen total: {len(habitaciones)} habitaciones.")
    print(f"   💵 Precio total: {precio_total} | Costo total: {costo_total_total} | Costo sin fee: {costo_sin_fee_total}")

    print("🧾 Obteniendo datos del agente y pago...")
    agente_nom = request.POST.get('agente_nombre', '').strip()
    agente_cod = request.POST.get('agente_codigo', '').strip()
    metodo_pago = request.POST.get('metodo_pago', '')
    comentarios = request.POST.get('comentarios_pago', '').strip()
    print(f"👤 Agente: {agente_nom} ({agente_cod}) | Método: {metodo_pago} | Comentarios: {comentarios}")

    print("🔎 Buscando proveedor DISTALCU...")
    try:
        proveedor_distal = Proveedor.objects.get(nombre__iexact="DISTALCU")
        print("✅ Proveedor DISTALCU encontrado.")
    except Proveedor.DoesNotExist:
        proveedor_distal = None
        print("❌ Proveedor DISTALCU no existe.")

    print("📨 Creando instancia de Reserva...")
    reserva = Reserva.objects.create(
        hotel_importado=hotel,
        nombre_usuario=agente_nom,
        email_empleado=agente_cod,
        notas=(
            f"Agente: {agente_nom} ({agente_cod})\n"
            f"Método de pago: {metodo_pago}\n"
            f"Comentarios: {comentarios}"
        ),
        costo_sin_fee=costo_sin_fee_total,
        costo_total=costo_total_total,
        precio_total=precio_total,
        tipo='hoteles',
        estatus='solicitada',
        numero_confirmacion='',
        cobrada=False,
        pagada=False,
        agencia=request.user.agencia,
        proveedor=proveedor_distal
    )
    print(f"✅ Reserva creada con ID: {reserva.id}")

    print("🏨 Guardando habitaciones y pasajeros...")
    for h in habitaciones:
        print(f"  🛏️ Guardando habitación #{h['roomNumber']}...")
        hab_res = HabitacionReserva.objects.create(
            reserva=reserva,
            habitacion_nombre=h['nombre_habitacion'],
            adultos=h['adultos'],
            ninos=h['ninos'],
            fechas_viaje=h['fechas_viaje'],
            precio=h['opcion']['precio_cliente'],
            oferta_codigo='',
            booking_code=h['opcion']['booking_code']
        )
        print(f"  ✅ Habitación guardada: {hab_res.habitacion_nombre} (Booking Code: {hab_res.booking_code})")

        for a in h['adultos_numeros']:
            pasajero = Pasajero.objects.create(
                habitacion=hab_res,
                nombre=request.POST.get(f"hab_{h['roomNumber']}_adulto_{a}_nombre", ''),
                fecha_nacimiento=request.POST.get(f"hab_{h['roomNumber']}_adulto_{a}_nac"),
                pasaporte=request.POST.get(f"hab_{h['roomNumber']}_adulto_{a}_pasaporte", ''),
                caducidad_pasaporte=request.POST.get(f"hab_{h['roomNumber']}_adulto_{a}_caducidad", ''),
                pais_emision_pasaporte=request.POST.get(f"hab_{h['roomNumber']}_adulto_{a}_pais", ''),
                email=request.POST.get(f"hab_{h['roomNumber']}_adulto_{a}_email", ''),
                telefono=request.POST.get(f"hab_{h['roomNumber']}_adulto_{a}_telefono", ''),
                tipo='adulto'
            )
            print(f"    👨 Adulto #{a} creado: {pasajero.nombre}")

        for n in h['ninos_numeros']:
            pasajero = Pasajero.objects.create(
                habitacion=hab_res,
                nombre=request.POST.get(f"hab_{h['roomNumber']}_nino_{n}_nombre", ''),
                fecha_nacimiento=request.POST.get(f"hab_{h['roomNumber']}_nino_{n}_nac"),
                pasaporte=request.POST.get(f"hab_{h['roomNumber']}_nino_{n}_pasaporte", ''),
                caducidad_pasaporte=request.POST.get(f"hab_{h['roomNumber']}_nino_{n}_caducidad", ''),
                pais_emision_pasaporte=request.POST.get(f"hab_{h['roomNumber']}_nino_{n}_pais", ''),
                tipo='nino'
            )
            print(f"    🧒 Niño #{n} creado: {pasajero.nombre}")

    print("📧 Enviando correo de confirmación de la reserva...")
    enviar_correo_confirmacion(reserva)
    print("✅ Correo enviado correctamente.")

    print("🎉 Reserva confirmada exitosamente.")
    messages.success(request, "¡Tu reserva se ha confirmado correctamente!")
    return redirect('booking:user_dashboard')


# ─────────────────────────────────
#       ENVIO DE CORREOS Y ADJUNTOS
# ─────────────────────────────────

def enviar_correo_confirmacion(reserva):
    """
    Llama a la función correspondiente según el tipo de reserva.
    """
    if reserva.tipo == 'hoteles':
        enviar_correo_confirmacion_hotel(reserva)
    elif reserva.tipo == 'traslados':
        enviar_correo_confirmacion_traslado(reserva)
    elif reserva.tipo == 'envio':
        enviar_correo_confirmacion_envio(reserva)
    elif reserva.tipo == 'remesas':
        enviar_correo_confirmacion_remesa(reserva)
    elif reserva.tipo == 'certificado':
        enviar_correo_confirmacion_certificado(reserva)
    else:
        print(f"[INFO] No se ha definido el envío de correo para el tipo: {reserva.tipo}")


def enviar_correo_confirmacion_hotel(reserva):
    """
    Envía un correo de confirmación de hotel con todos los detalles de la reserva.
    """
    try:
        pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)
        habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
        encabezado = "Gracias por reservar con RUTA MULTISERVICE. A continuación encontrará los detalles de su reserva:"
        asunto, cuerpo_html, cuerpo_texto = generar_contenido_correo_hotel_mejorado(reserva, pasajeros, habitaciones, encabezado)

        enviar_email_basico(
            asunto=asunto,
            html=cuerpo_html,
            texto=cuerpo_texto,
            destinatario=reserva.email_empleado
        )

    except Exception as e:
        print(f"[ERROR] Error al generar o enviar el correo: {e}")


def enviar_email_basico(asunto, html, texto, destinatario):
    """
    Envía un correo básico con versión HTML y texto plano.
    """
    remitente = os.getenv("EMAIL_REMITENTE", "booking@rutamultiservice.com")
    clave = os.getenv("EMAIL_PASSWORD")

    if not clave:
        print("[ERROR] Clave de correo no definida en variable de entorno EMAIL_PASSWORD.")
        return

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destinatario

    mensaje.attach(MIMEText(texto, "plain"))
    mensaje.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.office365.com", 587) as servidor:
            servidor.starttls()
            servidor.login(remitente, clave)
            servidor.sendmail(remitente, destinatario, mensaje.as_string())
            print("✉️ Correo enviado correctamente.")
    except Exception as e:
        print(f"[ERROR] Fallo al enviar correo: {e}")


def generar_contenido_correo_hotel_mejorado(reserva, pasajeros, habitaciones, encabezado):
    nombre_hotel = getattr(reserva.hotel_importado, 'hotel_name', 'Hotel no disponible')
    destino = getattr(reserva.hotel_importado, 'destino', 'Destino no disponible')
    moneda = getattr(reserva.hotel_importado, 'currency', 'USD')
    fechas_viaje = habitaciones[0].fechas_viaje if habitaciones else ''
    fechas = fechas_viaje.split(' - ') if fechas_viaje else ['', '']
    checkin = f"{fechas[0]} 14:00" if fechas[0] else "No disponible"
    checkout = f"{fechas[1]} 12:00" if len(fechas) > 1 and fechas[1] else "No disponible"
    total = f"{reserva.precio_total} {moneda}"
    asunto = f"🧾 Confirmación de Reserva Hotel #{reserva.id}"

    html = f"""
    <div style="font-family:'Segoe UI', sans-serif; max-width:700px; margin:40px auto; border-radius:12px; overflow:hidden; box-shadow:0 0 10px rgba(0,0,0,0.1); background-color:#f4f6f8;">
        <div style="background:#003366; padding:30px 20px; text-align:center; color:#fff;">
            <img src="http://build.dev.travel-sys.loc:8000/static/images/ruta_Logo.jpeg" alt="Ruta Multiservice" style="width:130px; margin-bottom:15px; border-radius:10px;" />
            <h2 style="margin:0; font-size:24px;">¡Gracias por tu reserva en <strong>Ruta Multiservice</strong>!</h2>
            <p style="margin:10px 0 0; font-size:16px; color:#e0e0e0;">{encabezado}</p>
        </div>

        <div style="padding:30px; background-color:#ffffff;">
            <h3 style="color:#003366; border-bottom:2px solid #dedede; padding-bottom:8px;">🏨 Detalles del Hotel</h3>
            <p><strong>Hotel:</strong> {nombre_hotel}</p>
            <p><strong>Destino:</strong> {destino}</p>
            <p><strong>Check-in:</strong> {checkin}</p>
            <p><strong>Check-out:</strong> {checkout}</p>
            <p><strong>Total a pagar:</strong> <span style="color:#28a745; font-weight:bold;">{total}</span></p>
            <hr style="margin:30px 0 20px;">
            <h3 style="color:#003366; border-bottom:2px solid #dedede; padding-bottom:8px;">🛌 Habitaciones</h3>
    """

    for i, hab in enumerate(habitaciones, 1):
        adultos = [p for p in pasajeros if p.habitacion_id == hab.id and p.tipo == 'adulto']
        ninos = [p for p in pasajeros if p.habitacion_id == hab.id and p.tipo == 'nino']
        html += f"""
            <div style="background:#f8f9fa; padding:20px; border-radius:8px; margin-bottom:20px;">
                <h4 style="margin:0 0 10px; color:#005580;">Habitación {i} - {getattr(hab, 'habitacion_nombre', f'Habitación {i}')}</h4>
                <p><strong>Adultos ({len(adultos)}):</strong> {' / '.join(p.nombre for p in adultos) if adultos else 'N/A'}</p>
        """
        if ninos:
            html += f"<p><strong>Niños ({len(ninos)}):</strong> {' / '.join(p.nombre for p in ninos)}</p>"
        html += "</div>"

    html += f"""
            <hr style="margin-top:40px;">
            <footer style="text-align:center; color:#999; font-size:13px;">
                <p>Ruta Multiservice | 9666 Coral Way, Miami, FL 33165</p>
                <p><a href="mailto:info@rutamultiservice.com" style="color:#007bff; text-decoration:none;">info@rutamultiservice.com</a></p>
            </footer>
        </div>
    </div>
    """

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
        adultos = [p for p in pasajeros if p.habitacion_id == hab.id and p.tipo == 'adulto']
        ninos = [p for p in pasajeros if p.habitacion_id == hab.id and p.tipo == 'nino']
        texto += f"""
Habitación {i} - {getattr(hab, 'habitacion_nombre', f'Habitación {i}')}
  Adultos ({len(adultos)}): {' / '.join(p.nombre for p in adultos) if adultos else 'N/A'}
"""
        if ninos:
            texto += f"  Niños ({len(ninos)}): {' / '.join(p.nombre for p in ninos)}"

    texto += f"""

--------------------------------------------
Este correo fue enviado por Ruta Multiservice
9666 Coral Way, Miami, FL 33165
info@rutamultiservice.com
"""

    return asunto, html, texto


def enviar_email_basico(asunto, html, texto, destinatario):
    remitente = "booking@rutamultiservice.com"
    password = "Mariana201622*"

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje.attach(MIMEText(texto, "plain"))
    mensaje.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as servidor:
            servidor.starttls()
            servidor.login(remitente, password)
            servidor.sendmail(remitente, destinatario, mensaje.as_string())
            print(f"[OK] Correo enviado a {destinatario}")
    except Exception as e:
        print(f"[ERROR] Fallo al enviar el correo: {e}")


def enviar_correo_confirmacion_traslado(reserva):
    traslado = reserva.traslado
    pasajeros = Pasajero.objects.filter(traslado=traslado)
    encabezado = "Gracias por reservar su traslado con RUTA MULTISERVICE. Estamos procesando su solicitud."

    nombre = pasajeros.first().nombre if pasajeros.exists() else "Cliente"
    asunto = f"{'Confirmación' if reserva.estatus == 'confirmada' else 'Solicitud'} de Traslado #{reserva.id} – {nombre}"

    cuerpo_html = f"""
    <html><body>
    <p>{encabezado}</p>
    <h3>Traslado</h3>
    <p><b>Origen:</b> {traslado.origen}</p>
    <p><b>Destino:</b> {traslado.destino}</p>
    <p><b>Vehículo:</b> {traslado.vehiculo}</p>
    <p><b>Costo:</b> ${traslado.costo}</p>
    </body></html>
    """

    cuerpo_texto = f"""{encabezado}
Traslado:
Origen: {traslado.origen}
Destino: {traslado.destino}
Vehículo: {traslado.vehiculo}
Costo: ${traslado.costo}
"""

    enviar_email_basico(asunto, cuerpo_html, cuerpo_texto, reserva.email_empleado)


def enviar_correo_confirmacion_envio(reserva):
    envio = reserva.envio
    items = envio.items.all()
    encabezado = "Gracias por realizar su envío con RUTA MULTISERVICE. Hemos recibido su solicitud."

    remitente = envio.remitente
    destinatario = envio.destinatario

    total_valor = sum(item.valor_aduanal for item in items)
    total_peso = sum(item.peso for item in items)
    total_items = sum(item.cantidad for item in items)

    asunto = f"📦 Confirmación de Envío #{reserva.id} – {destinatario.nombre_completo}"

    html = f"""
    <div style="font-family:'Segoe UI', sans-serif; max-width:700px; margin:40px auto; background-color:#f4f6f8; border-radius:12px; overflow:hidden; box-shadow:0 0 10px rgba(0,0,0,0.1);">
        <div style="background:#003366; padding:30px 20px; text-align:center; color:#fff;">
            <img src="https://www.rutamultiservice.com/static/images/ruta_Logo.jpeg" alt="Ruta Multiservice" style="width:130px; margin-bottom:15px; border-radius:10px;" />
            <h2 style="margin:0; font-size:24px;">¡Gracias por tu envío con <strong>Ruta Multiservice</strong>!</h2>
            <p style="margin:10px 0 0; font-size:16px; color:#e0e0e0;">{encabezado}</p>
        </div>

        <div style="padding:30px; background-color:#ffffff;">
            <h3 style="color:#003366; border-bottom:2px solid #dedede; padding-bottom:8px;">📦 Detalles del Envío</h3>
            <p><strong>Remitente:</strong> {remitente.nombre_apellido}</p>
            <p><strong>Destinatario:</strong> {destinatario.nombre_completo}</p>
            <p><strong>CI:</strong> {destinatario.ci}</p>
            <p><strong>Teléfono:</strong> {destinatario.telefono}</p>
            <p><strong>Dirección:</strong> {destinatario.direccion_completa}</p>

            <hr style="margin:30px 0 20px;">
            <h3 style="color:#003366; border-bottom:2px solid #dedede; padding-bottom:8px;">📋 Artículos</h3>
    """

    for i, item in enumerate(items, 1):
        tipo = 'Aéreo' if item.tipo == 'air' else 'Marítimo'
        html += f"""
        <div style="background:#f8f9fa; padding:15px; border-left:4px solid {'#6366f1' if item.tipo == 'air' else '#f97316'}; border-radius:6px; margin-bottom:15px;">
            <p style="margin:0;"><strong>{i}. {item.descripcion}</strong> <span style="font-size:12px; padding:3px 6px; background:{'#e0e7ff' if item.tipo == 'air' else '#ffedd5'}; color:{'#4338ca' if item.tipo == 'air' else '#c2410c'}; border-radius:4px; margin-left:10px;">{tipo}</span></p>
            <p style="margin:4px 0 0; font-size:14px;">Cantidad: {item.cantidad} | Peso: {item.peso} kg</p>
            <p style="margin:2px 0; font-size:14px;">HBL: {item.hbl} | Valor Aduanal: ${item.valor_aduanal}</p>
            {"<p style='margin:2px 0; font-size:14px;'>Envío y Manejo: $" + str(item.envio_manejo) + "</p>" if item.tipo == 'maritime' and item.envio_manejo else ""}
        </div>
        """

    html += f"""
            <hr style="margin:30px 0;">
            <h3 style="color:#003366; border-bottom:2px solid #dedede; padding-bottom:8px;">📊 Resumen del Envío</h3>
            <p><strong>Total de artículos:</strong> {total_items}</p>
            <p><strong>Peso total:</strong> {total_peso} kg</p>
            <p><strong>Valor aduanal total:</strong> <span style="color:#28a745; font-weight:bold;">${total_valor}</span></p>
            <p><strong>Total a pagar:</strong> <span style="color:#28a745; font-weight:bold;">${reserva.precio_total}</span></p>

            <hr style="margin-top:40px;">
            <footer style="text-align:center; color:#999; font-size:13px;">
                <p>Ruta Multiservice | 6915 W Flagler St, Miami, FL 33144</p>
                <p><a href="mailto:info@rutamultiservice.com" style="color:#007bff; text-decoration:none;">info@rutamultiservice.com</a></p>
            </footer>
        </div>
    </div>
    """

    texto = f"""{encabezado}

Remitente: {remitente.nombre_apellido}
Destinatario: {destinatario.nombre_completo}
CI: {destinatario.ci}
Teléfono: {destinatario.telefono}
Dirección: {destinatario.direccion_completa}

Artículos:
"""
    for i, item in enumerate(items, 1):
        texto += f"""
  {i}. {item.descripcion} - Tipo: {'Aéreo' if item.tipo == 'air' else 'Marítimo'}
     Cantidad: {item.cantidad}, Peso: {item.peso} kg, Valor Aduanal: ${item.valor_aduanal}, HBL: {item.hbl}{" | Envío y Manejo: $" + str(item.envio_manejo) if item.tipo == 'maritime' and item.envio_manejo else ""}
"""

    texto += f"""

Resumen del Envío:
- Total artículos: {total_items}
- Peso total: {total_peso} kg
- Valor aduanal total: ${total_valor}
- Total a pagar: ${reserva.precio_total}

--------------------------------------------
Este correo fue enviado por Ruta Multiservice
6915 W Flagler St, Miami, FL 33144
info@rutamultiservice.com
"""

    enviar_email_basico(asunto, html, texto, reserva.email_empleado)


def enviar_correo_confirmacion_remesa(reserva):
    remesa = reserva.remesa
    encabezado = "Gracias por realizar su remesa con RUTA MULTISERVICE. Hemos recibido su solicitud."

    asunto = f"{'Confirmación' if reserva.estatus == 'confirmada' else 'Solicitud'} de Remesa #{reserva.id} – {remesa.destinatario}"

    cuerpo_html = f"""
    <html><body>
    <p>{encabezado}</p>
    <h3>Remesa</h3>
    <p><b>Remitente:</b> {remesa.remitente}</p>
    <p><b>Destinatario:</b> {remesa.destinatario}</p>
    <p><b>Importe enviado:</b> ${remesa.monto} {remesa.moneda}</p>
    </body></html>
    """

    cuerpo_texto = f"""{encabezado}
Remesa:
Remitente: {remesa.remitente}
Destinatario: {remesa.destinatario}
Importe enviado: ${remesa.monto} {remesa.moneda}
"""

    enviar_email_basico(asunto, cuerpo_html, cuerpo_texto, reserva.email_empleado)


def enviar_correo_confirmacion_certificado(reserva):
    cert = reserva.certificado_vacaciones
    encabezado = "Gracias por solicitar su Certificado de Vacaciones con RUTA MULTISERVICE."

    consumidor = cert.consumidor.nombre if cert.consumidor else "Cliente"
    asunto = f"{'Confirmación' if reserva.estatus == 'confirmada' else 'Solicitud'} de Certificado #{reserva.id} – {consumidor}"

    cuerpo_html = f"""
    <html><body>
    <p>{encabezado}</p>
    <h3>Certificado</h3>
    <p><b>Nombre:</b> {cert.nombre}</p>
    <p><b>Solo Adultos:</b> {"Sí" if cert.solo_adultos else "No"}</p>
    <p><b>Consumidor:</b> {consumidor}</p>
    <p><b>Precio:</b> ${cert.precio}</p>
    </body></html>
    """

    cuerpo_texto = f"""{encabezado}
Certificado:
Nombre: {cert.nombre}
Solo Adultos: {"Sí" if cert.solo_adultos else "No"}
Consumidor: {consumidor}
Precio: ${cert.precio}
"""

    enviar_email_basico(asunto, cuerpo_html, cuerpo_texto, reserva.email_empleado)



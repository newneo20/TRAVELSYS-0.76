# apps/backoffice/views.py

# apps/backoffice/views.py (o donde tengas esta vista)
from django.contrib import messages
from django.db import IntegrityError
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from .models import CadenaHotelera
# from .decorators import manager_required  # asumiendo que ya lo tienes

# ===============================
# Imports de la biblioteca estándar
# ===============================
import os
import json
import logging
import time
import requests
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from random import randint
from xml.dom import minidom

# ===============================
# Imports de Django
# ===============================
from django.forms import model_to_dict  # type: ignore
from django.http import HttpResponse, JsonResponse  # type: ignore
from django.shortcuts import render, get_object_or_404, redirect  # type: ignore
from django.contrib.auth import logout, login, authenticate  # type: ignore
from django.contrib.auth.decorators import login_required  # type: ignore
from django.contrib import messages  # type: ignore
from django.core.serializers import serialize  # type: ignore
from django.db.models import Q  # type: ignore
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from django.core.paginator import Paginator  # type: ignore
from django.core.exceptions import ValidationError, ObjectDoesNotExist  # type: ignore
from django.core.files.storage import default_storage  # type: ignore
from django.urls import reverse  # type: ignore
from django.db import transaction  # type: ignore
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET

# ===============================
# Imports locales
# ===============================
from apps.usuarios.decorators import manager_required  # type: ignore
from .models import (
    Hotel, PlanAlimenticio, Proveedor, PoloTuristico, Habitacion, TipoFee, Oferta, HotelFacility,
    HotelSetting, CadenaHotelera, Reserva, Pasajero, HabitacionReserva, OfertasEspeciales, Rentadora,
    Categoria, ModeloAuto, Location, CertificadoVacaciones, OpcionCertificado, Servicio, TasaCambio,
    Traslado, Transportista, Ubicacion, Vehiculo, Cliente, Contacto, Envio, Destinatario, Remitente,
    ItemEnvio, Remesa
)
from .forms import (
    PoloTuristicoForm, ProveedorForm, CadenaHoteleraForm, ReservaForm, PasajeroForm,
    HabitacionForm, OfertasEspecialesForm
)
from .funciones_externas import leer_datos_hoteles
from apps.booking.xml_builders_1way2italy import enviar_booking_api

logger = logging.getLogger(__name__)

BOOKING_WINDOW_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\s*-\s*\d{4}-\d{2}-\d{2}$")

@login_required
def logout_view(request):
    logout(request)    
    return redirect('login')


@login_required
def check_session_status(request):
    # Si el usuario está autenticado, devuelve "active", de lo contrario "inactive"
    return JsonResponse({'status': 'active'})


# ---------------------------------------- DASHBOARD / PANEL DE CONTROL ----------------------------------------#

@manager_required
@login_required
def dashboard(request):
    return render(request, 'backoffice/dashboard.html')


@manager_required
@login_required
def en_desarrollo(request):
    return render(request, 'backoffice/en_desarrollo.html')


@manager_required
@login_required
def en_mantenimiento(request):
    return render(request, 'backoffice/en_mantenimiento.html')

# =========================================================================================== #
# ---------------------------------------- PROVEEDORES -------------------------------------- #
# =========================================================================================== #

@manager_required
@login_required
def listar_proveedores(request):
    # Obtiene el parámetro de búsqueda (puedes usarlo luego para filtrar)
    query = request.GET.get('q', '')

    # Queryset base
    proveedores_qs = Proveedor.objects.all()

    # Si quieres filtrar por nombre o correo, descomenta y ajusta:
    # from django.db.models import Q
    # if query:
    #     proveedores_qs = proveedores_qs.filter(
    #         Q(nombre__icontains=query) |
    #         Q(correo1__icontains=query) |
    #         Q(correo2__icontains=query) |
    #         Q(correo3__icontains=query) |
    #         Q(telefono__icontains=query) |
    #         Q(direccion__icontains=query)
    #     )

    # Paginador: 10 proveedores por página
    paginator = Paginator(proveedores_qs, 10)
    page_number = request.GET.get('page')
    proveedores = paginator.get_page(page_number)

    return render(request, 'backoffice/proveedores/listar_proveedores.html', {
        'proveedores': proveedores,
        'query': query,
    })

@manager_required
@login_required
def crear_proveedor(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo1 = request.POST.get('correo1')
        correo2 = request.POST.get('correo2')
        correo3 = request.POST.get('correo3')
        telefono = request.POST.get('telefono')
        detalles_cuenta_bancaria = request.POST.get('detalles_cuenta_bancaria')
        direccion = request.POST.get('direccion')
        tipo = request.POST.get('tipo')
        servicios_ids = request.POST.getlist('servicios')

        # Inicializamos los campos dinámicos
        fee_adultos = request.POST.get('fee_adultos') or None
        fee_ninos = request.POST.get('fee_ninos') or None
        fee_noche = request.POST.get('fee_noche') or None

        # Creamos el proveedor
        nuevo_proveedor = Proveedor(
            nombre=nombre,
            correo1=correo1,
            correo2=correo2,
            correo3=correo3,
            telefono=telefono,
            detalles_cuenta_bancaria=detalles_cuenta_bancaria,
            direccion=direccion,
            tipo=tipo,
            fee_adultos=fee_adultos,
            fee_ninos=fee_ninos,
            fee_noche=fee_noche
        )
        nuevo_proveedor.save()

        nuevo_proveedor.servicios.set(servicios_ids)

        return redirect('backoffice:listar_proveedores')

    servicios = Servicio.objects.all()
    return render(request, 'backoffice/proveedores/crear_proveedor.html', {'servicios': servicios})


@manager_required
@login_required
def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)

    if request.method == 'POST':
        proveedor.nombre = request.POST.get('nombre')
        proveedor.correo1 = request.POST.get('correo1')
        proveedor.correo2 = request.POST.get('correo2')
        proveedor.correo3 = request.POST.get('correo3')
        proveedor.telefono = request.POST.get('telefono')
        proveedor.detalles_cuenta_bancaria = request.POST.get('detalles_cuenta_bancaria')
        proveedor.direccion = request.POST.get('direccion')
        proveedor.tipo = request.POST.get('tipo')

        proveedor.fee_adultos = request.POST.get('fee_adultos') or None
        proveedor.fee_ninos = request.POST.get('fee_ninos') or None
        proveedor.fee_noche = request.POST.get('fee_noche') or None

        servicios_ids = request.POST.getlist('servicios')
        proveedor.servicios.set(servicios_ids)

        proveedor.save()
        return redirect('backoffice:listar_proveedores')

    servicios = Servicio.objects.all()
    return render(request, 'backoffice/proveedores/editar_proveedor.html', {
        'proveedor': proveedor,
        'servicios': servicios
    })
    
@manager_required
@login_required
def eliminar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)

    if request.method == 'POST':
        if request.POST.get('confirm_text', '').strip().upper() != 'ELIMINAR':
            messages.error(request, "Debes escribir ELIMINAR para confirmar.")
        else:
            proveedor.delete()
            messages.success(request, "Proveedor eliminado correctamente.")
            return redirect('backoffice:listar_proveedores')

    return render(request, 'backoffice/proveedores/eliminar_proveedor.html', {'proveedor': proveedor})


# =========================================================================================== #
# ---------------------------------------- POLOS -------------------------------------------- #
# =========================================================================================== #
@manager_required
@login_required
def listar_polos(request):
    # Obtener término de búsqueda (cadena vacía si no se pasa)
    query = request.GET.get('q', '')

    # Queryset base
    polos_qs = PoloTuristico.objects.all()

    # Filtrar por nombre o país si hay búsqueda
    if query:
        polos_qs = polos_qs.filter(
            Q(nombre__icontains=query) |
            Q(pais__icontains=query)
        )

    # Paginación: 10 polos por página
    paginator = Paginator(polos_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/polos/listar_polos.html', {
        'page_obj': page_obj,
        'query': query,
    })
    
@manager_required
@login_required
def crear_polo_turistico(request):
    if request.method == 'POST':
        # Capturar los datos del formulario
        nombre = request.POST.get('nombre')
        pais = request.POST.get('pais')

        # Crear un nuevo PoloTuristico
        nuevo_polo = PoloTuristico(
            nombre=nombre,
            pais=pais,
        )
        nuevo_polo.save()
        return redirect('backoffice:listar_polos')

    return render(request, 'backoffice/polos/crear_polo_turistico.html')

@manager_required
@login_required
def editar_polo_turistico(request, polo_id):
    polo = get_object_or_404(PoloTuristico, id=polo_id)

    if request.method == 'POST':
        # Capturar los datos del formulario
        polo.nombre = request.POST.get('nombre')
        polo.pais = request.POST.get('pais')

        # Guardar los cambios
        polo.save()
        return redirect('backoffice:listar_polos')

    return render(request, 'backoffice/polos/editar_polo_turistico.html', {'polo': polo})

@manager_required
@login_required
def eliminar_polo(request, polo_id):
    polo = get_object_or_404(PoloTuristico, pk=polo_id)
    if request.method == 'POST':
        polo.delete()
        return redirect('backoffice:listar_polos')
    return render(request, 'backoffice/polos/eliminar_polo.html', {'polo': polo})

# =========================================================================================== #
# ---------------------------------------- HOTELES ------------------------------------------ #
# =========================================================================================== #

@manager_required
@login_required
def listar_hoteles(request):
    hoteles = Hotel.objects.all()
    query = request.GET.get('q', '')
    if query:
        hoteles = hoteles.filter(
            Q(hotel_nombre__icontains=query) |
            Q(proveedor__nombre__icontains=query) |
            Q(polo_turistico__nombre__icontains=query) |
            Q(cadena_hotelera__nombre__icontains=query)
        )

    paginator = Paginator(hoteles, 10)  # 10 hoteles por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'hoteles': page_obj,
        'query': query,
    }
    return render(request, 'backoffice/hoteles/listar_hoteles.html', context)

@manager_required
@login_required
def hotel_management(request, hotel_id=None):
    # Obtener listas de objetos para los campos de selección.
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()
    proveedores = Proveedor.objects.all()

    # Si se proporciona un `hotel_id`, obtenemos el hotel para editar.
    hotel = get_object_or_404(Hotel, id=hotel_id) if hotel_id else None

    # Obtener habitaciones, configuraciones, ofertas, e instalaciones relacionadas con el hotel.
    habitaciones = Habitacion.objects.filter(hotel_id=hotel_id) if hotel_id else None
    configuraciones = HotelSetting.objects.filter(hotel_id=hotel_id).first() if hotel_id else None
    ofertas = Oferta.objects.filter(hotel_id=hotel_id) if hotel_id else None
    instalaciones = HotelFacility.objects.filter(hotel_id=hotel_id) if hotel_id else None

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'hotel':
            # Crear o actualizar el hotel según la presencia del objeto `hotel`.
            if hotel:
                # Actualizar el hotel existente
                hotel.hotel_nombre = request.POST.get('hotel_nombre')
                hotel.polo_turistico_id = request.POST.get('polo_turistico')
                hotel.cadena_hotelera_id = request.POST.get('cadena_hotelera')
                hotel.proveedor_id = request.POST.get('proveedor')
                hotel.fee = request.POST.get('fee')
                hotel.tipo_fee = request.POST.get('tipo_fee')
                hotel.plan_alimenticio = request.POST.get('plan_alimenticio')
                hotel.descripcion_hotel = request.POST.get('descripcion_hotel')
                hotel.direccion = request.POST.get('direccion')
                hotel.checkin = request.POST.get('checkin')
                hotel.checkout = request.POST.get('checkout')
                hotel.orden = request.POST.get('orden')
                hotel.categoria = request.POST.get('categoria')
                hotel.solo_adultos = 'solo_adultos' in request.POST
                if 'foto_hotel' in request.FILES:
                    hotel.foto_hotel = request.FILES['foto_hotel']
                hotel.save()
                messages.success(request, 'Hotel actualizado correctamente.')
            else:
                # Crear un nuevo hotel
                nuevo_hotel = Hotel(
                    hotel_nombre=request.POST.get('hotel_nombre'),
                    polo_turistico_id=request.POST.get('polo_turistico'),
                    cadena_hotelera_id=request.POST.get('cadena_hotelera'),
                    proveedor_id=request.POST.get('proveedor'),
                    fee=request.POST.get('fee'),
                    tipo_fee=request.POST.get('tipo_fee'),
                    plan_alimenticio=request.POST.get('plan_alimenticio'),
                    descripcion_hotel=request.POST.get('descripcion_hotel'),
                    direccion=request.POST.get('direccion'),
                    checkin=request.POST.get('checkin'),
                    checkout=request.POST.get('checkout'),
                    orden=request.POST.get('orden'),
                    categoria=request.POST.get('categoria'),
                    solo_adultos='solo_adultos' in request.POST,
                    foto_hotel=request.FILES.get('foto_hotel', '')
                )
                nuevo_hotel.save()
                messages.success(request, 'Hotel creado correctamente.')
                return redirect('backoffice:listar_hoteles')

        elif form_type == 'configuraciones':
            # Manejar la configuración del hotel
            if configuraciones:
                configuraciones.edad_limite_nino = request.POST.get('edad_limite_nino', 0)
                configuraciones.edad_limite_infante = request.POST.get('edad_limite_infante', 0)
                configuraciones.cantidad_noches = request.POST.get('cantidad_noches', 0)
                configuraciones.save()
                messages.success(request, 'Configuración actualizada correctamente.')
            else:
                # Crear una nueva configuración si no existe
                HotelSetting.objects.create(
                    hotel=hotel,
                    edad_limite_nino=request.POST.get('edad_limite_nino', 0),
                    edad_limite_infante=request.POST.get('edad_limite_infante', 0),
                    cantidad_noches=request.POST.get('cantidad_noches', 0),
                )
                messages.success(request, 'Configuración creada correctamente.')

        # Otros tipos de formulario como habitaciones, ofertas e instalaciones pueden ser manejados aquí.

        return redirect('backoffice:editar_hotel', hotel_id=hotel.id if hotel else nuevo_hotel.id)

    # Renderizar la plantilla con los datos necesarios para el formulario.
    context = {
        'hotel': hotel,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
        'proveedores': proveedores,
        'habitaciones': habitaciones,
        'configuraciones': configuraciones,
        'ofertas': ofertas,
        'instalaciones': instalaciones,
    }
    return render(request, 'backoffice/hoteles/hotel_management.html', context)

@manager_required
@login_required
def crear_hotel(request):    
    if request.method == 'POST':
        # Obtener los valores del formulario
        hotel_nombre = request.POST.get('hotel_nombre')
        proveedor_id = request.POST.get('proveedor')
        fee = request.POST.get('fee')
        tipo_fee = request.POST.get('tipo_fee')
        polo_turistico_id = request.POST.get('polo_turistico')
        plan_alimenticio = request.POST.get('plan_alimenticio')
        descripcion_hotel = request.POST.get('descripcion_hotel')
        direccion = request.POST.get('direccion')
        checkin = request.POST.get('checkin')
        checkout = request.POST.get('checkout')
        orden = request.POST.get('orden')
        categoria = request.POST.get('categoria')
        cadena_hotelera_id = request.POST.get('cadena_hotelera')
        solo_adultos = request.POST.get('solo_adultos') == 'on'  # Checkboxes return 'on' if checked
        foto_hotel = request.FILES.get('foto_hotel')

        # Crear instancia del hotel
        nuevo_hotel = Hotel(
            hotel_nombre=hotel_nombre,
            proveedor=Proveedor.objects.get(id=proveedor_id) if proveedor_id else None,
            fee=fee,
            tipo_fee=tipo_fee,
            polo_turistico=PoloTuristico.objects.get(id=polo_turistico_id) if polo_turistico_id else None,
            plan_alimenticio=plan_alimenticio,
            descripcion_hotel=descripcion_hotel,
            direccion=direccion,
            checkin=checkin,
            checkout=checkout,
            orden=orden if orden else None,
            categoria=categoria if categoria else None,
            cadena_hotelera=CadenaHotelera.objects.get(id=cadena_hotelera_id) if cadena_hotelera_id else None,
            solo_adultos=solo_adultos,
            foto_hotel=foto_hotel.name if foto_hotel else None
        )

        # Guardar el hotel en la base de datos
        nuevo_hotel.save()

        # Redirigir a una página de éxito o a la lista de hoteles
        return redirect('backoffice:listar_hoteles')

    # Obtener datos para llenar los selects del formulario
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()

    # Renderizar el formulario con los datos
    context = {
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
    }
    return render(request, 'backoffice/hoteles/partials/form_hotel.html', context)

@manager_required
@login_required
def editar_hotel(request, hotel_id):
    # Obtener el hotel por ID o lanzar un error 404 si no existe
    hotel = get_object_or_404(Hotel, id=hotel_id)

    # Obtener listas de proveedores, polos turísticos, y cadenas hoteleras
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()

    # Obtener habitaciones relacionadas con el hotel
    habitaciones = Habitacion.objects.filter(hotel_id=hotel_id)

    # Obtener la configuración relacionada con el hotel (asumiendo que solo hay una por hotel)
    configuraciones = HotelSetting.objects.filter(hotel_id=hotel_id).first()

    # Obtener las ofertas relacionadas con el hotel
    ofertas = Oferta.objects.filter(hotel_id=hotel_id)

    # Obtener las instalaciones relacionadas con el hotel
    instalaciones = HotelFacility.objects.filter(hotel_id=hotel_id)

    if request.method == 'POST' and request.POST.get('form_type') == 'configuraciones':
        # Actualizar la configuración existente
        if configuraciones:
            configuraciones.edad_limite_nino = request.POST.get('edad_limite_nino', 0)
            configuraciones.edad_limite_infante = request.POST.get('edad_limite_infante', 0)
            configuraciones.cantidad_noches = request.POST.get('cantidad_noches', 0)
            configuraciones.save()
            messages.success(request, 'Configuración actualizada correctamente.')
        else:
            # Crear una nueva configuración si no existe
            HotelSetting.objects.create(
                hotel=hotel,
                edad_limite_nino=request.POST.get('edad_limite_nino', 0),
                edad_limite_infante=request.POST.get('edad_limite_infante', 0),
                cantidad_noches=request.POST.get('cantidad_noches', 0),
            )
            messages.success(request, 'Configuración creada correctamente.')

        return redirect('backoffice:editar_hotel', hotel_id=hotel_id)

    # Renderizar el formulario con los datos actuales del hotel
    context = {
        'hotel': hotel,
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
        'habitaciones': habitaciones,
        'configuraciones': configuraciones,
        'ofertas': ofertas,
        'instalaciones': instalaciones,
    }
    return render(request, 'backoffice/hoteles/hotel_management.html', context)

#@manager_required
#@login_required
#def listar_habitaciones(request, hotel_id):
#    hotel = get_object_or_404(Hotel, id=hotel_id)
#    habitaciones = Habitacion.objects.filter(hotel=hotel)
#    data = {
#        'habitaciones': [
#            {
#                'id': habitacion.id,
#                'tipo_habitacion': habitacion.tipo,
#                'descripcion': habitacion.descripcion,
#                'capacidad_habitacion': habitacion.max_capacidad,
#            }
#            for habitacion in habitaciones
#        ]
#    }
#    return JsonResponse(data)


# Vista para guardar una nueva habitación
@manager_required
@login_required
def guardar_habitacion(request, hotel_id):
    
    print('*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/')
    print('--- ENTRO A GUARDAR HABITACION ---')
    print('*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/')
    
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        
        # Obtener los valores del formulario        
        tipo = request.POST.get('tipo', '')
        descripcion = request.POST.get('descripcion', '')
        adultos = request.POST.get('adultos', '0')  # Ajustar el nombre del campo si es necesario
        ninos = request.POST.get('ninos', '0')  # Ajustar el nombre del campo si es necesario
        max_capacidad = request.POST.get('max_capacidad', '0')  # Ajustar el nombre del campo si es necesario
        min_capacidad = request.POST.get('min_capacidad', '0')  # Ajustar el nombre del campo si es necesario
        descripcion_capacidad = request.POST.get('descripcion_capacidad', '')
        admite_3_con_1 = request.POST.get('admite_3_con_1') == 'on'
        solo_adultos = request.POST.get('solo_adultos') == 'on'

        # Convertir valores a los tipos correctos si es necesario
        try:
            adultos = int(adultos)
            ninos = int(ninos)
            max_capacidad = int(max_capacidad)
            min_capacidad = int(min_capacidad)
        except ValueError as e:
            print(f"Error al convertir valores a enteros: {e}")



        # Guardar la habitación
        habitacion = Habitacion(
            hotel=hotel,
            tipo=tipo,
            descripcion=descripcion,
            adultos=adultos,
            ninos=ninos,
            max_capacidad=max_capacidad,
            min_capacidad=min_capacidad,
            descripcion_capacidad=descripcion_capacidad,
            admite_3_con_1=admite_3_con_1,
            solo_adultos=solo_adultos
        )
        habitacion.save()

        return JsonResponse({'success': True, 'message': 'Habitación guardada exitosamente.'})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

# Vista para obtener los datos de una habitación específica
@login_required
def obtener_habitacion_test(request, habitacion_id):
    # Validar que solo se permita GET
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    # Obtener la habitación o devolver 404
    habitacion = get_object_or_404(Habitacion, pk=habitacion_id)

    # Construir respuesta
    data = {
        'habitacion': {
            'id': habitacion.id,
            'tipo': habitacion.tipo,
            'descripcion': habitacion.descripcion,
            'max_capacidad': habitacion.max_capacidad,
            'min_capacidad': habitacion.min_capacidad,
            'adultos': habitacion.adultos,
            'ninos': habitacion.ninos,
            'descripcion_capacidad': habitacion.descripcion_capacidad,
            'admite_3_con_1': habitacion.admite_3_con_1,
            'solo_adultos': habitacion.solo_adultos,
        }
    }
    return JsonResponse(data)

@login_required
def editar_oferta(request, oferta_id):
    return JsonResponse({'oferta_id': oferta_id})

def _to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "t", "yes", "y", "si", "sí"):
            return True
        if v in ("0", "false", "f", "no", "n"):
            return False
    return default

def _to_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _to_decimal(value, default=None):
    try:
        if value in (None, ""):
            return default
        return Decimal(str(value))
    except Exception:
        return default

@login_required
@require_POST
@transaction.atomic
def crear_editar_oferta(request):
    """
    Crea o actualiza una Oferta asociada a un Hotel.
    - Espera JSON en el body.
    - Valida hotel_id obligatorio.
    - Si viene oferta_id (o id) actualiza, si no, crea.
    - Valida formato booking_window: 'YYYY-MM-DD - YYYY-MM-DD'
    - Maneja bool/int/decimal en campos comunes.
    - Devuelve JSON con id de la oferta y mensaje.
    """
    # 1) Parseo seguro del JSON
    try:
        raw_body = request.body.decode("utf-8") if request.body else "{}"
        data = json.loads(raw_body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "JSON inválido en el cuerpo de la solicitud."},
            status=400
        )

    logger.debug("crear_editar_oferta | DATA RECIBIDA: %s", data)

    # 2) Validaciones básicas
    oferta_id = data.get("oferta_id") or data.get("id")
    hotel_id = data.get("hotel_id")
    if not hotel_id:
        return JsonResponse(
            {"status": "error", "message": "Debe especificar 'hotel_id'."},
            status=400
        )

    # 3) Obtener hotel y oferta (cuando aplique)
    hotel = get_object_or_404(Hotel, pk=hotel_id)

    if oferta_id:
        oferta = get_object_or_404(Oferta, pk=oferta_id)
        creando = False
        mensaje = "Oferta actualizada exitosamente."
    else:
        oferta = Oferta(hotel=hotel)
        creando = True
        mensaje = "Oferta creada exitosamente."

    # Si actualizas, garantiza la asociación correcta con el hotel indicado
    oferta.hotel = hotel

    # 4) Whitelist de campos permitidos a asignar desde el JSON
    #    (Ajusta esta lista a tu modelo real)
    FIELD_MAP = {
        # booleanos
        "disponible": ("bool", "disponible"),

        # strings
        "codigo": ("str", "codigo"),
        "tipo_habitacion": ("str", "tipo_habitacion"),
        "temporada": ("str", "temporada"),
        "booking_window": ("str", "booking_window"),
        "sencilla": ("str", "sencilla"),
        "doble": ("str", "doble"),
        "triple": ("str", "triple"),
        "primer_nino": ("str", "primer_nino"),
        "segundo_nino": ("str", "segundo_nino"),
        "un_adulto_con_ninos": ("str", "un_adulto_con_ninos"),
        "primer_nino_con_un_adulto": ("str", "primer_nino_con_un_adulto"),
        "segundo_nino_con_un_adulto": ("str", "segundo_nino_con_un_adulto"),
        "edad_nino": ("str", "edad_nino"),
        "edad_infante": ("str", "edad_infante"),
        "tipo_fee": ("str", "tipo_fee"),

        # enteros
        "noches_minimas": ("int", "noches_minimas"),
        "cantidad_habitaciones": ("int", "cantidad_habitaciones"),

        # decimales (si en tu modelo son CharField, cámbialos a "str")
        "fee_doble": ("dec", "fee_doble"),
        "fee_triple": ("dec", "fee_triple"),
        "fee_sencilla": ("dec", "fee_sencilla"),
        "fee_primer_nino": ("dec", "fee_primer_nino"),
        "fee_segundo_nino": ("dec", "fee_segundo_nino"),
    }

    # 5) Asignación con casting básico
    for incoming_key, (kind, model_field) in FIELD_MAP.items():
        if incoming_key not in data:
            continue  # no lo envió → no tocar
        val = data[incoming_key]

        if kind == "bool":
            setattr(oferta, model_field, _to_bool(val, default=False))
        elif kind == "int":
            setattr(oferta, model_field, _to_int(val, default=None))
        elif kind == "dec":
            setattr(oferta, model_field, _to_decimal(val, default=None))
        else:  # "str"
            setattr(oferta, model_field, (val or "").strip())

    # 6) Validación específica de booking_window si vino
    if "booking_window" in data:
        bw = (data.get("booking_window") or "").strip()
        if bw and not BOOKING_WINDOW_RE.match(bw):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Formato inválido de 'booking_window'. Use 'YYYY-MM-DD - YYYY-MM-DD'."
                },
                status=400
            )

    # Log antes de guardar (opcional)
    logger.debug("crear_editar_oferta | OFERTA ANTES DE GUARDAR: %s", model_to_dict(oferta))

    # 7) Guardar
    try:
        oferta.full_clean()  # valida el Model antes de persistir
        oferta.save()
    except Exception as e:
        logger.exception("Error guardando Oferta:")
        return JsonResponse(
            {"status": "error", "message": f"Error al guardar la oferta: {e}"},
            status=400
        )

    # 8) Respuesta
    payload = {
        "status": "success",
        "message": mensaje,
        "data": {
            "id": oferta.id,
            "hotel_id": oferta.hotel_id,
        }
    }
    status_code = 201 if creando else 200
    return JsonResponse(payload, status=status_code)

# Vista para editar una habitación existente
@manager_required
@login_required
def editar_habitacion(request, habitacion_id):
    if request.method == 'POST':
        habitacion = get_object_or_404(Habitacion, id=habitacion_id)
        
        habitacion.tipo = request.POST.get('tipo')
        habitacion.descripcion = request.POST.get('descripcion')
        habitacion.adultos = request.POST.get('adultos')
        habitacion.ninos = request.POST.get('ninos',)
        habitacion.max_capacidad = request.POST.get('max_capacidad')
        habitacion.min_capacidad = request.POST.get('min_capacidad')
        habitacion.descripcion_capacidad = request.POST.get('descripcion_capacidad')
        habitacion.admite_3_con_1 = request.POST.get('admite_3_con_1') == 'on'
        habitacion.solo_adultos = request.POST.get('solo_adultos') == 'on'

        
        # Actualiza otros campos
        habitacion.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Vista para eliminar una habitación
#@manager_required
#@login_required
#def eliminar_habitacion(request, habitacion_id):
#    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
#    habitacion.delete()
#    return JsonResponse({'success': True})

@manager_required
@login_required
def hotel_rooms(request):    
    return render(request, 'backoffice/hotel_rooms.html')

@manager_required
@login_required
def hotel_settings(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    setting, created = HotelSetting.objects.get_or_create(hotel=hotel)
    
    context = {
        'setting': setting,
        'hotel': hotel
    }
    return render(request, 'backoffice/hotel_settings.html', context)

#@csrf_exempt
#@login_required
#def guardar_configuracion_hotel(request, hotel_id):
#    if request.method == 'POST':
#        hotel = get_object_or_404(Hotel, id=hotel_id)
#        setting, created = HotelSetting.objects.get_or_create(hotel=hotel)
#
#        try:
#            setting.edad_limite_nino = int(request.POST.get('edadLimite_nino', 0))
#            setting.edad_limite_infante = int(request.POST.get('edadLimite_infante', 0))
#            setting.cantidad_noches = int(request.POST.get('cantidad_noches', 0))
#            setting.save()
#            return JsonResponse({'status': 'success'})
#        except ValueError as e:
#            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
#
#    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@manager_required
@login_required
def hotel_facilities(request):
    return render(request, 'backoffice/hotel_facilities.html')

@manager_required
@login_required
def hotel_discounts(request):
    return render(request, 'backoffice/hotel_discounts.html')

@manager_required
@login_required
def hotel_tabs(request):
    if request.method == 'POST':
        # Código para manejar la creación del hotel
        hotel_nombre = request.POST.get('hotel_nombre')
        polo_turistico_id = request.POST.get('polo_turistico')
        proveedor_id = request.POST.get('proveedor')
        fee = request.POST.get('fee')
        tipo_fee = request.POST.get('tipo_fee')
        plan_alimenticio = request.POST.get('plan_alimenticio')
        descripcion_hotel = request.POST.get('descripcion_hotel')
        direccion = request.POST.get('direccion')
        checkin = request.POST.get('checkin')
        checkout = request.POST.get('checkout')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        orden = request.POST.get('orden')
        foto_hotel = request.POST.get('foto_hotel')

        # Validar y guardar el hotel
        hotel = Hotel(
            hotel_nombre=hotel_nombre,
            polo_turistico_id=polo_turistico_id,
            proveedor_id=proveedor_id,
            fee=fee,
            tipo_fee=tipo_fee,
            plan_alimenticio=plan_alimenticio,
            descripcion_hotel=descripcion_hotel,
            direccion=direccion,
            checkin=checkin,
            checkout=checkout,
            latitud=latitud,
            longitud=longitud,
            orden=orden,
            foto_hotel=foto_hotel
        )
        hotel.save()
        
        return redirect('hotel_tabs_edit', hotel_id=hotel.id)

    else:
        proveedores = Proveedor.objects.all()
        polos_turisticos = PoloTuristico.objects.all()
        cadenas_hoteleras = CadenaHotelera.objects.all()
        
        context = {
            'proveedores': proveedores,
            'polos_turisticos': polos_turisticos,
            'cadenas_hoteleras' : cadenas_hoteleras,
            'hotel': None  # Ajuste para manejar el hotel_id en la plantilla
        }
        return render(request, 'backoffice/hotel_tabs.html', context)

@manager_required
@login_required
def hotel_tabs_edit(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    if request.method == 'POST':
        # Código para manejar la edición del hotel
        hotel.hotel_nombre = request.POST.get('hotel_nombre')
        hotel.polo_turistico = request.POST.get('polo_turistico')
        hotel.proveedor = request.POST.get('proveedor')
        hotel.fee = request.POST.get('fee')
        hotel.tipo_fee = request.POST.get('tipo_fee')
        hotel.plan_alimenticio = request.POST.get('plan_alimenticio')
        hotel.descripcion_hotel = request.POST.get('descripcion_hotel')
        hotel.direccion = request.POST.get('direccion')
        hotel.checkin = request.POST.get('checkin')
        hotel.checkout = request.POST.get('checkout')
        hotel.latitud = request.POST.get('latitud')
        hotel.longitud = request.POST.get('longitud')
        hotel.orden = request.POST.get('orden')
        hotel.foto_hotel = request.POST.get('foto_hotel')
        hotel.save()
        return redirect('hotel_tabs_edit', hotel_id=hotel.id)
    
    else:
        proveedores = Proveedor.objects.all()
        polos_turisticos = PoloTuristico.objects.all()          
        cadenas_hoteleras = CadenaHotelera.objects.all()
        
        context = {
            'hotel': hotel,
            'proveedores': proveedores,
            'cadenas_hoteleras': cadenas_hoteleras,
            'polos_turisticos': polos_turisticos,
        }
        return render(request, 'backoffice/hotel_tabs_edit.html', context)

@manager_required
@login_required
def hotel_content(request):
    return render(request, 'backoffice/hotel_content.html')

@manager_required
@login_required
def hotel_editar(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    context = {
        'hotel': hotel,
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
    }
    return render(request, 'backoffice/hotel_editar.html', context)

@manager_required
@login_required
def guardar_hotel_editado(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    if request.method == 'POST':
        hotel.hotel_nombre = request.POST.get('hotel_nombre', '')
        hotel.polo_turistico_id = request.POST.get('polo_turistico')
        hotel.cadena_hotelera_id = request.POST.get('cadena_hotelera')
        hotel.proveedor_id = request.POST.get('proveedor')
        hotel.fee = request.POST.get('fee', '')
        hotel.tipo_fee = request.POST.get('tipo_fee', '')
        hotel.plan_alimenticio = request.POST.get('plan_alimenticio', '')
        hotel.descripcion_hotel = request.POST.get('descripcion_hotel', '')
        hotel.direccion = request.POST.get('direccion', '')
        hotel.checkin = request.POST.get('checkin', '')
        hotel.checkout = request.POST.get('checkout', '')
        hotel.orden = request.POST.get('orden', None)
        hotel.categoria = request.POST.get('categoria', None)
        hotel.foto_hotel = request.FILES.get('foto_hotel', None)
        hotel.solo_adultos = 'solo_adultos' in request.POST

        # Guardar el hotel
        hotel.save()

        # Redirigir a la misma página para ver los cambios
        return redirect('backoffice:hotel_tabs_edit', hotel_id=hotel.id)

    # Obtener datos necesarios para el formulario
    polos_turisticos = PoloTuristico.objects.all()
    cadenas_hoteleras = CadenaHotelera.objects.all()
    proveedores = Proveedor.objects.all()

    context = {
        'hotel': hotel,
        'polos_turisticos': polos_turisticos,
        'cadenas_hoteleras': cadenas_hoteleras,
        'proveedores': proveedores,
    }

    return render(request, 'backoffice/hotel_editar.html', context)

@manager_required
@login_required
def guardar_hotel(request):
    if request.method == 'POST':
        hotel_nombre = request.POST.get('hotel_nombre')
        polo_turistico_id = request.POST.get('polo_turistico')
        proveedor_id = request.POST.get('proveedor')
        fee = request.POST.get('fee')
        tipo_fee = request.POST.get('tipo_fee')
        plan_alimenticio = request.POST.get('plan_alimenticio')
        descripcion_hotel = request.POST.get('descripcion_hotel')
        direccion = request.POST.get('direccion')
        checkin = request.POST.get('checkin')
        checkout = request.POST.get('checkout')
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        orden = request.POST.get('orden')
        foto_hotel = request.POST.get('foto_hotel')
        categoria = request.POST.get('categoria')

        # Validación manual
        if hotel_nombre and polo_turistico_id and proveedor_id:
            try:
                polo_turistico = PoloTuristico.objects.get(id=polo_turistico_id)
                proveedor = Proveedor.objects.get(id=proveedor_id)

                hotel = Hotel.objects.create(
                    hotel_nombre=hotel_nombre,
                    polo_turistico=polo_turistico,
                    proveedor=proveedor,
                    fee=fee,
                    tipo_fee=tipo_fee,
                    plan_alimenticio=plan_alimenticio,
                    descripcion_hotel=descripcion_hotel,
                    direccion=direccion,
                    checkin=checkin,
                    checkout=checkout,
                    latitud=latitud,
                    longitud=longitud,
                    orden=orden,
                    foto_hotel=foto_hotel,
                    categoria=categoria,
                )
                return redirect('backoffice:hotel_tabs_edit', hotel_id=hotel.id)
            except PoloTuristico.DoesNotExist:
                return HttpResponse('Polo Turístico no existe', status=400)
            except Proveedor.DoesNotExist:
                return HttpResponse('Proveedor no existe', status=400)
        else:
            return HttpResponse('Datos incompletos o inválidos', status=400)
    else:
        return HttpResponse('Método no permitido', status=405)

@manager_required
@login_required
def eliminar_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    if request.method == 'POST':
        hotel.delete()
        return redirect('backoffice:listar_hoteles')
    return render(request, 'backoffice/hoteles/eliminar_hotel.html', {'hotel': hotel})

# ---------------------------------------- CADENAS HOTELERAS ---------------------------------------- #
@manager_required
@login_required
def listar_cadenas_hoteleras(request):
    # Obtener término de búsqueda (o cadena vacía si no se pasa)
    query = request.GET.get('q', '')

    # Queryset base
    cadenas_qs = CadenaHotelera.objects.all()

    # Filtrar por nombre o descripción si hay búsqueda
    if query:
        cadenas_qs = cadenas_qs.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query)
        )

    # Paginación: 5 cadenas hoteleras por página
    paginator = Paginator(cadenas_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/cadena_hotelera/listar_cadenas_hoteleras.html', {
        'page_obj': page_obj,
        'query': query,
    })
    

@manager_required
@login_required
def crear_cadena_hotelera(request):
    errores = {}
    valores = {}
    error_general = ""

    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        descripcion = (request.POST.get('descripcion') or '').strip()
        valores = {"nombre": nombre, "descripcion": descripcion}

        # Validaciones
        if not nombre:
            errores['nombre'] = _("El nombre es obligatorio.")
        elif len(nombre) > 255:
            errores['nombre'] = _("Máximo 255 caracteres.")
        elif CadenaHotelera.objects.filter(nombre__iexact=nombre).exists():
            errores['nombre'] = _("Ya existe una cadena con ese nombre.")

        if not errores:
            try:
                CadenaHotelera.objects.create(
                    nombre=nombre,
                    descripcion=descripcion or None
                )
                messages.success(request, _("Cadena hotelera creada correctamente."))
                return redirect('backoffice:listar_cadenas_hoteleras')
            except IntegrityError:
                error_general = _("No se pudo guardar. Inténtalo de nuevo.")

    ctx = {
        "errores": errores,
        "valores": valores,
        "error_general": error_general,
    }
    return render(request, 'backoffice/cadena_hotelera/crear_cadena_hotelera.html', ctx)



@manager_required
@login_required
def editar_cadena_hotelera(request, pk):
    obj = get_object_or_404(CadenaHotelera, pk=pk)

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        descripcion = (request.POST.get("descripcion") or "").strip()

        if not nombre:
            messages.error(request, "El nombre es obligatorio.")
            # re‑render con el objeto actual (ya está precargado en el template)
            return render(request, "backoffice/cadena_hotelera/editar_cadena_hotelera.html", {"obj": obj})

        # Guardar
        obj.nombre = nombre
        obj.descripcion = descripcion or None
        obj.save()
        messages.success(request, "Cadena actualizada correctamente.")
        return redirect("backoffice:listar_cadenas_hoteleras")

    # GET
    return render(
        request,
        "backoffice/cadena_hotelera/editar_cadena_hotelera.html",
        {"obj": obj},
    )

@manager_required
@login_required
def eliminar_cadena_hotelera(request, pk):
    cadena_hotelera = get_object_or_404(CadenaHotelera, pk=pk)
    if request.method == 'POST':
        cadena_hotelera.delete()
        return redirect('backoffice:listar_cadenas_hoteleras')
    return render(request, 'backoffice/cadena_hotelera/eliminar_cadena_hotelera.html', {'cadena_hotelera': cadena_hotelera})

# ---------------------------------------- HABITACIONES ---------------------------------------- #
@manager_required
@login_required
def listar_habitaciones(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    habitaciones = Habitacion.objects.filter(hotel=hotel)

    context = {
        'hotel': hotel,
        'habitaciones': habitaciones
    }

    return render(request, 'backoffice/listar_habitaciones.html', context)

@manager_required
@login_required
def crear_habitacion(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    context = {
        'hotel': hotel,
    }
    return render(request, 'backoffice/hotel_rooms.html', context)

@manager_required
@login_required
def eliminar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    hotel_id = habitacion.hotel.id

    if request.method == 'POST':
        habitacion.delete()
        # Redirige usando el namespace si corresponde
        return redirect(reverse('backoffice:editar_hotel', args=[hotel_id]))

    context = {
        'habitacion': habitacion,
        'hotel_id': hotel_id
    }

    return render(request, 'backoffice/eliminar_habitacion.html', context)

# ---------------------------------------- HABITACIONES OFERTAS ---------------------------------------- #
@manager_required
@login_required
def hotel_offers(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    habitaciones = hotel.habitaciones.all()  # Usar el related_name definido en el modelo Habitacion
    ofertas = Oferta.objects.filter(hotel=hotel)

    context = {
        'hotel': hotel,
        'habitaciones': habitaciones,
        'ofertas': ofertas,
    }
    return render(request, 'backoffice/hotel_offers.html', context)

@manager_required
@login_required
def hotel_crear_offers(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)
    habitaciones = hotel.habitaciones.all()  # Usar el related_name definido en el modelo Habitacion
    context = {
        'hotel': hotel,
        'habitaciones': habitaciones,
    }
    return render(request, 'backoffice/hotel_crear_offers.html', context)

@manager_required
@login_required
def guardar_oferta(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)

    if request.method == 'POST':
        disponible = request.POST.get('disponible') == 'on'
        codigo = request.POST.get('codigo_oferta')
        tipo_habitacion = request.POST.get('tipoHabitacion_oferta')
        temporada = request.POST.get('temporada')
        booking_window = request.POST.get('booking_window')
        sencilla = request.POST.get('sencilla_oferta')
        doble = request.POST.get('doble_oferta')
        triple = request.POST.get('triple_oferta')
        primer_nino = request.POST.get('primerNino_oferta')
        segundo_nino = request.POST.get('segundoNino_oferta')
        un_adulto_con_ninos = request.POST.get('un_adulto_con_ninos')
        primer_nino_con_un_adulto = request.POST.get('primer_nino_con_un_adulto')
        segundo_nino_con_un_adulto = request.POST.get('segundo_nino_con_un_adulto')
        edad_nino = request.POST.get('edad_nino')
        edad_infante = request.POST.get('edad_infante')
        noches_minimas = request.POST.get('noches_minimas')

        oferta = Oferta(
            hotel=hotel,
            disponible=disponible,
            codigo=codigo,
            tipo_habitacion=tipo_habitacion,
            temporada=temporada,
            booking_window=booking_window,
            sencilla=sencilla,
            doble=doble,
            triple=triple,
            primer_nino=primer_nino,
            segundo_nino=segundo_nino,
            un_adulto_con_ninos=un_adulto_con_ninos,
            primer_nino_con_un_adulto=primer_nino_con_un_adulto,
            segundo_nino_con_un_adulto=segundo_nino_con_un_adulto,
            edad_nino=edad_nino,
            edad_infante=edad_infante,
            noches_minimas=noches_minimas,
        )
        oferta.save()

        return redirect('backoffice:hotel_offers', hotel_id=hotel_id)

    context = {
        'hotel': hotel,
    }
    return render(request, 'backoffice/hotel_crear_offers.html', context)

@manager_required
@login_required
def eliminar_oferta(request, oferta_id):
    oferta = get_object_or_404(Oferta, id=oferta_id)
    hotel_id = oferta.hotel.id
    oferta.delete()
    return redirect('backoffice:hotel_offers', hotel_id=hotel_id)

@manager_required
@login_required
def cargar_datos_hoteles(request, hotel_id):
    ruta_archivo = os.path.join('backoffice/static/backoffice/plantilla_hoteles.xlsx')
    datos_hoteles = leer_datos_hoteles(ruta_archivo)
    
    # Obtener el nombre del hotel de los parámetros de la solicitud
    hotel = get_object_or_404(Hotel, id=hotel_id)
    print(f"Hotel: ID: {hotel.id}, Nombre: {hotel.hotel_nombre}")
    
    hotel_nombre = hotel.hotel_nombre
    hotel_data = next((hotel for hotel in datos_hoteles if hotel['nombre_hotel'] == hotel_nombre), None)
    print(f"Hotel data: {hotel_data}")
    habitaciones = hotel_data['habitaciones'] if hotel_data else []

    return JsonResponse({'ofertas': habitaciones})

@manager_required
@login_required
def eliminar_oferta(request, hotel_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            oferta_id = data.get('id')
            oferta = Oferta.objects.get(id=oferta_id)
            oferta.delete()
            return JsonResponse({'status': 'success'}, status=200)
        except Oferta.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Oferta no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@manager_required
@login_required
def guardar_todas_ofertas(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        ofertas_data = json.loads(request.body).get('ofertas', [])

        for oferta_data in ofertas_data:
            temporada = oferta_data['temporada']
            booking_window = oferta_data['booking_window']
            tipo_habitacion = oferta_data['tipo_habitacion']
            cantidad_habitaciones = oferta_data.get('cantidad_habitaciones', 1)

            # Verificar que no existan dos ofertas con la misma temporada exacta
            if Oferta.objects.filter(hotel=hotel, tipo_habitacion=tipo_habitacion, temporada=temporada, booking_window=booking_window).exists():
                continue

            oferta = Oferta(
                hotel=hotel,
                disponible=oferta_data['disponible'],
                codigo=oferta_data['codigo'],
                tipo_habitacion=tipo_habitacion,
                temporada=temporada,
                booking_window=booking_window,
                sencilla=oferta_data['sencilla'],
                doble=oferta_data['doble'],
                triple=oferta_data['triple'],
                primer_nino=oferta_data['primer_nino'],
                segundo_nino=oferta_data['segundo_nino'],
                un_adulto_con_ninos=oferta_data['un_adulto_con_ninos'],
                primer_nino_con_un_adulto=oferta_data['primer_nino_con_un_adulto'],
                segundo_nino_con_un_adulto=oferta_data['segundo_nino_con_un_adulto'],
                edad_nino=oferta_data['edad_nino'],
                edad_infante=oferta_data['edad_infante'],
                noches_minimas=oferta_data['noches_minimas'],
                cantidad_habitaciones=cantidad_habitaciones,
                tipo_fee=oferta_data.get('tipo_fee'),                  # Nuevo campo
                fee_doble=oferta_data.get('fee_doble'),                # Nuevo campo
                fee_triple=oferta_data.get('fee_triple'),              # Nuevo campo
                fee_sencilla=oferta_data.get('fee_sencilla'),          # Nuevo campo
                fee_primer_nino=oferta_data.get('fee_primer_nino'),    # Nuevo campo
                fee_segundo_nino=oferta_data.get('fee_segundo_nino')   # Nuevo campo
            )
            oferta.save()

        return JsonResponse({'message': 'Ofertas guardadas exitosamente'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@manager_required
@login_required
def guardar_instalaciones_hotel(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        data = request.POST
        
        facility, created = HotelFacility.objects.update_or_create(
            hotel=hotel,  # Usa el campo de relación correctamente
            defaults={
                'articulos_aseo': data.get('articulos_aseo') == 'true',
                'inodoro': data.get('inodoro') == 'true',
                'toallas': data.get('toallas') == 'true',
                'bano_privado': data.get('bano_privado') == 'true',
                'banera_ducha': data.get('banera_ducha') == 'true',
                'secador_pelo': data.get('secador_pelo') == 'true',
                'extintores': data.get('extintores') == 'true',
                'detectores_humo': data.get('detectores_humo') == 'true',
                'cctv': data.get('cctv') == 'true',
                'ropa_cama': data.get('ropa_cama') == 'true',
                'armario_ropero': data.get('armario_ropero') == 'true',
                'bar': data.get('bar') == 'true',
                'restaurante': data.get('restaurante') == 'true',
                'menu_ninos': data.get('menu_ninos') == 'true',
                'menu_dietetico': data.get('menu_dietetico') == 'true',
                'desayuno': data.get('desayuno') == 'true',
                'tetera_cafetera': data.get('tetera_cafetera') == 'true',
                'ascensor': data.get('ascensor') == 'true',
                'discapacitados': data.get('discapacitados') == 'true',
                'hipoalergenico': data.get('hipoalergenico') == 'true',
                'habitaciones_familiares': data.get('habitaciones_familiares') == 'true',
                'prohibido_fumar': data.get('prohibido_fumar') == 'true',
                'calefaccion': data.get('calefaccion') == 'true',
                'alfombrado': data.get('alfombrado') == 'true',
                'instalaciones_planchar': data.get('instalaciones_planchar') == 'true',
                'plancha': data.get('plancha') == 'true',
                'guardaequipaje': data.get('guardaequipaje') == 'true',
                'factura_proporcionada': data.get('factura_proporcionada') == 'true',
                'recepcion_24h': data.get('recepcion_24h') == 'true',
                'checkin_checkout_privado': data.get('checkin_checkout_privado') == 'true',
                'tv_pantalla_plana': data.get('tv_pantalla_plana') == 'true',
                'radio': data.get('radio') == 'true',
                'canales_via_satellite': data.get('canales_via_satellite') == 'true',
                'tv': data.get('tv') == 'true',
                'telefono': data.get('telefono') == 'true',
                'lavanderia': data.get('lavanderia') == 'true',
                'tintoreria': data.get('tintoreria') == 'true',
                'limpieza_diaria': data.get('limpieza_diaria') == 'true'
            }
        )
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'fail'}, status=400)

@login_required
def guardar_configuracion_hotel(request, hotel_id):
    if request.method == 'POST':
        hotel = get_object_or_404(Hotel, id=hotel_id)
        data = request.POST
        
        setting, created = HotelSetting.objects.update_or_create(
            hotel=hotel,
            defaults={
                'edad_limite_primer_nino': int(data.get('edadLimite_primerNino', 0)),
                'edad_limite_infante': int(data.get('edadLimite_infante', 0)),
                'cantidad_noches': int(data.get('cantidad_noches', 0)),
            }
        )
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'fail'}, status=400)

# ---------------------------------------- REMESAS ---------------------------------------- #

def _calcular_estimado(monto_envio: Decimal, moneda_envio: str, moneda_recepcion: str) -> Decimal:
    """
    Convierte monto_envio desde moneda_envio hacia moneda_recepcion usando TasaCambio más reciente.
    Base de tasas: USD -> CUP (tasa_cup), USD -> MLC (tasa_mlc), USD -> USD (1.0)
    """
    tasa_cambio = TasaCambio.objects.order_by('-fecha_actualizacion').first()
    if not tasa_cambio:
        return monto_envio  # no hay tasa, devolvemos igual

    # normalizamos todo vía USD
    # 1) Pasar monto a USD
    if moneda_envio == 'USD':
        monto_en_usd = monto_envio
    elif moneda_envio == 'CUP':
        monto_en_usd = Decimal(monto_envio) / Decimal(tasa_cambio.tasa_cup or 1)
    elif moneda_envio == 'MLC':
        monto_en_usd = Decimal(monto_envio) / Decimal(tasa_cambio.tasa_mlc or 1)
    else:
        monto_en_usd = monto_envio

    # 2) USD -> moneda_recepcion
    if moneda_recepcion == 'USD':
        return monto_en_usd
    elif moneda_recepcion == 'CUP':
        return monto_en_usd * Decimal(tasa_cambio.tasa_cup or 1)
    elif moneda_recepcion == 'MLC':
        return monto_en_usd * Decimal(tasa_cambio.tasa_mlc or 1)
    return monto_envio


@manager_required
@login_required
def listar_remesas(request):
    qs = (Reserva.objects
          .filter(tipo='remesas')
          .select_related('remesa', 'remesa__remitente', 'remesa__destinatario')
          .order_by('-fecha_reserva'))
    # búsqueda opcional
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(remesa__remitente__nombre_apellido__icontains=q) |
            Q(remesa__destinatario__primer_nombre__icontains=q) |
            Q(remesa__destinatario__primer_apellido__icontains=q)
        )

    paginator = Paginator(qs, 10)
    reservas = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/remesas/listar_remesas.html', {
        'reservas': reservas,
        'query': q,
    })


@manager_required
@login_required
def crear_remesa(request):
    remitentes = Remitente.objects.all().order_by('-created_at')
    destinatarios = Destinatario.objects.all().order_by('-created_at')
    monedas = ['USD', 'CUP', 'MLC']

    # Intentamos obtener la última tasa de cambio
    try:
        tc = TasaCambio.objects.latest('fecha_actualizacion')
        tasas_dict = {"cup": str(tc.tasa_cup), "mlc": str(tc.tasa_mlc)}
    except TasaCambio.DoesNotExist:
        tc = None
        tasas_dict = {"cup": "0", "mlc": "0"}

    def convertir(importe: Decimal, desde: str, hacia: str) -> Decimal:
        """
        Convierte montos usando USD como divisa base.
        tc.tasa_cup = USD -> CUP
        tc.tasa_mlc = USD -> MLC
        """
        if desde == hacia:
            return importe

        if not tc:
            # si piden conversión entre distintas monedas y no hay tasa -> error aguas arriba
            return Decimal('0')

        # Paso 1: a USD
        if desde == 'USD':
            en_usd = importe
        elif desde == 'CUP':
            en_usd = importe / (tc.tasa_cup or Decimal('1'))
        elif desde == 'MLC':
            en_usd = importe / (tc.tasa_mlc or Decimal('1'))
        else:
            en_usd = importe

        # Paso 2: de USD a destino
        if hacia == 'USD':
            return en_usd
        elif hacia == 'CUP':
            return en_usd * (tc.tasa_cup or Decimal('1'))
        elif hacia == 'MLC':
            return en_usd * (tc.tasa_mlc or Decimal('1'))

        return en_usd  # fallback

    if request.method == 'POST':
        valores = {
            "remitente_id": request.POST.get('remitente_id') or "",
            "destinatario_id": request.POST.get('destinatario_id') or "",
            "montoEnvio": request.POST.get('montoEnvio') or "",
            "monedaEnvio": request.POST.get('monedaEnvio') or "USD",
            "monedaRecepcion": request.POST.get('monedaRecepcion') or "USD",
        }

        # Validaciones básicas
        errores = []
        if not valores["remitente_id"]:
            errores.append("Debe seleccionar un remitente.")
        if not valores["destinatario_id"]:
            errores.append("Debe seleccionar un destinatario.")
        if not valores["montoEnvio"]:
            errores.append("Debe indicar el monto a enviar.")

        try:
            monto_envio = Decimal(valores["montoEnvio"] or "0")
            if monto_envio <= 0:
                errores.append("El monto a enviar debe ser mayor que cero.")
        except (InvalidOperation, TypeError):
            errores.append("El monto a enviar no es válido.")
            monto_envio = Decimal('0')

        if valores["monedaEnvio"] not in monedas or valores["monedaRecepcion"] not in monedas:
            errores.append("Monedas inválidas.")

        # Si las monedas son diferentes y no hay tasa, no podemos convertir
        if valores["monedaEnvio"] != valores["monedaRecepcion"] and not tc:
            errores.append("No hay tasa de cambio configurada para convertir entre monedas.")

        if errores:
            for e in errores:
                messages.error(request, e)
            return render(request, 'backoffice/remesas/crear_remesa.html', {
                "remitentes": remitentes,
                "destinatarios": destinatarios,
                "monedas": monedas,
                "tasas_json": json.dumps(tasas_dict),
                "valores": valores,
            })

        remitente = get_object_or_404(Remitente, id=valores["remitente_id"])
        destinatario = get_object_or_404(Destinatario, id=valores["destinatario_id"])

        # Calcular estimado en la moneda de recepción
        monto_estimado = convertir(monto_envio, valores["monedaEnvio"], valores["monedaRecepcion"])

        # Crear la Remesa
        remesa = Remesa.objects.create(
            remitente=remitente,
            destinatario=destinatario,
            monto_envio=monto_envio,
            moneda_envio=valores["monedaEnvio"],
            monto_estimado_recepcion=monto_estimado,
            moneda_recepcion=valores["monedaRecepcion"],
        )

        # Crear la Reserva mínima necesaria para aparecer en listados
        # Campos obligatorios de Reserva: agencia, nombre_usuario, email_empleado, costo_total, precio_total, tipo, estatus
        nombre_usuario = (getattr(request.user, "get_full_name", lambda: "")() or request.user.username or "usuario")
        email_empleado = getattr(request.user, "email", None) or f"{request.user.username or 'usuario'}@example.com"

        Reserva.objects.create(
            remesa=remesa,
            agencia="Backoffice",
            nombre_usuario=nombre_usuario,
            email_empleado=email_empleado,
            costo_sin_fee=monto_envio,
            costo_total=monto_envio,
            precio_total=monto_estimado,
            tipo='remesas',
            estatus='confirmada',  # o 'pendiente' si prefieres
        )

        messages.success(request, "Remesa creada correctamente.")
        return redirect('backoffice:listar_remesas')

    # GET
    return render(request, 'backoffice/remesas/crear_remesa.html', {
        "remitentes": remitentes,
        "destinatarios": destinatarios,
        "monedas": monedas,
        "tasas_json": json.dumps(tasas_dict),
        "valores": {},  # para preservar si hay errores en POST
    })


@manager_required
@login_required
def editar_remesa(request, pk):
    """
    Reemplaza a cargar_editar_remesa/guardar_editar_remesa con una sola vista.
    El pk corresponde a la Reserva (tipo='remesas').
    """
    reserva = get_object_or_404(Reserva, pk=pk, tipo='remesas')
    remesa = reserva.remesa
    if not remesa:
        messages.error(request, "Esta reserva no posee remesa asociada.")
        return redirect('backoffice:listar_remesas')

    remitentes = Remitente.objects.all().order_by('-created_at')
    destinatarios = Destinatario.objects.all().order_by('-created_at')
    monedas = ['USD', 'CUP', 'MLC']

    # Intentar obtener la última tasa
    try:
        tc = TasaCambio.objects.latest('fecha_actualizacion')
    except TasaCambio.DoesNotExist:
        tc = None

    def convertir(importe: Decimal, desde: str, hacia: str) -> Decimal:
        if desde == hacia:
            return importe
        if not tc:
            return Decimal('0')
        # a USD
        if desde == 'USD':
            en_usd = importe
        elif desde == 'CUP':
            en_usd = importe / (tc.tasa_cup or Decimal('1'))
        elif desde == 'MLC':
            en_usd = importe / (tc.tasa_mlc or Decimal('1'))
        else:
            en_usd = importe
        # a destino
        if hacia == 'USD':
            return en_usd
        if hacia == 'CUP':
            return en_usd * (tc.tasa_cup or Decimal('1'))
        if hacia == 'MLC':
            return en_usd * (tc.tasa_mlc or Decimal('1'))
        return en_usd

    if request.method == 'POST':
        valores = {
            "remitente_id": request.POST.get('remitente_id') or "",
            "destinatario_id": request.POST.get('destinatario_id') or "",
            "montoEnvio": request.POST.get('montoEnvio') or "",
            "monedaEnvio": request.POST.get('monedaEnvio') or remesa.moneda_envio or "USD",
            "monedaRecepcion": request.POST.get('monedaRecepcion') or remesa.moneda_recepcion or "USD",
        }

        errores = []
        if not valores["remitente_id"]:
            errores.append("Debe seleccionar un remitente.")
        if not valores["destinatario_id"]:
            errores.append("Debe seleccionar un destinatario.")
        if not valores["montoEnvio"]:
            errores.append("Debe indicar el monto a enviar.")

        try:
            monto_envio = Decimal(valores["montoEnvio"] or "0")
            if monto_envio <= 0:
                errores.append("El monto a enviar debe ser mayor que cero.")
        except (InvalidOperation, TypeError):
            errores.append("El monto a enviar no es válido.")
            monto_envio = Decimal('0')

        if valores["monedaEnvio"] not in monedas or valores["monedaRecepcion"] not in monedas:
            errores.append("Monedas inválidas.")

        # Si hay cambio de moneda y no existen tasas
        if valores["monedaEnvio"] != valores["monedaRecepcion"] and not tc:
            errores.append("No hay tasa de cambio configurada para convertir entre monedas.")

        if errores:
            for e in errores:
                messages.error(request, e)
            return render(request, 'backoffice/remesas/editar_remesa.html', {
                "reserva": reserva,
                "remesa": remesa,
                "remitentes": remitentes,
                "destinatarios": destinatarios,
                "monedas": monedas,
                "valores": valores,
            })

        # Actualizar objetos
        remesa.remitente = get_object_or_404(Remitente, id=valores["remitente_id"])
        remesa.destinatario = get_object_or_404(Destinatario, id=valores["destinatario_id"])
        remesa.monto_envio = monto_envio
        remesa.moneda_envio = valores["monedaEnvio"]

        # Recalcular estimado
        remesa.monto_estimado_recepcion = convertir(monto_envio, valores["monedaEnvio"], valores["monedaRecepcion"])
        remesa.moneda_recepcion = valores["monedaRecepcion"]
        remesa.save()

        # Actualizar totales en reserva
        reserva.costo_total = remesa.monto_envio
        reserva.precio_total = remesa.monto_estimado_recepcion
        reserva.save()

        messages.success(request, "Remesa actualizada correctamente.")
        return redirect('backoffice:listar_remesas')

    # GET
    return render(request, 'backoffice/remesas/editar_remesa.html', {
        "reserva": reserva,
        "remesa": remesa,
        "remitentes": remitentes,
        "destinatarios": destinatarios,
        "monedas": monedas,
        "valores": {},  # para preservar si hay errores en POST
    })


@manager_required
@login_required
def eliminar_remesa(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk, tipo='remesas')
    remesa = reserva.remesa
    if request.method == 'POST':
        if request.POST.get('confirm_text', '').strip().upper() != 'ELIMINAR':
            messages.error(request, "Debes escribir ELIMINAR para confirmar.")
        else:
            # importante: borrar primero reserva o remesa es indistinto por on_delete, lo hacemos explícito
            reserva.delete()
            if remesa.pk:
                remesa.delete()
            messages.success(request, f"Remesa #{pk} eliminada correctamente.")
            return redirect('backoffice:listar_remesas')

    return render(request, 'backoffice/remesas/eliminar_remesa.html', {
        'reserva': reserva,
        'remesa': remesa,
    })


# Endpoint para el modal de detalle del listar
@manager_required
@login_required
def detalles_remesa_json(request, pk):
    reserva = get_object_or_404(
        Reserva.objects.select_related('remesa', 'remesa__remitente', 'remesa__destinatario'),
        pk=pk, tipo='remesas'
    )
    r = reserva.remesa
    data = {
        "reserva_id": reserva.id,
        "fecha_reserva": reserva.fecha_reserva.isoformat() if reserva.fecha_reserva else None,
        "remitente": r.remitente.nombre_apellido if r and r.remitente else None,
        "destinatario": r.destinatario.nombre_completo if r and r.destinatario else None,
        "monto_envio": str(r.monto_envio) if r else None,
        "moneda_envio": r.moneda_envio if r else None,
        "monto_estimado_recepcion": str(r.monto_estimado_recepcion) if r else None,
        "moneda_recepcion": r.moneda_recepcion if r else None,
    }
    return JsonResponse(data)


# ---------------------------------------- RESERVAS ---------------------------------------- #


@manager_required
@login_required
def listar_reservas(request, estado=None):
    reservas = Reserva.objects.select_related('proveedor').all().order_by('-fecha_reserva')

    # Filtrar por estado
    if estado:
        if estado == 'por_cobrar':
            reservas = reservas.filter(cobrada=False)
        elif estado == 'pagada':
            reservas = reservas.filter(pagada=True)
        else:
            reservas = reservas.filter(estatus=estado)

    # Filtro: búsqueda general
    query = request.GET.get('q', '')
    if query:
        reservas = reservas.filter(
            Q(hotel__hotel_nombre__icontains=query) |
            Q(nombre_usuario__icontains=query) |
            Q(email_empleado__icontains=query) |
            Q(proveedor__nombre__icontains=query)  # <-- AÑADIMOS búsqueda por proveedor
        )

    # Filtro: ID de reserva
    id_reserva = request.GET.get('id_reserva', '')
    if id_reserva:
        reservas = reservas.filter(id=id_reserva)

    # Filtro: nombre del pasajero
    nombre_pasajero = request.GET.get('nombre_pasajero', '')
    if nombre_pasajero:
        reservas = reservas.filter(habitaciones_reserva__pasajeros__nombre__icontains=nombre_pasajero)

    # Filtro: rango de fechas (con validación)
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            reservas = reservas.filter(fecha_reserva__date__gte=fecha_inicio_dt.date())
        except ValueError:
            print(f"⚠️ Fecha inválida inicio: {fecha_inicio}")

    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            reservas = reservas.filter(fecha_reserva__date__lte=fecha_fin_dt.date())
        except ValueError:
            print(f"⚠️ Fecha inválida fin: {fecha_fin}")

    # Paginación
    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'reservas': page_obj,
        'query': query,
        'estado': estado,
        'id_reserva': id_reserva,
        'nombre_pasajero': nombre_pasajero,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'backoffice/reservas/listar_reservas.html', context)




def _safe_get(obj, path, default=None):
    """
    Accede a atributos anidados de forma segura.
    Ej: _safe_get(reserva, "envio.destinatario.primer_nombre")
    """
    try:
        for part in path.split("."):
            obj = getattr(obj, part)
            if obj is None:
                return default
        return obj
    except Exception:
        return default


def _full_name(*parts):
    return " ".join([str(p).strip() for p in parts if p]).strip() or "N/A"


@manager_required           # ← debe ir por encima para envolver al inner (login_required)
@login_required             # ← inner: primero obliga a autenticarse, luego valida rol
@require_GET
def detalles_reserva(request, reserva_id):
    """
    Devuelve detalles resumidos de una reserva en JSON.
    Solo accesible para MANAGERS autenticados.
    """
    reserva = get_object_or_404(Reserva, pk=reserva_id)

    # (Opcional) Filtro adicional: si quieres limitar por agencia/tenant añade tu lógica aquí.
    # if not usuario_puede_ver_reserva(request.user, reserva):
    #     return HttpResponseForbidden(JsonResponse({"error": "No autorizado"}))

    # Datos base comunes
    base = {
        "id": reserva.id,
        "tipo": reserva.tipo or "N/A",
        "usuario": reserva.nombre_usuario or "N/A",
        "fecha": reserva.fecha_reserva.strftime("%Y-%m-%d %H:%M") if reserva.fecha_reserva else "N/A",
        "estatus": reserva.estatus or "N/A",
    }

    detalle = {}

    # ---- Detalle por tipo ----
    if reserva.tipo == "hoteles":
        # Hotel local o importado (Distal)
        if reserva.hotel_importado:
            detalle["hotel"] = {
                "origen": "importado",
                "nombre": _safe_get(reserva, "hotel_importado.hotel_name", "N/A"),
                "city_code": _safe_get(reserva, "hotel_importado.hotel_city_code", "N/A"),
                "hotel_code": _safe_get(reserva, "hotel_importado.hotel_code", "N/A"),
            }
        elif reserva.hotel:
            detalle["hotel"] = {
                "origen": "local",
                "nombre": _safe_get(reserva, "hotel.hotel_nombre", "N/A"),
                "polo": _safe_get(reserva, "hotel.polo_turistico.nombre", "N/A"),
                "cadena": _safe_get(reserva, "hotel.cadena_hotelera.nombre", "N/A"),
            }
        else:
            detalle["hotel"] = {"origen": "N/A", "nombre": "N/A"}

        # (Opcional) Si guardas booking_code/plan/estancia, puedes añadirlos:
        detalle["resumen_estadia"] = {
            "checkin": getattr(reserva, "checkin", None) or "N/A",
            "checkout": getattr(reserva, "checkout", None) or "N/A",
            "noches": getattr(reserva, "noches", None) or "N/A",
            "plan": getattr(reserva, "plan", None) or "N/A",
            "booking_code": getattr(reserva, "booking_code", None) or "N/A",
        }

    elif reserva.tipo == "envio":
        # Envío (remitente/destinatario + descripción)
        remitente_nombre = _safe_get(reserva, "envio.remitente.nombre_apellido", "N/A")
        dest_nombre = _full_name(
            _safe_get(reserva, "envio.destinatario.primer_nombre"),
            _safe_get(reserva, "envio.destinatario.segundo_nombre"),
            _safe_get(reserva, "envio.destinatario.primer_apellido"),
            _safe_get(reserva, "envio.destinatario.segundo_apellido"),
        )
        detalle["envio"] = {
            "remitente": remitente_nombre,
            "destinatario": dest_nombre,
            "descripcion": _safe_get(reserva, "envio.descripcion", "N/A"),
            "cantidad_items": _safe_get(reserva, "envio.cantidad_items", "N/A"),
            "peso_total": _safe_get(reserva, "envio.peso_total", "N/A"),
            "tipo_envio": _safe_get(reserva, "envio.tipo_envio", "N/A"),  # aéreo/marítimo si lo manejas
        }

    elif reserva.tipo == "remesa":
        # Remesa (remitente/destinatario + monto/monedas)
        remitente = _safe_get(reserva, "remesa.remitente.nombre_apellido", "N/A")
        destinatario = _safe_get(reserva, "remesa.destinatario.nombre_apellido", "N/A")
        detalle["remesa"] = {
            "remitente": remitente,
            "destinatario": destinatario,
            "monto": _safe_get(reserva, "remesa.monto", "N/A"),
            "moneda_envio": _safe_get(reserva, "remesa.moneda_envio", "N/A"),
            "moneda_recepcion": _safe_get(reserva, "remesa.moneda_recepcion", "N/A"),
            "tasa_cambio": _safe_get(reserva, "remesa.tasa_cambio", "N/A"),
            "monto_estimado": _safe_get(reserva, "remesa.monto_estimado", "N/A"),
        }

    elif reserva.tipo == "traslados":
        # Traslados (origen/destino, fecha/hora, vehículo)
        detalle["traslado"] = {
            "origen": _safe_get(reserva, "traslado.origen.nombre", "N/A"),
            "destino": _safe_get(reserva, "traslado.destino.nombre", "N/A"),
            "fecha": _safe_get(reserva, "traslado.fecha", "N/A"),
            "hora": _safe_get(reserva, "traslado.hora", "N/A"),
            "vehiculo": _safe_get(reserva, "traslado.vehiculo.nombre", "N/A"),
            "transportista": _safe_get(reserva, "traslado.transportista.nombre", "N/A"),
        }

    elif reserva.tipo == "certificados":
        # Certificados de vacaciones (si tu modelo lo maneja)
        detalle["certificado"] = {
            "nombre": _safe_get(reserva, "certificado.nombre", "N/A"),
            "solo_adultos": _safe_get(reserva, "certificado.solo_adultos", False),
            "precio": _safe_get(reserva, "certificado.precio", "N/A"),
            "costo": _safe_get(reserva, "certificado.costo", "N/A"),
            "pasajero": _safe_get(reserva, "pasajero.nombre_apellido", "N/A"),
        }

    else:
        # Tipo no mapeado aún
        detalle["info"] = "Tipo de reserva no mapeado aún para detalle."

    # Respuesta final
    data = {**base, "detalle": detalle}
    return JsonResponse(data, safe=True, status=200)


@manager_required
@login_required
def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('backoffice:listar_reservas')  # Usa el namespace aquí
    else:
        form = ReservaForm()
    return render(request, 'backoffice/reservas/editar_reserva.html', {'form': form})

@manager_required
@login_required
def eliminar_reserva(request, pk):
    reserva = get_object_or_404(Reserva, pk=pk)
    if request.method == 'POST':
        reserva.delete()
        return redirect('backoffice:listar_reservas')  # Usa el namespace aquí
    return render(request, 'backoffice/reservas/eliminar_reserva.html', {'reserva': reserva})

# -------------------------------------------------------------------------------- #

@manager_required
@login_required
def edit_reserva_load(request, reserva_id):
    # ------------------------------------------------------
    # Función para cargar los datos de una reserva existente.
    # Obtiene la reserva, sus habitaciones, y los pasajeros asociados.
    # Renderiza la página de edición de la reserva con la información cargada.
    # ------------------------------------------------------
    # Cargar la reserva existente
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    
    # Cargar las habitaciones asociadas, junto con los pasajeros
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva).prefetch_related('pasajeros')
    
    tipos_habitacion = Habitacion.objects.filter(hotel=reserva.hotel)
    
    # Pasar la reserva y habitaciones a la plantilla
    return render(request, 'backoffice/reservas/edit_reserva.html', {
        'reserva': reserva,
        'habitaciones': habitaciones,
        'tipos_habitacion': tipos_habitacion,
    })


@login_required
def actualizar_reserva_principal(request, reserva):
    """
    Actualiza los campos generales de la reserva (independientemente del tipo).
    """
    reserva.nombre_usuario = request.POST.get('nombre_usuario', reserva.nombre_usuario)
    reserva.email_empleado = request.POST.get('email_empleado', reserva.email_empleado)
    reserva.costo_total = request.POST.get('costo_total', reserva.costo_total)
    reserva.precio_total = request.POST.get('precio_total', reserva.precio_total)
    reserva.tipo = request.POST.get('tipo', reserva.tipo)
    reserva.estatus = request.POST.get('estatus', reserva.estatus)
    reserva.numero_confirmacion = request.POST.get('numero_confirmacion', reserva.numero_confirmacion)
    reserva.notas = request.POST.get('notas', reserva.notas)
    
    # Campos booleanos
    reserva.cobrada = True if request.POST.get('cobrada') == 'on' else False
    reserva.pagada = True if request.POST.get('pagada') == 'on' else False

    try:
        reserva.save()
        print(f'Reserva {reserva.id} actualizada exitosamente.')
    except Exception as e:
        print(f'Error al guardar la reserva {reserva.id}: {e}')

#@csrf_exempt
#@login_required
#def actualizar_traslado_y_pasajeros(request, reserva):
#    """
#    Actualiza los detalles específicos de un traslado y sus pasajeros.
#    Se espera que la reserva tenga un objeto 'traslado' asociado.
#    """
#    # Importar modelos necesarios (si no están importados globalmente)
#    from backoffice.models import Transportista, Ubicacion, Vehiculo
#
#    traslado = reserva.traslado
#
#    # Actualizar campos del traslado
#    transportista_name = request.POST.get('transportista')
#    origen_name = request.POST.get('origen')
#    destino_name = request.POST.get('destino')
#    vehiculo_tipo = request.POST.get('vehiculo')
#    costo_traslado = request.POST.get('costo_traslado')
#
#    try:
#        costo_traslado = float(costo_traslado)
#    except (TypeError, ValueError):
#        costo_traslado = traslado.costo  # O dejar el costo anterior si hay error
#
#    try:
#        traslado.transportista = Transportista.objects.get(nombre=transportista_name)
#    except Transportista.DoesNotExist:
#        print(f"No se encontró el transportista '{transportista_name}'.")
#    try:
#        traslado.origen = Ubicacion.objects.get(nombre=origen_name)
#    except Ubicacion.DoesNotExist:
#        print(f"No se encontró el origen '{origen_name}'.")
#    try:
#        traslado.destino = Ubicacion.objects.get(nombre=destino_name)
#    except Ubicacion.DoesNotExist:
#        print(f"No se encontró el destino '{destino_name}'.")
#    try:
#        traslado.vehiculo = Vehiculo.objects.get(tipo=vehiculo_tipo)
#    except Vehiculo.DoesNotExist:
#        print(f"No se encontró el vehículo '{vehiculo_tipo}'.")
#    
#    traslado.costo = costo_traslado
#    traslado.save()
#
#    # Actualizar pasajeros existentes asociados al traslado
#    for pasajero in traslado.pasajeros.all():
#        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
#        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
#        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
#        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
#        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
#        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
#        
#        if fecha_nacimiento:
#            try:
#                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
#            except ValueError:
#                fecha_nacimiento = pasajero.fecha_nacimiento
#        if caducidad_pasaporte:
#            try:
#                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
#            except ValueError:
#                caducidad_pasaporte = pasajero.caducidad_pasaporte
#
#        pasajero.nombre = nombre
#        pasajero.fecha_nacimiento = fecha_nacimiento
#        pasajero.pasaporte = pasaporte
#        pasajero.caducidad_pasaporte = caducidad_pasaporte
#        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
#        pasajero.tipo = tipo
#        pasajero.save()
#
#    # Agregar nuevos pasajeros para el traslado
#    for key in request.POST:
#        if key.startswith('traslado_pasajero_nombre_'):
#            new_id = key.split('_')[-1]
#            nombre = request.POST.get(f'traslado_pasajero_nombre_{new_id}')
#            fecha_nacimiento = request.POST.get(f'traslado_pasajero_fecha_nacimiento_{new_id}')
#            pasaporte = request.POST.get(f'traslado_pasajero_pasaporte_{new_id}')
#            caducidad_pasaporte = request.POST.get(f'traslado_pasajero_caducidad_pasaporte_{new_id}')
#            pais_emision_pasaporte = request.POST.get(f'traslado_pasajero_pais_emision_pasaporte_{new_id}')
#            tipo = request.POST.get(f'traslado_pasajero_tipo_{new_id}')
#            
#            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
#                print(f"Datos incompletos para pasajero nuevo en traslado: {nombre}")
#                continue
#            
#            try:
#                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
#                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
#            except ValueError:
#                print(f"Error al convertir fechas para pasajero nuevo: {nombre}")
#                continue
#            
#            Pasajero.objects.create(
#                traslado=traslado,
#                nombre=nombre,
#                fecha_nacimiento=fecha_nacimiento,
#                pasaporte=pasaporte,
#                caducidad_pasaporte=caducidad_pasaporte,
#                pais_emision_pasaporte=pais_emision_pasaporte,
#                tipo=tipo
#            )

@csrf_exempt
@login_required
def actualizar_habitaciones_y_pasajeros(request, reserva):
    """
    Actualiza las habitaciones y pasajeros para reservas de hoteles.
    """
    habitaciones = HabitacionReserva.objects.filter(reserva_id=reserva.id)
    
    for habitacion in habitaciones:
        actualizar_habitacion(request, habitacion)
        actualizar_pasajeros_existentes(request, habitacion)
        agregar_nuevos_pasajeros(request, habitacion)
    
    recalcular_precio_y_costo(reserva)

#@csrf_exempt
#@login_required
#def actualizar_habitacion(request, habitacion):
#    habitacion_nombre = request.POST.get(f'habitacion_nombre_{habitacion.id}')
#    adultos = request.POST.get(f'adultos_{habitacion.id}')
#    ninos = request.POST.get(f'ninos_{habitacion.id}')
#    fechas_viaje = request.POST.get(f'fechas_viaje_{habitacion.id}')
#    
#    if fechas_viaje and fechas_viaje != 'Invalid date':
#        try:
#            fechas_viaje = datetime.strptime(fechas_viaje, '%Y/%m/%d').strftime('%Y-%m-%d')
#        except ValueError:
#            fechas_viaje = habitacion.fechas_viaje
#    habitacion.habitacion_nombre = habitacion_nombre
#    habitacion.adultos = adultos
#    habitacion.ninos = ninos
#    habitacion.fechas_viaje = fechas_viaje
#    habitacion.save()
#
#@csrf_exempt
#@login_required
#def actualizar_pasajeros_existentes(request, habitacion):
#    for pasajero in habitacion.pasajeros.all():
#        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
#        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
#        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
#        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
#        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
#        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
#        
#        if fecha_nacimiento and fecha_nacimiento != 'Invalid date':
#            try:
#                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
#            except ValueError:
#                fecha_nacimiento = pasajero.fecha_nacimiento
#        if caducidad_pasaporte and caducidad_pasaporte != 'Invalid date':
#            try:
#                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
#            except ValueError:
#                caducidad_pasaporte = pasajero.caducidad_pasaporte
#        
#        pasajero.nombre = nombre
#        pasajero.fecha_nacimiento = fecha_nacimiento
#        pasajero.pasaporte = pasaporte
#        pasajero.caducidad_pasaporte = caducidad_pasaporte
#        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
#        pasajero.tipo = tipo
#        pasajero.save()
#
#@csrf_exempt
#@login_required
#def agregar_nuevos_pasajeros(request, habitacion):
#    total_adultos = int(habitacion.adultos) if habitacion.adultos else 0
#    total_ninos = int(habitacion.ninos) if habitacion.ninos else 0
#
#    for key in request.POST:
#        if key.startswith(f'habitacion_{habitacion.id}_pasajero_nombre_'):
#            new_passenger_id = key.split('_')[-1]
#            nombre = request.POST.get(f'habitacion_{habitacion.id}_pasajero_nombre_{new_passenger_id}')
#            fecha_nacimiento = request.POST.get(f'habitacion_{habitacion.id}_pasajero_fecha_nacimiento_{new_passenger_id}')
#            pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pasaporte_{new_passenger_id}')
#            caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_caducidad_pasaporte_{new_passenger_id}')
#            pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pais_emision_pasaporte_{new_passenger_id}')
#            tipo = request.POST.get(f'habitacion_{habitacion.id}_pasajero_tipo_{new_passenger_id}')
#
#            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
#                print(f"Error: Faltan datos obligatorios para el pasajero {nombre}. No se guardará.")
#                continue
#
#            try:
#                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
#                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
#            except ValueError:
#                print(f"Error al convertir fechas para el pasajero {nombre}.")
#                continue
#
#            if not Pasajero.objects.filter(habitacion=habitacion, nombre=nombre, pasaporte=pasaporte).exists():
#                nuevo_pasajero = Pasajero.objects.create(
#                    habitacion=habitacion,
#                    nombre=nombre,
#                    fecha_nacimiento=fecha_nacimiento,
#                    pasaporte=pasaporte,
#                    caducidad_pasaporte=caducidad_pasaporte,
#                    pais_emision_pasaporte=pais_emision_pasaporte,
#                    tipo=tipo
#                )
#                if tipo == 'adulto':
#                    total_adultos += 1
#                else:
#                    total_ninos += 1
#
#    habitacion.adultos = total_adultos
#    habitacion.ninos = total_ninos
#    habitacion.save()

@csrf_exempt
@login_required
def agregar_nuevas_habitaciones(request, reserva):
    habitacion_counter = reserva.habitaciones_reserva.count() + 1
    while True:
        habitacion_nombre = request.POST.get(f'nueva_habitacion_nombre_{habitacion_counter}')
        if not habitacion_nombre:
            break
        adultos = int(request.POST.get(f'nueva_adultos_{habitacion_counter}', 0))
        ninos = int(request.POST.get(f'nueva_ninos_{habitacion_counter}', 0))
        fechas_viaje_antes = request.POST.get(f'nueva_fechas_viaje_{habitacion_counter}')
        fechas_viaje = fechas_viaje_antes.replace('/', '-') if fechas_viaje_antes else '2024-01-01'
        if fechas_viaje and fechas_viaje != 'Invalid date':
            try:
                fechas_viaje = fechas_viaje.strip()
            except ValueError:
                fechas_viaje = '2024-01-01'
        else:
            fechas_viaje = '2024-01-01'
        precio = 100.00  # Ajusta según la lógica de tu negocio
        oferta_codigo = "OFERTA2024"  # Ajusta según corresponda
        nueva_habitacion = HabitacionReserva.objects.create(
            reserva=reserva,
            habitacion_nombre=habitacion_nombre,
            adultos=adultos,
            ninos=ninos,
            fechas_viaje=fechas_viaje,
            precio=precio,
            oferta_codigo=oferta_codigo
        )
        agregar_nuevos_pasajeros_a_habitacion_nueva(request, nueva_habitacion, habitacion_counter)
        habitacion_counter += 1

#@csrf_exempt
#@login_required
#def agregar_nuevos_pasajeros_a_habitacion_nueva(request, habitacion, habitacion_counter):
#    pasajero_counter = 1
#    while True:
#        nombre = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_nombre')
#        if not nombre:
#            break
#        fecha_nacimiento = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_fecha_nacimiento')
#        pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pasaporte')
#        caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_caducidad_pasaporte')
#        pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pais_emision_pasaporte')
#        tipo = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_tipo')
#
#        if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
#            break
#
#        try:
#            fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
#            caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
#        except ValueError:
#            break
#
#        Pasajero.objects.create(
#            habitacion=habitacion,
#            nombre=nombre,
#            fecha_nacimiento=fecha_nacimiento,
#            pasaporte=pasaporte,
#            caducidad_pasaporte=caducidad_pasaporte,
#            pais_emision_pasaporte=pais_emision_pasaporte,
#            tipo=tipo
#        )
#        pasajero_counter += 1
#
#@login_required
#def correo_confirmada(reserva):
#    """
#    Envía el correo de confirmación (para reservas de hoteles, por ahora).
#    """
#    pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)
#    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
#    encabezado = "{% trans 'Muchas gracias por reservar con RUTA MULTISERVICE, su solicitud ha sido confirmada:' %}"
#    #enviar_correo(reserva, pasajeros, habitaciones, reserva.email_empleado, encabezado)
#
#@login_required
#def recalcular_precio_y_costo(reserva):
#    habitaciones_reserva = HabitacionReserva.objects.filter(reserva=reserva)
#    precio_total = 0
#    for habitacion_reserva in habitaciones_reserva:
#        cant_adultos = habitacion_reserva.adultos
#        habitacion_nombre = habitacion_reserva.habitacion_nombre
#        fecha_viaje = habitacion_reserva.fechas_viaje
#        nombre_hotel = reserva.hotel.hotel_nombre
#        habitacion = obtener_habitacion(nombre_hotel, habitacion_nombre)
#        ofertas = obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre)
#        if habitacion_reserva.ninos == 1:
#            nino1 = 1; nino2 = 0
#        elif habitacion_reserva.ninos == 2:
#            nino1 = 1; nino2 = 1
#        else:
#            nino1 = 0; nino2 = 0
#        if habitacion and ofertas:
#            dias_oferta = calcular_dias_por_oferta(ofertas, fecha_viaje)
#            for result in dias_oferta:
#                precio_total += calcula_precio(cant_adultos, nino1, nino2, result["oferta"], habitacion, result["dias_en_oferta"])
#    return precio_total

@csrf_exempt
@login_required
def actualizar_habitacion(request, habitacion):
    habitacion_nombre = request.POST.get(f'habitacion_nombre_{habitacion.id}')
    adultos = request.POST.get(f'adultos_{habitacion.id}')
    ninos = request.POST.get(f'ninos_{habitacion.id}')
    fechas_viaje = request.POST.get(f'fechas_viaje_{habitacion.id}')
    if fechas_viaje and fechas_viaje != 'Invalid date':
        try:
            fechas_viaje = datetime.strptime(fechas_viaje, '%Y/%m/%d').strftime('%Y-%m-%d')
        except ValueError:
            fechas_viaje = habitacion.fechas_viaje
    habitacion.habitacion_nombre = habitacion_nombre
    habitacion.adultos = adultos
    habitacion.ninos = ninos
    habitacion.fechas_viaje = fechas_viaje
    habitacion.save()

@csrf_exempt
@login_required
def actualizar_pasajeros_existentes(request, habitacion):
    for pasajero in habitacion.pasajeros.all():
        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
        if fecha_nacimiento and fecha_nacimiento != 'Invalid date':
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                fecha_nacimiento = pasajero.fecha_nacimiento
        if caducidad_pasaporte and caducidad_pasaporte != 'Invalid date':
            try:
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                caducidad_pasaporte = pasajero.caducidad_pasaporte
        pasajero.nombre = nombre
        pasajero.fecha_nacimiento = fecha_nacimiento
        pasajero.pasaporte = pasaporte
        pasajero.caducidad_pasaporte = caducidad_pasaporte
        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
        pasajero.tipo = tipo
        pasajero.save()

@csrf_exempt
@login_required
def agregar_nuevos_pasajeros(request, habitacion):
    total_adultos = int(habitacion.adultos) if habitacion.adultos else 0
    total_ninos = int(habitacion.ninos) if habitacion.ninos else 0
    for key in request.POST:
        if key.startswith(f'habitacion_{habitacion.id}_pasajero_nombre_'):
            new_passenger_id = key.split('_')[-1]
            nombre = request.POST.get(f'habitacion_{habitacion.id}_pasajero_nombre_{new_passenger_id}')
            fecha_nacimiento = request.POST.get(f'habitacion_{habitacion.id}_pasajero_fecha_nacimiento_{new_passenger_id}')
            pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pasaporte_{new_passenger_id}')
            caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_caducidad_pasaporte_{new_passenger_id}')
            pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion.id}_pasajero_pais_emision_pasaporte_{new_passenger_id}')
            tipo = request.POST.get(f'habitacion_{habitacion.id}_pasajero_tipo_{new_passenger_id}')
            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
                print(f"Error: Faltan datos obligatorios para el pasajero {nombre}. No se guardará.")
                continue
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                print(f"Error al convertir las fechas para el pasajero {nombre}.")
                continue
            if not Pasajero.objects.filter(habitacion=habitacion, nombre=nombre, pasaporte=pasaporte).exists():
                Pasajero.objects.create(
                    habitacion=habitacion,
                    nombre=nombre,
                    fecha_nacimiento=fecha_nacimiento,
                    pasaporte=pasaporte,
                    caducidad_pasaporte=caducidad_pasaporte,
                    pais_emision_pasaporte=pais_emision_pasaporte,
                    tipo=tipo
                )
                if tipo == 'adulto':
                    total_adultos += 1
                else:
                    total_ninos += 1
    habitacion.adultos = total_adultos
    habitacion.ninos = total_ninos
    habitacion.save()

@csrf_exempt
@login_required
def agregar_nuevos_pasajeros_a_habitacion_nueva(request, habitacion, habitacion_counter):
    pasajero_counter = 1
    while True:
        nombre = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_nombre')
        if not nombre:
            break
        fecha_nacimiento = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_fecha_nacimiento')
        pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pasaporte')
        caducidad_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_caducidad_pasaporte')
        pais_emision_pasaporte = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_pais_emision_pasaporte')
        tipo = request.POST.get(f'habitacion_{habitacion_counter}_pasajero_{pasajero_counter}_tipo')
        if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
            break
        try:
            fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
        except ValueError:
            break
        Pasajero.objects.create(
            habitacion=habitacion,
            nombre=nombre,
            fecha_nacimiento=fecha_nacimiento,
            pasaporte=pasaporte,
            caducidad_pasaporte=caducidad_pasaporte,
            pais_emision_pasaporte=pais_emision_pasaporte,
            tipo=tipo
        )
        pasajero_counter += 1

@login_required
def correo_confirmada(reserva):
    """
    Envía el correo de confirmación (para reservas de hoteles, por ahora).
    """
    pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)
    habitaciones = HabitacionReserva.objects.filter(reserva=reserva)
    encabezado = "{% trans 'Muchas gracias por reservar con RUTA MULTISERVICE, su solicitud ha sido confirmada:' %}"
    #enviar_correo(reserva, pasajeros, habitaciones, reserva.email_empleado, encabezado)

@login_required
def calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion, cant_dias):
    # ... (Lógica de cálculo de precio para hoteles)
    # Esta función se mantiene sin cambios.
    pass  # Usa tu implementación actual aquí

#@login_required
#def calcular_dias_por_oferta(ofertas, fecha_viaje):
#    try:
#        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
#    except ValueError as e:
#        print(f"Error al parsear fechas de viaje: {e}")
#        raise
#    resultado = []
#    for oferta in ofertas:
#        try:
#            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
#        except ValueError as e:
#            print(f"Error al parsear fechas de la oferta {oferta}: {e}")
#            continue
#        inicio_solapamiento = max(fecha_inicio_viaje, fecha_inicio_oferta)
#        fin_solapamiento = min(fecha_fin_viaje, fecha_fin_oferta)
#        if inicio_solapamiento <= fin_solapamiento:
#            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days + 1
#            resultado.append({
#                "oferta": oferta,
#                "dias_en_oferta": dias_en_oferta
#            })
#    return resultado
#
#@login_required
#def obtener_habitacion(nombre_hotel, nombre_habitacion):
#    try:
#        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
#        habitacion = Habitacion.objects.get(hotel=hotel, tipo=nombre_habitacion)
#        return habitacion
#    except ObjectDoesNotExist:
#        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{nombre_habitacion}'.")
#        return None
#
#@login_required
#def obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre):
#    try:
#        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
#        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
#        ofertas = Oferta.objects.filter(
#            hotel=hotel,
#            tipo_habitacion=habitacion_nombre,
#            disponible=True
#        )
#        ofertas_validas = []
#        for oferta in ofertas:
#            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
#            if fecha_inicio_viaje <= fecha_fin_oferta and fecha_fin_viaje >= fecha_inicio_oferta:
#                ofertas_validas.append(oferta)
#        return ofertas_validas
#    except ObjectDoesNotExist:
#        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{habitacion_nombre}'.")
#        return []
#    except ValueError as e:
#        print(f"Error al parsear las fechas: {e}")
#        return []
#
#@login_required
#def recalcular_precio_y_costo(reserva):
#    habitaciones_reserva = HabitacionReserva.objects.filter(reserva=reserva)
#    precio_total = 0
#    for habitacion_reserva in habitaciones_reserva:
#        cant_adultos = habitacion_reserva.adultos
#        habitacion_nombre = habitacion_reserva.habitacion_nombre
#        fecha_viaje = habitacion_reserva.fechas_viaje
#        nombre_hotel = reserva.hotel.hotel_nombre
#        habitacion = obtener_habitacion(nombre_hotel, habitacion_nombre)
#        ofertas = obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre)
#        if habitacion_reserva.ninos == 1:
#            nino1 = 1; nino2 = 0
#        elif habitacion_reserva.ninos == 2:
#            nino1 = 1; nino2 = 1
#        else:
#            nino1 = 0; nino2 = 0
#        if habitacion and ofertas:
#            dias_oferta = calcular_dias_por_oferta(ofertas, fecha_viaje)
#            for result in dias_oferta:
#                precio_total += calcula_precio(cant_adultos, nino1, nino2, result["oferta"], habitacion, result["dias_en_oferta"])
#    return precio_total

@login_required
def actualizar_traslado_y_pasajeros(request, reserva):
    """
    Actualiza los campos específicos de un traslado y sus pasajeros.
    Se asume que la reserva tiene un objeto 'traslado' asociado.
    """
    from backoffice.models import Transportista, Ubicacion, Vehiculo  # Asegúrate de tenerlos importados
    traslado = reserva.traslado

    transportista_name = request.POST.get('transportista')
    origen_name = request.POST.get('origen')
    destino_name = request.POST.get('destino')
    vehiculo_tipo = request.POST.get('vehiculo')
    costo_traslado = request.POST.get('costo_traslado')
    try:
        costo_traslado = float(costo_traslado)
    except (TypeError, ValueError):
        costo_traslado = traslado.costo

    try:
        traslado.transportista = Transportista.objects.get(nombre=transportista_name)
    except Transportista.DoesNotExist:
        print(f"No se encontró el transportista '{transportista_name}'.")
    try:
        traslado.origen = Ubicacion.objects.get(nombre=origen_name)
    except Ubicacion.DoesNotExist:
        print(f"No se encontró el origen '{origen_name}'.")
    try:
        traslado.destino = Ubicacion.objects.get(nombre=destino_name)
    except Ubicacion.DoesNotExist:
        print(f"No se encontró el destino '{destino_name}'.")
    try:
        traslado.vehiculo = Vehiculo.objects.get(tipo=vehiculo_tipo)
    except Vehiculo.DoesNotExist:
        print(f"No se encontró el vehículo '{vehiculo_tipo}'.")
    
    traslado.costo = costo_traslado
    traslado.save()

    # Actualizar pasajeros existentes en el traslado
    for pasajero in traslado.pasajeros.all():
        nombre = request.POST.get(f'pasajero_nombre_{pasajero.id}')
        fecha_nacimiento = request.POST.get(f'pasajero_fecha_nacimiento_{pasajero.id}')
        pasaporte = request.POST.get(f'pasajero_pasaporte_{pasajero.id}')
        caducidad_pasaporte = request.POST.get(f'pasajero_caducidad_pasaporte_{pasajero.id}')
        pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{pasajero.id}')
        tipo = request.POST.get(f'pasajero_tipo_{pasajero.id}')
        if fecha_nacimiento:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                fecha_nacimiento = pasajero.fecha_nacimiento
        if caducidad_pasaporte:
            try:
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                caducidad_pasaporte = pasajero.caducidad_pasaporte
        pasajero.nombre = nombre
        pasajero.fecha_nacimiento = fecha_nacimiento
        pasajero.pasaporte = pasaporte
        pasajero.caducidad_pasaporte = caducidad_pasaporte
        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
        pasajero.tipo = tipo
        pasajero.save()

    # Agregar nuevos pasajeros para el traslado
    for key in request.POST:
        if key.startswith('traslado_pasajero_nombre_'):
            new_id = key.split('_')[-1]
            nombre = request.POST.get(f'traslado_pasajero_nombre_{new_id}')
            fecha_nacimiento = request.POST.get(f'traslado_pasajero_fecha_nacimiento_{new_id}')
            pasaporte = request.POST.get(f'traslado_pasajero_pasaporte_{new_id}')
            caducidad_pasaporte = request.POST.get(f'traslado_pasajero_caducidad_pasaporte_{new_id}')
            pais_emision_pasaporte = request.POST.get(f'traslado_pasajero_pais_emision_pasaporte_{new_id}')
            tipo = request.POST.get(f'traslado_pasajero_tipo_{new_id}')
            if not (nombre and fecha_nacimiento and pasaporte and caducidad_pasaporte and pais_emision_pasaporte):
                continue
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%m/%d/%Y').strftime('%Y-%m-%d')
                caducidad_pasaporte = datetime.strptime(caducidad_pasaporte, '%m/%d/%Y').strftime('%Y-%m-%d')
            except ValueError:
                continue
            Pasajero.objects.create(
                traslado=traslado,
                nombre=nombre,
                fecha_nacimiento=fecha_nacimiento,
                pasaporte=pasaporte,
                caducidad_pasaporte=caducidad_pasaporte,
                pais_emision_pasaporte=pais_emision_pasaporte,
                tipo=tipo
            )


## Las siguientes funciones se mantienen o se implementan según tu lógica actual:
#@login_required
#def calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion, cant_dias):
#    # Lógica actual para calcular el precio en reservas de hoteles
#    pass

@login_required
def calcular_dias_por_oferta(ofertas, fecha_viaje):
    try:
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
    except ValueError as e:
        print(f"Error al parsear fechas de viaje: {e}")
        raise
    resultado = []
    for oferta in ofertas:
        try:
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
        except ValueError as e:
            print(f"Error al parsear fechas de la oferta {oferta}: {e}")
            continue
        inicio_solapamiento = max(fecha_inicio_viaje, fecha_inicio_oferta)
        fin_solapamiento = min(fecha_fin_viaje, fecha_fin_oferta)
        if inicio_solapamiento <= fin_solapamiento:
            dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days + 1
            resultado.append({
                "oferta": oferta,
                "dias_en_oferta": dias_en_oferta
            })
    return resultado

@login_required
def obtener_habitacion(nombre_hotel, nombre_habitacion):
    try:
        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
        habitacion = Habitacion.objects.get(hotel=hotel, tipo=nombre_habitacion)
        return habitacion
    except ObjectDoesNotExist:
        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{nombre_habitacion}'.")
        return None

@login_required
def obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre):
    try:
        fecha_inicio_viaje, fecha_fin_viaje = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in fecha_viaje.split(' - ')]
        hotel = Hotel.objects.get(hotel_nombre=nombre_hotel)
        ofertas = Oferta.objects.filter(
            hotel=hotel,
            tipo_habitacion=habitacion_nombre,
            disponible=True
        )
        ofertas_validas = []
        for oferta in ofertas:
            fecha_inicio_oferta, fecha_fin_oferta = [datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in oferta.temporada.split(' - ')]
            if fecha_inicio_viaje <= fecha_fin_oferta and fecha_fin_viaje >= fecha_inicio_oferta:
                ofertas_validas.append(oferta)
        return ofertas_validas
    except ObjectDoesNotExist:
        print(f"No se encontró el hotel '{nombre_hotel}' o la habitación '{habitacion_nombre}'.")
        return []
    except ValueError as e:
        print(f"Error al parsear las fechas: {e}")
        return []

@login_required
def recalcular_precio_y_costo(reserva):
    habitaciones_reserva = HabitacionReserva.objects.filter(reserva=reserva)
    precio_total = 0
    for habitacion_reserva in habitaciones_reserva:
        cant_adultos = habitacion_reserva.adultos
        habitacion_nombre = habitacion_reserva.habitacion_nombre
        fecha_viaje = habitacion_reserva.fechas_viaje
        nombre_hotel = reserva.hotel.hotel_nombre
        habitacion = obtener_habitacion(nombre_hotel, habitacion_nombre)
        ofertas = obtener_oferta(nombre_hotel, fecha_viaje, habitacion_nombre)
        if habitacion_reserva.ninos == 1:
            nino1 = 1; nino2 = 0
        elif habitacion_reserva.ninos == 2:
            nino1 = 1; nino2 = 1
        else:
            nino1 = 0; nino2 = 0
        if habitacion and ofertas:
            dias_oferta = calcular_dias_por_oferta(ofertas, fecha_viaje)
            for result in dias_oferta:
                precio_total += calcula_precio(cant_adultos, nino1, nino2, result["oferta"], habitacion, result["dias_en_oferta"])
    return precio_total

# =========================================================================================== #
# ---------------------------------------- PASAJEROS ---------------------------------------- #
# =========================================================================================== #

ESTADO_CIVIL_CHOICES = [
    ('soltero', 'Soltero'),
    ('casado', 'Casado'),
    ('divorciado', 'Divorciado'),
    ('viudo', 'Viudo'),
]
TIPO_CHOICES = [
    ('adulto', 'Adulto'),
    ('nino', 'Niño'),
]


@manager_required
@login_required
def listar_pasajeros(request):
    query = (request.GET.get('q') or '').strip()

    pasajeros_qs = Pasajero.objects.all()
    if query:
        pasajeros_qs = pasajeros_qs.filter(
            Q(nombre__icontains=query) |
            Q(pasaporte__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(pasajeros_qs.order_by('-id'), 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/pasajeros/listar_pasajeros.html', {
        'page_obj': page_obj,
        'query': query,
    })


@manager_required
@login_required
def crear_pasajero(request):
    if request.method == 'POST':
        p = Pasajero(
            nombre=(request.POST.get('nombre') or '').strip(),
            fecha_nacimiento=request.POST.get('fecha_nacimiento') or None,
            pasaporte=(request.POST.get('pasaporte') or '').strip() or None,
            caducidad_pasaporte=request.POST.get('caducidad_pasaporte') or None,
            pais_emision_pasaporte=(request.POST.get('pais_emision_pasaporte') or '').strip() or None,
            email=(request.POST.get('email') or '').strip() or None,
            telefono=(request.POST.get('telefono') or '').strip() or None,
            direccion=(request.POST.get('direccion') or '').strip() or None,
            estado_civil=(request.POST.get('estado_civil') or '') or None,
            tipo=(request.POST.get('tipo') or '') or None,
            # habitacion / traslado opcionales, si los decides incluir en el form:
            habitacion_id=(request.POST.get('habitacion') or None),
            traslado_id=(request.POST.get('traslado') or None),
        )
        # Requisito mínimo
        if not p.nombre:
            valores = request.POST
            return render(request, 'backoffice/pasajeros/crear_pasajero.html', {
                'valores': valores,
                'errores': {'nombre': 'El nombre es obligatorio.'},
                'estado_civil_choices': ESTADO_CIVIL_CHOICES,
                'tipo_choices': TIPO_CHOICES,
            })
        p.save()
        return redirect('backoffice:listar_pasajeros')

    return render(request, 'backoffice/pasajeros/crear_pasajero.html', {
        'estado_civil_choices': ESTADO_CIVIL_CHOICES,
        'tipo_choices': TIPO_CHOICES,
    })


@manager_required
@login_required
def editar_pasajero(request, pk):
    pasajero = get_object_or_404(Pasajero, pk=pk)

    if request.method == 'POST':
        pasajero.nombre = (request.POST.get('nombre') or '').strip()
        pasajero.fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        pasajero.pasaporte = (request.POST.get('pasaporte') or '').strip() or None
        pasajero.caducidad_pasaporte = request.POST.get('caducidad_pasaporte') or None
        pasajero.pais_emision_pasaporte = (request.POST.get('pais_emision_pasaporte') or '').strip() or None
        pasajero.email = (request.POST.get('email') or '').strip() or None
        pasajero.telefono = (request.POST.get('telefono') or '').strip() or None
        pasajero.direccion = (request.POST.get('direccion') or '').strip() or None
        pasajero.estado_civil = (request.POST.get('estado_civil') or '') or None
        pasajero.tipo = (request.POST.get('tipo') or '') or None
        pasajero.habitacion_id = request.POST.get('habitacion') or None
        pasajero.traslado_id = request.POST.get('traslado') or None

        if not pasajero.nombre:
            valores = request.POST
            return render(request, 'backoffice/pasajeros/editar_pasajero.html', {
                'pasajero': pasajero,
                'valores': valores,
                'errores': {'nombre': 'El nombre es obligatorio.'},
                'estado_civil_choices': ESTADO_CIVIL_CHOICES,
                'tipo_choices': TIPO_CHOICES,
            })

        pasajero.save()
        return redirect('backoffice:listar_pasajeros')

    return render(request, 'backoffice/pasajeros/editar_pasajero.html', {
        'pasajero': pasajero,
        'estado_civil_choices': ESTADO_CIVIL_CHOICES,
        'tipo_choices': TIPO_CHOICES,
    })


@manager_required
@login_required
def eliminar_pasajero(request, pk):
    pasajero = get_object_or_404(Pasajero, pk=pk)

    if request.method == 'POST':
        if (request.POST.get('confirm') or '').strip().upper() == 'ELIMINAR':
            pasajero.delete()
            return redirect('backoffice:listar_pasajeros')

    return render(request, 'backoffice/pasajeros/eliminar_pasajero.html', {
        'pasajero': pasajero
    })

# =========================================================================================== #
# --------------------------------- OFERTAS ESPECIALES -------------------------------------- #
# =========================================================================================== #

TIPOS = [
    ('hoteles', 'Hoteles'),
    ('carros', 'Carros'),
    ('vuelos', 'Vuelos'),
    ('traslados', 'Traslados'),
]

@manager_required
@login_required
def listar_ofertas_especiales(request):
    q = (request.GET.get('q') or '').strip()
    tipo = (request.GET.get('tipo') or '').strip()         # '', 'hoteles', ...
    disponible = (request.GET.get('disponible') or '').strip()  # '', '1', '0'

    qs = OfertasEspeciales.objects.all()

    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
    if tipo:
        qs = qs.filter(tipo=tipo)
    if disponible in ('0', '1'):
        qs = qs.filter(disponible=(disponible == '1'))

    qs = qs.order_by('-id')

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/ofertas_especiales/listar_ofertas_especiales.html', {
        'page_obj': page_obj,
        'query': q,
        'tipo': tipo,
        'disponible': disponible,
        'tipos_choices': TIPOS,
    })


@manager_required
@login_required
def crear_oferta_especial(request):
    if request.method == 'POST':
        oferta = OfertasEspeciales(
            codigo=(request.POST.get('codigo') or '').strip(),
            nombre=(request.POST.get('nombre') or '').strip(),
            descripcion=(request.POST.get('descripcion') or '').strip(),
            tipo=(request.POST.get('tipo') or '').strip(),
            disponible=(request.POST.get('disponible') == 'on')
        )
        oferta.save()
        messages.success(request, 'Oferta especial creada exitosamente.')
        return redirect('backoffice:listar_ofertas_especiales')

    return render(request, 'backoffice/ofertas_especiales/crear_oferta_especial.html', {
        'tipos_choices': TIPOS
    })


@manager_required
@login_required
def editar_oferta_especial(request, pk):
    oferta = get_object_or_404(OfertasEspeciales, pk=pk)

    if request.method == 'POST':
        oferta.codigo = (request.POST.get('codigo') or '').strip()
        oferta.nombre = (request.POST.get('nombre') or '').strip()
        oferta.descripcion = (request.POST.get('descripcion') or '').strip()
        oferta.tipo = (request.POST.get('tipo') or '').strip()
        oferta.disponible = (request.POST.get('disponible') == 'on')
        oferta.save()
        messages.success(request, 'Oferta especial actualizada exitosamente.')
        return redirect('backoffice:listar_ofertas_especiales')

    return render(request, 'backoffice/ofertas_especiales/editar_oferta_especial.html', {
        'oferta': oferta,
        'tipos_choices': TIPOS
    })


@manager_required
@login_required
def eliminar_oferta_especial(request, pk):
    oferta = get_object_or_404(OfertasEspeciales, pk=pk)

    if request.method == 'POST':
        # Requerimos confirmación "ELIMINAR" como en los demás módulos
        if (request.POST.get('confirm') or '').strip().upper() == 'ELIMINAR':
            oferta.delete()
            messages.success(request, 'Oferta especial eliminada exitosamente.')
            return redirect('backoffice:listar_ofertas_especiales')

    return render(request, 'backoffice/ofertas_especiales/eliminar_oferta_especial.html', {
        'oferta': oferta
    })
# =========================================================================================== #
# ---------------------------------------- RENTADORAS --------------------------------------- #
# =========================================================================================== #


@manager_required
@login_required
def listar_rentadoras(request):
    query = request.GET.get('q', '').strip()
    proveedor_id = request.GET.get('proveedor', '').strip()

    rentadoras_qs = Rentadora.objects.select_related('proveedor').all()

    if query:
        rentadoras_qs = rentadoras_qs.filter(
            Q(nombre__icontains=query) | Q(proveedor__nombre__icontains=query)
        )
    if proveedor_id:
        rentadoras_qs = rentadoras_qs.filter(proveedor_id=proveedor_id)

    paginator = Paginator(rentadoras_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    proveedores = Proveedor.objects.all().order_by('nombre')

    return render(request, 'backoffice/rentadoras/listar_rentadoras.html', {
        'page_obj': page_obj,
        'query': query,
        'proveedores': proveedores,
        'proveedor_id': proveedor_id,
    })


@manager_required
@login_required
@transaction.atomic
def crear_rentadora(request):
    proveedores = Proveedor.objects.all().order_by('nombre')
    errores = {}
    error_global = None  # <- para errores generales

    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        proveedor_id = (request.POST.get('proveedor') or '').strip()

        # Validaciones
        if not nombre:
            errores['nombre'] = "El nombre es obligatorio."
        if not proveedor_id:
            errores['proveedor'] = "Debes seleccionar un proveedor."

        proveedor = None
        if proveedor_id:
            proveedor = Proveedor.objects.filter(id=proveedor_id).first()
            if not proveedor:
                errores['proveedor'] = "El proveedor seleccionado no existe."

        # Unicidad lógica: misma rentadora bajo el mismo proveedor
        if not errores and Rentadora.objects.filter(
            nombre__iexact=nombre, proveedor_id=proveedor_id
        ).exists():
            errores['nombre'] = "Ya existe una rentadora con ese nombre para este proveedor."

        # Si quieres error general en vez de ligado a un campo:
        # if algun_error_global:
        #     error_global = "Mensaje de error general."

        if not errores and not error_global:
            Rentadora.objects.create(nombre=nombre, proveedor=proveedor)
            messages.success(request, "Rentadora creada correctamente.")
            return redirect('backoffice:listar_rentadoras')

        # Si hay errores, re-render con valores y errores
        return render(request, 'backoffice/rentadoras/crear_rentadora.html', {
            'proveedores': proveedores,
            'valores': {'nombre': nombre, 'proveedor': proveedor_id},
            'errores': errores,
            'error_global': error_global,
        })

    return render(request, 'backoffice/rentadoras/crear_rentadora.html', {
        'proveedores': proveedores,
        'valores': {},
        'errores': errores,
        'error_global': error_global,
    })

@manager_required
@login_required
@transaction.atomic
def editar_rentadora(request, rentadora_id):
    rentadora = get_object_or_404(Rentadora.objects.select_related('proveedor'), id=rentadora_id)
    proveedores = Proveedor.objects.all().order_by('nombre')
    errores = {}

    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        proveedor_id = (request.POST.get('proveedor') or '').strip()

        if not nombre:
            errores['nombre'] = "El nombre es obligatorio."
        if not proveedor_id:
            errores['proveedor'] = "Debes seleccionar un proveedor."

        proveedor = None
        if proveedor_id:
            proveedor = Proveedor.objects.filter(id=proveedor_id).first()
            if not proveedor:
                errores['proveedor'] = "El proveedor seleccionado no existe."

        # Unicidad excluyendo el actual
        if not errores and Rentadora.objects.filter(
            nombre__iexact=nombre, proveedor_id=proveedor_id
        ).exclude(id=rentadora.id).exists():
            errores['nombre'] = "Ya existe una rentadora con ese nombre para este proveedor."

        if not errores:
            rentadora.nombre = nombre
            rentadora.proveedor = proveedor
            rentadora.save()
            messages.success(request, "Cambios guardados correctamente.")
            return redirect('backoffice:listar_rentadoras')

        return render(request, 'backoffice/rentadoras/editar_rentadora.html', {
            'rentadora': rentadora,
            'proveedores': proveedores,
            'valores': {'nombre': nombre, 'proveedor': proveedor_id},
            'errores': errores,
        })

    # GET inicial
    return render(request, 'backoffice/rentadoras/editar_rentadora.html', {
        'rentadora': rentadora,
        'proveedores': proveedores,
        'valores': {'nombre': rentadora.nombre, 'proveedor': str(rentadora.proveedor_id)},
        'errores': errores,
    })


@manager_required
@login_required
@transaction.atomic
def eliminar_rentadora(request, rentadora_id):
    rentadora = get_object_or_404(Rentadora, id=rentadora_id)

    if request.method == 'POST':
        nombre = rentadora.nombre
        rentadora.delete()
        messages.success(request, f"Rentadora «{nombre}» eliminada correctamente.")
        return redirect('backoffice:listar_rentadoras')

    return render(request, 'backoffice/rentadoras/eliminar_rentadora.html', {
        'rentadora': rentadora
    })

@manager_required
@login_required
@require_GET
def detalles_rentadora(request, rentadora_id):
    rentadora = get_object_or_404(
        Rentadora.objects.select_related('proveedor'),
        id=rentadora_id
    )

    data = {
        "id": rentadora.id,
        "nombre": rentadora.nombre,
        "proveedor": {
            "id": rentadora.proveedor.id,
            "nombre": rentadora.proveedor.nombre
        },
        "creado": rentadora.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(rentadora, 'created_at') else None,
        "modificado": rentadora.updated_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(rentadora, 'updated_at') else None,
    }

    return JsonResponse(data)


# =========================================================================================== #
# ---------------------------------------- CATEGORIAS --------------------------------------- #
# =========================================================================================== #
@manager_required
@login_required
def listar_categorias(request):
    # Obtener término de búsqueda (o cadena vacía si no se pasa)
    query = request.GET.get('q', '')

    # Queryset base
    categorias_qs = Categoria.objects.all()
    if query:
        categorias_qs = categorias_qs.filter(
            Q(nombre__icontains=query) |
            Q(gasolina__icontains=query) |
            Q(rentadora__nombre__icontains=query)
        )

    # Paginación: 10 categorías por página
    paginator = Paginator(categorias_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/categorias/listar_categorias.html', {
        'page_obj': page_obj,
        'query': query,
    })
    
@manager_required
@login_required
def crear_categoria(request):
    rentadoras = Rentadora.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        gasolina = request.POST.get('gasolina')
        rentadora_id = request.POST.get('rentadora')
        rentadora = get_object_or_404(Rentadora, id=rentadora_id)

        Categoria.objects.create(nombre=nombre, gasolina=gasolina, rentadora=rentadora)
        return redirect('backoffice:listar_categorias')

    return render(request, 'backoffice/categorias/crear_categoria.html', {'rentadoras': rentadoras})

@manager_required
@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    rentadoras = Rentadora.objects.all()

    if request.method == 'POST':
        categoria.nombre = request.POST.get('nombre')
        categoria.gasolina = request.POST.get('gasolina')
        rentadora_id = request.POST.get('rentadora')
        categoria.rentadora = get_object_or_404(Rentadora, id=rentadora_id)
        categoria.save()
        return redirect('backoffice:listar_categorias')

    return render(request, 'backoffice/categorias/editar_categoria.html', {'categoria': categoria, 'rentadoras': rentadoras})

@manager_required
@login_required
def eliminar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == 'POST':
        categoria.delete()
        return redirect('backoffice:listar_categorias')
    return render(request, 'backoffice/categorias/eliminar_categoria.html', {'categoria': categoria})

# =========================================================================================== #
# ------------------------------------ MODELOS DE AUTOS ------------------------------------- #
# =========================================================================================== #
@manager_required
@login_required
def listar_modelos_autos(request):
    query = request.GET.get('q', '')

    # queryset base y filtro por nombre o categoría
    modelos_qs = ModeloAuto.objects.all()
    if query:
        modelos_qs = modelos_qs.filter(
            Q(nombre__icontains=query) |
            Q(categoria__nombre__icontains=query)
        )

    # paginación: 10 modelos por página
    paginator = Paginator(modelos_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/modelos_autos/listar_modelos_autos.html', {
        'page_obj': page_obj,
        'query': query,
    })
    
@manager_required
@login_required
def crear_modelo_auto(request):
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        foto = request.FILES.get('foto')
        categoria_id = request.POST.get('categoria')
        categoria = get_object_or_404(Categoria, id=categoria_id)

        ModeloAuto.objects.create(nombre=nombre, descripcion=descripcion, foto=foto, categoria=categoria)
        return redirect('backoffice:listar_modelos_autos')

    return render(request, 'backoffice/modelos_autos/crear_modelo_auto.html', {'categorias': categorias})

@manager_required
@login_required
def editar_modelo_auto(request, modelo_id):
    modelo = get_object_or_404(ModeloAuto, id=modelo_id)
    categorias = Categoria.objects.all()

    if request.method == 'POST':
        modelo.nombre = request.POST.get('nombre')
        modelo.descripcion = request.POST.get('descripcion')
        modelo.foto = request.FILES.get('foto') or modelo.foto
        categoria_id = request.POST.get('categoria')
        modelo.categoria = get_object_or_404(Categoria, id=categoria_id)
        modelo.save()
        return redirect('backoffice:listar_modelos_autos')

    return render(request, 'backoffice/modelos_autos/editar_modelo_auto.html', {'modelo': modelo, 'categorias': categorias})

@manager_required
@login_required
def eliminar_modelo_auto(request, modelo_id):
    modelo = get_object_or_404(ModeloAuto, id=modelo_id)
    if request.method == 'POST':
        modelo.delete()
        return redirect('backoffice:listar_modelos_autos')
    return render(request, 'backoffice/modelos_autos/eliminar_modelo_auto.html', {'modelo': modelo})


# =========================================================================================== #
# ---------------------------------------- LOCATIONS ---------------------------------------- #
# =========================================================================================== #

@manager_required
@login_required
def listar_locations(request):
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    aeropuerto = request.GET.get('aeropuerto', '').strip()  # '1', '0' o ''

    qs = Location.objects.select_related('categoria').all()

    if query:
        qs = qs.filter(
            Q(nombre__icontains=query) |
            Q(pais__icontains=query) |
            Q(nomenclatura__icontains=query)
        )

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)

    if aeropuerto in ('0', '1'):
        qs = qs.filter(es_aeropuerto=(aeropuerto == '1'))

    qs = qs.order_by('id')

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/locations/listar_locations.html', {
        'page_obj': page_obj,
        'query': query,
        'categoria_id': categoria_id,
        'aeropuerto': aeropuerto,
        'categorias': Categoria.objects.all().order_by('nombre'),
    })


@manager_required
@login_required
def crear_location(request):
    categorias = Categoria.objects.all().order_by('nombre')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        pais = request.POST.get('pais', '').strip()
        nomenclatura = request.POST.get('nomenclatura', '').strip()
        es_aeropuerto = request.POST.get('es_aeropuerto') == 'on'
        disponibilidad_carros = int(request.POST.get('disponibilidad_carros') or 0)
        categoria_id = request.POST.get('categoria')

        Location.objects.create(
            nombre=nombre,
            pais=pais,
            nomenclatura=nomenclatura,
            es_aeropuerto=es_aeropuerto,
            disponibilidad_carros=disponibilidad_carros,
            categoria=get_object_or_404(Categoria, id=categoria_id),
        )
        return redirect('backoffice:listar_locations')

    return render(request, 'backoffice/locations/crear_location.html', {
        'categorias': categorias
    })


@manager_required
@login_required
def editar_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)
    categorias = Categoria.objects.all().order_by('nombre')

    if request.method == 'POST':
        location.nombre = request.POST.get('nombre', '').strip()
        location.pais = request.POST.get('pais', '').strip()
        location.nomenclatura = request.POST.get('nomenclatura', '').strip()
        location.es_aeropuerto = request.POST.get('es_aeropuerto') == 'on'
        location.disponibilidad_carros = int(request.POST.get('disponibilidad_carros') or 0)
        categoria_id = request.POST.get('categoria')
        location.categoria = get_object_or_404(Categoria, id=categoria_id)
        location.save()
        return redirect('backoffice:listar_locations')

    return render(request, 'backoffice/locations/editar_location.html', {
        'location': location,
        'categorias': categorias
    })


@manager_required
@login_required
def eliminar_location(request, location_id):
    location = get_object_or_404(Location, id=location_id)

    if request.method == 'POST':
        confirm = (request.POST.get('confirm') or '').strip().upper()
        if confirm == 'ELIMINAR':
            location.delete()
            return redirect('backoffice:listar_locations')

    return render(request, 'backoffice/locations/eliminar_location.html', {
        'location': location
    })

# =========================================================================================== #
# --------------------------------- CERTIFICADOS DE VACACIONES ------------------------------ #
# =========================================================================================== #

@manager_required
@login_required
def listar_certificados(request):
    query = request.GET.get('q', '')
    certificados = CertificadoVacaciones.objects.filter(nombre__icontains=query) if query else CertificadoVacaciones.objects.all()
    return render(request, 'backoffice/certificado_vacaciones/listar_certificados.html', {'certificados': certificados, 'query': query})

@manager_required
@login_required
def crear_certificado(request):
    pasajeros = Pasajero.objects.all()
    opciones = OpcionCertificado.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        es_solo_adultos = request.POST.get('es_solo_adultos') == 'on'
        pasajero_id = request.POST.get('pasajero')
        pasajero = get_object_or_404(Pasajero, id=pasajero_id)

        # Crear el certificado de vacaciones
        certificado = CertificadoVacaciones.objects.create(
            nombre=nombre,
            es_solo_adultos=es_solo_adultos,
            pasajero=pasajero
        )

        # Añadir las opciones seleccionadas
        opciones_ids = request.POST.getlist('opciones')
        for opcion_id in opciones_ids:
            opcion = get_object_or_404(OpcionCertificado, id=opcion_id)
            certificado.opciones.add(opcion)

        return redirect('backoffice:listar_certificados')

    return render(request, 'backoffice/certificado_vacaciones/crear_certificado.html', {'pasajeros': pasajeros, 'opciones': opciones})

@manager_required
@login_required
def editar_certificado(request, certificado_id):
    certificado = get_object_or_404(CertificadoVacaciones, id=certificado_id)
    pasajeros = Pasajero.objects.all()
    opciones = OpcionCertificado.objects.all()

    if request.method == 'POST':
        certificado.nombre = request.POST.get('nombre')
        certificado.es_solo_adultos = request.POST.get('es_solo_adultos') == 'on'
        
        pasajero_id = request.POST.get('pasajero')
        certificado.pasajero = get_object_or_404(Pasajero, id=pasajero_id)
        
        # Actualizar las opciones seleccionadas
        opciones_ids = request.POST.getlist('opciones')
        certificado.opciones.clear()  # Limpiar las opciones actuales
        for opcion_id in opciones_ids:
            opcion = get_object_or_404(OpcionCertificado, id=opcion_id)
            certificado.opciones.add(opcion)

        certificado.save()
        return redirect('backoffice:listar_certificados')

    return render(request, 'backoffice/certificado_vacaciones/editar_certificado.html', {'certificado': certificado, 'pasajeros': pasajeros, 'opciones': opciones})

@manager_required
@login_required
def eliminar_certificado(request, certificado_id):
    certificado = get_object_or_404(CertificadoVacaciones, id=certificado_id)
    if request.method == 'POST':
        certificado.delete()
        return redirect('backoffice:listar_certificados')
    return render(request, 'backoffice/certificado_vacaciones/eliminar_certificado.html', {'certificado': certificado})

# =========================================================================================== #
# ---------------------------------- OPCIONES DE CERTIFICADOS ------------------------------- #
# =========================================================================================== #
@manager_required
@login_required
def listar_opciones_certificado(request):
    query = request.GET.get('q', '')
    opciones = OpcionCertificado.objects.filter(nombre__icontains=query) if query else OpcionCertificado.objects.all()
    return render(request, 'backoffice/opciones_certificado/listar_opciones_certificado.html', {'opciones': opciones, 'query': query})

@manager_required
@login_required
def crear_opcion_certificado(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        categoria = request.POST.get('categoria')
        foto = request.FILES.get('foto')

        OpcionCertificado.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            foto=foto
        )
        return redirect('backoffice:listar_opciones_certificado')

    return render(request, 'backoffice/opciones_certificado/crear_opcion_certificado.html')

@manager_required
@login_required
def editar_opcion_certificado(request, opcion_id):
    opcion = get_object_or_404(OpcionCertificado, id=opcion_id)

    if request.method == 'POST':
        opcion.nombre = request.POST.get('nombre')
        opcion.descripcion = request.POST.get('descripcion')
        opcion.categoria = request.POST.get('categoria')
        if 'foto' in request.FILES:
            opcion.foto = request.FILES['foto']
        opcion.save()
        return redirect('backoffice:listar_opciones_certificado')

    return render(request, 'backoffice/opciones_certificado/editar_opcion_certificado.html', {'opcion': opcion})

@manager_required
@login_required
def eliminar_opcion_certificado(request, opcion_id):
    opcion = get_object_or_404(OpcionCertificado, id=opcion_id)
    if request.method == 'POST':
        opcion.delete()
        return redirect('backoffice:listar_opciones_certificado')
    return render(request, 'backoffice/opciones_certificado/eliminar_opcion_certificado.html', {'opcion': opcion})

# -------------------------------------------------------------------------------------------------#
# ---------------------------------------- TASAS DE CAMBIO ----------------------------------------#
@manager_required
@login_required
def listar_tasas_cambio(request):
    tasas_cambio = TasaCambio.objects.all()
    return render(request, 'backoffice/tasas_cambio/listar_tasas_cambio.html', {'tasas_cambio': tasas_cambio})

@manager_required
@login_required
def crear_tasa_cambio(request):
    if request.method == 'POST':
        # Capturar los datos del formulario
        tasa_cup = request.POST.get('tasa_cup')
        tasa_mlc = request.POST.get('tasa_mlc')
        activa = request.POST.get('activa') == 'true'

        # Crear una nueva tasa de cambio
        nueva_tasa = TasaCambio(
            tasa_cup=tasa_cup,
            tasa_mlc=tasa_mlc,
            activa=activa
        )
        nueva_tasa.save()
        return redirect('backoffice:listar_tasas_cambio')

    return render(request, 'backoffice/tasas_cambio/crear_tasa_cambio.html')

@manager_required
@login_required
def editar_tasa_cambio(request, tasa_id):
    tasa_cambio = get_object_or_404(TasaCambio, id=tasa_id)

    if request.method == 'POST':
        # Capturar los datos del formulario
        tasa_cambio.tasa_cup = request.POST.get('tasa_cup')
        tasa_cambio.tasa_mlc = request.POST.get('tasa_mlc')
        tasa_cambio.activa = request.POST.get('activa') == 'true'

        # Guardar los cambios
        tasa_cambio.save()
        return redirect('backoffice:listar_tasas_cambio')

    return render(request, 'backoffice/tasas_cambio/editar_tasa_cambio.html', {'tasa_cambio': tasa_cambio})

@manager_required
@login_required
def eliminar_tasa_cambio(request, tasa_id):
    tasa_cambio = get_object_or_404(TasaCambio, pk=tasa_id)
    if request.method == 'POST':
        tasa_cambio.delete()
        return redirect('backoffice:listar_tasas_cambio')
    return render(request, 'backoffice/tasas_cambio/eliminar_tasa_cambio.html', {'tasa_cambio': tasa_cambio})

# =========================================================================================== #
# ---------------------------------------- TRASLADOS ---------------------------------------- #
# =========================================================================================== #
@manager_required
@login_required
def listar_traslados(request):
    query = request.GET.get('q')
    traslados_list = Traslado.objects.all()

    if query:
        traslados_list = traslados_list.filter(
            transportista__nombre__icontains=query
        ) | traslados_list.filter(
            origen__nombre__icontains=query
        ) | traslados_list.filter(
            destino__nombre__icontains=query
        )

    paginator = Paginator(traslados_list, 10)  # 10 traslados por página
    page_number = request.GET.get('page')
    traslados = paginator.get_page(page_number)

    return render(request, 'backoffice/traslados/listar_traslados.html', {
        'traslados': traslados,
        'query': query,
    })

@manager_required
@login_required
def crear_traslado(request):
    if request.method == 'POST':
        transportista_id = request.POST.get('transportista')
        origen_id = request.POST.get('origen')
        destino_id = request.POST.get('destino')
        vehiculo_id = request.POST.get('vehiculo')
        costo = request.POST.get('costo')

        # Crear traslado
        Traslado.objects.create(
            transportista_id=transportista_id,
            origen_id=origen_id,
            destino_id=destino_id,
            vehiculo_id=vehiculo_id,
            costo=costo
        )
        return redirect('backoffice:listar_traslados')

    transportistas = Transportista.objects.all()
    ubicaciones = Ubicacion.objects.all()
    vehiculos = Vehiculo.objects.all()

    return render(request, 'backoffice/traslados/crear_traslado.html', {
        'transportistas': transportistas,
        'ubicaciones': ubicaciones,
        'vehiculos': vehiculos
    })

@manager_required
@login_required
def editar_traslado(request, traslado_id):
    traslado = get_object_or_404(Traslado, id=traslado_id)

    if request.method == 'POST':
        traslado.transportista_id = request.POST.get('transportista')
        traslado.origen_id = request.POST.get('origen')
        traslado.destino_id = request.POST.get('destino')
        traslado.vehiculo_id = request.POST.get('vehiculo')
        traslado.costo = request.POST.get('costo')
        traslado.save()
        return redirect('backoffice:listar_traslados')

    transportistas = Transportista.objects.all()
    ubicaciones = Ubicacion.objects.all()
    vehiculos = Vehiculo.objects.all()

    return render(request, 'backoffice/traslados/editar_traslado.html', {
        'traslado': traslado,
        'transportistas': transportistas,
        'ubicaciones': ubicaciones,
        'vehiculos': vehiculos
    })


@manager_required
@login_required
def eliminar_traslado(request, traslado_id):
    traslado = get_object_or_404(Traslado, pk=traslado_id)
    if request.method == 'POST':
        traslado.delete()
        return redirect('backoffice:listar_traslados')
    return render(request, 'backoffice/traslados/eliminar_traslado.html', {'traslado': traslado})


# =========================================================================================== #
# ----------------------------------- TRANSPORTISTAS ---------------------------------------- #
# =========================================================================================== #

@manager_required
@login_required
def listar_transportistas(request):
    # Obtener término de búsqueda (o cadena vacía si no se pasó)
    query = request.GET.get('q', '')

    # Queryset base
    transportistas_qs = Transportista.objects.all()

    # Filtrar por nombre si hay búsqueda
    if query:
        transportistas_qs = transportistas_qs.filter(
            nombre__icontains=query
        )

    # Paginación: 10 transportistas por página
    paginator = Paginator(transportistas_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/transportistas/listar_transportistas.html', {
        'page_obj': page_obj,
        'query': query,
    })
    
@manager_required
@login_required
def crear_transportista(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        Transportista.objects.create(nombre=nombre)
        return redirect('backoffice:listar_transportistas')
    return render(request, 'backoffice/transportistas/crear_transportista.html')

@manager_required
@login_required
def editar_transportista(request, transportista_id):
    transportista = get_object_or_404(Transportista, id=transportista_id)
    if request.method == 'POST':
        transportista.nombre = request.POST.get('nombre')
        transportista.save()
        return redirect('backoffice:listar_transportistas')
    return render(request, 'backoffice/transportistas/editar_transportista.html', {'transportista': transportista})

@manager_required
@login_required
def eliminar_transportista(request, transportista_id):
    transportista = get_object_or_404(Transportista, pk=transportista_id)
    if request.method == 'POST':
        transportista.delete()
        return redirect('backoffice:listar_transportistas')
    return render(request, 'backoffice/transportistas/eliminar_transportista.html', {'transportista': transportista})


# ======================================================================================== #
# ----------------------------------- UBICACIONES ---------------------------------------- #
# ======================================================================================== #
@manager_required
@login_required
def listar_ubicaciones(request):
    # Obtener término de búsqueda (o cadena vacía si no se pasó)
    query = request.GET.get('q', '')

    # Queryset base de ubicaciones
    ubicaciones_qs = Ubicacion.objects.all()

    # Filtrar por nombre si hay búsqueda
    if query:
        ubicaciones_qs = ubicaciones_qs.filter(nombre__icontains=query)

    # Paginación: 10 ubicaciones por página
    paginator = Paginator(ubicaciones_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/ubicaciones/listar_ubicaciones.html', {
        'page_obj': page_obj,
        'query': query,
    })


@manager_required
@login_required
def crear_ubicacion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        Ubicacion.objects.create(nombre=nombre)
        return redirect('backoffice:listar_ubicaciones')
    return render(request, 'backoffice/ubicaciones/crear_ubicacion.html')

@manager_required
@login_required
def editar_ubicacion(request, ubicacion_id):
    ubicacion = get_object_or_404(Ubicacion, id=ubicacion_id)
    if request.method == 'POST':
        ubicacion.nombre = request.POST.get('nombre')
        ubicacion.save()
        return redirect('backoffice:listar_ubicaciones')
    return render(request, 'backoffice/ubicaciones/editar_ubicacion.html', {'ubicacion': ubicacion})

@manager_required
@login_required
def eliminar_ubicacion(request, ubicacion_id):
    ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
    if request.method == 'POST':
        ubicacion.delete()
        return redirect('backoffice:listar_ubicaciones')
    return render(request, 'backoffice/ubicaciones/eliminar_ubicacion.html', {'ubicacion': ubicacion})


# ====================================================================================== #
# ----------------------------------- VEHICULOS ---------------------------------------- #
# ====================================================================================== #
@manager_required
@login_required
def listar_vehiculos(request):
    # obtener término de búsqueda (o cadena vacía si no viene)
    query = request.GET.get('q', '')

    # queryset base
    vehiculos_qs = Vehiculo.objects.all()

    # filtrar por tipo (label) si hay búsqueda
    if query:
        # asumiendo que quieres buscar en el campo 'tipo' (valor interno) o en la representación:
        vehiculos_qs = vehiculos_qs.filter(
            Q(tipo__icontains=query) |
            Q(get_tipo_display__icontains=query)
        )

    # paginación: 10 vehículos por página
    paginator = Paginator(vehiculos_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/vehiculos/listar_vehiculos.html', {
        'page_obj': page_obj,
        'query': query,
    })
    
@manager_required
@login_required
def crear_vehiculo(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        capacidad_min = request.POST.get('capacidad_min')
        capacidad_max = request.POST.get('capacidad_max')
        foto = request.FILES.get('foto', None)

        # Crear y guardar el vehículo
        vehiculo = Vehiculo(
            tipo=tipo,
            capacidad_min=capacidad_min,
            capacidad_max=capacidad_max,
            foto=foto
        )
        vehiculo.save()

        return redirect('backoffice:listar_vehiculos')

    return render(request, 'backoffice/vehiculos/crear_vehiculo.html')

@manager_required
@login_required
def editar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
    
    if request.method == 'POST':
        vehiculo.tipo = request.POST.get('tipo')
        vehiculo.capacidad_min = request.POST.get('capacidad_min')
        vehiculo.capacidad_max = request.POST.get('capacidad_max')

        # Manejo de la imagen subida
        if 'foto' in request.FILES:
            vehiculo.foto = request.FILES['foto']

        vehiculo.save()
        return redirect('backoffice:listar_vehiculos')
    
    return render(request, 'backoffice/vehiculos/editar_vehiculo.html', {'vehiculo': vehiculo})

@manager_required
@login_required
def eliminar_vehiculo(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    if request.method == 'POST':
        vehiculo.delete()
        return redirect('backoffice:listar_vehiculos')
    
    return render(request, 'backoffice/vehiculos/eliminar_vehiculo.html', {'vehiculo': vehiculo})

# ====================================================================================== #
# ====================================================================================== #
# ====================================================================================== #
# ====================================================================================== #


# Carga el Editar Reserva #
@login_required
def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    proveedores = Proveedor.objects.all()
    habitaciones = reserva.habitaciones_reserva.prefetch_related('pasajeros').all()

    context = {
        "reserva": reserva,
        "proveedores": proveedores,
        "habitaciones": habitaciones,
        "estatus_choices": Reserva._meta.get_field('estatus').choices,
    }
    return render(request, 'backoffice/reservas/editar_reserva.html', context)



logger = logging.getLogger(__name__)


# ------------------ Funciones Auxiliares de Conversión ------------------ #

@login_required
def convertir_fecha(valor, valor_default="2050-12-31"):
    """
    Convierte un string de fecha a formato YYYY-MM-DD.
    Prueba primero con formato MM/DD/YYYY y luego YYYY-MM-DD.
    Si falla, retorna el valor por defecto.
    """
    
    print(f'                  >>>>> Entro a Convertir Fechas')
    
    if not valor:
        return valor_default
    try:
        # Intentamos el formato MM/DD/YYYY
        fecha = datetime.strptime(valor, "%m/%d/%Y").date()
        return fecha.isoformat()
    except ValueError:
        try:
            # Intentamos el formato YYYY-MM-DD
            fecha = datetime.strptime(valor, "%Y-%m-%d").date()
            return fecha.isoformat()
        except ValueError:
            logger.error(f"Formato de fecha inválido: {valor}. Se usa valor por defecto: {valor_default}")
            return valor_default

# ------------------ Funciones para procesar Pasajeros / Habitaciones ------------------ #
@login_required
def procesar_pasajeros(request, room, habitacion_index, pasajero_count):
    """
    Procesa los pasajeros de una habitación, actualizando contadores de adultos y niños.
    Devuelve (adultos, ninos) para recalcular la habitación al final.
    """
    
    print(f'                >>>>> Entro a Procesar Pasajeros')
    
    adultos = 0
    ninos = 0

    for j in range(1, pasajero_count + 1):
        pasajero_id = request.POST.get(f"pasajero_id_{habitacion_index}_{j}")
        pasajero_tipo = request.POST.get(f"pasajero_tipo_{habitacion_index}_{j}", '').lower()
        logger.debug(f"Habitación {habitacion_index} - Procesando pasajero {j} de tipo: {pasajero_tipo}")

        if pasajero_tipo == 'adulto':
            adultos += 1
        elif pasajero_tipo == 'nino':
            ninos += 1

        if pasajero_id:
            try:
                pasajero = Pasajero.objects.get(id=pasajero_id)
                logger.debug(f"Habitación {habitacion_index} - Pasajero existente con id: {pasajero_id}")
            except Pasajero.DoesNotExist:
                logger.error(f"No se encontró el pasajero con id {pasajero_id}.")
                messages.error(request, f"No se encontró el pasajero con id {pasajero_id}.")
                continue
        else:
            pasajero = Pasajero(habitacion=room)
            logger.debug(f"Habitación {habitacion_index} - Creando nuevo pasajero, índice {j}")

        pasajero.nombre = request.POST.get(f"pasajero_nombre_{habitacion_index}_{j}", '')
        pasajero.pasaporte = request.POST.get(f"pasajero_pasaporte_{habitacion_index}_{j}", '')

        # Convertir la fecha de caducidad del pasaporte a 'YYYY-MM-DD'
        caducidad_input = request.POST.get(f"pasajero_caducidad_pasaporte_{habitacion_index}_{j}", "2050-12-31")
        pasajero.caducidad_pasaporte = convertir_fecha(caducidad_input)

        pasajero.pais_emision_pasaporte = request.POST.get(f"pasajero_pais_emision_pasaporte_{habitacion_index}_{j}", '')
        pasajero.tipo = pasajero_tipo  # 'adulto' o 'nino'

        try:
            pasajero.save()
            logger.debug(f"Pasajero {pasajero.id} guardado correctamente.")
        except Exception as e:
            logger.error(f"Error al guardar pasajero: {e}", exc_info=True)
            messages.error(request, f"Error al guardar pasajero: {e}")

    return adultos, ninos

# ------------------ Funciones de Cálculo de Precios ------------------ #
@login_required
def calcula_precio(cant_adultos, nino1, nino2, oferta, habitacion, dias_en_oferta):
    """
    Tu lógica detallada para una oferta específica, p.ej.:
    - 'oferta' tiene los campos doble, triple, sencilla, etc.
    - calculas la parte sin fee y la parte con fee, etc.
    
    Devuelve (precio_total, precio_sin_fee, fee_total).
    """
    
    print(f'          >>>>> Entro a Calcular Precio')
    
    
    # Aquí pegas la misma lógica que ya tienes en tu 'calcula_precio'
    # con los if/elif (cant_adultos == 1, 2, 3...) y la multiplicación
    # por dias_en_oferta
    #
    # Ejemplo muy simplificado:
    from decimal import Decimal
    
    precio_sin_fee = Decimal("0.00")
    fee_total = Decimal("0.00")

    # ...
    # Ajusta según tu lógica
    # ...
    precio_total = precio_sin_fee + fee_total
    return precio_total, precio_sin_fee, fee_total

@login_required
def calcular_precio_habitacion(habitacion, ofertas, cant_adultos, cant_ninos, edades_ninos, 
                               fecha_viaje, fee_hotel, fee_nino, tipo_fee_hotel):
    """
    Calcula el precio final para una habitación dada, basándose en:
      - Tipo de habitación y sus reglas (triple, doble, etc.).
      - Ofertas disponibles.
      - Cantidad de adultos, niños y sus edades.
      - Fechas de viaje.
      - Reglas de fee (tipo_fee_hotel: "PAX", "Reserva", "%", etc.).
    Devuelve un Decimal con el precio total final.
    """
    
    print(f'          >>>>> Entro a Calcular Precio Habitacion')
    
    from decimal import Decimal

    fecha_inicio_str, fecha_fin_str = fecha_viaje.split(" - ")
    fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
    cantidad_noches = (fecha_fin - fecha_inicio).days

    nino1 = 1 if cant_ninos >= 1 else 0
    nino2 = 1 if cant_ninos >= 2 else 0
    
    # Filtrar ofertas relevantes
    ofertas_tipo = [o for o in ofertas if o.tipo_habitacion == habitacion.tipo and o.disponible]

    precio_final = Decimal("0.00")

    for oferta in ofertas_tipo:
        try:
            oferta_inicio_str, oferta_fin_str = oferta.temporada.split(" - ")
            oferta_inicio = datetime.strptime(oferta_inicio_str, "%Y-%m-%d").date()
            oferta_fin = datetime.strptime(oferta_fin_str, "%Y-%m-%d").date()

            inicio_solapamiento = max(fecha_inicio, oferta_inicio)
            fin_solapamiento = min(fecha_fin, oferta_fin)

            dias_en_oferta = 0
            if inicio_solapamiento < fin_solapamiento:
                dias_en_oferta = (fin_solapamiento - inicio_solapamiento).days
            elif inicio_solapamiento == fin_solapamiento:
                dias_en_oferta = 1

            if dias_en_oferta > 0:
                costo_oferta, precio_sin_fee, fee_total = calcula_precio(
                    cant_adultos, 
                    nino1, 
                    nino2, 
                    oferta, 
                    habitacion, 
                    dias_en_oferta
                )
                precio_final += Decimal(costo_oferta)
        except ValueError as e:
            logger.error(f"Error al procesar oferta {oferta}: {e}")
            continue

    # Aplica fee segun "PAX", "Reserva", "%", etc.
    if tipo_fee_hotel == "PAX":
        suplemento = (Decimal(fee_hotel) * cant_adultos + Decimal(fee_nino) * cant_ninos) * cantidad_noches
        precio_final += suplemento
    elif tipo_fee_hotel == "Reserva":
        precio_final += Decimal(fee_hotel)
    else:
        # Asumimos que es porcentaje
        precio_final += precio_final * Decimal(fee_hotel) / Decimal("100.00")

    return precio_final


# ------------------ Vista Principal para Guardar Reserva ------------------ #


def parse_fecha(fecha_str):
    if not fecha_str or fecha_str == '':
        return None
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except:
        return None


@transaction.atomic
def guardar_edicion_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)

    if request.method == 'POST':
        print("\n===========================")
        print(f"📝 ENTRANDO A EDITAR RESERVA ID {reserva.id}...")
        for h in reserva.habitaciones_reserva.all():
            print(f"➡️ Habitación: {h.habitacion_nombre} | ID: {h.id}")
            for p in h.pasajeros.all():
                print(f"   👤 Pasajero: {p.nombre} | ID: {p.id}")
        print("===========================\n")

        print("===========================")
        print("📥 PARTE DE RESERVA: Procesando POST para guardar reserva...")
        reserva.nombre_usuario = request.POST.get('nombre_usuario', '')
        reserva.email_empleado = request.POST.get('email_empleado', '')
        reserva.numero_confirmacion = request.POST.get('numero_confirmacion', '')
        proveedor_id = request.POST.get('proveedor', '')
        reserva.proveedor = get_object_or_404(Proveedor, id=proveedor_id) if proveedor_id else None
        reserva.costo_sin_fee = Decimal(request.POST.get('costo_sin_fee') or 0)
        reserva.costo_total = Decimal(request.POST.get('costo_total') or 0)
        reserva.precio_total = Decimal(request.POST.get('precio_total') or 0)
        reserva.estatus = request.POST.get('estatus', reserva.estatus)
        reserva.cobrada = request.POST.get('cobrada') == 'on'
        reserva.pagada = request.POST.get('pagada') == 'on'
        reserva.notas = request.POST.get('notas', '')
        reserva.save()
        print("✅ Datos generales de reserva actualizados\n")

        habitaciones_existentes = {str(h.id): h for h in reserva.habitaciones_reserva.all()}
        habitaciones_enviadas = []

        for key in request.POST.keys():
            if key.startswith('habitacion_nombre_'):
                index_hab = key.split('_')[-1]
                habitaciones_enviadas.append(index_hab)

        habitaciones_actualizadas = []

        for hab_index in habitaciones_enviadas:
            print("===========================")
            print(f"🔁 Procesando habitación índice {hab_index}...")

            habitacion_id = request.POST.get(f'habitacion_id_{hab_index}', '')
            habitacion_nombre = request.POST.get(f'habitacion_nombre_{hab_index}', '')
            fechas_viaje = request.POST.get(f'fechas_viaje_{hab_index}', '')
            precio = Decimal(request.POST.get(f'precio_{hab_index}', 0) or 0)
            adultos = int(request.POST.get(f'adultos_{hab_index}', 0) or 0)
            ninos = int(request.POST.get(f'ninos_{hab_index}', 0) or 0)

            if habitacion_id and habitacion_id in habitaciones_existentes:
                habitacion = habitaciones_existentes[habitacion_id]
                habitacion.habitacion_nombre = habitacion_nombre
                habitacion.fechas_viaje = fechas_viaje
                habitacion.precio = precio
                habitacion.adultos = adultos
                habitacion.ninos = ninos
                habitacion.save()
                print(f"🔁 Habitación actualizada ID {habitacion.id} ({habitacion_nombre})")
            else:
                habitacion = HabitacionReserva.objects.create(
                    reserva=reserva,
                    habitacion_nombre=habitacion_nombre,
                    fechas_viaje=fechas_viaje,
                    precio=precio,
                    adultos=adultos,
                    ninos=ninos,
                    oferta_codigo=''
                )
                print(f"🆕 Habitación creada ID {habitacion.id} ({habitacion_nombre})")

            habitaciones_actualizadas.append(habitacion.id)

            pasajeros_existentes = {str(p.id): p for p in habitacion.pasajeros.all()}
            pasajeros_actualizados = []

            print("===========================")
            print(f"🧍 Procesando pasajeros de habitación ID {habitacion.id} ({habitacion_nombre})...")

            for key in request.POST.keys():
                if key.startswith(f'pasajero_id_{habitacion.id}_'):
                    pasajero_id = key.split(f'pasajero_id_{habitacion.id}_')[-1]
                    id_valor = request.POST.get(key)

                    nombre = request.POST.get(f'pasajero_nombre_{habitacion.id}_{pasajero_id}', '')
                    fecha_nacimiento = parse_fecha(request.POST.get(f'pasajero_fecha_nacimiento_{habitacion.id}_{pasajero_id}', ''))
                    pasaporte = request.POST.get(f'pasajero_pasaporte_{habitacion.id}_{pasajero_id}', '')
                    caducidad_pasaporte = parse_fecha(request.POST.get(f'pasajero_caducidad_pasaporte_{habitacion.id}_{pasajero_id}', ''))
                    pais_emision_pasaporte = request.POST.get(f'pasajero_pais_emision_pasaporte_{habitacion.id}_{pasajero_id}', '')

                    if id_valor != 'nuevo' and id_valor in pasajeros_existentes:
                        pasajero = pasajeros_existentes[id_valor]
                        pasajero.nombre = nombre
                        pasajero.fecha_nacimiento = fecha_nacimiento
                        pasajero.pasaporte = pasaporte
                        pasajero.caducidad_pasaporte = caducidad_pasaporte
                        pasajero.pais_emision_pasaporte = pais_emision_pasaporte
                        pasajero.save()
                        pasajeros_actualizados.append(int(id_valor))
                        print(f"🔁 Editando pasajero ID {pasajero.id} ({nombre})")
                    else:
                        pasajero = Pasajero.objects.create(
                            habitacion=habitacion,
                            nombre=nombre,
                            fecha_nacimiento=fecha_nacimiento,
                            pasaporte=pasaporte,
                            caducidad_pasaporte=caducidad_pasaporte,
                            pais_emision_pasaporte=pais_emision_pasaporte
                        )
                        pasajeros_actualizados.append(pasajero.id)
                        print(f"🆕 Creando pasajero ID {pasajero.id} ({nombre})")

            for p_id, pasajero in pasajeros_existentes.items():
                if int(p_id) not in pasajeros_actualizados:
                    print(f"🗑️ Eliminando pasajero ID {p_id} ({pasajero.nombre})")
                    pasajero.delete()

        for h_id, habitacion in habitaciones_existentes.items():
            if int(h_id) not in habitaciones_actualizadas:
                print(f"🗑️ Habitación eliminada ID {h_id} ({habitacion.habitacion_nombre})")
                habitacion.delete()

        print("===========================")
        print(f"📝 ESTADO FINAL RESERVA ID {reserva.id}...")
        for h in reserva.habitaciones_reserva.all():
            print(f"➡️ Habitación: {h.habitacion_nombre} | ID: {h.id}")
            for p in h.pasajeros.all():
                print(f"   👤 Pasajero: {p.nombre} | ID: {p.id}")
        print("===========================\n")

        if reserva.estatus in ['confirmada', 'ejecutada'] and reserva.email_empleado:
            print(f"📤 Enviando voucher automático para reserva ID {reserva.id} con estatus '{reserva.estatus}'...")
            try:
                from apps.backoffice.utils.email_voucher_distal import enviar_voucher_hotel_distal
                enviar_voucher_hotel_distal(reserva)
                messages.success(request, "Reserva actualizada y voucher enviado exitosamente.")
                print("✅ Voucher enviado correctamente.")
            except Exception as e:
                print(f"❌ Error al enviar el voucher: {e}")
                messages.warning(request, f"Reserva actualizada, pero ocurrió un error al enviar el voucher: {str(e)}")

        messages.success(request, "Reserva actualizada correctamente.")
        return redirect('backoffice:listar_reservas')

    else:
        messages.error(request, "Error al procesar la solicitud.")
        return redirect('backoffice:editar_reserva', reserva_id=reserva_id)


# ====================================================================================== #
# ----------------------------------- CLIENTES  ---------------------------------------- #
# ====================================================================================== #

@login_required
def listar_clientes(request):
    q = request.GET.get('q', '')
    clientes_list = Cliente.objects.all()

    if q:
        # Ajusta tu lógica de búsqueda a los campos del nuevo modelo
        clientes_list = clientes_list.filter(
            Q(nombre__icontains=q) |
            Q(apellidos__icontains=q) |
            Q(email__icontains=q) |
            Q(telefono_principal__icontains=q)
        )

    paginator = Paginator(clientes_list, 10)  # 10 resultados por página
    page_number = request.GET.get('page')
    clientes_page = paginator.get_page(page_number)

    context = {
        'clientes': clientes_page,
        'query': q
    }
    return render(request, 'backoffice/clientes/listar_clientes.html', context)

@login_required
def crear_cliente(request):
    if request.method == 'POST':
        # Capturar todos los campos del formulario según tu modelo actual
        nombre = request.POST.get('nombre', '')
        apellidos = request.POST.get('apellidos', '')

        pasaporte = request.POST.get('pasaporte', '')
        carnet_identidad = request.POST.get('carnet_identidad', '')
        licencia = request.POST.get('licencia', '')

        telefono_principal = request.POST.get('telefono_principal', '')
        email = request.POST.get('email', '')

        direccion = request.POST.get('direccion', '')
        ciudad = request.POST.get('ciudad', '')
        estado = request.POST.get('estado', '')
        pais = request.POST.get('pais', '')
        zip_code_str = request.POST.get('zip_code', '')

        fecha_nacimiento_str = request.POST.get('fecha_nacimiento', None)
        observaciones = request.POST.get('observaciones', '')

        # Manejo del checkbox VIP
        es_vip = request.POST.get('es_vip', 'off')

        # Parsear fecha_nacimiento
        fecha_nacimiento = None
        if fecha_nacimiento_str:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_nacimiento = None

        # Crear instancia del modelo Cliente
        cliente = Cliente(
            nombre=nombre,
            apellidos=apellidos,
            pasaporte=pasaporte,
            carnet_identidad=carnet_identidad,
            licencia=licencia,
            telefono_principal=telefono_principal,
            email=email,
            direccion=direccion,
            ciudad=ciudad,
            estado=estado,
            pais=pais,
            zip_code=zip_code_str,
            fecha_nacimiento=fecha_nacimiento,
            observaciones=observaciones,
            es_vip=(es_vip == 'on')
        )
        cliente.save()

        # Redirigir al listado de clientes
        return redirect('backoffice:listar_clientes')

    # GET: Mostrar formulario vacío
    return render(request, 'backoffice/clientes/crear_cliente.html')

@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        apellidos = request.POST.get('apellidos', '')

        pasaporte = request.POST.get('pasaporte', '')
        carnet_identidad = request.POST.get('carnet_identidad', '')
        licencia = request.POST.get('licencia', '')
        pasaporte_licencia = request.POST.get('pasaporte_licencia', '')

        telefono_principal = request.POST.get('telefono_principal', '')
        email = request.POST.get('email', '')

        direccion = request.POST.get('direccion', '')
        ciudad = request.POST.get('ciudad', '')
        estado = request.POST.get('estado', '')
        pais = request.POST.get('pais', '')
        zip_code = request.POST.get('zip_code', '')

        fecha_nacimiento_str = request.POST.get('fecha_nacimiento', None)
        observaciones = request.POST.get('observaciones', '')
        es_vip = request.POST.get('es_vip', 'off')

        fecha_nacimiento = None
        if fecha_nacimiento_str:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_nacimiento = None

        cliente.nombre = nombre
        cliente.apellidos = apellidos
        cliente.pasaporte = pasaporte
        cliente.carnet_identidad = carnet_identidad
        cliente.licencia = licencia
        cliente.pasaporte_licencia = pasaporte_licencia
        cliente.telefono_principal = telefono_principal
        cliente.email = email
        cliente.direccion = direccion
        cliente.ciudad = ciudad
        cliente.estado = estado
        cliente.pais = pais
        cliente.zip_code = zip_code
        cliente.fecha_nacimiento = fecha_nacimiento
        cliente.observaciones = observaciones
        cliente.es_vip = (es_vip == 'on')

        cliente.save()
        return redirect('backoffice:listar_clientes')

    return render(request, 'backoffice/clientes/editar_cliente.html', {'cliente': cliente})


def _pick(*vals):
    """Devuelve el primer valor no vacío (truthy) de la lista."""
    for v in vals:
        if v is not None and str(v).strip() != "":
            return v
    return None

@login_required
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)

    # Coalesce de campos para soportar distintos nombres usados en tus formularios
    nombre = _pick(getattr(cliente, "primer_nombre", None),
                   getattr(cliente, "nombre", None))
    segundo_nombre = getattr(cliente, "segundo_nombre", None)
    apellido = _pick(getattr(cliente, "primer_apellido", None),
                     getattr(cliente, "apellidos", None))
    segundo_apellido = getattr(cliente, "segundo_apellido", None)

    nombre_completo = " ".join([p for p in [nombre, segundo_nombre, apellido, segundo_apellido] if _pick(p)])

    telefono = _pick(
        getattr(cliente, "telefono", None),
        getattr(cliente, "telefono_principal", None),
        getattr(cliente, "movil", None),
        getattr(cliente, "celular", None),
    )

    identificacion = _pick(
        getattr(cliente, "numero_documento", None),
        getattr(cliente, "carnet_identidad", None),
        getattr(cliente, "ci", None),
        getattr(cliente, "pasaporte", None),
        getattr(cliente, "licencia", None),
        getattr(cliente, "pasaporte_licencia_extra", None),
        getattr(cliente, "documento", None),
    )

    email = _pick(getattr(cliente, "email", None),
                  getattr(cliente, "correo", None))

    if request.method == 'POST':
        confirm_text = request.POST.get('confirm', '').strip().upper()
        if confirm_text == 'ELIMINAR':
            cliente.delete()
            messages.success(request, _("El cliente ‘%(nombre)s’ fue eliminado correctamente.") % {"nombre": nombre_completo or _("Sin nombre")})
            return redirect('backoffice:listar_clientes')
        else:
            messages.error(request, _("Debes escribir 'ELIMINAR' para confirmar la eliminación."))

    context = {
        "cliente": cliente,
        # Valores normalizados para la plantilla
        "info": {
            "nombre_completo": nombre_completo,
            "telefono": telefono,
            "identificacion": identificacion,
            "email": email,
        },
    }
    return render(request, 'backoffice/clientes/eliminar_cliente.html', context)


# ====================================================================================== #
# ----------------------------------- CONTACTOS ---------------------------------------- #
# ====================================================================================== #
@login_required
def crear_contacto(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        apellidos = request.POST.get('apellidos', '')
        fecha_nacimiento_str = request.POST.get('fecha_nacimiento', '')

        carnet_identidad = request.POST.get('carnet_identidad', '')
        pasaporte_licencia = request.POST.get('pasaporte_licencia', '')
        nacionalidad = request.POST.get('nacionalidad', '')

        telefono_primario = request.POST.get('telefono_primario', '')
        telefono_secundario = request.POST.get('telefono_secundario', '')
        email = request.POST.get('email', '')

        calle = request.POST.get('calle', '')
        numero = request.POST.get('numero', '')   # <-- antes venía 'No'
        entre_calle = request.POST.get('entre_calle', '')
        y_calle = request.POST.get('y_calle', '')
        apto_reparto = request.POST.get('apto_reparto', '')
        piso = request.POST.get('piso', '')
        municipio = request.POST.get('municipio', '')
        provincia = request.POST.get('provincia', '')
        reparto = request.POST.get('reparto', '')
        ciudad = request.POST.get('ciudad', '')
        estado = request.POST.get('estado', '')
        zip_code = request.POST.get('zip_code', '')

        observaciones = request.POST.get('observaciones', '')

        fecha_nacimiento = None
        if fecha_nacimiento_str:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_nacimiento = None

        contacto = Contacto(
            cliente=cliente,
            nombre=nombre,
            apellidos=apellidos,
            fecha_nacimiento=fecha_nacimiento,
            carnet_identidad=carnet_identidad,
            pasaporte_licencia=pasaporte_licencia,
            nacionalidad=nacionalidad,
            telefono_primario=telefono_primario,
            telefono_secundario=telefono_secundario,
            email=email,
            calle=calle,
            numero=numero,
            entre_calle=entre_calle,
            y_calle=y_calle,
            apto_reparto=apto_reparto,
            piso=piso,
            municipio=municipio,
            provincia=provincia,
            reparto=reparto,
            ciudad=ciudad,
            estado=estado,
            zip_code=zip_code,
            observaciones=observaciones
        )
        contacto.save()
        return redirect('backoffice:editar_cliente', pk=cliente.id)

    return redirect('backoffice:editar_cliente', pk=cliente.id)


@login_required
def editar_contacto(request, contacto_id):
    contacto = get_object_or_404(Contacto, pk=contacto_id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '')
        apellidos = request.POST.get('apellidos', '')
        fecha_nacimiento_str = request.POST.get('fecha_nacimiento', '')

        carnet_identidad = request.POST.get('carnet_identidad', '')
        pasaporte_licencia = request.POST.get('pasaporte_licencia', '')
        nacionalidad = request.POST.get('nacionalidad', '')

        telefono_primario = request.POST.get('telefono_primario', '')
        telefono_secundario = request.POST.get('telefono_secundario', '')
        email = request.POST.get('email', '')

        calle = request.POST.get('calle', '')
        numero = request.POST.get('numero', '')  # <-- corregido
        entre_calle = request.POST.get('entre_calle', '')
        y_calle = request.POST.get('y_calle', '')
        apto_reparto = request.POST.get('apto_reparto', '')
        piso = request.POST.get('piso', '')
        municipio = request.POST.get('municipio', '')
        provincia = request.POST.get('provincia', '')
        reparto = request.POST.get('reparto', '')
        ciudad = request.POST.get('ciudad', '')
        estado = request.POST.get('estado', '')
        zip_code = request.POST.get('zip_code', '')

        observaciones = request.POST.get('observaciones', '')

        fecha_nacimiento = None
        if fecha_nacimiento_str:
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d').date()
            except ValueError:
                fecha_nacimiento = None

        contacto.nombre = nombre
        contacto.apellidos = apellidos
        contacto.fecha_nacimiento = fecha_nacimiento
        contacto.carnet_identidad = carnet_identidad
        contacto.pasaporte_licencia = pasaporte_licencia
        contacto.nacionalidad = nacionalidad
        contacto.telefono_primario = telefono_primario
        contacto.telefono_secundario = telefono_secundario
        contacto.email = email
        contacto.calle = calle
        contacto.numero = numero     # <-- corregido
        contacto.entre_calle = entre_calle
        contacto.y_calle = y_calle
        contacto.apto_reparto = apto_reparto
        contacto.piso = piso
        contacto.municipio = municipio
        contacto.provincia = provincia
        contacto.reparto = reparto
        contacto.ciudad = ciudad
        contacto.estado = estado
        contacto.zip_code = zip_code
        contacto.observaciones = observaciones

        contacto.save()
        return redirect('backoffice:editar_cliente', pk=contacto.cliente.id)

    return render(request, 'backoffice/clientes/editar_contacto.html', {'contacto': contacto})

@login_required
def eliminar_contacto(request, contacto_id):
    contacto = get_object_or_404(Contacto, pk=contacto_id)
    cliente_id = contacto.cliente.id
    contacto.delete()
    return redirect('backoffice:editar_cliente', pk=cliente_id)

# ====================================================================================== #
# ---------------------------------------- ENVÍOS -------------------------------------- #
# ====================================================================================== #

@manager_required
@login_required
def listar_envios(request):
    query = request.GET.get('q', '')

    envios_qs = Envio.objects.select_related('remitente', 'destinatario').all()

    if query:
        envios_qs = envios_qs.filter(
            Q(remitente__nombre_apellido__icontains=query) |
            Q(destinatario__primer_nombre__icontains=query) |
            Q(destinatario__primer_apellido__icontains=query)
        )

    paginator = Paginator(envios_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/envios/listar_envios.html', {
        'page_obj': page_obj,
        'query': query,
    })


def _clean(v): return (v or "").strip()

@manager_required
@login_required
def crear_envio(request):
    errores, valores = {}, {}
    # Orden correctísimo con tus campos reales
    remitentes = Remitente.objects.all().order_by('nombre_apellido')
    destinatarios = Destinatario.objects.all().order_by('primer_nombre', 'primer_apellido')

    if request.method == 'POST':
        for c in ['remitente','destinatario','modalidad','servicio',
                  'item_hbl','item_descripcion','item_cantidad','item_peso','item_precio','item_valor_aduanal','item_tipo']:
            valores[c] = _clean(request.POST.get(c))

        # Validaciones mínimas del Envío
        if not valores['remitente']:
            errores['remitente'] = _("El remitente es obligatorio.")
        if not valores['destinatario']:
            errores['destinatario'] = _("El destinatario es obligatorio.")

        if not errores:
            envio = Envio.objects.create(
                remitente_id=valores['remitente'],
                destinatario_id=valores['destinatario'],
                modalidad=valores['modalidad'] or None,
                servicio=valores['servicio'] or None,
            )

            # Crear Item opcional si hay al menos descripción o cantidad/peso
            hay_item = any([valores['item_hbl'], valores['item_descripcion'],
                            valores['item_cantidad'], valores['item_peso'], valores['item_precio']])
            if hay_item:
                try:
                    ItemEnvio.objects.create(
                        envio=envio,
                        hbl=valores['item_hbl'] or "",
                        descripcion=valores['item_descripcion'] or "",
                        cantidad=int(valores['item_cantidad'] or 1),
                        peso=float(valores['item_peso'] or 0) or 0,
                        precio=float(valores['item_precio'] or 0) or 0,
                        valor_aduanal=float(valores['item_valor_aduanal'] or 0) or 0,
                        tipo=valores['item_tipo'] or None,
                        envio_manejo=None,
                    )
                except Exception:
                    # No rompemos el flujo si el ítem falla; solo avisamos
                    messages.warning(request, _("El envío se creó pero el ítem opcional no fue válido."))

            messages.success(request, _("Envío creado correctamente."))
            return redirect('backoffice:listar_envios')
        else:
            messages.error(request, _("Por favor corrige los errores."))

    return render(request, 'backoffice/envios/crear_envio.html', {
        'remitentes': remitentes,
        'destinatarios': destinatarios,
        'errores': errores,
        'valores': valores,
    })

def _any(vals): return any(_clean(v) for v in vals)

@manager_required
@login_required
def editar_envio(request, envio_id):
    envio = get_object_or_404(Envio, id=envio_id)
    errores, valores = {}, {}

    remitentes = Remitente.objects.all().order_by('nombre_apellido')
    destinatarios = Destinatario.objects.all().order_by('primer_nombre', 'primer_apellido')

    # Primer ítem (si existe) y variables "seguras" para la plantilla
    item = envio.items.first()
    ctx_item = {
        "item_hbl":            (item.hbl if item else ""),
        "item_descripcion":    (item.descripcion if item else ""),
        "item_cantidad":       (item.cantidad if item else ""),
        "item_peso":           (item.peso if item else ""),
        "item_precio":         (item.precio if item else ""),
        "item_valor_aduanal":  (item.valor_aduanal if item else ""),
        "item_tipo":           (item.tipo if item else ""),
    }

    if request.method == 'POST':
        for c in ['remitente','destinatario','modalidad','servicio',
                  'item_hbl','item_descripcion','item_cantidad','item_peso',
                  'item_precio','item_valor_aduanal','item_tipo']:
            valores[c] = _clean(request.POST.get(c))

        # Validaciones mínimas
        if not valores['remitente']:
            errores['remitente'] = _("El remitente es obligatorio.")
        if not valores['destinatario']:
            errores['destinatario'] = _("El destinatario es obligatorio.")

        if not errores:
            # Actualizar envío
            envio.remitente_id    = valores['remitente']
            envio.destinatario_id = valores['destinatario']
            envio.modalidad       = valores['modalidad'] or None
            envio.servicio        = valores['servicio'] or None
            envio.save()

            # Upsert/Eliminar primer ítem
            hay_item = _any([
                valores['item_hbl'], valores['item_descripcion'],
                valores['item_cantidad'], valores['item_peso'],
                valores['item_precio'], valores['item_valor_aduanal'],
                valores['item_tipo']
            ])

            if hay_item:
                # parseo con defaults
                try: cantidad = int(valores['item_cantidad'] or (item.cantidad if item else 1) or 1)
                except Exception: cantidad = 1
                try: peso = float(valores['item_peso'] or (item.peso if item else 0) or 0)
                except Exception: peso = 0
                try: precio = float(valores['item_precio'] or (item.precio if item else 0) or 0)
                except Exception: precio = 0
                try: vaduanal = float(valores['item_valor_aduanal'] or (item.valor_aduanal if item else 0) or 0)
                except Exception: vaduanal = 0

                if item:
                    item.hbl           = valores['item_hbl'] or item.hbl or ""
                    item.descripcion   = valores['item_descripcion'] or item.descripcion or ""
                    item.cantidad      = cantidad
                    item.peso          = peso
                    item.precio        = precio
                    item.valor_aduanal = vaduanal
                    item.tipo          = valores['item_tipo'] or item.tipo or None
                    item.save()
                else:
                    ItemEnvio.objects.create(
                        envio=envio,
                        hbl=valores['item_hbl'] or "",
                        descripcion=valores['item_descripcion'] or "",
                        cantidad=cantidad,
                        peso=peso,
                        precio=precio,
                        valor_aduanal=vaduanal,
                        tipo=valores['item_tipo'] or None,
                        envio_manejo=None,
                    )
            else:
                if item:
                    item.delete()

            messages.success(request, _("Cambios guardados correctamente."))
            return redirect('backoffice:listar_envios')
        else:
            messages.error(request, _("Por favor corrige los errores."))

    # GET o POST con errores → render con precarga
    context = {
        'envio': envio,
        'remitentes': remitentes,
        'destinatarios': destinatarios,
        'errores': errores,
        'valores': valores,
        'item': item,  # por si lo necesitas
    }
    context.update(ctx_item)  # inyectamos variables seguras
    return render(request, 'backoffice/envios/editar_envio.html', context)

@manager_required
@login_required
def eliminar_envio(request, envio_id):
    envio = get_object_or_404(Envio, pk=envio_id)

    info = {
        'remitente': getattr(envio.remitente, 'nombre_apellido', None),
        'destinatario': getattr(envio.destinatario, 'nombre_completo', None),
    }

    if request.method == 'POST':
        confirm = _clean(request.POST.get('confirm')).upper()
        if confirm == 'ELIMINAR':
            envio.delete()
            messages.success(request, _("Envío eliminado correctamente."))
            return redirect('backoffice:listar_envios')
        messages.error(request, _("Debes escribir 'ELIMINAR' para confirmar la eliminación."))

    return render(request, 'backoffice/envios/eliminar_envio.html', {
        'envio': envio,
        'info': info,
    })

# ====================================================================================== #
# ----------------------------------------- REMITENTES --------------------------------- #
# ====================================================================================== #

@manager_required
@login_required
def listar_remitentes(request):
    query = request.GET.get('q', '')
    qs = Remitente.objects.all()

    if query:
        qs = qs.filter(
            Q(nombre_apellido__icontains=query) |
            Q(telefono__icontains=query)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/remitentes/listar_remitentes.html', {
        'page_obj': page_obj,
        'query': query,
    })


@manager_required
@login_required
def crear_remitente(request):
    if request.method == 'POST':
        nombre_apellido = request.POST.get('nombre_apellido')
        id_documento = request.POST.get('id_documento')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')

        Remitente.objects.create(
            nombre_apellido=nombre_apellido,
            id_documento=id_documento,
            telefono=telefono,
            direccion=direccion
        )
        return redirect('backoffice:listar_remitentes')

    return render(request, 'backoffice/remitentes/crear_remitente.html')


@manager_required
@login_required
def editar_remitente(request, remitente_id):
    remitente = get_object_or_404(Remitente, id=remitente_id)

    if request.method == 'POST':
        remitente.nombre_apellido = request.POST.get('nombre_apellido')
        remitente.id_documento = request.POST.get('id_documento')
        remitente.telefono = request.POST.get('telefono')
        remitente.direccion = request.POST.get('direccion')
        remitente.save()
        return redirect('backoffice:listar_remitentes')

    return render(request, 'backoffice/remitentes/editar_remitente.html', {
        'remitente': remitente
    })


@manager_required
@login_required
def eliminar_remitente(request, remitente_id):
    remitente = get_object_or_404(Remitente, id=remitente_id)

    if request.method == 'POST':
        remitente.delete()
        return redirect('backoffice:listar_remitentes')

    return render(request, 'backoffice/remitentes/eliminar_remitente.html', {
        'remitente': remitente
    })


# ====================================================================================== #
# ------------------------------------- DESTINATARIOS ---------------------------------- #
# ====================================================================================== #

@manager_required
@login_required
def listar_destinatarios(request):
    query = request.GET.get('q', '')
    qs = Destinatario.objects.all()

    if query:
        qs = qs.filter(
            Q(primer_nombre__icontains=query) |
            Q(primer_apellido__icontains=query) |
            Q(telefono__icontains=query)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/destinatarios/listar_destinatarios.html', {
        'page_obj': page_obj,
        'query': query,
    })

def _clean(s): 
    return (s or "").strip()

def _first(*vals):
    for v in vals:
        if v is not None and str(v).strip() != "":
            return v
    return None

@manager_required
@login_required
def crear_destinatario(request):
    errores, valores = {}, {}

    if request.method == 'POST':
        campos = ["primer_nombre","segundo_nombre","primer_apellido","segundo_apellido",
                  "ci","telefono","telefono_adicional","calle","numero"]
        for c in campos:
            valores[c] = _clean(request.POST.get(c))

        # Validación mínima
        if not valores["primer_nombre"]:
            errores["primer_nombre"] = _("El primer nombre es obligatorio.")
        if not valores["primer_apellido"]:
            errores["primer_apellido"] = _("El primer apellido es obligatorio.")
        if not valores["telefono"]:
            errores["telefono"] = _("El teléfono es obligatorio.")
        if not valores["calle"]:
            errores["calle"] = _("La calle es obligatoria.")

        if not errores:
            d = Destinatario(
                primer_nombre=valores["primer_nombre"],
                segundo_nombre=valores["segundo_nombre"] or None,
                primer_apellido=valores["primer_apellido"],
                segundo_apellido=valores["segundo_apellido"] or None,
                ci=valores["ci"] or None,
                telefono=valores["telefono"],
                telefono_adicional=valores["telefono_adicional"] or None,
                calle=valores["calle"],
                numero=valores["numero"] or None,
            )
            d.save()
            messages.success(request, _("Destinatario creado correctamente."))
            return redirect('backoffice:listar_destinatarios')
        else:
            messages.error(request, _("Por favor corrige los errores."))

    return render(request, 'backoffice/destinatarios/crear_destinatario.html', {
        "errores": errores,
        "valores": valores,
    })


@manager_required
@login_required
def editar_destinatario(request, destinatario_id):
    destinatario = get_object_or_404(Destinatario, id=destinatario_id)
    errores, valores = {}, {}

    if request.method == 'POST':
        campos = ["primer_nombre","segundo_nombre","primer_apellido","segundo_apellido",
                  "ci","telefono","telefono_adicional","calle","numero"]
        for c in campos:
            valores[c] = _clean(request.POST.get(c))

        if not valores["primer_nombre"]:
            errores["primer_nombre"] = _("El primer nombre es obligatorio.")
        if not valores["primer_apellido"]:
            errores["primer_apellido"] = _("El primer apellido es obligatorio.")
        if not valores["telefono"]:
            errores["telefono"] = _("El teléfono es obligatorio.")
        if not valores["calle"]:
            errores["calle"] = _("La calle es obligatoria.")

        if not errores:
            destinatario.primer_nombre = valores["primer_nombre"]
            destinatario.segundo_nombre = valores["segundo_nombre"] or None
            destinatario.primer_apellido = valores["primer_apellido"]
            destinatario.segundo_apellido = valores["segundo_apellido"] or None
            destinatario.ci = valores["ci"] or None
            destinatario.telefono = valores["telefono"]
            destinatario.telefono_adicional = valores["telefono_adicional"] or None
            destinatario.calle = valores["calle"]
            destinatario.numero = valores["numero"] or None
            destinatario.save()
            messages.success(request, _("Cambios guardados correctamente."))
            return redirect('backoffice:listar_destinatarios')
        else:
            messages.error(request, _("Por favor corrige los errores."))

    return render(request, 'backoffice/destinatarios/editar_destinatario.html', {
        "destinatario": destinatario,
        "errores": errores,
        "valores": valores,
    })


@manager_required
@login_required
def eliminar_destinatario(request, destinatario_id):
    destinatario = get_object_or_404(Destinatario, id=destinatario_id)

    # Normalizamos nombre y teléfono para mostrar en la tarjeta
    nombre_completo = " ".join([p for p in [
        _first(getattr(destinatario, "primer_nombre", None)),
        _first(getattr(destinatario, "segundo_nombre", None)),
        _first(getattr(destinatario, "primer_apellido", None),
               getattr(destinatario, "apellidos", None)),
        _first(getattr(destinatario, "segundo_apellido", None)),
    ] if _first(p)])

    telefono = _first(getattr(destinatario, "telefono", None),
                      getattr(destinatario, "telefono_principal", None),
                      getattr(destinatario, "movil", None))

    if request.method == 'POST':
        confirm = _clean(request.POST.get('confirm')).upper()
        if confirm == 'ELIMINAR':
            destinatario.delete()
            messages.success(request, _("Destinatario eliminado correctamente."))
            return redirect('backoffice:listar_destinatarios')
        messages.error(request, _("Debes escribir 'ELIMINAR' para confirmar la eliminación."))

    return render(request, 'backoffice/destinatarios/eliminar_destinatario.html', {
        "destinatario": destinatario,
        "info": {
            "nombre_completo": nombre_completo,
            "telefono": telefono,
        }
    })

# ====================================================================================== #
# ------------------------------ ITEMS DE ENVÍO ---------------------------------------- #
# ====================================================================================== #

@manager_required
@login_required
def listar_items_envio(request):
    query = request.GET.get('q', '')
    qs = ItemEnvio.objects.select_related('envio').all()

    if query:
        qs = qs.filter(
            Q(descripcion__icontains=query) |
            Q(envio__id__icontains=query)
        )

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'backoffice/items_envio/listar_items_envio.html', {
        'page_obj': page_obj,
        'query': query,
    })

@manager_required
@login_required
def crear_item_envio(request):
    errores, valores = {}, {}
    envios = Envio.objects.select_related('remitente','destinatario').order_by('-id')

    if request.method == 'POST':
        for c in ['envio','hbl','descripcion','cantidad','peso','precio','valor_aduanal','tipo','envio_manejo']:
            valores[c] = _clean(request.POST.get(c))

        if not valores['envio']:
            errores['envio'] = _("El envío es obligatorio.")
        if not valores['descripcion']:
            errores['descripcion'] = _("La descripción es obligatoria.")

        if not errores:
            try:
                item = ItemEnvio.objects.create(
                    envio_id=int(valores['envio']),
                    hbl=valores['hbl'] or "",
                    descripcion=valores['descripcion'],
                    cantidad=int(valores['cantidad'] or 1),
                    peso=float(valores['peso'] or 0),
                    precio=float(valores['precio'] or 0),
                    valor_aduanal=float(valores['valor_aduanal'] or 0),
                    tipo=valores['tipo'] or None,
                    envio_manejo=valores['envio_manejo'] or None,
                )
                messages.success(request, _("Ítem creado (#{id}).").format(id=item.id))
                return redirect('backoffice:listar_items_envio')
            except Exception as e:
                errores['__all__'] = _("No se pudo crear el ítem.")
                messages.error(request, errores['__all__'])

    return render(request, 'backoffice/items_envio/crear_item_envio.html', {
        'envios': envios,
        'errores': errores,
        'valores': valores,
        'error_global': errores.get('__all__'),
    })


@manager_required
@login_required
def editar_item_envio(request, item_id):
    item = get_object_or_404(ItemEnvio, id=item_id)
    envios = Envio.objects.select_related('remitente','destinatario').order_by('-id')

    if request.method == 'POST':
        envio_id = _clean(request.POST.get('envio'))
        item.hbl = _clean(request.POST.get('hbl')) or ""
        item.descripcion = _clean(request.POST.get('descripcion')) or item.descripcion
        item.cantidad = int(_clean(request.POST.get('cantidad')) or item.cantidad or 1)
        item.peso = float(_clean(request.POST.get('peso')) or item.peso or 0)
        item.precio = float(_clean(request.POST.get('precio')) or item.precio or 0)
        item.valor_aduanal = float(_clean(request.POST.get('valor_aduanal')) or item.valor_aduanal or 0)
        item.tipo = _clean(request.POST.get('tipo')) or None
        item.envio_manejo = _clean(request.POST.get('envio_manejo')) or None
        if envio_id:
            item.envio_id = int(envio_id)
        item.save()
        messages.success(request, _("Cambios guardados."))
        return redirect('backoffice:listar_items_envio')

    return render(request, 'backoffice/items_envio/editar_item_envio.html', {
        'item': item,
        'envios': envios,
    })


@manager_required
@login_required
def eliminar_item_envio(request, item_id):
    item = get_object_or_404(ItemEnvio, id=item_id)

    if request.method == 'POST':
        confirm = _clean(request.POST.get('confirm')).upper()
        if confirm == 'ELIMINAR':
            item.delete()
            messages.success(request, _("Ítem eliminado."))
            return redirect('backoffice:listar_items_envio')
        messages.error(request, _("Debes escribir 'ELIMINAR' para confirmar."))

    return render(request, 'backoffice/items_envio/eliminar_item_envio.html', {
        'item': item
    })

# ─────────────────────────────────────
#   ENVÍO A BOOKING DISTAL (BookingRQ)
# ─────────────────────────────────────

# -*- coding: utf-8 -*-
"""
Backoffice - Distal Booking (HotelRes / ResStatus=Book) + Previews

Incluye:
- enviar_booking_distal (POST a Distal HTTP)
- generar_xml_reserva_distal (GuestCounts + AgeQualifyingCode, ResIDs 14/16, Gender/NamePrefix)
- vista_preview_booking_distal (muestra XML generado)
- vista_preview_voucher_distal (render del voucher para Distal)

Notas:
- Endpoint HTTP (no HTTPS): http://api.1way2italy.it/Service/Production/v10/OtaService/HotelRes
- No enviar datos de tarjeta reales por HTTP.
"""

import time
from datetime import date
from xml.dom import minidom
from xml.etree import ElementTree as ET

import requests
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import Reserva, Pasajero  # ajusta a tu estructura real

# ============================
# CONSTANTES / CONFIG
# ============================
DISTAL_HOTELRES_URL = "http://api.1way2italy.it/Service/Production/v10/OtaService/HotelRes"
DISTAL_REQUESTOR_ID = "RUTA-US"
DISTAL_PASSWORD = "xxxxxxx"
HTTP_TIMEOUT = 30

OTA_NS = "http://www.opentravel.org/OTA/2003/05"
NS = {"ota": OTA_NS}


# ============================
# AUXILIARES
# ============================
def _iso(d):
    return d.isoformat() if hasattr(d, "isoformat") else str(d)

def _age_on(checkin: date, birth_iso: str | None, edad_fallback: int | None) -> int:
    if birth_iso:
        b = date.fromisoformat(birth_iso)
        return max(0, checkin.year - b.year - ((checkin.month, checkin.day) < (b.month, b.day)))
    if edad_fallback is not None:
        return int(edad_fallback)
    raise ValueError("Falta fecha_nacimiento o edad para calcular Age en GuestCounts.")

def _birthdate_from_age(checkin: date, edad: int) -> str:
    # fecha “estable” para evitar bordes (1 de julio)
    return f"{checkin.year - int(edad)}-07-01"

def _normaliza_nombre(p):
    nombre = (getattr(p, "nombre", "") or "").strip()
    apellidos = (getattr(p, "apellidos", "") or "").strip()
    if nombre and apellidos:
        return nombre.split()[0], apellidos.split()[-1]
    parts = nombre.split()
    if len(parts) >= 2:
        return parts[0], parts[-1]
    return (parts[0] if parts else "GUEST"), (parts[-1] if parts else "GUEST")

def _get_birthdate_or_raise(p, checkin: date) -> str:
    fn = getattr(p, "fecha_nacimiento", None)
    if fn:
        return _iso(fn)
    edad = getattr(p, "edad", None)
    if edad is None:
        raise ValueError(
            f"El pasajero '{getattr(p, 'nombre', 'SIN NOMBRE')}' no tiene 'fecha_nacimiento' ni 'edad'."
        )
    return _birthdate_from_age(checkin, int(edad))

def _prefix_and_gender(p):
    sexo = (getattr(p, "genero", None) or getattr(p, "sexo", "") or "").lower()
    if sexo in ("m", "male", "h", "masculino"):
        return "MR", "Male"
    if sexo in ("f", "female", "fem", "femenino"):
        return "MRS", "Female"
    return "MR", "Male"

def _guardar_meta_distal(reserva, xml_req: str, xml_rs: str, supplier_id: str | None = None) -> None:
    """Guarda request/response/supplier_id si el modelo tiene campos para ello (no bloquea flujo si falla)."""
    try:
        if hasattr(reserva, "xml_solicitud_proveedor"):
            reserva.xml_solicitud_proveedor = xml_req
        if hasattr(reserva, "xml_respuesta_proveedor"):
            reserva.xml_respuesta_proveedor = xml_rs
        if supplier_id and hasattr(reserva, "codigo_confirmacion_proveedor"):
            reserva.codigo_confirmacion_proveedor = supplier_id
        if hasattr(reserva, "metadatos"):
            meta = reserva.metadatos or {}
            distal = meta.get("distal", {})
            distal.update({
                "hotelres_request_xml": xml_req,
                "hotelres_response_xml": xml_rs,
                "supplier_reservation_id": supplier_id,
            })
            meta["distal"] = distal
            reserva.metadatos = meta
        reserva.save()
    except Exception:
        pass


# ============================
# GENERACIÓN XML BOOKING
# ============================
def generar_xml_reserva_distal(reserva: Reserva) -> str:
    """
    Requisitos:
      - reserva.tipo == 'hoteles' y reserva.hotel_importado presente
      - HabitacionReserva con booking_code y fechas_viaje = 'YYYY-MM-DD - YYYY-MM-DD'
      - Cada pasajero con fecha_nacimiento o edad
      - En booking: GuestCounts con Age (+ AgeQualifyingCode)
    """
    if reserva.tipo != 'hoteles' or not getattr(reserva, "hotel_importado", None):
        raise ValueError("Reserva no válida para Distal (tipo 'hoteles' y hotel_importado requerido).")

    habitaciones = reserva.habitaciones_reserva.all()
    if not habitaciones.exists():
        raise ValueError("No hay habitaciones asociadas.")

    chain_code = 'DISTALCU'
    hotel_code = reserva.hotel_importado.hotel_code

    # Referencias cliente (enviamos 14 y 16 para máxima compatibilidad)
    # 14: booking reference del cliente
    # 16: customer reference (obligatoria)
    ref_16 = getattr(reserva, "referencia_cliente", None)
    if not ref_16:
        ref_16 = f"RUTA-{date.today().strftime('%Y%m%d')}-{reserva.id}"
        if hasattr(reserva, "referencia_cliente"):
            reserva.referencia_cliente = ref_16
            try:
                reserva.save(update_fields=["referencia_cliente"])
            except Exception:
                pass
    ref_14 = getattr(reserva, "numero_confirmacion", None) or f"API-{reserva.id:05d}"

    # Check-in global (mínimo entre las habitaciones)
    fechas_inicio = [h.fechas_viaje.split(' - ')[0] for h in habitaciones if h.fechas_viaje]
    checkin_global = min(date.fromisoformat(fi) for fi in fechas_inicio) if fechas_inicio else date.today()

    # Construcción de RoomStays con RPHs y GuestCounts (EDADES + AgeQualifyingCode)
    rph_counter = 1
    rph_map: list[tuple[int, list[str], list[Pasajero]]] = []
    room_stays_xml_parts = []

    for habitacion in habitaciones:
        try:
            fecha_inicio, fecha_fin = habitacion.fechas_viaje.split(' - ')
        except Exception as e:
            raise ValueError(f"No se pudo obtener fechas de la habitación {habitacion.id}: {e}")

        if not habitacion.booking_code:
            raise ValueError(f"La habitación {habitacion.id} no tiene booking_code.")

        pasajeros_h = list(habitacion.pasajeros.all())
        rphs = []
        ages_xml = []

        for p in pasajeros_h:
            rphs.append(str(rph_counter))
            rph_counter += 1

            # calcular edad real al check-in de la HABITACIÓN
            birth = getattr(p, "fecha_nacimiento", None)
            birth_iso = _iso(birth) if birth else None
            edad_fallback = getattr(p, "edad", None)
            age_val = _age_on(date.fromisoformat(fecha_inicio), birth_iso, edad_fallback)

            # AgeQualifyingCode: 10=adulto, 8=niño (umbral 12 años; ajusta si tu negocio usa otro)
            aqc = "8" if age_val < 12 else "10"
            ages_xml.append(f'<GuestCount Age="{age_val}" AgeQualifyingCode="{aqc}" Count="1"/>')

        rphs_xml = ''.join(f'<ResGuestRPH>{r}</ResGuestRPH>' for r in rphs)
        guestcounts_xml = ''.join(ages_xml)

        room_stays_xml_parts.append(f"""
        <RoomStay>
          <RoomRates>
            <RoomRate BookingCode="{habitacion.booking_code}">
              <Total AmountAfterTax="0" CurrencyCode="EUR"/>
            </RoomRate>
          </RoomRates>
          <TimeSpan Start="{fecha_inicio}" End="{fecha_fin}"/>
          <BasicPropertyInfo ChainCode="{chain_code}" HotelCode="{hotel_code}"/>
          <GuestCounts IsPerRoom="true">
            {guestcounts_xml}
          </GuestCounts>
          <ResGuestRPHs>
            {rphs_xml}
          </ResGuestRPHs>
        </RoomStay>
        """.strip())

        rph_map.append((habitacion.id, rphs, pasajeros_h))

    # Pasajeros (Profiles/Customer con BirthDate + NamePrefix + Gender)
    pasajeros_xml_parts = []
    for _, rphs, pasajeros_h in rph_map:
        for p, rph in zip(pasajeros_h, rphs):
            given, sur = _normaliza_nombre(p)
            birth_date = _get_birthdate_or_raise(p, checkin_global)
            prefix, gender = _prefix_and_gender(p)
            telefono = getattr(p, "telefono", None) or "0000000000"
            email = getattr(p, "email", None) or "booking@rutamultiservice.com"
            direccion = getattr(p, "direccion", None) or "Dirección Genérica"
            ciudad = getattr(p, "ciudad", None) or "Havana"
            postal = getattr(p, "codigo_postal", None) or "00000"
            country_code = getattr(p, "pais_codigo", None) or "CU"

            # CountryAccessCode: si el país es CU usamos 53, si no 001
            country_access = "53" if country_code == "CU" else "001"
            country_name_txt = "CUBA" if country_code == "CU" else "COUNTRY"

            # StateProv: omitir si vacío
            state = getattr(p, "estado", None) or getattr(p, "provincia", None) or ""
            state_line = f"<StateProv>{state}</StateProv>" if state else ""

            pasajeros_xml_parts.append(f"""
        <ResGuest ResGuestRPH="{rph}">
          <Profiles>
            <ProfileInfo>
              <Profile>
                <Customer Gender="{gender}" BirthDate="{birth_date}">
                  <PersonName>
                    <NamePrefix>{prefix}</NamePrefix>
                    <GivenName>{given}</GivenName>
                    <Surname>{sur}</Surname>
                  </PersonName>
                  <Telephone CountryAccessCode="{country_access}" PhoneNumber="{telefono}" PhoneTechType="5"/>
                  <Email>{email}</Email>
                  <Address>
                    <AddressLine>{direccion}</AddressLine>
                    <CityName>{ciudad}</CityName>
                    <PostalCode>{postal}</PostalCode>
                    {state_line}
                    <CountryName Code="{country_code}">{country_name_txt}</CountryName>
                  </Address>
                </Customer>
              </Profile>
            </ProfileInfo>
          </Profiles>
        </ResGuest>
            """.strip())

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OTA_HotelResRQ xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                Target="Production" ResStatus="Book" MarketCountryCode="us"
                PrimaryLangID="en"
                xmlns="{OTA_NS}">
  <POS>
    <Source>
      <RequestorID ID="{DISTAL_REQUESTOR_ID}" MessagePassword="{DISTAL_PASSWORD}"/>
    </Source>
  </POS>

  <HotelReservations>
    <HotelReservation>
      <RoomStays>
        {' '.join(room_stays_xml_parts)}
      </RoomStays>

      <ResGuests>
        {' '.join(pasajeros_xml_parts)}
      </ResGuests>

      <ResGlobalInfo>
        <HotelReservationIDs>
          <!-- Enviamos ambas referencias para máxima compatibilidad -->
          <HotelReservationID ResID_Type="14" ResID_Value="{ref_14}"/>
          <HotelReservationID ResID_Type="16" ResID_Value="{ref_16}"/>
        </HotelReservationIDs>
      </ResGlobalInfo>
    </HotelReservation>
  </HotelReservations>
</OTA_HotelResRQ>"""

    return minidom.parseString(xml).toprettyxml(indent="  ")


# ============================
# ENVÍO Y PARSEO DE RESPUESTA
# ============================
def enviar_booking_api(xml_data: str, url: str = DISTAL_HOTELRES_URL):
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    resp = requests.post(url, data=xml_data.encode("utf-8"), headers=headers, timeout=HTTP_TIMEOUT)
    print("📥 Respuesta cruda de Distal:\n", resp.text)

    if resp.status_code != 200:
        return None, False, f"{resp.status_code} {resp.reason} for url: {url}", resp.text

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        return None, False, f"XML mal formado: {e}", resp.text

    # EchoToken para soporte
    echo_token = root.get("EchoToken") or ""
    if echo_token:
        print(f"🔎 EchoToken de Distal: {echo_token}")

    # Errores
    error_node = root.find(".//ota:Error", NS) or root.find(".//Error")
    if error_node is not None:
        code = error_node.get("Code", "") if hasattr(error_node, "get") else ""
        msg  = error_node.get("ShortText", "") if hasattr(error_node, "get") else (error_node.text or "")
        return None, False, f"Distal Error {code}: {msg}{f' [EchoToken={echo_token}]' if echo_token else ''}", resp.text

    # Success (a veces vacío): presencia del nodo cuenta como True
    success_el = root.find(".//ota:Success", NS) or root.find(".//Success")
    success_flag = success_el is not None

    # Booking ID del proveedor (no nuestros 14/16 si los reflejan)
    booking_id = None
    for el in root.findall(".//ota:HotelReservationID", NS) + root.findall(".//HotelReservationID"):
        rid = el.get("ResID_Value") if hasattr(el, "get") else None
        rtype = el.get("ResID_Type") if hasattr(el, "get") else None
        if rid and (rtype is None or rtype not in ("14", "16")):
            booking_id = rid
            break

    if not booking_id:
        el = root.find(".//ota:BookingID", NS) or root.find(".//BookingID")
        if el is not None and (el.text or "").strip():
            booking_id = el.text.strip()

    if not booking_id:
        el = root.find(".//ota:UniqueID", NS) or root.find(".//UniqueID")
        if el is not None and el.get("ID"):
            booking_id = el.get("ID")

    if (success_flag and booking_id) or booking_id:
        return booking_id, True, None, resp.text

    return None, False, "No se encontró BookingID/UniqueID/HotelReservationID del proveedor", resp.text


# ============================
# VISTAS
# ============================
@login_required
@manager_required
@transaction.atomic
def enviar_booking_distal(request, reserva_id):
    print("🔄 Iniciando proceso de envío de booking a Distal...")
    reserva = get_object_or_404(Reserva, id=reserva_id)
    print(f"✅ Reserva encontrada: ID {reserva.id}")

    try:
        print("🧾 Generando XML de la reserva (GuestCounts + AQC + ResID 14/16 + Gender/Prefix)...")
        xml_data = generar_xml_reserva_distal(reserva)
        print("📦 XML generado para enviar a Distal:\n", xml_data)

        max_intentos = 3
        intento = 1
        booking_id = None
        success = False
        error_message = None
        raw_response = ""

        while intento <= max_intentos:
            print(f"🌍 Intento #{intento}: POST → {DISTAL_HOTELRES_URL}")
            try:
                booking_id, success, error_message, raw_response = enviar_booking_api(xml_data, DISTAL_HOTELRES_URL)
                if success:
                    print("✅ Solicitud procesada con éxito por Distal.")
                    break
                if error_message and any(x in error_message for x in (" 502 ", " 503 ", "Error 999")):
                    print(f"🔁 {error_message}. Reintentando en 2s…")
                    time.sleep(2)
                    intento += 1
                    continue
                break
            except requests.RequestException as e:
                print(f"💥 Excepción de red: {e}. Reintentando en 2s…")
                time.sleep(2)
                intento += 1

        print("📥 Resultado API:",
              f"\n   🔑 Booking ID proveedor: {booking_id}",
              f"\n   ✅ Éxito: {success}",
              f"\n   ❌ Error: {error_message}")

        # Auditoría
        try:
            _guardar_meta_distal(reserva, xml_data, raw_response, booking_id)
        except Exception:
            pass

        if success:
            if booking_id and hasattr(reserva, "numero_confirmacion"):
                reserva.numero_confirmacion = booking_id
            reserva.estatus = 'confirmada'
            reserva.save()
            messages.success(request, f"✅ Reserva confirmada en Distal{f' (ID: {booking_id})' if booking_id else ''}")
        else:
            messages.error(request, f"❌ Error al confirmar booking: {error_message or 'Respuesta sin éxito ni error explícito.'}")

    except Exception as e:
        print("💥 Excepción inesperada durante el proceso:", e)
        messages.error(request, f"⚠️ Error inesperado: {e}")

    print("✅ Finalizado proceso de envío de booking.\n" + "-"*60)
    return redirect('backoffice:editar_reserva', reserva_id=reserva.id)


@login_required
def vista_preview_booking_distal(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    try:
        xml_generado = generar_xml_reserva_distal(reserva)
    except Exception as e:
        xml_generado = f"⚠️ ERROR al generar XML: {str(e)}"

    return render(request, 'backoffice/preview_booking_distal.html', {
        'reserva': reserva,
        'xml': xml_generado
    })


@login_required
@manager_required
def vista_preview_voucher_distal(request, reserva_id):
    """
    Render sencillo del voucher para reservas Distal.
    Puedes ajustar el template/variables según tu diseño.
    """
    reserva = get_object_or_404(Reserva, id=reserva_id)
    habitaciones = reserva.habitaciones_reserva.all()
    pasajeros = Pasajero.objects.filter(habitacion__reserva=reserva)

    # Datos del hotel (local o importado)
    if getattr(reserva, "hotel", None):
        hotel_nombre = getattr(reserva.hotel, 'hotel_nombre', None) or "No disponible"
        hotel_direccion = getattr(reserva.hotel, 'direccion', None) or ""
        hotel_telefono = getattr(reserva.hotel, 'telefono', None) or ""
    else:
        imp = reserva.hotel_importado
        hotel_nombre = getattr(imp, 'hotel_name', 'No disponible')
        hotel_direccion = getattr(imp, 'address', '')
        hotel_telefono = getattr(imp, 'email', '')

    # Fechas checkin/checkout
    fechas_checkin = fechas_checkout = ""
    if habitaciones.exists():
        rangos = [h.fechas_viaje for h in habitaciones if h.fechas_viaje]
        if rangos:
            inicio = min(r.split(' - ')[0] for r in rangos)
            fin = max(r.split(' - ')[1] for r in rangos)
            fechas_checkin = f"{inicio} a las 4:00 PM"
            fechas_checkout = f"{fin} a las 12:00 M"

    return render(
        request,
        'backoffice/emails/voucher_hotel_distal.html',
        {
            'reserva': reserva,
            'habitaciones': habitaciones,
            'pasajeros': pasajeros,
            'fechas_checkin': fechas_checkin,
            'fechas_checkout': fechas_checkout,
            'hotel_nombre': hotel_nombre,
            'hotel_direccion': hotel_direccion,
            'hotel_telefono': hotel_telefono,
        }
    )

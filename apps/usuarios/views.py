# apps/usuarios/views.py

# ────────────────────────────
#  Librerías estándar
# ────────────────────────────
from datetime import datetime, timedelta, date
from decimal import Decimal
from collections import defaultdict, Counter

# ────────────────────────────
#  Django imports
# ────────────────────────────
from django.contrib import messages
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Avg, Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
# Paginación para Alerta de Pago
from django.core.paginator import Paginator
from django.db import transaction

# ────────────────────────────
#  App imports
# ────────────────────────────
from apps.usuarios.decorators import manager_required
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

# ────────────────────────────
#  Backoffice imports
# ────────────────────────────
from apps.backoffice.models import (
    Hotel, PlanAlimenticio, Proveedor, PoloTuristico, Habitacion, 
    TipoFee, Oferta, HotelFacility, HotelSetting, CadenaHotelera, 
    Reserva, Pasajero
)
from apps.backoffice.funciones_externas import (contar_reservas_por_mes)




@login_required
def check_session_status(request):
    # Si el usuario está autenticado, devuelve "active", de lo contrario "inactive"
    return JsonResponse({'status': 'active'})

@login_required
def home(request):
    # Forzar cierre de sesión al iniciar el servidor (solo para desarrollo)
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'usuarios/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_manager:
                return redirect('dashboard')
            else:
                return redirect('booking:user_dashboard')
        else:
            # Add an error message if authentication fails
            messages.error(request, 'Error de Usuario y contraseña.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'usuarios/login.html', {'form': form})

@login_required
def index(request):
    return render(request, 'renta_hoteles/index.html')

@login_required
def logout_view(request):
    logout(request)    
    return redirect('login')

@login_required
@manager_required
def dashboard(request):
    # Obtener el rango seleccionado desde la solicitud GET
    rango = request.GET.get('range', 'mes')

    # Definir las fechas iniciales y finales basadas en el rango seleccionado
    hoy = timezone.now().date()
    if rango == 'hoy':
        fecha_inicio = hoy
        selected_range = 'Hoy'
    elif rango == '7_dias':
        fecha_inicio = hoy - timedelta(days=7)
        selected_range = 'Últimos 7 días'
    elif rango == '30_dias':
        fecha_inicio = hoy - timedelta(days=30)
        selected_range = 'Últimos 30 días'
    elif rango == 'mes':
        fecha_inicio = hoy.replace(day=1)
        selected_range = 'Este mes'
    elif rango == 'ano':
        fecha_inicio = hoy.replace(month=1, day=1)
        selected_range = 'Este año'
    else:
        fecha_inicio = hoy.replace(day=1)
        selected_range = 'Este mes'

    # Filtrar las reservas según la fecha
    reservas = Reserva.objects.filter(fecha_reserva__gte=fecha_inicio)
    total_reservas = reservas.count()
    
    hoteles = Hotel.objects.all()
    usuarios = CustomUser.objects.all()
    ultimos_usuarios = CustomUser.objects.order_by('-date_joined')[:5]
    

    # Los Ingresos Totales y Gastos Totales
    ingresos_totales = reservas\
        .filter(cobrada=True, pagada=True)\
        .aggregate(total_ingresos=Sum('precio_total'))['total_ingresos'] or 0.0

    gastos_totales = reservas\
        .filter(cobrada=True, pagada=True)\
        .aggregate(total_gastos=Sum('costo_total'))['total_gastos'] or 0.0

    
    ingresos_totales = float(ingresos_totales)
    gastos_totales = float(gastos_totales)
    
    reservas_activas = [reserva for reserva in reservas if reserva.esta_activa()]

    # Generar datos para los gráficos
    labels_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    datos_reservas_mensuales = contar_reservas_por_mes(reservas)
    datos_ingresos = [float(calcular_ingresos_mes(mes, reservas)) for mes in range(1, 13)]
    datos_gastos = [float(calcular_gastos_mes(mes, reservas)) for mes in range(1, 13)]
    
    # Genera dos listas con las Reservas que tienen ALERTAS de cobro y de pago 
    reservas_alerta_pago, reservas_alerta_cobro = obtener_reservas_alerta(Reserva.objects.all())
    
    # Calcula el tiempo Promedio de Reservas
    tiempo_promedio_reserva = calcular_tiempo_promedio_reserva()
    
    # Crea un top 5 de las agencias que mas venden
    top_agencias = top_5_agencias_mas_reservas()
    
    # Crea un top 5 de los hoteles mas vendidos
    top_hoteles = top_5_hoteles_mas_reservados()

    # ----------------------------------------------------------------------
    # AÑADIR: Determinar si cada submenú (Booking, Backoffice, EnDesarrollo)
    # debe iniciar abierto según la URL actual
    url_name = request.resolver_match.url_name

    # 1. Booking: Ejemplo, si la URL actual es 'user_dashboard' o 'hotel_dashboard'
    booking_urls = ['user_dashboard', 'hotel_dashboard']
    booking_open = (url_name in booking_urls)

    # 2. Backoffice: Ajusta con los nombres reales de tus rutas
    backoffice_urls = [
        'dashboard', 'listar_reservas', 'listar_usuarios',
        'listar_ofertas_especiales', 'listar_proveedores', 'listar_clientes'
    ]
    backoffice_open = (url_name in backoffice_urls)

    # 3. EnDesarrollo
    en_desarrollo_urls = ['en_desarrollo', 'en_mantenimiento']
    en_desarrollo_open = (url_name in en_desarrollo_urls)
    # ----------------------------------------------------------------------
    
    # Genera dos listas con las Reservas que tienen ALERTAS de cobro y de pago 
    reservas_alerta_pago, reservas_alerta_cobro = obtener_reservas_alerta(Reserva.objects.all())

    pago_paginator = Paginator(reservas_alerta_pago, 5)
    pago_page = request.GET.get('pago_page')
    pago_paginated = pago_paginator.get_page(pago_page)

    # Paginación para Alerta de Cobro
    cobro_paginator = Paginator(reservas_alerta_cobro, 5)
    cobro_page = request.GET.get('cobro_page')
    cobro_paginated = cobro_paginator.get_page(cobro_page)
    
    ganancia_total = ingresos_totales - gastos_totales

    context = {
        'hoteles': hoteles,
        'reservas': reservas,
        'usuarios': usuarios,
        'ingresos_totales': ingresos_totales,
        'gastos_totales': gastos_totales,
        'reservas_activas': reservas_activas, 
        'labels_meses': labels_meses,
        'datos_reservas_mensuales': datos_reservas_mensuales,
        'datos_ingresos': datos_ingresos,
        'datos_gastos': datos_gastos,
        'reservas_alerta_pago': reservas_alerta_pago,
        'reservas_alerta_cobro': reservas_alerta_cobro,
        'selected_range': selected_range,
        'tiempo_promedio_reserva': tiempo_promedio_reserva,
        'top_agencias': top_agencias,
        'top_hoteles': top_hoteles,
        'ultimos_usuarios': ultimos_usuarios,
        'total_reservas': total_reservas,
        'ganancia_total': ganancia_total,

        # Variables para abrir/cerrar submenús
        'booking_open': booking_open,
        'backoffice_open': backoffice_open,
        'en_desarrollo_open': en_desarrollo_open,
        
        'reservas_alerta_pago': pago_paginated,
        'reservas_alerta_cobro': cobro_paginated,
        'total_alerta_pago': pago_paginator.count,
        'total_alerta_cobro': cobro_paginator.count,
    }
    return render(request, 'usuarios/dashboard.html', context)


# ----------------- FUNCIONES AUXILIARES --------------------

def calcular_ingresos_mes(mes, reservas):
    total = reservas.filter(fecha_reserva__month=mes, cobrada=True, pagada=True).aggregate(
        total=Sum('precio_total')
    )['total'] or 0.0
    return float(total)

def calcular_gastos_mes(mes, reservas):
    total = reservas.filter(fecha_reserva__month=mes, cobrada=True, pagada=True).aggregate(
        total=Sum('costo_total')
    )['total'] or 0.0
    return float(total)

def contar_reservas_por_mes(reservas):
    return [reservas.filter(fecha_reserva__month=mes).count() for mes in range(1, 13)]

def obtener_reservas_alerta(reservas):
    """
    Retorna dos listas: 
    - reservas de hoteles no pagadas con check-in en los próximos 15 días
    - reservas de hoteles no cobradas con check-in en los próximos 15 días
    """
    hoy = timezone.now().date()
    quince_dias_despues = hoy + timedelta(days=15)

    reservas_alerta_pago = []
    reservas_alerta_cobro = []

    for reserva in reservas:
        # Nos enfocamos solo en reservas de hoteles
        if reserva.tipo == 'hoteles':
            for habitacion in reserva.habitaciones_reserva.all():
                fechas_str = getattr(habitacion, 'fechas_viaje', '')
                
                # Esperamos un formato: 'YYYY-MM-DD - YYYY-MM-DD'
                partes = fechas_str.split(' - ')
                if len(partes) != 2:
                    continue  # formato inválido

                try:
                    check_in = datetime.strptime(partes[0], '%Y-%m-%d').date()
                    check_out = datetime.strptime(partes[1], '%Y-%m-%d').date()
                except ValueError:
                    continue  # fecha malformateada

                # Verificamos si está dentro del rango de alerta
                if hoy <= check_in <= quince_dias_despues:
                    if not reserva.pagada:
                        reservas_alerta_pago.append(reserva)
                    if not reserva.cobrada:
                        reservas_alerta_cobro.append(reserva)

    return reservas_alerta_pago, reservas_alerta_cobro

def calcular_tiempo_promedio_reserva():
    reservas = Reserva.objects.all()
    tiempos_reserva = []

    for reserva in reservas:
        for habitacion in reserva.habitaciones_reserva.all():
            try:
                fechas = habitacion.fechas_viaje.split(' - ')
                if len(fechas) != 2:
                    print(f"[WARN] Fechas mal formateadas en habitación {habitacion.id}: {habitacion.fechas_viaje}")
                    continue

                check_in_str = fechas[0].strip()

                # Asegura que la fecha de reserva es datetime
                if not reserva.fecha_reserva or not isinstance(reserva.fecha_reserva, datetime):
                    print(f"[WARN] reserva.fecha_reserva inválida para reserva {reserva.id}")
                    continue

                # Intentar parsear check-in
                check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()

                diferencia_dias = (check_in - reserva.fecha_reserva.date()).days
                tiempos_reserva.append(diferencia_dias)

            except Exception as e:
                print(f"[ERROR] en reserva {reserva.id}: {e}")
                continue

    if tiempos_reserva:
        tiempo_promedio_reserva = sum(tiempos_reserva) / len(tiempos_reserva)
    else:
        tiempo_promedio_reserva = 0

    return tiempo_promedio_reserva

def top_5_agencias_mas_reservas():
    reservas = Reserva.objects.all()
    conteo_reservas = defaultdict(lambda: {'total_reservas': 0, 'ingresos': Decimal('0.00')})

    for reserva in reservas:
        if reserva.nombre_usuario:
            conteo_reservas[reserva.nombre_usuario]['total_reservas'] += 1
            conteo_reservas[reserva.nombre_usuario]['ingresos'] += reserva.precio_total

    total_reservas = sum(data['total_reservas'] for data in conteo_reservas.values())

    lista_agencias = sorted(
        [
            {
                'agencia': agencia,
                'total_reservas': data['total_reservas'],
                'ingresos': data['ingresos'],
                'porcentaje': round((data['total_reservas'] / total_reservas * 100), 1) if total_reservas > 0 else 0
            }
            for agencia, data in conteo_reservas.items()
        ],
        key=lambda x: x['total_reservas'],
        reverse=True
    )

    return lista_agencias[:5]

def top_5_hoteles_mas_reservados():
    """
    Obtiene el top 5 de hoteles con más reservas y devuelve también
    el porcentaje de ocupación relativo al máximo para pintar la barra.
    """
    # 1) Traemos todas las reservas que estén asociadas a un hotel
    reservas_hoteles = Reserva.objects.filter(hotel__isnull=False)

    # 2) Contamos cuántas reservas tiene cada hotel
    conteo = Counter(r.hotel for r in reservas_hoteles)

    # 3) Tomamos los 5 más comunes
    top5 = conteo.most_common(5)
    if not top5:
        return []

    # 4) Averiguamos cuál es la máxima para normalizar
    max_reservas = top5[0][1] or 1  # evitar división por cero
    
    cant_reservas = reservas_hoteles.count()

    resultados = []
    for hotel, num_reservas in top5:
        # 5) Sumamos ingresos de ese hotel
        ingresos = reservas_hoteles.filter(hotel=hotel).aggregate(
            ingresos_totales=Sum('precio_total')
        )['ingresos_totales'] or Decimal('0.00')

        # 6) Calculamos ocupación relativa
        ocupacion_pct = round((num_reservas / cant_reservas) * 100, 1)

        resultados.append({
            'hotel_nombre': hotel.hotel_nombre,
            'num_reservas': num_reservas,
            'ingresos_totales': ingresos,
            'ocupacion': ocupacion_pct,
        })
    

    return resultados

@manager_required
@login_required
def listar_usuarios(request):
    query = request.GET.get('q')
    usuarios_list = CustomUser.objects.all()
    if query:
        usuarios_list = usuarios_list.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(direccion__icontains=query)
        )
    paginator = Paginator(usuarios_list, 10)  # Mostrar 10 usuarios por página
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)

    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios, 'query': query})

@manager_required
@login_required
def crear_usuario(request):
    if request.method == 'POST':
        agencia            = request.POST.get('agencia')
        username           = request.POST.get('username')
        email              = request.POST.get('email')
        telefono           = request.POST.get('telefono')
        direccion          = request.POST.get('direccion')
        nombre_dueno       = request.POST.get('nombre_dueno')
        telefono_dueno     = request.POST.get('telefono_dueno')
        is_manager         = request.POST.get('is_manager') == 'on'
        password           = request.POST.get('password')
        confirm_password   = request.POST.get('confirm_password')
        saldo_pendiente    = request.POST.get('saldo_pendiente')
        logo               = request.FILES.get('logo')

        fee_hotel          = request.POST.get('fee_hotel')
        tipo_fee_hotel     = request.POST.get('tipo_fee_hotel')
        fee_carro          = request.POST.get('fee_carro')
        tipo_fee_carro     = request.POST.get('tipo_fee_carro')
        fee_traslados      = request.POST.get('fee_traslados')
        tipo_fee_traslados = request.POST.get('tipo_fee_traslados')

        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'usuarios/crear_usuario.html', {
                'agencia': agencia,
                'username': username,
                'email': email,
                'telefono': telefono,
                'direccion': direccion,
                'nombre_dueno': nombre_dueno,
                'telefono_dueno': telefono_dueno,
                'is_manager': is_manager,
                'saldo_pendiente': saldo_pendiente,
                'fee_hotel': fee_hotel,
                'tipo_fee_hotel': tipo_fee_hotel,
                'fee_carro': fee_carro,
                'tipo_fee_carro': tipo_fee_carro,
                'fee_traslados': fee_traslados,
                'tipo_fee_traslados': tipo_fee_traslados,
            })

        nuevo_usuario = CustomUser(
            agencia=agencia,
            username=username,
            email=email,
            telefono=telefono,
            direccion=direccion,
            nombre_dueno=nombre_dueno,
            telefono_dueno=telefono_dueno,
            is_manager=is_manager,
            saldo_pendiente=saldo_pendiente,
            fee_hotel=fee_hotel,
            tipo_fee_hotel=tipo_fee_hotel,
            fee_carro=fee_carro,
            tipo_fee_carro=tipo_fee_carro,
            fee_traslados=fee_traslados,
            tipo_fee_traslados=tipo_fee_traslados,
            logo=logo
        )
        nuevo_usuario.set_password(password)

        # Logo por defecto si no se sube uno nuevo
        if not logo:
            nuevo_usuario.logo.name = 'logos/user_default_logo.png'

        nuevo_usuario.save()

        messages.success(request, "Usuario creado exitosamente.")
        return redirect('listar_usuarios')

    return render(request, 'usuarios/crear_usuario.html')

@manager_required
@login_required
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('listar_usuarios')
    return render(request, 'usuarios/eliminar_usuario.html', {'usuario': usuario})


from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

from django.shortcuts import get_object_or_404, redirect, render
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .decorators import manager_required
from .models import CustomUser

def _to_decimal(value, default="0"):
    txt = (value or "").strip()
    if txt == "":
        txt = default
    try:
        return Decimal(txt)
    except (InvalidOperation, TypeError):
        return Decimal(default)

@login_required
@manager_required
@transaction.atomic
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(CustomUser, id=usuario_id)

    if request.method == 'POST':
        # Básicos
        username = (request.POST.get('username') or '').strip()
        email    = (request.POST.get('email') or '').strip().lower()
        agencia  = (request.POST.get('agencia') or '').strip()
        telefono = (request.POST.get('telefono') or '').strip()
        direccion = (request.POST.get('direccion') or '').strip()

        nombre_dueno   = (request.POST.get('nombre_dueno') or '').strip()
        telefono_dueno = (request.POST.get('telefono_dueno') or '').strip()

        is_manager = request.POST.get('is_manager') == 'on'

        # Unicidad username/email
        if CustomUser.objects.exclude(id=usuario.id).filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

        if CustomUser.objects.exclude(id=usuario.id).filter(email=email).exists():
            messages.error(request, "El email ya está en uso.")
            return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

        # Email válido
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "El email no es válido.")
            return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

        # Contraseña (opcional)
        password       = request.POST.get('password') or ''
        confirm_passwd = request.POST.get('confirm_password') or ''
        if password:
            if password != confirm_passwd:
                messages.error(request, "Las contraseñas no coinciden.")
                return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})
            usuario.set_password(password)
            # Si edito mi propia cuenta, mantén la sesión
            if request.user.id == usuario.id:
                update_session_auth_hash(request, usuario)

        # Saneos simples
        telefono = ''.join(c for c in telefono if c.isdigit() or c in '+-() ')
        telefono_dueno = ''.join(c for c in telefono_dueno if c.isdigit() or c in '+-() ')

        # Decimals
        saldo_pendiente = _to_decimal(request.POST.get('saldo_pendiente'), "0")
        if saldo_pendiente < 0:
            messages.error(request, "El saldo no puede ser negativo.")
            return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

        # Fees + tipos
        def get_fee_pair(prefix):
            fee = _to_decimal(request.POST.get(f'fee_{prefix}'), "0")
            tipo = request.POST.get(f'tipo_fee_{prefix}') or '$'
            tipo = tipo if tipo in ('$', '%') else '$'
            if tipo == '%' and not (Decimal('0') <= fee <= Decimal('100')):
                raise ValueError(f"El Fee {prefix.capitalize()} en % debe estar entre 0 y 100.")
            if fee < 0:
                raise ValueError(f"El Fee {prefix.capitalize()} no puede ser negativo.")
            return fee, tipo

        try:
            fee_hotel, tipo_fee_hotel = get_fee_pair('hotel')
            fee_nino, tipo_fee_nino   = get_fee_pair('nino')
            fee_carro, tipo_fee_carro = get_fee_pair('carro')
            fee_tras,  tipo_fee_tras  = get_fee_pair('traslados')
        except ValueError as e:
            messages.error(request, str(e))
            return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})

        # Logo (solo si suben archivo)
        if 'logo' in request.FILES:
            usuario.logo = request.FILES['logo']
        # Si no hay archivo, dejamos el actual/fallback del template

        # Asignaciones finales
        usuario.username        = username
        usuario.email           = email
        usuario.agencia         = agencia
        usuario.telefono        = telefono
        usuario.direccion       = direccion
        usuario.nombre_dueno    = nombre_dueno
        usuario.telefono_dueno  = telefono_dueno
        usuario.is_manager      = is_manager

        usuario.saldo_pendiente    = saldo_pendiente
        usuario.fee_hotel          = fee_hotel
        usuario.tipo_fee_hotel     = tipo_fee_hotel
        usuario.fee_nino           = fee_nino
        usuario.tipo_fee_nino      = tipo_fee_nino
        usuario.fee_carro          = fee_carro
        usuario.tipo_fee_carro     = tipo_fee_carro
        usuario.fee_traslados      = fee_tras
        usuario.tipo_fee_traslados = tipo_fee_tras

        usuario.save()
        messages.success(request, "Usuario actualizado correctamente.")
        return redirect('listar_usuarios')

    return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})
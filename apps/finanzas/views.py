# finanzas/views.py

# ────────────────────────────
#  Librerías estándar
# ────────────────────────────
from decimal import Decimal

# ────────────────────────────
#  Django imports
# ────────────────────────────
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import (
    Q, Sum, Case, When, F, FloatField, DecimalField
)
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

# ────────────────────────────
#  App imports
# ────────────────────────────
from apps.backoffice.models import Reserva
from apps.usuarios.models import CustomUser
from .forms import TransaccionForm
from .models import Transaccion



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from apps.backoffice.models import Reserva
from apps.usuarios.decorators import manager_required


@manager_required
@login_required
def listar_reservas_finanzas(request):
    reservas = Reserva.objects.select_related(
        'proveedor',
        'hotel',
        'hotel_importado',
        'traslado',
        'envio',
        'remesa'
    ).prefetch_related(
        'habitaciones_reserva__pasajeros'
    ).all()

    # Filtros...
    query = request.GET.get('q', '').strip()
    if query:
        reservas = reservas.filter(
            Q(hotel__hotel_nombre__icontains=query) |
            Q(hotel_importado__hotel_name__icontains=query) |
            Q(nombre_usuario__icontains=query) |
            Q(email_empleado__icontains=query) |
            Q(proveedor__nombre__icontains=query)
        )

    id_reserva = request.GET.get('id_reserva', '').strip()
    if id_reserva.isdigit():
        reservas = reservas.filter(id=id_reserva)

    nombre_pasajero = request.GET.get('nombre_pasajero', '').strip()
    if nombre_pasajero:
        reservas = reservas.filter(habitaciones_reserva__pasajeros__nombre__icontains=nombre_pasajero)

    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    if fecha_inicio:
        try:
            reservas = reservas.filter(fecha_reserva__date__gte=datetime.strptime(fecha_inicio, "%Y-%m-%d").date())
        except ValueError:
            print(f"⚠️ Fecha inválida inicio: {fecha_inicio}")

    if fecha_fin:
        try:
            reservas = reservas.filter(fecha_reserva__date__lte=datetime.strptime(fecha_fin, "%Y-%m-%d").date())
        except ValueError:
            print(f"⚠️ Fecha inválida fin: {fecha_fin}")

    reservas = reservas.order_by('-fecha_reserva').distinct()

    paginator = Paginator(reservas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'reservas': page_obj,
        'query': query,
        'id_reserva': id_reserva,
        'nombre_pasajero': nombre_pasajero,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'finanzas/listar_reservas_finanzas.html', context)




@login_required
@transaction.atomic
def transacciones_view(request, reserva_id):
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)

    # Obtener las transacciones asociadas
    transacciones = Transaccion.objects.filter(reserva=reserva).order_by('-fecha')

    # Calcular montos por tipo
    monto_cobrado = sum(t.monto for t in transacciones if t.tipo == 'cobro')
    monto_pagado = sum(t.monto for t in transacciones if t.tipo == 'pago')
    monto_reembolsado = sum(t.monto for t in transacciones if t.tipo == 'reembolso')

    # Totales
    total_cobros = monto_cobrado
    total_pagos = monto_pagado
    total_reembolsos = monto_reembolsado
    balance = total_cobros - total_pagos

    # Saldos a mostrar
    saldo_por_cobrar = reserva.importe_por_cobrar - total_cobros
    saldo_por_pagar = reserva.importe_por_pagar - total_pagos

    ganancia = reserva.costo_total - reserva.costo_sin_fee

    # Actualizar estado cobrada/pagada
    if saldo_por_cobrar <= Decimal('0.00') and not reserva.cobrada:
        reserva.cobrada = True
        reserva.save()

    if saldo_por_pagar <= Decimal('0.00') and not reserva.pagada:
        reserva.pagada = True
        reserva.save()

    # Obtener usuario relacionado
    username = reserva.agencia
    usuario = get_object_or_404(CustomUser, agencia=username)

    # Ajustar saldo del usuario en caso de exceso
    if saldo_por_cobrar < Decimal('0.00') or saldo_por_pagar < Decimal('0.00'):
        exceso_cobro = abs(saldo_por_cobrar) if saldo_por_cobrar < Decimal('0.00') else Decimal('0.00')
        exceso_pago = abs(saldo_por_pagar) if saldo_por_pagar < Decimal('0.00') else Decimal('0.00')
        # Puedes guardar ajustes si deseas
        usuario.save()

    # Procesar formulario POST
    if request.method == 'POST':
        form = TransaccionForm(request.POST)
        if form.is_valid():
            nueva_transaccion = form.save(commit=False)
            nueva_transaccion.reserva = reserva
            action = request.POST.get('action')

            if action == 'add':
                nueva_transaccion.save()
                messages.success(request, "Transacción agregada con éxito.")

            elif action == 'refund':
                nueva_transaccion.monto = monto_cobrado
                nueva_transaccion.tipo = 'reembolso'
                nueva_transaccion.save()

                usuario.saldo_pendiente -= monto_cobrado
                usuario.save()

                messages.success(request, "Reembolso realizado con éxito.")

            return redirect('transacciones', reserva_id=reserva.id)
    else:
        form = TransaccionForm()

    # Contexto completo
    context = {
        'reserva': reserva,
        'transacciones': transacciones,
        'form': form,
        'saldo_por_cobrar': saldo_por_cobrar,
        'saldo_por_pagar': saldo_por_pagar,
        'ganancia': ganancia,
        'total_cobros': total_cobros,
        'total_pagos': total_pagos,
        'total_reembolsos': total_reembolsos,
        'balance': balance,
    }

    return render(request, 'finanzas/transacciones.html', context)


login_required
@require_POST
def transaccion_eliminar(request, reserva_id, transaccion_id):
    # Obtener la reserva
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Obtener la transacción y asegurarse de que pertenece a la reserva
    transaccion = get_object_or_404(Transaccion, id=transaccion_id, reserva=reserva)
    
    # Eliminar la transacción
    transaccion.delete()
    messages.success(request, "Transacción eliminada con éxito.")
    
    # Redirigir a la página de transacciones de la reserva
    return redirect('transacciones', reserva_id=reserva.id)

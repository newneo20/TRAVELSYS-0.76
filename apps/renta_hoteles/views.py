from .models import Proveedor, PoloTuristico
from django.shortcuts import render, get_object_or_404, redirect
from .forms import PoloTuristicoForm

def hotel_tabs(request):
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    context = {
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
    }
    return render(request, 'renta_hoteles/hotel_tabs.html', context)

def hotel_content(request):
    proveedores = Proveedor.objects.all()
    polos_turisticos = PoloTuristico.objects.all()
    context = {
        'proveedores': proveedores,
        'polos_turisticos': polos_turisticos,
    }
    return render(request, 'renta_hoteles/hotel_content.html', context)

def hotel_rooms(request):
    return render(request, 'renta_hoteles/hotel_rooms.html')

def hotel_settings(request):
    return render(request, 'renta_hoteles/hotel_settings.html')

def hotel_offers(request):
    return render(request, 'renta_hoteles/hotel_offers.html')

def hotel_facilities(request):
    return render(request, 'renta_hoteles/hotel_facilities.html')

def hotel_discounts(request):
    return render(request, 'renta_hoteles/hotel_discounts.html')

# Proveedores #

def listar_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'renta_hoteles/proveedores/listar_proveedores.html', {'proveedores': proveedores})

def crear_proveedor(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        correo1 = request.POST.get('correo1')
        correo2 = request.POST.get('correo2')
        correo3 = request.POST.get('correo3')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        detalles_cuenta_bancaria = request.POST.get('detalles_cuenta_bancaria')
        Proveedor.objects.create(
            nombre=nombre, 
            correo1=correo1, 
            correo2=correo2, 
            correo3=correo3, 
            telefono=telefono, 
            direccion=direccion, 
            detalles_cuenta_bancaria=detalles_cuenta_bancaria
        )
        return redirect('listar_proveedores')
    return render(request, 'renta_hoteles/proveedores/crear_proveedor.html')

def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.nombre = request.POST.get('nombre')
        proveedor.correo1 = request.POST.get('correo1')
        proveedor.correo2 = request.POST.get('correo2')
        proveedor.correo3 = request.POST.get('correo3')
        proveedor.telefono = request.POST.get('telefono')
        proveedor.direccion = request.POST.get('direccion')
        proveedor.detalles_cuenta_bancaria = request.POST.get('detalles_cuenta_bancaria')
        proveedor.save()
        return redirect('listar_proveedores')
    return render(request, 'renta_hoteles/proveedores/editar_proveedor.html', {'proveedor': proveedor})

def eliminar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        return redirect('listar_proveedores')
    return render(request, 'renta_hoteles/proveedores/eliminar_proveedor.html', {'proveedor': proveedor})

# Polo Turistico #

def listar_polos(request):
    polos = PoloTuristico.objects.all()
    return render(request, 'renta_hoteles/polos/listar_polo.html', {'polos': polos})

def crear_polo(request):
    if request.method == 'POST':
        form = PoloTuristicoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_polos')
    else:
        form = PoloTuristicoForm()
    return render(request, 'renta_hoteles/polos/crear_polo.html', {'form': form})

def editar_polo(request, pk):
    polo = get_object_or_404(PoloTuristico, pk=pk)
    if request.method == 'POST':
        form = PoloTuristicoForm(request.POST, instance=polo)
        if form.is_valid():
            form.save()
            return redirect('listar_polos')
    else:
        form = PoloTuristicoForm(instance=polo)
    return render(request, 'renta_hoteles/polos/editar_polo.html', {'form': form})

def eliminar_polo(request, pk):
    polo = get_object_or_404(PoloTuristico, pk=pk)
    if request.method == 'POST':
        polo.delete()
        return redirect('listar_polos')
    return render(request, 'renta_hoteles/polos/eliminar_polo.html', {'polo': polo})
    
from django import forms
from .models import PoloTuristico, Proveedor, Hotel, Habitacion, ReservaHotel

class ReservaHotelForm(forms.ModelForm):
    class Meta:
        model = ReservaHotel
        fields = ['hotel', 'noches', 'fecha_reserva', 'total']

class PoloTuristicoForm(forms.ModelForm):
    class Meta:
        model = PoloTuristico
        fields = ['nombre', 'pais']

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'correo1', 'correo2', 'correo3', 'telefono', 'detalles_cuenta_bancaria', 'direccion']
from django import forms
from apps.backoffice.models import PoloTuristico, Proveedor, Hotel, Habitacion, ReservaHotel, CadenaHotelera, Reserva, Pasajero, OfertasEspeciales

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
        fields = '__all__'  # O lista explícitamente los campos que deseas incluir


class CadenaHoteleraForm(forms.ModelForm):
    class Meta:
        model = CadenaHotelera
        fields = ['nombre', 'descripcion']
        

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = '__all__'

class PasajeroForm(forms.ModelForm):
    class Meta:
        model = Pasajero
        fields = '__all__'
        
class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['hotel', 'tipo', 'descripcion', 'datetimes', 'foto', 'adultos', 'ninos', 
                  'max_capacidad', 'min_capacidad', 'descripcion_capacidad', 'admite_3_con_1', 'solo_adultos']
        widgets = {
            'datetimes': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'descripcion_capacidad': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['admite_3_con_1', 'solo_adultos']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['admite_3_con_1'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['solo_adultos'].widget.attrs.update({'class': 'form-check-input'})
        
class OfertasEspecialesForm(forms.ModelForm):
    class Meta:
        model = OfertasEspeciales
        fields = ['codigo', 'disponible', 'nombre', 'descripcion']


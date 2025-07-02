from django import forms
from .models import Transaccion

class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['monto', 'tipo']  # Ajusta según los campos en tu modelo
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': (
                    'w-full p-2 border border-gray-300 rounded '
                    'focus:outline-none focus:ring-2 focus:ring-indigo-500'
                ),
                'placeholder': 'Monto',
                'step': '0.01',  # Para indicar decimales si lo deseas
            }),
            'tipo': forms.Select(attrs={
                'class': (
                    'w-full p-2 border border-gray-300 rounded '
                    'focus:outline-none focus:ring-2 focus:ring-indigo-500'
                ),
            }),
        }

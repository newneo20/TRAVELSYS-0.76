from django.db import models
from apps.backoffice.models import Reserva

class Transaccion(models.Model):
    TIPO_CHOICES = [
        ('cobro', 'Cobro'),
        ('pago', 'Pago'),
        ('reembolso', 'Reembolso'),
    ]
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='transacciones')
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    def __str__(self):
        return f"{self.tipo.capitalize()} de ${self.monto} para {self.reserva}"
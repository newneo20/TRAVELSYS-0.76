# gestion_economica/models.py
from django.db import models

class Transaccion(models.Model):
    tipo = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    descripcion = models.TextField()

class ReporteFinanciero(models.Model):
    total_ingresos = models.DecimalField(max_digits=10, decimal_places=2)
    total_egresos = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
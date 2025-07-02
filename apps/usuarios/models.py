# usuarios/models.py
from django.contrib.auth.models import AbstractUser # type: ignore
from django.db import models # type: ignore

class CustomUser(AbstractUser):
    is_manager = models.BooleanField(default=False)
    agencia = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    nombre_dueno = models.CharField(max_length=255, blank=True, null=True)
    telefono_dueno = models.CharField(max_length=15, blank=True, null=True)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # ==================================== #
    #------------- LOS FEE --------------- #
    # ==================================== #
    
    #------------- HOTELES --------------- #
    fee_hotel = models.IntegerField(blank=True, null=True)
    fee_nino = models.IntegerField(blank=True, null=True)
    tipo_fee_hotel = models.CharField(max_length=2, blank=True, null=True)
    #------------- CARROS --------------- #
    fee_carro = models.IntegerField(blank=True, null=True)
    tipo_fee_carro = models.CharField(max_length=2, blank=True, null=True)
    #------------- TARARA --------------- #
    fee_tarara = models.IntegerField(blank=True, null=True)
    tipo_fee_tarara = models.CharField(max_length=2, blank=True, null=True)
    #------------- TRASLADOS --------------- #
    fee_traslados = models.IntegerField(blank=True, null=True)
    tipo_fee_traslados = models.CharField(max_length=2, blank=True, null=True)
    

    def __str__(self):
        return self.username

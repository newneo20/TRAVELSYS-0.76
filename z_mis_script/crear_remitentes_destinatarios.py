import os
import django
import random
from faker import Faker

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')  # ✅ Cambiado correctamente
django.setup()

from apps.backoffice.models import Remitente, Destinatario  # ✅ Cambia 'envios' si tu app se llama diferente

fake = Faker('es_ES')

# Crear 20 Remitentes
for _ in range(20):
    Remitente.objects.create(
        nombre_apellido=fake.name(),
        id_documento=fake.license_plate(),
        telefono=fake.phone_number(),
        direccion=fake.address()
    )

print("✅ Se han creado 20 remitentes.")

# Crear 20 Destinatarios
for _ in range(20):
    Destinatario.objects.create(
        primer_nombre=fake.first_name(),
        segundo_nombre=fake.first_name() if random.choice([True, False]) else '',
        primer_apellido=fake.last_name(),
        segundo_apellido=fake.last_name() if random.choice([True, False]) else '',
        ci=str(fake.random_int(min=10000000000, max=99999999999)),
        telefono=fake.phone_number(),
        telefono_adicional=fake.phone_number() if random.choice([True, False]) else '',
        calle=fake.street_name(),
        numero=str(fake.building_number()),
        entre_calle=fake.street_name(),
        y_calle=fake.street_name(),
        apto_reparto=fake.secondary_address(),
        piso=str(random.randint(1, 10)),
        municipio=fake.city(),
        provincia=fake.state(),
        email=fake.email(),
        observaciones=fake.text(max_nb_chars=100)
    )

print("✅ Se han creado 20 destinatarios.")

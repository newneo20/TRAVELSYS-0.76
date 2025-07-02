import os
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.apps import apps
from faker import Faker

fake = Faker('es_ES')
User = get_user_model()

# Crear 100 usuarios realistas
print("Creando usuarios...")
for _ in range(100):
    username = fake.user_name()
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(
            username=username,
            email=fake.email(),
            password='12345678',
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
print("Usuarios creados.")

# Modelos excluidos
excluir_modelos = ['Permission', 'Group', 'ContentType', 'Session', 'LogEntry']
modelos_creados = {}

print("Poblando modelos de todas las apps...")
for model in apps.get_models():
    model_name = model.__name__
    app_label = model._meta.app_label

    if model_name in excluir_modelos or model == User or model_name.lower() == 'reserva':
        continue

    print(f"→ {app_label}.{model_name}")
    creados = 0

    for _ in range(300):
        instancia = model()
        for field in model._meta.fields:
            nombre = field.name
            if nombre in ['id', 'pk']:
                continue
            try:
                if field.many_to_one:
                    related_model = field.remote_field.model
                    related_objs = related_model.objects.all()
                    if related_objs.exists():
                        setattr(instancia, nombre, random.choice(related_objs))
                elif field.get_internal_type() == 'CharField':
                    if 'nombre' in nombre:
                        valor = fake.company() if 'hotel' in nombre or 'agencia' in nombre else fake.first_name()
                    elif 'apellido' in nombre:
                        valor = fake.last_name()
                    elif 'codigo' in nombre:
                        valor = fake.bothify(text='??##??')
                    elif 'telefono' in nombre:
                        valor = fake.phone_number()
                    elif 'email' in nombre:
                        valor = fake.email()
                    elif 'direccion' in nombre:
                        valor = fake.address()
                    elif 'pasaporte' in nombre:
                        valor = fake.bothify(text='[A-Z]########')
                    elif 'id_documento' in nombre or 'ci' in nombre:
                        valor = fake.bothify(text='###########')
                    else:
                        valor = fake.word()
                    setattr(instancia, nombre, valor[:field.max_length])
                elif field.get_internal_type() == 'TextField':
                    setattr(instancia, nombre, fake.paragraph(nb_sentences=3))
                elif field.get_internal_type() == 'DateField':
                    setattr(instancia, nombre, fake.date_between(start_date='-2y', end_date='today'))
                elif field.get_internal_type() == 'DateTimeField':
                    setattr(instancia, nombre, fake.date_time_between(start_date='-2y', end_date='now'))
                elif field.get_internal_type() == 'IntegerField':
                    setattr(instancia, nombre, random.randint(1, 10))
                elif field.get_internal_type() == 'DecimalField':
                    setattr(instancia, nombre, Decimal(random.uniform(10.0, 2000.0)).quantize(Decimal('0.01')))
                elif field.get_internal_type() == 'BooleanField':
                    setattr(instancia, nombre, random.choice([True, False]))
            except Exception:
                continue
        try:
            instancia.save()
            creados += 1
        except Exception:
            continue

    modelos_creados[f"{app_label}.{model_name}"] = creados

# Crear 300 reservas realistas
print("Creando reservas aleatorias...")
try:
    Reserva = apps.get_model('reservas', 'Reserva')  # Ajusta si el modelo está en otra app
    for _ in range(300):
        reserva = Reserva()
        for field in Reserva._meta.fields:
            nombre = field.name
            if nombre in ['id', 'pk']:
                continue
            try:
                if field.many_to_one:
                    related_model = field.remote_field.model
                    related_objs = related_model.objects.all()
                    if related_objs.exists():
                        setattr(reserva, nombre, random.choice(related_objs))
                elif field.get_internal_type() == 'CharField':
                    if 'numero_confirmacion' in nombre:
                        valor = fake.bothify(text='CONF-####')
                    elif 'tipo' in nombre:
                        valor = random.choice(['hotel', 'traslado', 'envio', 'remesa', 'certificado'])
                    else:
                        valor = fake.word()
                    setattr(reserva, nombre, valor[:field.max_length])
                elif field.get_internal_type() == 'TextField':
                    setattr(reserva, nombre, fake.text(max_nb_chars=200))
                elif field.get_internal_type() == 'DateField':
                    setattr(reserva, nombre, fake.date_between(start_date='-1y', end_date='+30d'))
                elif field.get_internal_type() == 'DateTimeField':
                    setattr(reserva, nombre, fake.date_time_between(start_date='-1y', end_date='now'))
                elif field.get_internal_type() == 'IntegerField':
                    setattr(reserva, nombre, random.randint(1, 10))
                elif field.get_internal_type() == 'DecimalField':
                    setattr(reserva, nombre, Decimal(random.uniform(50.0, 2000.0)).quantize(Decimal('0.01')))
                elif field.get_internal_type() == 'BooleanField':
                    setattr(reserva, nombre, random.choice([True, False]))
            except Exception:
                continue
        try:
            reserva.save()
        except Exception:
            continue
    print("Reservas creadas correctamente.")
except LookupError:
    print("⚠️  El modelo 'Reserva' no fue encontrado.")

# Resumen
print("\nResumen de modelos poblados:")
for modelo, cantidad in modelos_creados.items():
    print(f"{modelo}: {cantidad} instancias creadas")
print("\n✅ Base de datos poblada exitosamente.")

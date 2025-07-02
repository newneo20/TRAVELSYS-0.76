import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from usuarios.models import CustomUser

usuarios = [
    {
                "username": "yoa",
                "email": "yoa@gmail.com",
                "telefono": "7864990620",
                "direccion": "Edif 22 Apto. 8 Bloque A. Rpto. Conrado Benítez",
                "is_manager": True,
                "saldo_pendiente": 0.00,
                "agencia": "SISTEMAS",
                "nombre_dueno": "Yoandri",
                "telefono_dueno": "7864990621",
                "fee_hotel": 10,
                "fee_nino": 5,
                "tipo_fee_hotel": "$",
                "fee_carro": 10,
                "tipo_fee_carro": "$",
                "fee_tarara": 10,
                "tipo_fee_tarara": "$",
            },
            {
                "username": "sadis",
                "email": "info@rutamultiservice.com",
                "telefono": "7864990612",
                "direccion": "9666 Cora Way, Miami, Florida, 33165",
                "is_manager": True,
                "saldo_pendiente": 0.00,
                "agencia": "RUTAMULTISERVICE",
                "nombre_dueno": "Sadis Martin",
                "telefono_dueno": "7864990613",
                "fee_hotel": 10,
                "fee_nino": 5,
                "tipo_fee_hotel": "$",
                "fee_carro": 10,
                "tipo_fee_carro": "$",
                "fee_tarara": 10,
                "tipo_fee_tarara": "$",
            },
            {
                "username": "barreto",
                "email": "marverde.travel@gmail.com",
                "telefono": "7864257872",
                "direccion": "9535 W Flagler St, Miami, FL, 33174",
                "is_manager": False,
                "saldo_pendiente": 0.00,
                "agencia": "MARVERDE",
                "nombre_dueno": "Jorge Barreto",
                "telefono_dueno": "7864257873",
                "fee_hotel": 10,
                "fee_nino": 5,
                "tipo_fee_hotel": "$",
                "fee_carro": 10,
                "tipo_fee_carro": "$",
                "fee_tarara": 10,
                "tipo_fee_tarara": "$",
            },
            {
                "username": "ramoncito",
                "email": "lacuevitamultiservice@gmail.com",
                "telefono": "7862222222",
                "direccion": "7210 NW 179TH APT 204 HIALEAH, FL 33015",
                "is_manager": False,
                "saldo_pendiente": 0.00,
                "agencia": "LA CUEVITA MULTISERVICE",
                "nombre_dueno": "Ramon Gonzalez",
                "telefono_dueno": "7862222223",
                "fee_hotel": 10,
                "fee_nino": 5,
                "tipo_fee_hotel": "$",
                "fee_carro": 10,
                "tipo_fee_carro": "$",
                "fee_tarara": 10,
                "tipo_fee_tarara": "$",
            },
            {
                "username": "danay",
                "email": "danay@gmail.com",
                "telefono": "786624835",
                "direccion": "1335 NW 98 Court. Unit 5 & 6 Doral, FL 33172",
                "is_manager": False,
                "saldo_pendiente": 0.00,
                "agencia": "A Tu Aire Vip Services",
                "nombre_dueno": "Danay Rios",
                "telefono_dueno": "786624836",
                "fee_hotel": 10,
                "fee_nino": 5,
                "tipo_fee_hotel": "$",
                "fee_carro": 10,
                "tipo_fee_carro": "$",
                "fee_tarara": 10,
                "tipo_fee_tarara": "$",
            },
            {
                "username": "yany",
                "email": "gotravelgotours@gmail.com",
                "telefono": "3053015249",
                "direccion": "Miami, FL, United States",
                "is_manager": False,
                "saldo_pendiente": 0.00,
                "agencia": "GO TRAVEL GO",
                "nombre_dueno": "Yany Lopez",
                "telefono_dueno": "3053015250",
                "fee_hotel": 10,
                "fee_nino": 5,
                "tipo_fee_hotel": "$",
                "fee_carro": 10,
                "tipo_fee_carro": "$",
                "fee_tarara": 10,
                "tipo_fee_tarara": "$",
            },
    # Agrega más usuarios aquí...
]

for usuario in usuarios:
    user, created = CustomUser.objects.get_or_create(
        username=usuario["username"],
        defaults=usuario
    )

    if created:
        print(f'Usuario {usuario["username"]} creado exitosamente')
    else:
        print(f'Usuario {usuario["username"]} ya existe')

print("Carga de usuarios completada")





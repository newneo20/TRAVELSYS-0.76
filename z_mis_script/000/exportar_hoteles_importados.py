import os
import sys
import django
import pandas as pd

# === Ruta actual del script ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# === Añadir el path del proyecto (2 niveles arriba) ===
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '../../'))
sys.path.append(BASE_DIR)

# === Establecer settings de Django ===
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

# === Importar modelo ===
from apps.backoffice.models import HotelImportado

# === Exportar a CSV ===
hoteles = HotelImportado.objects.all()

datos = []
for hotel in hoteles:
    datos.append({
        'destino': hotel.destino,
        'city_code': hotel.city_code,
        'hotel_code': hotel.hotel_code,
        'hotel_name': hotel.hotel_name,
        'hotel_city_code': hotel.hotel_city_code,
        'area_id': hotel.area_id,
        'giata_id': hotel.giata_id,
        'country_iso_code': hotel.country_iso_code,
        'country_name': hotel.country_name,
        'address': hotel.address,
        'email': hotel.email,
        'latitude': hotel.latitude,
        'longitude': hotel.longitude,
        'rating': hotel.rating,
    })

df = pd.DataFrame(datos)

# Guardar en CSV en la misma carpeta del script
output_path = os.path.join(SCRIPT_DIR, 'HotelImportado.csv')
df.to_csv(output_path, index=False)

print(f"✅ Exportación completada en: {output_path}")

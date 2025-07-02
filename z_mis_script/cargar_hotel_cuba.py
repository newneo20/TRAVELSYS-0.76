# cargar_hotel_cuba.py

import os
import django
import pandas as pd
from decimal import Decimal

# Configura entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from apps.backoffice.models import HotelImportado  # ← AJUSTADO AQUÍ

# Ruta al archivo Excel
excel_path = 'hoteles_cuba_Distal.xlsx'

# Cargar el archivo
df = pd.read_excel(excel_path)

# Procesar cada fila
nuevos = 0
actualizados = 0
for index, row in df.iterrows():
    hotel, created = HotelImportado.objects.update_or_create(
        hotel_code=row['HotelCode'],
        defaults={
            'destino': row['Destino'],
            'city_code': row['CityCode'],
            'hotel_name': row['HotelName'],
            'hotel_city_code': row['HotelCityCode'],
            'area_id': row.get('AreaID') or None,
            'giata_id': str(row['GiataID']) if not pd.isna(row['GiataID']) else None,
            'country_iso_code': row['CountryISOCode'],
            'country_name': row['CountryName'],
            'address': row.get('Address') or "",
            'email': row.get('Email') or "",
            'latitude': Decimal(row['Latitude']) if not pd.isna(row['Latitude']) else None,
            'longitude': Decimal(row['Longitude']) if not pd.isna(row['Longitude']) else None,
            'rating': str(row['Rating']) if not pd.isna(row['Rating']) else None,
        }
    )
    if created:
        nuevos += 1
    else:
        actualizados += 1

print(f"✔️ Hoteles creados: {nuevos}")
print(f"♻️ Hoteles actualizados: {actualizados}")

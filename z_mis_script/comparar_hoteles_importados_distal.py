import os
import django
import requests
from bs4 import BeautifulSoup

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from apps.backoffice.models import HotelImportado

HEADERS = {"User-Agent": "Mozilla/5.0"}

def contar_hoteles_en_distal(destino_nombre):
    """
    Retorna la cantidad de hoteles mostrados en Distal para un destino dado.
    """
    base_url = "https://www.distalcaribe.com/es/booking/risultati/hotel"
    params = {
        "StartDate": "20250901",
        "EndDate": "20250908",
        "Groups": "[A2]",
        "IsRoundTrip": "True",
        "Destination": f"[COD;{destino_nombre.upper()}§§Cuba]",
        "SearchId": "static"
    }

    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        bloques = soup.select(".accommodation-card")
        return len(bloques)

    except Exception as e:
        print(f"⚠️ {destino_nombre}: error accediendo a Distal → {str(e)}")
        return 0

# Lista única de destinos en BD
destinos = HotelImportado.objects.values_list("destino", flat=True).distinct()

print("\n📊 COMPARATIVA DE HOTELES EN BD VS DISTAL POR DESTINO\n")

for destino in sorted(destinos):
    cantidad_bd = HotelImportado.objects.filter(destino=destino).count()
    cantidad_distal = contar_hoteles_en_distal(destino)
    print(f"📍 {destino}: ({cantidad_bd}) en BD / ({cantidad_distal}) en DISTAL")

print("\n✅ COMPARACIÓN FINALIZADA.\n")

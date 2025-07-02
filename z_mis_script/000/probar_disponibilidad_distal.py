import os
import django
import requests
import traceback
from collections import defaultdict, Counter
from xml.etree import ElementTree as ET

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from apps.backoffice.models import HotelImportado

# Configuración API
ENDPOINT = "http://api.1way2italy.it/Service/Production/v10/OtaService/HotelAvail"
PASSWORD = "Gmh3S246t987$"
FECHA_INICIO = "2025-09-01"
FECHA_FIN = "2025-09-08"
ADULTOS = 2
NINOS = 0
HEADERS = {"Content-Type": "application/xml"}

def construir_xml(hotel_code):
    guest_count = f'<GuestCount Age="30" Count="{ADULTOS}"/>'
    if NINOS > 0:
        guest_count += f'<GuestCount Age="10" Count="{NINOS}"/>'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<OTA_HotelAvailRQ xmlns="http://www.opentravel.org/OTA/2003/05"
                  Target="Production"
                  PrimaryLangID="en"
                  OnRequestInd="true"
                  MarketCountryCode="us">
  <POS>
    <Source>
      <RequestorID ID="RUTA-US" MessagePassword="{PASSWORD}"/>
    </Source>
  </POS>
  <AvailRequestSegments>
    <AvailRequestSegment>
      <HotelSearchCriteria>
        <Criterion>
          <HotelRef ChainCode="DISTALCU" HotelCode="{hotel_code}"/>
        </Criterion>
      </HotelSearchCriteria>
      <StayDateRange Start="{FECHA_INICIO}" End="{FECHA_FIN}"/>
      <RoomStayCandidates>
        <RoomStayCandidate Quantity="1" RPH="01">
          <GuestCounts>{guest_count}</GuestCounts>
        </RoomStayCandidate>
      </RoomStayCandidates>
    </AvailRequestSegment>
  </AvailRequestSegments>
</OTA_HotelAvailRQ>
"""

# Cargar hoteles
hoteles = HotelImportado.objects.all()
print("📋 INICIO DE VERIFICACIÓN DE DISPONIBILIDAD EN LA API DISTAL\n")
print(f"📅 Fechas: {FECHA_INICIO} al {FECHA_FIN} | 👤 Adultos: {ADULTOS} | 👶 Niños: {NINOS}")
print(f"🏨 Total de hoteles a verificar: {hoteles.count()}")
print("═══════════════════════════════════════════════════════════════════════\n")

resumen_por_destino = defaultdict(list)
cont = 1

for hotel in hoteles:
    xml = construir_xml(hotel.hotel_code)

    print(f"\n🔍 ({cont}) Consultando hotel: {hotel.hotel_name} ({hotel.hotel_code})")
    print("📤 XML ENVIADO:")
    print(xml)

    try:
        response = requests.post(ENDPOINT, data=xml.encode("utf-8"), headers=HEADERS, timeout=20)
        print(f"📡 HTTP Status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            print("📩 Contenido de respuesta:")
            print(response.text)
            cont += 1
            continue

        root = ET.fromstring(response.content)
        ns = {"ns": "http://www.opentravel.org/OTA/2003/05"}
        roomstay = root.find(".//ns:RoomStay", ns)

        if roomstay is not None:
            hotel_info = roomstay.find("ns:BasicPropertyInfo", ns)
            total = roomstay.find("ns:RoomRates/ns:RoomRate/ns:Total", ns)

            nombre   = hotel_info.attrib.get("HotelName", hotel.hotel_name).strip() if hotel_info is not None else hotel.hotel_name
            ciudad   = hotel_info.attrib.get("HotelCityCode", hotel.hotel_city_code).strip() if hotel_info is not None else hotel.hotel_city_code
            destino  = hotel.destino.strip()
            codigo   = hotel.hotel_code.strip()
            precio_raw = total.attrib.get("AmountAfterTax", None) if total is not None else None
            moneda   = total.attrib.get("CurrencyCode", "EUR") if total is not None else "EUR"

            try:
                precio_float = float(precio_raw)
                print(f"✅ DISPONIBLE: {nombre:<45} ({codigo:<15}) | Destino: {destino:<20} | Ciudad: {ciudad:<6} | Precio: {precio_float:>8.2f} {moneda}")
                resumen_por_destino[destino].append((nombre, codigo, precio_float, moneda))
            except (ValueError, TypeError):
                print(f"⚠️ ERROR: Precio inválido para {nombre} ({codigo}) → '{precio_raw}'")

        else:
            print("❌ NO DISPONIBLE: No se encontró RoomStay")
            print("📩 XML de respuesta:")
            print(response.text)

            # Detección de errores específicos
            if "No availability" in response.text:
                print("❗ MOTIVO: No hay disponibilidad en el hotel para esas fechas (Código 322).")
            elif "task was canceled" in response.text or "1999" in response.text:
                print("❗ MOTIVO: El motor de la API canceló la consulta. Puede ser error interno o problema con el código del hotel.")
            else:
                print("❗ MOTIVO: Error desconocido, revisar XML completo.")

    except Exception as e:
        print(f"❌ ERROR: {hotel.hotel_name} ({hotel.hotel_code})")
        traceback.print_exc()

    cont += 1

# RESUMEN FINAL
print("\n📊 RESUMEN FINAL POR DESTINO")
print("═══════════════════════════════════════════════════════════════════════\n")

for destino, hoteles_info in resumen_por_destino.items():
    nombres = [h[0] for h in hoteles_info]
    repetidos = [nombre for nombre, count in Counter(nombres).items() if count > 1]
    print(f"🌍 Destino: {destino}")
    print(f"🏨 Hoteles Analizados: {len(hoteles_info)}")
    print(f"🔁 Nombres Repetidos: {len(repetidos)}")
    if repetidos:
        print("🧾 Lista de Nombres Repetidos:")
        for nombre in repetidos:
            print(f"  🔹 {nombre}")
            for info in hoteles_info:
                if info[0] == nombre:
                    print(f"     ↳ Código: {info[1]} | Precio: {info[2]:.2f} {info[3]}")
    print("───────────────────────────────────────────────────────────────────────")

print("\n📌 RESUMEN RESUMIDO POR DESTINO")
print("═══════════════════════════════════════════════════════════════════════\n")

total_destinos = 0
total_hoteles_global = 0
total_nombres_repetidos_global = 0

for destino, hoteles_info in resumen_por_destino.items():
    total_destinos += 1
    total_hoteles = len(hoteles_info)
    nombres = [h[0] for h in hoteles_info]
    num_repetidos = sum(1 for count in Counter(nombres).values() if count > 1)

    total_hoteles_global += total_hoteles
    total_nombres_repetidos_global += num_repetidos

    print(f"🌍 {destino}: {total_hoteles} hoteles analizados, {num_repetidos} nombres repetidos")

print("\n📈 TOTALES GENERALES")
print("═══════════════════════════════════════════════════════════════════════")
print(f"📌 Total destinos analizados:     {total_destinos}")
print(f"🏨 Total hoteles disponibles:     {total_hoteles_global}")
print(f"🔁 Total nombres repetidos:       {total_nombres_repetidos_global}")
print("═══════════════════════════════════════════════════════════════════════\n")

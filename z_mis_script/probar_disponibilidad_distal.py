import requests
from lxml import etree
from collections import defaultdict, Counter

# Configuración de conexión
URL = "https://xml.1way2italy.com/ota/Service.asmx"
HEADERS = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": "http://www.opentravel.org/OTA/2003/05/HotelProductRQ"
}
PASSWORD = "Gmh3S246t987$"  # Reemplaza con tu clave real

FECHA_ENTRADA = "2025-08-01"
FECHA_SALIDA = "2025-08-08"

POLOS = [
    "BAR", "CAM", "CAY", "CYCZ", "CAYG", "CYL", "CAYP", "CSTM", "CGV", "CFG",
    "GIBC", "GRNM", "GUAQ", "PGUA", "HAV", "HOG", "LTNS", "MATZ", "QPD", "PLG",
    "SSSS", "SNTA", "STLQ", "SAA", "TRI", "VAR", "VIAL"
]

def generar_xml_busqueda(city_code):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <HotelProductRQ xmlns="http://www.opentravel.org/OTA/2003/05" Target="Production" Version="1.0">
      <POS>
        <Source>
          <RequestorID ID="RUTA-US" MessagePassword="{PASSWORD}"/>
        </Source>
      </POS>
      <HotelSearchCriteria>
        <Criterion>
          <HotelRef HotelCityCode="{city_code}" />
          <StayDateRange Start="{FECHA_ENTRADA}" End="{FECHA_SALIDA}"/>
        </Criterion>
      </HotelSearchCriteria>
    </HotelProductRQ>
  </soap:Body>
</soap:Envelope>"""

resumen_por_polo = defaultdict(list)
contador = 1

def consultar_hoteles_por_polo(city_code):
    global contador
    print(f"\n🌐 Conectando al servicio para polo: {city_code}")
    xml = generar_xml_busqueda(city_code)

    try:
        print(f"➡️ Enviando solicitud SOAP para {city_code}...")
        response = requests.post(URL, data=xml.encode("utf-8"), headers=HEADERS, timeout=10)
        print(f"✅ Respuesta recibida para {city_code} (HTTP {response.status_code})")
        response.raise_for_status()

        root = etree.fromstring(response.content)
        ns = {"ns": "http://www.opentravel.org/OTA/2003/05"}

        hoteles = root.findall(".//ns:HotelRef", ns)
        print(f"🏨 Polo {city_code} tiene {len(hoteles)} hoteles disponibles")

        for hotel in hoteles:
            nombre  = hotel.attrib.get("HotelName", "").strip()
            codigo  = hotel.attrib.get("HotelCode", "").strip()
            ciudad  = hotel.attrib.get("HotelCityCode", "").strip()

            total_elem = hotel.find(".//ns:Total", ns)
            if total_elem is not None:
                precio = total_elem.attrib.get("AmountAfterTax", None)
                moneda = total_elem.attrib.get("CurrencyCode", "EUR")
            else:
                precio = None
                moneda = "EUR"

            try:
                precio_float = float(precio)
                print(f"({contador}) ✅ {nombre:<45} ({codigo}) - {ciudad} | {precio_float:.2f} {moneda}")
                resumen_por_polo[city_code].append((nombre, codigo, precio_float, moneda))
            except (TypeError, ValueError):
                print(f"({contador}) ⚠️ Precio inválido para hotel {nombre} ({codigo}) → '{precio}'")

            contador += 1

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR de conexión para polo {city_code}: {str(e)}")

print(f"📅 Buscando hoteles del {FECHA_ENTRADA} al {FECHA_SALIDA}")
print(f"🔁 Iniciando consulta para {len(POLOS)} polos")
print("═══════════════════════════════════════════════════════════════════════")

for polo in POLOS:
    consultar_hoteles_por_polo(polo)

# Resumen final
print("\n📊 RESUMEN FINAL POR POLO")
print("═══════════════════════════════════════════════════════════════════════")
total_hoteles_global = 0
total_nombres_repetidos = 0

for polo, hoteles_info in resumen_por_polo.items():
    total = len(hoteles_info)
    nombres = [h[0] for h in hoteles_info]
    repetidos = [nombre for nombre, count in Counter(nombres).items() if count > 1]

    print(f"🌍 Polo: {polo}")
    print(f"🏨 Hoteles disponibles: {total}")
    print(f"🔁 Nombres repetidos: {len(repetidos)}")
    total_hoteles_global += total
    total_nombres_repetidos += len(repetidos)

    if repetidos:
        for nombre in repetidos:
            print(f"  🔹 {nombre}")
            for h in hoteles_info:
                if h[0] == nombre:
                    print(f"     ↳ Código: {h[1]} | Precio: {h[2]:.2f} {h[3]}")
    print("───────────────────────────────────────────────────────────────────────")

print("📈 TOTALES GLOBALES")
print("═══════════════════════════════════════════════════════════════════════")
print(f"📌 Total polos analizados:        {len(resumen_por_polo)}")
print(f"🏨 Total hoteles disponibles:     {total_hoteles_global}")
print(f"🔁 Total nombres repetidos:       {total_nombres_repetidos}")
print("═══════════════════════════════════════════════════════════════════════\n")

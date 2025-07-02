import requests
import csv
import os
from lxml import etree
from datetime import datetime

# === Configuración ===
URL_PRODUCT = "http://api.1way2italy.it/service/test/v10/otaservice/hotelproduct"
URL_DETAIL = "http://api.1way2italy.it/service/test/v10/otaservice/hoteldescriptiveinfo"
HEADERS = {"Content-Type": "application/xml"}
PASSWORD = "Gmh3S246t987$"
CHAIN_CODE = "DISTALCU"

POLOS = [
    "BAR", "CAM", "CAY", "CYCZ", "CAYG", "CYL", "CAYP", "CSTM", "CGV", "CFG",
    "GIBC", "GRNM", "GUAQ", "PGUA", "HAV", "HOG", "LTNS", "MATZ", "QPD", "PLG",
    "SSSS", "SNTA", "STLQ", "SAA", "TRI", "VAR", "VIAL"
]

CAMPOS_CSV = [
    'destino', 'city_code', 'hotel_code', 'hotel_name', 'hotel_city_code',
    'area_id', 'giata_id', 'country_iso_code', 'country_name',
    'address', 'email', 'latitude', 'longitude', 'rating'
]

def obtener_hoteles(city_code):
    xml = f"""
    <OTA_HotelProductRQ xmlns="http://www.opentravel.org/OTA/2003/05" Target="Test" PrimaryLangID="en">
      <POS>
        <Source>
          <RequestorID ID="RUTA-US" MessagePassword="{PASSWORD}"/>
        </Source>
      </POS>
      <HotelProducts ChainCode="{CHAIN_CODE}" HotelCityCode="{city_code}"/>
    </OTA_HotelProductRQ>
    """
    try:
        response = requests.post(URL_PRODUCT, data=xml.encode("utf-8"), headers=HEADERS, timeout=15)
        response.raise_for_status()
        root = etree.fromstring(response.content)
        ns = {"ns": "http://www.opentravel.org/OTA/2003/05"}
        return root.findall(".//ns:HotelProduct", ns)
    except Exception as e:
        print(f"❌ Error al consultar hoteles en {city_code}: {e}")
        return []

def obtener_detalles_hotel(hotel_code):
    xml = f"""
    <OTA_HotelDescriptiveInfoRQ xmlns="http://www.opentravel.org/OTA/2003/05" Target="Test" Version="1.0">
      <POS>
        <Source>
          <RequestorID ID="RUTA-US" MessagePassword="{PASSWORD}" />
        </Source>
      </POS>
      <HotelDescriptiveInfos>
        <HotelDescriptiveInfo HotelCode="{hotel_code}" ChainCode="{CHAIN_CODE}" />
      </HotelDescriptiveInfos>
    </OTA_HotelDescriptiveInfoRQ>
    """
    try:
        response = requests.post(URL_DETAIL, data=xml.encode("utf-8"), headers=HEADERS, timeout=15)
        response.raise_for_status()
        root = etree.fromstring(response.content)
        ns = {"ns": "http://www.opentravel.org/OTA/2003/05"}

        direccion = root.findtext(".//ns:Address/ns:AddressLine", default="", namespaces=ns).strip()
        email = root.findtext(".//ns:Email", default="", namespaces=ns).strip()
        lat = root.findtext(".//ns:Latitude", default="", namespaces=ns).strip()
        lon = root.findtext(".//ns:Longitude", default="", namespaces=ns).strip()
        rating = root.findtext(".//ns:Award/ns:Rating", default="", namespaces=ns).strip()

        return direccion, email, lat, lon, rating
    except Exception as e:
        print(f"⚠️ No se pudo obtener detalles para {hotel_code}: {e}")
        return "", "", "", "", ""

def procesar_hoteles(city_code, hoteles):
    filas = []
    for hotel in hoteles:
        nombre = hotel.attrib.get("HotelName", "").strip()
        codigo = hotel.attrib.get("HotelCode", "").strip()
        ciudad = hotel.attrib.get("HotelCityCode", city_code)
        giata = hotel.attrib.get("GIATA", "")
        area_id = hotel.attrib.get("AreaID", "")

        # Consultar detalles
        address, email, lat, lon, rating = obtener_detalles_hotel(codigo)

        filas.append({
            'destino': area_id,
            'city_code': city_code,
            'hotel_code': codigo,
            'hotel_name': nombre,
            'hotel_city_code': ciudad,
            'area_id': area_id,
            'giata_id': giata,
            'country_iso_code': "CU",
            'country_name': "CUBA",
            'address': address,
            'email': email,
            'latitude': lat,
            'longitude': lon,
            'rating': rating
        })
    return filas

def guardar_csv(filas):
    fecha = datetime.now().strftime('%Y-%m-%d_%H-%M')
    nombre_archivo = f"HotelImportado_{fecha}.csv"
    with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
        writer.writeheader()
        writer.writerows(filas)
    print(f"\n📁 Archivo generado: {nombre_archivo} con {len(filas)} hoteles.")

def main():
    print("\n🏨 Obteniendo información completa de hoteles DISTAL...")
    todas_filas = []
    for city_code in POLOS:
        print(f"\n🔍 Consultando hoteles en {city_code}...")
        hoteles = obtener_hoteles(city_code)
        filas = procesar_hoteles(city_code, hoteles)
        todas_filas.extend(filas)
    guardar_csv(todas_filas)

if __name__ == "__main__":
    main()

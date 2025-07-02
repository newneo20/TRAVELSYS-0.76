import requests
import xml.etree.ElementTree as ET

# Lista de polos que deseas consultar
polos = [
    'BAR', 'CAM', 'CAY', 'CYCZ', 'CAYG', 'CYL', 'CAYP', 'CSTM', 'CGV', 'CFG',
    'GIBC', 'GRNM', 'GUAQ', 'PGUA', 'HAV', 'HOG', 'LTNS', 'MATZ', 'QPD', 'PLG',
    'SSSS', 'SNTA', 'STLQ', 'SAA', 'TRI', 'VAR', 'VIAL'
]

# URL y headers de la API
url = "http://api.1way2italy.it/service/test/v10/otaservice/hotelproduct"
headers = {"Content-Type": "application/xml"}

# Espacio de nombres XML
namespaces = {"ota": "http://www.opentravel.org/OTA/2003/05"}

print("\n📋 Consulta de hoteles por polo (Distal - catálogo general)")
print("════════════════════════════════════════════════════════════\n")

# Función para hacer la consulta
def consultar_hoteles_por_polo(city_code):
    xml_data = f"""
    <OTA_HotelProductRQ xmlns="http://www.opentravel.org/OTA/2003/05" Target="Test" PrimaryLangID="en">
        <POS>
            <Source>
                <RequestorID ID="RUTA-US" MessagePassword="Gmh3S246t987$"/>
            </Source>
        </POS>
        <HotelProducts ChainCode="DISTALCU" HotelCode="" HotelCityCode="{city_code}"/>
    </OTA_HotelProductRQ>
    """

    try:
        response = requests.post(url, data=xml_data.encode("utf-8"), headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ Error consultando polo {city_code}: {response.status_code}")
            return []

        # Parsear XML
        root = ET.fromstring(response.text)
        hoteles = root.findall(".//ota:HotelProduct", namespaces=namespaces)
        return [hotel.attrib.get("HotelName", "SIN NOMBRE") for hotel in hoteles]

    except Exception as e:
        print(f"❌ Excepción consultando {city_code}: {str(e)}")
        return []

# Iterar por cada polo
for polo in polos:
    print(f"🔍 Consultando polo: {polo}")
    hoteles = consultar_hoteles_por_polo(polo)
    print(f"🏨 {polo} ({len(hoteles)} hoteles)")
    for nombre in hoteles:
        print(f"   - {nombre}")
    print()

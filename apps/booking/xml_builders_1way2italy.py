# apps/booking/xml_builders_1way2italy.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
import requests

def build_hotel_avail_xml(hotel_code, fecha_inicio, fecha_fin, datos_habs):
    guest_counts_xml = ""
    for idx, hab in enumerate(datos_habs, start=1):
        adultos = hab.get('adultos', 0)
        ninos = hab.get('ninos', 0)
        guest_counts_xml += f'<GuestCount Age="30" Count="{adultos}"/>'
        if ninos > 0:
            guest_counts_xml += f'<GuestCount Age="10" Count="{ninos}"/>'

    xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<OTA_HotelAvailRQ xmlns="http://www.opentravel.org/OTA/2003/05"
                  Target="Test"
                  PrimaryLangID="en"
                  OnRequestInd="true"
                  MarketCountryCode="us">
  <POS>
    <Source>
      <RequestorID ID="RUTA-US" MessagePassword="Gmh3S246t987$"/>
    </Source>
  </POS>
  <AvailRequestSegments>
    <AvailRequestSegment>
      <HotelSearchCriteria>
        <Criterion>
          <HotelRef ChainCode="DISTALCU" HotelCode="{hotel_code}"/>
        </Criterion>
      </HotelSearchCriteria>
      <StayDateRange Start="{fecha_inicio}" End="{fecha_fin}"/>
      <RoomStayCandidates>
        <RoomStayCandidate Quantity="1" RPH="01">
          <GuestCounts>{guest_counts_xml}</GuestCounts>
          <RatePlanCandidates>
            <RatePlanCandidate CurrencyCode="USD"/>
          </RatePlanCandidates>
        </RoomStayCandidate>
      </RoomStayCandidates>
    </AvailRequestSegment>
  </AvailRequestSegments>
</OTA_HotelAvailRQ>"""
    return xml_data

  
def build_booking_xml(reserva, habitaciones, pasajeros):
    """
    Construye el XML completo HotelBookingRQ según OTA 2003.05 para Distal.
    """

    NS = "http://www.opentravel.org/OTA/2003/05"
    ET.register_namespace("", NS)

    root = ET.Element("{%s}OTA_HotelBookingRQ" % NS, {
        "Target": "Test",
        "Version": "1.0"
    })

    # POS - Credenciales
    pos = ET.SubElement(root, "POS")
    source = ET.SubElement(pos, "Source")
    requestor = ET.SubElement(source, "RequestorID", {
        "ID": "RUTA-US",
        "MessagePassword": "Gmh3S246t987$"
    })

    # HotelReservations
    hotel_res = ET.SubElement(root, "HotelReservations")
    hotel_reservation = ET.SubElement(hotel_res, "HotelReservation", {"CreateDateTime": datetime.utcnow().isoformat()})

    # RoomStays
    room_stays = ET.SubElement(hotel_reservation, "RoomStays")

    for idx, hab in enumerate(habitaciones, start=1):
        room_stay = ET.SubElement(room_stays, "RoomStay")

        # BasicPropertyInfo (ajustado)
        ET.SubElement(room_stay, "BasicPropertyInfo", {
            "HotelCode": reserva.hotel_importado.hotel_code,
            "ChainCode": "DISTALCU",
            "HotelCityCode": reserva.hotel_importado.destino or ""
        })

        # RoomTypes
        room_types = ET.SubElement(room_stay, "RoomTypes")
        ET.SubElement(room_types, "RoomType", {
            "RoomTypeCode": hab['opcion'].get('RoomTypeCode', ''),
            "RoomTypeName": hab['opcion'].get('nombre', '')
        })

        # RatePlans
        rate_plans = ET.SubElement(room_stay, "RatePlans")
        ET.SubElement(rate_plans, "RatePlan", {
            "RatePlanCode": hab['opcion'].get('RatePlanCode', ''),
            "MealPlan": hab['opcion'].get('MealPlan', '')
        })

        # GuestCounts
        guest_counts = ET.SubElement(room_stay, "GuestCounts")
        ET.SubElement(guest_counts, "GuestCount", {"Age": "30", "Count": str(hab['adultos'])})
        if hab['ninos'] > 0:
            ET.SubElement(guest_counts, "GuestCount", {"Age": "10", "Count": str(hab['ninos'])})

        # TimeSpan (Fechas)
        fechas_split = hab['fechas_viaje'].split(" - ")
        ET.SubElement(room_stay, "TimeSpan", {
            "Start": fechas_split[0],
            "End": fechas_split[1]
        })

        # Total Amount
        ET.SubElement(room_stay, "Total", {
            "AmountAfterTax": str(hab['opcion']['precio_cliente']),
            "CurrencyCode": hab['opcion']['moneda']
        })

    # Customer
    customer = ET.SubElement(hotel_reservation, "Customer")
    profile = ET.SubElement(customer, "Profile")
    primary = ET.SubElement(profile, "CustomerInfo")

    primer_adulto = pasajeros[0]

    ET.SubElement(primary, "PersonName").text = primer_adulto.nombre
    ET.SubElement(primary, "Telephone").text = primer_adulto.telefono or ''
    ET.SubElement(primary, "Email").text = primer_adulto.email or ''

    # Guarantee
    guarantee = ET.SubElement(hotel_reservation, "Guarantee")
    ET.SubElement(guarantee, "GuaranteeType").text = "PrePay"

    # ResGlobalInfo
    res_info = ET.SubElement(hotel_reservation, "ResGlobalInfo")
    ET.SubElement(res_info, "SpecialRequest").text = reserva.notas or ''

    # Pretty XML
    xml_string = ET.tostring(root, encoding="utf-8")
    parsed = minidom.parseString(xml_string)
    pretty_xml = parsed.toprettyxml(indent="  ")

    return pretty_xml  
  
def enviar_booking_api(xml_string):
    """
    Envía el BookingRQ al endpoint de reservas de 1way2italy.
    Retorna el resultado de la API: bookingID, success, errorMessage.
    """

    # 🚩 IMPORTANTE: cuando Michele nos confirme, actualizamos el endpoint si es diferente
    endpoint = "http://api.1way2italy.it/service/test/v10/otaservice/hotelbooking"

    headers = {
        "Content-Type": "application/xml"
    }

    try:
        response = requests.post(endpoint, data=xml_string.encode("utf-8"), headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Fallo al enviar el BookingRQ: {e}")
        return None, False, str(e)

    # ✅ Ahora parseamos la respuesta (muy básica por ahora, luego la refinamos)
    import xml.etree.ElementTree as ET
    ns = {'ns': 'http://www.opentravel.org/OTA/2003/05'}
    root = ET.fromstring(response.content)

    booking_id = None
    try:
        booking_id = root.find('.//ns:HotelReservationID', ns).get('ResID_Value')
        print(f"[OK] Reserva confirmada con BookingID: {booking_id}")
        return booking_id, True, None
    except Exception as e:
        print(f"[WARN] No se encontró BookingID en la respuesta: {e}")
        return None, False, "Respuesta sin BookingID"
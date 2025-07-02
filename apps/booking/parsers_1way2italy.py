import xml.etree.ElementTree as ET
from decimal import Decimal

def parse_hotel_avail_rs(xml_response):
    ns = {'ns': 'http://www.opentravel.org/OTA/2003/05'}
    root = ET.fromstring(xml_response)

    # Extraer Info del Hotel
    basic = root.find('.//ns:BasicPropertyInfo', ns)
    hotel_info = {
        'HotelCode': basic.get('HotelCode'),
        'HotelName': basic.get('HotelName'),
        'HotelCityCode': basic.get('HotelCityCode'),
        'ChainCode': basic.get('ChainCode'),
        'Rating': basic.find('ns:Award', ns).get('Rating') if basic.find('ns:Award', ns) is not None else None,
        'Latitude': basic.find('ns:Position', ns).get('Latitude') if basic.find('ns:Position', ns) is not None else None,
        'Longitude': basic.find('ns:Position', ns).get('Longitude') if basic.find('ns:Position', ns) is not None else None,
    }

    # Dirección
    address_el = basic.find('ns:Address', ns)
    if address_el is not None:
        hotel_info['AddressLines'] = [el.text for el in address_el.findall('ns:AddressLine', ns) if el.text]
        hotel_info['CityName'] = address_el.findtext('ns:CityName', default='', namespaces=ns)
        hotel_info['PostalCode'] = address_el.findtext('ns:PostalCode', default='', namespaces=ns)
        state = address_el.find('ns:StateProv', ns)
        hotel_info['StateProv'] = state.get('StateCode') if state is not None else ''
        country = address_el.find('ns:CountryName', ns)
        hotel_info['Country'] = country.get('Code') if country is not None else ''

    # Imágenes
    hotel_info['Images'] = list({el.text for el in root.findall('.//ns:ImageItem/ns:ImageFormat/ns:URL', ns) if el.text})

    # Notas y Servicios
    hotel_info['Notes'] = [
        {'SourceID': el.get('SourceID'), 'Text': el.findtext('ns:Description', default='', namespaces=ns).strip()}
        for el in root.findall('.//ns:TextItem', ns)
    ]
    hotel_info['Services'] = [
        {'Code': el.get('Code'), 'Description': el.findtext('ns:DescriptiveText', default='', namespaces=ns)}
        for el in root.findall('.//ns:Services/ns:Service', ns)
    ]

    # Habitaciones
    habitaciones = []
    for roomstay in root.findall('.//ns:RoomStay', ns):
        # Room Info
        roomtype_el = roomstay.find('.//ns:RoomType', ns)
        room_desc_el = roomstay.find('.//ns:RoomType/ns:RoomDescription/ns:Text', ns)
        room_type_code = roomtype_el.get('RoomTypeCode') if roomtype_el is not None else ''
        room_type_name = roomtype_el.get('RoomTypeName') if roomtype_el is not None else ''
        desc = room_desc_el.text if room_desc_el is not None else ''

        # Fallback inteligente para el nombre
        nombre = room_type_name or desc or '—'

        # Rate Plan
        rateplan_el = roomstay.find('.//ns:RatePlan', ns)
        rate_plan_code = rateplan_el.get('RatePlanCode') if rateplan_el is not None else ''
        meal_plan = rateplan_el.get('MealPlan') if rateplan_el is not None else ''

        # Precio
        total_el = roomstay.find('.//ns:Total', ns)
        price = Decimal(total_el.get('AmountAfterTax', '0')) if total_el is not None else Decimal('0.00')
        currency = total_el.get('CurrencyCode', '') if total_el is not None else ''

        # Booking Code
        booking_code = ''
        roomrate_el = roomstay.find('.//ns:RoomRate', ns)
        if roomrate_el is not None:
            booking_code = roomrate_el.get('BookingCode', '')

        # Cancel Policies
        cancel_policy_el = roomstay.find('.//ns:CancelPenalties', ns)
        cancel_policy = None
        if cancel_policy_el is not None:
            penalty = cancel_policy_el.find('.//ns:CancelPenalty', ns)
            if penalty is not None:
                deadline = penalty.find('.//ns:Deadline', ns)
                cancel_policy = {
                    'Deadline': deadline.get('AbsoluteDeadline') if deadline is not None else '',
                    'PenaltyDescription': penalty.findtext('.//ns:PenaltyDescription/ns:Text', default='', namespaces=ns)
                }

        # Booking Rules (Release)
        booking_rules_el = roomstay.find('.//ns:BookingRules', ns)
        release_days = None
        if booking_rules_el is not None:
            rule = booking_rules_el.find('.//ns:BookingRule', ns)
            if rule is not None:
                release = rule.find('.//ns:CancelPenalty/ns:Deadline', ns)
                if release is not None:
                    release_days = release.get('OffsetTimeUnit') + ' ' + release.get('OffsetUnitMultiplier') if release.get('OffsetTimeUnit') else ''

        habitaciones.append({
            'RoomTypeCode': room_type_code,
            'RoomTypeName': room_type_name,
            'Description': desc,
            'NombreFinal': nombre,
            'RatePlanCode': rate_plan_code,
            'MealPlan': meal_plan,
            'Price': float(price),
            'Currency': currency,
            'CancelPolicy': cancel_policy,
            'Release': release_days,
            'BookingCode': booking_code  # ✅ NUEVO
        })

    return {
        'HotelInfo': hotel_info,
        'Habitaciones': habitaciones
    }

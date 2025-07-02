
import pandas as pd # type: ignore
import os
import django # type: ignore

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from backoffice.models import Hotel, PoloTuristico, CadenaHotelera, Proveedor, Oferta, Habitacion, HotelSetting

# Función para solicitar confirmación del usuario
def solicitar_confirmacion(mensaje):
    respuesta = input(f"{mensaje} (s/n): ")
    return respuesta.lower() == 's'

# Cargar los archivos de Excel
file1_path = 'doc_informacion_hoteles_y_detalle_habitaciones.xlsx'
file2_path = 'doc_plantilla_ofertas_hoteles.xlsx'
df_file1 = pd.read_excel(file1_path)
df_file2 = pd.read_excel(file2_path)

# Función auxiliar para corregir el tipo de habitación
def corregir_tipo_habitacion(tipo_incorrecto, tipos_correctos):
    # Esta función podría implementarse para mapear los tipos incorrectos a los correctos
    # Por simplicidad, si hay un solo tipo correcto, lo usamos; si hay varios, podrías implementar una lógica adicional
    if len(tipos_correctos) == 1:
        return next(iter(tipos_correctos))
    else:
        # Aquí podrías implementar reglas adicionales para mapear nombres similares
        # Por ejemplo, usar una función de similitud de strings
        return tipo_incorrecto  # Por ahora, no se cambia



# Paso 1: Verificar los nombres de los hoteles en ambos archivos
print('---------------------------------------------------------------')
if solicitar_confirmacion("¿Deseas verificar los nombres de los hoteles en ambos archivos?"):
    # Filtrar valores solo de tipo string para evitar problemas de comparación
    hotels_file1 = [hotel for hotel in df_file1['Hotel'].dropna().unique() if isinstance(hotel, str)]
    hotels_file2 = [hotel for hotel in df_file2['Nombre del Hotel'].dropna().unique() if isinstance(hotel, str)]

    matching_hotels = sorted(set(hotels_file1).intersection(set(hotels_file2)))
    non_matching_hotels_file1 = sorted(set(hotels_file1) - set(matching_hotels))
    non_matching_hotels_file2 = sorted(set(hotels_file2) - set(matching_hotels))

    print(f"\nHoteles que coinciden ({len(matching_hotels)}):")
    for hotel in matching_hotels:
        print(f"- {hotel}")
        
    if non_matching_hotels_file1 or non_matching_hotels_file2:
        print(f"\nHoteles no coincidentes en el archivo 1 ({len(non_matching_hotels_file1)}):")
        for hotel in non_matching_hotels_file1:
            print(f"- {hotel}")
        print(f"\nHoteles no coincidentes en el archivo 2 ({len(non_matching_hotels_file2)}):")
        for hotel in non_matching_hotels_file2:
            print(f"- {hotel}")
            
        # Paso 1b: Quitar espacios finales en nombres de hoteles en ambos archivos
        if solicitar_confirmacion("¿Deseas eliminar los espacios en blanco finales en nombres de hoteles en ambos archivos?"):
            # Contador de correcciones realizadas
            corrections_file1 = df_file1['Hotel'].apply(lambda x: isinstance(x, str) and x.endswith(" ")).sum()
            corrections_file2 = df_file2['Nombre del Hotel'].apply(lambda x: isinstance(x, str) and x.endswith(" ")).sum()
            
            # Eliminar espacios finales y actualizar
            df_file1['Hotel'] = df_file1['Hotel'].apply(lambda x: x.rstrip() if isinstance(x, str) else x)
            df_file2['Nombre del Hotel'] = df_file2['Nombre del Hotel'].apply(lambda x: x.rstrip() if isinstance(x, str) else x)
            
            # Guardar los archivos corregidos
            df_file1.to_excel(file1_path, index=False)
            df_file2.to_excel(file2_path, index=False)
            
            print(f"Se eliminaron espacios finales en {corrections_file1} hoteles en el archivo 1.")
            print(f"Se eliminaron espacios finales en {corrections_file2} hoteles en el archivo 2.")
    else:
        print("\n.....TODOS LOS NOMBRES DE HOTELES COINCIDEN EN LOS DOS FICHEROS.....")
        
    # Paso 2: Ajustar los tipos de habitaciones por hotel
    if solicitar_confirmacion("¿Deseas verificar y ajustar los tipos de habitaciones por hotel en ambos archivos?"):
        # Primero, eliminar espacios en blanco finales en los tipos de habitaciones en ambos archivos
        df_file1['Tipo Habitación'] = df_file1['Tipo Habitación'].apply(lambda x: x.rstrip() if isinstance(x, str) else x)
        df_file2['Tipo Habitacion'] = df_file2['Tipo Habitacion'].apply(lambda x: x.rstrip() if isinstance(x, str) else x)
        
        # Guardar los archivos corregidos
        df_file1.to_excel(file1_path, index=False)
        df_file2.to_excel(file2_path, index=False)
        
        # Crear un diccionario de hotel a conjunto de tipos de habitación en cada archivo
        room_types_file1 = df_file1.groupby('Hotel')['Tipo Habitación'].apply(lambda x: set(x.dropna().unique()))
        room_types_file2 = df_file2.groupby('Nombre del Hotel')['Tipo Habitacion'].apply(lambda x: set(x.dropna().unique()))
        
        # Para cada hotel que coincida, comparar los tipos de habitación
        for hotel in matching_hotels:
            types_file1 = room_types_file1.get(hotel, set())
            types_file2 = room_types_file2.get(hotel, set())
            
            matching_types = types_file1.intersection(types_file2)
            non_matching_types_file1 = types_file1 - matching_types
            non_matching_types_file2 = types_file2 - matching_types
            
            if non_matching_types_file1 or non_matching_types_file2:
                print(f"\nTipos de habitación no coincidentes para el hotel '{hotel}':")
                if non_matching_types_file1:
                    print(f" - En archivo 1 pero no en archivo 2: {', '.join(non_matching_types_file1)}")
                if non_matching_types_file2:
                    print(f" - En archivo 2 pero no en archivo 1: {', '.join(non_matching_types_file2)}")
                
                # Opcional: Ajustar los tipos de habitación en archivo 2 para que coincidan con archivo 1
                if solicitar_confirmacion(f"¿Deseas ajustar los tipos de habitación en archivo 2 para el hotel '{hotel}' para que coincidan con archivo 1?"):
                    # Encontrar las filas en archivo 2 que corresponden al hotel y tipos de habitación no coincidentes
                    mask = (df_file2['Nombre del Hotel'] == hotel) & (df_file2['Tipo Habitacion'].isin(non_matching_types_file2))
                    # Reemplazar los tipos de habitación no coincidentes por el tipo correspondiente en archivo 1
                    # Aquí asumimos que los nombres deberían ser los de archivo 1
                    # Podrías implementar una lógica más compleja si es necesario
                    df_file2.loc[mask, 'Tipo Habitacion'] = df_file2.loc[mask, 'Tipo Habitacion'].apply(lambda x: corregir_tipo_habitacion(x, types_file1))
                    
                    # Guardar los cambios en archivo 2
                    df_file2.to_excel(file2_path, index=False)
                    print(f"Se ajustaron los tipos de habitación para el hotel '{hotel}' en archivo 2.")
            else:
                print(f"\nTodos los tipos de habitación para el hotel '{hotel}' coinciden en ambos archivos.")

# Paso 2: Transformar las fechas en el archivo 2 en las columnas 'Temporada' y 'Booking Window'
print('---------------------------------------------------------------')
if solicitar_confirmacion("¿Deseas transformar las fechas en las columnas 'Temporada' y 'Booking Window'?"):
    # Función envolvente para definir 'linea' como nonlocal
    def transformar_fechas_con_contador():
        linea = 1  # Iniciar el contador de líneas
        def transformar_fecha(fecha_str):     
            nonlocal linea  # Permitir modificar 'linea' dentro de la función interna
            # Verificar si el valor es una cadena antes de intentar dividirlo
            if isinstance(fecha_str, str):
                try:
                    start_date, end_date = fecha_str.split(" - ")
                    start_date = pd.to_datetime(start_date, format='%d-%m-%Y').strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(end_date, format='%d-%m-%Y').strftime('%Y-%m-%d')
                    print(f"Línea {linea}, Transformación correcta. '{start_date} - {end_date}'")
                    linea += 1
                    return f"{start_date} - {end_date}"
                except Exception as e:
                    print(f"Línea {linea}, Error transformando fecha '{fecha_str}': {e}")
                    linea += 1 
                    return fecha_str
            else:
                # Imprimir el valor que no es una cadena para depuración            
                print(f"Línea {linea}, Valor no procesado (no es una cadena): {fecha_str}")
                linea += 1
                return fecha_str

        # Aplicar la función de transformación
        df_file2['Temporada'] = df_file2['Temporada'].apply(transformar_fecha)
        linea = 1 
        df_file2['Booking Window'] = df_file2['Booking Window'].apply(transformar_fecha)

    # Ejecutar la función envolvente
    transformar_fechas_con_contador()

    # Guardar los cambios en el documento 2
    df_file2.to_excel(file2_path, index=False)
    print(f"Los cambios han sido guardados en '{file2_path}'.")

# Paso 3: Importar los hoteles del primer archivo al modelo Django
print('---------------------------------------------------------------')
if solicitar_confirmacion("¿Deseas importar los hoteles del archivo?"):
    def obtener_valor_fila(row, columna):
        """Obtiene el valor de una columna específica de la fila. Retorna None si el valor es NaN."""
        valor = row.get(columna, None)
        return valor if pd.notna(valor) else None

    index = 0
    while index < len(df_file1):
        row = df_file1.iloc[index]
        print('-------------------------------------------')
        print('-------------------------------------------')
        print(f"Procesando fila {index}: {row.to_dict()}")  # Debug: Muestra la fila actual
        hotel_nombre = obtener_valor_fila(row, 'Hotel')

        if hotel_nombre:  # Procesar solo si la fila tiene un hotel
            print(f"Procesando hotel: {hotel_nombre}")  # Debug: Nombre del hotel
            try:
                # Crear o actualizar el hotel
                hotel_instance, created = Hotel.objects.update_or_create(
                    hotel_nombre=hotel_nombre,
                    defaults={
                        'polo_turistico': PoloTuristico.objects.get_or_create(
                            nombre=obtener_valor_fila(row, 'Polo Turistico')
                        )[0],
                        'cadena_hotelera': CadenaHotelera.objects.get_or_create(
                            nombre=obtener_valor_fila(row, 'Cadena Hotelera')
                        )[0],
                        'proveedor': Proveedor.objects.get_or_create(
                            nombre=obtener_valor_fila(row, 'Proveedor')
                        )[0],
                        'descripcion_hotel': obtener_valor_fila(row, 'Descripcion'),
                        'direccion': obtener_valor_fila(row, 'Direccion'),
                        'fee': obtener_valor_fila(row, 'Fee'),
                        'telefono': obtener_valor_fila(row, 'TELEFONO'),
                        'tipo_fee': obtener_valor_fila(row, 'Tipo de fee'),
                        'foto_hotel': obtener_valor_fila(row, 'Foto'),
                        'categoria': obtener_valor_fila(row, 'Categoria'),
                        'plan_alimenticio': obtener_valor_fila(row, 'Plan alimenticio'),
                        'checkin': obtener_valor_fila(row, 'Check in'),
                        'checkout': obtener_valor_fila(row, 'Check out'),
                        'solo_adultos': bool(obtener_valor_fila(row, 'Solo Adultos')),
                    }
                )
                action = "creado" if created else "actualizado"
                print(f"Hotel: {hotel_instance.hotel_nombre}, {action} satisfactoriamente.")

                # Crear o actualizar la configuración del hotel
                HotelSetting.objects.update_or_create(
                    hotel=hotel_instance,
                    defaults={
                        'edad_limite_nino': int(obtener_valor_fila(row, 'Edad limite nino') or 0),
                        'edad_limite_infante': int(obtener_valor_fila(row, 'Edad limite infante') or 0),
                        'cantidad_noches': int(obtener_valor_fila(row, 'Cantidad Noches') or 1),
                    }
                )
                print(f"Configuración para el hotel '{hotel_instance.hotel_nombre}' creada o actualizada con éxito.")

                # Verificar si la fila contiene información de una habitación
                tipo_habitacion = obtener_valor_fila(row, 'Tipo Habitación')
                if tipo_habitacion:
                    print(f"Creando habitación '{tipo_habitacion}' para el hotel '{hotel_instance.hotel_nombre}'.")
                    Habitacion.objects.update_or_create(
                        hotel=hotel_instance,
                        tipo=tipo_habitacion,
                        defaults={
                            'descripcion': obtener_valor_fila(row, 'Descripción') or "",
                            'foto': obtener_valor_fila(row, 'Foto') or "",
                            'adultos': int(obtener_valor_fila(row, 'Adultos') or 0),
                            'ninos': int(obtener_valor_fila(row, 'Niños') or 0),
                            'max_capacidad': int(obtener_valor_fila(row, 'Máxima Capacidad') or 0),
                            'min_capacidad': int(obtener_valor_fila(row, 'Mínima Capacidad') or 0),
                            'admite_3_con_1': bool(obtener_valor_fila(row, '3+1')),
                            'solo_adultos': bool(obtener_valor_fila(row, 'Solo adultos')),
                        }
                    )
                    print(f"Habitación: {tipo_habitacion}, creada satisfactoriamente para el hotel '{hotel_instance.hotel_nombre}'.")

                # Procesar las habitaciones asociadas al hotel (filas posteriores)
                index += 1
                while index < len(df_file1):
                    row = df_file1.iloc[index]
                    print(f"Procesando fila {index} para habitaciones: {row.to_dict()}")  # Debug de la fila actual

                    # Verificar si la fila está completamente en blanco
                    if row.isnull().all():
                        print(f"Fila {index} está completamente en blanco. Saltando al siguiente hotel.")
                        break  # Detener el bucle si se encuentra una fila en blanco

                    tipo_habitacion = obtener_valor_fila(row, 'Tipo Habitación')
                    if tipo_habitacion:
                        print(f"Creando habitación '{tipo_habitacion}' para el hotel '{hotel_instance.hotel_nombre}'.")
                        Habitacion.objects.update_or_create(
                            hotel=hotel_instance,
                            tipo=tipo_habitacion,
                            defaults={
                                'descripcion': obtener_valor_fila(row, 'Descripción') or "",
                                'foto': obtener_valor_fila(row, 'Foto') or "",
                                'adultos': int(obtener_valor_fila(row, 'Adultos') or 0),
                                'ninos': int(obtener_valor_fila(row, 'Niños') or 0),
                                'max_capacidad': int(obtener_valor_fila(row, 'Máxima Capacidad') or 0),
                                'min_capacidad': int(obtener_valor_fila(row, 'Mínima Capacidad') or 0),
                                'admite_3_con_1': bool(obtener_valor_fila(row, '3+1')),
                                'solo_adultos': bool(obtener_valor_fila(row, 'Solo adultos')),
                            }
                        )
                        print(f"Habitación: {tipo_habitacion}, creada satisfactoriamente para el hotel '{hotel_instance.hotel_nombre}'.")
                    else:
                        print(f"Fila {index} ignorada: no contiene información válida de habitación.")

                    index += 1

                # Saltar filas en blanco hasta el siguiente hotel
                while index < len(df_file1) and df_file1.iloc[index].isnull().all():
                    print(f"Saltando fila en blanco en índice {index}.")
                    index += 1

            except Exception as e:
                print(f"Error al procesar el hotel '{hotel_nombre}': {e}")
        else:
            print(f"Fila {index} no tiene nombre de hotel. Saltando.")
            index += 1












# Paso 4: Importar ofertas del segundo archivo
print('---------------------------------------------------------------')
if solicitar_confirmacion("¿Deseas importar las ofertas del segundo archivo?"):
    current_hotel_name = None  # Variable para almacenar el nombre del hotel actual
    cantidad_temporadas = None  # Almacena la cantidad de temporadas
    cantidad_habitaciones = None  # Almacena la cantidad de habitaciones
    categoria = None  # Almacena la categoría
    
    for index, row in df_file2.iterrows():
        # Detectar una nueva sección de hotel cuando hay un nombre en la columna "Nombre del Hotel"
        if pd.notna(row.get('Nombre del Hotel')):  # Verificar si hay un valor no nulo en la columna
            current_hotel_name = row.get('Nombre del Hotel')
            cantidad_temporadas = row.get('Cantidad de Temporadas')
            cantidad_habitaciones = row.get('Cantidad de Habitaciones')
            categoria = row.get('Categoria')
            print(f"Detectada nueva sección de hotel: {current_hotel_name}")
            print(f"Cantidad de Temporadas: {cantidad_temporadas}, Cantidad de Habitaciones: {cantidad_habitaciones}, Categoría: {categoria}")
        
        # Solo proceder si tenemos un hotel válido al cual asociar la oferta
        if current_hotel_name:
            try:
                # Buscar el hotel en la base de datos
                hotel = Hotel.objects.get(hotel_nombre=current_hotel_name)
                
                # Crear la oferta para el hotel encontrado
                Oferta.objects.create(
                    hotel=hotel,
                    disponible=row.get('Disponible', True),
                    codigo=row.get('Codigo'),
                    tipo_habitacion=row.get('Tipo Habitacion'),
                    temporada=row.get('Temporada'),
                    booking_window=row.get('Booking Window'),
                    sencilla=row.get('Sencilla'),
                    doble=row.get('Doble'),
                    triple=row.get('Triple'),
                    primer_nino=row.get('Primer Niño'),
                    segundo_nino=row.get('Segundo Niño'),
                    un_adulto_con_ninos=row.get('Un Adulto Con Ninos'),
                    primer_nino_con_un_adulto=row.get('Primer Nino con 1 Adulto'),
                    segundo_nino_con_un_adulto=row.get('Segundo Nino con 1 Adulto'),
                    edad_nino=row.get('Edad Nino'),
                    edad_infante=row.get('Edad Infante'),
                    noches_minimas=row.get('Noches Minimas'),
                    cantidad_habitaciones=cantidad_habitaciones,  # Usar el valor almacenado
                    tipo_fee=row.get('Tipo Fee'),
                    fee_doble=row.get('Fee Doble'),
                    fee_triple=row.get('Fee Triple'),
                    fee_sencilla=row.get('Fee Sencilla'),
                    fee_primer_nino=row.get('Fee Primer Niño'),
                    fee_segundo_nino=row.get('Fee Segundo Niño'),
                )
                print(f"Oferta para el hotel '{current_hotel_name}' creada con éxito.")
                
            except Hotel.DoesNotExist:
                print(f"Hotel '{current_hotel_name}' no encontrado. Oferta no creada.")
            except Exception as e:
                print(f"Error al crear la oferta para el hotel '{current_hotel_name}': {e}")



print("Proceso de importación completado.")


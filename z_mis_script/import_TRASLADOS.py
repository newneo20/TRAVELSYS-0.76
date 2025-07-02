import os
import django
import pandas as pd

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')  # Reemplaza 'viajero_plus' con el nombre de tu proyecto
django.setup()

from backoffice.models import Transportista, Ubicacion, Vehiculo, Traslado

# Diccionario de capacidades mínimas y máximas por tipo de vehículo
capacidad_vehiculos = {
    'Micro 10 Plazas (4 a 8 pax)': (4, 8),
    'Bus 12-16 Plazas (9 a 14 pax)': (9, 14),
    'Bus 24-29 Plazas (15 a 22 pax)': (15, 22),
    'Ómnibus Protocolo': (1, 50),  # Asumir valores por defecto si no están claros
    'Ómnibus 34 Plazas (23-32 Pax)': (23, 32),
    'Ómnibus 44 Plazas (33-42 Pax)': (33, 42),
    'Ómnibus 48 Plazas (43-46 Pax)': (43, 46),
    'Auto estándar (1-2 Pax)': (1, 2),
    'Auto Lujo (1-3 Pax)': (1, 3),
    'Jeep (1-4 Pax)': (1, 4),
    'Micro (1-5 Pax)': (1, 5),
    'Microbús de 6-10 plazas (6-10 Pax)': (6, 10),
    'Minibús hasta 16 plazas (11-16 Pax)': (11, 16),
    'Minibús de 21-24 plazas (21-24 Pax)': (21, 24),
    'Ómnibus de 41-49 plazas (41-49 Pax)': (41, 49),
}

def cargar_datos_desde_excel():
    # Nombre del archivo Excel
    archivo = 'Traslados_MAYUSCULAS.xlsx'

    try:
        # Cargar los datos desde el archivo Excel
        datos = pd.read_excel(archivo)
        datos.rename(columns={'ORIGEN': 'Origen', 'DESTINO ': 'Destino'}, inplace=True)

        # Validar que las columnas necesarias estén presentes
        columnas_requeridas = ['Transportista', 'Origen', 'Destino'] + list(datos.columns[3:18])
        for columna in columnas_requeridas:
            if columna not in datos.columns:
                raise ValueError(f"La columna '{columna}' no se encuentra en el archivo Excel.")

        # Iterar por cada fila del archivo Excel
        for index, row in datos.iterrows():
            try:
                # Validar datos requeridos
                if pd.isnull(row['Origen']) or pd.isnull(row['Destino']):
                    print(f"Error en la fila {index + 1}: Datos faltantes en 'Origen' o 'Destino'")
                    continue

                # Obtener o crear el transportista
                transportista, _ = Transportista.objects.get_or_create(nombre=row['Transportista'])

                # Obtener o crear las ubicaciones de origen y destino
                origen, _ = Ubicacion.objects.get_or_create(nombre=row['Origen'])
                destino, _ = Ubicacion.objects.get_or_create(nombre=row['Destino'])

                # Iterar sobre columnas de tipo de vehículos
                for col in datos.columns[3:18]:  # Ajusta los índices según corresponda
                    if not pd.isnull(row[col]):  # Verificar que el costo no sea nulo
                        costo = row[col]

                        # Verificar si el costo es 0, no agregarlo
                        if costo == 0:
                            print(f"Fila {index + 1}: Costo 0 para el vehículo '{col.strip()}', se omite.")
                            continue

                        tipo_vehiculo = col.strip()
                        capacidades = capacidad_vehiculos.get(tipo_vehiculo, (1, 50))  # Valores predeterminados si no se encuentra

                        # Obtener o crear el vehículo, con capacidades mínimas y máximas dinámicas
                        vehiculo, _ = Vehiculo.objects.get_or_create(
                            tipo=tipo_vehiculo,
                            defaults={
                                'capacidad_min': capacidades[0],
                                'capacidad_max': capacidades[1]
                            }
                        )

                        # Crear o actualizar el traslado
                        traslado, creado = Traslado.objects.get_or_create(
                            transportista=transportista,
                            origen=origen,
                            destino=destino,
                            vehiculo=vehiculo,
                            defaults={
                                'costo': costo
                            }
                        )

                        # Mensaje según si el traslado fue creado o ya existía
                        if creado:
                            print(f"Traslado creado: {traslado}")
                        else:
                            print(f"Traslado ya existente: {traslado}")

            except Exception as e:
                print(f"Error en la fila {index + 1}: {e}")

    except FileNotFoundError:
        print(f"Error: El archivo '{archivo}' no se encuentra en el directorio.")
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")

if __name__ == '__main__':
    cargar_datos_desde_excel()

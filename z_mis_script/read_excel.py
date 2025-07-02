import os
import django
import pandas as pd

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from backoffice.models import Hotel, PoloTuristico, CadenaHotelera, Proveedor

# Nombre del archivo Excel
excel_file_name = 'TIPOS DE HABITACION POR HOTELES SISTEMA.xlsx'
df = pd.read_excel(excel_file_name, header=0)
df.dropna(how='all', inplace=True)
df.columns = df.columns.str.strip()

print("Nombres de las columnas en el archivo Excel después de limpiar:")
print(df.columns)

# Función para obtener valores de fila con verificación de NaN
def obtener_valor_fila(row, columna):
    valor = row.get(columna, None)
    return valor if pd.notna(valor) else None

# Iterar sobre las filas del DataFrame
for index, row in df.iterrows():
    hotel_nombre = obtener_valor_fila(row, 'Hotel')
    
    # Validación: asegurarse de que el nombre del hotel esté presente
    if hotel_nombre:
        try:
            # Crear o actualizar el hotel sin el campo de teléfono
            hotel_instance, created = Hotel.objects.update_or_create(
                hotel_nombre=hotel_nombre,
                defaults={
                    'polo_turistico': PoloTuristico.objects.get_or_create(nombre=obtener_valor_fila(row, 'Polo Turistico'))[0],
                    'cadena_hotelera': CadenaHotelera.objects.get_or_create(nombre=obtener_valor_fila(row, 'Cadena Hotelera'))[0],
                    'proveedor': Proveedor.objects.get_or_create(nombre=obtener_valor_fila(row, 'Proveedor'))[0],
                    'direccion': obtener_valor_fila(row, 'Direccion'),
                    
                    'fee': obtener_valor_fila(row, 'fee'),
                    'tipo_fee': obtener_valor_fila(row, 'Tipo de fee'),
                    'foto_hotel': obtener_valor_fila(row, 'Foto'),
                    
                    'categoria': obtener_valor_fila(row, 'Categoria'),
                    'plan_alimenticio': obtener_valor_fila(row, 'Plan alimenticio'),
                    'descripcion_hotel': obtener_valor_fila(row, 'Descripcion'),
                    'checkin': obtener_valor_fila(row, 'Check in'),
                    'checkout': obtener_valor_fila(row, 'Check out'),
                    'solo_adultos': bool(obtener_valor_fila(row, 'Solo Adultos')),
                }
            )
            action = "creado" if created else "actualizado"
            print(f"Hotel '{hotel_instance.hotel_nombre}' {action} con éxito.")
        except Exception as e:
            print(f"Error al crear o actualizar el hotel '{hotel_nombre}': {e}")
    else:
        # Mensaje para filas con datos incompletos
        print(f"Datos incompletos para el hotel en la fila {index + 2}: nombre='{hotel_nombre}'")

print("Finalizado.")

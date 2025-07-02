import pandas as pd
import os

# Obtener la ruta del archivo Excel desde la misma carpeta del script
current_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(current_dir, "plantilla_hoteles.xlsx")
output_file = os.path.join(current_dir, "plantilla_hoteles_OK.xlsx")

# Verificar que la ruta es correcta
print(f"Intentando abrir el archivo: {input_file}")

# Cargar el archivo Excel
try:
    df = pd.read_excel(input_file)
except FileNotFoundError:
    print("Error: El archivo no se encuentra en la ruta especificada.")
    exit(1)

# Función para transformar las fechas
def transformar_fecha(fecha):
    if pd.isna(fecha):
        return fecha  # Devolver la fecha si es NaN
    
    # Separar las fechas por ' - '
    fechas = fecha.split(' - ')
    fechas_transformadas = []
    for f in fechas:
        try:
            # Cambiar formato de día-mes-año a año-mes-día
            fecha_formateada = pd.to_datetime(f, dayfirst=True).strftime("%Y-%m-%d")
            fechas_transformadas.append(fecha_formateada)
        except ValueError:
            # Si la fecha no tiene el formato esperado, se deja igual
            fechas_transformadas.append(f)
    return ' - '.join(fechas_transformadas)

# Aplicar la transformación a las columnas H e I, verificando si existen
if 'Temporada' in df.columns:
    df['Temporada'] = df['Temporada'].astype(str).apply(transformar_fecha)
if 'Booking Window' in df.columns:
    df['Booking Window'] = df['Booking Window'].astype(str).apply(transformar_fecha)

# Guardar el archivo Excel con las fechas transformadas
df.to_excel(output_file, index=False)
print(f"Fechas transformadas y archivo guardado como {output_file}.")

import pandas as pd
import os
from colorama import Fore, Style, init

# Inicializar colorama para colores en consola
init(autoreset=True)

# Obtener la ruta del directorio donde está el script
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'Traslados.xlsx')

# Función para cargar el archivo Excel
def cargar_documento():
    if os.path.exists(file_path):
        print(Fore.GREEN + "Documento cargado correctamente desde:", file_path)
        return pd.ExcelFile(file_path)
    else:
        print(Fore.RED + "Error: No se encontró el archivo 'Traslados.xlsx' en el directorio actual.")
        return None

# Función para convertir a mayúsculas y contar cambios
def transformar_a_mayusculas():
    # Cargar el archivo
    excel_data = pd.read_excel(file_path, sheet_name=None)

    # Diccionario para almacenar el resumen de cambios
    resumen_cambios = {}

    for sheet_name, sheet_data in excel_data.items():
        cambios_por_columna = {}
        for col in sheet_data.columns:
            if sheet_data[col].dtype == 'object':  # Solo convertir columnas de tipo string
                original_count = sheet_data[col].nunique()
                sheet_data[col] = sheet_data[col].str.upper()
                new_count = sheet_data[col].nunique()
                cambios_por_columna[col] = new_count - original_count
        
        resumen_cambios[sheet_name] = cambios_por_columna
        excel_data[sheet_name] = sheet_data

    # Guardar el archivo modificado
    output_file_path = os.path.join(script_dir, "Traslados_MAYUSCULAS.xlsx")
    with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
        for sheet_name, sheet_data in excel_data.items():
            sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)

    print(Fore.YELLOW + f"Documento guardado como: {output_file_path}")

    # Mostrar resumen de cambios
    for sheet, cambios in resumen_cambios.items():
        print(Fore.CYAN + f"\nResumen de cambios en la hoja: {sheet}")
        for col, count in cambios.items():
            print(Fore.MAGENTA + f"   - Columna '{col}': {count} modificaciones.")

# Ejecutar el script
documento = cargar_documento()

if documento:
    transformar_a_mayusculas()
else:
    print(Fore.RED + "No se pudo procesar el documento.")

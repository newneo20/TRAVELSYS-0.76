import pandas as pd

# Ruta del archivo de entrada y salida
file_path = "Traslados.xlsx"  # Reemplázala con la ubicación real
output_file_path = "Traslados_OK.xlsx"  # Ruta del archivo corregido

# Definir el diccionario de reglas de sustitución
REGLAS_SUSTITUCION = {
    'AEPTO': 'AEROPUERTO',
    'GV': 'GUARDALAVACA',
    'GVACA': 'GUARDALAVACA',
    'H.': 'HOTELES',
    'HOT.': 'HOTELES',                
    'HTLES': 'HOTELES',
    'HTLS.': 'HOTELES',
    'HTLS': 'HOTELES',
    'PTO': 'PUNTO',
    'S SANTOS': 'SANCTI SPIRITUS',
    'STA': 'SANTA',
    'STGO': 'SANTIAGO',
    'STO': 'SANTO',    
    'GV-': 'GUARDALAVACA',
    'GVACA-': 'GUARDALAVACA',
    'GVACA': 'GUARDALAVACA',
    'PESQ': 'PESQUERO',
    'AEROPUERTO TERMINAL NO. 3': 'AEROPUERTO HABANA T3',
    'AEROPUERTO TERMINAL NO.5 (WAJAY)': 'AEROPUERTO HABANA T3',
    'AEROPUERTO SANTIAGO CUBA': 'AEROPUERTO SANTIAGO DE CUBA',
    'AEROPUERTO JOSE MARTI NO 1': 'AEROPUERTO HABANA T1',
    'AEROPUERTO JOSE MARTI NO 2': 'AEROPUERTO HABANA T2',
    'AEROPUERTO JOSE MARTI NO 3': 'AEROPUERTO HABANA T3',
    'JOSE MARTI NO.1 Y 2': 'AEROPUERTO HABANA T1 Y T2',
    'JOSE MARTI NO.5 (WAJAY)': 'AEROPUERTO HABANA T5 (WAJAY)',
    'AEROPUERTO JOSÉ MARTÍ': 'AEROPUERTO HABANA T1',
    'APTO MANZANILLO': 'AEROPUERTO MANZANILLO',
    'APTO SANTIAGO DE CUBA': 'AEROPUERTO SANTIAGO DE CUBA',
    'AEROPUERTO C. AVILA': 'AEROPUERTO CIEGO DE AVILA',
    'AEROPUERTO CIEGO DE ÁVILA': 'AEROPUERTO CIEGO DE AVILA',
    'AEROPUERTO TUNAS': 'AEROPUERTO LAS TUNAS',
    'SANTIAGO DE CUBA AEROPUERTO': 'AEROPUERTO SANTIAGO DE CUBA',
    'VARADERO AEROPUERTO': 'AEROPUERTO VARADERO',
    'CARISOL- CORALES': 'CARISOL LOS CORALES',
    'CIUDAD HABANA': 'LA HABANA',        
    'LAS TUNAS CIUDAD': 'LAS TUNAS',
    'PINAR DE RIO CIUDAD': 'PINAR DEL RIO',    
    'VILLA STO DOMINGO VIA BAYAMO': 'VILLA SANTO DOMINGO VIA BAYAMO',    
    'HOTEL CARISOL - CORALES': 'HOTEL CARISOL LOS CORALES',
    'H. SANTA. LUCIA': 'HOTELES SANTA LUCIA',
    'H. GUARDALAVACA.': 'HOTELES GUARDALAVACA',
    'HOTEL GUARDALAVACA / GUARDALAVACA': 'HOTELES GUARDALAVACA',
    'HOTEL JIBACOA': 'HOTELES JIBACOA',
    'HOTEL MORON / MORON': 'HOTEL MORON',
    'HOTELES CAMAGÜEY / CAMAGÜEY': 'HOTELES CAMAGUEY',
    'HOTELES CAYO COCO / CAYO COCO': 'HOTELES CAYO COCO',
    'HOTELES CAYO COCO / CAYO COCO (POR EL VIAL)': 'HOTELES CAYO COCO (POR EL VIAL)',
    'HOTELES CAYO GUILLERMO / CAYO GUILLERMO': 'HOTELES CAYO GUILLERMO',
    'HOTELES CAYO GUILLERMO / CAYO GUILLERMO (POR EL VIAL)': 'HOTELES CAYO GUILLERMO (POR EL VIAL)',
    'HOTELES CIEGO DE ÁVILA / CIEGO DE ÁVILA': 'HOTELES CIEGO DE ÁVILA',
    'HOTELES CIENFUEGOS / CIENFUEGOS': 'HOTELES CIENFUEGOS',
    'HOTELES GUARDALAVACA / GUARDALAVACA': 'HOTELES GUARDALAVACA',
    'HOTELES HABANA': 'HOTELES LA HABANA',
    'HOTELES HABANA (HABANA)': 'HOTELES LA HABANA',
    'HOTELES HABANA (VEDADO)': 'HOTELES LA HABANA',
    'HOTELES HABANA (PLAYA - VEDADO - H.VIEJA)': 'HOTELES LA HABANA',
    'HOTELES HABANA VIEJA': 'HOTELES LA HABANA',
    'HOTELES HOLGUIN / HOLGUIN': 'HOTELES HOLGUIN',
    'HOTELES LAS TUNAS / CIUDAD LAS TUNAS': 'HOTELES LAS TUNAS',
    'HOTELES MIRAMAR-PLAYA': 'HOTELES LA HABANA',
    'HOTEL MORÓN / MORÓN': 'HOTEL MORON',
    'HOTELES PINAR DEL RIO / PINAR DEL RIO': 'HOTELES PINAR DEL RIO',
    'HOTELES P. DEL RIO': 'HOTELES PINAR DEL RIO',
    'HOTELES PLAYAS DEL ESTE': 'HOTELES LA HABANA',
    'HOTELES PLAYA DEL ESTE': 'HOTELES LA HABANA',
    'HOTELES SANCTI SPÍRITUS / SANCTI SPÍRITUS': 'HOTELES SANCTI SPÍRITUS',
    'HOTELES S. SPIRITUS': 'HOTELES SANCTI SPÍRITUS',
    'HOTELES SANTA CLARA / SANTA CLARA': 'HOTELES SANTA CLARA',
    'HOTELES SANTA LUCÍA / SANTA LUCÍA': 'HOTELES SANTA LUCIA',
    'HOTELES SANTA LUCIA / SANTA LUCÍA': 'HOTELES SANTA LUCIA',
    'HOTELES SANTIAGO DE CUBA / SANTIAGO DE CUBA': 'HOTELES SANTIAGO DE CUBA',
    'HOTELES SANTIAGO': 'HOTELES SANTIAGO DE CUBA',
    'HTL MEMORIS JIBACOA': 'HOTELES MEMORIS JIBACOA',
    'HTL SANTIAGO DE CUBA': 'HOTELES SANTIAGO DE CUBA',        
    'Á': 'A',
    'É': 'E',
    'Í': 'I',
    'Ó': 'O',
    'Ú': 'U',
    'Ú': 'U'
    
}

def aplicar_reglas(lista, reglas):
    """Aplica las reglas de sustitución a una lista de cadenas."""
    lista_modificada = []
    for item in lista:
        for clave, valor in reglas.items():
            if clave in item:
                item = item.replace(clave, valor)
        lista_modificada.append(item)
    return lista_modificada

def procesar_traslados():
    # Cargar el archivo Excel
    df = pd.read_excel(file_path)

    # Limpiar los nombres de las columnas eliminando espacios extra
    df.columns = df.columns.str.strip()

    # Extraer las columnas ORIGEN y DESTINO en listas y convertirlas a mayúsculas
    lista_origen = [str(origen).upper() for origen in df["ORIGEN"].tolist()]
    lista_destino = [str(destino).upper() for destino in df["DESTINO"].tolist()]

    # Aplicar reglas de sustitución
    lista_origen = aplicar_reglas(lista_origen, REGLAS_SUSTITUCION)
    lista_destino = aplicar_reglas(lista_destino, REGLAS_SUSTITUCION)

    # Sobreescribir las columnas originales con los datos corregidos
    df["ORIGEN"] = lista_origen
    df["DESTINO"] = lista_destino

    # Guardar el archivo corregido
    df.to_excel(output_file_path, index=False)

    print(f"Archivo corregido guardado como: {output_file_path}")
    print("\nPrimeros 10 valores de ORIGEN corregidos:")
    print(lista_origen[:10])

    print("\nPrimeros 10 valores de DESTINO corregidos:")
    print(lista_destino[:10])

# Ejecutar la función
procesar_traslados()

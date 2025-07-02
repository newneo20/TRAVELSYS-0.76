import os
import sys
import django
import psycopg2
from psycopg2.extras import execute_values
import csv

# === Configurar entorno Django ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '../../'))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()

from apps.backoffice.models import Proveedor

# === Datos del proveedor DISTALCU ===
proveedor_data = {
    'nombre': 'DISTALCU',
    'correo1': 'm.rombaldoni@datagest.it',
    'correo2': 'support@1way2italy.i',
    'correo3': 'm.rombaldoni@datagest.it',
    'telefono': '54266480',
    'detalles_cuenta_bancaria': None,
    'direccion': 'https://www.distalcaribe.com/es/home',
    'tipo': 'hoteles',
    'fee_adultos': 6,
    'fee_ninos': 3,
    'fee_noche': None,
}

proveedor, creado = Proveedor.objects.get_or_create(
    nombre=proveedor_data['nombre'],
    defaults=proveedor_data
)

if creado:
    print(f"✅ Proveedor '{proveedor.nombre}' creado.")
else:
    print(f"ℹ️ Proveedor '{proveedor.nombre}' ya existía.")

# === Ruta al archivo CSV ===
HOTEL_CSV = os.path.join(BASE_DIR, 'z_mis_script/000/HotelImportado.csv')

# === Config DB para psycopg2 ===
DB_CONFIG = {
    'dbname': 'db_build',
    'user': 'newneo20',
    'password': '0123456789',
    'host': 'store.prod.travel-sys.loc',
    'port': '5432',
    'sslmode': 'require'
}

# === Campos del modelo HotelImportado ===
CAMPOS = [
    'destino',
    'city_code',
    'hotel_code',
    'hotel_name',
    'hotel_city_code',
    'area_id',
    'giata_id',
    'country_iso_code',
    'country_name',
    'address',
    'email',
    'latitude',
    'longitude',
    'rating',
]

# === Ejecución ===
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 🔴 Orden correcto: PASAJEROS → HABITACIONES → RESERVAS → HOTELES
    print("🧹 Eliminando pasajeros de reservas de hoteles importados...")
    cursor.execute("""
        DELETE FROM backoffice_pasajero
        WHERE habitacion_id IN (
            SELECT id FROM backoffice_habitacionreserva
            WHERE reserva_id IN (
                SELECT id FROM backoffice_reserva
                WHERE hotel_importado_id IS NOT NULL
            )
        )
    """)
    conn.commit()

    print("🧹 Eliminando habitaciones de reservas de hoteles importados...")
    cursor.execute("""
        DELETE FROM backoffice_habitacionreserva
        WHERE reserva_id IN (
            SELECT id FROM backoffice_reserva
            WHERE hotel_importado_id IS NOT NULL
        )
    """)
    conn.commit()

    print("🧹 Eliminando reservas asociadas a hoteles importados...")
    cursor.execute("DELETE FROM backoffice_reserva WHERE hotel_importado_id IS NOT NULL")
    conn.commit()

    print("🧹 Eliminando hoteles importados...")
    cursor.execute("DELETE FROM backoffice_hotelimportado")
    conn.commit()

    # 📥 Cargar datos desde CSV
    if not os.path.exists(HOTEL_CSV):
        print(f"❌ Archivo no encontrado: {HOTEL_CSV}")
        sys.exit(1)

    with open(HOTEL_CSV, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = []
        for row in reader:
            rows.append([row.get(campo, None) or None for campo in CAMPOS])

    if rows:
        query = f"""
            INSERT INTO backoffice_hotelimportado ({', '.join(CAMPOS)})
            VALUES %s
        """
        execute_values(cursor, query, rows)
        conn.commit()
        print(f"✅ Hoteles importados: {len(rows)}")
    else:
        print("⚠️ El archivo CSV está vacío.")

except Exception as e:
    print("❌ Error:", e)

finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()

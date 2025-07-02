# tasks.py
from celery import shared_task
from datetime import date, datetime
from backoffice.models import Oferta  # Asegúrate de importar tu modelo

print("Archivo tasks.py cargado correctamente")


@shared_task
def mi_tarea_programada():
    print(f"Tarea programada ejecutada a las {datetime.now()}")
    # Aquí va la lógica de tu tarea

def extraer_fecha_fin(booking_window):
    """Extrae y convierte la fecha de finalización del booking_window"""
    try:
        _, fecha_fin_str = booking_window.split(" - ")
        fecha_fin = datetime.strptime(fecha_fin_str.strip(), "%Y-%m-%d").date()
        print(f"Fecha fin extraída: {fecha_fin}")  # Muestra la fecha fin extraída
        return fecha_fin
    
    except (ValueError, AttributeError):
        print("Error al extraer fecha fin, formato incorrecto o valor nulo.")
        return None  # Maneja errores de formato o valor nulo

@shared_task
def deshabilitar_ofertas_expiradas():
    hoy = datetime.today().date()
    print(f"Iniciando tarea de deshabilitar ofertas expiradas. Fecha de hoy: {hoy}")
    ofertas = Oferta.objects.filter(disponible=True)
    
    for oferta in ofertas:
        print(f"Revisando oferta: {oferta.codigo} (booking_window: {oferta.booking_window})")
        fecha_fin = extraer_fecha_fin(oferta.booking_window)
        if fecha_fin:
            if fecha_fin < hoy:
                print(f"Deshabilitando oferta {oferta.codigo} (fecha fin: {fecha_fin})")
                oferta.disponible = False
                oferta.save()
            else:
                print(f"La oferta {oferta.codigo} aún está vigente (fecha fin: {fecha_fin})")
        else:
            print(f"No se pudo obtener fecha fin para la oferta {oferta.codigo}")

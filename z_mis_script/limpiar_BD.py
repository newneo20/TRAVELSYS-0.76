import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')  # Reemplaza 'viajero_plus' con el nombre de tu proyecto
django.setup()

from django.apps import apps

def eliminar_datos_backoffice():
    # Obtener todos los modelos de la aplicación 'backoffice'
    modelos = apps.get_app_config('backoffice').get_models()

    for modelo in modelos:
        try:
            # Eliminar todos los objetos del modelo
            nombre_modelo = modelo.__name__
            cantidad = modelo.objects.count()
            modelo.objects.all().delete()
            print(f"Se eliminaron {cantidad} registros del modelo {nombre_modelo}.")
        except Exception as e:
            print(f"Error al eliminar datos del modelo {modelo.__name__}: {e}")

if __name__ == '__main__':
    eliminar_datos_backoffice()

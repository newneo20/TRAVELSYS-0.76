# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab # type: ignore
from django.conf import settings  # type: ignore

# Establecer el entorno de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')

app = Celery('viajero_plus')

# Cargar la configuración desde settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks en todas las apps registradas en INSTALLED_APPS
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# Configuración del programador de tareas periódicas
app.conf.beat_schedule = {
    'deshabilitar_ofertas_diarias': {
        'task': 'viajero_plus.tasks.deshabilitar_ofertas_expiradas',
        'schedule': crontab(hour=0, minute=1),  # 12:01 AM todos los días
    },
}

# Ejecutar tarea automáticamente al iniciar el servidor de Django
@app.on_after_finalize.connect
def startup_tasks(sender, **kwargs):
    sender.send_task('viajero_plus.tasks.deshabilitar_ofertas_expiradas')
    print("Tarea 'deshabilitar_ofertas_expiradas' ejecutada al iniciar Celery.")

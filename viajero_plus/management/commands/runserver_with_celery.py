import subprocess
from django.core.management.base import BaseCommand # type: ignore

class Command(BaseCommand):
    help = 'Inicia el servidor Django, Celery Worker y Celery Beat juntos'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Iniciando el servidor Django..."))
        django_server = subprocess.Popen(["python", "manage.py", "runserver", "0.0.0.0:8000"])

        self.stdout.write(self.style.SUCCESS("Iniciando Celery Worker..."))
        celery_worker = subprocess.Popen(["celery", "-A", "viajero_plus", "worker", "--loglevel=info"])

        self.stdout.write(self.style.SUCCESS("Iniciando Celery Beat..."))
        celery_beat = subprocess.Popen(["celery", "-A", "viajero_plus", "beat", "--loglevel=info"])

        try:
            django_server.wait()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Deteniendo los procesos..."))
            django_server.terminate()
            celery_worker.terminate()
            celery_beat.terminate()
            self.stdout.write(self.style.SUCCESS("Todos los procesos han sido detenidos correctamente."))

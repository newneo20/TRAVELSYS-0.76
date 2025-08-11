#!/bin/sh

# start.sh
# Espera a que la base de datos esté lista
echo "Esperando a que la base de datos esté lista..."
while ! nc -z db-srv 5432; do
  sleep 0.1
done
echo "La base de datos está lista."

# Recolecta archivos estáticos
echo "Recolectando archivos estáticos..."
# Asegúrate de que el manage.py esté en /app/viajero_plus
python /app/manage.py collectstatic --noinput

# Aplica las migraciones de la base de datos
echo "Aplicando migraciones de la base de datos..."
python /app/manage.py migrate

# Inicia Gunicorn
echo "Iniciando Gunicorn..."
# Asegúrate de que 'viajero_plus.wsgi:application' coincida con la ruta a tu archivo wsgi.py
# Si tu wsgi.py está en /app/viajero_plus/wsgi.py, este es el módulo correcto.
#exec gunicorn viajero_plus.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
#exec gunicorn viajero_plus.wsgi:application --bind 0.0.0.0:8000 --workers 3 --log-level debug --access-logfile - --error-logfile -

# Inicia Gunicorn con un formato de logs detallado
echo "Iniciando Gunicorn..."
exec gunicorn viajero_plus.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 2 \
  --worker-class gthread \
  --timeout 120 \
  --max-requests 500 \
  --max-requests-jitter 50 \
  --access-logfile - \
  --error-logfile - \
  --log-level info

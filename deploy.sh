#!/bin/bash

# Este script automatiza el proceso de despliegue y actualización de la aplicación.
# Se asume que estás en el directorio de tu proyecto.

# 1. Trae los últimos cambios del repositorio Git
echo "Paso 1: Obteniendo los últimos cambios del repositorio Git..."
git pull https://github.com/newneo20/TRAVELSYS-0.76.git

# Verificar si el pull fue exitoso
if [ $? -ne 0 ]; then
    echo "Error: git pull falló. Saliendo del script."
    exit 1
fi

# 2. Reconstruye y reinicia los servicios de Docker
# Se usa --build para forzar la reconstrucción de la imagen 'app-srv'
# Se usa -d para ejecutar los contenedores en segundo plano (detached mode)
echo "Paso 2: Reconstruyendo y reiniciando los servicios de Docker..."
docker-compose up --build -d

# Verificar si docker-compose up fue exitoso
if [ $? -ne 0 ]; then
    echo "Error: docker-compose up --build -d falló. Saliendo del script."
    exit 1
fi

# 3. Limpia las imágenes de Docker no utilizadas
# Esto ayuda a liberar espacio en disco. El comando 'prune'
# elimina todas las imágenes que no están asociadas a un contenedor.
echo "Paso 3: Limpiando imágenes de Docker antiguas..."
docker image prune -f

echo "¡Despliegue completado con éxito! Tu aplicación ha sido actualizada."

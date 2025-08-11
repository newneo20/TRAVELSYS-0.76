# --- Etapa de construcción ---
FROM python:3.10.18-slim-bookworm AS builder

# 1. Instala dependencias de compilación con limpieza
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./viajero_plus/requirements.txt .

# 2. Instalación optimizada de pip
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Etapa final ---
FROM python:3.10.18-slim-bookworm

# 3. Dependencias runtime mínimas (actualizadas para Bookworm)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libwebp7 \
    && rm -rf /var/lib/apt/lists/*

# 4. Configuración de timezone
ENV TZ=America/Toronto
RUN ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime && echo "$TZ" > /etc/timezone

# 5. Creación de usuario seguro
RUN groupadd -g 1000 manager && \
    useradd -u 1000 -g manager -m -d /home/manager manager

WORKDIR /app
ENV PYTHONPATH=/app \
    PATH="/home/manager/.local/bin:${PATH}" \
    # Variables de entorno adicionales para seguridad
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 6. Copia de artefactos con permisos correctos
COPY --from=builder --chown=manager:manager /root/.local /home/manager/.local
COPY --chown=manager:manager . .

# 7. Configuración final para producción
USER manager
EXPOSE 8000

# Verificación de salud (opcional pero recomendado)
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "/app/start.sh 2>&1"]

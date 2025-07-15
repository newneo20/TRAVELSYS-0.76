# 🚀 TRAVELSYS – Sistema de Reservas para Agencias de Viajes

**Versión:** 0.76.1  
**Autor:** Carlos Ríos Marimón  
**Licencia:** Propietaria  
**Última actualización:** Julio 2025

TRAVELSYS es un sistema integral de reservas desarrollado para agencias de viajes, con módulos personalizados para hoteles, traslados, vuelos, certificados de vacaciones, remesas y más. Incluye un backoffice completo y un frontend moderno utilizando Tailwind CSS.

---

## 📦 Tecnologías principales

- **Backend:** Python 3.10+, Django 4.2.7
- **Frontend:** Tailwind CSS, Alpine.js
- **Base de datos:** PostgreSQL / SQLite (para desarrollo)
- **Tareas en segundo plano:** Celery + Redis
- **PDFs y Excel:** ReportLab y OpenPyXL
- **Servidor WSGI:** Gunicorn

---

## 📂 Estructura del proyecto

```
TRAVELSYS/
├── backoffice/            # Panel administrativo personalizado
├── booking/               # Lógica de reservas y flujo de usuarios
├── usuarios/              # Gestión de usuarios y autenticación
├── z_mis_script/          # Scripts utilitarios y carga de datos
├── templates/             # Plantillas HTML por módulo
├── static/                # Archivos estáticos Tailwind y otros
├── documentos/            # Documentación y vouchers PDF generados
├── manage.py              # Entrada principal del proyecto
├── tailwind.config.js     # Configuración Tailwind
├── postcss.config.js      # Configuración PostCSS
├── requirements.txt       # Dependencias del entorno
├── README.md              # Este archivo

```

---

## ⚙️ Instalación (entorno de desarrollo)

### 1. Clona el repositorio

```bash
git clone https://github.com/tuusuario/travelsys.git
cd travelsys
```

### 2. Crea un entorno virtual y actívalo

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instala las dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Aplica migraciones

```bash
python manage.py migrate
```

### 5. Ejecuta el servidor

```bash
python manage.py runserver
```

---

## 🧵 Tailwind CSS

Para recompilar los estilos de Tailwind si haces cambios:

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/output.css --watch
```

---

## 🔁 Celery (procesamiento en segundo plano)

Asegúrate de tener Redis corriendo y luego lanza Celery con:

```bash
celery -A viajero_plus worker --loglevel=info
```

---

## 🧪 Variables de entorno

Ejemplo de archivo `.env`:

```
DEBUG=True
SECRET_KEY=tu_clave_secreta
DATABASE_URL=postgres://usuario:password@localhost:5432/travelsys
ALLOWED_HOSTS=127.0.0.1,localhost
```

Usa `django-environ` para cargarlo (agregar si no está).

---

## ✍️ Scripts útiles

Se encuentran en la carpeta `z_mis_script/`:

- `carga_usuarios.py`: importa usuarios desde CSV o Excel.
- `import_TRASLADOS.py`: importa traslados desde hojas de cálculo.
- `limpiar_BD.py`: elimina datos de prueba para resetear el entorno.
- `arreglar_traslados.py`: corrige inconsistencias.

---

## 📑 Generación de PDFs

Los vouchers y confirmaciones se generan automáticamente en `documentos/voucher/` usando `reportlab`.

---

## ✅ Checklist de módulos implementados

- [x] Gestión de hoteles y habitaciones
- [x] Módulo de traslados
- [x] Certificados de vacaciones
- [x] Módulo de remesas
- [x] Vuelos (en desarrollo)
- [x] API integración con 1way2italy (fase 1: hoteles)
- [x] Reservas multiproducto y multicliente
- [x] Panel de administración personalizado

---

## 📧 Contacto

**Desarrollado por:** Carlos Ríos Marimón  
**Email:** carlosalej1985@gmail.com  
**Ubicación:** Miami, FL, USA

---

## 📜 Licencia

Este proyecto es de uso exclusivo de **TRAVELSYS**. No redistribuir sin permiso expreso del autor.


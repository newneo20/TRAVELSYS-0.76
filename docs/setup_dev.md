# 🛠 TravelSYS – Guía de Instalación para Desarrollo

## 1. 📦 Requisitos Previos

- **Python 3.10 o superior**  
- **PostgreSQL** (si aplica para producción; en desarrollo puedes usar SQLite)  
- **Redis** (si usas Celery)  
- **Node.js** y **npm** (para Tailwind CSS y herramientas de frontend modernas)  
- **Git**

## 2. 📂 Clonar el proyecto

```bash
git clone https://github.com/newneo20/TRAVELSYS-0.74
cd TRAVELSYS-0.74
```

## 3. 🐍 Crear entorno virtual y activarlo

```bash
python3 -m venv venv

# En Linux/macOS:
source venv/bin/activate

# En Windows PowerShell:
venv\Scripts\Activate.ps1
```

## 4. 💾 Instalar dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. 🌱 Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el archivo `.env` y define al menos estas variables:

```ini
DJANGO_SECRET_KEY="tu_clave_secreta_aqui"
DEBUG=True
DATABASE_URL=postgres://usuario:password@localhost:5432/travelsys_db
REDIS_URL=redis://localhost:6379/0
```

> **Nota:** En desarrollo puedes omitir `DATABASE_URL` para usar SQLite por defecto.

## 6. 🗄️ Configurar la base de datos

Si usas PostgreSQL, crea la base y el usuario:

```sql
-- En psql o PgAdmin:
CREATE DATABASE travelsys_db;
CREATE USER travelsys_user WITH ENCRYPTED PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE travelsys_db TO travelsys_user;
```

## 7. 🚀 Aplicar migraciones

```bash
python manage.py migrate
```

## 8. 🛠️ Crear un superusuario

```bash
python manage.py createsuperuser
```

Sigue las indicaciones para email y contraseña.

## 9. 📥 Cargar datos iniciales (fixtures)

```bash
python manage.py loaddata initial_data.json
```

## 10. 🎨 Compilar assets de Tailwind CSS

```bash
npm install
npm run build         # Compilación de desarrollo
npm run build:prod    # Compilación para producción
```

Para modo *watch* en desarrollo:

```bash
npm run watch
```

## 11. 🏃‍♂️ Ejecutar el servidor de desarrollo

```bash
python manage.py runserver
```

Accede luego en tu navegador a:  
[http://127.0.0.1:8000](http://127.0.0.1:8000)

## 12. ⚙️ Uso básico

1. Ingresa a `/admin/` con el superusuario.  
2. Configura polos turísticos, proveedores, habitaciones y tarifas.  
3. Prueba la funcionalidad de reserva en la parte pública.

## 13. 🧪 Ejecutar tests

```bash
pytest
# o bien
python manage.py test
```

## 14. 📝 Documentación adicional

- **Backoffice**: `docs/backoffice.md`  
- **API externas**: `docs/api_integrations.md`  
- **Despliegue en producción**: `docs/deploy.md`  

# ✅ TravelSYS – Lista de Preparación Antes del Deploy

## 🔐 Seguridad y control de acceso
- [X] Verificar que todas las vistas sensibles usan `@login_required`
- [X] Aplicar `@manager_required` o permisos personalizados donde corresponda
- [X] Verificar que el usuario anónimo no pueda acceder a rutas protegidas
- [X] Asegurar que el superuser se puede crear y accede correctamente al panel admin

## ⚙️ Migraciones y base de datos
- [X] Borrar migraciones antiguas innecesarias si ya no se usarán
- [X] Regenerar migraciones limpias (`makemigrations`, `migrate`)
- [X] Validar que la base de datos esté sincronizada (`No changes detected`)
- [X] Crear superusuario con `createsuperuser`

## ⚙️ Configuración del proyecto (`settings.py`)
- [X] Confirmar que `DEBUG = True` durante desarrollo
- [X] Definir correctamente `ALLOWED_HOSTS`
- [X] Usar variables de entorno para `SECRET_KEY` y credenciales
- [X] Separar configuración de desarrollo y producción si es posible

## 🗂 Archivos estáticos y media
- [ ] `STATICFILES_DIRS` bien definido
- [ ] `MEDIA_URL` y `MEDIA_ROOT` correctamente configurados
- [ ] Verificar que los archivos de media se cargan correctamente en desarrollo

## 💾 Formularios y validaciones
- [X] Revisar que todos los formularios tengan validación adecuada
- [X] Revisar CSRF en formularios HTML personalizados
- [X] Mostrar errores en campos si hay errores de validación

## 🧠 Manejo de sesiones
- [X] Verificar el comportamiento de cierre automático de sesión
- [X] Confirmar que el tiempo de sesión (`SESSION_COOKIE_AGE`) se respeta

## 🎨 Migración a Tailwind (en progreso)
- [X] Revisar `base.html`
- [X] Reemplazar `navbar`, login y dashboard
- [ ] Migrar formularios de Bootstrap a Tailwind

### ❗ Formularios no migrados aún:
- `apps/backoffice/templates/backoffice/cadena_hotelera/crear_cadena_hotelera.html`
- `apps/backoffice/templates/backoffice/cadena_hotelera/editar_cadena_hotelera.html`
- `apps/backoffice/templates/backoffice/categorias/listar_categorias.html`
- `apps/backoffice/templates/backoffice/certificado_vacaciones/listar_certificados.html`
- `apps/backoffice/templates/backoffice/locations/listar_locations.html`

## 📄 Documentación interna
- [X] Crear `docs/setup_dev.md` con pasos de instalación y uso
- [ ] Agregar comandos útiles para desarrollo y testing
- [ ] Anotar cómo conectar a PostgreSQL o configurar Redis (si aplica)

## 🧪 Testing funcional básico
- [ ] Acceder a `/admin/` con superuser
- [ ] Probar el flujo: login → dashboard → crear/editar entidades → logout
- [ ] Confirmar que errores de usuario se muestran correctamente

## 🛢 Preparación para PostgreSQL (si se usará)
- [ ] Crear base de datos PostgreSQL
- [ ] Actualizar `DATABASES` en `settings.py`
- [ ] Probar conexión a PostgreSQL con `psql` o desde Django

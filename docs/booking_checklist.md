# ✅ Checklist de Auditoría — APLICACIÓN: booking
_Generado: 2025-08-10 03:22._  
Marca cada casilla a medida que resuelvas cada punto.

---

## 0) Resumen por severidad
- [ ] **Crítico:** `@csrf_exempt` en vista del panel, **credenciales en duro** (SMTP y `MessagePassword`), **nombres de URL duplicados**, nombre de URL erróneo (`hotel_detalleNO`), posible **ruta mal escrita** en `urls.py`.
- [ ] **Alto:** Endpoints POST **sin `@login_required`**, `.objects.get()` **sin manejo** → 500 potenciales, formularios HTML sin `method`/`csrf` (según caso).
- [ ] **Medio:** Mezcla de rutas con guion y guion_bajo, cobertura i18n incompleta, pocos `select_related/prefetch_related`.
- [ ] **Bajo:** uso extensivo de `print()` (reemplazar por `logging`), mensajes de error genéricos.

---

## 1) URLs (`booking/urls.py`)
- [ ] **Duplicados de `name=` (Crítico)**
  - [ ] `hotel_pago_reserva` duplicado (L24, L35).
  - [ ] `complete_solicitud` duplicado (L25, L83).
  - **Acción:** Mantener un único `name` por vista. Ajustar `{% raw %}{% url %}{% endraw %}`/`reverse()` en templates/vistas.
- [ ] **Nombre de URL incorrecto (Alto)**
  - [ ] L23: `name='hotel_detalleNO'` → debe ser `name='hotel_detalle'`.
- [ ] **Posible token roto en ruta (Crítico)**
  - [ ] L85: confirmar que sea `views.confirmar_reserva_distal` (sin texto truncado).
- [ ] **Consistencia de estilo en paths (Medio)**
  - [ ] Unificar a **kebab-case** (hay mezcla de `-` y `_`).

### Sugerencia de commit
- [ ] `fix(booking/urls): eliminar duplicados y corregir name=hotel_detalle`

---

## 2) Vistas (`booking/views.py`)
- [ ] **CSRF deshabilitado (Crítico)**
  - [ ] L2220: `@csrf_exempt` sobre `crear_reserva_envio_final` → **eliminar** y usar `@require_POST`.
- [ ] **POST sin `@login_required` (Alto)**
  - [ ] `crear_destinatario` (L2143) y `crear_remitente` (L2186) → añadir `@login_required`.
- [ ] **`.objects.get()` sin manejo (Alto)**
  - [ ] Reemplazar por `get_object_or_404` o `try/except DoesNotExist` en: 1152, 1283, 1316, 1448, 1596, 1597, 1634, 1808, 1892, 2042, 2048, 2580, 2819.
- [ ] **Enforcement método HTTP (Medio)**
  - [ ] Añadir `@require_GET`/`@require_POST` (además de `HttpResponseNotAllowed` cuando aplique).
- [ ] **Rendimiento (Medio)**
  - [ ] Añadir `select_related/prefetch_related` en listados y detalles: `Reserva` (`hotel`, `envio`, `remesa`, `traslado`…).
- [ ] **Logs (Bajo)**
  - [ ] Reemplazar `print()` por `logging` (configurar `LOGGING` en `settings`).

### Sugerencia de commits
- [ ] `sec(booking/views): quitar csrf_exempt y exigir require_POST`
- [ ] `sec(booking/views): añadir login_required en crear_destinatario/crear_remitente`
- [ ] `refactor(booking/views): get_object_or_404 + logging`
- [ ] `perf(booking): select_related/prefetch_related`

---

## 3) Formularios (`booking/forms.py`)
- [ ] **Validaciones (Alto)**
  - [ ] Añadir `clean_*` y/o `clean()` para: fechas coherentes, montos > 0, capacidades, noches mínimas, rangos de edad, etc.
- [ ] **Consistencia de widgets y mensajes (Bajo)**
  - [ ] Unificar clases CSS (`form-control`/Tailwind), `help_text` y mensajes de error.

### Sugerencia de commit
- [ ] `feat(booking/forms): validaciones clean_* y UI consistente`

---

## 4) Templates (`booking/templates/**`)
- [ ] **Sin `method` (Alto)**
  - [ ] `envios/modals/destinatario_modal.html` (L21)
  - [ ] `envios/modals/remitente_modal.html` (L22)
  - [ ] `hotel/hotel_detalle.html` (L68)
  - [ ] `hotel/hotel_pago_reserva.html` (L50)
  - [ ] `traslados/base_traslados.html` (L8)
  - [ ] `traslados/detalle_traslados.html` (L22)
  - [ ] `traslados/reserva_traslados.html` (L20)
  - [ ] `traslados/traslados.html` (L23)
- [ ] **Sin `{{% raw %}}{% csrf_token %}{{% endraw %}}` (Alto)**
  - [ ] `envios/modals/destinatario_modal.html`
  - [ ] `envios/modals/remitente_modal.html`
  - **Nota:** aunque uses `fetch` con `X-CSRFToken`, conviene incluir un `csrfmiddlewaretoken` en DOM para no fallar si cambia el selector.
- [ ] **i18n incompleto (Medio)**
  - [ ] Añadir `{% raw %}{% trans %}{% endraw %}`/`{% raw %}{% blocktrans %}{% endraw %}` en textos visibles (botones, títulos, estados).

### Sugerencia de commit
- [ ] `ui(booking/templates): method+csrf en formularios + i18n`

---

## 5) Integraciones y secretos
- [ ] **SMTP en duro (Crítico)** — `booking/funciones_externas_booking.py`
  - [ ] L106–107: `from_email="admin@travel-sys.com"`, `password="Z6d*ibHDAyJTmLNq%kvQNx"`
  - [ ] L175–176: repetido.
  - **Acción:** mover a `settings` y leer de variables de entorno; **rotar** credenciales.
- [ ] **MessagePassword en XML (Crítico)** — `booking/xml_builders_1way2italy.py`
  - [ ] L24: `<RequestorID ... MessagePassword="Gmh3S246t987$"/>`
  - [ ] L67: `"MessagePassword": "Gmh3S246t987$"`
  - **Acción:** extraer a entorno/`settings` y no comitear secretos.
- [ ] **Endpoints/headers**
  - [ ] Confirmar endpoints de producción/sandbox via `settings` (no hardcode).

### Sugerencia de commits
- [ ] `sec(integrations): extraer SMTP/MessagePassword a entorno`
- [ ] `chore(settings): variables de entorno para endpoints y credenciales`

---

## 6) Seguridad adicional
- [ ] `@login_required` en endpoints sensibles.
- [ ] Cookies seguras (`Secure`, `HttpOnly`) y `CSRF_TRUSTED_ORIGINS` correcto.
- [ ] Limitar tamaño de payload JSON (si procede).

---

## 7) Rendimiento
- [ ] Paginación + `select_related/prefetch_related` en listados (reservas, hoteles, traslados).
- [ ] Evitar N+1 en plantillas que tocan relaciones.

---

## 8) Calidad/UX
- [ ] `messages.success/error` consistentes tras POST.
- [ ] Estados vacíos uniformes.
- [ ] Validación de fechas y `booking_window` (regex) tanto en front como en back.

---

## 9) Tests (`booking/tests.py`)
- [ ] Smoke de rutas (200 con login, 302/403 sin login).
- [ ] Métodos HTTP correctos (POST rechaza GET → 405).
- [ ] CRUD remitente/destinatario con CSRF+login.
- [ ] Fixtures/XML: parseo de `HotelAvailRS` (Distal).

---

## 10) Plan de commits (lista final)
- [ ] `fix(booking/urls): eliminar duplicados y corregir name=hotel_detalle`
- [ ] `sec(booking/views): quitar csrf_exempt y exigir require_POST`
- [ ] `sec(booking/views): añadir login_required a crear_destinatario/crear_remitente`
- [ ] `refactor(booking/views): get_object_or_404 y logging`
- [ ] `perf(booking): select_related/prefetch_related`
- [ ] `ui(booking/templates): method + csrf + i18n`
- [ ] `sec(integrations): extraer SMTP/MessagePassword a entorno`

> **Tip:** tras cada grupo, ejecuta comprobaciones rápidas:
- `grep -n "@csrf_exempt" booking/views.py` → debe quedar vacío.
- `grep -n "objects.get(" booking/views.py` → solo en servicios con manejo de errores.
- `python manage.py test booking` → smoke verde.

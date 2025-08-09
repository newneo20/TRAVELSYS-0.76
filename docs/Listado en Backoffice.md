# LISTADO DE DIRECTORIOS EN `templates/backoffice`


#### 🔐 Resumen ejecutivo (prioridades) ####
	( 01 ) Crítico (rompe / inseguro)
	( 02 ) Funciones duplicadas en views.py (15 duplicados: p.ej. listar_habitaciones, eliminar_habitacion, guardar_configuracion_hotel, múltiples actualizar_*, etc.).
    ( 03 ) Esto genera override silencioso y comportamientos impredecibles.
	( 04 ) Múltiples endpoints @csrf_exempt en backoffice (edición de reserva, guardar config de hotel, ofertas, etc.). Riesgo de CSRF/CSRF bypass en panel administrativo.
	( 05 ) urls.py con nombres duplicados (hotel_offers duplicado exacto; listar_habitaciones y eliminar_habitacion con dos rutas distintas al mismo name; slug y underscore  mezclados).
	( 06 ) forms.py está corrupto/recortado (aparecen ... dentro del código y definiciones a medias). Así no compila confiablemente ni valida lo que debe.
	( 07 ) Alto (bugs y 500s potenciales)
	( 08 ) Varios .objects.get(...) con IDs de request sin get_object_or_404() ni try/except → 500 si no existe (habitaciones, ofertas, transporte/ubicación, etc.).
	( 09 ) Vistas guardar_* que no usan ModelForm ni validaciones exhaustivas → datos inconsistentes/ataques de parámetros.
	( 10 ) Doble definición de guardar_configuracion_hotel (dos funciones con el mismo nombre).
	( 11 ) Medio (rendimiento, DX y UX)
	( 12 ) Listados sin select_related/prefetch_related pese a mostrar FK (hoteles, cadenas, etc.) → N+1 queries y lentitud con datos reales.
	( 13 ) Inconsistencias de naming en URLs (guardar-configuracion-hotel/ vs guardar_configuracion_hotel/).
	( 14 ) i18n parcial: ~38% de templates usan {% trans %}; el resto no.
	( 15 ) Mezcla de estilos (Bootstrap fuerte en backoffice; si quieres migrar a Tailwind, hay que unificar criterios).
	( 16 ) Bajo (calidad/orden)
	( 17 ) tests.py vacío → sin smoke tests mínimos para CRUD y permisos.
	( 18 ) Algunos parciales HTML de hotel carecen de method en <form> (si se usan de forma independiente).



#### 🔐 Detalle con referencias (archivo/línea) ####

## (1) Duplicados en views.py (crítico)
	- [X] Funciones duplicadas (la segunda definición pisa a la primera):
	- [X] listar_habitaciones: L509 y L1025
	- [X] eliminar_habitacion: L701 y L1047
	- [X] guardar_configuracion_hotel: L725 y L1285

	<----> Bloque “edición de reserva” con duplicados:
	- [X] actualizar_traslado_y_pasajeros: L1585 y L2112
	- [X] actualizar_habitacion: L1704 y L1899
	- [X] actualizar_pasajeros_existentes: L1723 y L1917
	- [X] agregar_nuevos_pasajeros: L1753 y L1945
	- [X] agregar_nuevos_pasajeros_a_habitacion_nueva: L1832 y L1986
	- [X] correo_confirmada: L1865 y L2016
	- [X] recalcular_precio_y_costo: L1875, L2089 y L2268
	- [X] calcula_precio: L2026, L2206 y L3279
	- [X] calcular_dias_por_oferta: L2032 y L2211
	- [X] obtener_habitacion: L2056 y L2235
	- [X] obtener_oferta: L2066 y L2245
	- [X] Acción: consolidar cada funcionalidad en una sola definición, mover helpers a utils/ y reimportar. Esto elimina comportamientos “fantasma”.

## (2) @csrf_exempt en endpoints sensibles (crítico)

Marcadores de @csrf_exempt en:
	- [X] L605 crear_editar_oferta
	- [X] L723/L1285 guardar_configuracion_hotel (dup)
	- [X] L1558-L1984 Todo el bloque de actualización de reservas (habitaciones/pasajeros/traslados, agregar/actualizar).
Acción: quitar @csrf_exempt y usar el token CSRF (si es AJAX: enviar X-CSRFToken). El backoffice debe estar CSRF-protegido.

## (3) URLs duplicadas e inconsistentes (crítico)

En backoffice/urls.py:
	- [X] name='hotel_offers' duplicado exacto (dos rutas iguales).
	- [X] name='listar_habitaciones' aparece en 2 rutas:
	- [X] listar_habitaciones/<int:hotel_id>/
	- [X] habitaciones/listar/<int:hotel_id>/
	- [X] name='eliminar_habitacion' en 2 rutas:
	- [X] eliminar_habitacion/<int:habitacion_id>/
	- [X] habitacion/eliminar/<int:habitacion_id>/
	- [X] Doble estilo en la misma intención:
	- [X] guardar-configuracion-hotel/<int:hotel_id>/
	- [X] guardar_configuracion_hotel/<int:hotel_id>/
Acción: dejar una sola ruta por name y unificar estilo (recomiendo kebab-case en paths).

## (4) forms.py corrupto / incompleto (crítico)
	- [ ] El archivo contiene ... (elipses) y clases cortadas. Ejemplo de encabezado y zonas intermedias truncadas.
Acción: reescribir forms.py desde cero con ModelForm por entidad (Hotel, Habitacion, Oferta, Cadena, Polo, etc.), validaciones clean_*, y widgets consistentes.

## (5) .objects.get() sin manejo (alto)

Usos sensibles (ejemplos):
	- [X] L582 Habitacion.objects.get(id=habitacion_id)
	- [ ] L623/L631/L1172 Oferta.objects.get(...) y Hotel.objects.get(id=hotel_id)
	- [ ] L923-L924 PoloTuristico.objects.get(...), Proveedor.objects.get(...)
	- [ ] L1608-L1620 Transportista/Ubicacion/Vehiculo.objects.get(...) por campos de texto
	- [ ] L2058-L2059 Hotel.objects.get(hotel_nombre=...) y Habitacion.objects.get(hotel=..., tipo=...)
    - [ ] Acción usar get_object_or_404 o try/except con DoesNotExist, devolviendo mensajes amigables y redirect en backoffice (no 50- [ ] .

## (6) Val- [ ] ación/seguridad en guardar_* (alto)
	- [ ] Varias vistas guardar_* escriben directo desde request.POST sin ModelForm ni validaciones robustas (p.ej. guardar_habitacion, guardar_oferta, guardar_instalaciones_hotel, guardar_editar_remesa, guardar_edicion_reserva).
Acción: migrar a ModelForm + validaciones server-side. Mantén la UX con mensajes messages.success/error.

## (7) Rendimiento en listados (medio)
	- [ ] Solo 4 usos de select_related() y 2 de prefetch_related() en todo backoffice.
	- [ ] Vistas tipo listar_hoteles (desde L271) filtran por FK (proveedor, polo, cadena) pero no usan select_related → N+1 queries.
Acción: en cada listar_*, añade:

.select_related('proveedor', 'polo_turistico', 'cadena_hotelera')
.prefetch_related('habitaciones', 'ofertas')  # según lo que se muestre

y paginación ya la tienes en varios (👍).

## (8) Parciales de formularios sin method (bajo → medio si se usan sueltos)
	- [ ] En templates/backoffice/hoteles/partials/:
	- [ ] form_config.html, form_habitaciones.html, form_instalaciones.html, form_ofertas.html no incluyen method en <form>.
Acción: si se usan como formularios independientes, pon method="post"; si son parciales dentro de otro <form>, documenta claramente.

## (9) i18n y consistencia de estilos (medio)
	- [ ] 41/108 templates usan {% trans %} → cobertura parcial.
	- [ ] Backoffice usa Bootstrap (muchos form-control, btn btn-*). Si tu plan es Tailwind solo para front, ok; si no, definamos una guía de estilos única.

## (10) Excepción amplia (bajo)
	- [ ] L3387: except: desnudo (fecha).
Acción: usa except Exception: al menos, o mejor ValueError.

## (11) Tests (bajo)
	- [ ] tests.py vacío.
Acción: agrega smoke tests:
	- [ ] Carga de cada listar_* con usuario logueado → 200.
	- [ ] Intento de acceso sin login → 302 a login.
	- [ ] CRUD básico (crear/editar/eliminar) para 2-3 modelos clave.

⸻

## Sugerencias de refactor (listas para commit)

Te propongo bloques de commits con mensajes claros:
	- [ ] fix(backoffice/urls): nombres únicos y paths consistentes
	- [ ] Eliminar rutas duplicadas de hotel_offers, listar_habitaciones, eliminar_habitacion.
	- [ ] Elegir un estilo (kebab-case) y mantener uno solo.
	- [ ] Buscar y reemplazar en templates {% url %} afectados.
	- [ ] fix(backoffice/views): eliminar duplicados y mover helpers
	- [ ] Consolidar cada función duplicada.
	- [ ] Extraer a backoffice/utils/reservas.py los helpers de edición de reserva y dejarlos una vez.
	- [ ] Alinear imports.
	- [ ] sec(backoffice): remover @csrf_exempt y aplicar CSRF en AJAX
	- [ ] Quitar @csrf_exempt en todas las vistas del panel.
	- [ ] Si hay endpoints AJAX, documentar en template/JS el uso de X-CSRFToken.
	- [ ] feat(backoffice/forms): ModelForms + validaciones
	- [ ] Reescribir forms.py (Hotel, Habitacion, Oferta, Cadena, Polo, etc.).
	- [ ] Mover lógica de limpieza a clean_*, campos/labels y widgets uniformes.
	- [ ] perf(backoffice): select_related/prefetch_related en listados
	- [ ] listar_hoteles, listar_cadenas_hoteleras, listar_reservas, etc.
	- [ ] Mantener paginación actual.
	- [ ] ux(backoffice): feedback y estados vacíos
	- [ ] Asegurar messages.success/error tras cada acción.
	- [ ] Plantillas “sin resultados” consistentes.
	- [ ] test(backoffice): smoke suite mínima
	- [ ] Pruebas de acceso a listar_*, crear_*, editar_*, eliminar_*.
	- [ ] Verificación de permisos (login requerido).

⸻

Mini-muestras (cambios clave)

## (A) URLs: unificar y evitar duplicados

# backoffice/urls.py (ejemplo)
app_name = 'backoffice'

urlpatterns = [
    # ✅ DEJAR SOLO UNA:
    path('hoteles/ofertas/<int:hotel_id>/', views.hotel_offers, name='hotel_offers'),

    # ✅ Unificar naming:
    path('hoteles/<int:hotel_id>/habitaciones/', views.listar_habitaciones, name='listar_habitaciones'),
    path('habitaciones/<int:habitacion_id>/eliminar/', views.eliminar_habitacion, name='eliminar_habitacion'),

    # ❌ Eliminar duplicados equivalentes:
    # path('listar_habitaciones/<int:hotel_id>/', ... )  # BORRAR
    # path('habitacion/eliminar/<int:habitacion_id>/', ...)  # BORRAR
    # path('guardar_configuracion_hotel/<int:hotel_id>/', ...)  # BORRAR si existe el kebab-case
]

## (B) CSRF en vistas (quitar @csrf_exempt)

# backoffice/views.py  (antes)
@csrf_exempt
@login_required
def guardar_configuracion_hotel(request, hotel_id):
    ...

# (después)
@login_required
def guardar_configuracion_hotel(request, hotel_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    # Validar CSRF automáticamente (middleware)

## (C) get_object_or_404 para evitar 500s
## (D) Listados con select_related
## (E) Forms robustos

Checklist “Go Live” (backoffice)
	- [ ] Quitar todos los @csrf_exempt en vistas del panel.
	- [ ] Eliminar duplicados de funciones en views.py.
	- [ ] Unificar rutas y nombres en urls.py (sin duplicados).
	- [ ] Reescribir forms.py con ModelForm y clean_*.
	- [ ] select_related/prefetch_related en todos los listar_* con FK mostradas.
	- [ ] Manejar errores con get_object_or_404 / try/except y messages.
	- [ ] i18n: cubrir textos visibles clave.
	- [ ] Tests smoke de CRUD y permisos.

⸻

¿Cómo quieres proceder?

Si te parece, te preparo commits listos (por bloques) para que los apliques en GitKraken. Dime si quieres que:
	1.	Empiece por URLs + vistas duplicadas + CSRF (bloque crítico),
	2.	Siga con Forms + validaciones,
	3.	Y cierre con performance + tests.

¿Arranco con el bloque crítico y te dejo el primer commit preparado?
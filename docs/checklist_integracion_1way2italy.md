
# Checklist actualizado de integración 1way2italy - Distal

---

## A. Finalizar y optimizar la fase de Cotización

### Datos de producto (HotelProductRQ)

- [x] Nombre del hotel
- [x] Código del hotel (HotelCode)
- [x] Ciudad (HotelCityCode)
- [x] Categoría de estrellas
- [x] Dirección
- [x] Descripción
- [x] Imágenes (si existen)

### Datos de habitaciones y opciones

- [x] RoomType
- [x] BoardType (tipo de alimentación)
- [x] RoomOption ID (opción seleccionable)
- [x] Precios (neto, bruto, moneda)
- [x] Release / CutOff (límite de compra anticipada)
- [x] Políticas de cancelación (cancel policies)
- [ ] Garantías o pagos (si aparecen)
- [ ] Edad máxima de niños (si aplica)

### Cálculo financiero

- [ ] Conversión de moneda (EUR → USD)
- [x] Aplicación de márgenes / fee / comisión
- [x] Formato final de precio al cliente

### Interfaz TravelSYS (Front)

- [x] Ficha de hotel en resultados
- [x] Ficha de detalle de hotel
- [x] Presentación de habitaciones disponibles
- [x] Inclusión de política de cancelación visible
- [ ] Mostrar estancia mínima
- [x] Mostrar cutoff (ultima fecha para reservar)

### Validación técnica

- [x] Realizar pruebas multi-habitación
- [x] Validar comportamiento en fechas límites (release policy)
- [x] Test de ocupación máxima por habitación
- [x] Simulaciones de reservas de prueba (cotización múltiple)

---

## B. Activar y desarrollar el flujo de Reservas Confirmadas

### Solicitudes a Datagest

- [ ] Solicitar activación del endpoint HotelBookingRQ
- [ ] Solicitar documentación completa de reservas confirmadas
- [ ] Confirmar esquema XML requerido
- [ ] Confirmar reglas de negocio de reservas (pagos, garantías, penalizaciones)

### Desarrollo de BookingRQ

- [ ] Construir el XML completo de booking:
   - [ ] Datos de hotel
   - [ ] Datos de habitación y opción seleccionada
   - [ ] Datos de pasajeros
   - [ ] Fechas y ocupación
   - [ ] Precio final
   - [ ] Datos de contacto / agencia

- [ ] Implementar el envío al endpoint de booking
- [ ] Manejar respuesta HotelBookingRS correctamente:
   - [ ] Confirmación de booking ID
   - [ ] Validación de errores
   - [ ] Registro de confirmación en la BD de TravelSYS

### Flujo completo en TravelSYS

- [ ] Integrar el flujo en el sistema actual de reservas
- [ ] Adaptar dashboard de reservas para mostrar los bookings confirmados
- [ ] Agregar botón "Confirmar reserva" en la interfaz de usuario
- [ ] Ajustar notificaciones de correo para confirmaciones Distal
- [ ] Ajustar reportes financieros internos

### Validación y QA

- [ ] Realizar múltiples tests completos de reserva
- [ ] Validar edge cases (errores, overbooking, cutoff)
- [ ] Simular cancelaciones (si la API lo permite)
- [ ] Validar logs de integración y debugging

---

## Opcional: Fase avanzada futura

- [ ] Activación de otros proveedores conectados en 1way2italy.
- [ ] Integración de circuitos y excursiones (closed tours).
- [ ] Modificaciones y anulaciones vía API.
- [ ] Sincronización automática de inventario.

---

## Plan de ejecución sugerido

1. Terminamos A (cotización al 100% optimizada).
2. Solicitamos a Datagest la activación de B.
3. Desarrollamos el flujo completo de reservas confirmadas.
4. Test de QA total.

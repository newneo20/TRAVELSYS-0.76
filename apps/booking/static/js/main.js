// main.js

// Función para inicializar componentes al cargar el documento
$(document).ready(function() {
    // Inicializar Select2 en el campo de destino
    $('#destino').select2({
        placeholder: '¿A dónde vas?',
        allowClear: true
    });

    // Inicializar el datepicker para fechas de viaje
    $('#fechas_viaje').daterangepicker({
        autoUpdateInput: false,
        startDate: moment(),
        endDate: moment().add(1, 'days'),
        locale: {
            format: 'YYYY-MM-DD',
            separator: ' - ',
            applyLabel: 'Aplicar',
            cancelLabel: 'Cancelar'
        }
    });

    // Actualizar el input cuando se seleccionen nuevas fechas
    $('#fechas_viaje').on('apply.daterangepicker', function(ev, picker) {
        $(this).val(picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD'));
    });

    // Limpiar el input si se cancela la selección
    $('#fechas_viaje').on('cancel.daterangepicker', function(ev, picker) {
        $(this).val('');
    });

    // Manejar el modal de habitaciones y pasajeros
    function actualizarHabitaciones() {
        var numHabitaciones = parseInt($('#habitaciones').val());
        var habitacionesContainer = $('#habitacionesContainer');
        habitacionesContainer.empty();

        // Genera dinámicamente campos para cada habitación adicional
        for (var i = 2; i <= numHabitaciones; i++) {
            var habitacionHtml = `
                <div class="row align-items-start mt-3">
                    <div class="form-group col-md-2">
                        <label>Habitación ${i}</label>
                    </div>
                    <div class="form-group col-md-2">
                        <label for="adultos${i}">Adultos</label>
                        <select id="adultos${i}" class="form-select">
                            <option value="1">1</option>
                            <option value="2" selected>2</option>
                            <option value="3">3</option>
                        </select>
                    </div>
                    <div class="form-group col-md-2">
                        <label for="ninos${i}">Niños</label>
                        <select id="ninos${i}" class="form-select ninos-select" data-habitacion="${i}">
                            <option value="0" selected>0</option>
                            <option value="1">1</option>
                            <option value="2">2</option>
                        </select>
                    </div>
                    <div class="form-group col-md-6" id="edadesNinos${i}">
                        <!-- Campos de edad de los niños se generan dinámicamente -->
                    </div>
                </div>
            `;
            habitacionesContainer.append(habitacionHtml);
        }
    }

    function actualizarCamposEdadNinos(habitacion) {
        var numNinos = parseInt($(`#ninos${habitacion}`).val());
        var edadesNinosDiv = $(`#edadesNinos${habitacion}`);
        edadesNinosDiv.empty();

        // Genera dinámicamente campos de edad para cada niño
        for (var i = 1; i <= numNinos; i++) {
            var campoEdad = `
                <div class="d-inline-block me-2">
                    <label for="edadNino${habitacion}_${i}" class="edad-label">Edad Niño ${i}</label>
                    <select id="edadNino${habitacion}_${i}" class="form-select edad-select">
                        <option value="" selected>-</option>
                        ${[...Array(13).keys()].map(age => `<option value="${age + 1}">${age + 1}</option>`).join('')}
                    </select>
                    <span class="edad-obligatoria text-danger">Edad obligatoria</span>
                </div>
            `;
            edadesNinosDiv.append(campoEdad);
        }
    }

    // Eventos asociados a cambios en el formulario
    $('#habitaciones').change(function() {
        actualizarHabitaciones();
        actualizarCamposEdadNinos(1);
    });

    $(document).on('change', '.ninos-select', function() {
        var habitacion = $(this).data('habitacion');
        actualizarCamposEdadNinos(habitacion);
    });

    // Guardar la selección de habitaciones y pasajeros
    $('#guardarHabitaciones').click(function() {
        var numHabitaciones = $('#habitaciones').val();
        var datosHabitaciones = [];
        var totalAdultos = 0;
        var totalNinos = 0;

        // Recorre todas las habitaciones y recoge la información de adultos, niños y edades
        for (var i = 1; i <= numHabitaciones; i++) {
            var adultos = $(`#adultos${i}`).val();
            var ninos = $(`#ninos${i}`).val();
            var edadesNinos = [];

            // Recoge las edades de los niños en la habitación actual
            for (var j = 1; j <= ninos; j++) {
                edadesNinos.push($(`#edadNino${i}_${j}`).val());
            }

            totalAdultos += parseInt(adultos);
            totalNinos += parseInt(ninos);

            datosHabitaciones.push({
                habitacion: i,
                adultos: adultos,
                ninos: ninos,
                edadesNinos: edadesNinos
            });
        }

        // Guarda la información en un campo oculto en formato JSON
        var infoHabitaciones = {
            numHabitaciones: numHabitaciones,
            totalAdultos: totalAdultos,
            totalNinos: totalNinos,
            datosHabitaciones: datosHabitaciones
        };

        $('#infoHabitacionesInput').val(JSON.stringify(infoHabitaciones));

        // Actualiza los campos ocultos con la información total
        $('#habitaciones_input').val(numHabitaciones);
        $('#adultos_input').val(totalAdultos);
        $('#ninos_input').val(totalNinos);

        // Actualiza el texto del botón con el resumen de habitaciones, adultos y niños
        var habitacionesTexto = `<i class="fas fa-bed"></i> ${numHabitaciones}`;
        var adultosTexto = `<i class="fas fa-user"></i> ${totalAdultos}`;
        var ninosTexto = `<i class="fas fa-child"></i> ${totalNinos}`;
        $('.btn-outline-primary').html(`${habitacionesTexto} ${adultosTexto} ${ninosTexto}`);

        // Cierra el modal
        $('#habitacionesModal').modal('hide');
    });

    // Inicializa el modal con una habitación
    $('#habitaciones').val('1').trigger('change');
    actualizarCamposEdadNinos(1);

    // Inicializar tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();

    // Código para hotel_results.html
    // Manejo del filtro de precio
    $('#priceRange').on('input', function() {
        $('#priceValue').text('$' + $(this).val());
    });

    // Manejo del formulario de filtros
    $('#filterForm').submit(function(e) {
        // Puedes implementar la lógica de filtrado aquí si es necesario
        // e.g., enviar el formulario o hacer una llamada AJAX
    });

    // Código para cargar valores en el modal desde infoHabitaciones
    var infoHabitacionesInput = $('#infoHabitacionesInput').val();
    if (infoHabitacionesInput) {
        var infoHabitaciones = JSON.parse(infoHabitacionesInput);
        cargarValoresModal(infoHabitaciones);
    }

    function cargarValoresModal(info) {
        $('#habitaciones').val(info.numHabitaciones).trigger('change');

        for (var i = 0; i < info.datosHabitaciones.length; i++) {
            var habitacion = info.datosHabitaciones[i];
            $('#adultos' + (i + 1)).val(habitacion.adultos);
            $('#ninos' + (i + 1)).val(habitacion.ninos).trigger('change');

            for (var j = 0; j < habitacion.edadesNinos.length; j++) {
                $('#edadNino' + (i + 1) + '_' + (j + 1)).val(habitacion.edadesNinos[j]);
            }
        }
    }

    // Código para hotel_detalle.html
    // Manejar selección de opciones de alojamiento
    $('.opcion-habitacion').change(function() {
        var habitacionIndex = $(this).attr('name').split('_')[2];
        var precio = $(this).data('precio');

        $('#precio_opcion_' + habitacionIndex).val(precio);
    });

    $('#reservaForm').submit(function(e) {
        // Validaciones adicionales si es necesario
    });

    // Manejo de fechas en hotel_detalle.html
    var fechasViaje = $('#fechas_viaje').val();
    if (fechasViaje) {
        var fechas = fechasViaje.split(' - ');
        $('#fechas_viaje').data('daterangepicker').setStartDate(fechas[0]);
        $('#fechas_viaje').data('daterangepicker').setEndDate(fechas[1]);
    }
});

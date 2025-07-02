document.addEventListener('DOMContentLoaded', function() {

    // Contenedor principal de las habitaciones
    const habitacionesContainer = document.getElementById('habitaciones-container');

    // Calcula la edad de una persona en base a su fecha de nacimiento.
    function calcularEdad(fechaNacimiento) {
        const hoy = new Date();
        const nacimiento = new Date(fechaNacimiento);
        let edad = hoy.getFullYear() - nacimiento.getFullYear();
        const mes = hoy.getMonth() - nacimiento.getMonth();
        if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
            edad--;
        }
        return edad;
    }

    // Valida la capacidad de una habitación según el número de adultos y niños.
    function validarCapacidadHabitacion(habitacionId) {
        const habitacionSelect = document.getElementById(`habitacion_nombre_${habitacionId}`);
        const adultosInput = document.getElementById(`adultos_${habitacionId}`);
        const ninosInput = document.getElementById(`ninos_${habitacionId}`);

        const soloAdultos = habitacionSelect?.selectedOptions[0].getAttribute('data-solo-adultos') === 'True';
        const maxAdultos = parseInt(habitacionSelect?.selectedOptions[0].getAttribute('data-max-adultos'));
        const maxNinos = parseInt(habitacionSelect?.selectedOptions[0].getAttribute('data-max-ninos'));
        const maxCapacidad = parseInt(habitacionSelect?.selectedOptions[0].getAttribute('data-max-capacidad'));
        const minCapacidad = parseInt(habitacionSelect?.selectedOptions[0].getAttribute('data-min-capacidad'));

        const adultos = parseInt(adultosInput.value);
        const ninos = parseInt(ninosInput.value);

        if (soloAdultos) {
            ninosInput.disabled = true;
            ninosInput.value = 0;
        } else {
            ninosInput.disabled = false;
        }

        if (adultos > maxAdultos) {
            alert(`El número de adultos no puede ser mayor que ${maxAdultos}.`);
            adultosInput.value = maxAdultos;
        }

        if (ninos > maxNinos) {
            alert(`El número de niños no puede ser mayor que ${maxNinos}.`);
            ninosInput.value = maxNinos;
        }

        if (adultos + ninos > maxCapacidad) {
            alert(`La capacidad total no puede ser mayor que ${maxCapacidad}.`);
            ninosInput.value = maxCapacidad - adultos;
        }

        if (adultos < minCapacidad) {
            alert(`El número de adultos no puede ser menor que ${minCapacidad}.`);
            adultosInput.value = minCapacidad;
        }
    }

    // Inicializa un picker de rango de fechas
    function initializeDateRangePicker(element) {
        $(element).daterangepicker({
            opens: 'left',
            locale: {
                format: 'MM/DD/YYYY'
            }
        }, function(start, end, label) {
            console.log("A new date selection was made: " + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'));
        });
    }

    // Inicializa un picker de una sola fecha y calcula la edad si se proporciona un campo de edad
    function initializeSingleDatePicker(element, campoEdadId) {
        $(element).daterangepicker({
            singleDatePicker: true,
            showDropdowns: true,
            minYear: 1901,
            maxYear: parseInt(moment().format('YYYY'), 10),
            locale: {
                format: 'MM/DD/YYYY'
            }
        }, function(start, end, label) {
            if (campoEdadId) {
                const edad = calcularEdad(start.format('YYYY-MM-DD'));
                document.getElementById(campoEdadId).value = edad;
            }
        });
    }

    // Agrega un nuevo pasajero (adulto o niño) a una habitación específica.
    function agregarPasajero(pasajerosContainer, habitacionId, tipoPasajero) {
        const nuevaPasajeroIndex = pasajerosContainer.children.length + 1;

        const edadInputHtml = tipoPasajero === 'nino' || tipoPasajero === 'adulto' ? `
            <div class="col-md-1">
                <div class="form-group">
                <label for="edad_pasajero_${habitacionId}_${nuevaPasajeroIndex}"><strong>Edad</strong></label>
                <input type="text" class="form-control edad" id="edad_pasajero_${habitacionId}_${nuevaPasajeroIndex}" name="habitaciones[${habitacionId}][pasajeros][nuevo_${nuevaPasajeroIndex}][edad]" readonly>
                </div>
            </div>` : '';

        const nuevoPasajero = document.createElement('div');
        nuevoPasajero.className = 'row pasajero';
        nuevoPasajero.setAttribute('data-tipo', tipoPasajero);
        nuevoPasajero.innerHTML = `
            <div class="col-md-3">
                <div class="form-group">
                <label for="nombre_pasajero_${habitacionId}_${nuevaPasajeroIndex}"><strong>Nombre</strong></label>
                <input type="text" class="form-control" id="nombre_pasajero_${habitacionId}_${nuevaPasajeroIndex}" name="habitaciones[${habitacionId}][pasajeros][nuevo_${nuevaPasajeroIndex}][nombre]" value="">
                </div>
            </div>
            <div class="col-md-2">
                <div class="form-group">
                <label for="fecha_nacimiento_pasajero_${habitacionId}_${nuevaPasajeroIndex}"><strong>Fecha de Nacimiento</strong></label>
                <input type="text" class="form-control fecha-nacimiento" id="fecha_nacimiento_pasajero_${habitacionId}_${nuevaPasajeroIndex}" name="habitaciones[${habitacionId}][pasajeros][nuevo_${nuevaPasajeroIndex}][fecha_nacimiento]" value="">
                </div>
            </div>
            ${edadInputHtml}
            <div class="col-md-2">
                <div class="form-group">
                <label for="pasaporte_pasajero_${habitacionId}_${nuevaPasajeroIndex}"><strong>Pasaporte</strong></label>
                <input type="text" class="form-control" id="pasaporte_pasajero_${habitacionId}_${nuevaPasajeroIndex}" name="habitaciones[${habitacionId}][pasajeros][nuevo_${nuevaPasajeroIndex}][pasaporte]" value="">
                </div>
            </div>
            <div class="col-md-2">
                <div class="form-group">
                <label for="caducidad_pasaporte_${habitacionId}_${nuevaPasajeroIndex}"><strong>Caducidad Pasaporte</strong></label>
                <input type="text" class="form-control caducidad-pasaporte" id="caducidad_pasaporte_${habitacionId}_${nuevaPasajeroIndex}" name="habitaciones[${habitacionId}][pasajeros][nuevo_${nuevaPasajeroIndex}][caducidad_pasaporte]" value="">
                </div>
            </div>
            <div class="col-md-1 d-flex align-items-end">
                <a href="#" class="btn btn-outline-danger eliminar-pasajero"><i class="fas fa-trash-alt"></i></a>
            </div>
        `;
        pasajerosContainer.appendChild(nuevoPasajero);

        initializeSingleDatePicker(`#fecha_nacimiento_pasajero_${habitacionId}_${nuevaPasajeroIndex}`, `edad_pasajero_${habitacionId}_${nuevaPasajeroIndex}`);
        initializeSingleDatePicker(`#caducidad_pasaporte_${habitacionId}_${nuevaPasajeroIndex}`);
    }

    // Maneja el cambio en los inputs de número de adultos y niños, agregando o eliminando pasajeros en consecuencia.
    function manejarCambioPasajeros(habitacionId, adultosInput, ninosInput) {
        const pasajerosContainer = document.querySelector(`.habitacion[data-id="${habitacionId}"] .pasajeros-container`);

        // Actualizar pasajeros adultos
        let pasajerosAdultos = pasajerosContainer.querySelectorAll('.pasajero[data-tipo="adulto"]');
        const nuevosAdultos = parseInt(adultosInput.value) - pasajerosAdultos.length;

        if (nuevosAdultos > 0) {
            for (let i = 0; i < nuevosAdultos; i++) {
                agregarPasajero(pasajerosContainer, habitacionId, 'adulto');
            }
        } else if (nuevosAdultos < 0) {
            for (let i = 0; i < Math.abs(nuevosAdultos); i++) {
                pasajerosAdultos[i].remove();
            }
        }

        // Actualizar pasajeros niños
        let pasajerosNinos = pasajerosContainer.querySelectorAll('.pasajero[data-tipo="nino"]');
        const nuevosNinos = parseInt(ninosInput.value) - pasajerosNinos.length;

        if (nuevosNinos > 0) {
            for (let i = 0; i < nuevosNinos; i++) {
                agregarPasajero(pasajerosContainer, habitacionId, 'nino');
            }
        } else if (nuevosNinos < 0) {
            for (let i = 0; i < Math.abs(nuevosNinos); i++) {
                pasajerosNinos[i].remove();
            }
        }
    }

    document.querySelectorAll('.habitacion-select').forEach(selectElement => {
        const habitacionId = selectElement.getAttribute('data-forloop-counter');
        const adultosInput = document.getElementById(`adultos_${habitacionId}`);
        const ninosInput = document.getElementById(`ninos_${habitacionId}`);

        selectElement.addEventListener('change', function() {
            validarCapacidadHabitacion(habitacionId);
        });

        adultosInput.addEventListener('change', function() {
            validarCapacidadHabitacion(habitacionId);
            manejarCambioPasajeros(habitacionId, adultosInput, ninosInput);
        });

        ninosInput.addEventListener('change', function() {
            validarCapacidadHabitacion(habitacionId);
            manejarCambioPasajeros(habitacionId, adultosInput, ninosInput);
        });

        validarCapacidadHabitacion(habitacionId);
    });

    document.getElementById('agregar-habitacion').addEventListener('click', function() {
        const nuevaHabitacionIndex = habitacionesContainer.children.length + 1;
        const nuevaHabitacion = document.createElement('div');
        nuevaHabitacion.className = 'card mt-3 mb-3';
        nuevaHabitacion.innerHTML = `
            <div class="card-body habitacion" data-id="nueva_${nuevaHabitacionIndex}">
                <h4>Habitación Nueva</h4>
                <div class="row">
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="habitacion_nombre_nueva_${nuevaHabitacionIndex}"><strong>Nombre de Habitación</strong></label>
                            <select class="form-control habitacion-select" id="habitacion_nombre_nueva_${nuevaHabitacionIndex}" name="habitaciones[nueva_${nuevaHabitacionIndex}][nombre]" data-forloop-counter="nueva_${nuevaHabitacionIndex}">
                                {% for tipo in tipos_habitacion %}
                                <option value="{{ tipo.tipo }}" data-solo-adultos="{{ tipo.solo_adultos }}" data-max-adultos="{{ tipo.adultos }}" data-max-ninos="{{ tipo.ninos }}" data-max-capacidad="{{ tipo.max_capacidad }}" data-min-capacidad="{{ tipo.min_capacidad }}">{{ tipo.tipo }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <div class="form-group">
                            <label for="adultos_nueva_${nuevaHabitacionIndex}"><strong>Adultos</strong></label>
                            <input type="number" class="form-control adultos-input" id="adultos_nueva_${nuevaHabitacionIndex}" name="habitaciones[nueva_${nuevaHabitacionIndex}][adultos]" value="0" data-forloop-counter="nueva_${nuevaHabitacionIndex}">
                        </div>
                    </div>
                    <div class="col-md-1">
                        <div class="form-group">
                            <label for="ninos_nueva_${nuevaHabitacionIndex}"><strong>Niños</strong></label>
                            <input type="number" class="form-control ninos-input" id="ninos_nueva_${nuevaHabitacionIndex}" name="habitaciones[nueva_${nuevaHabitacionIndex}][ninos]" value="0" data-forloop-counter="nueva_${nuevaHabitacionIndex}">
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="fechas_viaje_nueva_${nuevaHabitacionIndex}"><strong>Fechas de Viaje</strong></label>
                            <input type="text" class="form-control daterange" id="fechas_viaje_nueva_${nuevaHabitacionIndex}" name="habitaciones[nueva_${nuevaHabitacionIndex}][fechas_viaje]" value="01/01/2018 - 01/15/2018">
                        </div>
                    </div>
                    <div class="col-md-1 d-flex align-items-end">
                        <a href="#" class="btn btn-outline-danger eliminar-habitacion"><i class="fas fa-trash-alt"></i></a>
                    </div>
                </div>
                <div class="card mt-3 mb-3">
                    <div class="card-body">
                        <h5>Pasajeros</h5>
                        <div class="pasajeros-container"></div>
                        <button type="button" class="btn btn-success agregar-pasajero" data-habitacion-id="nueva_${nuevaHabitacionIndex}">Agregar Pasajero</button>
                    </div>
                </div>
            </div>
        `;
        habitacionesContainer.appendChild(nuevaHabitacion);

        $(`#fechas_viaje_nueva_${nuevaHabitacionIndex}`).daterangepicker({
            opens: 'left',
            locale: {
              format: 'MM/DD/YYYY'
            }
        }, function(start, end, label) {
            console.log("A new date selection was made: " + start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'));
        });

        const newHabitacionSelect = document.getElementById(`habitacion_nombre_nueva_${nuevaHabitacionIndex}`);
        const newAdultosInput = document.getElementById(`adultos_nueva_${nuevaHabitacionIndex}`);
        const newNinosInput = document.getElementById(`ninos_nueva_${nuevaHabitacionIndex}`);

        newHabitacionSelect.addEventListener('change', function() {
            validarCapacidadHabitacion(`nueva_${nuevaHabitacionIndex}`);
        });

        newAdultosInput.addEventListener('change', function() {
            validarCapacidadHabitacion(`nueva_${nuevaHabitacionIndex}`);
            manejarCambioPasajeros(`nueva_${nuevaHabitacionIndex}`, newAdultosInput, newNinosInput);
        });

        newNinosInput.addEventListener('change', function() {
            validarCapacidadHabitacion(`nueva_${nuevaHabitacionIndex}`);
            manejarCambioPasajeros(`nueva_${nuevaHabitacionIndex}`, newAdultosInput, newNinosInput);
        });
    });

    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('agregar-pasajero')) {
            const habitacionId = event.target.getAttribute('data-habitacion-id');
            $('#pasajeroModal').data('habitacion-id', habitacionId).modal('show');
        }

        if (event.target.classList.contains('eliminar-habitacion') || event.target.closest('.eliminar-habitacion')) {
            const habitacion = event.target.closest('.habitacion');
            habitacion.remove();
        }

        if (event.target.classList.contains('eliminar-pasajero') || event.target.closest('.eliminar-pasajero')) {
            const pasajero = event.target.closest('.pasajero');
            pasajero.remove();
        }
    });

    document.querySelectorAll('.habitacion').forEach(habitacionElement => {
        const habitacionId = habitacionElement.getAttribute('data-id');
        const adultosInput = document.getElementById(`adultos_${habitacionId}`);
        const ninosInput = document.getElementById(`ninos_${habitacionId}`);

        validarCapacidadHabitacion(habitacionId);

        adultosInput.addEventListener('change', function() {
            manejarCambioPasajeros(habitacionId, adultosInput, ninosInput);
        });

        ninosInput.addEventListener('change', function() {
            manejarCambioPasajeros(habitacionId, adultosInput, ninosInput);
        });

        habitacionElement.querySelectorAll('.fecha-nacimiento').forEach(fechaNacimientoInput => {
            fechaNacimientoInput.addEventListener('change', function() {
                const edadInput = fechaNacimientoInput.parentElement.parentElement.querySelector('.edad');
                if (edadInput) {
                    edadInput.value = calcularEdad(fechaNacimientoInput.value);
                }
            });
        });
    });

    document.querySelectorAll('.daterange').forEach(element => {
        initializeDateRangePicker(element);
    });
});

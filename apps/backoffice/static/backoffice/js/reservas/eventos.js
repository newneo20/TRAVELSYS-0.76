document.addEventListener('DOMContentLoaded', function() {
    const habitacionesContainer = document.getElementById('habitaciones-container');
    
    document.querySelectorAll('.habitacion-select').forEach(selectElement => {
        const habitacionId = selectElement.getAttribute('data-forloop-counter');
        selectElement.addEventListener('change', function() {
            validarCapacidadHabitacion(habitacionId);
        });

        document.getElementById(`adultos_${habitacionId}`).addEventListener('change', function() {
            validarCapacidadHabitacion(habitacionId);
        });

        document.getElementById(`ninos_${habitacionId}`).addEventListener('change', function() {
            validarCapacidadHabitacion(habitacionId);
        });

        // Validar al cargar la página
        validarCapacidadHabitacion(habitacionId);
    });

    document.getElementById('agregar-habitacion').addEventListener('click', function() {
        const nuevaHabitacionIndex = agregarHabitacion(habitacionesContainer, tiposHabitacion);

        // Añadir event listeners para la nueva habitación
        const newHabitacionSelect = document.getElementById(`habitacion_nombre_nueva_${nuevaHabitacionIndex}`);
        const newAdultosInput = document.getElementById(`adultos_nueva_${nuevaHabitacionIndex}`);
        const newNinosInput = document.getElementById(`ninos_nueva_${nuevaHabitacionIndex}`);
        const newFechasInput = document.getElementById(`fechas_viaje_nueva_${nuevaHabitacionIndex}`);

        newHabitacionSelect.addEventListener('change', function() {
            validarCapacidadHabitacion(`nueva_${nuevaHabitacionIndex}`);
        });

        newAdultosInput.addEventListener('change', function() {
            validarCapacidadHabitacion(`nueva_${nuevaHabitacionIndex}`);
        });

        newNinosInput.addEventListener('change', function() {
            validarCapacidadHabitacion(`nueva_${nuevaHabitacionIndex}`);
        });

        // Inicializa el daterangepicker en el nuevo campo de fechas
        inicializarRangoFecha(newFechasInput);

        // Inicializa el picker de fecha única en los campos de fecha de nacimiento y caducidad pasaporte
        const nuevoFechaNacimientoInput = document.getElementById(`fecha_nacimiento_pasajero_nueva_${nuevaHabitacionIndex}`);
        inicializarPickerFechaUnica(nuevoFechaNacimientoInput, `edad_pasajero_${nuevaHabitacionIndex}`);
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
});

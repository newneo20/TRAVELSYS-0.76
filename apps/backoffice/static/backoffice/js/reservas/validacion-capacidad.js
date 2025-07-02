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

function validarCapacidadHabitacion(habitacionId) {
    const habitacionSelect = document.getElementById(`habitacion_nombre_${habitacionId}`);
    const adultosInput = document.getElementById(`adultos_${habitacionId}`);
    const ninosInput = document.getElementById(`ninos_${habitacionId}`);

    const soloAdultos = habitacionSelect.selectedOptions[0].getAttribute('data-solo-adultos') === 'True';
    const maxAdultos = parseInt(habitacionSelect.selectedOptions[0].getAttribute('data-max-adultos'));
    const maxNinos = parseInt(habitacionSelect.selectedOptions[0].getAttribute('data-max-ninos'));
    const maxCapacidad = parseInt(habitacionSelect.selectedOptions[0].getAttribute('data-max-capacidad'));
    const minCapacidad = parseInt(habitacionSelect.selectedOptions[0].getAttribute('data-min-capacidad'));

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

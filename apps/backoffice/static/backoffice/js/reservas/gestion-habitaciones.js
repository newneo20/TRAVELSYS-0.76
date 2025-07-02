function agregarHabitacion(habitacionesContainer, tiposHabitacion) {
    const nuevaHabitacionIndex = habitacionesContainer.children.length + 1; // Nuevo índice
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
                            ${tiposHabitacion.map(tipo => `<option value="${tipo.tipo}" data-solo-adultos="${tipo.solo_adultos}" data-max-adultos="${tipo.adultos}" data-max-ninos="${tipo.ninos}" data-max-capacidad="${tipo.max_capacidad}" data-min-capacidad="${tipo.min_capacidad}">${tipo.tipo}</option>`).join('')}
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
                        <input type="text" class="form-control daterange" id="fechas_viaje_nueva_${nuevaHabitacionIndex}" name="habitaciones[nueva_${nuevaHabitacionIndex}][fechas_viaje]" value="">
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

    return nuevaHabitacionIndex;
}

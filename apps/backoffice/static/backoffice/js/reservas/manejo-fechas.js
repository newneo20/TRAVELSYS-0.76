function inicializarRangoFecha(elemento) {
    $(elemento).daterangepicker({
        opens: 'left',
        locale: {
            format: 'MMMM D, YYYY'  // Formato para daterangepicker
        }
    }, function(start, end, label) {
        console.log("Se ha realizado una nueva selección de fecha: " + start.format('MMMM D, YYYY') + ' hasta ' + end.format('MMMM D, YYYY'));
    });
}

function inicializarPickerFechaUnica(elemento, campoEdadId) {
    $(elemento).daterangepicker({
        singleDatePicker: true,
        showDropdowns: true,
        minYear: 1901,
        maxYear: parseInt(moment().format('YYYY'), 10),
        locale: {
            format: 'MMMM D, YYYY'  // Formato de la fecha
        }
    }, function(start, end, label) {
        if (campoEdadId) {
            const edadInput = document.getElementById(campoEdadId);
            if (edadInput) {
                edadInput.value = calcularEdad(start.format('YYYY-MM-DD'));
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Gráfico de Reservas Mensuales
    const ctxReservas = document.getElementById('reservasMensualesChart').getContext('2d');
    new Chart(ctxReservas, {
        type: 'line',
        data: {
            labels: {{ labels_meses|safe }},
            datasets: [{
                label: 'Reservas',
                data: {{ datos_reservas_mensuales|safe }},
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                borderColor: 'rgba(13, 110, 253, 1)',
                tension: 0.4,
                fill: true,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: { grid: { display: false } },
                y: { beginAtZero: true }
            }
        }
    });

    // Gráfico de Ingresos y Gastos
    const ctxIngresosGastos = document.getElementById('ingresosGastosChart').getContext('2d');
    new Chart(ctxIngresosGastos, {
        type: 'bar',
        data: {
            labels: {{ labels_meses|safe }},
            datasets: [
                {
                    label: 'Ingresos',
                    data: {{ datos_ingresos|safe }},
                    backgroundColor: 'rgba(25, 135, 84, 0.7)',
                },
                {
                    label: 'Gastos',
                    data: {{ datos_gastos|safe }},
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
            },
            scales: {
                x: { stacked: true },
                y: { beginAtZero: true, stacked: true }
            }
        }
    });
});

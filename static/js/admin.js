// Funções para área administrativa
document.addEventListener('DOMContentLoaded', function() {
    // Inicializa todos os tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Inicializa todos os modals
    var modalTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="modal"]'))
    var modalList = modalTriggerList.map(function (modalTriggerEl) {
        return new bootstrap.Modal(modalTriggerEl)
    });
});

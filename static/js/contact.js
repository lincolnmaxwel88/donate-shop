document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // Validação do formulário
    const form = document.querySelector('.needs-validation');
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }

    // Máscara para o telefone
    const phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value;

            // Remove todos os caracteres que não são números
            value = value.replace(/\D/g, '');

            // Adiciona a máscara ao telefone
            if (value.length <= 2) {
                value = `(${value}`;
            } else if (value.length <= 7) {
                value = `(${value.slice(0, 2)}) ${value.slice(2)}`;
            } else {
                value = `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7, 11)}`;
            }

            // Limita o tamanho máximo a 15 caracteres
            value = value.slice(0, 15);

            // Atualiza o valor no campo
            e.target.value = value;
        });

        // Adiciona validação personalizada
        phoneInput.addEventListener('change', function(e) {
            const phonePattern = /^\([0-9]{2}\) [0-9]{5}-[0-9]{4}$/;
            if (!phonePattern.test(e.target.value)) {
                e.target.setCustomValidity('Por favor, informe um telefone válido no formato (99) 99999-9999');
            } else {
                e.target.setCustomValidity('');
            }
        });
    }
});

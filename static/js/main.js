// Validate donation amount
document.addEventListener('DOMContentLoaded', function() {
    const donationForm = document.querySelector('form[action*="donate"]');
    if (donationForm) {
        donationForm.addEventListener('submit', function(e) {
            const amount = document.getElementById('amount').value;
            if (!amount || parseFloat(amount.replace(/\./g, '').replace(',', '.')) <= 0) {
                e.preventDefault();
                alert('Por favor, insira um valor válido para doação.');
            }
        });
    }
});

        document.getElementById("goal").addEventListener("input", function (e) {
            let value = e.target.value;

            // Remove caracteres que não sejam números
            value = value.replace(/\D/g, "");

            // Adiciona a vírgula para os centavos
            value = (value / 100).toFixed(2).replace(".", ",");

            // Adiciona os pontos para separar os milhares
            value = value.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

            // Atualiza o campo de entrada
            e.target.value = value;
        });

// Format currency input
function formatCurrency(value) {
    // Remove tudo que não é número
    value = value.replace(/\D/g, '');
    
    // Adiciona os centavos
    value = (value / 100).toFixed(2);
    
    // Converte para o formato brasileiro (1.234,56)
    value = value.replace('.', ',');
    
    // Adiciona os pontos para milhares
    if (value.length > 6) {
        value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
    }
    
    return value;
}

// Handle currency input
document.addEventListener('DOMContentLoaded', function() {
    const goalInput = document.getElementById('goal');
    const amountInput = document.getElementById('amount');
    
    const handleCurrencyInput = (input) => {
        if (!input) return;
        
        // Adiciona R$ no início do campo quando ganhar foco
        input.addEventListener('focus', function(e) {
            if (!e.target.value) {
                e.target.value = '';
            }
        });
        
        input.addEventListener('input', function(e) {
            let value = e.target.value;
            
            // Remove tudo que não é número
            value = value.replace(/\D/g, '');
            
            if (value === '') {
                e.target.value = '';
                return;
            }
            
            // Formata o valor
            e.target.value = formatCurrency(value);
        });
        
        // Formata quando o campo perde o foco
        input.addEventListener('blur', function(e) {
            if (!e.target.value) return;
            
            let value = e.target.value.replace(/\D/g, '');
            if (value === '') {
                e.target.value = '';
                return;
            }
            
            e.target.value = formatCurrency(value);
        });
    };
    
    handleCurrencyInput(goalInput);
    handleCurrencyInput(amountInput);
});

// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 3000);
    });
});

function formatCurrency(input) {
    let value = input.value.replace(/\D/g, '');
    value = (value / 100).toFixed(2) + '';
    value = value.replace(".", ",");
    value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
    input.value = value;
}
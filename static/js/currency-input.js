// Função para formatar campos de moeda no padrão brasileiro
function formatCurrencyInput(input) {
    // Remove tudo que não é número
    let value = input.value.replace(/\D/g, '');
    
    // Converte para centavos
    value = parseInt(value) / 100;
    
    // Formata para o padrão brasileiro
    const formatter = new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    // Remove o símbolo R$ pois ele já está no prefixo do input
    let formattedValue = formatter.format(value).replace('R$', '').trim();
    
    // Atualiza o valor do input
    input.value = formattedValue;
}

// Função para inicializar todos os campos de moeda
function initCurrencyInputs() {
    // Seleciona todos os inputs com a classe currency-input
    document.querySelectorAll('.currency-input').forEach(input => {
        // Adiciona o evento de input
        input.addEventListener('input', function() {
            formatCurrencyInput(this);
        });
        
        // Formata o valor inicial se existir
        if (input.value) {
            formatCurrencyInput(input);
        }
        
        // Quando o campo perde o foco, garante que tenha pelo menos "0,00"
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.value = '0,00';
            }
        });
        
        // Quando o campo recebe foco, remove o valor "0,00" para facilitar a digitação
        input.addEventListener('focus', function() {
            if (this.value === '0,00') {
                this.value = '';
            }
        });
    });
}

// Inicializa os campos quando o documento carrega
document.addEventListener('DOMContentLoaded', initCurrencyInputs);

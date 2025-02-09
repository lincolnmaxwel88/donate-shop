// Variáveis globais
let currentForm = null;

// Função para formatar valor monetário
function formatCurrency(value) {
    // Remove tudo que não é número
    value = value.replace(/\D/g, '');
    
    // Converte para número e divide por 100 para ter os centavos
    value = (parseInt(value) / 100).toFixed(2);
    
    // Formata com pontos e vírgulas
    value = value.replace('.', ',');
    value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
    
    return value;
}

// Função para inicializar os campos de moeda
function initializeCurrencyFields() {
    // Procura por campos de moeda
    const currencyFields = document.querySelectorAll('.currency-input');
    
    if (currencyFields.length > 0) {
        currencyFields.forEach(field => {
            // Formata o valor inicial
            if (field.value) {
                field.value = formatCurrency(field.value);
            }
            
            // Adiciona os event listeners
            field.addEventListener('input', function(e) {
                let value = e.target.value;
                e.target.value = formatCurrency(value);
            });
            
            field.addEventListener('blur', function(e) {
                let value = e.target.value;
                if (!value) {
                    e.target.value = '0,00';
                }
            });
            
            field.addEventListener('focus', function(e) {
                if (e.target.value === '0,00') {
                    e.target.value = '';
                }
            });
        });
    }
}

// Funções do Modal
function showModal(amount) {
    const modal = document.getElementById('confirmModal');
    const overlay = document.getElementById('modalOverlay');
    const amountElement = modal.querySelector('.donation-amount');
    
    // Atualiza o valor
    amountElement.textContent = `R$ ${amount}`;
    
    // Mostra o modal e overlay com animação
    overlay.style.display = 'block';
    modal.style.display = 'block';
    
    // Força o reflow para a animação funcionar
    modal.offsetHeight;
    
    // Adiciona as classes de animação
    overlay.classList.add('fade-in');
    modal.classList.add('fade-in');
}

function closeModal() {
    const modal = document.getElementById('confirmModal');
    const overlay = document.getElementById('modalOverlay');
    
    // Adiciona animação de saída
    overlay.classList.remove('fade-in');
    modal.classList.remove('fade-in');
    overlay.classList.add('fade-out');
    modal.classList.add('fade-out');
    
    // Esconde após a animação
    setTimeout(() => {
        modal.style.display = 'none';
        overlay.style.display = 'none';
        overlay.classList.remove('fade-out');
        modal.classList.remove('fade-out');
    }, 200);
}

function confirmDonation() {
    if (currentForm) {
        prepareSubmit(currentForm);
        currentForm.submit();
    }
}

// Função para preparar o valor antes de enviar
function prepareSubmit(form) {
    let input = form.querySelector('input[name="amount"]');
    // Remove pontos e troca vírgula por ponto
    let value = input.value.replace(/\./g, '').replace(',', '.');
    input.value = value;
    return true;
}

// Inicializa quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    initializeCurrencyFields();
    
    // Adiciona confirmação ao formulário
    let form = document.querySelector('.donation-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Previne o envio do formulário
            e.preventDefault();
            
            // Guarda o formulário atual
            currentForm = this;
            
            // Pega o valor atual
            let input = this.querySelector('input[name="amount"]');
            let amount = input.value;
            
            // Mostra o modal de confirmação
            showModal(amount);
        });
    }
    
    // Fecha o modal se clicar fora
    document.getElementById('modalOverlay').addEventListener('click', closeModal);
});

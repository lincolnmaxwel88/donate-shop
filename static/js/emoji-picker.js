document.addEventListener('DOMContentLoaded', function() {
    const descriptionInput = document.getElementById('description');
    const emojiButtons = document.querySelectorAll('.emoji-btn');

    emojiButtons.forEach(button => {
        button.addEventListener('click', function() {
            const emoji = this.dataset.emoji;
            const cursorPos = descriptionInput.selectionStart;
            const textBefore = descriptionInput.value.substring(0, cursorPos);
            const textAfter = descriptionInput.value.substring(cursorPos);
            
            // Insere o emoji na posição do cursor
            descriptionInput.value = textBefore + emoji + textAfter;
            
            // Atualiza a posição do cursor para depois do emoji
            const newCursorPos = cursorPos + emoji.length;
            descriptionInput.setSelectionRange(newCursorPos, newCursorPos);
            
            // Mantém o foco no campo de texto
            descriptionInput.focus();
            
            // Adiciona animação ao botão
            button.classList.add('active');
            setTimeout(() => button.classList.remove('active'), 200);
        });
    });
});

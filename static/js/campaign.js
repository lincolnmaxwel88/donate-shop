document.addEventListener('DOMContentLoaded', function() {
    // Manipulador de likes
    const likeButtons = document.querySelectorAll('.btn-like');
    
    function createHeartParticles(button, liked) {
        const numParticles = liked ? 5 : 3;
        const colors = liked ? ['❤️', '💖', '💝', '💕', '💗'] : ['💔'];
        
        for (let i = 0; i < numParticles; i++) {
            const particle = document.createElement('span');
            particle.className = 'heart-particle';
            particle.textContent = colors[Math.floor(Math.random() * colors.length)];
            
            // Posição aleatória
            const angle = (Math.random() * Math.PI * 2);
            const distance = 50 + Math.random() * 50;
            const tx = Math.cos(angle) * distance;
            const ty = Math.sin(angle) * distance - 50;
            
            particle.style.setProperty('--tx', `${tx}px`);
            particle.style.setProperty('--ty', `${ty}px`);
            
            button.appendChild(particle);
            
            // Remover partícula após a animação
            setTimeout(() => particle.remove(), 1000);
        }
    }

    likeButtons.forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const campaignId = this.getAttribute('data-campaign-id');
            const icon = this.querySelector('i');
            const likeCount = this.nextElementSibling;
            
            try {
                const response = await fetch(`/like/${campaignId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    likeCount.textContent = data.likes_count;
                    
                    // Alternar classe 'liked' e ícone
                    this.classList.toggle('liked');
                    const isLiked = this.classList.contains('liked');
                    
                    // Remover classes de animação anteriores
                    icon.classList.remove('heart-beat', 'heart-pop', 'heart-break');
                    
                    // Adicionar nova animação
                    if (isLiked) {
                        icon.classList.add('heart-pop');
                        createHeartParticles(this, true);
                    } else {
                        icon.classList.add('heart-break');
                        createHeartParticles(this, false);
                    }
                    
                    // Atualizar ícone
                    icon.className = isLiked ? 'fas fa-heart' : 'far fa-heart';
                }
            } catch (error) {
                console.error('Erro ao processar like:', error);
            }
        });
    });

    // Função para lidar com o like de forma assíncrona
    const likeForm = document.querySelector('.like-form');
    if (likeForm) {
        likeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                const likeButton = this.querySelector('button');
                const likeCount = document.querySelector('.like-count');
                
                if (data.liked) {
                    likeButton.classList.remove('btn-outline-danger');
                    likeButton.classList.add('btn-danger');
                    likeButton.innerHTML = '<i class="fas fa-heart"></i> Curtido';
                } else {
                    likeButton.classList.remove('btn-danger');
                    likeButton.classList.add('btn-outline-danger');
                    likeButton.innerHTML = '<i class="fas fa-heart"></i> Curtir';
                }
                
                likeCount.textContent = data.likes_count + ' curtida(s)';
            })
            .catch(error => {
                console.error('Erro:', error);
            });
        });
    }
});

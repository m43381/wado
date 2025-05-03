document.addEventListener('DOMContentLoaded', function() {
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature-card, .section-title');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.3;
            
            if (elementPosition < screenPosition) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };
    
    // Инициализация
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease';
    });
    
    const sectionTitle = document.querySelector('.section-title');
    sectionTitle.style.opacity = '0';
    sectionTitle.style.transform = 'translateY(20px)';
    sectionTitle.style.transition = 'all 0.6s ease';
    
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Запустить сразу для видимых элементов
});
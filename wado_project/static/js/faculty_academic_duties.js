// static/js/faculty_duties_simple.js

document.addEventListener('DOMContentLoaded', function() {
    initDutiesPage();
});

function initDutiesPage() {
    // Подсветка сегодняшней даты
    highlightToday();
    
    // Инициализация кликабельных строк
    initClickableRows();
    
    // Инициализация статистики
    initStatsAnimation();
}

function highlightToday() {
    const todayRows = document.querySelectorAll('.today-row');
    todayRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#e8f4fc';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '#f0f9ff';
        });
    });
}

function initClickableRows() {
    const rows = document.querySelectorAll('.duties-table tbody tr');
    
    rows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Не открываем детали если кликнули на ссылку
            if (e.target.tagName === 'A') return;
            
            const dateCell = this.querySelector('.date-cell');
            const date = dateCell.querySelector('.date-day').textContent;
            const month = document.querySelector('.month-name').textContent;
            
            // Показываем информацию о дне
            showDayInfo(date, month, this);
        });
    });
}

function showDayInfo(day, month, row) {
    // Находим все наряды этого дня
    const duties = row.querySelectorAll('.duty-item');
    const units = row.querySelectorAll('.unit-item');
    
    if (duties.length === 0) return;
    
    // Создаем простой popup
    let message = `📅 ${day} ${month}\n\n`;
    
    duties.forEach((duty, index) => {
        const dutyName = duty.querySelector('.duty-name').textContent;
        const unitInfo = units[index] ? units[index].textContent : '';
        
        message += `• ${dutyName}\n`;
        if (unitInfo) {
            message += `  ${unitInfo}\n`;
        }
        message += '\n';
    });
    
    alert(message);
}

function initStatsAnimation() {
    // Простая анимация для статистических карточек
    const statCards = document.querySelectorAll('.stat-card');
    
    statCards.forEach((card, index) => {
        // Задержка для появления
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Вспомогательные функции
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}
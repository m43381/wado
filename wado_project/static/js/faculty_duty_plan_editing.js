// faculty_duty_plan_editing.js - адаптация для факультета

function initFacultyEditingFunctionality() {
    console.log('🎓 Инициализация редактирования факультетских нарядов');
    
    // Используем те же функции что и в duty_plan_editing.js
    // но адаптируем их для факультета
    
    // Функции openUnitModal и openQuickUnitModal уже определены в faculty_duty_plan.js
    // и переопределяются здесь для совместимости
    
    if (typeof window.openUnitModal === 'function') {
        console.log('✅ Функции редактирования уже инициализированы');
        return;
    }
    
    // Если функции не определены, создаем простые реализации
    window.openUnitModal = function(scheduleId) {
        currentScheduleId = scheduleId;
        document.getElementById('currentScheduleId').value = scheduleId;
        document.getElementById('unitSelectModal').style.display = 'block';
    };
    
    window.openQuickUnitModal = function(scheduleId, dutyName) {
        currentScheduleId = scheduleId;
        document.getElementById('quickScheduleId').value = scheduleId;
        document.getElementById('quickDutyName').textContent = dutyName;
        
        // Заполняем список подразделений
        const quickUnitsGrid = document.getElementById('quickUnitsGrid');
        quickUnitsGrid.innerHTML = '';
        
        // Управление факультета
        const managementItem = document.createElement('div');
        managementItem.className = 'quick-unit-item';
        managementItem.innerHTML = `
            <div class="quick-unit-name">🏢 Управление факультета</div>
            <button class="btn-select-unit" onclick="updateFacultyAssignment('management', 'management', 'Управление факультета')">
                Выбрать
            </button>
        `;
        quickUnitsGrid.appendChild(managementItem);
        
        // Кафедры из DOM
        const departments = document.querySelectorAll('.unit-item[data-type="department"]');
        departments.forEach(department => {
            const deptItem = document.createElement('div');
            deptItem.className = 'quick-unit-item';
            deptItem.innerHTML = `
                <div class="quick-unit-name">🏛️ ${department.textContent}</div>
                <button class="btn-select-unit" onclick="updateFacultyAssignment('department', '${department.dataset.id}', '${department.textContent}')">
                    Выбрать
                </button>
            `;
            quickUnitsGrid.appendChild(deptItem);
        });
        
        document.getElementById('quickUnitModal').style.display = 'block';
    };
    
    window.updateFacultyAssignment = function(unitType, unitId, unitName) {
        const scheduleId = document.getElementById('quickScheduleId').value;
        const formData = new FormData();
        formData.append('unit_type', unitType);
        formData.append('unit_id', unitId);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        fetch('/faculty/schedules/' + scheduleId + '/update/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            alert('Ошибка сети');
        });
    };
    
    // Инициализация обработчиков для модальных окон
    const unitModal = document.getElementById('unitSelectModal');
    const quickModal = document.getElementById('quickUnitModal');
    
    if (unitModal) {
        const closeBtn = unitModal.querySelector('.close');
        const cancelBtn = document.getElementById('cancelSelection');
        
        closeBtn.addEventListener('click', function() {
            unitModal.style.display = 'none';
        });
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                unitModal.style.display = 'none';
            });
        }
        
        window.addEventListener('click', function(event) {
            if (event.target === unitModal) {
                unitModal.style.display = 'none';
            }
        });
        
        // Обработчики для выбора подразделения
        document.querySelectorAll('.unit-item').forEach(item => {
            item.addEventListener('click', function() {
                const scheduleId = document.getElementById('currentScheduleId').value;
                const unitType = this.dataset.type;
                const unitId = this.dataset.id;
                const unitName = this.textContent.trim();
                
                updateFacultyAssignment(unitType, unitId, unitName);
            });
        });
    }
    
    if (quickModal) {
        const quickCloseBtn = quickModal.querySelector('.quick-close');
        const cancelQuickBtn = document.getElementById('cancelQuickSelection');
        
        quickCloseBtn.addEventListener('click', function() {
            quickModal.style.display = 'none';
        });
        
        if (cancelQuickBtn) {
            cancelQuickBtn.addEventListener('click', function() {
                quickModal.style.display = 'none';
            });
        }
        
        window.addEventListener('click', function(event) {
            if (event.target === quickModal) {
                quickModal.style.display = 'none';
            }
        });
    }
    
    console.log('✅ Редактирование факультетских нарядов инициализировано');
}

// Запускаем при загрузке документа
document.addEventListener('DOMContentLoaded', function() {
    initFacultyEditingFunctionality();
});
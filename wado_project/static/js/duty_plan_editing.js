// duty_plan_editing.js - функционал редактирования записей

document.addEventListener('DOMContentLoaded', function() {
    initEditingFunctionality();
});

function initEditingFunctionality() {
    // Глобальные переменные
    let currentScheduleId = null;

    // Вспомогательные функции
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    function showToastMessage(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast-message toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }

    // === ОСНОВНОЕ МОДАЛЬНОЕ ОКНО ===

    function openUnitModal(scheduleId) {
        currentScheduleId = scheduleId;
        document.getElementById('currentScheduleId').value = scheduleId;
        document.getElementById('unitSelectModal').style.display = 'block';
    }

    function closeUnitModal() {
        document.getElementById('unitSelectModal').style.display = 'none';
        currentScheduleId = null;
    }

    // === БЫСТРОЕ МОДАЛЬНОЕ ОКНО ДЛЯ КАЛЕНДАРЯ ===

    function openQuickUnitModal(scheduleId, dutyName) {
        currentScheduleId = scheduleId;
        document.getElementById('quickScheduleId').value = scheduleId;
        document.getElementById('quickDutyName').textContent = dutyName;
        
        populateQuickUnits();
        document.getElementById('quickUnitModal').style.display = 'block';
    }

    function populateQuickUnits() {
        const quickUnitsGrid = document.getElementById('quickUnitsGrid');
        quickUnitsGrid.innerHTML = '';
        
        // Берем ВСЕ факультеты для быстрого выбора
        const faculties = Array.from(document.querySelectorAll('.unit-item[data-type="faculty"]'));
        faculties.forEach(faculty => {
            const unitItem = document.createElement('div');
            unitItem.className = 'quick-unit-item';
            unitItem.textContent = faculty.textContent;
            unitItem.onclick = () => {
                updateScheduleAssignment(
                    currentScheduleId, 
                    faculty.dataset.type, 
                    faculty.dataset.id, 
                    faculty.textContent.trim()
                );
                closeQuickModal();
            };
            quickUnitsGrid.appendChild(unitItem);
        });
        
        // Берем ВСЕ кафедры для быстрого выбора
        const departments = Array.from(document.querySelectorAll('.unit-item[data-type="department"]'));
        departments.forEach(department => {
            const unitItem = document.createElement('div');
            unitItem.className = 'quick-unit-item';
            unitItem.textContent = department.textContent;
            unitItem.onclick = () => {
                updateScheduleAssignment(
                    currentScheduleId, 
                    department.dataset.type, 
                    department.dataset.id, 
                    department.textContent.trim()
                );
                closeQuickModal();
            };
            quickUnitsGrid.appendChild(unitItem);
        });
    }

    function closeQuickModal() {
        document.getElementById('quickUnitModal').style.display = 'none';
        currentScheduleId = null;
    }

    // === ОБНОВЛЕНИЕ НАЗНАЧЕНИЙ ===

    function updateScheduleAssignment(scheduleId, unitType, unitId, unitName) {
        const formData = new FormData();
        formData.append('unit_type', unitType);
        formData.append('unit_id', unitId);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        fetch(`/commandant/schedules/${scheduleId}/update/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateScheduleDisplay(scheduleId, unitType, unitName);
                updateCalendarDisplay(scheduleId, unitType, unitName);
                showToastMessage('Назначение успешно обновлено', 'success');
            } else {
                showToastMessage('Ошибка: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToastMessage('Ошибка при обновлении назначения', 'error');
        });
    }

    function updateScheduleDisplay(scheduleId, unitType, unitName) {
        const scheduleRow = document.querySelector(`tr[data-schedule-id="${scheduleId}"]`);
        if (scheduleRow) {
            const unitCell = scheduleRow.querySelector('.unit-display');
            const typeCell = scheduleRow.querySelector('.assignment-type');
            
            if (unitType === 'faculty') {
                unitCell.innerHTML = `Факультет: ${unitName}`;
            } else {
                unitCell.innerHTML = `Кафедра: ${unitName}`;
            }
            typeCell.innerHTML = '<span class="badge badge-changed">Изменен</span>';
            
            scheduleRow.classList.add('schedule-updated');
            setTimeout(() => {
                scheduleRow.classList.remove('schedule-updated');
            }, 1000);
        }
    }

    function updateCalendarDisplay(scheduleId, unitType, unitName) {
        const scheduleElement = document.querySelector(`.clickable-duty[data-schedule-id="${scheduleId}"]`);
        if (scheduleElement) {
            const assignedUnit = scheduleElement.querySelector('.plan-assigned-unit');
            if (assignedUnit) {
                if (unitType === 'faculty') {
                    assignedUnit.innerHTML = `Ф: ${unitName} *`;
                } else {
                    assignedUnit.innerHTML = `К: ${unitName} *`;
                }
                assignedUnit.classList.add('changed');
            }
            
            scheduleElement.classList.add('manual-assignment', 'schedule-updated');
            setTimeout(() => {
                scheduleElement.classList.remove('schedule-updated');
            }, 1000);
        }
    }

    // === ИНИЦИАЛИЗАЦИЯ ОБРАБОТЧИКОВ ===

    function initEventHandlers() {
        const unitModal = document.getElementById('unitSelectModal');
        const quickModal = document.getElementById('quickUnitModal');
        const closeBtn = unitModal.querySelector('.close');
        const cancelBtn = document.getElementById('cancelSelection');
        const quickCloseBtn = quickModal.querySelector('.quick-close');
        const cancelQuickBtn = document.getElementById('cancelQuickSelection');
        const showFullSelectionBtn = document.getElementById('showFullSelection');
        
        // Обработчики основного модального окна
        document.querySelectorAll('.unit-item').forEach(item => {
            item.addEventListener('click', function() {
                const unitType = this.dataset.type;
                const unitId = this.dataset.id;
                const unitName = this.textContent.trim();
                
                updateScheduleAssignment(currentScheduleId, unitType, unitId, unitName);
                closeUnitModal();
            });
        });
        
        closeBtn.addEventListener('click', closeUnitModal);
        cancelBtn.addEventListener('click', closeUnitModal);
        window.addEventListener('click', function(event) {
            if (event.target === unitModal) {
                closeUnitModal();
            }
        });
        
        // Обработчики быстрого модального окна
        quickCloseBtn.addEventListener('click', closeQuickModal);
        cancelQuickBtn.addEventListener('click', closeQuickModal);
        window.addEventListener('click', function(event) {
            if (event.target === quickModal) {
                closeQuickModal();
            }
        });
        
        showFullSelectionBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const scheduleId = document.getElementById('quickScheduleId').value;
            closeQuickModal();
            openUnitModal(scheduleId);
        });
        
        // Обработчики таблицы
        document.querySelectorAll('.plan-schedules-table tbody tr').forEach(row => {
            row.addEventListener('click', function(event) {
                if (!event.target.closest('.btn-change')) {
                    const scheduleId = this.dataset.scheduleId;
                    openUnitModal(scheduleId);
                }
            });
        });
    }

    // Сделаем функции глобальными для onclick атрибутов
    window.openUnitModal = openUnitModal;
    window.openQuickUnitModal = openQuickUnitModal;

    // Запуск инициализации
    initEventHandlers();
}
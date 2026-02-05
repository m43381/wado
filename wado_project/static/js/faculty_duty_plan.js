// faculty_duty_plan.js - адаптация для факультета

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎓 Инициализация системы планирования факультетских нарядов...');

    // === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ФАКУЛЬТЕТА ===
    const GENERATE_FACULTY_PLAN_URL = "{% url 'faculty:generate_duty_plan' %}";
    const UPDATE_SCHEDULE_URL = "{% url 'faculty:update_schedule' 0 %}".replace('/0/', '/');
    const SAVE_SCHEDULE_SETTINGS_URL = "{% url 'faculty:duty_plan' %}";
    let currentScheduleId = null;

    // === ОСНОВНЫЕ ФУНКЦИИ ===

    // Функция для добавления диапазона дат
    window.addDateRange = function(dutyId) {
        const container = document.querySelector(`[data-duty-id="${dutyId}"] .plan-range-container`);
        if (container) {
            const startInput = container.querySelector('.plan-range-start');
            const endInput = container.querySelector('.plan-range-end');
            addDateRangeFromInputs(dutyId, startInput, endInput);
        }
    };

    function addDateRangeFromInputs(dutyId, startInput, endInput) {
        const startValue = startInput.value.trim();
        const endValue = endInput.value.trim();
        
        if (!startValue || !endValue) {
            showNotification('Заполните обе даты диапазона', 'warning');
            return;
        }
        
        const rangeValue = `${startValue} по ${endValue}`;
        addScheduleOption(dutyId, 'range', rangeValue);
        
        startInput.value = '';
        endInput.value = '';
        if (startInput._flatpickr) startInput._flatpickr.clear();
        if (endInput._flatpickr) endInput._flatpickr.clear();
    }

    // Функция для добавления опции в расписание
    function addScheduleOption(dutyId, type, value) {
        const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
        const hiddenFieldsContainer = document.querySelector(`.plan-hidden-fields[data-duty-id="${dutyId}"]`);
        
        if (!tagsContainer || !hiddenFieldsContainer) return;
        
        // Удаляем тег по умолчанию если он есть
        removeDefaultTag(dutyId);
        
        // Проверяем дубликаты
        const existingTags = tagsContainer.querySelectorAll('.plan-option-tag');
        for (let tag of existingTags) {
            const removeButton = tag.querySelector('.plan-remove-tag');
            if (removeButton && removeButton.dataset.value === value && removeButton.dataset.type === type) {
                showNotification('Этот параметр уже добавлен', 'warning', 2000);
                return;
            }
        }
        
        // Создаем визуальный тег
        const tag = document.createElement('span');
        tag.className = `plan-option-tag plan-${type}-tag`;
        
        tag.innerHTML = `
            <i class="fas fa-${getIconForType(type)}"></i>
            ${value}
            <button type="button" class="plan-remove-tag" data-type="${type}" data-value="${value}">&times;</button>
        `;
        
        tagsContainer.appendChild(tag);
        
        // Создаем скрытое поле для формы
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        
        if (type === 'date') {
            hiddenField.name = 'specific_dates[]';
        } else {
            hiddenField.name = `${type}s[]`;
        }
        
        hiddenField.value = value;
        hiddenFieldsContainer.appendChild(hiddenField);
        
        // Добавляем обработчик удаления
        const removeButton = tag.querySelector('.plan-remove-tag');
        removeButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            removeScheduleOption(dutyId, type, value, tag, hiddenField);
        });
        
        // Сохраняем настройки
        saveScheduleSettings(dutyId);
        updateGenerateButton();
        
        showNotification('Параметр добавлен', 'success', 2000);
    }

    function getIconForType(type) {
        const icons = {
            'range': 'calendar-day',
            'date': 'calendar-check',
            'weekday': 'calendar-week'
        };
        return icons[type] || 'calendar-alt';
    }

    function removeScheduleOption(dutyId, type, value, tagElement, hiddenField) {
        if (tagElement) tagElement.remove();
        if (hiddenField) hiddenField.remove();
        
        const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
        const remainingTags = tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)');
        
        if (remainingTags.length === 0) {
            showDefaultTag(dutyId);
        }
        
        saveScheduleSettings(dutyId);
        updateGenerateButton();
        showNotification('Параметр удален', 'info', 2000);
    }

    function removeDefaultTag(dutyId) {
        const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
        if (!tagsContainer) return;
        
        const defaultTag = tagsContainer.querySelector('.plan-default-tag');
        if (defaultTag) {
            defaultTag.remove();
        }
    }

    function showDefaultTag(dutyId) {
        const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
        tagsContainer.innerHTML = `
            <span class="plan-option-tag plan-default-tag">
                <i class="fas fa-calendar-alt"></i>
                Весь месяц
                <span class="plan-tag-hint">(по умолчанию)</span>
            </span>
        `;
    }

    function clearAllScheduleSettings(dutyId) {
        const container = document.querySelector(`.plan-schedule-container[data-duty-id="${dutyId}"]`);
        if (!container) return;

        // Очищаем диапазоны дат
        const rangeContainer = container.querySelector('.plan-range-container');
        if (rangeContainer) {
            const startInput = rangeContainer.querySelector('.plan-range-start');
            const endInput = rangeContainer.querySelector('.plan-range-end');
            
            if (startInput) {
                startInput.value = '';
                if (startInput._flatpickr) startInput._flatpickr.clear();
            }
            
            if (endInput) {
                endInput.value = '';
                if (endInput._flatpickr) endInput._flatpickr.clear();
            }
        }

        // Очищаем конкретные даты
        const datesInput = container.querySelector('input[data-dates-selector]');
        if (datesInput) {
            datesInput.value = '';
            if (datesInput._flatpickr) datesInput._flatpickr.clear();
        }

        // Снимаем выделение с чекбоксов дней недели
        container.querySelectorAll('.weekday-checkbox').forEach(ch => {
            ch.checked = false;
        });

        // Очищаем скрытые поля
        const hiddenFields = container.querySelector('.plan-hidden-fields');
        if (hiddenFields) {
            hiddenFields.innerHTML = '';
        }

        // Показываем тег по умолчанию
        showDefaultTag(dutyId);
        
        // Сохраняем изменения
        saveScheduleSettings(dutyId);
    }

    // === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    function parseDate(dateStr) {
        const match = dateStr.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
        if (match) {
            const day = parseInt(match[1]);
            const month = parseInt(match[2]);
            const year = parseInt(match[3]);
            return new Date(year, month - 1, day);
        }
        return null;
    }

    function formatDate(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
    }

    // === ИНИЦИАЛИЗАЦИЯ FLATPICKR ===
    function initFlatpickr() {
        console.log('📅 Инициализация Flatpickr для факультета...');
        
        // Диапазоны дат
        document.querySelectorAll('.plan-schedule-container').forEach(container => {
            const dutyId = container.dataset.dutyId;
            const startInput = container.querySelector('.plan-range-start');
            const endInput = container.querySelector('.plan-range-end');
            
            if (startInput && endInput) {
                flatpickr(startInput, {
                    locale: "ru",
                    dateFormat: "d.m.Y",
                    allowInput: true
                });
                
                flatpickr(endInput, {
                    locale: "ru",
                    dateFormat: "d.m.Y",
                    allowInput: true
                });
                
                const addButton = container.querySelector('.plan-add-range');
                if (addButton) {
                    addButton.addEventListener('click', function() {
                        addDateRangeFromInputs(dutyId, startInput, endInput);
                    });
                }
            }
        });

        // Конкретные даты
        document.querySelectorAll('.plan-schedule-container').forEach(container => {
            const dutyId = container.dataset.dutyId;
            const datesInput = container.querySelector('input[data-dates-selector]');
            
            if (datesInput) {
                flatpickr(datesInput, {
                    mode: "multiple",
                    locale: "ru",
                    dateFormat: "d.m.Y",
                    allowInput: true
                });
            }
        });
    }

    // === УПРАВЛЕНИЕ РАСКРЫТИЕМ/СКРЫТИЕМ НАСТРОЕК ===
    function initScheduleToggles() {
        document.querySelectorAll('.plan-expand-indicator').forEach(indicator => {
            indicator.addEventListener('click', function(e) {
                e.stopPropagation();
                const dutyCard = this.closest('.plan-duty-card');
                const settingsPanel = dutyCard.querySelector('.plan-schedule-settings');
                const icon = this.querySelector('i');
                
                if (settingsPanel.style.display === 'none' || !settingsPanel.style.display) {
                    settingsPanel.style.display = 'block';
                    icon.className = 'fas fa-chevron-up';
                } else {
                    settingsPanel.style.display = 'none';
                    icon.className = 'fas fa-chevron-down';
                }
            });
        });
        
        // Клик по заголовку
        document.querySelectorAll('.plan-duty-header').forEach(header => {
            header.addEventListener('click', function(e) {
                if (e.target.type === 'checkbox') return;
                
                const dutyCard = this.closest('.plan-duty-card');
                const settings = dutyCard.querySelector('.plan-schedule-settings');
                const indicator = this.querySelector('.plan-expand-indicator i');
                
                if (!settings || !indicator) return;
                
                if (settings.style.display === 'none' || !settings.style.display) {
                    settings.style.display = 'block';
                    indicator.className = 'fas fa-chevron-up';
                    dutyCard.classList.add('expanded');
                } else {
                    settings.style.display = 'none';
                    indicator.className = 'fas fa-chevron-down';
                    dutyCard.classList.remove('expanded');
                }
            });
        });
    }

    // === РАБОТА С ТЕГАМИ РАСПИСАНИЯ ===
    function initScheduleTags() {
        // Добавление конкретных дат
        document.querySelectorAll('.plan-add-dates').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const input = document.querySelector(`input[data-dates-selector][data-duty-id="${dutyId}"]`);
                
                if (!input || !input.value.trim()) {
                    showNotification('Выберите конкретные даты', 'warning');
                    return;
                }
                
                const flatpickrInstance = input._flatpickr;
                if (!flatpickrInstance || !flatpickrInstance.selectedDates.length) {
                    showNotification('Выберите конкретные даты', 'warning');
                    return;
                }
                
                let addedCount = 0;
                
                flatpickrInstance.selectedDates.forEach(date => {
                    const formattedDate = formatDate(date);
                    addScheduleOption(dutyId, 'date', formattedDate);
                    addedCount++;
                });
                
                input.value = '';
                if (flatpickrInstance) {
                    flatpickrInstance.clear();
                }
                
                showNotification(`Добавлено ${addedCount} конкретных дат`, 'success', 2000);
            });
        });

        // Добавление дней недели
        document.querySelectorAll('.plan-add-weekdays').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const checkboxes = document.querySelectorAll(`.weekday-checkbox[data-duty-id="${dutyId}"]:checked`);
                
                if (checkboxes.length === 0) {
                    showNotification('Выберите хотя бы один день недели', 'warning');
                    return;
                }

                checkboxes.forEach(ch => {
                    addScheduleOption(dutyId, 'weekday', ch.value);
                    ch.checked = false;
                });
            });
        });

        // Очистка всех настроек
        document.querySelectorAll('.plan-clear-all').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                if (confirm('Очистить ВСЕ параметры расписания для этого наряда?')) {
                    clearAllScheduleSettings(dutyId);
                }
            });
        });
    }

    // === СОХРАНЕНИЕ НАСТРОЕК РАСПИСАНИЯ ===
    function saveScheduleSettings(dutyId) {
        const container = document.querySelector(`.plan-schedule-container[data-duty-id="${dutyId}"]`);
        if (!container) return;

        const formData = new FormData();
        formData.append('duty_id', dutyId);
        formData.append('year', CURRENT_YEAR);
        formData.append('month', CURRENT_MONTH);
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // Собираем данные из скрытых полей
        const hiddenFieldsContainer = document.querySelector(`.plan-hidden-fields[data-duty-id="${dutyId}"]`);
        if (hiddenFieldsContainer) {
            hiddenFieldsContainer.querySelectorAll('input').forEach(input => {
                if (input.name === 'ranges[]' && input.value) {
                    formData.append('ranges[]', input.value);
                } else if (input.name === 'specific_dates[]' && input.value) {
                    formData.append('specific_dates[]', input.value);
                } else if (input.name === 'weekdays[]' && input.value) {
                    formData.append('weekdays[]', input.value);
                }
            });
        }

        // Отправляем на сервер
        fetch(SAVE_SCHEDULE_SETTINGS_URL + `?year=${CURRENT_YEAR}&month=${CURRENT_MONTH}`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data && data.success) {
                console.log('✅ Настройки успешно сохранены на сервере');
            } else {
                console.error('❌ Ошибка сохранения настроек:', data);
            }
        })
        .catch(error => {
            console.error('❌ Ошибка при сохранении настроек:', error);
        });
    }

    // === УПРАВЛЕНИЕ ПОДРАЗДЕЛЕНИЯМИ (ФАКУЛЬТЕТ) ===
    function initUnitSelection() {
        const selectAllBtn = document.getElementById('select-all-units');
        const deselectAllBtn = document.getElementById('deselect-all-units');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                document.querySelectorAll('.unit-checkbox-input').forEach(ch => {
                    ch.checked = true;
                    updateUnitCheckboxState(ch);
                });
                updateUnitSelection();
            });
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => {
                document.querySelectorAll('.unit-checkbox-input').forEach(ch => {
                    ch.checked = false;
                    updateUnitCheckboxState(ch);
                });
                updateUnitSelection();
            });
        }

        // Обработка изменений чекбоксов
        document.querySelectorAll('.unit-checkbox-input').forEach(ch => {
            if (ch) {
                ch.addEventListener('change', () => {
                    updateUnitCheckboxState(ch);
                    updateUnitSelection();
                });
                updateUnitCheckboxState(ch);
            }
        });

        updateUnitSelection();
    }

    function updateUnitCheckboxState(checkbox) {
        const label = checkbox.closest('.unit-checkbox');
        if (checkbox.checked) {
            label.classList.add('checked');
        } else {
            label.classList.remove('checked');
        }
    }

    function updateUnitSelection() {
        const selectedCount = document.querySelectorAll('.unit-checkbox-input:checked').length;
        const countElement = document.getElementById('selected-units-count');
        
        if (countElement) {
            countElement.textContent = selectedCount;
            
            // Динамическое изменение цвета
            if (selectedCount === 0) {
                countElement.style.color = '#f44747';
            } else if (selectedCount < 3) {
                countElement.style.color = '#d7ba7d';
            } else {
                countElement.style.color = '#4ec9b0';
            }
        }

        // Сохраняем в скрытое поле
        updateSelectedUnitsField();
        
        // Валидируем кнопку
        validateGenerateButton();
    }

    function updateSelectedUnitsField() {
        const selectedUnits = Array.from(document.querySelectorAll('.unit-checkbox-input:checked'))
            .map(checkbox => checkbox.value);
        
        const hiddenField = document.getElementById('plan-selected-units');
        if (hiddenField) {
            hiddenField.value = selectedUnits.join(',');
        }
    }

    // === УПРАВЛЕНИЕ НАРЯДАМИ (ФАКУЛЬТЕТ) ===
    function initDutySelection() {
        document.querySelectorAll('.plan-duty-check').forEach(checkbox => {
            if (!checkbox) return;
            
            checkbox.addEventListener('change', function() {
                const card = this.closest('.plan-duty-card');
                if (card) {
                    if (this.checked) {
                        card.classList.add('selected');
                    } else {
                        card.classList.remove('selected');
                    }
                }
                updateDutySelection();
            });
            
            if (checkbox.checked) {
                const card = checkbox.closest('.plan-duty-card');
                if (card) {
                    card.classList.add('selected');
                }
            }
        });

        updateDutySelection();
    }

    function updateDutySelection() {
        const selectedDuties = Array.from(document.querySelectorAll('.plan-duty-check:checked'))
            .map(checkbox => checkbox.value);
        
        const hiddenField = document.getElementById('plan-selected-duties');
        if (hiddenField) {
            hiddenField.value = selectedDuties.join(',');
        }
        
        validateGenerateButton();
    }

    // === ВАЛИДАЦИЯ КНОПКИ ГЕНЕРАЦИИ (ФАКУЛЬТЕТ) ===
    function validateGenerateButton() {
        const selectedUnits = document.querySelectorAll('.unit-checkbox-input:checked').length;
        const selectedDuties = document.querySelectorAll('.plan-duty-check:checked').length;
        
        const isValid = selectedUnits > 0 && selectedDuties > 0;
        const generateBtn = document.getElementById('plan-generate-btn');
        
        if (generateBtn) {
            generateBtn.disabled = !isValid;
            
            if (isValid) {
                generateBtn.classList.add('ready');
                generateBtn.title = 'Готово к генерации графика факультетских нарядов';
            } else {
                generateBtn.classList.remove('ready');
                generateBtn.title = 'Выберите подразделения и наряды для генерации';
            }
        }
        
        // Обновляем валидационные сообщения
        updateValidationMessages(selectedUnits, selectedDuties);
        
        return isValid;
    }

    function updateValidationMessages(unitsCount, dutiesCount) {
        const unitsValidation = document.getElementById('plan-validation-units');
        const dutiesValidation = document.getElementById('plan-validation-duties');
        
        if (unitsValidation) {
            if (unitsCount > 0) {
                unitsValidation.innerHTML = '<i class="fas fa-check-circle"></i><span>Подразделения выбраны (' + unitsCount + ')</span>';
                unitsValidation.classList.add('valid');
            } else {
                unitsValidation.innerHTML = '<i class="fas fa-times-circle"></i><span>Выберите подразделения для распределения</span>';
                unitsValidation.classList.remove('valid');
            }
        }
        
        if (dutiesValidation) {
            if (dutiesCount > 0) {
                dutiesValidation.innerHTML = '<i class="fas fa-check-circle"></i><span>Наряды выбраны (' + dutiesCount + ')</span>';
                dutiesValidation.classList.add('valid');
            } else {
                dutiesValidation.innerHTML = '<i class="fas fa-times-circle"></i><span>Выберите наряды для планирования</span>';
                dutiesValidation.classList.remove('valid');
            }
        }
    }

    // === УВЕДОМЛЕНИЯ ===
    function showNotification(message, type = 'info', duration = 5000) {
        let container = document.getElementById('notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            background: ${getNotificationColor(type)};
            color: white;
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideInRight 0.3s ease-out;
        `;
        
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        notification.innerHTML = `
            <i class="fas fa-${icons[type] || 'info-circle'}"></i>
            <span>${message}</span>
            <button class="notification-close" style="margin-left: auto; background: none; border: none; color: inherit; cursor: pointer;">
                &times;
            </button>
        `;
        
        container.appendChild(notification);
        
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }
        
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOutRight {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    function getNotificationColor(type) {
        const colors = {
            success: '#4ec9b0',
            error: '#f44747',
            warning: '#d7ba7d',
            info: '#569cd6'
        };
        return colors[type] || '#569cd6';
    }

    // === ГЕНЕРАЦИЯ ГРАФИКА (ФАКУЛЬТЕТ) ===
    function initGeneratePlan() {
        const generateBtn = document.getElementById('plan-generate-btn');
        if (!generateBtn) return;

        generateBtn.addEventListener('click', function() {
            const selectedDuties = Array.from(document.querySelectorAll('.plan-duty-check:checked'))
                .map(checkbox => checkbox.value);
            const selectedUnits = Array.from(document.querySelectorAll('.unit-checkbox-input:checked'))
                .map(checkbox => checkbox.value);

            if (selectedDuties.length === 0) {
                showNotification('Выберите факультетские наряды для генерации', 'warning');
                return;
            }

            if (selectedUnits.length === 0) {
                showNotification('Выберите подразделения для распределения', 'warning');
                return;
            }

            if (!confirm(`Сгенерировать график факультетских нарядов?\n\nВыбрано:\n- ${selectedDuties.length} нарядов\n- ${selectedUnits.length} подразделений`)) {
                return;
            }

            generateFacultyPlan(selectedDuties, selectedUnits);
        });
    }

    function generateFacultyPlan(dutyIds, unitValues) {
        console.log('🚀 Генерация факультетского плана');
        
        const formData = new FormData();
        formData.append('year', CURRENT_YEAR);
        formData.append('month', CURRENT_MONTH);
        formData.append('duties', dutyIds.join(','));
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        unitValues.forEach(unit => {
            formData.append('selected_units', unit);
        });
        
        const generateBtn = document.getElementById('plan-generate-btn');
        const originalText = generateBtn.innerHTML;
        
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерация...';
        
        fetch(GENERATE_FACULTY_PLAN_URL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`График успешно сгенерирован! Создано ${data.count} записей.`, 'success', 3000);
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                showNotification(`Ошибка: ${data.error}`, 'error');
                generateBtn.innerHTML = originalText;
                generateBtn.disabled = false;
            }
        })
        .catch(error => {
            showNotification('Ошибка при генерации графика', 'error');
            console.error('Error:', error);
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        });
    }

    // === ФУНКЦИОНАЛ РЕДАКТИРОВАНИЯ ЗАПИСЕЙ (ФАКУЛЬТЕТ) ===

    window.openUnitModal = function(scheduleId) {
        currentScheduleId = scheduleId;
        document.getElementById('currentScheduleId').value = scheduleId;
        document.getElementById('unitSelectModal').style.display = 'block';
    }

    function closeUnitModal() {
        document.getElementById('unitSelectModal').style.display = 'none';
        currentScheduleId = null;
    }

    window.openQuickUnitModal = function(scheduleId, dutyName) {
        currentScheduleId = scheduleId;
        document.getElementById('quickScheduleId').value = scheduleId;
        document.getElementById('quickDutyName').textContent = dutyName;
        
        populateQuickUnits();
        document.getElementById('quickUnitModal').style.display = 'block';
    }

    function populateQuickUnits() {
        const quickUnitsGrid = document.getElementById('quickUnitsGrid');
        quickUnitsGrid.innerHTML = '';
        
        // Управление факультета
        const managementItem = document.createElement('div');
        managementItem.className = 'quick-unit-item';
        managementItem.textContent = 'Управление факультета';
        managementItem.onclick = () => {
            updateScheduleAssignment(
                currentScheduleId, 
                'management', 
                'management', 
                'Управление факультета'
            );
            closeQuickModal();
        };
        quickUnitsGrid.appendChild(managementItem);
        
        // Кафедры
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

    function updateScheduleAssignment(scheduleId, unitType, unitId, unitName) {
        const formData = new FormData();
        formData.append('unit_type', unitType);
        formData.append('unit_id', unitId);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        const url = UPDATE_SCHEDULE_URL + scheduleId + '/update/';
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Ошибка при обновлении: ' + data.error);
            }
        })
        .catch(error => {
            alert('Ошибка: ' + error.message);
        });
    }

    function initEditingEventHandlers() {
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
    }

    // Обновление кнопки генерации
    function updateGenerateButton() {
        const hasScheduleSettings = checkIfAnyDutyHasScheduleSettings();
        
        const generateBtn = document.getElementById('plan-generate-btn');
        if (!generateBtn) return;
        
        if (hasScheduleSettings) {
            generateBtn.disabled = false;
            generateBtn.classList.add('ready');
            generateBtn.title = 'Готово к генерации графика факультетских нарядов';
        } else {
            validateGenerateButton();
        }
    }

    function checkIfAnyDutyHasScheduleSettings() {
        let hasSettings = false;
        
        document.querySelectorAll('.plan-duty-check:checked').forEach(checkbox => {
            const dutyId = checkbox.value;
            const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
            
            if (tagsContainer) {
                const customTags = tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)');
                if (customTags.length > 0) {
                    hasSettings = true;
                }
            }
        });
        
        return hasSettings;
    }

    function loadInitialScheduleSettings() {
        console.log('📥 Загрузка начальных настроек факультетского расписания...');
        
        document.querySelectorAll('.plan-duty-card').forEach(card => {
            const dutyId = card.dataset.dutyId;
            const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
            
            if (tagsContainer) {
                const existingTags = tagsContainer.querySelectorAll('.plan-option-tag');
                if (existingTags.length > 0) {
                    const hiddenFieldsContainer = document.querySelector(`.plan-hidden-fields[data-duty-id="${dutyId}"]`);
                    if (hiddenFieldsContainer) {
                        hiddenFieldsContainer.innerHTML = '';
                        
                        existingTags.forEach(tag => {
                            const removeButton = tag.querySelector('.plan-remove-tag');
                            if (removeButton && removeButton.dataset.type && removeButton.dataset.value) {
                                const type = removeButton.dataset.type;
                                let value = removeButton.dataset.value;
                                
                                if (tag.classList.contains('plan-default-tag')) {
                                    return;
                                }
                                
                                // Восстанавливаем скрытое поле
                                const hiddenField = document.createElement('input');
                                hiddenField.type = 'hidden';
                                
                                if (type === 'date') {
                                    hiddenField.name = 'specific_dates[]';
                                } else {
                                    hiddenField.name = `${type}s[]`;
                                }
                                
                                hiddenField.value = value;
                                hiddenFieldsContainer.appendChild(hiddenField);
                                
                                // Добавляем обработчик удаления
                                removeButton.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    removeScheduleOption(dutyId, type, value, tag, hiddenField);
                                });
                            }
                        });
                    }
                }
            }
        });
    }

    // === ОСНОВНАЯ ИНИЦИАЛИЗАЦИЯ ===
    function init() {
        console.log('🚀 Запуск инициализации факультетской системы...');
        
        try {
            initFlatpickr();
            initScheduleToggles(); 
            initScheduleTags();
            initUnitSelection();
            initDutySelection();
            validateGenerateButton();
            initGeneratePlan();
            initEditingEventHandlers();
            
            setTimeout(() => {
                loadInitialScheduleSettings();
            }, 100);
            
            console.log('✅ Факультетская система инициализирована');
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            showNotification('Ошибка инициализации системы', 'error');
        }
    }

    // Запуск
    init();
});
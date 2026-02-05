// faculty_duty_plan_full.js - ИСПРАВЛЕННЫЙ ВАРИАНТ
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎓 Инициализация системы планирования факультетских нарядов...');
    
    // === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
    let currentScheduleId = null;
    let csrfToken = window.CSRF_TOKEN;
    
    // === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
    
    function getCSRFToken() {
        if (!csrfToken) {
            const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
            csrfToken = csrfInput ? csrfInput.value : '';
        }
        return csrfToken;
    }

    function showNotification(message, type = 'info', duration = 3000) {
        const oldContainer = document.getElementById('notifications-container');
        if (oldContainer) oldContainer.remove();
        
        const container = document.createElement('div');
        container.id = 'notifications-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            max-width: 400px;
        `;
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            background: ${type === 'success' ? '#4ec9b0' : 
                        type === 'error' ? '#f44747' : 
                        type === 'warning' ? '#d7ba7d' : '#569cd6'};
            color: white;
            padding: 15px 20px;
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
            <button class="notification-close" style="margin-left: auto; background: none; border: none; color: inherit; cursor: pointer; font-size: 18px;">
                &times;
            </button>
        `;
        
        container.appendChild(notification);
        document.body.appendChild(container);
        
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => container.remove(), 300);
        });
        
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => {
                        if (container.parentNode) container.remove();
                    }, 300);
                }
            }, duration);
        }
    }

    // === ВАЛИДАЦИЯ И ОБНОВЛЕНИЕ КНОПКИ ГЕНЕРАЦИИ ===
    function validateGenerateButton() {
        const selectedUnits = document.querySelectorAll('.unit-checkbox-input:checked').length;
        const selectedDuties = document.querySelectorAll('.plan-duty-check:checked').length;
        
        const isValid = selectedUnits > 0 && selectedDuties > 0;
        const generateBtn = document.getElementById('plan-generate-btn');
        
        if (generateBtn) {
            generateBtn.disabled = !isValid;
            generateBtn.classList.toggle('ready', isValid);
        }
        
        return isValid;
    }

    // === УПРАВЛЕНИЕ РАСКРЫТИЕМ НАСТРОЕК ===
    function initScheduleToggles() {
        console.log('🔄 Инициализация переключателей настроек...');
        
        document.querySelectorAll('.plan-duty-header').forEach(header => {
            header.addEventListener('click', function(e) {
                if (e.target.type === 'checkbox' || 
                    e.target.closest('input[type="checkbox"]') || 
                    e.target.tagName === 'BUTTON') {
                    return;
                }
                
                const dutyCard = this.closest('.plan-duty-card');
                if (!dutyCard) return;
                
                const settings = dutyCard.querySelector('.plan-schedule-settings');
                const indicator = this.querySelector('.plan-expand-indicator i');
                
                if (!settings || !indicator) return;
                
                const isHidden = settings.style.display === 'none' || !settings.style.display;
                settings.style.display = isHidden ? 'block' : 'none';
                indicator.className = isHidden ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
                dutyCard.classList.toggle('expanded', isHidden);
            });
        });
        
        console.log('✅ Переключатели настроек инициализированы');
    }

    // === ИНИЦИАЛИЗАЦИЯ FLATPICKR ===
    function initFlatpickr() {
        console.log('📅 Инициализация Flatpickr...');
        
        if (!window.flatpickr) {
            console.error('❌ Flatpickr не загружен');
            return;
        }
        
        flatpickr.localize(flatpickr.l10ns.ru);
        
        const currentYear = window.CURRENT_YEAR || new Date().getFullYear();
        const currentMonth = window.CURRENT_MONTH || new Date().getMonth() + 1;
        const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
        
        const commonOptions = {
            locale: "ru",
            dateFormat: "d.m.Y",
            minDate: new Date(currentYear, currentMonth - 1, 1),
            maxDate: new Date(currentYear, currentMonth - 1, daysInMonth),
            allowInput: true
        };
        
        document.querySelectorAll('.plan-range-start, .plan-range-end').forEach(input => {
            flatpickr(input, commonOptions);
        });
        
        document.querySelectorAll('.plan-dates-input').forEach(datesInput => {
            flatpickr(datesInput, {
                ...commonOptions,
                mode: "multiple"
            });
        });
        
        console.log('✅ Flatpickr инициализирован');
    }

    // === РАБОТА С ТЕГАМИ РАСПИСАНИЯ ===
    function initScheduleTags() {
        console.log('🏷️ Инициализация работы с тегами...');
        
        // Добавление диапазонов дат
        document.querySelectorAll('.plan-add-range').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const container = this.closest('.plan-range-container');
                
                if (!container) {
                    showNotification('Контейнер диапазона не найден', 'error');
                    return;
                }
                
                const startInput = container.querySelector('.plan-range-start');
                const endInput = container.querySelector('.plan-range-end');
                
                if (!startInput || !endInput) {
                    showNotification('Не найдены поля ввода дат', 'error');
                    return;
                }
                
                const startValue = startInput.value.trim();
                const endValue = endInput.value.trim();
                
                if (!startValue || !endValue) {
                    showNotification('Заполните обе даты диапазона', 'warning');
                    return;
                }
                
                const dateRegex = /^\d{2}\.\d{2}\.\d{4}$/;
                if (!dateRegex.test(startValue) || !dateRegex.test(endValue)) {
                    showNotification('Некорректный формат даты. Используйте ДД.ММ.ГГГГ', 'warning');
                    return;
                }
                
                const rangeValue = `${startValue} по ${endValue}`;
                addScheduleOption(dutyId, 'range', rangeValue);
                
                startInput.value = '';
                endInput.value = '';
                if (startInput._flatpickr) startInput._flatpickr.clear();
                if (endInput._flatpickr) endInput._flatpickr.clear();
            });
        });

        // Добавление конкретных дат
        document.querySelectorAll('.plan-add-dates').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const input = document.querySelector(`.plan-dates-input[data-duty-id="${dutyId}"]`);
                
                if (!input) {
                    showNotification('Поле ввода дат не найдено', 'error');
                    return;
                }

                const flatpickrInstance = input._flatpickr;
                if (!flatpickrInstance || !flatpickrInstance.selectedDates.length) {
                    showNotification('Выберите конкретные даты', 'warning');
                    return;
                }
                
                let addedCount = 0;
                let hasDuplicates = false;
                
                flatpickrInstance.selectedDates.forEach(date => {
                    const formattedDate = formatDate(date);
                    if (addScheduleOption(dutyId, 'date', formattedDate, true)) {
                        addedCount++;
                    } else {
                        hasDuplicates = true;
                    }
                });
                
                input.value = '';
                if (flatpickrInstance) {
                    flatpickrInstance.clear();
                }
                
                let message = `Добавлено ${addedCount} конкретных дат`;
                if (hasDuplicates) {
                    message += ' (некоторые даты уже были добавлены)';
                }
                showNotification(message, 'success', 2000);
            });
        });

        // === ИСПРАВЛЕННЫЙ КОД ДЛЯ ДНЕЙ НЕДЕЛИ ===
        document.querySelectorAll('.plan-add-weekdays').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
                if (!dutyCard) {
                    showNotification('Карточка наряда не найдена', 'error');
                    return;
                }
                
                // ПРОБУЕМ РАЗНЫЕ СЕЛЕКТОРЫ ДЛЯ ПОИСКА ЧЕКБОКСОВ ДНЕЙ НЕДЕЛИ
                
                // Сначала ищем по классу weekday-checkbox (самый вероятный)
                let checkboxes = dutyCard.querySelectorAll('.weekday-checkbox');
                
                // Если не нашли, ищем по input с type="checkbox" внутри контейнера дней недели
                if (checkboxes.length === 0) {
                    console.log('Не найдены чекбоксы по .weekday-checkbox, ищем другие варианты...');
                    
                    // Ищем все чекбоксы в контейнере дней недели
                    const weekdaySection = dutyCard.querySelector('.weekday-section, .weekday-options, [data-weekday-section]');
                    if (weekdaySection) {
                        checkboxes = weekdaySection.querySelectorAll('input[type="checkbox"]');
                    } else {
                        // Ищем любые чекбоксы в карточке, которые могут быть днями недели
                        checkboxes = dutyCard.querySelectorAll('input[type="checkbox"]');
                        // Фильтруем только те, у которых value соответствует дням недели
                        checkboxes = Array.from(checkboxes).filter(checkbox => {
                            const val = checkbox.value.toLowerCase();
                            const weekdayValues = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье',
                                                  '0', '1', '2', '3', '4', '5', '6', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];
                            return weekdayValues.includes(val);
                        });
                    }
                }
                
                if (checkboxes.length === 0) {
                    console.log('Не найдено ни одного чекбокса дня недели. Все чекбоксы на странице:');
                    dutyCard.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                        console.log(`  Чекбокс: value="${cb.value}", class="${cb.className}", name="${cb.name}"`);
                    });
                    showNotification('Не найдены варианты дней недели. Проверьте структуру HTML.', 'error');
                    return;
                }
                
                console.log(`📅 Найдено ${checkboxes.length} чекбоксов дней недели для наряда ${dutyId}`);
                
                // Собираем выбранные дни недели
                const selectedDays = [];
                
                checkboxes.forEach(checkbox => {
                    if (checkbox.checked && checkbox.value) {
                        // Получаем текст метки
                        let dayName = checkbox.value;
                        const label = checkbox.closest('label') || 
                                     checkbox.parentElement.querySelector('label') ||
                                     document.querySelector(`label[for="${checkbox.id}"]`);
                        
                        if (label) {
                            dayName = label.textContent.trim() || checkbox.value;
                        }
                        
                        selectedDays.push({
                            value: checkbox.value,
                            name: dayName
                        });
                        console.log(`✓ Выбран день: ${checkbox.value} (${dayName})`);
                    }
                });
                
                if (selectedDays.length === 0) {
                    showNotification('Выберите хотя бы один день недели', 'warning');
                    return;
                }

                console.log(`📅 Добавляем ${selectedDays.length} дней недели для наряда ${dutyId}:`, 
                    selectedDays.map(d => d.name));
                
                let addedCount = 0;
                let hasDuplicates = false;
                
                // Добавляем ВСЕ выбранные дни недели за один раз
                selectedDays.forEach(day => {
                    if (addScheduleOption(dutyId, 'weekday', day.value, true)) {
                        addedCount++;
                    } else {
                        hasDuplicates = true;
                    }
                });
                
                // После добавления снимаем флажки со ВСЕХ чекбоксов
                selectedDays.forEach(day => {
                    // Находим соответствующий чекбокс и снимаем флажок
                    checkboxes.forEach(checkbox => {
                        if (checkbox.value === day.value && checkbox.checked) {
                            checkbox.checked = false;
                        }
                    });
                });
                
                let message = `Добавлено ${addedCount} дней недели`;
                if (hasDuplicates) {
                    message += ' (некоторые дни уже были добавлены)';
                }
                
                if (addedCount > 0) {
                    showNotification(message, 'success', 2000);
                } else {
                    showNotification('Дни недели не добавлены (все уже существуют)', 'warning', 2000);
                }
            });
        });

        // Очистка всех настроек
        document.querySelectorAll('.plan-clear-all').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
                if (!dutyCard) return;
                
                const tagsCount = dutyCard.querySelectorAll('.plan-option-tag:not(.plan-default-tag)').length;
                if (tagsCount === 0) {
                    showNotification('Нет настроек для очистки', 'info');
                    return;
                }
                
                if (confirm(`Очистить ВСЕ параметры расписания для этого наряда?`)) {
                    clearAllOptions(dutyId);
                }
            });
        });
        
        // Инициализация существующих тегов удаления
        document.querySelectorAll('.plan-remove-tag').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const type = this.dataset.type;
                const value = this.dataset.value;
                const tag = this.closest('.plan-option-tag');
                const dutyCard = tag.closest('.plan-duty-card');
                
                if (!dutyCard) return;
                
                const dutyId = dutyCard.dataset.dutyId;
                tag.remove();
                
                updateHiddenFields(dutyId);
                
                const tagsContainer = dutyCard.querySelector('.plan-options-tags');
                const remainingTags = tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)');
                
                if (remainingTags.length === 0) {
                    showDefaultTag(dutyId);
                }
                
                saveScheduleSettings(dutyId);
                validateGenerateButton(); // ИСПРАВЛЕНО: было updateGenerateButton()
                
                showNotification('Параметр удален', 'success', 2000);
            });
        });
        
        console.log('✅ Теги расписания инициализированы');
    }

    // Функция для добавления опции в расписание
    function addScheduleOption(dutyId, type, value, checkDuplicates = false) {
        console.log(`➕ Добавление опции: duty=${dutyId}, type=${type}, value="${value}"`);
        
        const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
        if (!dutyCard) {
            console.error('❌ Карточка наряда не найдена');
            showNotification('Ошибка: карточка наряда не найдена', 'error');
            return false;
        }
        
        const tagsContainer = dutyCard.querySelector('.plan-options-tags');
        const hiddenFieldsContainer = dutyCard.querySelector('.plan-hidden-fields');
        
        if (!tagsContainer || !hiddenFieldsContainer) {
            console.error('❌ Контейнеры не найдены');
            showNotification('Ошибка: контейнеры настроек не найдены', 'error');
            return false;
        }
        
        removeDefaultTag(dutyId);
        
        let normalizedValue = value;
        let displayValue = value;
        
        if (type === 'weekday') {
            const weekdayMap = {
                '0': 'Понедельник',
                '1': 'Вторник', 
                '2': 'Среда',
                '3': 'Четверг',
                '4': 'Пятница',
                '5': 'Суббота',
                '6': 'Воскресенье'
            };
            
            // Если пришло название, а не число - преобразуем
            if (isNaN(value)) {
                const reverseMap = {
                    'понедельник': '0', 'пн': '0', 'понедельник': '0',
                    'вторник': '1', 'вт': '1', 'вторник': '1',
                    'среда': '2', 'ср': '2', 'среда': '2',
                    'четверг': '3', 'чт': '3', 'четверг': '3',
                    'пятница': '4', 'пт': '4', 'пятница': '4',
                    'суббота': '5', 'сб': '5', 'суббота': '5',
                    'воскресенье': '6', 'вс': '6', 'воскресенье': '6'
                };
                const key = value.toLowerCase();
                normalizedValue = reverseMap[key] || value;
            }
            
            displayValue = weekdayMap[normalizedValue] || value;
        }
        
        // Проверка дубликатов
        if (checkDuplicates) {
            const existingTags = tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)');
            for (let tag of existingTags) {
                const removeButton = tag.querySelector('.plan-remove-tag');
                if (removeButton && removeButton.dataset.value === normalizedValue) {
                    console.log(`⚠️ Дубликат: ${type} "${displayValue}" (нормализовано: ${normalizedValue}) уже существует`);
                    return false;
                }
            }
        }
        
        // Создаем визуальный тег
        const tag = document.createElement('span');
        tag.className = `plan-option-tag plan-${type}-tag`;
        
        const icon = getIconForType(type);
        tag.innerHTML = `
            <i class="fas fa-${icon}"></i>
            ${displayValue}
            <button type="button" class="plan-remove-tag" data-type="${type}" data-value="${normalizedValue}" title="Удалить">
                &times;
            </button>
        `;
        
        tagsContainer.appendChild(tag);
        
        // Добавляем обработчик удаления
        const removeButton = tag.querySelector('.plan-remove-tag');
        removeButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.closest('.plan-option-tag').remove();
            updateHiddenFields(dutyId);
            
            const remainingTags = tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)');
            if (remainingTags.length === 0) {
                showDefaultTag(dutyId);
            }
            
            saveScheduleSettings(dutyId);
            validateGenerateButton(); // ИСПРАВЛЕНО: было updateGenerateButton()
            showNotification('Параметр удален', 'success', 2000);
        });
        
        // Обновляем скрытые поля
        updateHiddenFields(dutyId);
        
        // Сохраняем настройки
        saveScheduleSettings(dutyId);
        validateGenerateButton(); // ИСПРАВЛЕНО: было updateGenerateButton()
        
        console.log(`✅ Опция ${type} "${displayValue}" добавлена (нормализовано: ${normalizedValue})`);
        return true;
    }

    function updateHiddenFields(dutyId) {
        const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
        if (!dutyCard) return;
        
        const tagsContainer = dutyCard.querySelector('.plan-options-tags');
        const hiddenFieldsContainer = dutyCard.querySelector('.plan-hidden-fields');
        
        if (!tagsContainer || !hiddenFieldsContainer) return;
        
        hiddenFieldsContainer.innerHTML = '';
        
        const ranges = [];
        const specificDates = [];
        const weekdays = [];
        
        tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)').forEach(tag => {
            if (tag.classList.contains('plan-range-tag')) {
                const removeBtn = tag.querySelector('.plan-remove-tag');
                if (removeBtn) {
                    ranges.push(removeBtn.dataset.value);
                }
            }
            else if (tag.classList.contains('plan-date-tag')) {
                const removeBtn = tag.querySelector('.plan-remove-tag');
                if (removeBtn) {
                    specificDates.push(removeBtn.dataset.value);
                }
            }
            else if (tag.classList.contains('plan-weekday-tag')) {
                const removeBtn = tag.querySelector('.plan-remove-tag');
                if (removeBtn) {
                    weekdays.push(removeBtn.dataset.value);
                }
            }
        });
        
        ranges.forEach(range => {
            const field = document.createElement('input');
            field.type = 'hidden';
            field.name = 'ranges[]';
            field.value = range;
            field.dataset.dutyId = dutyId;
            hiddenFieldsContainer.appendChild(field);
        });
        
        specificDates.forEach(date => {
            const field = document.createElement('input');
            field.type = 'hidden';
            field.name = 'specific_dates[]';
            field.value = date;
            field.dataset.dutyId = dutyId;
            hiddenFieldsContainer.appendChild(field);
        });
        
        weekdays.forEach(day => {
            const field = document.createElement('input');
            field.type = 'hidden';
            field.name = 'weekdays[]';
            field.value = day;
            field.dataset.dutyId = dutyId;
            hiddenFieldsContainer.appendChild(field);
        });
        
        console.log(`📝 Обновлены скрытые поля для duty_id=${dutyId}:`);
        console.log(`  ranges: ${ranges.length}, dates: ${specificDates.length}, weekdays: ${weekdays.length}`);
    }

    function getIconForType(type) {
        const icons = {
            'range': 'calendar-day',
            'date': 'calendar-check',
            'weekday': 'calendar-week'
        };
        return icons[type] || 'calendar-alt';
    }

    function removeDefaultTag(dutyId) {
        const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
        if (!dutyCard) return;
        
        const tagsContainer = dutyCard.querySelector('.plan-options-tags');
        if (!tagsContainer) return;
        
        const defaultTag = tagsContainer.querySelector('.plan-default-tag');
        if (defaultTag) {
            defaultTag.remove();
        }
    }

    function showDefaultTag(dutyId) {
        const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
        if (!dutyCard) return;
        
        const tagsContainer = dutyCard.querySelector('.plan-options-tags');
        if (!tagsContainer) return;
        
        tagsContainer.innerHTML = '';
        
        const defaultTag = document.createElement('span');
        defaultTag.className = 'plan-option-tag plan-default-tag';
        defaultTag.innerHTML = `
            <i class="fas fa-calendar-alt"></i>
            Весь месяц
            <span class="plan-tag-hint">(по умолчанию)</span>
        `;
        
        tagsContainer.appendChild(defaultTag);
        
        const hiddenFieldsContainer = dutyCard.querySelector('.plan-hidden-fields');
        if (hiddenFieldsContainer) {
            hiddenFieldsContainer.innerHTML = '';
        }
        
        saveScheduleSettings(dutyId);
    }

    function formatDate(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
    }

    function clearAllOptions(dutyId) {
        const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
        if (!dutyCard) return;
        
        const tagsContainer = dutyCard.querySelector('.plan-options-tags');
        const hiddenFieldsContainer = dutyCard.querySelector('.plan-hidden-fields');
        
        if (tagsContainer) {
            tagsContainer.innerHTML = '';
            showDefaultTag(dutyId);
        }
        
        if (hiddenFieldsContainer) {
            hiddenFieldsContainer.innerHTML = '';
        }
        
        saveScheduleSettings(dutyId);
        validateGenerateButton(); // ИСПРАВЛЕНО: было updateGenerateButton()
        
        showNotification('Все настройки очищены', 'success', 2000);
    }

    // === СОХРАНЕНИЕ НАСТРОЕК РАСПИСАНИЯ ===
    function saveScheduleSettings(dutyId) {
        const dutyCard = document.querySelector(`.plan-duty-card[data-duty-id="${dutyId}"]`);
        if (!dutyCard) return;

        const formData = new FormData();
        formData.append('duty_id', dutyId);
        formData.append('year', window.CURRENT_YEAR || new Date().getFullYear());
        formData.append('month', window.CURRENT_MONTH || new Date().getMonth() + 1);
        
        const token = getCSRFToken();
        if (token) {
            formData.append('csrfmiddlewaretoken', token);
        }

        const hiddenFieldsContainer = dutyCard.querySelector('.plan-hidden-fields');
        if (hiddenFieldsContainer) {
            const ranges = [];
            const specificDates = [];
            const weekdays = [];
            
            hiddenFieldsContainer.querySelectorAll('input[name="ranges[]"]').forEach(field => {
                if (field.value && field.value.trim()) {
                    ranges.push(field.value.trim());
                }
            });
            
            hiddenFieldsContainer.querySelectorAll('input[name="specific_dates[]"]').forEach(field => {
                if (field.value && field.value.trim()) {
                    specificDates.push(field.value.trim());
                }
            });
            
            hiddenFieldsContainer.querySelectorAll('input[name="weekdays[]"]').forEach(field => {
                if (field.value && field.value.trim()) {
                    weekdays.push(field.value.trim());
                }
            });
            
            ranges.forEach(range => formData.append('ranges[]', range));
            specificDates.forEach(date => formData.append('specific_dates[]', date));
            weekdays.forEach(day => formData.append('weekdays[]', day));
            
            console.log(`💾 Сохраняем для duty_id=${dutyId}:`);
            console.log(`  - ranges: ${ranges.length}`);
            console.log(`  - specific_dates: ${specificDates.length}`);
            console.log(`  - weekdays: ${weekdays.length}`);
        }

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': token
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                console.log(`✅ Настройки для наряда ${dutyId} сохранены`);
            } else {
                console.error(`❌ Ошибка сохранения для наряда ${dutyId}:`, data);
                showNotification(`Ошибка сохранения настроек: ${data?.error || 'Неизвестная ошибка'}`, 'error');
            }
        })
        .catch(error => {
            console.error(`❌ Ошибка сети при сохранении настроек для наряда ${dutyId}:`, error);
            showNotification('Ошибка сети при сохранении настроек', 'error');
        });
    }

    // === УПРАВЛЕНИЕ ПОДРАЗДЕЛЕНИЯМИ ===
    function initUnitSelection() {
        console.log('🏛️ Инициализация выбора подразделений...');
        
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

        document.querySelectorAll('.unit-checkbox-input').forEach(ch => {
            ch.addEventListener('change', () => {
                updateUnitCheckboxState(ch);
                updateUnitSelection();
            });
            updateUnitCheckboxState(ch);
        });

        updateUnitSelection();
    }

    function updateUnitCheckboxState(checkbox) {
        const label = checkbox.closest('.unit-checkbox');
        if (label) {
            label.classList.toggle('checked', checkbox.checked);
        }
    }

    function updateUnitSelection() {
        const selectedCount = document.querySelectorAll('.unit-checkbox-input:checked').length;
        const countElement = document.getElementById('selected-units-count');
        
        if (countElement) {
            countElement.textContent = selectedCount;
        }

        updateSelectedUnitsField();
        validateGenerateButton();
    }

    function updateSelectedUnitsField() {
        const selectedUnits = Array.from(document.querySelectorAll('.unit-checkbox-input:checked'))
            .map(checkbox => checkbox.value)
            .filter(value => value);
        
        const hiddenField = document.getElementById('plan-selected-units');
        if (hiddenField) {
            hiddenField.value = selectedUnits.join(',');
        }
    }

    // === УПРАВЛЕНИЕ НАРЯДАМИ ===
    function initDutySelection() {
        console.log('🎖️ Инициализация выбора нарядов...');
        
        document.querySelectorAll('.plan-duty-check').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const card = this.closest('.plan-duty-card');
                if (card) {
                    card.classList.toggle('selected', this.checked);
                }
                updateDutySelection();
            });
            
            const card = checkbox.closest('.plan-duty-card');
            if (card) {
                card.classList.toggle('selected', checkbox.checked);
            }
        });

        updateDutySelection();
    }

    function updateDutySelection() {
        const selectedDuties = Array.from(document.querySelectorAll('.plan-duty-check:checked'))
            .map(checkbox => checkbox.value)
            .filter(value => value);
        
        const hiddenField = document.getElementById('plan-selected-duties');
        if (hiddenField) {
            hiddenField.value = selectedDuties.join(',');
        }
        
        validateGenerateButton();
    }

    // === ГЕНЕРАЦИЯ ГРАФИКА ===
    function initGeneratePlan() {
        const generateBtn = document.getElementById('plan-generate-btn');
        if (!generateBtn) return;

        generateBtn.addEventListener('click', function() {
            if (this.disabled) {
                showNotification('Не выбраны наряды или подразделения', 'warning');
                return;
            }
            
            const selectedDuties = Array.from(document.querySelectorAll('.plan-duty-check:checked'))
                .map(checkbox => checkbox.value)
                .filter(value => value);
            const selectedUnits = Array.from(document.querySelectorAll('.unit-checkbox-input:checked'))
                .map(checkbox => checkbox.value)
                .filter(value => value);

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
        console.log('🚀 Начало генерации факультетского плана');
        
        saveAllScheduleSettings();
        
        const formData = new FormData();
        formData.append('year', window.CURRENT_YEAR || new Date().getFullYear());
        formData.append('month', window.CURRENT_MONTH || new Date().getMonth() + 1);
        formData.append('duties', dutyIds.join(','));
        
        const token = getCSRFToken();
        if (token) {
            formData.append('csrfmiddlewaretoken', token);
        }
        
        unitValues.forEach(unit => {
            if (unit) {
                formData.append('selected_units', unit);
            }
        });
        
        const generateBtn = document.getElementById('plan-generate-btn');
        const originalText = generateBtn.innerHTML;
        
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерация...';
        
        const url = '/faculty/duty/plan/generate/';
        console.log('📤 Отправка запроса на генерацию:', url);
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': token
            }
        })
        .then(response => {
            console.log('📥 Получен ответ:', response.status);
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('❌ Ошибка HTTP:', response.status, text);
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ Ответ сервера:', data);
            if (data.success) {
                showNotification(data.message || `График успешно сгенерирован! Создано ${data.count} записей.`, 'success', 3000);
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(`Ошибка: ${data.error}`, 'error');
                generateBtn.innerHTML = originalText;
                generateBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('❌ Ошибка при генерации:', error);
            showNotification('Ошибка при генерации графика: ' + error.message, 'error');
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        });
    }
    
    function saveAllScheduleSettings() {
        console.log('💾 Сохранение всех настроек перед генерацией...');
        document.querySelectorAll('.plan-duty-check:checked').forEach(checkbox => {
            const dutyId = checkbox.value;
            if (dutyId) {
                saveScheduleSettings(dutyId);
            }
        });
    }

    // === МОДАЛЬНЫЕ ОКНА ===
    function initModals() {
        console.log('🪟 Инициализация модальных окон...');
        
        const unitModal = document.getElementById('unitSelectModal');
        if (!unitModal) {
            console.error('❌ Модальное окно не найдено');
            return;
        }
        
        const closeBtn = unitModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                unitModal.style.display = 'none';
            });
        }
        
        const cancelBtn = document.getElementById('cancelSelection');
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
        
        document.querySelectorAll('.unit-item').forEach(item => {
            item.addEventListener('click', function() {
                const unitType = this.dataset.type;
                const unitId = this.dataset.id;
                const unitName = this.textContent.trim();
                
                updateFacultyAssignment(unitType, unitId, unitName);
                unitModal.style.display = 'none';
            });
        });
        
        console.log('✅ Модальные окна инициализированы');
    }

    // === ИНИЦИАЛИЗАЦИЯ ТЕГОВ С СЕРВЕРА ===
    function initServerTags() {
        console.log('🔄 Инициализация тегов с сервера...');
        
        document.querySelectorAll('.plan-duty-card').forEach(card => {
            const dutyId = card.dataset.dutyId;
            
            card.querySelectorAll('.plan-remove-tag').forEach(removeBtn => {
                removeBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const type = this.dataset.type;
                    const value = this.dataset.value;
                    const tag = this.closest('.plan-option-tag');
                    
                    if (tag) {
                        tag.remove();
                        updateHiddenFields(dutyId);
                        
                        const tagsContainer = card.querySelector('.plan-options-tags');
                        const remainingTags = tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)');
                        
                        if (remainingTags.length === 0) {
                            showDefaultTag(dutyId);
                        }
                        
                        saveScheduleSettings(dutyId);
                        validateGenerateButton(); // ИСПРАВЛЕНО: было updateGenerateButton()
                        
                        showNotification('Параметр удален', 'success', 2000);
                    }
                });
            });
        });
        
        console.log('✅ Теги с сервера инициализированы');
    }

    // Глобальные функции для модальных окон
    window.openFacultyUnitModal = function(scheduleId) {
        console.log('🪟 Открытие модального окна для расписания:', scheduleId);
        currentScheduleId = scheduleId;
        const modal = document.getElementById('unitSelectModal');
        if (modal) {
            modal.style.display = 'block';
        }
    };

    window.updateFacultyAssignment = function(unitType, unitId, unitName) {
        const scheduleId = currentScheduleId;
        if (!scheduleId) {
            showNotification('Ошибка: не найден ID расписания', 'error');
            return;
        }
        
        console.log('🔄 Обновление назначения:', scheduleId, unitType, unitId, unitName);
        
        const formData = new FormData();
        formData.append('unit_type', unitType);
        formData.append('unit_id', unitId);
        
        const token = getCSRFToken();
        if (token) {
            formData.append('csrfmiddlewaretoken', token);
        }
        
        const url = `/faculty/schedules/${scheduleId}/update/`;
        console.log('📤 Отправка запроса на:', url);
        
        const tableRow = document.querySelector(`tr[data-schedule-id="${scheduleId}"]`);
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': token
            }
        })
        .then(response => {
            console.log('📥 Получен ответ:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showNotification('Назначение успешно обновлено', 'success');
                
                if (tableRow) {
                    const unitCell = tableRow.querySelector('.unit-display');
                    if (unitCell) {
                        unitCell.textContent = data.unit_name;
                        unitCell.setAttribute('data-unit-type', data.unit_type);
                        unitCell.setAttribute('data-unit-id', unitId);
                    }
                    
                    const statusCell = tableRow.querySelector('.assignment-type');
                    if (statusCell) {
                        statusCell.setAttribute('data-is-fixed', data.duty_type === 'fixed' ? 'true' : 'false');
                        statusCell.setAttribute('data-is-manually-assigned', 'true');
                        
                        statusCell.innerHTML = '';
                        statusCell.innerHTML = '<span class="plan-badge badge-changed">Изменен</span>';
                    }
                    
                    const actionBtn = tableRow.querySelector('.btn-change-modern');
                    if (actionBtn) {
                        actionBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Изменено';
                        actionBtn.disabled = true;
                        actionBtn.style.opacity = '0.6';
                        actionBtn.style.cursor = 'not-allowed';
                    }
                }
                
                updateCalendarSchedule(scheduleId, data.unit_name);
                
            } else {
                showNotification('Ошибка: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка сети:', error);
            showNotification('Ошибка сети: ' + error.message, 'error');
        });
    };

    function updateCalendarSchedule(scheduleId, unitName) {
        const calendarSchedule = document.querySelector(`.clickable-duty[data-schedule-id="${scheduleId}"]`);
        if (calendarSchedule) {
            const assignedUnitDiv = calendarSchedule.querySelector('.plan-assigned-unit');
            if (assignedUnitDiv) {
                assignedUnitDiv.textContent = unitName;
                assignedUnitDiv.classList.add('changed');
                
                if (!assignedUnitDiv.innerHTML.includes('*')) {
                    assignedUnitDiv.innerHTML += ' *';
                }
            }
        }
    }

    // === ОСНОВНАЯ ИНИЦИАЛИЗАЦИЯ ===
    function init() {
        console.log('🚀 Запуск инициализации факультетской системы...');
        
        try {
            if (!window.CURRENT_YEAR || !window.CURRENT_MONTH) {
                const now = new Date();
                window.CURRENT_YEAR = now.getFullYear();
                window.CURRENT_MONTH = now.getMonth() + 1;
            }
            
            initScheduleToggles();
            initFlatpickr();
            initScheduleTags();
            initUnitSelection();
            initDutySelection();
            initGeneratePlan();
            initModals();
            initServerTags();
            validateGenerateButton();
            
            console.log('✅ Факультетская система полностью инициализирована');
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            showNotification('Ошибка инициализации системы: ' + error.message, 'error');
        }
    }

    window.initFacultySystem = init;
    
    setTimeout(init, 100);
});
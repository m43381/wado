// duty_plan.js - полный рабочий файл

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Инициализация системы планирования нарядов...');

    // === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
    let currentScheduleId = null;

    // === ОСНОВНЫЕ ФУНКЦИИ ДЛЯ ПЛАНИРОВАНИЯ ===

    // Функция для добавления диапазона дат
    window.addDateRange = function(dutyId) {
        console.log('🎯 Вызов addDateRange для dutyId:', dutyId);
        
        const rangeInput = document.querySelector(`[data-duty-id="${dutyId}"] [data-range-selector]`);
        if (!rangeInput) {
            console.error('❌ Поле ввода не найдено для dutyId:', dutyId);
            showNotification('Ошибка: поле ввода не найдено', 'error');
            return;
        }
        
        const rangeValue = rangeInput.value.trim();
        
        console.log('📅 Добавление диапазона:', {
            dutyId: dutyId,
            value: rangeValue
        });
        
        if (!rangeValue) {
            showNotification('Выберите диапазон дат', 'warning');
            return;
        }
        
        // Упрощенная проверка - просто проверяем что есть "по" и две даты
        if (!rangeValue.includes(' по ') || rangeValue.split(' по ').length !== 2) {
            showNotification('Некорректный формат диапазона. Используйте "дд.мм.гггг по дд.мм.гггг"', 'error');
            return;
        }
        
        console.log('✅ Формат корректен, добавляем опцию...');
        addScheduleOption(dutyId, 'range', rangeValue);
        rangeInput.value = '';
        
        // Очищаем flatpickr
        if (rangeInput._flatpickr) {
            rangeInput._flatpickr.clear();
        }
    };

    // Функция для добавления опции в расписание
    function addScheduleOption(dutyId, type, value) {
        console.log(`➕ Добавление опции: duty=${dutyId}, type=${type}, value=${value}`);
        
        const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
        const hiddenFieldsContainer = document.querySelector(`.plan-hidden-fields[data-duty-id="${dutyId}"]`);
        
        if (!tagsContainer || !hiddenFieldsContainer) {
            console.error('❌ Контейнеры не найдены');
            return;
        }
        
        // Удаляем тег по умолчанию если он есть
        removeDefaultTag(dutyId);
        
        // Для дней недели преобразуем название в число
        let normalizedValue = value;
        let displayValue = value;
        
        if (type === 'weekday') {
            // Преобразуем название дня недели в число
            const weekdayMap = {
                'Понедельник': '0',
                'Вторник': '1', 
                'Среда': '2',
                'Четверг': '3',
                'Пятница': '4',
                'Суббота': '5',
                'Воскресенье': '6'
            };
            
            normalizedValue = weekdayMap[value] || value;
            displayValue = value; // Оставляем название для отображения
            console.log(`📅 Преобразовано: "${value}" -> "${normalizedValue}"`);
        }
        
        // Проверяем дубликаты по значению И типу
        const existingTags = tagsContainer.querySelectorAll('.plan-option-tag');
        for (let tag of existingTags) {
            const removeButton = tag.querySelector('.plan-remove-tag');
            if (removeButton && removeButton.dataset.value === normalizedValue && removeButton.dataset.type === type) {
                console.log('⚠️ Такой тег уже существует');
                showNotification('Этот параметр уже добавлен', 'warning', 2000);
                return;
            }
        }
        
        // Создаем визуальный тег
        const tag = document.createElement('span');
        tag.className = `plan-option-tag plan-${type}-tag`;
        
        tag.innerHTML = `
            <i class="fas fa-${getIconForType(type)}"></i>
            ${displayValue}
            <button type="button" class="plan-remove-tag" data-type="${type}" data-value="${normalizedValue}">&times;</button>
        `;
        
        tagsContainer.appendChild(tag);
        
        // Создаем скрытое поле для формы
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';

        // ИСПРАВЛЕНИЕ: для конкретных дат используем correct name
        if (type === 'date') {
            hiddenField.name = 'specific_dates[]';
        } else {
            hiddenField.name = `${type}s[]`;
        }

        hiddenField.value = normalizedValue;
        hiddenFieldsContainer.appendChild(hiddenField);
        
        console.log(`📝 Создано скрытое поле: ${type}s[] = ${normalizedValue}`);
        
        // Добавляем обработчик удаления
        const removeButton = tag.querySelector('.plan-remove-tag');
        removeButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🗑️ Удаление тега:', type, normalizedValue);
            removeScheduleOption(dutyId, type, normalizedValue, tag, hiddenField);
        });
        
        console.log('✅ Тег успешно добавлен');
        
        // Сохраняем настройки
        saveScheduleSettings(dutyId);
        updateGenerateButton();
        
        showNotification('Параметр добавлен', 'success', 2000);
    }

    // Функция для получения иконки по типу
    function getIconForType(type) {
        const icons = {
            'range': 'calendar-day',
            'date': 'calendar-check',
            'weekday': 'calendar-week'
        };
        return icons[type] || 'calendar-alt';
    }

    // Функция удаления опции
    function removeScheduleOption(dutyId, type, value, tagElement, hiddenField) {
        if (tagElement) tagElement.remove();
        if (hiddenField) hiddenField.remove();
        
        // Проверяем, остались ли теги
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
            console.log('🗑️ Удален тег по умолчанию');
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

    function clearScheduleSettings(dutyId) {
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

    // CSRF токен
    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    // Функция для нормализации дней недели
    function normalizeWeekdayForDisplay(weekday) {
        const weekdayMap = {
            '0': 'Понедельник',
            '1': 'Вторник',
            '2': 'Среда',
            '3': 'Четверг',
            '4': 'Пятница',
            '5': 'Суббота',
            '6': 'Воскресенье'
        };
        return weekdayMap[weekday] || weekday;
    }

    // === ИНИЦИАЛИЗАЦИЯ FLATPICKR ===
    function initFlatpickr() {
        console.log('📅 Инициализация Flatpickr...');
        
        // Диапазоны дат - исправленная версия
        document.querySelectorAll('.plan-schedule-container').forEach(container => {
            const dutyId = container.dataset.dutyId;
            
            // Ищем все группы опций
            const rangeGroups = container.querySelectorAll('.plan-option-group');
            
            rangeGroups.forEach((rangeGroup, index) => {
                // Первая группа - это диапазон дат
                if (index === 0) {
                    const inputGroup = rangeGroup.querySelector('.plan-input-group');
                    
                    if (!inputGroup) {
                        console.log(`⚠️ Группа ввода не найдена для наряда ${dutyId}`);
                        return;
                    }
                    
                    // Создаем контейнер для двух полей ввода
                    const newHtml = `
                        <div class="plan-range-container" style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px;">
                            <input type="text" class="form-control plan-range-start" 
                                placeholder="Начало (дд.мм.гггг)" 
                                style="flex: 1;">
                            <span style="color: #666;">по</span>
                            <input type="text" class="form-control plan-range-end" 
                                placeholder="Конец (дд.мм.гггг)" 
                                style="flex: 1;">
                            <button type="button" class="btn btn-outline-primary btn-sm plan-add-range" 
                                    data-duty-id="${dutyId}">
                                <i class="fas fa-plus"></i> Добавить
                            </button>
                        </div>
                    `;
                    
                    // Заменяем содержимое
                    inputGroup.innerHTML = newHtml;
                    
                    // Скрываем старое поле если оно есть
                    const oldInput = rangeGroup.querySelector('input[data-range-selector]');
                    if (oldInput) {
                        oldInput.style.display = 'none';
                    }
                    
                    // Инициализируем Flatpickr
                    const startInput = inputGroup.querySelector('.plan-range-start');
                    const endInput = inputGroup.querySelector('.plan-range-end');
                    
                    if (startInput && endInput) {
                        flatpickr(startInput, {
                            locale: "ru",
                            dateFormat: "d.m.Y",
                            minDate: new Date(CURRENT_YEAR, CURRENT_MONTH - 1, 1),
                            maxDate: new Date(CURRENT_YEAR, CURRENT_MONTH, 0),
                            allowInput: true
                        });
                        
                        flatpickr(endInput, {
                            locale: "ru",
                            dateFormat: "d.m.Y",
                            minDate: new Date(CURRENT_YEAR, CURRENT_MONTH - 1, 1),
                            maxDate: new Date(CURRENT_YEAR, CURRENT_MONTH, 0),
                            allowInput: true
                        });
                        
                        // Обработчик кнопки
                        const addButton = inputGroup.querySelector('.plan-add-range');
                        if (addButton) {
                            addButton.addEventListener('click', function() {
                                addDateRangeFromInputs(dutyId, startInput, endInput);
                            });
                            
                            // Также добавляем обработчик на Enter
                            [startInput, endInput].forEach(input => {
                                input.addEventListener('keypress', function(e) {
                                    if (e.key === 'Enter') {
                                        addDateRangeFromInputs(dutyId, startInput, endInput);
                                    }
                                });
                            });
                        }
                    }
                }
            });
        });

        // Конкретные даты - исправленная версия
        document.querySelectorAll('.plan-schedule-container').forEach(container => {
            const dutyId = container.dataset.dutyId;
            const datesInput = container.querySelector('input[data-dates-selector]');
            
            if (datesInput) {
                flatpickr(datesInput, {
                    mode: "multiple",
                    locale: "ru",
                    dateFormat: "d.m.Y",
                    minDate: new Date(CURRENT_YEAR, CURRENT_MONTH - 1, 1),
                    maxDate: new Date(CURRENT_YEAR, CURRENT_MONTH, 0),
                    showMonths: 1,
                    allowInput: true
                });
            }
        });
        
        console.log('✅ Flatpickr инициализирован');
    }

    // Новая функция для добавления диапазона из двух полей
    function addDateRangeFromInputs(dutyId, startInput, endInput) {
        const startValue = startInput.value.trim();
        const endValue = endInput.value.trim();
        
        if (!startValue || !endValue) {
            showNotification('Заполните обе даты диапазона', 'warning');
            return;
        }
        
        const startDate = parseDate(startValue);
        const endDate = parseDate(endValue);
        
        if (!startDate || !endDate) {
            showNotification('Некорректный формат дат. Используйте дд.мм.гггг', 'error');
            return;
        }
        
        if (startDate > endDate) {
            showNotification('Дата начала не может быть позже даты окончания', 'error');
            return;
        }
        
        // Форматируем диапазон
        const rangeValue = `${formatDate(startDate)} по ${formatDate(endDate)}`;
        console.log('✅ Диапазон сформирован:', rangeValue);
        
        addScheduleOption(dutyId, 'range', rangeValue);
        
        // Очищаем поля
        startInput.value = '';
        endInput.value = '';
        if (startInput._flatpickr) startInput._flatpickr.clear();
        if (endInput._flatpickr) endInput._flatpickr.clear();
    }

    // Вспомогательные функции для работы с датами
    function parseDate(dateStr) {
        const formats = [
            /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/,
            /^(\d{1,2})\.(\d{1,2})\.(\d{2})$/
        ];
        
        for (const format of formats) {
            const match = dateStr.match(format);
            if (match) {
                let day = parseInt(match[1]);
                let month = parseInt(match[2]);
                let year = parseInt(match[3]);
                
                // Для двухзначного года
                if (year < 100) {
                    year += 2000;
                }
                
                // Проверяем валидность даты
                const date = new Date(year, month - 1, day);
                if (date.getDate() === day && date.getMonth() === month - 1 && date.getFullYear() === year) {
                    return date;
                }
            }
        }
        return null;
    }

    function formatDate(date) {
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        return `${day}.${month}.${year}`;
    }

    // Обновляем старую функцию addDateRange для совместимости
    window.addDateRange = function(dutyId) {
        console.log('⚠️ Используется устаревший метод addDateRange');
        const container = document.querySelector(`[data-duty-id="${dutyId}"] .plan-range-container`);
        if (container) {
            const startInput = container.querySelector('.plan-range-start');
            const endInput = container.querySelector('.plan-range-end');
            addDateRangeFromInputs(dutyId, startInput, endInput);
        }
    };

    // === УПРАВЛЕНИЕ РАСКРЫТИЕМ/СКРЫТИЕМ НАСТРОЕК ===
    function initScheduleToggles() {
        const dutyHeaders = document.querySelectorAll('.plan-duty-header');
        
        dutyHeaders.forEach(header => {
            if (!header) return;
            
            header.addEventListener('click', function(e) {
                // Не срабатывает при клике на чекбокс
                if (e.target.type === 'checkbox') return;
                
                const dutyCard = this.closest('.plan-duty-card');
                if (!dutyCard) return;
                
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
        
        console.log('✅ Переключатели настроек инициализированы');
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

                console.log('📅 Добавление конкретных дат:', input.value);
                
                // Получаем выбранные даты из flatpickr
                const flatpickrInstance = input._flatpickr;
                if (!flatpickrInstance || !flatpickrInstance.selectedDates.length) {
                    showNotification('Выберите конкретные даты', 'warning');
                    return;
                }
                
                let addedCount = 0;
                
                // Обрабатываем каждую выбранную дату
                flatpickrInstance.selectedDates.forEach(date => {
                    const formattedDate = formatDate(date);
                    console.log(`📅 Добавление конкретной даты: ${formattedDate}`);
                    addScheduleOption(dutyId, 'date', formattedDate);
                    addedCount++;
                });
                
                console.log(`✅ Добавлено ${addedCount} дат`);
                
                // Очищаем поле
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
                if (confirm('Очистить ВСЕ параметры расписания для этого наряда? Все диапазоны, даты и дни недели будут удалены.')) {
                    clearAllScheduleSettings(dutyId);
                }
            });
        });
        
        // Сброс фильтров (полная очистка + сброс на сервере)
        document.querySelectorAll('.plan-reset-filters').forEach(btn => {
            btn.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                if (confirm('Полностью сбросить все фильтры для этого наряда? Это очистит все настройки и на сервере.')) {
                    resetScheduleFilters(dutyId);
                }
            });
        });
        
        console.log('✅ Теги расписания инициализированы');
    }

    // Новая функция для полного сброса фильтров
    function resetScheduleFilters(dutyId) {
        console.log(`🔄 Полный сброс фильтров для наряда ${dutyId}`);
        
        // Очищаем локальные настройки
        clearAllScheduleSettings(dutyId);
        
        // Отправляем запрос на сервер для полного сброса
        const formData = new FormData();
        formData.append('duty_id', dutyId);
        formData.append('year', CURRENT_YEAR);
        formData.append('month', CURRENT_MONTH);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Отправляем пустые данные для полного сброса
        fetch('', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Все фильтры полностью сброшены', 'success', 3000);
            } else {
                throw new Error(data.error || 'Ошибка сброса фильтров');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка при сбросе фильтров:', error);
            showNotification('Ошибка при сбросе фильтров', 'error');
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
        const ranges = [];
        const specificDates = [];
        const weekdays = [];

        if (hiddenFieldsContainer) {
            console.log(`🔍 Поиск скрытых полей для наряда ${dutyId}:`);
            
            hiddenFieldsContainer.querySelectorAll('input').forEach(input => {
                console.log(`   📋 Найдено поле: ${input.name} = ${input.value}`);
                
                if (input.name === 'ranges[]' && input.value) {
                    ranges.push(input.value);
                    console.log(`     ✅ Добавлен диапазон: ${input.value}`);
                } else if ((input.name === 'specific_dates[]' || input.name === 'dates[]') && input.value) {
                    specificDates.push(input.value);
                    console.log(`     ✅ Добавлена дата: ${input.value}`);
                } else if (input.name === 'weekdays[]' && input.value) {
                    weekdays.push(input.value);
                    console.log(`     ✅ Добавлен день недели: ${input.value}`);
                }
            });
        }

        console.log(`💾 Сохранение настроек для наряда ${dutyId}:`, {
            ranges: ranges,
            specificDates: specificDates,
            weekdays: weekdays
        });

        // Добавляем данные в formData
        ranges.forEach(range => {
            if (range && range.trim()) {
                formData.append('ranges[]', range.trim());
            }
        });
        
        specificDates.forEach(date => {
            if (date && date.trim()) {
                formData.append('specific_dates[]', date.trim());
            }
        });
        
        weekdays.forEach(weekday => {
            if (weekday && weekday.trim()) {
                formData.append('weekdays[]', weekday.trim());
            }
        });

        // Отправляем на сервер
        fetch('', {
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
                console.log('✅ Настройки успешно сохранены на сервере:', data.settings);
            } else {
                console.error('❌ Ошибка сохранения настроек:', data);
            }
        })
        .catch(error => {
            console.error('❌ Ошибка при сохранении настроек:', error);
        });
    }

    // === УПРАВЛЕНИЕ ПОДРАЗДЕЛЕНИЯМИ ===
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
                saveSelectionState();
            });
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => {
                document.querySelectorAll('.unit-checkbox-input').forEach(ch => {
                    ch.checked = false;
                    updateUnitCheckboxState(ch);
                });
                updateUnitSelection();
                saveSelectionState();
            });
        }

        // Обработка изменений чекбоксов
        document.querySelectorAll('.unit-checkbox-input').forEach(ch => {
            if (ch) {
                ch.addEventListener('change', () => {
                    updateUnitCheckboxState(ch);
                    updateUnitSelection();
                    saveSelectionState();
                });
                updateUnitCheckboxState(ch);
            }
        });

        updateUnitSelection();
    }


    function saveSelectionState() {
        const selectedUnits = Array.from(document.querySelectorAll('.unit-checkbox-input:checked'))
            .map(checkbox => checkbox.value);
        const selectedDuties = Array.from(document.querySelectorAll('.plan-duty-check:checked'))
            .map(checkbox => checkbox.value);
        
        localStorage.setItem('selected_units_state', JSON.stringify(selectedUnits));
        localStorage.setItem('selected_duties_state', JSON.stringify(selectedDuties));
        
        console.log('💾 Сохранено состояние:', { selectedUnits, selectedDuties });
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
            console.log('💾 Сохранены выбранные подразделения:', hiddenField.value);
        }
    }

    // === УПРАВЛЕНИЕ НАРЯДАМИ ===
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
                saveSelectionState();
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

    // === ВАЛИДАЦИЯ КНОПКИ ГЕНЕРАЦИИ ===
    function validateGenerateButton() {
        const selectedUnits = document.querySelectorAll('.unit-checkbox-input:checked').length;
        const selectedDuties = document.querySelectorAll('.plan-duty-check:checked').length;
        
        const isValid = selectedUnits > 0 && selectedDuties > 0;
        const generateBtn = document.getElementById('plan-generate-btn');
        
        if (generateBtn) {
            generateBtn.disabled = !isValid;
            
            if (isValid) {
                generateBtn.classList.add('ready');
                generateBtn.title = 'Готово к генерации графика';
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
        // Создаем контейнер для уведомлений если его нет
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
        
        // Закрытие по клику
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Автоматическое закрытие
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }
        
        // Добавляем CSS анимации
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

    // === ГЕНЕРАЦИЯ ГРАФИКА ===
    function initGeneratePlan() {
        const generateBtn = document.getElementById('plan-generate-btn');
        if (!generateBtn) return;

        generateBtn.addEventListener('click', function() {
            const selectedDuties = Array.from(document.querySelectorAll('.plan-duty-check:checked'))
                .map(checkbox => checkbox.value);
            const selectedUnits = Array.from(document.querySelectorAll('.unit-checkbox-input:checked'))
                .map(checkbox => checkbox.value);

            if (selectedDuties.length === 0) {
                showNotification('Выберите наряды для генерации', 'warning');
                return;
            }

            if (selectedUnits.length === 0) {
                showNotification('Выберите подразделения для распределения', 'warning');
                return;
            }

            if (!confirm(`Сгенерировать график нарядов?\n\nВыбрано:\n- ${selectedDuties.length} нарядов\n- ${selectedUnits.length} подразделений`)) {
                return;
            }

            generatePlan(selectedDuties, selectedUnits);
        });
    }

    function generatePlan(dutyIds, unitValues) {
        console.log('🚀 Начало генерации плана');
        console.log('📦 Отправляемые данные:');
        console.log('   - dutyIds:', dutyIds);
        console.log('   - unitValues:', unitValues);
        
        // Проверяем что unitValues не пустые
        if (unitValues.length === 0) {
            showNotification('Ошибка: не выбраны подразделения', 'error');
            console.error('❌ unitValues пустой!');
            return;
        }
        
        // Сохраняем текущее состояние выбранных подразделений в localStorage
        const selectedUnitsState = Array.from(document.querySelectorAll('.unit-checkbox-input:checked'))
            .map(checkbox => checkbox.value);
        localStorage.setItem('selected_units_state', JSON.stringify(selectedUnitsState));
        
        console.log('💾 Сохранены подразделения в localStorage:', selectedUnitsState);
        
        // ВАЖНО: Сохраняем настройки расписания перед генерацией
        saveAllScheduleSettings();
        
        // Проверяем что URL доступен
        if (!GENERATE_DUTY_PLAN_URL) {
            showNotification('Ошибка: URL для генерации не найден', 'error');
            console.error('GENERATE_DUTY_PLAN_URL is not defined');
            return;
        }

        const generateBtn = document.getElementById('plan-generate-btn');
        const originalText = generateBtn.innerHTML;
        
        // Блокируем кнопку и показываем индикатор
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерация...';

        const formData = new FormData();
        formData.append('year', CURRENT_YEAR);
        formData.append('month', CURRENT_MONTH);
        formData.append('duties', dutyIds.join(','));
        
        // ВАЖНО: Правильно добавляем selected_units
        unitValues.forEach(unit => {
            console.log('➕ Добавляем подразделение:', unit);
            formData.append('selected_units', unit);
        });
        
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        console.log('📤 Отправка запроса на генерацию графика...');

        fetch(GENERATE_DUTY_PLAN_URL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
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
                showNotification(
                    `График успешно сгенерирован! Создано ${data.count} записей для ${data.units_count} подразделений`, 
                    'success', 
                    3000
                );
                
                // Обновляем страницу через 2 секунды чтобы увидеть изменения
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                console.error('❌ Ошибка от сервера:', data.error);
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка при генерации:', error);
            showNotification('Ошибка при генерации графика: ' + error.message, 'error');
        })
        .finally(() => {
            // Восстанавливаем кнопку
            generateBtn.disabled = false;
            generateBtn.innerHTML = originalText;
        });
    }
    
    // Функция для сохранения всех настроек расписания
    function saveAllScheduleSettings() {
        console.log('💾 Сохранение всех настроек расписания перед генерацией...');
        
        document.querySelectorAll('.plan-duty-check:checked').forEach(checkbox => {
            const dutyId = checkbox.value;
            saveScheduleSettings(dutyId);
        });
    }

    // === ФУНКЦИОНАЛ РЕДАКТИРОВАНИЯ ЗАПИСЕЙ ===

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

    function updateScheduleAssignment(scheduleId, unitType, unitId, unitName) {
        console.log(`🔄 Обновление назначения: schedule=${scheduleId}, unit=${unitType}_${unitId}`);
        
        // Получаем текущее назначение перед изменением
        const currentAssignment = getCurrentAssignment(scheduleId);
        console.log('📋 Текущее назначение:', currentAssignment);
        
        const formData = new FormData();
        formData.append('unit_type', unitType);
        formData.append('unit_id', unitId);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Используем правильный URL
        const url = `/commandant/schedules/${scheduleId}/update/`;
        console.log(`📤 Отправка запроса на: ${url}`);
        
        // Сохраняем информацию о наряде для обновления статистики
        const scheduleElement = document.querySelector(`.clickable-duty[data-schedule-id="${scheduleId}"]`);
        const dutyName = scheduleElement ? scheduleElement.dataset.dutyName : 'Наряд';
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        })
        .then(response => {
            console.log(`📥 Получен ответ: ${response.status}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('✅ Назначение успешно обновлено:', data);
                
                // ВАЖНО: Используем unitId из ответа сервера, а не из параметров
                const actualUnitId = data.unit_id || unitId;
                updateScheduleDisplay(scheduleId, unitType, actualUnitId, data.unit_name, data.status);
                updateCalendarDisplay(scheduleId, unitType, data.unit_name);
                
                // ОБНОВЛЯЕМ СТАТИСТИКУ с учетом старого и нового назначения
                updateStatistics(
                    currentAssignment.type, 
                    currentAssignment.id,
                    unitType, 
                    actualUnitId, 
                    data.unit_name, 
                    dutyName
                );
                
                showNotification('Назначение успешно обновлено', 'success');
            } else {
                console.error('❌ Ошибка от сервера:', data.error);
                throw new Error(data.error || 'Unknown server error');
            }
        })
        .catch(error => {
            console.error('❌ Ошибка при обновлении назначения:', error);
            showNotification('Ошибка при обновлении назначения: ' + error.message, 'error');
        });
    }

    function updateScheduleDisplay(scheduleId, unitType, unitId, unitName, status) {
        const scheduleRow = document.querySelector(`tr[data-schedule-id="${scheduleId}"]`);
        if (scheduleRow) {
            const unitCell = scheduleRow.querySelector('.unit-display');
            const typeCell = scheduleRow.querySelector('.assignment-type');
            
            // Форматируем отображение в зависимости от типа подразделения
            let displayText = unitName;
            if (unitType === 'faculty' && !unitName.includes('Факультет')) {
                displayText = `Факультет: ${unitName}`;
            } else if (unitType === 'department' && !unitName.includes('Кафедра')) {
                displayText = `Кафедра: ${unitName}`;
            }
            // Если unitName уже содержит правильный префикс, используем как есть
            
            unitCell.innerHTML = displayText;
            
            // ВАЖНО: Устанавливаем data-атрибуты с ТЕМИ ЖЕ значениями, что передаются в updateStatistics
            unitCell.dataset.unitType = unitType;
            unitCell.dataset.unitId = unitId; // Используем тот же unitId что пришел из сервера
            
            console.log(`📝 Установлены data-атрибуты: ${unitType}_${unitId}`);
            
            // Обновляем статус на основе данных с сервера
            const statusMap = {
                'fixed': '<span class="plan-badge plan-badge-fixed">Закреплен</span>',
                'rotating': '<span class="plan-badge plan-badge-rotating">Ротация</span>',
                'changed': '<span class="plan-badge badge-changed">Изменен</span>'
            };
            
            if (statusMap[status]) {
                typeCell.innerHTML = statusMap[status];
            }
            
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
                // Форматируем отображение для календаря
                let displayText = unitName;
                if (unitType === 'faculty' && !unitName.includes('Факультет')) {
                    displayText = `Ф: ${unitName}`;
                } else if (unitType === 'department' && !unitName.includes('Кафедра')) {
                    displayText = `К: ${unitName}`;
                }
                
                assignedUnit.innerHTML = `${displayText} *`;
                assignedUnit.classList.add('changed');
            }
            
            scheduleElement.classList.add('manual-assignment', 'schedule-updated');
            setTimeout(() => {
                scheduleElement.classList.remove('schedule-updated');
            }, 1000);
        }
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
        
        // Обработчики таблицы
        // document.querySelectorAll('.plan-schedules-table tbody tr').forEach(row => {
        //     row.addEventListener('click', function(event) {
        //         if (!event.target.closest('.btn-change')) {
        //             const scheduleId = this.dataset.scheduleId;
        //             openUnitModal(scheduleId);
        //         }
        //     });
        // });
    }

    // === ФУНКЦИЯ ДЛЯ ВОССТАНОВЛЕНИЯ СОСТОЯНИЯ ===
    function restoreSelectionState() {
        console.log('🔄 Восстановление состояния...');
        
        // Проверяем, есть ли план и сгенерирован ли он
        const debugInfo = document.querySelector('.plan-status .alert');
        const isPlanGenerated = debugInfo && debugInfo.textContent.includes('График сгенерирован');
        
        // Если план не сгенерирован, очищаем localStorage
        if (!isPlanGenerated) {
            console.log('📭 План не сгенерирован, очищаем localStorage');
            localStorage.removeItem('selected_units_state');
            localStorage.removeItem('selected_duties_state');
            return;
        }
        
        // Восстанавливаем выбранные подразделения из localStorage
        const savedUnits = localStorage.getItem('selected_units_state');
        if (savedUnits) {
            try {
                const units = JSON.parse(savedUnits);
                console.log('📋 Восстановление подразделений:', units);
                
                document.querySelectorAll('.unit-checkbox-input').forEach(checkbox => {
                    const shouldBeChecked = units.includes(checkbox.value);
                    checkbox.checked = shouldBeChecked;
                    updateUnitCheckboxState(checkbox);
                });
            } catch (e) {
                console.error('❌ Ошибка восстановления подразделений:', e);
            }
        }
        
        // Восстанавливаем выбранные наряды из localStorage
        const savedDuties = localStorage.getItem('selected_duties_state');
        if (savedDuties) {
            try {
                const duties = JSON.parse(savedDuties);
                console.log('📋 Восстановление нарядов:', duties);
                
                document.querySelectorAll('.plan-duty-check').forEach(checkbox => {
                    const shouldBeChecked = duties.includes(checkbox.value);
                    checkbox.checked = shouldBeChecked;
                    const card = checkbox.closest('.plan-duty-card');
                    if (shouldBeChecked) {
                        card.classList.add('selected');
                    } else {
                        card.classList.remove('selected');
                    }
                });
            } catch (e) {
                console.error('❌ Ошибка восстановления нарядов:', e);
            }
        }
        
        // Обновляем интерфейс
        updateUnitSelection();
        updateDutySelection();
        
        console.log('✅ Состояние восстановлено');
    }

    // === ОБНОВЛЕНИЕ КНОПКИ ГЕНЕРАЦИИ ===
    function updateGenerateButton() {
        console.log('🔄 Обновление состояния кнопки генерации');
        
        // Проверяем, есть ли хотя бы один наряд с настройками расписания
        const hasScheduleSettings = checkIfAnyDutyHasScheduleSettings();
        
        const generateBtn = document.getElementById('plan-generate-btn');
        if (!generateBtn) return;
        
        // Если есть настройки расписания, активируем кнопку
        if (hasScheduleSettings) {
            generateBtn.disabled = false;
            generateBtn.classList.add('ready');
            generateBtn.title = 'Готово к генерации графика';
            console.log('✅ Кнопка генерации активирована');
        } else {
            // Иначе используем стандартную валидацию
            validateGenerateButton();
        }
    }

    // Проверяем, есть ли у нарядов настройки расписания
    function checkIfAnyDutyHasScheduleSettings() {
        let hasSettings = false;
        
        document.querySelectorAll('.plan-duty-check:checked').forEach(checkbox => {
            const dutyId = checkbox.value;
            const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
            
            if (tagsContainer) {
                // Проверяем, есть ли теги (кроме тега по умолчанию)
                const customTags = tagsContainer.querySelectorAll('.plan-option-tag:not(.plan-default-tag)');
                if (customTags.length > 0) {
                    hasSettings = true;
                    console.log(`✅ Наряд ${dutyId} имеет настройки расписания`);
                }
            }
        });
        
        return hasSettings;
    }

    function updateScheduleStatusDisplay(scheduleId, status) {
        const scheduleRow = document.querySelector(`tr[data-schedule-id="${scheduleId}"]`);
        if (!scheduleRow) return;
        
        const statusCell = scheduleRow.querySelector('.assignment-type');
        const statusMap = {
            'fixed': '<span class="plan-badge plan-badge-fixed">Закреплен</span>',
            'rotating': '<span class="plan-badge plan-badge-rotating">Ротация</span>',
            'changed': '<span class="plan-badge badge-changed">Изменен</span>'
        };
        
        if (statusMap[status]) {
            statusCell.innerHTML = statusMap[status];
        }
        
        // Добавляем анимацию обновления
        scheduleRow.classList.add('schedule-updated');
        setTimeout(() => {
            scheduleRow.classList.remove('schedule-updated');
        }, 1000);
    }


    function updateStatistics(oldUnitType, oldUnitId, newUnitType, newUnitId, newUnitName, dutyName) {
        console.log('📊 Обновление статистики:', {
            oldUnit: `${oldUnitType}_${oldUnitId}`,
            newUnit: `${newUnitType}_${newUnitId}`
        });
        
        const statsGrid = document.querySelector('.plan-stats-grid');
        if (!statsGrid) {
            console.log('❌ Сетка статистики не найдена');
            return;
        }
        
        // 1. Уменьшаем счетчик у старого подразделения
        if (oldUnitType && oldUnitId && !(oldUnitType === newUnitType && oldUnitId === newUnitId)) {
            const oldStatCard = findStatCard(statsGrid, oldUnitType, oldUnitId);
            
            if (oldStatCard) {
                const countElement = oldStatCard.querySelector('.plan-stat-count');
                const dutiesElement = oldStatCard.querySelector('.plan-stat-duties');
                
                const currentCount = getCountFromElement(countElement);
                const newCount = Math.max(0, currentCount - 1);
                
                console.log(`   Старый счетчик: ${currentCount} -> ${newCount}`);
                
                if (newCount <= 0) {
                    oldStatCard.remove();
                    console.log('🗑️ Удалена карточка статистики для старого подразделения');
                } else {
                    updateCountElement(countElement, newCount);
                    removeDutyFromList(dutiesElement, dutyName);
                }
            }
        }
        
        // 2. Увеличиваем счетчик у нового подразделения
        if (newUnitType && newUnitId && !(oldUnitType === newUnitType && oldUnitId === newUnitId)) {
            let newStatCard = findStatCard(statsGrid, newUnitType, newUnitId);
            
            if (newStatCard) {
                const countElement = newStatCard.querySelector('.plan-stat-count');
                const dutiesElement = newStatCard.querySelector('.plan-stat-duties');
                
                const currentCount = getCountFromElement(countElement);
                const newCount = currentCount + 1;
                
                console.log(`   Новый счетчик: ${currentCount} -> ${newCount}`);
                
                updateCountElement(countElement, newCount);
                addDutyToList(dutiesElement, dutyName);
            } else {
                // Создаем новую карточку
                newStatCard = createStatCard(newUnitType, newUnitId, newUnitName, dutyName);
                statsGrid.appendChild(newStatCard);
                console.log('✅ Добавлена новая карточка статистики');
            }
        }
        
        // 3. Очищаем пустые карточки
        cleanupEmptyStatCards(statsGrid);
    }

    // Вспомогательные функции для работы со счетчиками
    function getCountFromElement(countElement) {
        if (!countElement) return 0;
        
        const countText = countElement.textContent.trim();
        const numberMatch = countText.match(/(\d+)/);
        return numberMatch ? parseInt(numberMatch[1]) : 0;
    }

    function updateCountElement(countElement, count) {
        if (!countElement) return;
        
        countElement.textContent = `${count} наряд${getRussianPlural(count)}`;
    }

    function findStatCard(statsGrid, unitType, unitId) {
        // Ищем по data-атрибутам
        const normalizedId = String(unitId).replace('faculty_', '').replace('department_', '');
        const card = statsGrid.querySelector(`[data-unit-type="${unitType}"][data-unit-id="${normalizedId}"]`);
        
        if (card) {
            console.log(`   ✅ Найдена карточка: ${unitType}_${normalizedId}`);
            return card;
        }
        
        console.log(`   ❌ Карточка не найдена: ${unitType}_${normalizedId}`);
        return null;
    }

    // Новая функция для очистки пустых карточек
    function cleanupEmptyStatCards(statsGrid) {
        const allCards = statsGrid.querySelectorAll('.plan-stat-card');
        let removedCount = 0;
        
        console.log(`🧹 Начало очистки пустых карточек. Всего карточек: ${allCards.length}`);
        
        allCards.forEach(card => {
            const countElement = card.querySelector('.plan-stat-count');
            const nameElement = card.querySelector('.plan-stat-name');
            const unitType = card.getAttribute('data-unit-type');
            const unitId = card.getAttribute('data-unit-id');
            
            if (countElement) {
                const count = getCountFromElement(countElement);
                
                console.log(`   🔍 Проверка: "${nameElement?.textContent}" (${unitType}_${unitId}): ${count}`);
                
                if (count <= 0) {
                    card.remove();
                    removedCount++;
                    console.log(`   🗑️ Удалена карточка "${nameElement?.textContent}" с нулевым счетчиком`);
                }
            }
        });
        
        if (removedCount > 0) {
            console.log(`🧹 Очищено ${removedCount} пустых карточек статистики`);
        } else {
            console.log(`🔍 Пустых карточек не найдено`);
        }
        
        // Покажем оставшиеся карточки для отладки
        const remainingCards = statsGrid.querySelectorAll('.plan-stat-card');
        console.log(`📊 Осталось карточек: ${remainingCards.length}`);
        remainingCards.forEach(card => {
            const name = card.querySelector('.plan-stat-name')?.textContent;
            const count = card.querySelector('.plan-stat-count')?.textContent;
            const unitType = card.getAttribute('data-unit-type');
            const unitId = card.getAttribute('data-unit-id');
            console.log(`   📋 ${name} (${unitType}_${unitId}): ${count}`);
        });
    }

    

    function createStatCard(unitType, unitId, unitName, dutyName) {
        const statCard = document.createElement('div');
        statCard.className = 'plan-stat-card';
        
        // Нормализуем ID
        const normalizedId = String(unitId).replace('faculty_', '').replace('department_', '');
        
        statCard.setAttribute('data-unit-type', unitType);
        statCard.setAttribute('data-unit-id', normalizedId);
        
        // Форматируем имя для отображения
        let displayName = unitName;
        if (unitType === 'faculty' && !unitName.includes('Факультет')) {
            displayName = `Факультет ${unitName}`;
        } else if (unitType === 'department' && !unitName.includes('Кафедра')) {
            displayName = `Кафедра ${unitName}`;
        }
        
        statCard.innerHTML = `
            <div class="plan-stat-name">${displayName}</div>
            <div class="plan-stat-count">1 наряд</div>
            <div class="plan-stat-duties">
                <span class="plan-duty-tag">${dutyName}</span>
            </div>
        `;
        
        console.log(`   ✅ Создана карточка: ${unitType}_${normalizedId} - "${displayName}"`);
        
        return statCard;
    }

    function removeDutyFromList(dutiesElement, dutyName) {
        const dutyTags = dutiesElement.querySelectorAll('.plan-duty-tag');
        const normalizedDutyName = dutyName.trim().toLowerCase();
        
        dutyTags.forEach(tag => {
            const tagText = tag.textContent.trim().toLowerCase();
            if (tagText === normalizedDutyName) {
                tag.remove();
                console.log(`   🗑️ Удален наряд "${dutyName}" из списка`);
            }
        });
        
        // Если после удаления список пуст, добавляем сообщение
        if (dutiesElement.children.length === 0) {
            dutiesElement.innerHTML = '<span class="no-duties">Нет нарядов</span>';
        }
    }
    const style = document.createElement('style');
    style.textContent = `
        .no-duties {
            color: #999;
            font-style: italic;
            font-size: 0.9em;
        }
    `;
    document.head.appendChild(style);

    function addDutyToList(dutiesElement, dutyName) {
        let dutyExists = false;
        const dutyTags = dutiesElement.querySelectorAll('.plan-duty-tag');
        
        dutyTags.forEach(tag => {
            if (tag.textContent.trim() === dutyName.trim()) {
                dutyExists = true;
            }
        });
        
        if (!dutyExists) {
            const dutyTag = document.createElement('span');
            dutyTag.className = 'plan-duty-tag';
            dutyTag.textContent = dutyName;
            dutiesElement.appendChild(dutyTag);
        }
    }

    // Вспомогательная функция для правильного склонения
    function getRussianPlural(count) {
        if (count % 10 === 1 && count % 100 !== 11) {
            return '';
        } else if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) {
            return 'а';
        } else {
            return 'ов';
        }
    }

    function getCurrentAssignment(scheduleId) {
        const scheduleRow = document.querySelector(`tr[data-schedule-id="${scheduleId}"]`);
        if (!scheduleRow) {
            console.log(`❌ Строка расписания ${scheduleId} не найдена`);
            return { type: null, id: null, name: null };
        }
        
        const unitCell = scheduleRow.querySelector('.unit-display');
        if (!unitCell) {
            console.log(`❌ Ячейка подразделения для ${scheduleId} не найдена`);
            return { type: null, id: null, name: null };
        }
        
        // Получаем данные из data-атрибутов
        const unitType = unitCell.dataset.unitType;
        const unitId = unitCell.dataset.unitId;
        
        console.log(`📋 Текущее назначение из data-атрибутов: ${unitType}_${unitId}`);
        
        return {
            type: unitType || null,
            id: unitId || null,
            name: unitCell.textContent.trim() || null
        };
    }

    function loadInitialScheduleSettings() {
        console.log('📥 Загрузка начальных настроек расписания...');
        
        // Проходим по всем нарядам и загружаем их настройки из data-атрибутов
        document.querySelectorAll('.plan-duty-card').forEach(card => {
            const dutyId = card.dataset.dutyId;
            const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
            
            if (tagsContainer) {
                // Проверяем, есть ли уже теги (значит настройки загружены из сервера)
                const existingTags = tagsContainer.querySelectorAll('.plan-option-tag');
                if (existingTags.length > 0) {
                    console.log(`✅ Настройки для наряда ${dutyId} уже загружены:`, existingTags.length, 'тегов');
                    
                    // ВАЖНО: Восстанавливаем скрытые поля для каждого тега
                    const hiddenFieldsContainer = document.querySelector(`.plan-hidden-fields[data-duty-id="${dutyId}"]`);
                    if (hiddenFieldsContainer) {
                        hiddenFieldsContainer.innerHTML = ''; // Очищаем перед восстановлением
                        
                        existingTags.forEach(tag => {
                            const removeButton = tag.querySelector('.plan-remove-tag');
                            if (removeButton && removeButton.dataset.type && removeButton.dataset.value) {
                                const type = removeButton.dataset.type;
                                let value = removeButton.dataset.value;
                                
                                // Пропускаем теги по умолчанию
                                if (tag.classList.contains('plan-default-tag')) {
                                    return;
                                }
                                
                                console.log(`   🔄 Восстановление тега: ${type} = ${value}`);
                                
                                // Восстанавливаем скрытое поле
                                const hiddenField = document.createElement('input');
                                hiddenField.type = 'hidden';

                                // ИСПРАВЛЕНИЕ: для конкретных дат используем правильное имя
                                if (type === 'date') {
                                    hiddenField.name = 'specific_dates[]';
                                } else {
                                    hiddenField.name = `${type}s[]`;
                                }

                                hiddenField.value = value;
                                hiddenFieldsContainer.appendChild(hiddenField);
                                
                                console.log(`     ✅ Восстановлено скрытое поле: ${type}s[] = ${value}`);
                                
                                // Добавляем обработчик удаления
                                removeButton.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    console.log('🗑️ Удаление существующего тега:', type, value);
                                    removeScheduleOption(dutyId, type, value, tag, hiddenField);
                                });
                            } else {
                                console.log(`   ⚠️ Тег без данных:`, tag.textContent);
                            }
                        });
                    }
                } else {
                    console.log(`📭 Для наряда ${dutyId} нет настроек`);
                }
            }
        });
    }

    function clearAllScheduleSettings(dutyId) {
        console.log(`🧹 Полная очистка настроек для наряда ${dutyId}`);
        
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

        // Полностью очищаем скрытые поля
        const hiddenFields = container.querySelector('.plan-hidden-fields');
        if (hiddenFields) {
            hiddenFields.innerHTML = '';
        }

        // Очищаем визуальные теги
        const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
        if (tagsContainer) {
            tagsContainer.innerHTML = '';
            showDefaultTag(dutyId);
        }
        
        // Сохраняем изменения на сервер
        saveScheduleSettings(dutyId);
        
        showNotification('Все параметры расписания очищены', 'success', 3000);
    }

    // Добавляем отладочную функцию для проверки состояния
    function debugScheduleSettings() {
        console.log('🐛 ОТЛАДКА: Текущее состояние настроек');
        
        document.querySelectorAll('.plan-duty-card').forEach(card => {
            const dutyId = card.dataset.dutyId;
            const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
            const hiddenFields = document.querySelector(`.plan-hidden-fields[data-duty-id="${dutyId}"]`);
            
            console.log(`🔍 Наряд ${dutyId}:`);
            console.log(`   - Теги:`, tagsContainer?.querySelectorAll('.plan-option-tag').length || 0);
            
            // Показываем все теги
            if (tagsContainer) {
                tagsContainer.querySelectorAll('.plan-option-tag').forEach((tag, index) => {
                    const removeButton = tag.querySelector('.plan-remove-tag');
                    const type = removeButton?.dataset.type || 'unknown';
                    const value = removeButton?.dataset.value || tag.textContent;
                    console.log(`     🏷️ Тег ${index}: ${type} = ${value}`);
                });
            }
            
            console.log(`   - Скрытые поля:`, hiddenFields?.querySelectorAll('input').length || 0);
            
            if (hiddenFields) {
                hiddenFields.querySelectorAll('input').forEach(input => {
                    console.log(`     📋 ${input.name}: ${input.value}`);
                });
            }
        });
    }

    function forceRefreshScheduleSettings() {
        console.log('🔄 Принудительное обновление настроек расписания...');
        
        // Перезагружаем настройки с сервера
        document.querySelectorAll('.plan-duty-card').forEach(card => {
            const dutyId = card.dataset.dutyId;
            const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
            
            if (tagsContainer) {
                // Очищаем текущие теги
                tagsContainer.innerHTML = '';
                
                // Показываем тег по умолчанию
                showDefaultTag(dutyId);
                
                // Загружаем настройки с сервера через AJAX
                loadDutySettingsFromServer(dutyId);
            }
        });
    }

    // Функция для загрузки настроек с сервера
    function loadDutySettingsFromServer(dutyId) {
        const url = `?year=${CURRENT_YEAR}&month=${CURRENT_MONTH}&ajax=1&duty_id=${dutyId}`;
        
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.settings) {
                console.log(`📥 Загружены настройки для наряда ${dutyId}:`, data.settings);
                applyServerSettings(dutyId, data.settings);
            }
        })
        .catch(error => {
            console.error(`❌ Ошибка загрузки настроек для наряда ${dutyId}:`, error);
        });
    }

    // Функция применения настроек с сервера
    function applyServerSettings(dutyId, settings) {
        const tagsContainer = document.getElementById(`plan-tags-${dutyId}`);
        const hiddenFieldsContainer = document.querySelector(`.plan-hidden-fields[data-duty-id="${dutyId}"]`);
        
        if (!tagsContainer || !hiddenFieldsContainer) return;
        
        // Очищаем текущие настройки
        tagsContainer.innerHTML = '';
        hiddenFieldsContainer.innerHTML = '';
        
        // Применяем настройки с сервера
        if (settings.ranges && settings.ranges.length > 0) {
            settings.ranges.forEach(range => {
                addScheduleOption(dutyId, 'range', range);
            });
        }
        
        if (settings.specific_dates && settings.specific_dates.length > 0) {
            settings.specific_dates.forEach(date => {
                addScheduleOption(dutyId, 'date', date);
            });
        }
        
        if (settings.weekdays && settings.weekdays.length > 0) {
            settings.weekdays.forEach(weekday => {
                addScheduleOption(dutyId, 'weekday', weekday);
            });
        }
        
        // Если нет настроек, показываем тег по умолчанию
        if (!settings.ranges?.length && !settings.specific_dates?.length && !settings.weekdays?.length) {
            showDefaultTag(dutyId);
        }
        
        console.log(`✅ Применены настройки с сервера для наряда ${dutyId}`);
    }

    // === ОСНОВНАЯ ИНИЦИАЛИЗАЦИЯ ===
    function init() {
        console.log('🚀 Запуск инициализации системы...');
        
        try {
            // Восстанавливаем состояние В ПЕРВУЮ ОЧЕРЕДЬ
            restoreSelectionState();
            
            // Инициализируем компоненты
            initFlatpickr();
            initScheduleToggles(); 
            initScheduleTags();
            initUnitSelection();
            initDutySelection();
            validateGenerateButton();
            initGeneratePlan();
            initEditingEventHandlers();
            
            // Загружаем начальные настройки расписания ПОСЛЕ инициализации всех компонентов
            setTimeout(() => {
                loadInitialScheduleSettings();
                debugScheduleSettings(); // Отладочная информация
            }, 100);
            
            console.log('✅ Система полностью инициализирована');
        } catch (error) {
            console.error('❌ Ошибка инициализации:', error);
            showNotification('Ошибка инициализации системы', 'error');
        }
    }

    // Запуск
    init();
});
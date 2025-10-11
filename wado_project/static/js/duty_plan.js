document.addEventListener('DOMContentLoaded', function() {
    // Функция для получения CSRF токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Инициализация Flatpickr с правильными настройками для диапазонов
    function initFlatpickr() {
        // Инициализация для диапазонов дат
        const rangeInputs = document.querySelectorAll('.range-input');
        rangeInputs.forEach(input => {
            flatpickr(input, {
                mode: "range",
                locale: "ru",
                dateFormat: "d.m.Y",
                allowInput: true,
                onChange: function(selectedDates, dateStr, instance) {
                    // Flatpickr сам форматирует дату правильно
                    // Просто принимаем то, что он возвращает
                    input.value = dateStr;
                }
            });
        });

        // Инициализация для конкретных дат (множественный выбор)
        const datesInputs = document.querySelectorAll('.dates-input');
        datesInputs.forEach(input => {
            flatpickr(input, {
                mode: "multiple",
                locale: "ru",
                dateFormat: "d.m.Y",
                allowInput: true,
                onChange: function(selectedDates, dateStr) {
                    input.value = dateStr;
                }
            });
        });
    }

    // Валидация диапазона дат - более гибкая
    function validateDateRange(rangeStr) {
    // Flatpickr всегда возвращает корректный формат, так что просто проверяем наличие текста
    return rangeStr && rangeStr.trim().length > 0 && rangeStr.includes(' ');
}

    // Нормализация диапазона дат для единообразного хранения
    function normalizeDateRange(rangeStr) {
    // Flatpickr уже возвращает в правильном формате, просто нормализуем даты
    if (!rangeStr) return rangeStr;
    
    const separators = [' to ', ' — ', ' - ', ' по '];
    let separator = ' to ';
    
    // Находим используемый разделитель
    for (const sep of separators) {
        if (rangeStr.includes(sep)) {
            separator = sep;
            break;
        }
    }
    
    const dateParts = rangeStr.split(separator);
    
    if (dateParts.length !== 2) return rangeStr;
    
    const normalizeDate = (dateStr) => {
        const parts = dateStr.trim().split('.');
        if (parts.length !== 3) return dateStr.trim();
        
        const day = parts[0].padStart(2, '0');
        const month = parts[1].padStart(2, '0');
        const year = parts[2];
        
        return `${day}.${month}.${year}`;
    };
    
    const start = normalizeDate(dateParts[0]);
    const end = normalizeDate(dateParts[1]);
    
    return `${start}${separator}${end}`;
}

    // Автоматическое сохранение при изменении
    function autoSaveFormData(dutyId) {
        const form = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"]`);
        if (!form) return;
        
        const formData = new FormData(form);
        
        // Добавляем параметры месяца
        const urlParams = new URLSearchParams(window.location.search);
        formData.append('year', urlParams.get('year') || new Date().getFullYear());
        formData.append('month', urlParams.get('month') || new Date().getMonth() + 1);
        
        // Показываем индикатор сохранения
        showSavingIndicator(dutyId);
        
        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData
        })
        .then(response => {
            if (response.redirected) {
                hideSavingIndicator(dutyId);
                showNotification('Настройки автоматически сохранены', 'success', 2000);
            }
        })
        .catch(error => {
            console.error('Error auto-saving data:', error);
            hideSavingIndicator(dutyId);
            showNotification('Ошибка при сохранении настроек', 'error');
        });
    }

    // Индикатор сохранения
    function showSavingIndicator(dutyId) {
        const form = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"]`);
        if (!form) return;
        
        let indicator = form.querySelector('.saving-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'saving-indicator';
            indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';
            const formActions = form.querySelector('.form-actions');
            if (formActions) {
                formActions.prepend(indicator);
            } else {
                form.appendChild(indicator);
            }
        }
        indicator.style.display = 'block';
    }

    function hideSavingIndicator(dutyId) {
        const form = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"]`);
        if (!form) return;
        
        const indicator = form.querySelector('.saving-indicator');
        if (indicator) {
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 500);
        }
    }

    // Функция для полной очистки формы и данных на сервере
    function clearFormData(dutyId) {
        const tagsContainer = document.getElementById(`tags-${dutyId}`);
        const hiddenFields = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"] .hidden-fields`);
        const rangeInput = document.querySelector(`.range-input[data-duty-id="${dutyId}"]`);
        const datesInput = document.querySelector(`.dates-input[data-duty-id="${dutyId}"]`);
        
        // Очищаем поля ввода
        if (rangeInput) {
            rangeInput.value = '';
            if (rangeInput._flatpickr) {
                rangeInput._flatpickr.clear();
            }
        }
        if (datesInput) {
            datesInput.value = '';
            if (datesInput._flatpickr) {
                datesInput._flatpickr.clear();
            }
        }
        
        // Сбрасываем чекбоксы дней недели
        const weekdaysCheckboxes = document.querySelectorAll(`.weekday-checkbox input[data-duty-id="${dutyId}"]`);
        weekdaysCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Очищаем скрытые поля
        if (hiddenFields) {
            hiddenFields.innerHTML = '';
        }
        
        // Очищаем теги и показываем "весь месяц"
        if (tagsContainer) {
            tagsContainer.innerHTML = `
                <span class="option-tag default-tag">
                    <i class="fas fa-calendar-alt"></i>
                    Весь месяц
                    <span class="tag-hint">(по умолчанию)</span>
                </span>
            `;
        }
        
        // Автоматически сохраняем очистку
        setTimeout(() => autoSaveFormData(dutyId), 300);
    }

    // Удаление тега "весь месяц" при добавлении любого параметра
    function removeDefaultTag(dutyId) {
        const tagsContainer = document.getElementById(`tags-${dutyId}`);
        if (tagsContainer) {
            const defaultTag = tagsContainer.querySelector('.default-tag');
            if (defaultTag) {
                defaultTag.remove();
            }
        }
    }

    // Управление тегами опций
    function initOptionTags() {
        // Добавление диапазона
        document.querySelectorAll('.add-range').forEach(button => {
            button.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const input = document.querySelector(`.range-input[data-duty-id="${dutyId}"]`);
                const tagsContainer = document.getElementById(`tags-${dutyId}`);
                const hiddenFields = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"] .hidden-fields`);
                
                if (input && input.value.trim()) {
                    // Валидация диапазона
                    if (!validateDateRange(input.value)) {
                        showNotification('Некорректный формат диапазона. Пример: 01.10.2025 to 10.10.2025', 'error');
                        return;
                    }
                    
                    removeDefaultTag(dutyId);
                    
                    // Нормализуем диапазон перед сохранением
                    const normalizedRange = normalizeDateRange(input.value);
                    addRangeTag(normalizedRange, dutyId, tagsContainer, hiddenFields);
                    
                    input.value = '';
                    
                    // Очищаем Flatpickr
                    if (input._flatpickr) {
                        input._flatpickr.clear();
                    }
                } else {
                    showNotification('Введите диапазон дат', 'warning');
                }
            });
        });

        // Добавление конкретных дат
        document.querySelectorAll('.add-dates').forEach(button => {
            button.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const input = document.querySelector(`.dates-input[data-duty-id="${dutyId}"]`);
                const tagsContainer = document.getElementById(`tags-${dutyId}`);
                const hiddenFields = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"] .hidden-fields`);
                
                if (input && input.value.trim()) {
                    removeDefaultTag(dutyId);
                    const dates = input.value.split(', ');
                    let validDatesAdded = false;
                    
                    dates.forEach(date => {
                        if (date.trim()) {
                            // Валидация даты
                            const dateRegex = /^\d{1,2}\.\d{1,2}\.\d{4}$/;
                            if (dateRegex.test(date.trim())) {
                                // Нормализуем дату
                                const normalizedDate = normalizeDate(date.trim());
                                addDateTag(normalizedDate, dutyId, tagsContainer, hiddenFields);
                                validDatesAdded = true;
                            }
                        }
                    });
                    
                    if (!validDatesAdded) {
                        showNotification('Некорректный формат дат. Используйте: дд.мм.гггг', 'error');
                    }
                    
                    input.value = '';
                    
                    // Очищаем Flatpickr
                    if (input._flatpickr) {
                        input._flatpickr.clear();
                    }
                } else {
                    showNotification('Выберите конкретные даты', 'warning');
                }
            });
        });

        // Добавление дней недели
        document.querySelectorAll('.add-weekdays').forEach(button => {
            button.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                const checkboxes = document.querySelectorAll(`.weekday-checkbox input[data-duty-id="${dutyId}"]:checked`);
                const tagsContainer = document.getElementById(`tags-${dutyId}`);
                const hiddenFields = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"] .hidden-fields`);
                
                if (checkboxes.length > 0) {
                    removeDefaultTag(dutyId);
                    checkboxes.forEach(checkbox => {
                        addWeekdayTag(checkbox.value, dutyId, tagsContainer, hiddenFields);
                        checkbox.checked = false;
                    });
                } else {
                    showNotification('Выберите хотя бы один день недели', 'warning');
                }
            });
        });

        // Удаление тегов
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-tag')) {
                const tag = e.target.closest('.option-tag');
                const dutyId = tag.closest('.schedule-form').dataset.dutyId;
                const type = e.target.dataset.type;
                const value = e.target.dataset.value;
                
                removeTag(type, value, dutyId);
                tag.remove();
                
                // Проверяем, остались ли теги
                const tagsContainer = document.getElementById(`tags-${dutyId}`);
                if (tagsContainer) {
                    const remainingTags = tagsContainer.querySelectorAll('.option-tag:not(.default-tag)');
                    
                    if (remainingTags.length === 0) {
                        tagsContainer.innerHTML = `
                            <span class="option-tag default-tag">
                                <i class="fas fa-calendar-alt"></i>
                                Весь месяц
                                <span class="tag-hint">(по умолчанию)</span>
                            </span>
                        `;
                    }
                    
                    // Автоматически сохраняем изменения
                    setTimeout(() => autoSaveFormData(dutyId), 300);
                }
                
                showNotification('Параметр удален', 'info', 2000);
            }
        });

        // Очистка всех тегов
        document.querySelectorAll('.clear-all').forEach(button => {
            button.addEventListener('click', function() {
                const dutyId = this.dataset.dutyId;
                
                if (confirm('Очистить все выбранные параметры? Наряд будет распределен на весь месяц.')) {
                    clearFormData(dutyId);
                    showNotification('Все параметры очищены', 'info', 3000);
                }
            });
        });
    }

    // Функция для нормализации даты (добавление ведущих нулей)
    function normalizeDate(dateStr) {
        const parts = dateStr.split('.');
        if (parts.length !== 3) return dateStr;
        
        const day = parts[0].padStart(2, '0');
        const month = parts[1].padStart(2, '0');
        const year = parts[2];
        
        return `${day}.${month}.${year}`;
    }

    // Функции для работы с тегами
    function addRangeTag(range, dutyId, tagsContainer, hiddenFields) {
        if (!tagsContainer || !hiddenFields) return;
        
        const tag = document.createElement('span');
        tag.className = 'option-tag range-tag';
        tag.innerHTML = `
            <i class="fas fa-calendar-day"></i>
            ${range}
            <button type="button" class="remove-tag" data-type="range" data-value="${range}">&times;</button>
        `;
        
        tagsContainer.appendChild(tag);
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'ranges[]';
        hiddenInput.value = range;
        hiddenFields.appendChild(hiddenInput);
        
        // Автоматически сохраняем
        setTimeout(() => autoSaveFormData(dutyId), 300);
        
        showNotification('Диапазон дат добавлен', 'success', 2000);
    }

    function addDateTag(date, dutyId, tagsContainer, hiddenFields) {
        if (!tagsContainer || !hiddenFields) return;
        
        const tag = document.createElement('span');
        tag.className = 'option-tag date-tag';
        tag.innerHTML = `
            <i class="fas fa-calendar-check"></i>
            ${date}
            <button type="button" class="remove-tag" data-type="date" data-value="${date}">&times;</button>
        `;
        
        tagsContainer.appendChild(tag);
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'specific_dates[]';
        hiddenInput.value = date;
        hiddenFields.appendChild(hiddenInput);
        
        // Автоматически сохраняем
        setTimeout(() => autoSaveFormData(dutyId), 300);
        
        showNotification('Конкретная дата добавлена', 'success', 2000);
    }

    function addWeekdayTag(weekday, dutyId, tagsContainer, hiddenFields) {
        if (!tagsContainer || !hiddenFields) return;
        
        const weekdayNames = {
            'Понедельник': 'Понедельник',
            'Вторник': 'Вторник',
            'Среда': 'Среда',
            'Четверг': 'Четверг',
            'Пятница': 'Пятница',
            'Суббота': 'Суббота',
            'Воскресенье': 'Воскресенье'
        };
        
        const displayName = weekdayNames[weekday] || weekday;
        
        const tag = document.createElement('span');
        tag.className = 'option-tag weekday-tag';
        tag.innerHTML = `
            <i class="fas fa-calendar-week"></i>
            ${displayName}
            <button type="button" class="remove-tag" data-type="weekday" data-value="${weekday}">&times;</button>
        `;
        
        tagsContainer.appendChild(tag);
        
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'weekdays[]';
        hiddenInput.value = weekday;
        hiddenFields.appendChild(hiddenInput);
        
        // Автоматически сохраняем
        setTimeout(() => autoSaveFormData(dutyId), 300);
        
        showNotification('День недели добавлен', 'success', 2000);
    }

    function removeTag(type, value, dutyId) {
        const hiddenFields = document.querySelector(`.schedule-form[data-duty-id="${dutyId}"] .hidden-fields`);
        if (!hiddenFields) return;
        
        const hiddenInputs = hiddenFields.querySelectorAll(`input[name="${type}s[]"]`);
        
        hiddenInputs.forEach(input => {
            if (input.value === value) {
                input.remove();
            }
        });
    }

    // Убираем кнопку сохранения и настраиваем автоматическое сохранение
    function initScheduleForms() {
        // Удаляем кнопки сохранения из DOM
        document.querySelectorAll('.schedule-form .btn-primary').forEach(btn => {
            if (btn.textContent.includes('Сохранить расписание')) {
                btn.remove();
            }
        });
        
        // Обновляем текст кнопки очистки
        document.querySelectorAll('.clear-all').forEach(btn => {
            btn.innerHTML = '<i class="fas fa-times"></i> Очистить все';
        });
        
        // Добавляем индикаторы сохранения в каждую форму
        document.querySelectorAll('.schedule-form').forEach(form => {
            const formActions = form.querySelector('.form-actions');
            if (formActions) {
                const indicator = document.createElement('div');
                indicator.className = 'saving-indicator';
                indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';
                indicator.style.display = 'none';
                formActions.prepend(indicator);
            }
        });
    }

    // Генерация плана нарядов
    function initGeneratePlan() {
        const generateBtn = document.getElementById('generate-plan-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', function() {
                const selectedDuties = getSelectedDuties();
                
                if (selectedDuties.length === 0) {
                    showNotification('Выберите хотя бы один наряд для планирования', 'warning');
                    return;
                }
                
                if (!confirm('Сгенерировать график нарядов? Существующие назначения будут перезаписаны.')) {
                    return;
                }
                
                generatePlan(selectedDuties);
            });
        }
    }

    function getSelectedDuties() {
        const selected = [];
        document.querySelectorAll('.duty-checkbox:checked').forEach(checkbox => {
            selected.push(checkbox.value);
        });
        return selected;
    }

    function generatePlan(dutyIds) {
        const url = '/commandant/generate-duty-plan/';
        const urlParams = new URLSearchParams(window.location.search);
        
        const formData = new FormData();
        formData.append('year', urlParams.get('year') || new Date().getFullYear());
        formData.append('month', urlParams.get('month') || new Date().getMonth() + 1);
        formData.append('duties', dutyIds.join(','));
        
        const generateBtn = document.getElementById('generate-plan-btn');
        const originalText = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерация...';
        generateBtn.disabled = true;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`График успешно сгенерирован! Создано ${data.count} записей.`, 'success');
                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                showNotification('Ошибка: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Произошла ошибка при генерации графика', 'error');
        })
        .finally(() => {
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        });
    }

    // Уведомления
    function showNotification(message, type = 'info', duration = 5000) {
        // Удаляем существующие уведомления того же типа
        document.querySelectorAll('.notification').forEach(notification => {
            if (notification.textContent.includes(message)) {
                notification.remove();
            }
        });
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Закрытие по кнопке
        notification.querySelector('.notification-close').addEventListener('click', () => {
            closeNotification(notification);
        });
        
        // Автоматическое закрытие
        if (duration > 0) {
            setTimeout(() => {
                closeNotification(notification);
            }, duration);
        }
    }

    function closeNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }

    function getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // Очистка старых данных при загрузке
    function cleanupOldData() {
        document.querySelectorAll('.hidden-fields').forEach(hiddenFields => {
            const inputs = hiddenFields.querySelectorAll('input');
            inputs.forEach(input => {
                if (input.value === '0' || input.value === '4' || input.value === '6') {
                    input.remove();
                }
            });
        });
    }

    // Инициализация тегов "весь месяц"
    function initDefaultTags() {
        document.querySelectorAll('.options-tags').forEach(tagsContainer => {
            const hasTags = tagsContainer.querySelectorAll('.option-tag:not(.default-tag)').length > 0;
            const hasDefaultTag = tagsContainer.querySelector('.default-tag');
            
            if (!hasTags && !hasDefaultTag) {
                tagsContainer.innerHTML = `
                    <span class="option-tag default-tag">
                        <i class="fas fa-calendar-alt"></i>
                        Весь месяц
                        <span class="tag-hint">(по умолчанию)</span>
                    </span>
                `;
            }
        });
    }

    // Анимации
    function initAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.duty-item').forEach(item => {
            observer.observe(item);
        });
    }

    // Обработка изменения чекбоксов нарядов
    function initDutyCheckboxes() {
        document.querySelectorAll('.duty-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const dutyItem = this.closest('.duty-item');
                if (this.checked) {
                    dutyItem.classList.add('active');
                } else {
                    dutyItem.classList.remove('active');
                }
            });
            
            // Инициализация состояния при загрузке
            if (checkbox.checked) {
                const dutyItem = checkbox.closest('.duty-item');
                dutyItem.classList.add('active');
            }
        });
    }

    // Управление сворачиванием блоков
function initCollapsibleSections() {
    // Сворачивание нарядов
    document.querySelectorAll('.duty-header').forEach(header => {
        header.addEventListener('click', function() {
            const dutyItem = this.closest('.duty-item');
            dutyItem.classList.toggle('collapsed');
            
            // Автоматически разворачиваем при выборе наряда
            const checkbox = dutyItem.querySelector('.duty-checkbox');
            if (checkbox && checkbox.checked && dutyItem.classList.contains('collapsed')) {
                dutyItem.classList.remove('collapsed');
            }
        });
    });
    
    // Сворачивание секций
    document.querySelectorAll('.section-header').forEach(header => {
        header.addEventListener('click', function() {
            this.classList.toggle('collapsed');
            const content = this.nextElementSibling;
            if (content) {
                content.classList.toggle('collapsed');
            }
        });
    });
    
    // Сворачивание основной панели управления
    const dutySelection = document.querySelector('.duty-selection');
    const dutySelectionHeader = dutySelection.querySelector('h3');
    
    dutySelectionHeader.addEventListener('click', function() {
        dutySelection.classList.toggle('collapsed');
        const content = dutySelection.querySelector('.duty-list, .plan-info, .generate-section');
        if (content) {
            content.classList.toggle('collapsed');
        }
    });
}

// Быстрые действия
function initQuickActions() {
    // Развернуть все
    document.getElementById('expand-all')?.addEventListener('click', function() {
        document.querySelectorAll('.duty-item.collapsed').forEach(item => {
            item.classList.remove('collapsed');
        });
        document.querySelectorAll('.section-header.collapsed').forEach(header => {
            header.classList.remove('collapsed');
            const content = header.nextElementSibling;
            if (content) content.classList.remove('collapsed');
        });
    });
    
    // Свернуть все
    document.getElementById('collapse-all')?.addEventListener('click', function() {
        document.querySelectorAll('.duty-item:not(.collapsed)').forEach(item => {
            item.classList.add('collapsed');
        });
        document.querySelectorAll('.section-header:not(.collapsed)').forEach(header => {
            header.classList.add('collapsed');
            const content = header.nextElementSibling;
            if (content) content.classList.add('collapsed');
        });
    });
    
    // Выбрать все наряды
    document.getElementById('select-all')?.addEventListener('click', function() {
        document.querySelectorAll('.duty-checkbox').forEach(checkbox => {
            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change'));
        });
    });
    
    // Снять выделение
    document.getElementById('deselect-all')?.addEventListener('click', function() {
        document.querySelectorAll('.duty-checkbox').forEach(checkbox => {
            checkbox.checked = false;
            checkbox.dispatchEvent(new Event('change'));
        });
    });
}

    // Инициализация всех функций
    function init() {
        initFlatpickr();
        initOptionTags();
        initScheduleForms();
        initGeneratePlan();
        initAnimations();
        initDutyCheckboxes();
        initCollapsibleSections();
        initQuickActions();
        cleanupOldData();
        initDefaultTags();
        
        console.log('Duty Plan JS initialized successfully');
    }

    // Запуск инициализации
    init();
});
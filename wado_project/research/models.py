from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from duty.models import MonthlyDutyPlan


class ResearchScenario(models.Model):
    """Сценарий исследования (внешний цикл СИМ)"""
    name = models.CharField('Название сценария', max_length=200)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    
    # Параметры СИМ
    n1_scenarios = models.IntegerField('Число сценариев (N₁)', default=100)
    n2_runs = models.IntegerField('Число прогонов (N₂)', default=50)
    guarantee_level = models.FloatField('Уровень гарантии (L)', default=0.9)
    
    # Требования (ẑ₁...ẑ₅)
    z1 = models.FloatField('ẑ₁ - мин. доля корректных', default=0.9)
    z2 = models.FloatField('ẑ₂ - мин. доля срочных', default=0.8)
    z3 = models.FloatField('ẑ₃ - макс. перегруз', default=0.1)
    z4 = models.FloatField('ẑ₄ - макс. перерасход', default=3.0)
    z5 = models.FloatField('ẑ₅ - макс. задержка', default=2.0)
    
    class Meta:
        verbose_name = 'Сценарий исследования'
        verbose_name_plural = 'Сценарии исследований'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (N₁={self.n1_scenarios}, N₂={self.n2_runs})"
    
    @property
    def total_simulations(self):
        """Общее число симуляций для сценария"""
        return self.n1_scenarios * self.n2_runs * 2  # *2 для V1 и V2
    
    def get_requirements_dict(self):
        """Возвращает требования в виде словаря"""
        return {
            'z1': self.z1,
            'z2': self.z2,
            'z3': self.z3,
            'z4': self.z4,
            'z5': self.z5
        }


class EffectivenessReport(models.Model):
    """Отчёт об эффективности распределения"""
    plan = models.ForeignKey(
        MonthlyDutyPlan, 
        on_delete=models.CASCADE, 
        related_name='research_reports',
        verbose_name='План распределения'
    )
    scenario = models.ForeignKey(
        ResearchScenario, 
        on_delete=models.CASCADE,
        verbose_name='Сценарий исследования'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    execution_time = models.FloatField('Время выполнения (сек)', default=0)
    total_simulations = models.IntegerField('Всего симуляций', default=0)
    
    # === ОСНОВНЫЕ ПОКАЗАТЕЛИ ===
    
    # Результаты для V1 (агрегированный)
    p_dc_v1_mean = models.FloatField(
        'P̄дц V1', 
        default=0.0,
        help_text='Средняя вероятность достижения цели для V1'
    )
    p_guaranteed_v1 = models.FloatField(
        'P₀.₉ V1', 
        default=0.0,
        help_text='Гарантируемая вероятность для V1 при L=0.9'
    )
    
    # Результаты для V2 (детализированный)
    p_dc_v2_mean = models.FloatField('P̄дц V2', default=0.0)
    p_guaranteed_v2 = models.FloatField('P₀.₉ V2', default=0.0)
    
    # === ДЕТАЛЬНАЯ СТАТИСТИКА V1 ===
    median_v1 = models.FloatField('Медиана V1', default=0.0)
    std_v1 = models.FloatField('Стандартное отклонение V1', default=0.0)
    min_v1 = models.FloatField('Минимальное значение V1', default=0.0)
    max_v1 = models.FloatField('Максимальное значение V1', default=0.0)
    cv_v1 = models.FloatField('Коэффициент вариации V1 (%)', default=0.0)
    skewness_v1 = models.FloatField('Асимметрия V1', default=0.0)
    kurtosis_v1 = models.FloatField('Эксцесс V1', default=0.0)
    
    # === ДЕТАЛЬНАЯ СТАТИСТИКА V2 ===
    median_v2 = models.FloatField('Медиана V2', default=0.0)
    std_v2 = models.FloatField('Стандартное отклонение V2', default=0.0)
    min_v2 = models.FloatField('Минимальное значение V2', default=0.0)
    max_v2 = models.FloatField('Максимальное значение V2', default=0.0)
    cv_v2 = models.FloatField('Коэффициент вариации V2 (%)', default=0.0)
    skewness_v2 = models.FloatField('Асимметрия V2', default=0.0)
    kurtosis_v2 = models.FloatField('Эксцесс V2', default=0.0)
    
    # === КОРРЕЛЯЦИОННЫЙ АНАЛИЗ ===
    correlation_pearson = models.FloatField(
        'Коэффициент корреляции Пирсона', 
        default=0.0,
        help_text='r = cov(X,Y) / (σ_X·σ_Y)'
    )
    correlation_spearman = models.FloatField(
        'Коэффициент корреляции Спирмена', 
        default=0.0,
        help_text='Коэффициент ранговой корреляции'
    )
    r_squared = models.FloatField(
        'Коэффициент детерминации R²', 
        default=0.0,
        help_text='Доля дисперсии Y, объяснённая X'
    )
    regression_slope = models.FloatField('Наклон регрессии (β₁)', default=0.0)
    regression_intercept = models.FloatField('Свободный член регрессии (β₀)', default=0.0)
    
    # === СТАТИСТИЧЕСКИЕ ТЕСТЫ ===
    t_statistic = models.FloatField(
        't-статистика Стьюдента', 
        default=0.0,
        help_text='t = (ȳ₁ - ȳ₂) / (s_p·√(1/n₁ + 1/n₂))'
    )
    p_value = models.FloatField(
        'p-значение', 
        default=1.0,
        help_text='Вероятность наблюдения результата при верной H₀'
    )
    degrees_of_freedom = models.IntegerField('Степени свободы', default=0)
    ks_statistic = models.FloatField(
        'D-статистика Колмогорова-Смирнова', 
        default=0.0
    )
    ks_p_value = models.FloatField('KS p-значение', default=1.0)
    
    # === ДОВЕРИТЕЛЬНЫЕ ИНТЕРВАЛЫ (95%) ===
    ci_v1_lower = models.FloatField('ДИ V1 нижняя граница', default=0.0)
    ci_v1_upper = models.FloatField('ДИ V1 верхняя граница', default=0.0)
    ci_v2_lower = models.FloatField('ДИ V2 нижняя граница', default=0.0)
    ci_v2_upper = models.FloatField('ДИ V2 верхняя граница', default=0.0)
    
    # === ДАННЫЕ ДЛЯ АНАЛИЗА И ВИЗУАЛИЗАЦИИ ===
    raw_data_v1 = models.JSONField(
        'Сырые данные V1', 
        default=list,
        help_text='Первые 20 оценок вероятности для V1'
    )
    raw_data_v2 = models.JSONField(
        'Сырые данные V2', 
        default=list,
        help_text='Первые 20 оценок вероятности для V2'
    )
    
    metrics_breakdown = models.JSONField(
        'Анализ показателей качества', 
        default=list,
        help_text='Детальный анализ вклада ŷ₁...ŷ₅ в P₄Ц'
    )
    
    graph_data = models.JSONField(
        'Данные для графиков', 
        default=dict,
        help_text='Данные для построения гистограмм, CDF, диаграмм рассеяния и радарных диаграмм'
    )
    
    # === ВЫВОДЫ И РЕКОМЕНДАЦИИ ===
    conclusion = models.TextField('Вывод', blank=True)
    recommendations = models.TextField('Рекомендации', blank=True)
    
    class Meta:
        verbose_name = 'Отчёт эффективности'
        verbose_name_plural = 'Отчёты эффективности'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['plan', 'scenario']),
        ]
    
    def __str__(self):
        return f"Отчёт: {self.plan.month.strftime('%Y-%m')} | {self.scenario.name} | {self.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    def get_better_variant(self):
        """Определяет, какой вариант лучше на основе статистической значимости"""
        # Если p-значение < 0.05 и V2 лучше по обоим показателям
        if self.p_value < 0.05 and self.p_dc_v2_mean > self.p_dc_v1_mean and self.p_guaranteed_v2 > self.p_guaranteed_v1:
            return 'V2'
        # Если p-значение < 0.05 и V1 лучше по обоим показателям
        elif self.p_value < 0.05 and self.p_dc_v1_mean > self.p_dc_v2_mean and self.p_guaranteed_v1 > self.p_guaranteed_v2:
            return 'V1'
        # Если различия не статистически значимы
        elif self.p_value >= 0.05:
            return 'Нет значимых различий'
        # В остальных случаях - неопределённо
        else:
            return 'Неопределённо (противоречивые результаты)'
    
    def get_improvement_percentage(self):
        """Процент улучшения V2 относительно V1"""
        if self.p_dc_v1_mean > 0:
            improvement = ((self.p_dc_v2_mean - self.p_dc_v1_mean) / self.p_dc_v1_mean) * 100
            return round(improvement, 1)
        return 0.0
    
    def is_statistically_significant(self):
        """Проверяет, является ли различие статистически значимым"""
        return self.p_value < 0.05
    
    def get_v1_ci_string(self):
        """Строковое представление доверительного интервала V1"""
        return f"[{self.ci_v1_lower:.3f}; {self.ci_v1_upper:.3f}]"
    
    def get_v2_ci_string(self):
        """Строковое представление доверительного интервала V2"""
        return f"[{self.ci_v2_lower:.3f}; {self.ci_v2_upper:.3f}]"
    
    def get_regression_equation(self):
        """Уравнение линейной регрессии"""
        return f"P_V2 = {self.regression_slope:.3f}·P_V1 + {self.regression_intercept:.3f}"
    
    def get_correlation_strength(self):
        """Определяет силу корреляции"""
        r_abs = abs(self.correlation_pearson)
        if r_abs >= 0.8:
            return 'Очень сильная'
        elif r_abs >= 0.6:
            return 'Сильная'
        elif r_abs >= 0.4:
            return 'Умеренная'
        elif r_abs >= 0.2:
            return 'Слабая'
        else:
            return 'Очень слабая'
    
    def get_variability_level(self):
        """Определяет уровень изменчивости на основе коэффициента вариации"""
        if self.cv_v1 < 10:
            v1_level = 'Низкая'
        elif self.cv_v1 < 20:
            v1_level = 'Умеренная'
        elif self.cv_v1 < 30:
            v1_level = 'Высокая'
        else:
            v1_level = 'Очень высокая'
        
        if self.cv_v2 < 10:
            v2_level = 'Низкая'
        elif self.cv_v2 < 20:
            v2_level = 'Умеренная'
        elif self.cv_v2 < 30:
            v2_level = 'Высокая'
        else:
            v2_level = 'Очень высокая'
        
        return {
            'V1': v1_level,
            'V2': v2_level
        }
    
    def get_metrics_summary(self):
        """Сводка по показателям качества"""
        if self.metrics_breakdown:
            try:
                import json
                metrics = json.loads(self.metrics_breakdown) if isinstance(self.metrics_breakdown, str) else self.metrics_breakdown
                if not metrics:
                    return None
                    
                # Находим наиболее проблемный показатель (наименьший вклад)
                min_contribution = min(m.get('contribution', 0) for m in metrics)
                problem_metric = next((m for m in metrics if m.get('contribution', 0) == min_contribution), metrics[0])
                
                # Находим наиболее сильный показатель (наибольший вклад)
                max_contribution = max(m.get('contribution', 0) for m in metrics)
                strong_metric = next((m for m in metrics if m.get('contribution', 0) == max_contribution), metrics[-1])
                
                return {
                    'problem_metric': problem_metric.get('name', ''),
                    'problem_contribution': problem_metric.get('contribution', 0),
                    'strong_metric': strong_metric.get('name', ''),
                    'strong_contribution': strong_metric.get('contribution', 0),
                    'total_metrics': len(metrics)
                }
            except:
                return None
        return None
    
    def save(self, *args, **kwargs):
        # Автоматически рассчитываем коэффициент вариации при сохранении
        if self.p_dc_v1_mean > 0 and self.std_v1 > 0:
            self.cv_v1 = (self.std_v1 / self.p_dc_v1_mean) * 100
        
        if self.p_dc_v2_mean > 0 and self.std_v2 > 0:
            self.cv_v2 = (self.std_v2 / self.p_dc_v2_mean) * 100
        
        super().save(*args, **kwargs)


class SimulationRun(models.Model):
    """Детализация одного прогона СИМ"""
    VARIANT_CHOICES = [
        ('V1', 'V1 - Агрегированная модель'),
        ('V2', 'V2 - Детализированная модель'),
    ]
    
    report = models.ForeignKey(
        EffectivenessReport, 
        on_delete=models.CASCADE, 
        related_name='simulation_runs',
        verbose_name='Отчёт'
    )
    variant = models.CharField(
        'Вариант модели', 
        max_length=2, 
        choices=VARIANT_CHOICES
    )
    scenario_index = models.IntegerField(
        'Номер сценария внешнего цикла',
        help_text='l = 1...N₁'
    )
    run_index = models.IntegerField(
        'Номер прогона внутреннего цикла',
        help_text='i = 1...N₂'
    )
    
    # Показатели качества (ПК РО)
    y1 = models.FloatField('ŷ₁ - доля корректных назначений', default=0.0)
    y2 = models.FloatField('ŷ₂ - доля срочных нарядов в срок', default=0.0)
    y3 = models.FloatField('ŷ₃ - показатель перегруза', default=0.0)
    y4 = models.FloatField('ŷ₄ - перерасход ресурса', default=0.0)
    y5 = models.FloatField('ŷ₅ - максимальная задержка', default=0.0)
    
    # Расчётные поля
    is_success = models.BooleanField('Цель достигнута', default=False)
    success_reason = models.TextField('Причина успеха/неудачи', blank=True)
    created_at = models.DateTimeField('Дата прогона', auto_now_add=True)
    
    # Метрики производительности
    calculation_time = models.FloatField(
        'Время расчёта (мс)', 
        default=0.0,
        help_text='Время выполнения алгоритма распределения'
    )
    memory_usage = models.FloatField(
        'Использование памяти (МБ)', 
        default=0.0
    )
    
    class Meta:
        verbose_name = 'Прогон СИМ'
        verbose_name_plural = 'Прогоны СИМ'
        ordering = ['scenario_index', 'run_index', 'variant']
        unique_together = ['report', 'variant', 'scenario_index', 'run_index']
        indexes = [
            models.Index(fields=['variant', 'is_success']),
            models.Index(fields=['scenario_index', 'run_index']),
        ]
    
    def __str__(self):
        return f"Прогон {self.run_index}.{self.scenario_index} ({self.variant})"
    
    def get_metrics_dict(self):
        """Возвращает показатели в виде словаря"""
        return {
            'y1': self.y1,
            'y2': self.y2,
            'y3': self.y3,
            'y4': self.y4,
            'y5': self.y5
        }
    
    def calculate_success(self, scenario):
        """Рассчитывает, была ли достигнута цель"""
        # Проверяем выполнение всех требований
        conditions = [
            self.y1 >= scenario.z1,  # ŷ₁ ≥ ẑ₁
            self.y2 >= scenario.z2,  # ŷ₂ ≥ ẑ₂
            self.y3 <= scenario.z3,  # ŷ₃ ≤ ẑ₃
            self.y4 <= scenario.z4,  # ŷ₄ ≤ ẑ₄
            self.y5 <= scenario.z5,  # ŷ₅ ≤ ẑ₅
        ]
        
        self.is_success = all(conditions)
        
        # Формируем причину успеха/неудачи
        if self.is_success:
            self.success_reason = "Все требования выполнены"
        else:
            failed_conditions = []
            if self.y1 < scenario.z1:
                failed_conditions.append(f"ŷ₁={self.y1:.3f} < ẑ₁={scenario.z1}")
            if self.y2 < scenario.z2:
                failed_conditions.append(f"ŷ₂={self.y2:.3f} < ẑ₂={scenario.z2}")
            if self.y3 > scenario.z3:
                failed_conditions.append(f"ŷ₃={self.y3:.3f} > ẑ₃={scenario.z3}")
            if self.y4 > scenario.z4:
                failed_conditions.append(f"ŷ₄={self.y4:.3f} > ẑ₄={scenario.z4}")
            if self.y5 > scenario.z5:
                failed_conditions.append(f"ŷ₅={self.y5:.3f} > ẑ₅={scenario.z5}")
            
            self.success_reason = "Не выполнены: " + ", ".join(failed_conditions)
        
        return self.is_success
    
    def get_quality_score(self):
        """Рассчитывает общий балл качества"""
        # Нормализуем показатели (все к диапазону 0-1)
        # Для ŷ₁ и ŷ₂: чем больше, тем лучше (уже в диапазоне 0-1)
        # Для ŷ₃, ŷ₄, ŷ₅: инвертируем (1 - значение/макс_значение)
        max_y3 = max(self.y3, 0.5)  # Предполагаем максимальный перегруз 0.5
        max_y4 = max(self.y4, 10.0)  # Предполагаем максимальный перерасход 10 часов
        max_y5 = max(self.y5, 5.0)  # Предполагаем максимальную задержку 5 дней
        
        normalized = [
            self.y1,  # ŷ₁
            self.y2,  # ŷ₂
            1 - (self.y3 / max_y3) if max_y3 > 0 else 1,  # ŷ₃ (инвертированный)
            1 - (self.y4 / max_y4) if max_y4 > 0 else 1,  # ŷ₄ (инвертированный)
            1 - (self.y5 / max_y5) if max_y5 > 0 else 1,  # ŷ₅ (инвертированный)
        ]
        
        # Взвешенное среднее (можно настроить веса)
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        score = sum(n * w for n, w in zip(normalized, weights))
        
        return round(score, 3)
    
    @property
    def composite_score(self):
        """Составной показатель качества"""
        return (self.y1 * 0.3 + self.y2 * 0.25 + 
                (1 - min(self.y3, 1.0)) * 0.2 + 
                (1 - min(self.y4/10, 1.0)) * 0.15 + 
                (1 - min(self.y5/5, 1.0)) * 0.1)


class ResearchParameterSet(models.Model):
    """Набор параметров для исследования"""
    name = models.CharField('Название набора', max_length=200)
    description = models.TextField('Описание', blank=True)
    
    # Параметры обстановки
    duty_intensity_min = models.FloatField(
        'Минимальная интенсивность нарядов', 
        default=5.0,
        help_text='Среднее число нарядов в день (мин)'
    )
    duty_intensity_max = models.FloatField(
        'Максимальная интенсивность нарядов', 
        default=15.0,
        help_text='Среднее число нарядов в день (макс)'
    )
    
    urgency_ratio_min = models.FloatField(
        'Минимальная доля срочных', 
        default=0.1,
        help_text='Минимальная доля срочных нарядов'
    )
    urgency_ratio_max = models.FloatField(
        'Максимальная доля срочных', 
        default=0.4,
        help_text='Максимальная доля срочных нарядов'
    )
    
    availability_mean = models.FloatField(
        'Средняя доступность подразделений', 
        default=0.85,
        help_text='Средний коэффициент доступности'
    )
    availability_std = models.FloatField(
        'Стандартное отклонение доступности', 
        default=0.1,
        help_text='Разброс коэффициента доступности'
    )
    
    # Параметры ресурсов
    resource_constraints = models.JSONField(
        'Ограничения ресурсов', 
        default=dict,
        help_text='JSON с ограничениями по ресурсам'
    )
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    is_active = models.BooleanField('Активный', default=True)
    
    class Meta:
        verbose_name = 'Набор параметров исследования'
        verbose_name_plural = 'Наборы параметров исследований'
    
    def __str__(self):
        return self.name


class ComparativeAnalysis(models.Model):
    """Сравнительный анализ нескольких отчётов"""
    name = models.CharField('Название анализа', max_length=200)
    description = models.TextField('Описание', blank=True)
    
    reports = models.ManyToManyField(
        EffectivenessReport,
        related_name='comparative_analyses',
        verbose_name='Отчёты для сравнения'
    )
    
    analysis_results = models.JSONField(
        'Результаты сравнительного анализа', 
        default=dict
    )
    
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Используем настройки вместо прямой ссылки
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Создатель'
    )
    
    class Meta:
        verbose_name = 'Сравнительный анализ'
        verbose_name_plural = 'Сравнительные анализы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.reports.count()} отчётов)"
    
    def add_report(self, report):
        """Добавляет отчёт в анализ"""
        self.reports.add(report)
    
    def remove_report(self, report):
        """Удаляет отчёт из анализа"""
        self.reports.remove(report)
    
    def get_comparison_summary(self):
        """Возвращает сводку сравнения"""
        reports = self.reports.all()
        
        if reports.count() < 2:
            return {'error': 'Необходимо минимум 2 отчёта для сравнения'}
        
        summary = {
            'total_reports': reports.count(),
            'scenarios': [],
            'best_v1': None,
            'best_v2': None,
            'average_improvement': 0.0
        }
        
        # Собираем данные по сценариям
        for report in reports:
            summary['scenarios'].append({
                'id': report.id,
                'scenario_name': report.scenario.name,
                'plan_date': report.plan.month.strftime('%Y-%m'),
                'p_dc_v1': report.p_dc_v1_mean,
                'p_dc_v2': report.p_dc_v2_mean,
                'improvement': report.get_improvement_percentage(),
                'significant': report.is_statistically_significant()
            })
        
        # Находим лучшие результаты
        if summary['scenarios']:
            summary['best_v1'] = max(summary['scenarios'], key=lambda x: x['p_dc_v1'])
            summary['best_v2'] = max(summary['scenarios'], key=lambda x: x['p_dc_v2'])
            summary['average_improvement'] = sum(s['improvement'] for s in summary['scenarios']) / len(summary['scenarios'])
        
        return summary
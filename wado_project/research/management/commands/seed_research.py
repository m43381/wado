# research/management/commands/seed_research.py
from django.core.management.base import BaseCommand
from research.models import ResearchScenario, EffectivenessReport, SimulationRun
from duty.models import MonthlyDutyPlan
from django.utils import timezone
from datetime import datetime, timedelta
import random
import json
import math
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Создание реалистичных тестовых данных для модуля исследования'
    
    def generate_realistic_probabilities(self, base_value, variant, n_scenarios):
        """Генерация реалистичных вероятностей достижения цели"""
        probabilities = []
        
        if variant == 'V1':
            # V1: более низкие и изменчивые результаты
            for i in range(n_scenarios):
                # Плавные колебания с тенденцией к улучшению к концу месяца
                time_factor = i / n_scenarios
                
                # Базовый уровень с учётом времени
                base = base_value * (0.9 + 0.2 * time_factor)
                
                # Добавляем случайные шумы
                noise = random.normalvariate(0, 0.08)  # Более высокий разброс
                weekly_pattern = 0.02 * math.sin(2 * math.pi * i / (n_scenarios/4))  # Недельные колебания
                
                value = base + noise + weekly_pattern
                
                # Ограничиваем диапазон
                value = max(0.5, min(0.92, value))
                
                probabilities.append(value)
        
        elif variant == 'V2':
            # V2: более высокие и стабильные результаты
            for i in range(n_scenarios):
                # Более высокая база
                base = base_value * (1.0 + 0.15 * (i / n_scenarios))
                
                # Меньший разброс
                noise = random.normalvariate(0, 0.04)
                
                # Плавный тренд улучшения
                trend = 0.005 * i
                
                # Сезонные колебания (слабые)
                seasonal = 0.01 * math.sin(2 * math.pi * i / (n_scenarios/3))
                
                value = base + noise + trend + seasonal
                value = max(0.65, min(0.97, value))
                
                probabilities.append(value)
        
        return probabilities
    
    def calculate_metrics_for_run(self, variant, scenario_index, is_success):
        """Расчёт реалистичных показателей качества для одного прогона"""
        # Базовые значения в зависимости от варианта
        if variant == 'V1':
            # V1: более низкое качество
            base_y1 = random.uniform(0.85, 0.95) if is_success else random.uniform(0.7, 0.9)
            base_y2 = random.uniform(0.75, 0.9) if is_success else random.uniform(0.6, 0.85)
            base_y3 = random.uniform(0.05, 0.15) if is_success else random.uniform(0.1, 0.25)
            base_y4 = random.uniform(1.5, 3.0) if is_success else random.uniform(2.5, 5.0)
            base_y5 = random.uniform(0.8, 1.8) if is_success else random.uniform(1.5, 3.0)
        else:
            # V2: более высокое качество
            base_y1 = random.uniform(0.92, 0.98) if is_success else random.uniform(0.85, 0.95)
            base_y2 = random.uniform(0.85, 0.95) if is_success else random.uniform(0.75, 0.9)
            base_y3 = random.uniform(0.02, 0.08) if is_success else random.uniform(0.05, 0.15)
            base_y4 = random.uniform(0.8, 2.0) if is_success else random.uniform(1.5, 3.5)
            base_y5 = random.uniform(0.5, 1.2) if is_success else random.uniform(1.0, 2.5)
        
        # Добавляем колебания в зависимости от номера сценария
        scenario_factor = 1.0 + 0.1 * math.sin(2 * math.pi * scenario_index / 20)
        
        return {
            'y1': base_y1 * (0.95 + 0.1 * random.random()),
            'y2': base_y2 * (0.95 + 0.1 * random.random()),
            'y3': base_y3 * (0.9 + 0.2 * random.random()),
            'y4': base_y4 * (0.8 + 0.4 * random.random()),
            'y5': base_y5 * (0.8 + 0.4 * random.random()),
        }
    
    def calculate_statistics(self, data):
        """Расчёт статистики для набора данных"""
        if not data:
            return {}
        
        n = len(data)
        mean_val = sum(data) / n
        sorted_data = sorted(data)
        
        # Медиана
        if n % 2 == 0:
            median_val = (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
        else:
            median_val = sorted_data[n//2]
        
        # Стандартное отклонение
        variance = sum((x - mean_val) ** 2 for x in data) / (n - 1) if n > 1 else 0
        std_val = math.sqrt(variance)
        
        # Коэффициент вариации
        cv_val = (std_val / mean_val * 100) if mean_val != 0 else 0
        
        # Асимметрия
        skewness_val = 0
        if n > 2 and std_val > 0:
            skewness_val = sum((x - mean_val) ** 3 for x in data) / n
            skewness_val /= std_val ** 3
        
        # Эксцесс
        kurtosis_val = 0
        if n > 3 and std_val > 0:
            kurtosis_val = sum((x - mean_val) ** 4 for x in data) / n
            kurtosis_val /= std_val ** 4
            kurtosis_val -= 3  # Нормализованный эксцесс
        
        return {
            'mean': mean_val,
            'median': median_val,
            'std': std_val,
            'min': min(data),
            'max': max(data),
            'cv': cv_val,
            'skewness': skewness_val,
            'kurtosis': kurtosis_val,
        }
    
    def handle(self, *args, **options):
        # Получаем или создаём тестовый план
        try:
            plan = MonthlyDutyPlan.objects.first()
            if not plan:
                plan = MonthlyDutyPlan.objects.create(
                    month=timezone.now().date().replace(day=1),
                    name='Тестовый план для исследования'
                )
                self.stdout.write(f'Создан тестовый план: {plan}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка создания плана: {e}'))
            return
        
        # Получаем или создаём пользователя (администратора)
        User = get_user_model()
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
        except:
            admin_user = None
        
        # Создаём реалистичные сценарии
        scenarios = [
            {
                'name': 'Базовый сценарий (стандартные условия)',
                'description': 'Типичные условия эксплуатации системы с умеренными требованиями',
                'n1_scenarios': 120,
                'n2_runs': 40,
                'guarantee_level': 0.90,
                'z1': 0.88,
                'z2': 0.78,
                'z3': 0.12,
                'z4': 3.5,
                'z5': 2.5,
            },
            {
                'name': 'Строгий режим (повышенные требования)',
                'description': 'Условия с повышенными требованиями к качеству распределения',
                'n1_scenarios': 200,
                'n2_runs': 60,
                'guarantee_level': 0.95,
                'z1': 0.92,
                'z2': 0.85,
                'z3': 0.08,
                'z4': 2.0,
                'z5': 1.5,
            },
            {
                'name': 'Оперативный анализ (быстрая оценка)',
                'description': 'Экспресс-оценка эффективности с сокращенным числом прогонов',
                'n1_scenarios': 60,
                'n2_runs': 20,
                'guarantee_level': 0.80,
                'z1': 0.85,
                'z2': 0.75,
                'z3': 0.15,
                'z4': 4.5,
                'z5': 3.0,
            },
            {
                'name': 'Детальное исследование V1 vs V2',
                'description': 'Углубленный сравнительный анализ двух моделей представления ресурса',
                'n1_scenarios': 300,
                'n2_runs': 80,
                'guarantee_level': 0.99,
                'z1': 0.90,
                'z2': 0.82,
                'z3': 0.10,
                'z4': 2.8,
                'z5': 2.0,
            },
            {
                'name': 'Ресурсоёмкая обстановка (много срочных)',
                'description': 'Сценарий с высокой долей срочных нарядов и ограниченными ресурсами',
                'n1_scenarios': 150,
                'n2_runs': 50,
                'guarantee_level': 0.85,
                'z1': 0.87,
                'z2': 0.80,
                'z3': 0.18,
                'z4': 4.0,
                'z5': 3.2,
            },
        ]
        
        created_reports = []
        
        for idx, scenario_data in enumerate(scenarios):
            try:
                # Создаём или получаем сценарий
                scenario, created = ResearchScenario.objects.get_or_create(
                    name=scenario_data['name'],
                    defaults=scenario_data
                )
                
                if created:
                    self.stdout.write(f'Создан сценарий: {scenario.name}')
                
                # Генерируем реалистичные данные для отчёта
                n_scenarios = scenario.n1_scenarios
                n_runs = scenario.n2_runs
                
                # Генерируем вероятности для V1 и V2
                p_values_v1 = self.generate_realistic_probabilities(0.72, 'V1', n_scenarios)
                p_values_v2 = self.generate_realistic_probabilities(0.82, 'V2', n_scenarios)
                
                # Добавляем корреляцию между V1 и V2
                correlation = 0.65 + random.uniform(-0.1, 0.1)
                for i in range(len(p_values_v2)):
                    p_values_v2[i] = correlation * p_values_v1[i] + (1 - correlation) * p_values_v2[i]
                    p_values_v2[i] = max(0.65, min(0.97, p_values_v2[i]))
                
                # Рассчитываем статистику
                stats_v1 = self.calculate_statistics(p_values_v1)
                stats_v2 = self.calculate_statistics(p_values_v2)
                
                # Рассчитываем корреляцию
                n = len(p_values_v1)
                mean_v1 = stats_v1['mean']
                mean_v2 = stats_v2['mean']
                std_v1 = stats_v1['std']
                std_v2 = stats_v2['std']
                
                if n > 1 and std_v1 > 0 and std_v2 > 0:
                    covariance = sum((p_values_v1[i] - mean_v1) * (p_values_v2[i] - mean_v2) 
                                   for i in range(n)) / (n - 1)
                    correlation_pearson = covariance / (std_v1 * std_v2)
                else:
                    correlation_pearson = 0.0
                
                r_squared = correlation_pearson ** 2
                
                # Рассчитываем регрессию
                if std_v1 > 0:
                    slope = correlation_pearson * std_v2 / std_v1
                else:
                    slope = 0
                intercept = mean_v2 - slope * mean_v1
                
                # Гарантируемая вероятность
                index = int((1 - scenario.guarantee_level) * len(p_values_v1))
                index = max(0, min(index, len(p_values_v1) - 1))
                p_guaranteed_v1 = sorted(p_values_v1)[index]
                p_guaranteed_v2 = sorted(p_values_v2)[index]
                
                # T-тест (упрощённый)
                t_statistic = (stats_v2['mean'] - stats_v1['mean']) / \
                            math.sqrt((stats_v1['std']**2 + stats_v2['std']**2) / 2)
                p_value = 2 * (1 - self.t_distribution_cdf(abs(t_statistic), n * 2 - 2))
                
                # Доверительные интервалы (95%)
                z_95 = 1.96
                ci_v1 = (
                    stats_v1['mean'] - z_95 * stats_v1['std'] / math.sqrt(n),
                    stats_v1['mean'] + z_95 * stats_v1['std'] / math.sqrt(n)
                )
                ci_v2 = (
                    stats_v2['mean'] - z_95 * stats_v2['std'] / math.sqrt(n),
                    stats_v2['mean'] + z_95 * stats_v2['std'] / math.sqrt(n)
                )
                
                # Тест Колмогорова-Смирнова (упрощённый)
                ks_statistic = self.calculate_ks_statistic(p_values_v1, p_values_v2)
                ks_p_value = 2 * math.exp(-2 * ((n * n) / (2 * n)) * ks_statistic**2)
                
                # Данные для гистограмм
                hist_bins = [0.5 + i * 0.025 for i in range(21)]  # 20 bins
                hist_v1 = [0] * 20
                hist_v2 = [0] * 20
                
                for val in p_values_v1:
                    for i in range(20):
                        if hist_bins[i] <= val < hist_bins[i+1]:
                            hist_v1[i] += 1
                            break
                
                for val in p_values_v2:
                    for i in range(20):
                        if hist_bins[i] <= val < hist_bins[i+1]:
                            hist_v2[i] += 1
                            break
                
                # Данные для CDF
                x_cdf = [0.5 + i * 0.005 for i in range(101)]
                cdf_v1 = []
                cdf_v2 = []
                
                for x in x_cdf:
                    cdf_v1.append(sum(1 for v in p_values_v1 if v <= x) / n)
                    cdf_v2.append(sum(1 for v in p_values_v2 if v <= x) / n)
                
                # Случайные данные для диаграммы рассеяния
                scatter_sample = min(50, n)
                indices = random.sample(range(n), scatter_sample)
                scatter_data = [{'x': p_values_v1[i], 'y': p_values_v2[i]} 
                              for i in indices]
                
                # Данные для радарной диаграммы
                radar_labels = ['ŷ₁: Корректность', 'ŷ₂: Срочность', 'ŷ₃: Перегруз', 
                              'ŷ₄: Перерасход', 'ŷ₅: Задержка']
                
                radar_v1 = []
                radar_v2 = []
                
                # Генерируем реалистичные значения для показателей
                for i in range(5):
                    if i == 0:  # Корректность
                        r1 = 0.85 + random.uniform(-0.08, 0.05)
                        r2 = 0.92 + random.uniform(-0.04, 0.03)
                    elif i == 1:  # Срочность
                        r1 = 0.75 + random.uniform(-0.1, 0.08)
                        r2 = 0.85 + random.uniform(-0.06, 0.05)
                    elif i == 2:  # Перегруз (меньше - лучше)
                        r1 = 0.08 + random.uniform(0, 0.1)
                        r2 = 0.04 + random.uniform(0, 0.05)
                    elif i == 3:  # Перерасход
                        r1 = 2.5 + random.uniform(0, 1.5)
                        r2 = 1.5 + random.uniform(0, 1.0)
                    else:  # Задержка
                        r1 = 1.8 + random.uniform(0, 1.2)
                        r2 = 1.1 + random.uniform(0, 0.8)
                    
                    radar_v1.append(round(r1, 3))
                    radar_v2.append(round(r2, 3))
                
                # Анализ показателей качества
                metrics_breakdown = []
                metric_names = ['Корректность', 'Срочность', 'Перегруз', 'Перерасход', 'Задержка']
                metric_weights = [0.3, 0.25, 0.2, 0.15, 0.1]
                
                for i, name in enumerate(metric_names):
                    # Базовые значения
                    if i == 0:  # Корректность
                        base_val = 0.9 + random.uniform(-0.05, 0.03)
                        threshold = scenario.z1
                    elif i == 1:  # Срочность
                        base_val = 0.82 + random.uniform(-0.08, 0.05)
                        threshold = scenario.z2
                    elif i == 2:  # Перегруз
                        base_val = 0.06 + random.uniform(0, 0.08)
                        threshold = scenario.z3
                    elif i == 3:  # Перерасход
                        base_val = 2.0 + random.uniform(0, 1.5)
                        threshold = scenario.z4
                    else:  # Задержка
                        base_val = 1.5 + random.uniform(0, 1.0)
                        threshold = scenario.z5
                    
                    # Вероятность выполнения требования
                    if i < 2:  # Чем больше, тем лучше
                        success_rate = min(1.0, base_val / max(threshold, 0.01))
                    else:  # Чем меньше, тем лучше
                        success_rate = max(0.0, 1.0 - base_val / max(threshold * 1.5, 0.01))
                    
                    contribution = success_rate * metric_weights[i] * 100
                    
                    metrics_breakdown.append({
                        'name': name,
                        'mean_value': round(base_val, 3),
                        'success_rate': round(success_rate, 3),
                        'contribution': round(contribution, 1)
                    })
                
                # Формируем выводы и рекомендации
                if stats_v2['mean'] > stats_v1['mean'] and p_value < 0.05:
                    conclusion = f"""✅ **Статистически значимое превосходство детализированной модели (V2).**
                    
                    Средняя вероятность достижения цели выше на **{(stats_v2['mean'] - stats_v1['mean']) * 100:.1f}%** 
                    (P̄дц V2 = {stats_v2['mean']:.3f}, P̄дц V1 = {stats_v1['mean']:.3f}).
                    
                    Гарантируемая вероятность (L={scenario.guarantee_level}) выше на 
                    **{(p_guaranteed_v2 - p_guaranteed_v1) * 100:.1f}%** 
                    (P₉₀ V2 = {p_guaranteed_v2:.3f}, P₉₀ V1 = {p_guaranteed_v1:.3f}).
                    
                    Статистическая значимость: p = {p_value:.4f} (p < 0.05).
                    
                    *Детализированная модель обеспечивает более высокую и стабильную эффективность распределения.*"""
                    
                    recommendations = """1. Рекомендуется внедрить детализированную модель (V2) для распределения нарядов
2. Учитывать индивидуальные характеристики исполнителей при распределении
3. Реализовать систему персональных ограничений и предпочтений
4. Провести обучение персонала работе с новой моделью
5. Осуществлять мониторинг показателей качества после внедрения"""
                else:
                    conclusion = f"""⚖️ **Сравнительный анализ не выявил статистически значимых различий.**
                    
                    Средняя вероятность достижения цели:
                    V1: {stats_v1['mean']:.3f}, V2: {stats_v2['mean']:.3f}
                    Разница: {(stats_v2['mean'] - stats_v1['mean']) * 100:.1f}%
                    
                    Статистическая значимость: p = {p_value:.4f} (p ≥ 0.05).
                    
                    *Обе модели демонстрируют сопоставимую эффективность в рамках данного сценария.*"""
                    
                    recommendations = """1. Рекомендуется провести дополнительные исследования с увеличенным объёмом выборки
2. Проанализировать конкретные случаи распределения для выявления закономерностей
3. Рассмотреть гибридный подход (использование V1 для планирования, V2 для корректировок)
4. Собрать обратную связь от пользователей о практическом использовании
5. Провести экономический анализ затрат на внедрение и эксплуатацию V2"""
                
                # Создаём отчёт
                report = EffectivenessReport.objects.create(
                    plan=plan,
                    scenario=scenario,
                    
                    # Основные показатели
                    p_dc_v1_mean=round(stats_v1['mean'], 3),
                    p_guaranteed_v1=round(p_guaranteed_v1, 3),
                    p_dc_v2_mean=round(stats_v2['mean'], 3),
                    p_guaranteed_v2=round(p_guaranteed_v2, 3),
                    
                    # Детальная статистика V1
                    median_v1=round(stats_v1['median'], 3),
                    std_v1=round(stats_v1['std'], 3),
                    min_v1=round(stats_v1['min'], 3),
                    max_v1=round(stats_v1['max'], 3),
                    cv_v1=round(stats_v1['cv'], 1),
                    skewness_v1=round(stats_v1['skewness'], 3),
                    kurtosis_v1=round(stats_v1['kurtosis'], 3),
                    
                    # Детальная статистика V2
                    median_v2=round(stats_v2['median'], 3),
                    std_v2=round(stats_v2['std'], 3),
                    min_v2=round(stats_v2['min'], 3),
                    max_v2=round(stats_v2['max'], 3),
                    cv_v2=round(stats_v2['cv'], 1),
                    skewness_v2=round(stats_v2['skewness'], 3),
                    kurtosis_v2=round(stats_v2['kurtosis'], 3),
                    
                    # Корреляционный анализ
                    correlation_pearson=round(correlation_pearson, 3),
                    correlation_spearman=round(correlation_pearson + random.uniform(-0.05, 0.05), 3),
                    r_squared=round(r_squared, 3),
                    regression_slope=round(slope, 3),
                    regression_intercept=round(intercept, 3),
                    
                    # Статистические тесты
                    t_statistic=round(t_statistic, 3),
                    p_value=round(p_value, 4),
                    degrees_of_freedom=n * 2 - 2,
                    ks_statistic=round(ks_statistic, 3),
                    ks_p_value=round(ks_p_value, 4),
                    
                    # Доверительные интервалы
                    ci_v1_lower=round(ci_v1[0], 3),
                    ci_v1_upper=round(ci_v1[1], 3),
                    ci_v2_lower=round(ci_v2[0], 3),
                    ci_v2_upper=round(ci_v2[1], 3),
                    
                    # Сырые данные
                    raw_data_v1=[round(x, 3) for x in p_values_v1[:10]],
                    raw_data_v2=[round(x, 3) for x in p_values_v2[:10]],
                    
                    # Время выполнения и симуляции
                    execution_time=round(random.uniform(2.5, 8.5), 2),
                    total_simulations=scenario.n1_scenarios * scenario.n2_runs * 2,
                    
                    # Анализ показателей
                    metrics_breakdown=metrics_breakdown,
                    conclusion=conclusion,
                    recommendations=recommendations,
                    
                    # Данные для графиков
                    graph_data={
                        'histogram_v1': {
                            'labels': [round(x, 2) for x in hist_bins[:-1]],
                            'values': hist_v1
                        },
                        'histogram_v2': {
                            'labels': [round(x, 2) for x in hist_bins[:-1]],
                            'values': hist_v2
                        },
                        'cdf_data': {
                            'x': [round(x, 2) for x in x_cdf],
                            'v1': [round(x, 3) for x in cdf_v1],
                            'v2': [round(x, 3) for x in cdf_v2]
                        },
                        'scatter_data': scatter_data,
                        'radar_data': {
                            'labels': radar_labels,
                            'v1': radar_v1,
                            'v2': radar_v2
                        }
                    }
                )
                
                created_reports.append(report)
                
                # Создаём детализацию прогонов (выборочно, чтобы не перегружать БД)
                self.create_sample_simulation_runs(report, scenario, p_values_v1, p_values_v2)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Создан отчёт: {report} (симуляций: {report.total_simulations})')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка создания отчёта для сценария {scenario_data["name"]}: {e}')
                )
        
        # Создаём сравнительный анализ
        if len(created_reports) >= 2:
            try:
                from research.models import ComparativeAnalysis
                
                analysis = ComparativeAnalysis.objects.create(
                    name='Сравнительный анализ всех сценариев',
                    description='Сводный анализ эффективности по всем созданным сценариям',
                    created_by=admin_user
                )
                
                for report in created_reports[:3]:  # Добавляем первые 3 отчёта
                    analysis.reports.add(report)
                
                # Генерируем результаты анализа
                analysis_results = {
                    'total_reports': analysis.reports.count(),
                    'scenarios': [],
                    'overall_conclusions': []
                }
                
                for report in analysis.reports.all():
                    analysis_results['scenarios'].append({
                        'id': report.id,
                        'name': report.scenario.name,
                        'p_dc_v1': report.p_dc_v1_mean,
                        'p_dc_v2': report.p_dc_v2_mean,
                        'improvement': report.get_improvement_percentage(),
                        'significant': report.is_statistically_significant()
                    })
                
                # Добавляем выводы
                if analysis_results['scenarios']:
                    avg_improvement = sum(s['improvement'] for s in analysis_results['scenarios']) / \
                                    len(analysis_results['scenarios'])
                    
                    if avg_improvement > 5 and all(s['significant'] for s in analysis_results['scenarios']):
                        conclusion = f"""Сводный анализ подтверждает статистически значимое превосходство модели V2 во всех сценариях.
Среднее улучшение эффективности: +{avg_improvement:.1f}%"""
                    else:
                        conclusion = f"""Анализ показывает неоднозначные результаты. 
Среднее изменение эффективности: {avg_improvement:+.1f}%"""
                    
                    analysis_results['overall_conclusions'].append(conclusion)
                
                analysis.analysis_results = analysis_results
                analysis.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Создан сравнительный анализ: {analysis}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка создания сравнительного анализа: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Успешно создано: {len(created_reports)} отчётов, {len(scenarios)} сценариев')
        )
    
    def create_sample_simulation_runs(self, report, scenario, p_values_v1, p_values_v2):
        """Создание выборочных записей прогонов для отчёта"""
        try:
            # Создаём прогоны только для 10% сценариев, чтобы не перегружать БД
            sample_size = max(1, scenario.n1_scenarios // 10)
            sampled_indices = random.sample(range(scenario.n1_scenarios), min(sample_size, 20))
            
            for scenario_index in sampled_indices:
                # Для V1
                is_success_v1 = p_values_v1[scenario_index] >= 0.7  # Порог успеха
                metrics_v1 = self.calculate_metrics_for_run('V1', scenario_index, is_success_v1)
                
                SimulationRun.objects.create(
                    report=report,
                    variant='V1',
                    scenario_index=scenario_index,
                    run_index=random.randint(0, scenario.n2_runs - 1),
                    y1=round(metrics_v1['y1'], 3),
                    y2=round(metrics_v1['y2'], 3),
                    y3=round(metrics_v1['y3'], 3),
                    y4=round(metrics_v1['y4'], 3),
                    y5=round(metrics_v1['y5'], 3),
                    is_success=is_success_v1,
                    success_reason='Все требования выполнены' if is_success_v1 else 
                                  f'Не выполнен порог: P={p_values_v1[scenario_index]:.3f}',
                    calculation_time=random.uniform(50, 200),
                    memory_usage=random.uniform(10, 50)
                )
                
                # Для V2
                is_success_v2 = p_values_v2[scenario_index] >= 0.7
                metrics_v2 = self.calculate_metrics_for_run('V2', scenario_index, is_success_v2)
                
                SimulationRun.objects.create(
                    report=report,
                    variant='V2',
                    scenario_index=scenario_index,
                    run_index=random.randint(0, scenario.n2_runs - 1),
                    y1=round(metrics_v2['y1'], 3),
                    y2=round(metrics_v2['y2'], 3),
                    y3=round(metrics_v2['y3'], 3),
                    y4=round(metrics_v2['y4'], 3),
                    y5=round(metrics_v2['y5'], 3),
                    is_success=is_success_v2,
                    success_reason='Все требования выполнены' if is_success_v2 else 
                                  f'Не выполнен порог: P={p_values_v2[scenario_index]:.3f}',
                    calculation_time=random.uniform(80, 300),
                    memory_usage=random.uniform(15, 60)
                )
            
            self.stdout.write(f'  Создано {len(sampled_indices) * 2} прогонов для отчёта {report.id}')
            
        except Exception as e:
            self.stdout.write(f'  Ошибка создания прогонов: {e}')
    
    def t_distribution_cdf(self, t, df):
        """Упрощённая аппроксимация CDF t-распределения"""
        if df <= 0:
            return 0.5
        
        # Аппроксимация нормальным распределением для больших df
        if df > 30:
            z = t
            return 0.5 * (1 + math.erf(z / math.sqrt(2)))
        
        # Аппроксимация для малых df
        x = df / (df + t**2)
        # Упрощённая аппроксимация
        if x < 0.5:
            cdf = 0.5 * (1 - (1 - x) ** (df/2))
        else:
            cdf = 0.5 + 0.5 * (x ** (df/2))
        
        return cdf
    
    def calculate_ks_statistic(self, data1, data2):
        """Расчёт статистики Колмогорова-Смирнова"""
        if not data1 or not data2:
            return 0
        
        n1, n2 = len(data1), len(data2)
        
        # Сортируем данные
        sorted1 = sorted(data1)
        sorted2 = sorted(data2)
        
        # Эмпирические функции распределения
        def ecdf(data, x):
            return sum(1 for d in data if d <= x) / len(data)
        
        # Находим максимальную разность
        all_values = sorted(set(sorted1 + sorted2))
        max_diff = 0
        for x in all_values:
            diff = abs(ecdf(sorted1, x) - ecdf(sorted2, x))
            if diff > max_diff:
                max_diff = diff
        
        return max_diff
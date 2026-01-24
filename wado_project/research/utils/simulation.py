"""
Реализация двухконтурного СИМ (Статистических испытаний)
"""
import time
import numpy as np
from typing import Dict, List, Tuple
from .formulas import IOFormulas


class SimulationService:
    """Сервис для проведения статистических испытаний"""
    
    def __init__(self, plan, scenario):
        self.plan = plan
        self.scenario = scenario
        self.formulas = IOFormulas()
    
    def generate_scenario_data(self, scenario_index: int) -> Dict:
        """
        Генерация данных для одного сценария внешнего цикла
        
        В реальности здесь генерировались бы:
        - Матрица допусков a_km
        - Матрица доступности b_kt
        - Мощности C_kt
        - Срочные наряды и сроки
        """
        # Заглушка для демонстрации
        return {
            'scenario_index': scenario_index,
            'intensity': np.random.uniform(0.7, 1.3),  # интенсивность потока нарядов
            'urgent_ratio': np.random.uniform(0.1, 0.4),  # доля срочных
            'availability': np.random.uniform(0.8, 1.0),  # доступность
            'complexity': np.random.uniform(0.8, 1.2),  # сложность нарядов
        }
    
    def simulate_single_run(self, variant: str, scenario_data: Dict) -> Tuple[List[float], bool]:
        """
        Один прогон внутреннего цикла СИМ
        
        Возвращает:
        - список показателей ŷ₁...ŷ₅
        - флаг успеха (выполнено событие A)
        """
        # Генерация "назначений" для данного прогона
        # В реальности здесь запускался бы алгоритм распределения
        assignments = self._generate_dummy_assignments(variant, scenario_data)
        
        # Расчёт показателей по формулам
        y_values = [
            self.formulas.calculate_y1(assignments, None, None),
            self.formulas.calculate_y2(assignments, [], {}),
            self.formulas.calculate_y3(assignments, None),
            self.formulas.calculate_y4(assignments, {}, None),
            self.formulas.calculate_y5(assignments, {}),
        ]
        
        # Проверка события A
        z_values = [
            self.scenario.z1,
            self.scenario.z2,
            self.scenario.z3,
            self.scenario.z4,
            self.scenario.z5,
        ]
        
        is_success = self.formulas.check_success(y_values, z_values)
        
        return y_values, is_success
    
    def run_two_loop_simulation(self, variant: str) -> Dict:
        """
        Запуск полного двухконтурного СИМ для одного варианта
        
        Возвращает:
        - среднюю вероятность P̄дц
        - гарантируемую вероятность P_L
        - список оценок p̂_l для каждого сценария
        - детализация прогонов (для сохранения в БД)
        """
        p_values = []  # оценки p̂_l для каждого сценария
        all_runs = []  # детализация всех прогонов
        
        # Внешний цикл: N1 сценариев
        for l in range(self.scenario.n1_scenarios):
            scenario_data = self.generate_scenario_data(l)
            success_count = 0
            scenario_runs = []
            
            # Внутренний цикл: N2 прогонов
            for i in range(self.scenario.n2_runs):
                y_values, is_success = self.simulate_single_run(variant, scenario_data)
                
                if is_success:
                    success_count += 1
                
                # Сохраняем детали прогона
                scenario_runs.append({
                    'scenario_index': l,
                    'run_index': i,
                    'y_values': y_values,
                    'is_success': is_success,
                })
            
            # Оценка условной вероятности для данного сценария
            p_l = success_count / self.scenario.n2_runs
            p_values.append(p_l)
            all_runs.extend(scenario_runs)
        
        # Расчёт итоговых показателей
        p_mean = np.mean(p_values)
        p_guaranteed = self.formulas.calculate_guaranteed_probability(
            p_values, self.scenario.guarantee_level
        )
        
        return {
            'p_mean': p_mean,
            'p_guaranteed': p_guaranteed,
            'p_values': p_values,
            'runs': all_runs,
            'total_scenarios': self.scenario.n1_scenarios,
            'total_runs': self.scenario.n1_scenarios * self.scenario.n2_runs,
        }
    
    def _generate_dummy_assignments(self, variant: str, scenario_data: Dict) -> List[Dict]:
        """Генерация заглушечных назначений для демонстрации"""
        # В реальности здесь была бы настоящая логика распределения
        num_assignments = int(50 * scenario_data['intensity'])
        
        assignments = []
        for _ in range(num_assignments):
            assignments.append({
                'unit': np.random.choice(['faculty', 'department']),
                'duty': f'duty_{np.random.randint(1, 10)}',
                'day': np.random.randint(1, 31),
                'weight': np.random.uniform(0.5, 2.0),
            })
        
        return assignments
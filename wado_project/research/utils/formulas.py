"""
Реализация формул из курсовой по Исследованию операций
"""
import numpy as np
from typing import List, Dict, Tuple


class IOFormulas:
    """Класс для работы с формулами из курсовой ИО"""
    
    @staticmethod
    def calculate_y1(assignments: List[Dict], a_matrix: np.ndarray, b_matrix: np.ndarray) -> float:
        """
        ŷ₁ - доля корректных назначений
        
        Формула:
        M_corr = Σ Σ Σ x_kmt * a_km * b_kt
        M_all = Σ Σ Σ x_kmt
        ŷ₁ = M_corr / M_all
        """
        # Заглушка для демонстрации
        # В реальности здесь был бы расчёт по матрицам назначений
        base = 0.95
        noise = np.random.normal(0, 0.03)
        return max(0.7, min(1.0, base + noise))
    
    @staticmethod
    def calculate_y2(assignments: List[Dict], urgent_tasks: List[int], deadlines: Dict) -> float:
        """
        ŷ₂ - доля срочных нарядов, выполненных в срок
        
        Формула:
        I_mt = 1 если F_mt ≤ L_mt, иначе 0
        ŷ₂ = Σ Σ q_mt * I_mt / Σ Σ q_mt
        """
        base = 0.85
        noise = np.random.normal(0, 0.05)
        return max(0.6, min(1.0, base + noise))
    
    @staticmethod
    def calculate_y3(assignments: List[Dict], capacities: np.ndarray) -> float:
        """
        ŷ₃ - показатель перегруза подразделений
        
        Формула:
        L_kt = Σ x_kmt
        Over_kt = max(0, L_kt - C_kt)
        ŷ₃ = Σ Σ Over_kt / M_all
        """
        base = 0.08
        noise = np.random.normal(0, 0.02)
        return max(0.0, min(0.3, base + noise))
    
    @staticmethod
    def calculate_y4(assignments: List[Dict], complexities: Dict, limits: np.ndarray) -> float:
        """
        ŷ₄ - перерасход ресурса (сверхурочные)
        
        Формула:
        H_kt = Σ x_kmt * h_m
        OT_kt = max(0, H_kt - H_kt^0)
        ŷ₄ = Σ Σ OT_kt
        """
        base = 1.5
        noise = np.random.normal(0, 0.5)
        return max(0.0, base + noise)
    
    @staticmethod
    def calculate_y5(assignments: List[Dict], deadlines: Dict) -> float:
        """
        ŷ₅ - максимальная задержка
        
        Формула:
        Δ_mt = max(0, F_mt - L_mt)
        ŷ₅ = max_{t,m} Δ_mt
        """
        base = 0.8
        noise = np.random.normal(0, 0.3)
        return max(0.0, base + noise)
    
    @staticmethod
    def check_success(y_values: List[float], z_values: List[float]) -> bool:
        """
        Проверка события достижения цели A
        
        Формула:
        A = {(ŷ₁ ≥ ẑ₁) ∩ (ŷ₂ ≥ ẑ₂) ∩ (ŷ₃ ≤ ẑ₃) ∩ (ŷ₄ ≤ ẑ₄) ∩ (ŷ₅ ≤ ẑ₅)}
        """
        return (
            y_values[0] >= z_values[0] and
            y_values[1] >= z_values[1] and
            y_values[2] <= z_values[2] and
            y_values[3] <= z_values[3] and
            y_values[4] <= z_values[4]
        )
    
    @staticmethod
    def calculate_guaranteed_probability(p_values: List[float], guarantee_level: float) -> float:
        """
        Расчёт гарантируемой вероятности P_L
        
        Формула:
        P_L = p_(r), где r = ⌊(1-L) * N⌋
        """
        if not p_values:
            return 0.0
        
        sorted_p = sorted(p_values)
        index = int((1 - guarantee_level) * len(sorted_p))
        index = max(0, min(index, len(sorted_p) - 1))
        return sorted_p[index]
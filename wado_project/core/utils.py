# core/utils.py
from people.models import People
from unit.models import Faculty, Department

def get_user_type(user):
    if user.is_superuser:
        return 'admin'

    groups = list(user.groups.values_list('name', flat=True))

    if 'Комендант' in groups:
        return 'commandant'
    elif 'Факультет' in groups:
        return 'faculty'
    elif 'Кафедра' in groups:
        return 'department'
    
    return None
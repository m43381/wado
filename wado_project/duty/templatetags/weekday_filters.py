# weekday_filters.py
from django import template

register = template.Library()

@register.filter
def weekday_display(value):
    """Отображает день недели по его номеру"""
    weekdays = {
        '0': 'Понедельник',
        '1': 'Вторник', 
        '2': 'Среда',
        '3': 'Четверг',
        '4': 'Пятница',
        '5': 'Суббота',
        '6': 'Воскресенье',
        'Понедельник': 'Понедельник',
        'Вторник': 'Вторник',
        'Среда': 'Среда',
        'Четверг': 'Четверг',
        'Пятница': 'Пятница',
        'Суббота': 'Суббота',
        'Воскресенье': 'Воскресенье',
    }
    return weekdays.get(str(value), str(value))
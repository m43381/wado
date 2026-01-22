# core/templatetags/custom_filters.py
from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def split(value, delimiter):
    """Разделить строку по разделителю"""
    return value.split(delimiter)

@register.filter
def get_last(value, delimiter='_'):
    """Получить последнюю часть строки после разделителя"""
    if delimiter in value:
        return value.split(delimiter)[-1]
    return value

@register.filter
def ru_plural(value, variants):
    """
    Склонение существительных после числительных
    Использование: {{ count|ru_plural:"товар,товара,товаров" }}
    """
    try:
        variants = variants.split(',')
        value = abs(int(value))
        
        if value % 10 == 1 and value % 100 != 11:
            return variants[0]
        elif value % 10 in [2, 3, 4] and value % 100 not in [12, 13, 14]:
            return variants[1]
        else:
            return variants[2]
    except (ValueError, AttributeError, IndexError):
        return variants[2] if len(variants) > 2 else ''

@register.filter
def slice_str(value, arg):
    """Срез строки как в Python"""
    try:
        start, end = arg.split(':')
        start = int(start) if start else 0
        end = int(end) if end else None
        return value[start:end]
    except (ValueError, AttributeError):
        return value
    

@register.filter
def add_days(value, days):
    """
    Добавить дни к дате
    Использование: {{ some_date|add_days:3 }}
    """
    try:
        days = int(days)
        return value + timedelta(days=days)
    except (ValueError, TypeError, AttributeError):
        return value

@register.filter
def filter_by_date(queryset, date):
    """
    Фильтровать QuerySet по дате
    """
    if hasattr(queryset, 'filter'):
        return queryset.filter(date=date)
    return [item for item in queryset if getattr(item, 'date', None) == date]

@register.filter
def divide(value, arg):
    """Разделить число"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Умножить число"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def day_of_week_short(date):
    """Короткое название дня недели"""
    days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
    try:
        return days[date.weekday()]
    except (AttributeError, IndexError):
        return ''
    
@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря"""
    return dictionary.get(key, [])
# research/templatetags/math_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Умножает value на arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Складывает value и arg."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def subtract(value, arg):
    """Вычитает arg из value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def divide(value, arg):
    """Делит value на arg."""
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0
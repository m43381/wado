from django import template

register = template.Library()

@register.filter
def str_equal(value, arg):
    """Сравнивает значения как строки"""
    return str(value) == str(arg)
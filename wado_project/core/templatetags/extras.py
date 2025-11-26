from django import template

register = template.Library()

@register.filter
def str_equal(value, arg):
    """Сравнивает значения как строки"""
    return str(value) == str(arg)

@register.filter
def cut(value, arg):
    """Удалить все вхождения arg из строки"""
    return value.replace(arg, '')
# people/templatetags/extras.py

from django import template

register = template.Library()

@register.filter(name='str_equal')
def str_equal(value, arg):
    return str(value) == str(arg)
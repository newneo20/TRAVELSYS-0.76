from django import template

register = template.Library()

@register.filter(name='add')
def add(value, arg):
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='get_item')
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return ''

@register.filter(name='range')
def filter_range(value):
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return range(0)

@register.filter(name='to_int')
def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

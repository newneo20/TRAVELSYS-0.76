from django import template

register = template.Library()

@register.filter(name='rangex')
def rangex(value):
    """Genera un rango que se puede iterar en la plantilla."""
    return range(int(value))

from django import template
from django.utils.text import slugify as django_slugify

register = template.Library()

@register.filter
def slugify(value):
    """
    Convierte un string en su forma 'slug': 
    - Pasa a minúsculas
    - Remueve caracteres especiales
    - Reemplaza espacios por guiones
    """
    if not value:
        return ''
    return django_slugify(value)

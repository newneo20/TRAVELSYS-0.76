from django import template

register = template.Library()

@register.filter
def currency_format(value):
    try:
        value = float(value)
        return "${:,.2f}".format(abs(value)) if value >= 0 else "-${:,.2f}".format(abs(value))
    except (ValueError, TypeError):
        return value  # Devuelve el valor original si no es un número

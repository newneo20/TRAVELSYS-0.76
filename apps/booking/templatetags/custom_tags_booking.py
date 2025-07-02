from django import template
from django.utils.html import format_html

register = template.Library()

@register.simple_tag
def badge_estatus(estatus):
    mapping = {
        'solicitada':  ('bg-blue-100 text-blue-800',       'fa-question-circle',  'Solicitada'),
        'pendiente':   ('bg-yellow-100 text-yellow-800',   'fa-clock',            'Pendiente'),
        'confirmada':  ('bg-green-100 text-green-800',     'fa-check-circle',     'Confirmada'),
        'modificada':  ('bg-blue-200 text-blue-900',       'fa-edit',             'Modificada'),
        'ejecutada':   ('bg-gray-100 text-gray-800',       'fa-calendar-check',   'Ejecutada'),
        'cancelada':   ('bg-red-100 text-red-800',         'fa-times-circle',     'Cancelada'),
        'reembolsada': ('bg-gray-200 text-gray-900',       'fa-undo',             'Reembolsada'),
    }
    classes, icon, label = mapping.get(
        estatus, 
        ('bg-gray-100 text-gray-800','fa-question','Desconocida')
    )
    return format_html(
        '<span class="inline-flex items-center px-2 py-1 rounded text-xs font-semibold {}">'
        '<i class="fas {} mr-1"></i>{}</span>',
        classes, icon, label
    )

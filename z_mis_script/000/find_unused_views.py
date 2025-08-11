#!/usr/bin/env python
import os
import django
import inspect
import importlib
import subprocess
from django.conf import settings
from django.urls import get_resolver, URLPattern, URLResolver

# Configura tu settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'viajero_plus.settings')
django.setup()


def get_url_view_names():
    """
    Recoge vistas mapeadas en urlpatterns.
    """
    resolver = get_resolver()
    views = set()

    def traverse(patterns):
        for pat in patterns:
            if isinstance(pat, URLPattern):
                view = pat.callback
                views.add(f"{view.__module__}.{view.__name__}")
            elif isinstance(pat, URLResolver):
                traverse(pat.url_patterns)

    traverse(resolver.url_patterns)
    return views


def get_defined_view_functions():
    """
    Escanea cada módulo views.py de las apps instaladas.
    """
    functions = {}
    for app in settings.INSTALLED_APPS:
        try:
            module = importlib.import_module(f"{app}.views")
        except ModuleNotFoundError:
            continue
        for name, func in inspect.getmembers(module, inspect.isfunction):
            full = f"{module.__name__}.{name}"
            functions[full] = func
    return functions


def is_referenced(name):
    """
    Usa grep para buscar referencias al nombre de función (excluyendo su definición).
    Devuelve True si aparece más de una vez (definición + usos).
    """
    # Buscar en todo el proyecto
    cmd = ['grep', '-R', '--include=*.py', f'{name}(', '.']
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    lines = result.stdout.decode().splitlines()
    # Si solo la definición en views.py -> len ==1
    return len(lines) > 1


if __name__ == '__main__':
    mapped = get_url_view_names()
    defined = get_defined_view_functions()

    candidates = [name for name in defined if name not in mapped]
    unused = []

    for name in candidates:
        func_name = name.split('.')[-1]
        if not is_referenced(func_name):
            unused.append(name)

    print("# Vistas potencialmente borrables (no mapeadas ni referenciadas):")
    for view in sorted(unused):
        print(view)
    print(f"\nTotal: {len(unused)} vistas")

import os
import re
from pathlib import Path

# Ruta base de las apps
base_dir = Path("apps")

# Decoradores permitidos para considerarse "protegidos"
decoradores_validos = {
    "login_required",
    "manager_required",
    "csrf_exempt",
    "require_POST",
    "permission_required",
}

# Patrón para detectar decoradores y funciones
re_decorador = re.compile(r"^@(\w+)")
re_funcion = re.compile(r"^def\s+(\w+)\s*\(request[,\)]")

# Resultado
resumen = {}

for root, _, files in os.walk(base_dir):
    if "views.py" in files:
        app_name = Path(root).parts[1]  # apps/<nombre_app>/views.py → toma el nombre de la app
        path_views = Path(root) / "views.py"

        with open(path_views, "r", encoding="utf-8") as f:
            lineas = f.readlines()

        funciones_sin_decorador = []
        decoradores_actuales = []

        for i, linea in enumerate(lineas):
            linea = linea.strip()

            match_decorador = re_decorador.match(linea)
            if match_decorador:
                decoradores_actuales.append(match_decorador.group(1))
                continue

            match_funcion = re_funcion.match(linea)
            if match_funcion:
                nombre_funcion = match_funcion.group(1)
                # Si no hay decorador válido, la marcamos como insegura
                if not any(d in decoradores_validos for d in decoradores_actuales):
                    funciones_sin_decorador.append((nombre_funcion, i + 1))
                decoradores_actuales = []

        if funciones_sin_decorador:
            resumen[app_name] = funciones_sin_decorador
        else:
            resumen[app_name] = "✔ OK"

# Mostrar resultados
print("\n🔍 Verificación de decoradores en vistas:\n")
for app, resultado in resumen.items():
    print(f"📂 {app}")
    if resultado == "✔ OK":
        print("   ✔ Todas las vistas protegidas\n")
    else:
        for nombre, linea in resultado:
            print(f"   ⚠ {nombre}  (línea {linea})")
        print()

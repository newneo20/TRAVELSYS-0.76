from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def index_redirect(request):
    if request.user.is_authenticated:
        return redirect("/usuarios/dashboard/")  # Redirige al dashboard si está logueado
    else:
        return redirect("/usuarios/login/")  # Redirige a login si no está logueado
